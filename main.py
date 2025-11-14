import os
import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Load .env (local dev only)
load_dotenv()

# ── CONFIG ─────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN in Render environment variables!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

SECURITY_IMG_URL = "https://i.ibb.co/r2LkRhCY/Security.jpg"
MATH_QUESTIONS = [
    ("3 + 5", "8"),
    ("7 - 2", "5"),
    ("4 × 6", "24"),
    ("9 ÷ 3", "3"),
    ("2 + 10", "12"),
]

# ── STATES ─────────────────────────────────────────────────────────────────────
class MathState(StatesGroup):
    waiting_answer = State()

# ── HELPERS ───────────────────────────────────────────────────────────────────
def loading_bar(percent: int) -> str:
    """Cool animated loading bar"""
    bar_len = 12
    filled = int(bar_len * percent // 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"`{bar} {percent}%`\n*Processing…*"

async def send_loading(message: Message, final_text: str):
    """Show progressive loading then final message"""
    msg = await message.answer(loading_bar(0), parse_mode="MarkdownV2")
    for p in range(10, 101, 15):
        await asyncio.sleep(0.35)
        await msg.edit_text(loading_bar(p), parse_mode="MarkdownV2")
    await msg.edit_text(final_text, parse_mode="MarkdownV2")

# ── HANDLERS ───────────────────────────────────────────────────────────────────
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    """Welcome + security image + math challenge"""
    user = message.from_user
    welcome = (
        "🔐 <b>Security Check</b>\n"
        f"Hello <i>{user.first_name}</i>! Before we start, prove you’re not a robot 🤖\n\n"
    )

    # Send image
    await message.answer_photo(
        photo=SECURITY_IMG_URL,
        caption=welcome,
        parse_mode="MarkdownV2"
    )

    # Pick random math question
    question, answer = random.choice(MATH_QUESTIONS)
    await state.set_data({"math_answer": answer, "math_question": question})
    await state.set_state(MathState.waiting_answer)

    # Buttons (escape for MarkdownV2)
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"math_{i}") for i in range(1, 5)],
        [InlineKeyboardButton(str(i), callback_data=f"math_{i}") for i in range(5, 9)],
        [InlineKeyboardButton("🔟", callback_data="math_10")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(
        f"❓ <b>Quick Math</b>: What is `{question.replace('+', '\\+').replace('×', '\\×').replace('÷', '\\÷')}`?\n"
        "Tap the correct answer below 👇",
        reply_markup=reply_markup,
        parse_mode="MarkdownV2"
    )

@dp.callback_query(F.data.startswith("math_"))
async def math_answer(callback: CallbackQuery, state: FSMContext):
    """Handle math answer"""
    await callback.answer()
    choice = callback.data.split("_")[1]
    data = await state.get_data()
    correct = data.get("math_answer")

    if choice == correct:
        await state.clear()
        await callback.message.edit_text(
            "✅ <b>Correct!</b> You passed the security check.\n"
            "Use /menu to explore the bot!",
            parse_mode="MarkdownV2"
        )
        await state.update_data(verified=True)
    else:
        await callback.message.edit_text(
            "❌ <b>Wrong!</b> Try again with /start",
            parse_mode="MarkdownV2"
        )

@dp.message(Command("menu"))
async def menu(message: Message, state: FSMContext):
    """Show main menu if verified"""
    data = await state.get_data()
    if not data.get("verified"):
        await message.answer("🔒 Please complete /start first!")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🎲 Random Fact", callback_data="fact")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(
        "🚀 <b>Main Menu</b> – Choose an option:",
        reply_markup=reply_markup,
        parse_mode="MarkdownV2"
    )

@dp.callback_query(F.data.in_(["stats", "fact", "settings", "menu"]))
async def button_handler(callback: CallbackQuery, state: FSMContext):
    """Handle menu buttons"""
    await callback.answer()
    data = callback.data

    if data == "menu":
        keyboard = [
            [InlineKeyboardButton("📊 Stats", callback_data="stats")],
            [InlineKeyboardButton("🎲 Random Fact", callback_data="fact")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await callback.message.edit_text(
            "🚀 <b>Main Menu</b> – Choose an option:",
            reply_markup=reply_markup,
            parse_mode="MarkdownV2"
        )
        return

    # Example Actions with Loading
    if data == "stats":
        await callback.message.edit_text("⏳ Loading stats…")
        await send_loading(callback.message, "📈 <b>Bot Stats</b>\n• Users: 1,337\n• Uptime: 24d")
    elif data == "fact":
        await callback.message.edit_text("⏳ Fetching a cool fact…")
        facts = [
            "Octopuses have three hearts ❤️❤️❤️",
            "A day on Venus is longer than a year on Venus 🌍",
            "Honey never spoils 🍯"
        ]
        await send_loading(callback.message, f"🎲 <b>Random Fact</b>\n{random.choice(facts)}")
    elif data == "settings":
        await callback.message.edit_text("⚙️ Settings coming soon…")

# ── MAIN ───────────────────────────────────────────────────────────────────────
async def main():
    print("🤖 Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
