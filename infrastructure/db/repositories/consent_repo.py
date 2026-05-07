from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.consent import UserConsent
from domain.interfaces.consent_repository import IConsentRepository
from infrastructure.db.models import UserConsent as ConsentModel


class ConsentRepository(IConsentRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> UserConsent | None:
        result = await self.session.execute(
            select(ConsentModel).where(ConsentModel.telegram_id == telegram_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    async def save(self, consent: UserConsent) -> UserConsent:
        existing = await self.session.execute(
            select(ConsentModel).where(ConsentModel.telegram_id == consent.telegram_id)
        )
        row = existing.scalar_one_or_none()

        if row is None:
            db_obj = ConsentModel(
                telegram_id=consent.telegram_id,
                full_name=consent.full_name,
                username=consent.username,
                agreed=consent.agreed,
                agreed_at=consent.agreed_at,
                declined_at=consent.declined_at,
            )
            self.session.add(db_obj)
        else:
            await self.session.execute(
                update(ConsentModel)
                .where(ConsentModel.telegram_id == consent.telegram_id)
                .values(
                    agreed=consent.agreed,
                    agreed_at=consent.agreed_at,
                    declined_at=consent.declined_at,
                    full_name=consent.full_name,
                    username=consent.username,
                )
            )

        await self.session.commit()
        return consent

    async def get_all(self) -> list[UserConsent]:
        result = await self.session.execute(
            select(ConsentModel).order_by(ConsentModel.created_at.desc())
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    @staticmethod
    def _to_entity(row: ConsentModel) -> UserConsent:
        return UserConsent(
            id=row.id,
            telegram_id=row.telegram_id,
            full_name=row.full_name,
            username=row.username,
            agreed=row.agreed,
            agreed_at=row.agreed_at,
            declined_at=row.declined_at,
            created_at=row.created_at,
        )
