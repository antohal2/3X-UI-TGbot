"""CRUD-операции для базы данных."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta

from .models import User, Subscription, Payment


# Пользователи
async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Получить пользователя по Telegram ID."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, telegram_id: int, username: str = None, full_name: str = None) -> User:
    """Создать нового пользователя."""
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(session: AsyncSession, telegram_id: int, **kwargs) -> bool:
    """Обновить данные пользователя."""
    result = await session.execute(
        update(User).where(User.telegram_id == telegram_id).values(**kwargs)
    )
    await session.commit()
    return result.rowcount > 0


async def get_all_users(session: AsyncSession) -> List[User]:
    """Получить всех пользователей."""
    result = await session.execute(select(User))
    return result.scalars().all()


# Подписки
async def get_user_subscriptions(session: AsyncSession, user_id: int) -> List[Subscription]:
    """Получить все подписки пользователя."""
    result = await session.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    return result.scalars().all()


async def create_subscription(
    session: AsyncSession,
    user_id: int,
    client_uuid: str,
    client_email: str,
    sub_id: str,
    plan_type: str,
    traffic_limit_gb: float,
    device_limit: int,
    expires_at: datetime,
) -> Subscription:
    """Создать новую подписку."""
    subscription = Subscription(
        user_id=user_id,
        client_uuid=client_uuid,
        client_email=client_email,
        sub_id=sub_id,
        plan_type=plan_type,
        traffic_limit_gb=traffic_limit_gb,
        device_limit=device_limit,
        expires_at=expires_at,
    )
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def update_subscription(session: AsyncSession, subscription_id: int, **kwargs) -> bool:
    """Обновить подписку."""
    result = await session.execute(
        update(Subscription).where(Subscription.id == subscription_id).values(**kwargs)
    )
    await session.commit()
    return result.rowcount > 0


async def get_subscription_by_id(session: AsyncSession, subscription_id: int) -> Optional[Subscription]:
    """Получить подписку по ID."""
    result = await session.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    return result.scalar_one_or_none()


async def get_expired_active_subscriptions(session: AsyncSession) -> List[Subscription]:
    """Получить активные подписки, которые истекли."""
    now = datetime.utcnow()
    result = await session.execute(
        select(Subscription).where(
            Subscription.status == "active",
            Subscription.expires_at < now
        )
    )
    return result.scalars().all()


async def get_expiring_subscriptions(session: AsyncSession, days: int = 3) -> List[Subscription]:
    """Получить подписки, истекающие через N дней."""
    now = datetime.utcnow()
    future = now + timedelta(days=days)
    result = await session.execute(
        select(Subscription).where(
            Subscription.status == "active",
            Subscription.expires_at.between(now, future)
        )
    )
    return result.scalars().all()


# Платежи
async def create_payment(
    session: AsyncSession,
    user_id: int,
    subscription_id: Optional[int],
    telegram_payment_id: str,
    amount_stars: int,
    plan_type: str,
) -> Payment:
    """Создать новый платеж."""
    payment = Payment(
        user_id=user_id,
        subscription_id=subscription_id,
        telegram_payment_id=telegram_payment_id,
        amount_stars=amount_stars,
        plan_type=plan_type,
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def get_user_payments(session: AsyncSession, user_id: int) -> List[Payment]:
    """Получить все платежи пользователя."""
    result = await session.execute(
        select(Payment).where(Payment.user_id == user_id)
    )
    return result.scalars().all()


async def get_all_payments(session: AsyncSession) -> List[Payment]:
    """Получить все платежи."""
    result = await session.execute(select(Payment))
    return result.scalars().all()