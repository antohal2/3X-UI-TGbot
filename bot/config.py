"""Конфигурация приложения."""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения."""

    # Telegram Bot
    bot_token: str = Field(..., env="BOT_TOKEN")
    admin_ids: str = Field("", env="ADMIN_IDS")

    # 3X-UI Panel
    xui_host: str = Field(..., env="XUI_HOST")
    xui_username: str = Field(..., env="XUI_USERNAME")
    xui_password: str = Field(..., env="XUI_PASSWORD")
    xui_inbound_id: int = Field(..., env="XUI_INBOUND_ID")

    # Подписки
    subscription_base_url: str = Field(..., env="SUBSCRIPTION_BASE_URL")

    # Тарифы (в Telegram Stars)
    trial_duration_days: int = Field(1, env="TRIAL_DURATION_DAYS")
    trial_traffic_gb: float = Field(1.0, env="TRIAL_TRAFFIC_GB")
    trial_device_limit: int = Field(1, env="TRIAL_DEVICE_LIMIT")

    monthly_price_stars: int = Field(50, env="MONTHLY_PRICE_STARS")
    monthly_duration_days: int = Field(30, env="MONTHLY_DURATION_DAYS")
    monthly_traffic_gb: float = Field(0.0, env="MONTHLY_TRAFFIC_GB")
    monthly_device_limit: int = Field(2, env="MONTHLY_DEVICE_LIMIT")

    # База данных
    database_url: str = Field("sqlite+aiosqlite:///./data/bot.db", env="DATABASE_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def admin_ids_list(self) -> List[int]:
        """Список ID администраторов."""
        if not self.admin_ids:
            return []
        return [int(id_str.strip()) for id_str in self.admin_ids.split(",") if id_str.strip().isdigit()]


# Глобальный экземпляр настроек
settings = Settings()