from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async
from handlers.keyboards import payment_keyboard


from products.models import Product

router = Router()


def get_product_sync(product_id):
    return Product.objects.get(id=product_id)


get_product = sync_to_async(get_product_sync)


@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    product = await get_product(product_id)

    data = await state.get_data()
    cart = data.get("cart", {})

    # Agar mahsulot allaqachon savatda bo'lsa, miqdorini +1 qilamiz
    if str(product_id) in cart:
        cart[str(product_id)]["quantity"] += 1
    else:
        cart[str(product_id)] = {
            "name": product.name,
            "price": float(product.sale_price),
            "quantity": 1,
        }

    await state.update_data(cart=cart)

    await callback.answer(f"✅ {product.name} savatga qo'shildi!", show_alert=False)
    

def build_cart_text(cart):
    if not cart:
        return "🛒 Savat bo'sh."

    text = "🛒 <b>Savat:</b>\n\n"
    total = 0
    for item in cart.values():
        subtotal = item["price"] * item["quantity"]
        total += subtotal
        text += f"• {item['name']} — {item['quantity']} x {int(item['price'])} = {int(subtotal)} so'm\n"

    text += f"\n💰 <b>Jami: {int(total)} so'm</b>"
    return text


def cart_keyboard(cart):
    buttons = []
    if cart:
        buttons.append([InlineKeyboardButton(text="✅ Rasmiylashtirish", callback_data="checkout")])
    buttons.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "show_cart")
async def show_cart(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})

    text = build_cart_text(cart)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cart_keyboard(cart))
    await callback.answer()
    

@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})

    if not cart:
        await callback.answer("🛒 Savat bo'sh!", show_alert=True)
        return

    text = build_cart_text(cart) + "\n\n💳 To'lov turini tanlang:"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=payment_keyboard())
    await callback.answer()