"""Middleware проверки ролей (admin/user)."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from config import settings


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки ролей пользователей."""

    def __init__(self, admin_only: bool = False):
        self.admin_only = admin_only

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id

        if self.admin_only:
            if user_id not in settings.admin_ids_list:
                # Игнорировать сообщение от не-админа
                return

        # Для обычных хендлеров проверка не требуется
        return await handler(event, data)