from __future__ import annotations

import socket
import sys
import threading
import time
import webbrowser


def find_free_port(preferred: int = 8653) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def open_browser_when_ready(host: str, port: int, timeout: float = 10.0) -> None:
    """Open the browser once the server is accepting connections."""

    def _wait_and_open() -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                with socket.create_connection((host, port), timeout=0.5):
                    webbrowser.open(f"http://{host}:{port}")
                    return
            except OSError:
                time.sleep(0.1)

    threading.Thread(target=_wait_and_open, daemon=True).start()


def main(argv: list[str] | None = None) -> int:
    from smvd.app import make_app
    from smvd.prereqs import require_ffmpeg

    try:
        require_ffmpeg()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    argv = list(sys.argv[1:] if argv is None else argv)
    host = "127.0.0.1"
    port = find_free_port()
    if "--port" in argv:
        idx = argv.index("--port")
        if idx + 1 >= len(argv):
            print("--port requires a value", file=sys.stderr)
            return 1
        port = int(argv[idx + 1])

    import uvicorn

    if "--no-browser" not in argv:
        open_browser_when_ready(host, port)

    print(f"Video Downloader running at http://{host}:{port}")
    uvicorn.run(make_app(), host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
