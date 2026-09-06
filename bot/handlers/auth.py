import os

ADMIN_IDS = [
    int(x) for x in os.getenv("TELEGRAM_ADMIN_ID", "").split(",") if x.strip()
]

KASSIR_IDS = [
    int(x) for x in os.getenv("TELEGRAM_KASSIR_IDS", "").split(",") if x.strip()
]


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def is_kassir(user_id: int) -> bool:
    return user_id in KASSIR_IDS


def is_allowed(user_id: int) -> bool:
    return is_admin(user_id) or is_kassir(user_id)