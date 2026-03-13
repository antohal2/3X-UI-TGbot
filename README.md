# 3X-UI Telegram Bot

Telegram-бот для администрирования и продажи VPN-подписок через панель 3X-UI.

## Функционал

### Для пользователей:
- 🆓 Пробная подписка (1 день, 1 ГБ, 1 устройство)
- 💳 Покупка месячной подписки через Telegram Stars
- 📋 Просмотр активных подписок
- 🔄 Продление подписок
- 🔗 Получение ссылок подписки

### Для администраторов:
- 📊 Статус сервера (CPU, RAM, диск, uptime)
- 👥 Управление клиентами (включить/отключить, продлить, удалить)
- 🔍 Поиск клиентов
- 🔄 Перезапуск Xray
- 📤 Рассылка сообщений
- 📈 Статистика

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/antohal2/3X-UI-TGbot.git
cd 3X-UI-TGbot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл
```

5. Запустите бота:
```bash
python bot/main.py
```

## Docker

```bash
docker-compose up -d
```

## Конфигурация

См. файл `.env.example` для всех необходимых переменных окружения.

## Структура проекта

```
3xui-bot/
├── bot/
│   ├── main.py              # Точка входа
│   ├── config.py             # Конфигурация
│   ├── middlewares/         # Middleware
│   ├── handlers/            # Обработчики команд
│   ├── services/            # Бизнес-логика
│   ├── database/            # Модели и CRUD
│   ├── keyboards/           # Клавиатуры
│   └── utils/               # Утилиты
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Технологии

- **Python 3.11+**
- **aiogram 3.x** - Telegram Bot Framework
- **py3xui** - 3X-UI API SDK
- **SQLAlchemy** - ORM для базы данных
- **SQLite** - База данных
- **Docker** - Контейнеризация

## Лицензия

MIT License