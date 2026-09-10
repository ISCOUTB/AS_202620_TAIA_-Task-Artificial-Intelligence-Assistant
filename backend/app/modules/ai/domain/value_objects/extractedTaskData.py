from dataclasses import dataclass, field
from enum import Enum
from datetime import date, datetime, timezone

@dataclass
class ExtractedTaskData:
    id: str
    tittle: str
    due_date: datetime=field(default_factory=lambda: datetime(timezone.utc))
    subject: str | None=None
    descrption: str | None=None
    created_at: datetime=field(default_factory=lambda: datetime(timezone.utc))