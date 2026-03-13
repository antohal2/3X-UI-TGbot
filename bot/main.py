"""Точка входа, инициализация бота и диспетчера."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import settings
from database.engine import create_tables
from services.scheduler import setup_scheduler
from middlewares.auth import AuthMiddleware
from middlewares.throttling import ThrottlingMiddleware

# Импорт хендлеров
from handlers.start import router as start_router
from handlers.user.menu import router as user_menu_router
from handlers.user.trial import router as trial_router
from handlers.user.payment import router as payment_router
from handlers.user.my_subs import router as my_subs_router
from handlers.user.renew import router as renew_router
from handlers.admin.menu import router as admin_menu_router
from handlers.admin.server import router as server_router
from handlers.admin.clients import router as clients_router
from handlers.admin.stats import router as stats_router
from handlers.admin.broadcast import router as broadcast_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция."""
    # Создание таблиц БД
    await create_tables()
    logger.info("База данных инициализирована.")

    # Инициализация бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()

    # Регистрация middleware
    dp.message.middleware(ThrottlingMiddleware(rate_limit=1.0))
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=1.0))

    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(user_menu_router)
    dp.include_router(trial_router)
    dp.include_router(payment_router)
    dp.include_router(my_subs_router)
    dp.include_router(renew_router)

    # Админ роутеры с middleware
    admin_menu_router.message.middleware(AuthMiddleware(admin_only=True))
    admin_menu_router.callback_query.middleware(AuthMiddleware(admin_only=True))
    server_router.message.middleware(AuthMiddleware(admin_only=True))
    server_router.callback_query.middleware(AuthMiddleware(admin_only=True))
    clients_router.message.middleware(AuthMiddleware(admin_only=True))
    clients_router.callback_query.middleware(AuthMiddleware(admin_only=True))
    stats_router.message.middleware(AuthMiddleware(admin_only=True))
    stats_router.callback_query.middleware(AuthMiddleware(admin_only=True))
    broadcast_router.message.middleware(AuthMiddleware(admin_only=True))
    broadcast_router.callback_query.middleware(AuthMiddleware(admin_only=True))

    dp.include_router(admin_menu_router)
    dp.include_router(server_router)
    dp.include_router(clients_router)
    dp.include_router(stats_router)
    dp.include_router(broadcast_router)
    admin_router.message.middleware(AuthMiddleware(admin_only=True))
    admin_router.callback_query.middleware(AuthMiddleware(admin_only=True))

    dp.include_router(admin_router)
    dp.include_router(server.router)
    dp.include_router(clients.router)
    dp.include_router(stats.router)
    dp.include_router(broadcast.router)

    # Настройка планировщика
    setup_scheduler(bot)

    logger.info("Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())