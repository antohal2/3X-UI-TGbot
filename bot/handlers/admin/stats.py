"""Статистика сервера и трафика."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.engine import get_db
from database.crud import count_active_subscriptions, get_all_payments, get_all_users
from utils.texts import STATS_MESSAGE

router = Router()


@router.callback_query(F.data == "admin:stats")
async def show_stats(callback: CallbackQuery):
    """Показать статистику."""
    async for session in get_db():
        users = await get_all_users(session)
        payments = await get_all_payments(session)
        active_subs = await count_active_subscriptions(session)

        revenue = sum(p.amount_stars for p in payments if p.status == "completed")

        text = STATS_MESSAGE.format(
            users=len(users),
            active_subs=active_subs,
            revenue=revenue,
            payments=len(payments)
        )

        await callback.message.edit_text(text)
        await callback.answer()
