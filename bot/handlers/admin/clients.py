"""Управление клиентами/подписками."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime

from database.crud import get_recent_subscriptions, get_subscription_by_email, get_subscription_by_id, update_subscription
from database.engine import get_db
from services.xui_service import XUIService
from keyboards.admin_kb import get_admin_back_kb, get_client_management_kb, get_clients_list_kb
from utils.helpers import format_bytes, format_datetime
from utils.texts import CLIENT_INFO, CLIENT_NOT_FOUND

router = Router()


@router.callback_query(F.data == "admin:clients_list")
async def clients_list(callback: CallbackQuery):
    """Показать список клиентов."""
    async for session in get_db():
        subscriptions = await get_recent_subscriptions(session, limit=10)

    if not subscriptions:
        await callback.message.edit_text(
            "👥 Подписок пока нет.",
            reply_markup=get_admin_back_kb(),
        )
        await callback.answer()
        return

    text = "👥 Последние подписки:\n\n"
    for sub in subscriptions:
        user_label = sub.user.telegram_id if sub.user else "N/A"
        expires_at = format_datetime(sub.expires_at)
        text += (
            f"• #{sub.id} {sub.client_email}\n"
            f"  Статус: {sub.status}\n"
            f"  Telegram ID: {user_label}\n"
            f"  Истекает: {expires_at}\n\n"
        )

    kb = get_clients_list_kb([(sub.id, sub.client_email) for sub in subscriptions])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "admin:search_client")
async def search_client(callback: CallbackQuery):
    """Поиск клиента."""
    await callback.answer(
        "Используйте список последних подписок. Поиск отдельной формой пока не добавлен.",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("admin:client:"))
async def show_client(callback: CallbackQuery):
    """Показать карточку клиента."""
    subscription_id = int(callback.data.split(":")[2])

    async for session in get_db():
        subscription = await get_subscription_by_id(session, subscription_id, load_user=True)

    if not subscription:
        await callback.answer(CLIENT_NOT_FOUND, show_alert=True)
        return

    xui = XUIService()
    try:
        traffic = await xui.get_client_traffic(subscription.client_email)
    except Exception:
        traffic = None

    up = format_bytes(traffic["up"]) if traffic else "0 B"
    down = format_bytes(traffic["down"]) if traffic else "0 B"
    total = format_bytes(traffic["total"]) if traffic else "0 B"
    status = subscription.status
    if traffic:
        status = "active" if traffic["enable"] else "disabled"

    text = CLIENT_INFO.format(
        email=subscription.client_email,
        up=up,
        down=down,
        total=total,
        expires=format_datetime(subscription.expires_at),
        devices=subscription.device_limit,
        status=status,
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_client_management_kb(subscription.client_email),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("client:"))
async def client_action(callback: CallbackQuery):
    """Действия с клиентом."""
    _, action, client_email = callback.data.split(":", 2)
    xui = XUIService()

    try:
        if action == "enable":
            await xui.enable_client(client_email)
            async for session in get_db():
                subscription = await get_subscription_by_email(session, client_email)
                if subscription:
                    await update_subscription(session, subscription.id, status="active")
            text = f"✅ Клиент {client_email} включен."
        elif action == "disable":
            await xui.disable_client(client_email)
            async for session in get_db():
                subscription = await get_subscription_by_email(session, client_email)
                if subscription:
                    await update_subscription(session, subscription.id, status="disabled")
            text = f"❌ Клиент {client_email} отключен."
        elif action == "renew":
            new_expire_ms = await xui.renew_client(client_email, 30)
            async for session in get_db():
                subscription = await get_subscription_by_email(session, client_email)
                if subscription and new_expire_ms:
                    await update_subscription(
                        session,
                        subscription.id,
                        status="active",
                        expires_at=datetime.utcfromtimestamp(new_expire_ms / 1000),
                    )
            text = f"🔄 Клиент {client_email} продлен на 30 дней."
        elif action == "delete":
            await xui.delete_client(client_email)
            async for session in get_db():
                subscription = await get_subscription_by_email(session, client_email)
                if subscription:
                    await update_subscription(session, subscription.id, status="disabled")
            text = f"🗑️ Клиент {client_email} удален."
        else:
            text = "Неизвестное действие."
    except Exception as e:
        text = f"❌ Ошибка: {str(e)}"

    reply_markup = get_admin_back_kb() if action == "delete" else get_client_management_kb(client_email)
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()
