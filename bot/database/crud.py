"""CRUD-операции для базы данных."""

from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from .models import User, Subscription, Payment


# Пользователи
async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Получить пользователя по Telegram ID."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str = None,
    full_name: str = None,
    is_admin: bool = False,
) -> User:
    """Создать нового пользователя."""
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        is_admin=is_admin,
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
    result = await session.execute(
        select(User)
        .options(selectinload(User.subscriptions))
        .order_by(User.created_at.desc())
    )
    return result.scalars().all()


# Подписки
async def get_user_subscriptions(session: AsyncSession, user_id: int) -> List[Subscription]:
    """Получить все подписки пользователя."""
    result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
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


async def get_subscription_by_id(
    session: AsyncSession,
    subscription_id: int,
    load_user: bool = False,
) -> Optional[Subscription]:
    """Получить подписку по ID."""
    query = select(Subscription).where(Subscription.id == subscription_id)
    if load_user:
        query = query.options(selectinload(Subscription.user))

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_subscription_by_email(
    session: AsyncSession,
    client_email: str,
    load_user: bool = False,
) -> Optional[Subscription]:
    """Получить подписку по email клиента 3X-UI."""
    query = select(Subscription).where(Subscription.client_email == client_email)
    if load_user:
        query = query.options(selectinload(Subscription.user))

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_recent_subscriptions(session: AsyncSession, limit: int = 10) -> List[Subscription]:
    """Получить последние подписки для админ-панели."""
    result = await session.execute(
        select(Subscription)
        .options(selectinload(Subscription.user))
        .order_by(Subscription.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def count_active_subscriptions(session: AsyncSession) -> int:
    """Подсчитать количество активных подписок."""
    result = await session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.status == "active")
    )
    return int(result or 0)


async def get_expired_active_subscriptions(session: AsyncSession) -> List[Subscription]:
    """Получить активные подписки, которые истекли."""
    now = datetime.utcnow()
    result = await session.execute(
        select(Subscription)
        .options(selectinload(Subscription.user))
        .where(
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
        select(Subscription)
        .options(selectinload(Subscription.user))
        .where(
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
    status: str = "completed",
) -> Payment:
    """Создать новый платеж."""
    payment = Payment(
        user_id=user_id,
        subscription_id=subscription_id,
        telegram_payment_id=telegram_payment_id,
        amount_stars=amount_stars,
        plan_type=plan_type,
        status=status,
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def update_payment(session: AsyncSession, payment_id: int, **kwargs: Any) -> bool:
    """Обновить платеж."""
    result = await session.execute(
        update(Payment).where(Payment.id == payment_id).values(**kwargs)
    )
    await session.commit()
    return result.rowcount > 0


async def get_payment_by_telegram_payment_id(
    session: AsyncSession,
    telegram_payment_id: str,
    load_subscription: bool = False,
) -> Optional[Payment]:
    """Получить платеж по Telegram payment charge id."""
    query = select(Payment).where(Payment.telegram_payment_id == telegram_payment_id)
    if load_subscription:
        query = query.options(selectinload(Payment.subscription))

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_user_payments(session: AsyncSession, user_id: int) -> List[Payment]:
    """Получить все платежи пользователя."""
    result = await session.execute(
        select(Payment).where(Payment.user_id == user_id)
    )
    return result.scalars().all()


async def get_all_payments(session: AsyncSession) -> List[Payment]:
    """Получить все платежи."""
    result = await session.execute(
        select(Payment).order_by(Payment.created_at.desc())
    )
    return result.scalars().all()
