import asyncio
import random
import string
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# === SECURE TOKEN LOADING ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found! Set it in Environment Variables.")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# === STATES ===
class PurchaseFlow(StatesGroup):
    awaiting_interest = State()
    awaiting_policy    = State()
    awaiting_device    = State()
    completed          = State()

# === KEYBOARDS ===
start_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="CashApp V7", callback_data="select_v7")]
])

policy_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="I Accept", callback_data="accept")],
    [InlineKeyboardButton(text="I Do Not Agree", callback_data="decline")]
])

check_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Check Compatibility")]
], resize_keyboard=True, one_time_keyboard=True)

# === HELPER ===
def generate_order_id() -> str:
    return "ORDERID-" + "".join(random.choices(string.digits, k=10))

# === HANDLERS ===
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await message.answer(
        "Welcome to our exclusive software service.\n\n"
        "Please select your desired product:",
        reply_markup=start_kb
    )
    await state.set_state(PurchaseFlow.awaiting_interest)

@dp.callback_query(F.data == "select_v7")
async def send_policy(callback: types.CallbackQuery, state: FSMContext):
    policy = (
        "<b>CashApp V7 – Terms of Service</b>\n\n"
        "• No resale or redistribution allowed\n"
        "• No illegal or malicious use\n"
        "• We are not responsible for any consequences\n"
        "• Payment in cryptocurrency only – no refunds\n\n"
        "By proceeding, you agree to all terms."
    )
    await callback.message.edit_text(policy, reply_markup=policy_kb)
    await state.set_state(PurchaseFlow.awaiting_policy)

@dp.callback_query(F.data == "decline")
async def policy_declined(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Process terminated. Thank you.")
    await state.clear()

@dp.callback_query(F.data == "accept")
async def policy_accepted(callback: types.CallbackQuery, state: FSMContext):
    order_id = generate_order_id()
    await state.update_data(order_id=order_id)

    instructions = (
        "<b>Device Compatibility Check</b>\n\n"
        "Please provide:\n"
        "• iPhone model\n"
        "• iOS version\n\n"
        "<u>How to find:</u>\n"
        "Settings → General → About\n\n"
        "Also send screenshot of:\n"
        "Settings → [Your Name] (top profile)\n\n"
        "When ready, press the button below."
    )
    await callback.message.edit_text(instructions, reply_markup=check_kb)
    await state.set_state(PurchaseFlow.awaiting_device)

@dp.message(F.text == "Check Compatibility")
async def compatibility_check(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")

    await message.answer("Verifying device compatibility...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(2)

    success_msg = (
        "Compatible\n\n"
        f"<b>Order ID:</b> <code>{order_id}</code>\n\n"
        "<b>Next Step:</b>\n"
        "Send this Order ID to <b>@vuling</b>\n"
        "Payment: Cryptocurrency only\n\n"
        "Thank you for your purchase."
    )
    await message.answer(success_msg)
    await state.set_state(PurchaseFlow.completed)

# === START ===
async def main():
    print("CashApp V7 Bot is now running securely...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
