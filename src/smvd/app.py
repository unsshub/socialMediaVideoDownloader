from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import Config
from .downloader import YtDlpDownloader, extract_url
from .engine import JobEngine
from .history import HistoryStore
from .jobs import JobState

STATIC_DIR = Path(__file__).parent / "static"


class SubmitBody(BaseModel):
    text: str


class SettingsBody(BaseModel):
    download_dir: str


def create_app(
    config: Optional[Config] = None,
    downloader=None,
    history: Optional[HistoryStore] = None,
) -> FastAPI:
    config = config or Config()
    downloader = downloader or YtDlpDownloader()
    history = history or HistoryStore(config.data_dir / "history.db")
    engine = JobEngine(downloader, history, config.download_dir)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        engine.shutdown()

    app = FastAPI(title="Video Downloader", lifespan=lifespan)

    app.state.engine = engine
    app.state.config = config

    @app.post("/jobs", status_code=201)
    def create_job(body: SubmitBody) -> dict:
        url = extract_url(body.text)
        if url is None:
            raise HTTPException(status_code=400, detail="No URL found in the pasted text.")
        job = engine.submit(url)
        return {"id": job.id}

    @app.get("/jobs")
    def list_jobs(limit: int = 100) -> list[dict]:
        return [job.to_dict() for job in engine.recent(limit=limit)]

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str) -> dict:
        job = engine.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found.")
        return job.to_dict()

    @app.post("/jobs/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict:
        if not engine.cancel(job_id):
            raise HTTPException(status_code=404, detail="Job not found or not cancellable.")
        return {"ok": True}

    @app.post("/jobs/{job_id}/retry")
    def retry_job(job_id: str) -> dict:
        job = engine.retry(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found or not retryable.")
        return {"id": job.id}

    @app.get("/download/{job_id}")
    def download(job_id: str) -> FileResponse:
        job = engine.get(job_id)
        if job is None or job.state != JobState.DONE or job.filename is None:
            raise HTTPException(status_code=404, detail="Downloaded file not found.")
        root = engine.download_dir.resolve()
        file_path = (root / job.filename).resolve()
        if root not in file_path.parents:
            raise HTTPException(status_code=404, detail="Downloaded file not found.")
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="Downloaded file not found.")
        return FileResponse(file_path, filename=job.filename)

    @app.get("/settings")
    def get_settings() -> dict:
        return {"download_dir": str(engine.download_dir)}

    @app.put("/settings")
    def put_settings(body: SettingsBody) -> dict:
        config.set_download_dir(Path(body.download_dir))
        engine.set_download_dir(config.download_dir)
        return {"download_dir": str(engine.download_dir)}

    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


def make_app() -> FastAPI:
    config = Config()
    history = HistoryStore(config.data_dir / "history.db")
    return create_app(config=config, downloader=YtDlpDownloader(), history=history)


app = make_app()
