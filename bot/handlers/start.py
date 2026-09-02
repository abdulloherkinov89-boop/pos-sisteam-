from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from handlers.auth import is_admin
from handlers.keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizga bu botdan foydalanishga ruxsat yo'q.")
        return

    await message.answer(
        "🏪 <b>POS Sisteam</b>\n\n"
        "👋 Xush kelibsiz, Administrator!\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:\n"
        "📦 — mahsulotlar ro'yxati\n"
        "🔍 — mahsulot qidirish\n"
        "🛒 — savat va sotuv",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )