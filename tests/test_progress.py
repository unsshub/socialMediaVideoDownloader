import time

from tests.conftest import FakeDownloader, wait_until


def test_job_transitions_through_states(client_factory):
    blocker = time.time()
    client = client_factory(FakeDownloader(delay=0.05))

    resp = client.post("/jobs", json={"text": "https://www.instagram.com/p/abc/"})
    job_id = resp.json()["id"]

    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "downloading")
    downloading = client.get(f"/jobs/{job_id}").json()
    assert downloading["state"] == "downloading"
    assert downloading["progress"] == 0.0 or downloading["progress"] > 0.0

    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "done")
    done = client.get(f"/jobs/{job_id}").json()
    assert done["state"] == "done"
    assert done["progress"] == 100.0


def test_progress_advances_during_download(client_factory):
    client = client_factory(FakeDownloader(progress=(0.0, 33.0, 66.0, 100.0), delay=0.05))

    resp = client.post("/jobs", json={"text": "https://www.facebook.com/watch?v=xyz"})
    job_id = resp.json()["id"]

    seen = set()
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        state = client.get(f"/jobs/{job_id}").json()
        if state["state"] == "downloading":
            seen.add(round(state["progress"]))
        if state["state"] == "done":
            break
        time.sleep(0.01)

    assert wait_until(lambda: client.get(f"/jobs/{job_id}").json()["state"] == "done")
    assert len(seen) >= 2
