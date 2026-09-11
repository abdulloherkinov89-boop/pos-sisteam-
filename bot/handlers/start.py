from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from handlers.auth import is_admin, is_kassir
from handlers.keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id

    if is_admin(user_id):
        is_admin_user = True
        role_text = "Administrator"
    elif is_kassir(user_id):
        is_admin_user = False
        role_text = "Kassir"
    else:
        await message.answer("⛔ Kirish taqiqlangan. Sizda bu botdan foydalanish huquqi yo'q.")
        return

    await message.answer(
        "🏪 <b>POS Sisteam</b> bosh menyusiga xush kelibsiz!\n\n"
        f"👋 {role_text} sifatida savdo jarayonini boshqarishingiz mumkin.\n"
        "Kerakli bo'limni tanlang:\n"
        "📦 — mahsulotlar ro'yxati\n"
        "🔍 — mahsulot qidirish\n"
        "🛒 — savat va sotuv",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(is_admin_user=is_admin_user)
    )