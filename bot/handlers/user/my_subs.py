"""Просмотр своих подписок."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.engine import get_db
from database.crud import get_user_subscriptions, get_user
from keyboards.user_kb import (
    get_main_menu_kb,
    get_subscription_actions_kb,
    get_subscriptions_list_kb,
)
from services.subscription import SubscriptionService
from utils.helpers import format_datetime
from utils.texts import ACCESS_DENIED, SUBSCRIPTION_LINK_MESSAGE

router = Router()


@router.callback_query(F.data == "my_subs")
async def my_subscriptions(callback: CallbackQuery):
    """Показать список подписок пользователя."""
    async for session in get_db():
        user = await get_user(session, callback.from_user.id)
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        subscriptions = await get_user_subscriptions(session, user.id)

        if not subscriptions:
            text = "У вас нет активных подписок."
            kb = get_main_menu_kb()
            await callback.message.edit_text(text, reply_markup=kb)
            await callback.answer()
            return

        text = "📋 Ваши подписки:\n\n"
        for sub in subscriptions:
            status_emoji = "✅" if sub.status == "active" else "❌"
            expires_str = format_datetime(sub.expires_at) if sub.expires_at else "Бессрочно"
            traffic_text = "Безлимит" if sub.traffic_limit_gb == 0 else f"{sub.traffic_limit_gb:g} ГБ"

            text += (
                f"{status_emoji} #{sub.id} {sub.plan_type.capitalize()}\n"
                f"📅 Истекает: {expires_str}\n"
                f"📊 Лимит: {traffic_text}\n"
                f"📱 Устройств: {sub.device_limit}\n\n"
            )

        if len(subscriptions) == 1:
            kb = get_subscription_actions_kb(subscriptions[0].id, include_back=True)
        else:
            kb = get_subscriptions_list_kb([sub.id for sub in subscriptions])

        await callback.message.edit_text(text, reply_markup=kb)

        await callback.answer()


@router.callback_query(F.data.startswith("get_link:"))
async def get_subscription_link(callback: CallbackQuery):
    """Получить ссылку подписки."""
    sub_id = int(callback.data.split(":")[1])
    async for session in get_db():
        subscription_service = SubscriptionService()
        sub_url = await subscription_service.get_subscription_link(
            session,
            sub_id,
            callback.from_user.id,
        )
        if not sub_url:
            await callback.answer(ACCESS_DENIED, show_alert=True)
            return

        await callback.message.answer(
            SUBSCRIPTION_LINK_MESSAGE.format(url=sub_url),
            parse_mode="Markdown",
        )
        await callback.answer("Ссылка отправлена сообщением.", show_alert=True)
