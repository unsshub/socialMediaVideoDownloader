from pathlib import Path

from smvd.downloader import DownloadResult
from smvd.jobs import Failure, JobState
from tests.conftest import FakeDownloader, wait_until


def _fail(error, message, text="https://www.tiktok.com/@x/video/123"):
    return FakeDownloader(result=DownloadResult(state=JobState.FAILED, error=error, message=message))


def _submit_and_wait(client, text="https://www.tiktok.com/@x/video/123"):
    resp = client.post("/jobs", json={"text": text})
    assert resp.status_code == 201
    job_id = resp.json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "failed")
    return client.get(f"/jobs/{job_id}").json()


def test_unsupported_url_category(client_factory):
    client = client_factory(_fail(Failure.UNSUPPORTED_URL, "Unsupported URL: example.com"))
    job = _submit_and_wait(client, "https://example.com/not-a-video")
    assert job["error"] == "unsupported_url"


def test_private_category(client_factory):
    client = client_factory(_fail(Failure.PRIVATE, "This video requires login"))
    job = _submit_and_wait(client)
    assert job["error"] == "private"


def test_unavailable_category(client_factory):
    client = client_factory(_fail(Failure.UNAVAILABLE, "Video unavailable"))
    job = _submit_and_wait(client)
    assert job["error"] == "unavailable"


def test_network_error_category(client_factory):
    client = client_factory(_fail(Failure.NETWORK, "Unable to connect to server"))
    job = _submit_and_wait(client)
    assert job["error"] == "network_error"


def test_failed_other_category(client_factory):
    client = client_factory(_fail(Failure.OTHER, "Something odd happened"))
    job = _submit_and_wait(client)
    assert job["error"] == "failed_other"


def test_failed_job_keeps_message(client_factory):
    client = client_factory(_fail(Failure.UNAVAILABLE, "Video has been removed by the uploader"))
    job = _submit_and_wait(client)
    assert "removed" in job["message"].lower()


def test_no_partial_files_left_after_failure(client_factory, config):
    client = client_factory(_fail(Failure.NETWORK, "connection dropped"))
    _submit_and_wait(client)
    leftovers = list(config.download_dir.glob("*"))
    assert leftovers == []


def test_partial_staging_removed_after_failure(client_factory):
    class PartialDownloader(FakeDownloader):
        def download(self, url, dest_dir, progress_cb, cancel_check):
            (Path(dest_dir) / "leftover.part").write_bytes(b"partial")
            return DownloadResult(state=JobState.FAILED, error=Failure.OTHER, message="boom")

    client = client_factory(PartialDownloader())
    _submit_and_wait(client)
