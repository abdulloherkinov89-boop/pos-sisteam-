from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from handlers.auth import is_admin
from handlers.keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ <b>Kirish imkoni mavjud emas.</b>\n\n"
            "Botdan foydalanish uchun administratoringizga murojaat qiling.",
            parse_mode="HTML",
        )
        return

    await message.answer(
        "🏪 <b>POS Sisteam</b> bosh menyusiga xush kelibsiz!\n\n"
        "👋 Administrator sifatida savdo jarayonini boshqarishingiz mumkin.\n"
        "Kerakli bo'limni tanlang:\n"
        "📦 — mahsulotlar ro'yxati\n"
        "🔍 — mahsulot qidirish\n"
        "🛒 — savat va sotuv",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )