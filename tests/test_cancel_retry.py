import threading

from smvd.downloader import DownloadResult
from smvd.jobs import Failure, JobState
from tests.conftest import FakeDownloader, wait_until


def test_cancel_queued_job(client_factory):
    block_first = threading.Event()
    blocker = FakeDownloader(result=None, block=block_first)
    client = client_factory(blocker)

    first = client.post("/jobs", json={"text": "https://www.tiktok.com/@a/video/1"}).json()["id"]
    second = client.post("/jobs", json={"text": "https://www.tiktok.com/@a/video/2"}).json()["id"]

    assert wait_until(lambda: client.get(f"/jobs/{first}").json()["state"] == "downloading")

    resp = client.post(f"/jobs/{second}/cancel")
    assert resp.status_code == 200
    assert client.get(f"/jobs/{second}").json()["state"] == "failed"
    assert client.get(f"/jobs/{second}").json()["error"] == "cancelled"

    block_first.set()
    assert wait_until(lambda: client.get(f"/jobs/{first}").json()["state"] == "done")


def test_cancel_downloading_job(client_factory):
    block = threading.Event()
    downloader = FakeDownloader(result=None, block=block)
    client = client_factory(downloader)

    job_id = client.post("/jobs", json={"text": "https://www.tiktok.com/@a/video/1"}).json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "downloading")

    resp = client.post(f"/jobs/{job_id}/cancel")
    assert resp.status_code == 200
    block.set()

    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "failed")
    assert client.get(f"/jobs/{job_id}").json()["error"] == "cancelled"


def test_retry_failed_job(client_factory):
    calls = []
    real = FakeDownloader(result=None)

    class RetryDownloader(FakeDownloader):
        def download(self, url, dest_dir, progress_cb, cancel_check):
            calls.append(url)
            if len(calls) == 1:
                return DownloadResult(state=JobState.FAILED, error=Failure.OTHER, message="flaky")
            return real.download(url, dest_dir, progress_cb, cancel_check)

    client = client_factory(RetryDownloader())
    first = client.post("/jobs", json={"text": "https://www.tiktok.com/@a/video/1"}).json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{first}").json()["state"] == "failed")

    resp = client.post(f"/jobs/{first}/retry")
    assert resp.status_code == 200
    new_id = resp.json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{new_id}").json()["state"] == "done")


def test_retry_uses_same_url(client_factory):
    calls = []
    real = FakeDownloader(result=None)

    class RetryDownloader(FakeDownloader):
        def download(self, url, dest_dir, progress_cb, cancel_check):
            calls.append(url)
            if len(calls) == 1:
                return DownloadResult(state=JobState.FAILED, error=Failure.OTHER, message="flaky")
            return real.download(url, dest_dir, progress_cb, cancel_check)

    client = client_factory(RetryDownloader())
    first = client.post("/jobs", json={"text": "https://www.instagram.com/p/xyz/"}).json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{first}").json()["state"] == "failed")
    client.post(f"/jobs/{first}/retry")
    assert wait_until(lambda: len(calls) == 2)
    assert calls[1] == "https://www.instagram.com/p/xyz/"


def test_retry_non_failed_job_rejected(client_factory):
    client = client_factory(FakeDownloader())
    job_id = client.post("/jobs", json={"text": "https://www.tiktok.com/@a/video/1"}).json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "done")
    assert client.post(f"/jobs/{job_id}/retry").status_code == 404
