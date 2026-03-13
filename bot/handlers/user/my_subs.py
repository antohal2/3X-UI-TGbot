"""Просмотр своих подписок."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import get_db
from database.crud import get_user_subscriptions, get_user
from keyboards.user_kb import get_main_menu_kb, get_subscription_actions_kb
from utils.helpers import format_bytes, format_datetime
from datetime import datetime

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

            text += (
                f"{status_emoji} {sub.plan_type.capitalize()}\n"
                f"📅 Истекает: {expires_str}\n"
                f"📊 Лимит: {sub.traffic_limit_gb} ГБ\n"
                f"📱 Устройств: {sub.device_limit}\n\n"
            )

            # Кнопки для каждой подписки
            kb = get_subscription_actions_kb(sub.id)
            await callback.message.edit_text(text, reply_markup=kb)

        await callback.answer()


@router.callback_query(F.data.startswith("get_link:"))
async def get_subscription_link(callback: CallbackQuery):
    """Получить ссылку подписки."""
    sub_id = int(callback.data.split(":")[1])
    # Получить sub_id из БД
    async for session in get_db():
        from database.crud import get_subscription_by_id  # Нужно добавить эту функцию
        # subscription = await get_subscription_by_id(session, sub_id)
        # if subscription:
        #     sub_url = f"{settings.subscription_base_url}{subscription.sub_id}"
        #     await callback.answer(f"Ссылка: {sub_url}", show_alert=True)
        # else:
        #     await callback.answer("Подписка не найдена", show_alert=True)
        await callback.answer("Ссылка: https://example.com/sub/12345678", show_alert=True)