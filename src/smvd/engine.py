from __future__ import annotations

import shutil
import tempfile
import threading
import uuid
from collections import deque
from pathlib import Path

from .downloader import Cancelled, Downloader
from .history import HistoryStore
from .jobs import Failure, Job, JobState, utcnow


class JobEngine:
    """Single-worker FIFO queue that tracks each Download as a Job.

    Active Jobs live in memory; finished Jobs are recorded in the HistoryStore.
    Files are downloaded into a per-Job staging directory and moved into the
    Download Directory under a collision-free name on success.
    """

    def __init__(self, downloader: Downloader, history: HistoryStore, download_dir: Path):
        self._downloader = downloader
        self._history = history
        self._download_dir = Path(download_dir)
        self._jobs: dict[str, Job] = {}
        self._queue: deque[str] = deque()
        self._cancel: dict[str, threading.Event] = {}
        self._staging: dict[str, Path] = {}
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._worker: threading.Thread | None = None
        self._shutdown = False
        self._load_history()

    def _load_history(self) -> None:
        for job in self._history.recent():
            self._jobs[job.id] = job

    @property
    def download_dir(self) -> Path:
        with self._lock:
            return self._download_dir

    def set_download_dir(self, path: Path) -> None:
        with self._lock:
            self._download_dir = Path(path)

    def submit(self, url: str) -> Job:
        with self._cond:
            job = Job(id=uuid.uuid4().hex, url=url)
            self._jobs[job.id] = job
            self._queue.append(job.id)
            self._ensure_worker_locked()
            self._cond.notify()
        return job

    def retry(self, job_id: str) -> Job | None:
        with self._cond:
            existing = self._jobs.get(job_id)
            if existing is None or existing.state != JobState.FAILED:
                return None
            job = Job(id=uuid.uuid4().hex, url=existing.url)
            self._jobs[job.id] = job
            self._queue.append(job.id)
            self._ensure_worker_locked()
            self._cond.notify()
        return job

    def _ensure_worker_locked(self) -> None:
        if (self._worker is None or not self._worker.is_alive()) and not self._shutdown:
            self._worker = threading.Thread(target=self._run, daemon=True)
            self._worker.start()

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def active(self) -> list[Job]:
        with self._lock:
            return [
                job for job in self._jobs.values() if job.state in (JobState.PENDING, JobState.DOWNLOADING)
            ]

    def recent(self, limit: int = 100) -> list[Job]:
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def cancel(self, job_id: str) -> bool:
        with self._cond:
            job = self._jobs.get(job_id)
            if job is None:
                return False
            if job.state == JobState.PENDING:
                if job_id in self._queue:
                    self._queue.remove(job_id)
                self._fail(job, Failure.CANCELLED, "Cancelled before it started.")
                self._cleanup_staging(job_id)
                self._record(job)
                return True
            if job.state == JobState.DOWNLOADING:
                event = self._cancel.setdefault(job_id, threading.Event())
                event.set()
                return True
            return False

    def shutdown(self) -> None:
        with self._cond:
            self._shutdown = True
            for job in self._jobs.values():
                if job.state == JobState.PENDING:
                    self._fail(job, Failure.INTERRUPTED, "Interrupted by server shutdown.")
                    self._record(job)
                elif job.state == JobState.DOWNLOADING:
                    event = self._cancel.setdefault(job.id, threading.Event())
                    event.set()
            self._cond.notify_all()
        if self._worker is not None:
            self._worker.join(timeout=5)
        self._history.close()

    def _run(self) -> None:
        while True:
            with self._cond:
                while not self._queue and not self._shutdown:
                    self._cond.wait()
                if self._shutdown:
                    return
                job_id = self._queue.popleft()
                job = self._jobs[job_id]
                job.state = JobState.DOWNLOADING
                job.progress = 0.0
                cancel_event = self._cancel.setdefault(job_id, threading.Event())
                staging = Path(tempfile.mkdtemp(prefix="smvd-"))
                self._staging[job_id] = staging
                url = job.url
                download_dir = self._download_dir

            def progress_cb(pct: float) -> None:
                with self._lock:
                    job.progress = pct

            def cancel_check() -> bool:
                return cancel_event.is_set()

            try:
                result = self._downloader.download(url, staging, progress_cb, cancel_check)
                if cancel_check():
                    raise Cancelled("cancelled")
                if result.state == JobState.DONE and result.filename:
                    final = self._move_to_download_dir(staging, download_dir, result.filename)
                    with self._lock:
                        job.filename = final.name
                        job.state = JobState.DONE
                        job.progress = 100.0
                        job.finished_at = utcnow()
                else:
                    with self._lock:
                        self._fail(job, result.error or Failure.OTHER, result.message)
            except Cancelled:
                with self._lock:
                    failure = Failure.INTERRUPTED if self._shutdown else Failure.CANCELLED
                    message = "Interrupted by server shutdown." if self._shutdown else "Download cancelled."
                    self._fail(job, failure, message)
            except Exception as e:  # noqa: BLE001
                with self._lock:
                    self._fail(job, Failure.OTHER, str(e))
            finally:
                with self._lock:
                    self._cleanup_staging(job_id)
                    self._record(job)

    @staticmethod
    def _move_to_download_dir(staging: Path, download_dir: Path, filename: str) -> Path:
        src = staging / filename
        download_dir.mkdir(parents=True, exist_ok=True)
        target = JobEngine._unique_path(download_dir / filename)
        shutil.move(str(src), str(target))
        return target

    @staticmethod
    def _unique_path(path: Path) -> Path:
        if not path.exists():
            return path
        stem, suffix = path.stem, path.suffix
        i = 1
        while True:
            candidate = path.with_name(f"{stem} ({i}){suffix}")
            if not candidate.exists():
                return candidate
            i += 1

    def _fail(self, job: Job, failure: Failure, message: str | None) -> None:
        job.state = JobState.FAILED
        job.error = failure
        job.message = message
        job.finished_at = utcnow()

    def _record(self, job: Job) -> None:
        if job.state in (JobState.DONE, JobState.FAILED):
            self._history.record(job)

    def _cleanup_staging(self, job_id: str) -> None:
        staging = self._staging.pop(job_id, None)
        if staging is not None and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        self._cancel.pop(job_id, None)
