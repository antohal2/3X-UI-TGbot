"""Сервис взаимодействия с 3X-UI API."""

from py3xui import AsyncApi, Client
from config import settings
import uuid
import time
from typing import Dict, Optional


class XUIService:
    """Сервис для работы с 3X-UI API."""

    def __init__(self):
        self.api = AsyncApi(
            settings.xui_host,
            settings.xui_username,
            settings.xui_password,
            use_tls_verify=False
        )
        self._logged_in = False

    async def ensure_login(self):
        """Убедиться, что мы залогинены."""
        if not self._logged_in:
            await self.api.login()
            self._logged_in = True

    async def create_client(
        self,
        email: str,
        traffic_gb: float = 0,
        expire_days: int = 30,
        device_limit: int = 2,
        tg_id: str = ""
    ) -> Dict:
        """Создаёт нового клиента в inbound 3X-UI."""
        await self.ensure_login()

        client_uuid = str(uuid.uuid4())
        sub_id = str(uuid.uuid4())[:8]

        expire_ms = 0
        if expire_days > 0:
            expire_ms = int((time.time() + expire_days * 86400) * 1000)

        total_bytes = int(traffic_gb * 1024 ** 3) if traffic_gb > 0 else 0

        new_client = Client(
            id=client_uuid,
            email=email,
            enable=True,
            expiry_time=expire_ms,
            total_gb=total_bytes,
            limit_ip=device_limit,
            tg_id=tg_id,
            sub_id=sub_id
        )

        await self.api.client.add(settings.xui_inbound_id, [new_client])

        return {
            "uuid": client_uuid,
            "email": email,
            "sub_id": sub_id,
            "expires_ms": expire_ms
        }

    async def renew_client(self, client_email: str, extra_days: int = 30) -> Optional[int]:
        """Продлевает подписку клиента на указанное количество дней."""
        await self.ensure_login()

        client = await self.api.client.get_by_email(client_email)
        if client:
            current_expire = client.expiry_time
            now_ms = int(time.time() * 1000)

            base_ms = max(current_expire, now_ms)
            new_expire = base_ms + (extra_days * 86400 * 1000)

            client.expiry_time = new_expire
            client.enable = True
            await self.api.client.update(client.id, client)

            return new_expire
        return None

    async def disable_client(self, client_email: str):
        """Отключает клиента (при истечении подписки)."""
        await self.ensure_login()
        client = await self.api.client.get_by_email(client_email)
        if client:
            client.enable = False
            await self.api.client.update(client.id, client)

    async def enable_client(self, client_email: str):
        """Включает клиента."""
        await self.ensure_login()
        client = await self.api.client.get_by_email(client_email)
        if client:
            client.enable = True
            await self.api.client.update(client.id, client)

    async def delete_client(self, client_email: str, inbound_id: int = None):
        """Удаляет клиента."""
        await self.ensure_login()
        inbound_id = inbound_id or settings.xui_inbound_id
        client = await self.api.client.get_by_email(client_email)
        if client:
            await self.api.client.delete(inbound_id, client.id)

    async def get_client_traffic(self, client_email: str) -> Optional[Dict]:
        """Получает статистику трафика клиента."""
        await self.ensure_login()
        client = await self.api.client.get_by_email(client_email)
        if client:
            return {
                "up": client.up,
                "down": client.down,
                "total": client.up + client.down,
                "limit": client.total_gb,
                "enable": client.enable,
                "expiry_time": client.expiry_time
            }
        return None

    async def get_server_status(self) -> Dict:
        """Получает статус сервера."""
        await self.ensure_login()
        return await self.api.server.get_status()

    async def get_inbounds(self):
        """Получает список всех inbound."""
        await self.ensure_login()
        return await self.api.inbound.get_list()

    async def get_online_clients(self):
        """Получает список клиентов онлайн."""
        await self.ensure_login()
        return await self.api.client.online()

    async def restart_xray(self):
        """Перезапускает Xray сервис."""
        await self.ensure_login()
        await self.api.server.restart_xray()