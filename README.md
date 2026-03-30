# 3X-UI Telegram Bot

Telegram-бот для администрирования и продажи VPN-подписок через панель 3X-UI.

## Быстрый деплой

Рекомендуемый путь для сервера:

```bash
chmod +x install.sh
./install.sh
```

Скрипт установки:
- задаст все обязательные вопросы по Telegram и 3X-UI;
- создаст или обновит `.env`;
- при необходимости предложит установить Docker на Debian/Ubuntu;
- соберет и запустит проект через `docker compose`.

Для production рекомендуется оставлять `XUI_TLS_VERIFY=true`.
Отключайте проверку TLS только если точно понимаете риск и используете self-signed сертификат.

## Функционал

### Для пользователей:
- 🆓 Пробная подписка (1 день, 1 ГБ, 1 устройство)
- 💳 Покупка месячной подписки через Telegram Stars
- 📋 Просмотр активных подписок
- 🔄 Продление подписок через Telegram Stars
- 🔗 Получение ссылки подписки из меню

### Для администраторов:
- 📊 Статус сервера (CPU, RAM, диск, uptime)
- 👥 Просмотр последних подписок и карточки клиента
- 🛠 Управление клиентами (включить/отключить, продлить, удалить)
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
python3 bot/main.py
```

Каталоги `data/` и `logs/` будут созданы автоматически при старте.

## Docker

```bash
docker compose up -d
```

Или через новый интерактивный установщик:

```bash
./install.sh
```

## Конфигурация

См. файл `.env.example` для всех необходимых переменных окружения.

Ключевые параметры:
- `BOT_TOKEN`: токен Telegram-бота из BotFather
- `ADMIN_IDS`: Telegram ID администраторов через запятую
- `XUI_HOST`, `XUI_USERNAME`, `XUI_PASSWORD`, `XUI_INBOUND_ID`: доступ к панели 3X-UI
- `XUI_TLS_VERIFY`: проверка TLS-сертификата панели 3X-UI
- `SUBSCRIPTION_BASE_URL`: базовый URL для подписочных ссылок
- `DATABASE_URL`: путь к БД SQLite или другой SQLAlchemy-compatible DSN

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
- **APScheduler** - фоновые задачи и уведомления
- **Docker** - Контейнеризация

## Лицензия

MIT License
