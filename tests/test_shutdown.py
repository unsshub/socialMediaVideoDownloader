import threading
import time

from smvd.downloader import DownloadResult
from smvd.jobs import Failure, JobState
from tests.conftest import wait_until


def test_shutdown_marks_inflight_jobs_interrupted(client_factory):
    block = threading.Event()
    downloader = FakeDownloaderBlocking(block)
    app = None
    from smvd.app import create_app

    import tempfile
    from pathlib import Path

    from smvd.config import Config
    from smvd.history import HistoryStore

    config = Config(config_dir=Path(tempfile.mkdtemp()) / "cfg", data_dir=Path(tempfile.mkdtemp()) / "data")
    history = HistoryStore(config.data_dir / "history.db")
    app = create_app(downloader=downloader, config=config, history=history)

    from fastapi.testclient import TestClient

    client = TestClient(app)
    job_id = client.post("/jobs", json={"text": "https://www.tiktok.com/@a/video/1"}).json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "downloading")

    engine = app.state.engine
    engine.shutdown()
    block.set()

    job = client.get(f"/jobs/{job_id}").json()
    assert job["state"] == "failed"
    assert job["error"] == "interrupted"


class FakeDownloaderBlocking:
    def __init__(self, block):
        self.block = block

    def download(self, url, dest_dir, progress_cb, cancel_check):
        from smvd.downloader import Cancelled

        while not self.block.is_set():
            if cancel_check():
                raise Cancelled("interrupted")
            time.sleep(0.01)
        return DownloadResult(state=JobState.DONE, filename="video.mp4")
