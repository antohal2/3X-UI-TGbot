"""Обработчик /start."""

from aiogram import Router, F
from aiogram.types import Message

from database.crud import create_user, get_user, update_user
from database.engine import get_db
from keyboards.user_kb import get_main_menu_kb
from keyboards.admin_kb import get_admin_menu_kb
from config import settings
from utils.texts import WELCOME_MESSAGE

router = Router()


@router.message(F.text == "/start")
async def start_command(message: Message):
    """Обработчик команды /start."""
    async for session in get_db():
        user_id = message.from_user.id
        username = message.from_user.username
        full_name = message.from_user.full_name

        is_admin = user_id in settings.admin_ids_list

        # Регистрация пользователя, если не существует
        user = await get_user(session, user_id)
        if not user:
            user = await create_user(session, user_id, username, full_name, is_admin=is_admin)
        else:
            await update_user(
                session,
                user_id,
                username=username,
                full_name=full_name,
                is_admin=is_admin,
            )

        if is_admin:
            # Админ меню
            kb = get_admin_menu_kb()
        else:
            # Пользовательское меню
            kb = get_main_menu_kb()

        await message.answer(WELCOME_MESSAGE, reply_markup=kb)
