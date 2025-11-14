import os
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Load .env (only for local dev – Render uses env vars directly)
load_dotenv()

# ── CONFIG ─────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN in Render environment variables")

SECURITY_IMG_URL = "https://i.ibb.co/r2LkRhCY/Security.jpg"
MATH_QUESTIONS = [
    ("3 + 5", "8"),
    ("7 - 2", "5"),
    ("4 × 6", "24"),
    ("9 ÷ 3", "3"),
    ("2 + 10", "12"),
]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def loading_bar(percent: int) -> str:
    """Cool animated loading bar"""
    bar_len = 12
    filled = int(bar_len * percent // 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"`{bar} {percent}%`\n*Processing…*"

async def send_loading(update: Update, context: ContextTypes.DEFAULT_TYPE, final_text: str):
    """Show progressive loading then final message"""
    msg = await update.message.reply_text(loading_bar(0), parse_mode="Markdown")
    for p in range(10, 101, 15):
        await asyncio.sleep(0.35)
        await msg.edit_text(loading_bar(p), parse_mode="Markdown")
    await msg.edit_text(final_text, parse_mode="Markdown")

# ── HANDLERS ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome + security image + math challenge"""
    user = update.effective_user
    welcome = (
        "🔐 **Security Check**\n"
        f"Hello *{user.first_name}*! Before we start, prove you’re not a robot 🤖\n\n"
    )

    # Send image
    await update.message.reply_photo(
        photo=SECURITY_IMG_URL,
        caption=welcome,
        parse_mode="Markdown"
    )

    # Pick random math question
    question, answer = random.choice(MATH_QUESTIONS)
    context.user_data["math_answer"] = answer
    context.user_data["math_question"] = question

    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"math_{i}") for i in range(1, 5)],
        [InlineKeyboardButton(str(i), callback_data=f"math_{i}") for i in range(5, 9)],
        [InlineKeyboardButton("🔟", callback_data="math_10")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"❓ *Quick Math*: What is `{question}`?\n"
        "Tap the correct answer below 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button presses"""
    query = update.callback_query
    await query.answer()

    data = query.data

    # ── Math Challenge ──
    if data.startswith("math_"):
        choice = data.split("_")[1]
        correct = context.user_data.get("math_answer")

        if choice == correct:
            await query.edit_message_caption(
                caption="✅ **Correct!** You passed the security check.\n"
                        "Use /menu to explore the bot!",
                parse_mode="Markdown"
            )
            context.user_data["verified"] = True
        else:
            await query.edit_message_caption(
                caption="❌ **Wrong!** Try again with /start",
                parse_mode="Markdown"
            )
            context.user_data.clear()
        return

    # ── Main Menu ──
    if data == "menu":
        keyboard = [
            [InlineKeyboardButton("📊 Stats", callback_data="stats")],
            [InlineKeyboardButton("🎲 Random Fact", callback_data="fact")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🚀 **Main Menu** – Choose an option:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    # ── Example Actions ──
    if data == "stats":
        await query.edit_message_text("⏳ Loading stats…")
        await send_loading(update, context, "📈 **Bot Stats**\n• Users: 1,337\n• Uptime: 24d")
    elif data == "fact":
        await query.edit_message_text("⏳ Fetching a cool fact…")
        facts = [
            "Octopuses have three hearts ❤️❤️❤️",
            "A day on Venus is longer than a year on Venus 🌍",
            "Honey never spoils 🍯"
        ]
        await send_loading(update, context, f"🎲 **Random Fact**\n{random.choice(facts)}")
    elif data == "settings":
        await query.edit_message_text("⚙️ Settings coming soon…")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu if user is verified"""
    if not context.user_data.get("verified"):
        await update.message.reply_text("🔒 Please complete /start first!")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🎲 Random Fact", callback_data="fact")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🚀 **Main Menu** – Choose an option:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
