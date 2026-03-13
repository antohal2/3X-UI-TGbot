"""Планировщик задач."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import async_session
from services.subscription import SubscriptionService
from database.crud import get_expiring_subscriptions, get_all_users


async def check_expired_subscriptions():
    """Проверяет истёкшие подписки каждые 30 минут."""
    async with async_session() as session:
        subscription_service = SubscriptionService()
        await subscription_service.disable_expired_subscriptions(session)


async def notify_expiring_soon(bot: Bot):
    """Уведомляет за 3 дня до истечения."""
    async with async_session() as session:
        expiring_subs = await get_expiring_subscriptions(session, days=3)

        for sub in expiring_subs:
            await bot.send_message(
                sub.user.telegram_id,
                f"📢 Ваша подписка истекает через 3 дня!\n"
                f"Продлите её в меню бота, чтобы не потерять доступ.",
            )


def setup_scheduler(bot: Bot):
    """Настроить планировщик."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_expired_subscriptions, "interval", minutes=30)
    scheduler.add_job(notify_expiring_soon, "cron", hour=12, args=[bot])  # Раз в день в 12:00
    scheduler.start()
    return scheduler