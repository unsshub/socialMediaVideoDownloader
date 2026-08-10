from dataclasses import dataclass, field
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
from enum import Enum


class JobState(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DONE = "done"
    FAILED = "failed"


class Failure(str, Enum):
    UNSUPPORTED_URL = "unsupported_url"
    PRIVATE = "private"
    UNAVAILABLE = "unavailable"
    NETWORK = "network_error"
    OTHER = "failed_other"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


@dataclass
class Job:
    id: str
    url: str
    state: JobState = JobState.PENDING
    progress: float = 0.0
    filename: str | None = None
    error: Failure | None = None
    message: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    finished_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "state": self.state.value,
            "progress": self.progress,
            "filename": self.filename,
            "error": self.error.value if self.error else None,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }
