"""Продление подписки."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

# Заглушка для продления
router = Router()


@router.callback_query(F.data.startswith("renew:"))
async def renew_subscription(callback: CallbackQuery):
    """Продлить подписку."""
    sub_id = callback.data.split(":")[1]
    # Логика продления через платеж
    await callback.answer(f"Продление подписки {sub_id} - в разработке", show_alert=True)