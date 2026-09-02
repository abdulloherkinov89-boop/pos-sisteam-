from aiogram.fsm.state import State, StatesGroup


class SaleStates(StatesGroup):
    waiting_for_product_query = State()   # mahsulot nomini kutish
    waiting_for_quantity = State()         # miqdorni kutish
    waiting_for_customer = State()         # (nasiya bo'lsa) mijoz ismini kutish