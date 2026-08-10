from pathlib import Path

from tests.conftest import FakeDownloader, wait_until


def test_settings_default_download_dir(client_factory, config):
    client = client_factory(FakeDownloader())
    assert client.get("/settings").json()["download_dir"] == str(config.download_dir)


def test_update_download_dir_persists_and_is_used(client_factory, config, tmp_path):
    client = client_factory(FakeDownloader(result=None))
    new_dir = tmp_path / "videos"
    resp = client.put("/settings", json={"download_dir": str(new_dir)})
    assert resp.status_code == 200
    assert resp.json()["download_dir"] == str(new_dir)

    job_id = client.post("/jobs", json={"text": "https://www.tiktok.com/@a/video/1"}).json()["id"]
    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "done")
    assert (new_dir / "video.mp4").exists()

    restarted = client_factory(FakeDownloader())
    assert restarted.get("/settings").json()["download_dir"] == str(new_dir)


def test_update_download_dir_writes_config_file(config, tmp_path):
    from fastapi.testclient import TestClient

    from smvd.app import create_app

    new_dir = tmp_path / "cfgvideos"
    app = create_app(downloader=FakeDownloader(), config=config)
    client = TestClient(app)
    client.put("/settings", json={"download_dir": str(new_dir)})
    config_file = config.config_dir / "config.json"
    assert config_file.exists()
    assert str(new_dir) in config_file.read_text()


def test_config_file_created_on_first_run(config):
    config_file = config.config_dir / "config.json"
    assert config_file.exists()
