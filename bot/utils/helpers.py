"""Утилиты."""

import uuid
from datetime import datetime
from typing import Optional


def generate_uuid() -> str:
    """Генерировать UUID."""
    return str(uuid.uuid4())


def generate_sub_id() -> str:
    """Генерировать короткий ID для подписки."""
    return str(uuid.uuid4())[:8]


def format_bytes(bytes_value: int) -> str:
    """Форматировать байты в читаемый вид."""
    if bytes_value == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    value = float(bytes_value)

    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1

    return ".1f"


def format_datetime(dt: datetime) -> str:
    """Форматировать дату и время."""
    return dt.strftime("%d.%m.%Y %H:%M")


def parse_datetime(date_str: str) -> Optional[datetime]:
    """Парсить строку даты."""
    try:
        return datetime.strptime(date_str, "%d.%m.%Y %H:%M")
    except ValueError:
        return None