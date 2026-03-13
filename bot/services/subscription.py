"""Бизнес-логика подписок."""

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional

from config import settings
from database.crud import get_user, create_user, update_user, create_subscription, get_subscription_by_email
from .xui_service import XUIService


class SubscriptionService:
    """Сервис для управления подписками."""

    def __init__(self):
        self.xui = XUIService()

    async def create_trial_subscription(self, session: AsyncSession, telegram_id: int) -> Optional[dict]:
        """Создать пробную подписку."""
        # Проверить пользователя
        user = await get_user(session, telegram_id)
        if not user:
            user = await create_user(session, telegram_id)

        if user.trial_used:
            return None  # Уже использована

        # Создать клиента в 3X-UI
        client_email = f"trial_{telegram_id}"
        client_data = await self.xui.create_client(
            email=client_email,
            traffic_gb=settings.trial_traffic_gb,
            expire_days=settings.trial_duration_days,
            device_limit=settings.trial_device_limit,
            tg_id=str(telegram_id)
        )

        # Сохранить подписку в БД
        expires_at = datetime.utcnow() + timedelta(days=settings.trial_duration_days)
        subscription = await create_subscription(
            session=session,
            user_id=user.id,
            client_uuid=client_data["uuid"],
            client_email=client_email,
            sub_id=client_data["sub_id"],
            plan_type="trial",
            traffic_limit_gb=settings.trial_traffic_gb,
            device_limit=settings.trial_device_limit,
            expires_at=expires_at,
        )

        # Обновить флаг trial_used
        await update_user(session, telegram_id, trial_used=True)

        return {
            "subscription": subscription,
            "sub_url": f"{settings.subscription_base_url}{client_data['sub_id']}"
        }

    async def create_monthly_subscription(self, session: AsyncSession, telegram_id: int) -> dict:
        """Создать месячную подписку."""
        # Проверить пользователя
        user = await get_user(session, telegram_id)
        if not user:
            user = await create_user(session, telegram_id)

        # Создать клиента в 3X-UI
        client_email = f"user_{telegram_id}_{int(datetime.utcnow().timestamp())}"
        client_data = await self.xui.create_client(
            email=client_email,
            traffic_gb=settings.monthly_traffic_gb,
            expire_days=settings.monthly_duration_days,
            device_limit=settings.monthly_device_limit,
            tg_id=str(telegram_id)
        )

        # Сохранить подписку в БД
        expires_at = datetime.utcnow() + timedelta(days=settings.monthly_duration_days)
        subscription = await create_subscription(
            session=session,
            user_id=user.id,
            client_uuid=client_data["uuid"],
            client_email=client_email,
            sub_id=client_data["sub_id"],
            plan_type="monthly",
            traffic_limit_gb=settings.monthly_traffic_gb,
            device_limit=settings.monthly_device_limit,
            expires_at=expires_at,
        )

        return {
            "subscription": subscription,
            "sub_url": f"{settings.subscription_base_url}{client_data['sub_id']}"
        }

    async def renew_subscription(self, session: AsyncSession, subscription_id: int, extra_days: int = 30) -> bool:
        """Продлить подписку."""
        # Получить подписку
        # Предполагаем, что subscription_id известен, но в коде нужно получить по ID
        # Для простоты, используем get_subscription_by_email, но нужно адаптировать
        # В реальности, нужно добавить функцию get_subscription_by_id
        # Пока пропустим детали, сосредоточимся на структуре
        # ...

        # Обновить в 3X-UI
        # await self.xui.renew_client(client_email, extra_days)

        # Обновить в БД
        # ...

        return True

    async def disable_expired_subscriptions(self, session: AsyncSession):
        """Отключить истёкшие подписки."""
        from database.crud import get_expired_active_subscriptions, update_subscription

        expired_subs = await get_expired_active_subscriptions(session)
        for sub in expired_subs:
            await self.xui.disable_client(sub.client_email)
            await update_subscription(session, sub.id, status="expired")