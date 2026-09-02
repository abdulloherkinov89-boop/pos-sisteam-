from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async

from products.models import Product


def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="products_list"),
            InlineKeyboardButton(text="🔍 Mahsulot qidirish", callback_data="search_product")
        ],
        [
            InlineKeyboardButton(text="🛒 Savat", callback_data="show_cart")
        ],
    ])


def get_products_keyboard_sync():
    products = list(Product.objects.all())

    buttons = []
    for i in range(0, len(products), 2):
        row = [InlineKeyboardButton(text=p.name, callback_data=f"product_{p.id}") for p in products[i:i+2]]
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


get_products_keyboard = sync_to_async(get_products_keyboard_sync)


def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Naqd", callback_data="pay_naqd")],
        [InlineKeyboardButton(text="💳 Karta", callback_data="pay_karta")],
        [InlineKeyboardButton(text="📝 Nasiya", callback_data="pay_qarz")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_cart")],
    ])