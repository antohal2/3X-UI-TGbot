"""Пробная подписка."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.engine import get_db
from services.payment import PaymentService
from keyboards.user_kb import get_main_menu_kb
from utils.texts import TRIAL_ALREADY_USED, TRIAL_SUCCESS
from config import settings

router = Router()


@router.callback_query(F.data == "trial")
async def trial_subscription(callback: CallbackQuery):
    """Обработка пробной подписки."""
    async for session in get_db():
        payment_service = PaymentService()
        result = await payment_service.process_trial_payment(session, callback.from_user.id)

        if result is None:
            await callback.answer(TRIAL_ALREADY_USED, show_alert=True)
            return

        sub_url = result["sub_url"]
        text = TRIAL_SUCCESS.format(
            days=settings.trial_duration_days,
            traffic=settings.trial_traffic_gb,
            devices=settings.trial_device_limit,
            url=sub_url
        )

        kb = get_main_menu_kb()
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        await callback.answer()
