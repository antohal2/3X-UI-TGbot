"""Модели базы данных."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey, Float
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    """Базовый класс для моделей."""
    pass


class User(Base):
    """Модель пользователя."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    trial_used = Column(Boolean, default=False)  # Использована ли пробная подписка
    created_at = Column(DateTime, default=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class Subscription(Base):
    """Модель подписки."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_uuid = Column(String, unique=True, nullable=False)  # UUID клиента в 3X-UI
    client_email = Column(String, unique=True, nullable=False)  # Email клиента в 3X-UI
    sub_id = Column(String, nullable=True)  # Subscription ID для ссылки подписки
    plan_type = Column(String, nullable=False)  # "trial", "monthly"
    status = Column(String, default="active")  # "active", "expired", "disabled"
    traffic_limit_gb = Column(Float, default=0)  # 0 = безлимит
    device_limit = Column(Integer, default=2)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")


class Payment(Base):
    """Модель платежа."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    telegram_payment_id = Column(String, unique=True, nullable=False)
    amount_stars = Column(Integer, nullable=False)
    plan_type = Column(String, nullable=False)
    status = Column(String, default="completed")  # "completed", "refunded"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")