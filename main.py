import os
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Load env (local only)
load_dotenv()

# CONFIG
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in Render!")

SECURITY_IMG = "https://i.ibb.co/r2LkRhCY/Security.jpg"
QUESTIONS = [
    ("3 + 5", "8"),
    ("7 - 2", "5"),
    ("4 × 6", "24"),
    ("9 ÷ 3", "3"),
]

# LOADING BAR
def loading(percent: int) -> str:
    bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
    return f"`{bar} {percent}%`\n*Processing…*"

async def show_loading(message, final_text: str):
    msg = await message.reply_text(loading(0), parse_mode="Markdown")
    for p in range(20, 101, 20):
        await asyncio.sleep(0.4)
        await msg.edit_text(loading(p), parse_mode="Markdown")
    await msg.edit_text(final_text, parse_mode="Markdown")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    q, a = random.choice(QUESTIONS)
    context.user_data["answer"] = a
    context.user_data["question"] = q

    await update.message.reply_photo(
        photo=SECURITY_IMG,
        caption=f"Security Check\nHello *{user.first_name}*! Prove you're human:\n\n*What is {q}?*",
        parse_mode="Markdown"
    )

    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"ans_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"ans_{i}") for i in range(6, 11)]
    ]
    await update.message.reply_text(
        "Tap the correct answer:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# BUTTONS
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("ans_"):
        choice = data.split("_")[1]
        correct = context.user_data.get("answer")

        if choice == correct:
            context.user_data["verified"] = True
            await query.edit_message_caption(
                caption="Correct! Welcome.\nUse /menu",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_caption(caption="Wrong! /start again", parse_mode="Markdown")
        return

    if data == "menu":
        keyboard = [
            [InlineKeyboardButton("Stats", callback_data="stats")],
            [InlineKeyboardButton("Fact", callback_data="fact")],
            [InlineKeyboardButton("Settings", callback_data="settings")]
        ]
        await query.edit_message_text(
            "Main Menu:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "stats":
        await query.edit_message_text("Loading stats…")
        await show_loading(query.message, "Bot Stats\n• Users: 1,337\n• Uptime: 24d")

    elif data == "fact":
        facts = ["Octopuses have 3 hearts", "Honey never spoils", "Venus day > Venus year"]
        await show_loading(query.message, f"Random Fact\n{random.choice(facts)}")

    elif data == "settings":
        await query.edit_message_text("Settings (soon)")

# /menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("verified"):
        await update.message.reply_text("Complete /start first!")
        return
    await button(update, context)  # reuse menu logic

# MAIN
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
