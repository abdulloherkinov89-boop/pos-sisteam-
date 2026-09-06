from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.db import transaction
from decimal import Decimal
from html import escape

from products.models import Product, Branch, Stock
from sales.models import Customer, Sale, SaleItem
from bot.fsm.states import SaleStates

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

    if callback.message:
        # Oddiy xabar bo'lsa
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=qty_keyboard(product_id, qty))
    else:
        # Inline natija bo'lsa
        await callback.bot.edit_message_text(
            text,
            inline_message_id=callback.inline_message_id,
            parse_mode="HTML",
            reply_markup=qty_keyboard(product_id, qty)
        )

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

    text = f"✅ {product.name} ({qty} dona) savatga qo'shildi!"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Savatni ko'rish", callback_data="show_cart")]
    ])

    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.bot.edit_message_text(
            text,
            inline_message_id=callback.inline_message_id,
            reply_markup=keyboard
        )

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
    keyboard = cart_keyboard(cart)

    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await callback.bot.edit_message_text(
            text,
            inline_message_id=callback.inline_message_id,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    await callback.answer()


from handlers.keyboards import main_menu_keyboard, payment_keyboard


class CheckoutError(Exception):
    pass


def create_sale_sync(cart, payment_type, customer_id=None):
    with transaction.atomic():
        branch = Branch.objects.first()
        if branch is None:
            raise CheckoutError("❌ Filial topilmadi.")

        customer = None
        if customer_id is not None:
            customer = Customer.objects.select_for_update().get(id=customer_id)

        total_amount = sum(
            (Decimal(str(item["price"])) * item["quantity"] for item in cart.values()),
            Decimal("0"),
        )
        sale = Sale.objects.create(
            branch=branch,
            customer=customer,
            payment_type=payment_type,
            total_amount=total_amount,
        )

        for product_id, item in cart.items():
            product = Product.objects.get(id=int(product_id))
            quantity = Decimal(str(item["quantity"]))
            stock = Stock.objects.select_for_update().get(branch=branch, product=product)
            if stock.quantity < quantity:
                raise CheckoutError(
                    f"❌ {product.name} uchun yetarli qoldiq yo'q "
                    f"(mavjud: {stock.quantity:g}, kerak: {quantity:g})."
                )

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                price=Decimal(str(item["price"])),
            )
            stock.quantity -= quantity
            stock.save(update_fields=["quantity"])

        if customer is not None:
            customer.debt_balance += total_amount
            customer.save(update_fields=["debt_balance"])

    return sale.id, total_amount


create_sale = sync_to_async(create_sale_sync)


def find_customers_sync(query):
    return list(Customer.objects.filter(name__icontains=query).values("id", "name"))


find_customers = sync_to_async(find_customers_sync)


def get_customer_sync(customer_id):
    return Customer.objects.get(id=customer_id)


get_customer = sync_to_async(get_customer_sync)


def customer_keyboard(customers):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=customer["name"],
            callback_data=f"select_customer_{customer['id']}"
        )]
        for customer in customers
    ])


def receipt_text(cart, sale_id, total_amount, payment_type, customer_name=None):
    text = "✅ <b>Sotuv muvaffaqiyatli amalga oshirildi!</b>\n\n"
    text += f"🧾 Chek ID: <b>#{sale_id}</b>\n"
    text += "\n"
    for item in cart.values():
        subtotal = Decimal(str(item["price"])) * item["quantity"]
        text += (
            f"• {escape(str(item['name']))} — {item['quantity']} x "
            f"{int(item['price'])} = {int(subtotal)} so'm\n"
        )
    text += f"\n💰 <b>Jami: {int(total_amount)} so'm</b>"
    text += f"\n💳 To'lov: <b>{payment_type}</b>"
    if customer_name:
        text += f"\n👤 Mijoz: <b>{escape(customer_name)}</b>"
    return text


async def edit_callback_text(callback, text, reply_markup=None):
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await callback.bot.edit_message_text(
            text,
            inline_message_id=callback.inline_message_id,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


async def complete_sale(callback, state, payment_type, customer_id=None, customer_name=None):
    data = await state.get_data()
    cart = data.get("cart", {})
    if not cart:
        await callback.answer("🛒 Savat bo'sh!", show_alert=True)
        return

    try:
        sale_id, total_amount = await create_sale(cart, payment_type, customer_id)
    except CheckoutError as error:
        await callback.answer(str(error), show_alert=True)
        return
    except (Customer.DoesNotExist, Product.DoesNotExist, Stock.DoesNotExist):
        await callback.answer("❌ Mahsulot yoki ombor qoldig'i topilmadi.", show_alert=True)
        return

    await state.clear()
    await edit_callback_text(
        callback,
        receipt_text(cart, sale_id, total_amount, payment_type, customer_name),
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})

    if not cart:
        await callback.answer("🛒 Savat bo'sh!", show_alert=True)
        return

    text = build_cart_text(cart) + "\n\n💳 To'lov turini tanlang:"
    await edit_callback_text(callback, text, payment_keyboard())
    await callback.answer()


@router.callback_query(F.data == "pay_naqd")
@router.callback_query(F.data == "pay_karta")
async def pay_cash_or_card(callback: CallbackQuery, state: FSMContext):
    payment_type = "naqd" if callback.data == "pay_naqd" else "karta"
    await complete_sale(callback, state, payment_type)


@router.callback_query(F.data == "pay_qarz")
async def start_credit_sale(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SaleStates.waiting_for_customer)
    await edit_callback_text(callback, "👤 Mijoz ismini kiriting:")
    await callback.answer()


@router.message(SaleStates.waiting_for_customer)
async def find_customer(message: Message, state: FSMContext):
    if message.via_bot:
        return

    customers = await find_customers((message.text or "").strip())
    if not customers:
        await message.answer("❌ Bunday mijoz topilmadi.")
        await state.clear()
        return

    if len(customers) > 1:
        await message.answer(
            "👤 Mijozni tanlang:",
            reply_markup=customer_keyboard(customers),
        )
        return

    customer = customers[0]
    data = await state.get_data()
    cart = data.get("cart", {})
    try:
        sale_id, total_amount = await create_sale(cart, "qarz", customer["id"])
    except CheckoutError as error:
        await message.answer(str(error))
        return
    except (Customer.DoesNotExist, Product.DoesNotExist, Stock.DoesNotExist):
        await message.answer("❌ Mahsulot yoki ombor qoldig'i topilmadi.")
        return

    await state.clear()
    await message.answer(
        receipt_text(cart, sale_id, total_amount, "qarz", customer["name"]),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data.startswith("select_customer_"))
async def select_customer(callback: CallbackQuery, state: FSMContext):
    customer_id = int(callback.data.removeprefix("select_customer_"))
    try:
        customer = await get_customer(customer_id)
    except Customer.DoesNotExist:
        await callback.answer("❌ Mijoz topilmadi.", show_alert=True)
        await state.clear()
        return

    await complete_sale(callback, state, "qarz", customer.id, customer.name)