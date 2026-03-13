"""Клавиатуры пользователя."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню пользователя."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🆓 Пробная подписка", callback_data="trial")
    builder.button(text="💳 Купить подписку", callback_data="buy_menu")
    builder.button(text="📋 Мои подписки", callback_data="my_subs")
    builder.adjust(1)
    return builder.as_markup()


def get_buy_menu_kb() -> InlineKeyboardMarkup:
    """Меню выбора подписки для покупки."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🆓 Пробная (бесплатно)", callback_data="buy:trial")
    builder.button(text="💰 Месячная (50 ⭐)", callback_data="buy:monthly")
    builder.button(text="⬅️ Назад", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


def get_subscription_actions_kb(sub_id: int) -> InlineKeyboardMarkup:
    """Кнопки действий для подписки."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Продлить", callback_data=f"renew:{sub_id}")
    builder.button(text="🔗 Получить ссылку", callback_data=f"get_link:{sub_id}")
    builder.adjust(2)
    return builder.as_markup()