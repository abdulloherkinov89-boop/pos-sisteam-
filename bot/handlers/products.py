from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async

from handlers.auth import is_admin
from handlers.keyboards import main_menu_keyboard, get_products_keyboard
from products.models import Product, Stock
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from fsm.states import SaleStates

router = Router()


def get_product_stock_text_sync(product_id):
    product = Product.objects.get(id=product_id)
    stocks = Stock.objects.filter(product=product)

    text = f"📦 <b>{product.name}</b> — {int(product.sale_price)} so'm\n"
    for stock in stocks:
        text += f"   • {stock.branch.name}: {int(stock.quantity)} dona\n"
    return text


get_product_stock_text = sync_to_async(get_product_stock_text_sync)


def get_products_keyboard_back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Mahsulotlar ro'yxati", callback_data="products_list")],
    ])


@router.callback_query(F.data == "products_list")
async def show_products_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
        return

    keyboard = await get_products_keyboard()
    await callback.message.edit_text(
        "🏪 <b>POS Sisteam</b>\n\n"
        "📦 <b>Mahsulotlar ro'yxati</b>\n\n"
        "Qoldig'ini ko'rish uchun mahsulotni tanlang:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_text("Bosh menyu:", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def show_product_stock(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
        return

    product_id = int(callback.data.split("_")[1])
    text = await get_product_stock_text(product_id)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_products_keyboard_back())
    
    
def get_product_stock_text_by_name(query):
    products = Product.objects.filter(name__icontains=query)

    if not products.exists():
        return None

    text = ""
    for product in products:
        text += f"\n📦 <b>{product.name}</b> — {int(product.sale_price)} so'm\n"
        stocks = Stock.objects.filter(product=product)
        for stock in stocks:
            text += f"   • {stock.branch.name}: {int(stock.quantity)} dona\n"
    return text


@router.callback_query(F.data == "search_product")
async def ask_product_query(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
        return

    await callback.message.edit_text("🔍 Mahsulot nomini yozing:")
    await state.set_state(SaleStates.waiting_for_product_query)
    await callback.answer()


@router.message(SaleStates.waiting_for_product_query)
async def receive_product_query(message: Message, state: FSMContext):
    query = message.text.strip()
    text = await sync_to_async(get_product_stock_text_by_name)(query)

    if text is None:
        await message.answer(f"❌ '{query}' nomli mahsulot topilmadi.")
        await state.clear()
        return

    await message.answer(text, parse_mode="HTML")
    await state.clear()