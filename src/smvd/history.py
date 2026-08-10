from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from .jobs import Failure, Job, JobState


class HistoryStore:
    """SQLite store of finished Jobs, capped at the most recent K entries."""

    def __init__(self, db_path: Path, cap: int = 100):
        self.db_path = Path(db_path)
        self.cap = cap
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                state TEXT NOT NULL,
                progress REAL NOT NULL DEFAULT 0,
                filename TEXT,
                error TEXT,
                message TEXT,
                created_at TEXT NOT NULL,
                finished_at TEXT
            )
            """
        )
        self._conn.commit()

    def record(self, job: Job) -> None:
        self._conn.execute(
            """
            INSERT INTO history (id, url, state, progress, filename, error, message, created_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                state=excluded.state, progress=excluded.progress, filename=excluded.filename,
                error=excluded.error, message=excluded.message, finished_at=excluded.finished_at
            """,
            (
                job.id,
                job.url,
                job.state.value,
                job.progress,
                job.filename,
                job.error.value if job.error else None,
                job.message,
                job.created_at.isoformat(),
                job.finished_at.isoformat() if job.finished_at else None,
            ),
        )
        self._conn.commit()
        self._prune()

    def _prune(self) -> None:
        self._conn.execute(
            "DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY created_at DESC LIMIT ?)",
            (self.cap,),
        )
        self._conn.commit()

    def recent(self, limit: int = 100) -> list[Job]:
        rows = self._conn.execute(
            "SELECT id, url, state, progress, filename, error, message, created_at, finished_at "
            "FROM history ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_job(r) for r in rows]

    def close(self) -> None:
        self._conn.close()


def _row_to_job(row: tuple) -> Job:
    created_at = datetime.fromisoformat(row[7]) if row[7] else datetime.now()
    finished_at = datetime.fromisoformat(row[8]) if row[8] else None
    return Job(
        id=row[0],
        url=row[1],
        state=JobState(row[2]),
        progress=row[3],
        filename=row[4],
        error=Failure(row[5]) if row[5] else None,
        message=row[6],
        created_at=created_at,
        finished_at=finished_at,
    )
