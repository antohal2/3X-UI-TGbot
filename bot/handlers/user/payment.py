"""Обработка Telegram Stars платежей."""

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice,
    PreCheckoutQuery, ContentType
)
from sqlalchemy.ext.asyncio import AsyncSession
import time

from config import settings
from database.engine import get_db
from services.payment import PaymentService
from keyboards.user_kb import get_main_menu_kb
from utils.texts import PAYMENT_SUCCESS, UNKNOWN_PLAN

router = Router()


@router.callback_query(F.data.startswith("buy:"))
async def process_buy(callback: CallbackQuery):
    """Обработка нажатия кнопки покупки."""
    plan_type = callback.data.split(":")[1]  # "trial" или "monthly"

    if plan_type == "trial":
        # Пробная обрабатывается отдельно
        await callback.answer("Используйте кнопку 'Пробная подписка'", show_alert=True)
        return
    elif plan_type == "monthly":
        price = settings.monthly_price_stars
        title = "Подписка VPN на 30 дней"
        description = "30 дней, безлимитный трафик, 2 устройства"
    else:
        await callback.answer(UNKNOWN_PLAN, show_alert=True)
        return

    prices = [LabeledPrice(label="XTR", amount=price)]

    await callback.message.answer_invoice(
        title=title,
        description=description,
        payload=f"sub_{plan_type}_{callback.from_user.id}",
        currency="XTR",  # Telegram Stars
        prices=prices,
        provider_token=""  # Для XTR токен пустой
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Проверка перед оплатой. Подтверждаем все платежи."""
    # Здесь можно добавить дополнительные проверки
    await pre_checkout_query.answer(ok=True)


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: Message):
    """Обработка успешного платежа."""
    payment = message.successful_payment
    payload_parts = payment.invoice_payload.split("_")
    plan_type = payload_parts[1]
    user_tg_id = int(payload_parts[2])

    async for session in get_db():
        payment_service = PaymentService()
        result = await payment_service.process_monthly_payment(
            session, user_tg_id, payment.telegram_payment_charge_id, payment.total_amount
        )

        sub_url = result["sub_url"]
        text = PAYMENT_SUCCESS.format(plan=plan_type, url=sub_url)

        kb = get_main_menu_kb()
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")