"""Статистика сервера и трафика."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import get_db
from database.crud import get_all_users, get_all_payments
from utils.texts import STATS_MESSAGE

router = Router()


@router.callback_query(F.data == "admin:stats")
async def show_stats(callback: CallbackQuery):
    """Показать статистику."""
    async for session in get_db():
        users = await get_all_users(session)
        payments = await get_all_payments(session)

        # Подсчет активных подписок (заглушка)
        active_subs = sum(1 for u in users if any(s.status == "active" for s in u.subscriptions))

        revenue = sum(p.amount_stars for p in payments)

        text = STATS_MESSAGE.format(
            users=len(users),
            active_subs=active_subs,
            revenue=revenue,
            payments=len(payments)
        )

        await callback.message.edit_text(text)
        await callback.answer()