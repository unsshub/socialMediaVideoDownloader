from pathlib import Path

from smvd.downloader import DownloadResult
from smvd.jobs import Failure, JobState
from tests.conftest import FakeDownloader, wait_until


def test_history_persists_across_restart(client_factory, config, tmp_path):
    first = client_factory(FakeDownloader(result=None))
    job_id = first.post("/jobs", json={"text": "https://www.tiktok.com/@a/video/1"}).json()["id"]
    assert wait_until(lambda: first.get(f"/jobs/{job_id}").json()["state"] == "done")

    second = client_factory(FakeDownloader(result=None))
    jobs = second.get("/jobs").json()
    assert any(j["id"] == job_id and j["state"] == "done" for j in jobs)
    done = [j for j in jobs if j["id"] == job_id][0]
    assert done["filename"] == "video.mp4"


def test_history_capped_at_last_100(client_factory, tmp_path, config):
    client = client_factory(FakeDownloader(result=None))
    for i in range(110):
        resp = client.post("/jobs", json={"text": f"https://www.tiktok.com/@a/video/{i}"})
        assert resp.status_code == 201
    assert wait_until(lambda: len(client.get("/jobs").json()) >= 100)

    restarted = client_factory(FakeDownloader(result=None))
    jobs = restarted.get("/jobs").json()
    assert len(jobs) <= 100
    assert len([j for j in jobs if j["state"] == "done"]) == len(jobs)


def test_retry_from_persisted_history_reuses_url(client_factory, config):
    calls = []
    real = FakeDownloader(result=None)

    class FlakyDownloader(FakeDownloader):
        def download(self, url, dest_dir, progress_cb, cancel_check):
            calls.append(url)
            if len(calls) == 1:
                return DownloadResult(state=JobState.FAILED, error=Failure.OTHER, message="flaky")
            return real.download(url, dest_dir, progress_cb, cancel_check)

    first_client = client_factory(FlakyDownloader())
    job_id = first_client.post("/jobs", json={"text": "https://www.tiktok.com/@a/video/1"}).json()["id"]
    assert wait_until(lambda: first_client.get(f"/jobs/{job_id}").json()["state"] == "failed")

    restarted = client_factory(FlakyDownloader())
    retried = restarted.post(f"/jobs/{job_id}/retry")
    assert retried.status_code == 200
    new_id = retried.json()["id"]
    assert wait_until(lambda: restarted.get(f"/jobs/{new_id}").json()["state"] == "done")
    assert calls == ["https://www.tiktok.com/@a/video/1", "https://www.tiktok.com/@a/video/1"]
