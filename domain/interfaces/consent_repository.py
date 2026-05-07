from abc import ABC, abstractmethod

from domain.entities.consent import UserConsent


class IConsentRepository(ABC):

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> UserConsent | None:
        ...

    @abstractmethod
    async def save(self, consent: UserConsent) -> UserConsent:
        ...

    @abstractmethod
    async def get_all(self) -> list[UserConsent]:
        ...
