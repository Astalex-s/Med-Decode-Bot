from abc import ABC, abstractmethod

from domain.entities.analysis import Analysis


class IAnalysisRepository(ABC):

    @abstractmethod
    async def save(self, analysis: Analysis) -> Analysis:
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> list[Analysis]:
        ...
