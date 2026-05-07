from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class User:
    telegram_id: int
    username: str | None = None
    analyses_used: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None
