"""Логика обработки платежей."""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from config import settings
from database.crud import create_payment
from .subscription import SubscriptionService


class PaymentService:
    """Сервис для обработки платежей."""

    def __init__(self):
        self.subscription_service = SubscriptionService()

    async def process_trial_payment(self, session: AsyncSession, telegram_id: int) -> Optional[dict]:
        """Обработать пробный платеж (бесплатный)."""
        return await self.subscription_service.create_trial_subscription(session, telegram_id)

    async def process_monthly_payment(
        self,
        session: AsyncSession,
        telegram_id: int,
        telegram_payment_id: str,
        amount_stars: int
    ) -> dict:
        """Обработать платеж за месячную подписку."""
        # Создать подписку
        sub_data = await self.subscription_service.create_monthly_subscription(session, telegram_id)

        # Сохранить платеж
        payment = await create_payment(
            session=session,
            user_id=sub_data["subscription"].user_id,
            subscription_id=sub_data["subscription"].id,
            telegram_payment_id=telegram_payment_id,
            amount_stars=amount_stars,
            plan_type="monthly"
        )

        return {
            "subscription": sub_data["subscription"],
            "payment": payment,
            "sub_url": sub_data["sub_url"]
        }

    async def process_renewal_payment(
        self,
        session: AsyncSession,
        subscription_id: int,
        telegram_payment_id: str,
        amount_stars: int,
        extra_days: int = 30
    ) -> bool:
        """Обработать платеж за продление подписки."""
        # Продлить подписку
        success = await self.subscription_service.renew_subscription(session, subscription_id, extra_days)

        if success:
            # Сохранить платеж (нужно получить user_id из subscription)
            # ...
            pass

        return success