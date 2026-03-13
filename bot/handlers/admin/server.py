"""Управление сервером."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from services.xui_service import XUIService
from utils.texts import SERVER_STATUS

router = Router()


@router.callback_query(F.data == "admin:server_status")
async def server_status(callback: CallbackQuery):
    """Показать статус сервера."""
    xui = XUIService()
    try:
        status = await xui.get_server_status()
        online = await xui.get_online_clients()

        text = SERVER_STATUS.format(
            cpu=status.get("cpu", "N/A"),
            ram=status.get("mem", {}).get("current", "N/A"),
            disk=status.get("disk", {}).get("current", "N/A"),
            uptime=status.get("uptime", "N/A"),
            xray_version=status.get("xray", {}).get("version", "N/A"),
            online_clients=len(online) if online else 0
        )
    except Exception as e:
        text = f"❌ Ошибка получения статуса: {str(e)}"

    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "admin:restart_xray")
async def restart_xray(callback: CallbackQuery):
    """Перезапустить Xray."""
    xui = XUIService()
    try:
        await xui.restart_xray()
        text = "✅ Xray перезапущен успешно."
    except Exception as e:
        text = f"❌ Ошибка перезапуска: {str(e)}"

    await callback.message.edit_text(text)
    await callback.answer()