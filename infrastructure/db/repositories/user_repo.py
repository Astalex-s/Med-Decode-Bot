from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.user import User
from domain.entities.subscription import Subscription
from domain.interfaces.user_repository import IUserRepository
from infrastructure.db.models import User as UserModel, Subscription as SubscriptionModel


class UserRepository(IUserRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.telegram_id == telegram_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return User(
            id=row.id,
            telegram_id=row.telegram_id,
            username=row.username,
            analyses_used=row.analyses_used,
            created_at=row.created_at,
        )

    async def create(self, user: User) -> User:
        db_user = UserModel(
            telegram_id=user.telegram_id,
            username=user.username,
            analyses_used=user.analyses_used,
        )
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        user.id = db_user.id
        return user

    async def increment_analyses_used(self, telegram_id: int) -> None:
        await self.session.execute(
            update(UserModel)
            .where(UserModel.telegram_id == telegram_id)
            .values(analyses_used=UserModel.analyses_used + 1)
        )
        await self.session.commit()

    async def get_subscription(self, user_id: int) -> Subscription | None:
        result = await self.session.execute(
            select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return Subscription(
            id=row.id,
            user_id=row.user_id,
            is_active=row.is_active,
            plan=row.plan,
            expires_at=row.expires_at,
        )

    async def create_subscription(self, subscription: Subscription) -> Subscription:
        db_sub = SubscriptionModel(
            user_id=subscription.user_id,
            is_active=subscription.is_active,
            plan=subscription.plan,
            expires_at=subscription.expires_at,
        )
        self.session.add(db_sub)
        await self.session.commit()
        await self.session.refresh(db_sub)
        subscription.id = db_sub.id
        return subscription

    async def update_subscription(self, subscription: Subscription) -> Subscription:
        await self.session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.id == subscription.id)
            .values(
                is_active=subscription.is_active,
                plan=subscription.plan,
                expires_at=subscription.expires_at,
            )
        )
        await self.session.commit()
        return subscription
