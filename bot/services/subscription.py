"""Бизнес-логика подписок."""

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional

from config import settings
from database.crud import (
    create_subscription,
    create_user,
    get_subscription_by_id,
    get_user,
    update_subscription,
    update_user,
)
from .xui_service import XUIService


class SubscriptionService:
    """Сервис для управления подписками."""

    def __init__(self):
        self.xui = XUIService()

    @staticmethod
    def build_subscription_url(sub_id: str) -> str:
        """Собрать ссылку на подписку по short id."""
        base_url = settings.subscription_base_url.rstrip("/")
        return f"{base_url}/{sub_id}"

    async def create_trial_subscription(self, session: AsyncSession, telegram_id: int) -> Optional[dict]:
        """Создать пробную подписку."""
        # Проверить пользователя
        user = await get_user(session, telegram_id)
        if not user:
            user = await create_user(
                session,
                telegram_id,
                is_admin=telegram_id in settings.admin_ids_list,
            )

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
            "sub_url": self.build_subscription_url(client_data["sub_id"])
        }

    async def create_monthly_subscription(self, session: AsyncSession, telegram_id: int) -> dict:
        """Создать месячную подписку."""
        # Проверить пользователя
        user = await get_user(session, telegram_id)
        if not user:
            user = await create_user(
                session,
                telegram_id,
                is_admin=telegram_id in settings.admin_ids_list,
            )

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
            "sub_url": self.build_subscription_url(client_data["sub_id"])
        }

    async def renew_subscription(
        self,
        session: AsyncSession,
        subscription_id: int,
        extra_days: int = 30,
    ):
        """Продлить подписку."""
        subscription = await get_subscription_by_id(session, subscription_id)
        if not subscription:
            return None

        new_expire_ms = await self.xui.renew_client(subscription.client_email, extra_days)
        if new_expire_ms is None:
            return None

        expires_at = datetime.utcfromtimestamp(new_expire_ms / 1000)
        await update_subscription(
            session,
            subscription.id,
            expires_at=expires_at,
            status="active",
        )
        return await get_subscription_by_id(session, subscription.id)

    async def get_subscription_link(
        self,
        session: AsyncSession,
        subscription_id: int,
        telegram_id: int,
    ) -> Optional[str]:
        """Получить ссылку подписки, если она принадлежит пользователю."""
        user = await get_user(session, telegram_id)
        if not user:
            return None

        subscription = await get_subscription_by_id(session, subscription_id)
        if not subscription or subscription.user_id != user.id or not subscription.sub_id:
            return None

        return self.build_subscription_url(subscription.sub_id)

    async def disable_expired_subscriptions(self, session: AsyncSession):
        """Отключить истёкшие подписки."""
        from database.crud import get_expired_active_subscriptions, update_subscription

        expired_subs = await get_expired_active_subscriptions(session)
        for sub in expired_subs:
            await self.xui.disable_client(sub.client_email)
            await update_subscription(session, sub.id, status="expired")
