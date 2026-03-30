"""Планировщик задач."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database.engine import async_session
from services.subscription import SubscriptionService
from database.crud import get_expiring_subscriptions
from utils.texts import SUBSCRIPTION_EXPIRING_SOON

logger = logging.getLogger(__name__)


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
            if not sub.user:
                continue

            try:
                await bot.send_message(sub.user.telegram_id, SUBSCRIPTION_EXPIRING_SOON)
            except Exception as exc:
                logger.warning("Не удалось отправить уведомление пользователю %s: %s", sub.user.telegram_id, exc)


def setup_scheduler(bot: Bot):
    """Настроить планировщик."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_expired_subscriptions, "interval", minutes=30)
    scheduler.add_job(notify_expiring_soon, "cron", hour=12, args=[bot])  # Раз в день в 12:00
    scheduler.start()
    return scheduler
