import secrets
import string
from datetime import datetime
from typing import List
import calendar

from aiogram.types import Chat

def generate_child_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_month_list(year: int = None) -> List[str]:
    """
    Возвращает список месяцев в формате YYYY.MM
    Например: ['2025.12', '2025.11', ..., '2025.01']
    Если year не указан, берется текущий год.
    """
    if year is None:
        year = datetime.now().year
    current_month = 12
    months = [f"{year}.{month:02}" for month in range(current_month, 0, -1)]
    return months


def get_days_from_month_str(month_str: str) -> List[str]:
    """
    Принимает строку 'YYYY.MM' и возвращает список дней месяца в формате 'YYYY.MM.DD'
    """
    year, month = map(int, month_str.split('.'))
    num_days = calendar.monthrange(year, month)[1]
    return [f"{year}.{month:02}.{day:02}" for day in range(1, num_days + 1)]



def format_chat_username(chat: Chat):
    if chat.username:
        return f"@{chat.username}"
    elif chat.full_name:  # full_name у pyrogram, у aiogram есть first_name + last_name
        return chat.full_name
    else:
        return str(chat.id)