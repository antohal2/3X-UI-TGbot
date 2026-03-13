"""Главное меню пользователя."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.user_kb import get_main_menu_kb, get_buy_menu_kb

router = Router()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню."""
    kb = get_main_menu_kb()
    await callback.message.edit_text("Выберите действие:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "buy_menu")
async def buy_menu(callback: CallbackQuery):
    """Меню покупки подписки."""
    kb = get_buy_menu_kb()
    await callback.message.edit_text("Выберите тарифный план:", reply_markup=kb)
    await callback.answer()