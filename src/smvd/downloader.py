from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

import yt_dlp
from yt_dlp.utils import DownloadError

from .jobs import Failure, JobState

ProgressCallback = Callable[[float], None]
CancelCheck = Callable[[], bool]


class Cancelled(Exception):
    """Raised by a Downloader when cancellation is requested mid-download."""


@dataclass
class DownloadResult:
    state: JobState
    filename: str | None = None
    error: Failure | None = None
    message: str | None = None


class Downloader(Protocol):
    def download(
        self,
        url: str,
        dest_dir: Path,
        progress_cb: ProgressCallback,
        cancel_check: CancelCheck,
    ) -> DownloadResult:
        """Download the Video at url into dest_dir, reporting progress.

        Returns a done result with the saved filename, or a failed result with
        a failure category and message. Raises Cancelled when cancel_check()
        turns true mid-download.
        """
        ...


class YtDlpDownloader:
    """Downloader backed by yt-dlp, mapping its output onto failure categories."""

    def download(
        self,
        url: str,
        dest_dir: Path,
        progress_cb: ProgressCallback,
        cancel_check: CancelCheck,
    ) -> DownloadResult:
        dest_dir.mkdir(parents=True, exist_ok=True)

        def hook(d: dict) -> None:
            if cancel_check():
                raise Cancelled("Download cancelled")
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total:
                    progress_cb(d["downloaded_bytes"] / total * 100)
            elif d.get("status") == "finished":
                progress_cb(100.0)

        opts: dict[str, Any] = {
            "outtmpl": str(dest_dir / "%(title)s.%(ext)s"),
            "format": "bestvideo*+bestaudio/best",
            "format_sort": ["ext:mp4:m4a"],
            "merge_output_format": "mp4",
            "restrictfilenames": True,
            "trim_file_name": 200,
            "noplaylist": True,
            "js_runtimes": {"deno": {}, "node": {}, "bun": {}, "quickjs": {}},
            "remote_components": ["ejs:github"],
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
                ydl.download([url])
        except Cancelled:
            raise
        except DownloadError as e:
            error, message = _categorize(str(e))
            return DownloadResult(state=JobState.FAILED, error=error, message=message)

        files = sorted(f for f in dest_dir.iterdir() if f.is_file())
        if not files:
            return DownloadResult(
                state=JobState.FAILED,
                error=Failure.UNAVAILABLE,
                message="No video could be extracted from the URL.",
            )
        return DownloadResult(state=JobState.DONE, filename=files[0].name)


def _categorize(raw: str) -> tuple[Failure, str]:
    lowered = raw.lower()
    message = raw.strip().splitlines()[-1].strip() if raw.strip() else "Download failed."
    if "unsupported url" in lowered:
        return Failure.UNSUPPORTED_URL, message
    if (
        "login" in lowered
        or "authentication" in lowered
        or "private" in lowered
        or "requires sign" in lowered
        or "sign in" in lowered
        or "members-only" in lowered
        or "members only" in lowered
    ):
        return Failure.PRIVATE, message
    if (
        "video unavailable" in lowered
        or "is unavailable" in lowered
        or "not available" in lowered
        or "no longer available" in lowered
        or "removed" in lowered
        or "geo-restricted" in lowered
        or "geo-restriction" in lowered
        or "is not a valid url" in lowered
        or "incomplete youtube id" in lowered
        or "404" in lowered
        or "this video has been" in lowered
    ):
        return Failure.UNAVAILABLE, message
    if (
        "network" in lowered
        or "unable to connect" in lowered
        or "unable to download" in lowered
        or "timed out" in lowered
        or "connection" in lowered
        or "name or service not known" in lowered
        or "couldn't resolve" in lowered
    ):
        return Failure.NETWORK, message
    return Failure.OTHER, message


_URL_RE = re.compile(r"https?://[^\s]+")
_TRAILING_PUNCT = ".,;:!?)]}'\""


def extract_url(text: str) -> str | None:
    """Return the first http(s) URL found in text, or None if there is none."""
    match = _URL_RE.search(text)
    if not match:
        return None
    url = match.group(0)
    return url.rstrip(_TRAILING_PUNCT)
