import os
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

user_topics = {}

def generate_content(topic: str) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Ты — контент-менеджер для соцсетей.
Напиши пост для Instagram/VK/Telegram на тему: "{topic}"

Формат ответа:

📝 ПОСТ:
[текст поста 150-200 слов, живой и вовлекающий]

#️⃣ ХЭШТЕГИ:
[10-15 релевантных хэштегов]

🔥 STORIES (коротко, 2-3 предложения):
[короткий вариант]"""
        }]
    )
    return message.content[0].text

def make_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Одобрить", callback_data="approve"),
            InlineKeyboardButton("🔄 Перегенерировать", callback_data="regenerate"),
        ],
        [InlineKeyboardButton("✏️ Изменить тему", callback_data="change_topic")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я контент-агент.\n\nНапиши тему — я создам пост для соцсетей!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text
    user_topics[update.effective_user.id] = topic
    await update.message.reply_text("⏳ Генерирую контент...")
    try:
        content = generate_content(topic)
        await update.message.reply_text(
            f"📌 Тема: *{topic}*\n\n{content}",
            parse_mode="Markdown",
            reply_markup=make_keyboard()
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "approve":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✅ Контент одобрен! Пиши следующую тему.")

    elif query.data == "regenerate":
        topic = user_topics.get(user_id, "")
        await query.message.reply_text("🔄 Перегенерирую...")
        try:
            content = generate_content(topic)
            await query.message.reply_text(
                f"📌 Тема: *{topic}*\n\n{content}",
                parse_mode="Markdown",
                reply_markup=make_keyboard()
            )
        except Exception as e:
            await query.message.reply_text(f"❌ Ошибка: {e}")

    elif query.data == "change_topic":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✏️ Напиши новую тему:")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
