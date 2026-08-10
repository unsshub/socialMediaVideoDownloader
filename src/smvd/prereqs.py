from __future__ import annotations

import shutil


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def require_ffmpeg() -> None:
    if not ffmpeg_available():
        raise RuntimeError(
            "ffmpeg is required to merge video and audio into MP4. "
            "Install it (e.g. `sudo apt install ffmpeg`) and try again."
        )
