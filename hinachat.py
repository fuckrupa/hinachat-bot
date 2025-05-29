import os
import time
import random
import asyncio
import requests
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

def fetch_online(category: str) -> str:
    try:
        resp = requests.get(f"https://api.truthordarebot.xyz/v1/{category}")
        resp.raise_for_status()
        data = resp.json()
        return data.get('question', 'Hmm... I have no question right now.')
    except Exception:
        return "Sorry, I couldn't fetch a question at the moment."

async def human_typing(context: ContextTypes.DEFAULT_TYPE, chat_id: int, typing_time: float = None):
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(typing_time if typing_time else random.uniform(1.0, 3.0))

def query_payload(prompt: str):
    return {"contents": [{"parts": [{"text": prompt}]}]}

async def query_gemini(user_input: str, context: ContextTypes.DEFAULT_TYPE) -> str:
    history = context.chat_data.get('history', [])
    if not history:
        history.append({
            "role": "system",
            "content": "You are Hinata Hyuga from Naruto Shippuden: shy, kind, and supportive. Respond like a caring friend."
        })

    history.append({"role": "user", "content": user_input})
    recent = history[-10:]
    chat_history = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
    prompt = f"{chat_history}\nuser: {user_input}"

    payload = query_payload(prompt)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}"
    }

    try:
        response = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        reply = response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        reply = "Sorry... I can't think of a good reply right now."

    history.append({"role": "assistant", "content": reply})
    context.chat_data['history'] = history[-20:]
    return reply

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await human_typing(context, update.effective_chat.id)
    user = update.effective_user.first_name
    greeting = f"Oh, hello {user}-san. I'm Hinata Hyuga. How can I help you today? 😊"
    keyboard = [
        [
            InlineKeyboardButton("Updates", url="https://t.me/YourChannel"),
            InlineKeyboardButton("Support", url="https://t.me/YourGroup")
        ],
        [
            InlineKeyboardButton("Add Me To Your Group", url="https://t.me/YourBotUsername?startgroup=true")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(greeting, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await human_typing(context, update.effective_chat.id)
    help_text = (
        "I can play Truth or Dare or just chat with you!\n"
        "/start - Greet Hinata\n"
        "/truth - Ask me a truth question\n"
        "/dare - Give me a dare\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text)

async def truth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await human_typing(context, update.effective_chat.id)
    question = fetch_online('truth')
    reply = await query_gemini(f"Truth question: {question}", context)
    await update.message.reply_text(reply)

async def dare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await human_typing(context, update.effective_chat.id)
    task = fetch_online('dare')
    reply = await query_gemini(f"Dare: {task}", context)
    await update.message.reply_text(reply)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await human_typing(context, update.effective_chat.id)
    user_msg = update.message.text
    reply = await query_gemini(user_msg, context)
    await update.message.reply_text(reply)

async def setup():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    await app.bot.set_my_commands([
        BotCommand("start", "Greet Hinata"),
        BotCommand("help", "Show help menu"),
        BotCommand("truth", "Ask a truth question"),
        BotCommand("dare", "Give me a dare")
    ])

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("truth", truth))
    app.add_handler(CommandHandler("dare", dare))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))

    await app.initialize()
    await app.start()
    print("Hinata Bot is running...")
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Railway or special environments like IPython
            asyncio.ensure_future(setup())
        else:
            loop.run_until_complete(setup())
    except RuntimeError:
        asyncio.run(setup())
