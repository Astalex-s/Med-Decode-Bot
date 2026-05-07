from dataclasses import dataclass
from datetime import datetime


@dataclass
class Subscription:
    user_id: int
    is_active: bool = False
    plan: str = "free"
    expires_at: datetime | None = None
    id: int | None = None
