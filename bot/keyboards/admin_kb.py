"""Клавиатуры администратора."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_menu_kb() -> InlineKeyboardMarkup:
    """Админ-панель."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статус сервера", callback_data="admin:server_status")
    builder.button(text="👥 Список клиентов", callback_data="admin:clients_list")
    builder.button(text="🔍 Поиск клиента", callback_data="admin:search_client")
    builder.button(text="🔄 Перезапуск Xray", callback_data="admin:restart_xray")
    builder.button(text="📤 Рассылка", callback_data="admin:broadcast")
    builder.button(text="📈 Статистика", callback_data="admin:stats")
    builder.button(text="⬅️ В пользовательское меню", callback_data="back_to_user")
    builder.adjust(1)
    return builder.as_markup()


def get_client_management_kb(client_email: str) -> InlineKeyboardMarkup:
    """Кнопки управления клиентом."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Включить", callback_data=f"client:enable:{client_email}")
    builder.button(text="❌ Отключить", callback_data=f"client:disable:{client_email}")
    builder.button(text="🔄 Продлить на 30 дней", callback_data=f"client:renew:{client_email}")
    builder.button(text="🗑️ Удалить", callback_data=f"client:delete:{client_email}")
    builder.button(text="⬅️ Назад", callback_data="admin:clients_list")
    builder.adjust(2)
    return builder.as_markup()