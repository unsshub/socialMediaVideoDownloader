# Video Downloader

A local web application for Linux that downloads Videos from TikTok, Instagram, and Facebook to your computer.

## Requirements

- Python 3.10+
- `ffmpeg` (required to merge best-quality video + audio into MP4). Install it, e.g. `sudo apt install ffmpeg`.

## Install

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Run

```sh
.venv/bin/python -m smvd
```

The app binds to `http://127.0.0.1:8653` (localhost only), prints the URL, and opens your browser. Paste a TikTok, Instagram, or Facebook video URL (or share text containing one) and click Download.

Optional flags:

- `--no-browser` — don't auto-open the browser
- `--port N` — use a specific port

## Configuration

- **Download Directory** — changeable from the Settings card in the UI; stored in `~/.config/smvd/config.json`. Defaults to your downloads folder.
- **Job history** — last 100 finished Jobs are stored in `~/.local/share/smvd/history.db`.

## Behavior

- Videos only; best-available quality, merged to MP4.
- One Download at a time; further Jobs queue in order.
- Cancel queued or in-flight Jobs; Retry failed Jobs.
- Failures are categorized: Unsupported URL, Private, Unavailable, Network error, Failed (other).

## Tests

```sh
.venv/bin/python -m pytest
```
