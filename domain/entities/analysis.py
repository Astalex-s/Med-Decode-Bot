from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Analysis:
    user_id: int
    file_type: str  # "photo" or "pdf"
    result_text: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None
