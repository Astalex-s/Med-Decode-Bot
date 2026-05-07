from abc import ABC, abstractmethod

from domain.entities.user import User
from domain.entities.subscription import Subscription


class IUserRepository(ABC):

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        ...

    @abstractmethod
    async def create(self, user: User) -> User:
        ...

    @abstractmethod
    async def increment_analyses_used(self, telegram_id: int) -> None:
        ...

    @abstractmethod
    async def get_subscription(self, user_id: int) -> Subscription | None:
        ...

    @abstractmethod
    async def create_subscription(self, subscription: Subscription) -> Subscription:
        ...

    @abstractmethod
    async def update_subscription(self, subscription: Subscription) -> Subscription:
        ...
