"""Anti-flood middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from collections import defaultdict
import time


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты сообщений."""

    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit  # секунды между сообщениями
        self.user_last_message = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = time.time()

        if now - self.user_last_message[user_id] < self.rate_limit:
            if isinstance(event, CallbackQuery):
                await event.answer("Слишком часто. Попробуйте через секунду.")
            return

        self.user_last_message[user_id] = now
        return await handler(event, data)
