"""Админ-панель."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.admin_kb import get_admin_menu_kb
from keyboards.user_kb import get_main_menu_kb

router = Router()


@router.callback_query(F.data == "back_to_user")
async def back_to_user_menu(callback: CallbackQuery):
    """Вернуться в пользовательское меню."""
    kb = get_main_menu_kb()
    await callback.message.edit_text("Выберите действие:", reply_markup=kb)
    await callback.answer()