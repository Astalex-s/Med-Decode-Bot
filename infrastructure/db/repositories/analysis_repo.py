from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.analysis import Analysis
from domain.interfaces.analysis_repository import IAnalysisRepository
from infrastructure.db.models import AnalysisHistory as AnalysisModel


class AnalysisRepository(IAnalysisRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, analysis: Analysis) -> Analysis:
        db_analysis = AnalysisModel(
            user_id=analysis.user_id,
            file_type=analysis.file_type,
            result_text=analysis.result_text,
        )
        self.session.add(db_analysis)
        await self.session.commit()
        await self.session.refresh(db_analysis)
        analysis.id = db_analysis.id
        return analysis

    async def get_by_user_id(self, user_id: int) -> list[Analysis]:
        result = await self.session.execute(
            select(AnalysisModel)
            .where(AnalysisModel.user_id == user_id)
            .order_by(AnalysisModel.created_at.desc())
        )
        rows = result.scalars().all()
        return [
            Analysis(
                id=row.id,
                user_id=row.user_id,
                file_type=row.file_type,
                result_text=row.result_text,
                created_at=row.created_at,
            )
            for row in rows
        ]
