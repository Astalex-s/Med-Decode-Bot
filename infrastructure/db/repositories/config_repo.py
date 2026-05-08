from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models import BotConfig


class ConfigRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str, default: str | None = None) -> str | None:
        result = await self.session.execute(select(BotConfig).where(BotConfig.key == key))
        row = result.scalar_one_or_none()
        return row.value if row else default

    async def set(self, key: str, value: str) -> None:
        result = await self.session.execute(select(BotConfig).where(BotConfig.key == key))
        row = result.scalar_one_or_none()
        if row:
            row.value = value
        else:
            self.session.add(BotConfig(key=key, value=value))
        await self.session.commit()
