"""Продление подписки."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice

from config import settings
from database.crud import get_subscription_by_id, get_user
from database.engine import get_db
from utils.texts import ACCESS_DENIED

router = Router()


@router.callback_query(F.data.startswith("renew:"))
async def renew_subscription(callback: CallbackQuery):
    """Продлить подписку."""
    sub_id = int(callback.data.split(":")[1])

    async for session in get_db():
        user = await get_user(session, callback.from_user.id)
        subscription = await get_subscription_by_id(session, sub_id)
        if not user or not subscription or subscription.user_id != user.id:
            await callback.answer(ACCESS_DENIED, show_alert=True)
            return

    prices = [LabeledPrice(label="XTR", amount=settings.monthly_price_stars)]

    await callback.message.answer_invoice(
        title="Продление VPN-подписки",
        description=f"Продление подписки #{sub_id} на {settings.monthly_duration_days} дней",
        payload=f"renew:{sub_id}:{callback.from_user.id}",
        currency="XTR",
        prices=prices,
        provider_token=""
    )
    await callback.answer()
