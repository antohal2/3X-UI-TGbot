"""Рассылка сообщений пользователям."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.engine import get_db
from database.crud import get_all_users
from utils.texts import BROADCAST_PROMPT, BROADCAST_SUCCESS

router = Router()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


@router.callback_query(F.data == "admin:broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Начать рассылку."""
    await callback.message.edit_text(BROADCAST_PROMPT)
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.answer()


@router.message(BroadcastState.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    """Обработать сообщение для рассылки."""
    broadcast_text = message.text

    async for session in get_db():
        users = await get_all_users(session)
        count = 0
        for user in users:
            try:
                await message.bot.send_message(user.telegram_id, broadcast_text)
                count += 1
            except Exception:
                pass  # Игнорировать ошибки отправки

    text = BROADCAST_SUCCESS.format(count=count)
    await message.answer(text)
    await state.clear()
