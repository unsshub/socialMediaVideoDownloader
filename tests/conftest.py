import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from smvd.downloader import Cancelled, DownloadResult
from smvd.config import Config


class FakeDownloader:
    def __init__(self, result=None, progress=(0.0, 50.0, 100.0), delay=0.0, block=None):
        self.result = result if result is not None else DownloadResult(state="done", filename="video.mp4")
        self.progress = list(progress)
        self.delay = delay
        self.block = block
        self.calls = []

    def download(self, url, dest_dir, progress_cb, cancel_check):
        self.calls.append(url)
        if self.block is not None:
            self.block.wait()
        if cancel_check():
            raise Cancelled("cancelled")
        for p in self.progress:
            if cancel_check():
                raise Cancelled("cancelled")
            progress_cb(p)
            if self.delay:
                time.sleep(self.delay)
        if self.result.state == "done":
            name = self.result.filename or "video.mp4"
            (Path(dest_dir) / name).write_bytes(b"FAKEVIDEO" * 100)
            self.result.filename = name
        return self.result


@pytest.fixture
def config(tmp_path):
    return Config(config_dir=tmp_path / "cfg", data_dir=tmp_path / "data", download_dir=tmp_path / "dl")


@pytest.fixture
def app_factory(tmp_path, config):
    from smvd.app import create_app

    def make(downloader, cfg=config):
        return create_app(downloader=downloader, config=cfg)

    return make


@pytest.fixture
def client_factory(app_factory):
    def make(downloader):
        return TestClient(app_factory(downloader))

    return make


def wait_until(predicate, timeout=5.0, interval=0.01):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False
