from pathlib import Path

from tests.conftest import FakeDownloader, wait_until


def test_paste_valid_url_ends_done_and_serves_file(client_factory, config):
    downloader = FakeDownloader(result=None)
    client = client_factory(downloader)

    resp = client.post("/jobs", json={"text": "https://www.tiktok.com/@x/video/123"})
    assert resp.status_code == 201
    job = resp.json()
    job_id = job["id"]

    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "done")

    done = client.get(f"/jobs/{job_id}").json()
    assert done["state"] == "done"
    assert done["filename"] == "video.mp4"

    dl = client.get(f"/download/{job_id}")
    assert dl.status_code == 200
    assert dl.content == b"FAKEVIDEO" * 100
    assert (config.download_dir / "video.mp4").read_bytes() == b"FAKEVIDEO" * 100


def test_paste_text_extracts_url(client_factory):
    client = client_factory(FakeDownloader())
    resp = client.post("/jobs", json={"text": "Check this out https://vm.tiktok.com/abc/xyz !"})
    assert resp.status_code == 201
    job_id = resp.json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "done")
    assert client.get(f"/jobs/{job_id}").json()["url"] == "https://vm.tiktok.com/abc/xyz"


def test_paste_with_no_url_rejected_without_creating_job(client_factory):
    client = client_factory(FakeDownloader())
    resp = client.post("/jobs", json={"text": "just some words, no link here"})
    assert resp.status_code == 400
    body = resp.json()
    assert "url" in str(body.get("detail", "")).lower() or "url" in str(body.get("message", "")).lower()


def test_path_traversal_blocked_on_download_endpoint(client_factory):
    client = client_factory(FakeDownloader())
    resp = client.get("/download/../../etc/passwd")
    assert resp.status_code in (404, 422)


def test_download_endpoint_requires_existing_done_job(client_factory):
    client = client_factory(FakeDownloader())
    resp = client.get("/download/nonexistent-id")
    assert resp.status_code == 404


def test_same_title_twice_produces_distinct_files(client_factory, config):
    client = client_factory(FakeDownloader(result=None))
    first = client.post("/jobs", json={"text": "https://www.tiktok.com/@x/video/123"}).json()["id"]
    second = client.post("/jobs", json={"text": "https://www.tiktok.com/@x/video/123"}).json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{first}").json()["state"] == "done")
    assert wait_until(lambda: client.get(f"/jobs/{second}").json()["state"] == "done")
    assert client.get(f"/jobs/{first}").json()["filename"] == "video.mp4"
    assert client.get(f"/jobs/{second}").json()["filename"] == "video (1).mp4"
    assert (config.download_dir / "video.mp4").exists()
    assert (config.download_dir / "video (1).mp4").exists()


def test_download_endpoint_blocks_filename_escaping_download_dir(client_factory, config, tmp_path):
    from smvd.downloader import DownloadResult
    from smvd.jobs import JobState

    class TraversalDownloader(FakeDownloader):
        def download(self, url, dest_dir, progress_cb, cancel_check):
            dest = Path(dest_dir)
            dest.joinpath("..", "outside.mp4").write_bytes(b"SNEAKY")
            return DownloadResult(state=JobState.DONE, filename="../outside.mp4")

    client = client_factory(TraversalDownloader())
    job_id = client.post("/jobs", json={"text": "https://www.tiktok.com/@x/video/123"}).json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "done")
    resp = client.get(f"/download/{job_id}")
    assert resp.status_code == 404
