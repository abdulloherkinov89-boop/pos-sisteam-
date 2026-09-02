from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from asgiref.sync import sync_to_async
import hashlib

from products.models import Product, Stock

router = Router()


def search_products_sync(query):
    products = Product.objects.filter(name__icontains=query)[:20]

    results = []
    for product in products:
        stocks = Stock.objects.filter(product=product)
        stock_lines = "\n".join(
            f"{s.branch.name}: {int(s.quantity)} dona" for s in stocks
        )

        result_id = hashlib.md5(str(product.id).encode()).hexdigest()

        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title=f"{product.name} — {int(product.sale_price)} so'm",
                description=stock_lines or "Qoldiq mavjud emas",
                input_message_content=InputTextMessageContent(
                    message_text=f"📦 <b>{product.name}</b> — {int(product.sale_price)} so'm\n\n{stock_lines}",
                    parse_mode="HTML",
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Savatga qo'shish", callback_data=f"add_cart_{product.id}")]
                ]),
            )
        )

    return results


search_products = sync_to_async(search_products_sync)


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery):
    query = inline_query.query.strip()

    if not query:
        await inline_query.answer([], cache_time=1)
        return

    results = await search_products(query)
    await inline_query.answer(results, cache_time=1)