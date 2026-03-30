"""Обработка Telegram Stars платежей."""

import logging
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice,
    PreCheckoutQuery, ContentType
)

from config import settings
from database.engine import get_db
from services.payment import PaymentService
from keyboards.user_kb import get_main_menu_kb
from utils.helpers import format_datetime
from utils.texts import PAYMENT_SUCCESS, RENEWAL_SUCCESS, UNKNOWN_PLAN

router = Router()
logger = logging.getLogger(__name__)


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
        payload=f"purchase:{plan_type}:{callback.from_user.id}",
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
    payload_parts = payment.invoice_payload.split(":")
    if len(payload_parts) != 3:
        await message.answer("Не удалось обработать платёж: некорректный payload.")
        return

    action, target, user_tg_id_raw = payload_parts
    user_tg_id = int(user_tg_id_raw)
    if message.from_user.id != user_tg_id:
        await message.answer("Не удалось подтвердить владельца платежа.")
        return

    async for session in get_db():
        payment_service = PaymentService()
        try:
            if action == "purchase" and target == "monthly":
                result = await payment_service.process_monthly_payment(
                    session, user_tg_id, payment.telegram_payment_charge_id, payment.total_amount
                )

                sub_url = result["sub_url"]
                text = PAYMENT_SUCCESS.format(plan="Месячная подписка", url=sub_url)
            elif action == "renew":
                result = await payment_service.process_renewal_payment(
                    session,
                    user_tg_id,
                    int(target),
                    payment.telegram_payment_charge_id,
                    payment.total_amount,
                    settings.monthly_duration_days,
                )
                if result is None:
                    await message.answer("Не удалось продлить подписку. Попробуйте позже.")
                    return

                sub_url = result["sub_url"]
                text = RENEWAL_SUCCESS.format(
                    expires_at=format_datetime(result["subscription"].expires_at),
                    url=sub_url,
                )
            else:
                await message.answer(UNKNOWN_PLAN)
                return
        except Exception as exc:
            logger.exception("Ошибка при обработке успешного платежа %s", payment.telegram_payment_charge_id)
            await message.answer(
                "Платеж получен, но выдача подписки завершилась ошибкой. "
                "Пожалуйста, свяжитесь с администратором и передайте ID платежа: "
                f"`{payment.telegram_payment_charge_id}`",
                parse_mode="Markdown",
            )
            return

        kb = get_main_menu_kb()
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
