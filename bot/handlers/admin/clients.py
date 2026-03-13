"""Управление клиентами/подписками."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from services.xui_service import XUIService
from keyboards.admin_kb import get_client_management_kb
from utils.texts import CLIENT_INFO, CLIENT_NOT_FOUND

router = Router()


@router.callback_query(F.data == "admin:clients_list")
async def clients_list(callback: CallbackQuery):
    """Показать список клиентов."""
    xui = XUIService()
    try:
        inbounds = await xui.get_inbounds()
        # Простая заглушка для списка клиентов
        text = "👥 Список клиентов:\n\n(В разработке - интеграция с 3X-UI)"
    except Exception as e:
        text = f"❌ Ошибка: {str(e)}"

    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "admin:search_client")
async def search_client(callback: CallbackQuery):
    """Поиск клиента."""
    # FSM для ввода email или telegram_id
    await callback.answer("Поиск клиента - в разработке", show_alert=True)


@router.callback_query(F.data.startswith("client:"))
async def client_action(callback: CallbackQuery):
    """Действия с клиентом."""
    action, client_email = callback.data.split(":", 2)[1], callback.data.split(":", 2)[2]
    xui = XUIService()

    try:
        if action == "enable":
            await xui.enable_client(client_email)
            text = f"✅ Клиент {client_email} включен."
        elif action == "disable":
            await xui.disable_client(client_email)
            text = f"❌ Клиент {client_email} отключен."
        elif action == "renew":
            await xui.renew_client(client_email, 30)
            text = f"🔄 Клиент {client_email} продлен на 30 дней."
        elif action == "delete":
            await xui.delete_client(client_email)
            text = f"🗑️ Клиент {client_email} удален."
        else:
            text = "Неизвестное действие."
    except Exception as e:
        text = f"❌ Ошибка: {str(e)}"

    await callback.message.edit_text(text)
    await callback.answer()