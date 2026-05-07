from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class UserConsent:
    telegram_id: int
    agreed: bool = False
    full_name: str | None = None
    username: str | None = None
    agreed_at: datetime | None = None
    declined_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None
