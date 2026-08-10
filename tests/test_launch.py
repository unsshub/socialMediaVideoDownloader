import socket

from smvd.prereqs import ffmpeg_available, require_ffmpeg


def test_ffmpeg_available_on_this_machine():
    assert ffmpeg_available() is True


def test_require_ffmpeg_no_error_when_present():
    require_ffmpeg()  # should not raise


def test_find_free_port_returns_preferred(monkeypatch):
    from smvd.main import find_free_port

    port = find_free_port(8653)
    assert port == 8653


def test_find_free_port_falls_back_when_occupied(monkeypatch):
    from smvd.main import find_free_port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        occupied = s.getsockname()[1]
        # First call uses preferred which is occupied -> falls back to ephemeral
        port = find_free_port(occupied)
        assert isinstance(port, int)
        assert port != occupied


def test_prereqs_module_exposes_require_ffmpeg():
    from smvd import prereqs

    assert callable(prereqs.require_ffmpeg)
