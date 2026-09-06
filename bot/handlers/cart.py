from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

from products.models import Product

router = Router()


def get_product_sync(product_id):
    return Product.objects.get(id=product_id)


get_product = sync_to_async(get_product_sync)


def qty_keyboard(product_id, qty):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"qty_{product_id}_{max(1, qty-1)}"),
            InlineKeyboardButton(text=str(qty), callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"qty_{product_id}_{qty+1}"),
        ],
        [InlineKeyboardButton(text="✅ Savatga qo'shish", callback_data=f"confirm_{product_id}_{qty}")],
    ])


@router.callback_query(F.data.startswith("qty_"))
async def change_qty(callback: CallbackQuery):
    _, product_id, qty = callback.data.split("_")
    product_id, qty = int(product_id), int(qty)

    product = await get_product(product_id)
    text = f"📦 <b>{product.name}</b> — {int(product.sale_price)} so'm\n\nMiqdorini tanlang:"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=qty_keyboard(product_id, qty))
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_"))
async def confirm_add_to_cart(callback: CallbackQuery, state: FSMContext):
    _, product_id, qty = callback.data.split("_")
    product_id, qty = int(product_id), int(qty)

    product = await get_product(product_id)

    data = await state.get_data()
    cart = data.get("cart", {})

    if str(product_id) in cart:
        cart[str(product_id)]["quantity"] += qty
    else:
        cart[str(product_id)] = {
            "name": product.name,
            "price": float(product.sale_price),
            "quantity": qty,
        }

    await state.update_data(cart=cart)

    await callback.message.edit_text(f"✅ {product.name} ({qty} dona) savatga qo'shildi!")
    await callback.answer()


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


from handlers.keyboards import payment_keyboard


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