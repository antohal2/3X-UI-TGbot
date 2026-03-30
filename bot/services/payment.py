"""Логика обработки платежей."""

import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from config import settings
from database.crud import (
    create_user,
    create_payment,
    get_payment_by_telegram_payment_id,
    get_subscription_by_id,
    get_user,
    update_payment,
)
from .subscription import SubscriptionService

logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис для обработки платежей."""

    def __init__(self):
        self.subscription_service = SubscriptionService()

    async def _get_existing_result(self, session: AsyncSession, telegram_payment_id: str) -> Optional[dict]:
        """Вернуть уже обработанный платеж, если он существует."""
        existing_payment = await get_payment_by_telegram_payment_id(
            session,
            telegram_payment_id,
            load_subscription=True,
        )
        if not existing_payment:
            return None

        if existing_payment.status == "completed" and existing_payment.subscription:
            subscription = existing_payment.subscription
            return {
                "subscription": subscription,
                "payment": existing_payment,
                "sub_url": self.subscription_service.build_subscription_url(subscription.sub_id),
            }

        if existing_payment.status == "processing":
            raise RuntimeError("Платеж уже обрабатывается, повторите попытку позже.")

        if existing_payment.status == "failed":
            raise RuntimeError(
                "Платеж был получен, но выдача подписки завершилась ошибкой. "
                "Проверьте заказ вручную."
            )

        return None

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
        existing_result = await self._get_existing_result(session, telegram_payment_id)
        if existing_result:
            return existing_result

        user = await get_user(session, telegram_id)
        if not user:
            user = await create_user(
                session,
                telegram_id,
                is_admin=telegram_id in settings.admin_ids_list,
            )

        try:
            payment = await create_payment(
                session=session,
                user_id=user.id,
                subscription_id=None,
                telegram_payment_id=telegram_payment_id,
                amount_stars=amount_stars,
                plan_type="monthly",
                status="processing",
            )
        except IntegrityError:
            await session.rollback()
            return await self._get_existing_result(session, telegram_payment_id)

        try:
            sub_data = await self.subscription_service.create_monthly_subscription(session, telegram_id)
            await update_payment(
                session,
                payment.id,
                subscription_id=sub_data["subscription"].id,
                status="completed",
            )
            payment = await get_payment_by_telegram_payment_id(session, telegram_payment_id)
            return {
                "subscription": sub_data["subscription"],
                "payment": payment,
                "sub_url": sub_data["sub_url"]
            }
        except Exception:
            logger.exception("Ошибка выдачи месячной подписки после успешного платежа %s", telegram_payment_id)
            await update_payment(session, payment.id, status="failed")
            raise

    async def process_renewal_payment(
        self,
        session: AsyncSession,
        telegram_id: int,
        subscription_id: int,
        telegram_payment_id: str,
        amount_stars: int,
        extra_days: int = 30
    ) -> Optional[dict]:
        """Обработать платеж за продление подписки."""
        existing_result = await self._get_existing_result(session, telegram_payment_id)
        if existing_result:
            return existing_result

        user = await get_user(session, telegram_id)
        subscription = await get_subscription_by_id(session, subscription_id)
        if not user or not subscription or subscription.user_id != user.id:
            return None

        try:
            payment = await create_payment(
                session=session,
                user_id=user.id,
                subscription_id=subscription.id,
                telegram_payment_id=telegram_payment_id,
                amount_stars=amount_stars,
                plan_type="renewal",
                status="processing",
            )
        except IntegrityError:
            await session.rollback()
            return await self._get_existing_result(session, telegram_payment_id)

        try:
            renewed_subscription = await self.subscription_service.renew_subscription(
                session,
                subscription_id,
                extra_days,
            )
            if renewed_subscription is None:
                await update_payment(session, payment.id, status="failed")
                return None

            await update_payment(
                session,
                payment.id,
                subscription_id=renewed_subscription.id,
                status="completed",
            )
            payment = await get_payment_by_telegram_payment_id(session, telegram_payment_id)
            return {
                "subscription": renewed_subscription,
                "payment": payment,
                "sub_url": self.subscription_service.build_subscription_url(renewed_subscription.sub_id)
            }
        except Exception:
            logger.exception("Ошибка продления подписки после успешного платежа %s", telegram_payment_id)
            await update_payment(session, payment.id, status="failed")
            raise
