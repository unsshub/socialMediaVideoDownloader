# Video Downloader — Product Requirements

A local web application for Linux that downloads Videos from TikTok, Instagram, and Facebook to the user's computer.

## Scope

In scope: single Videos from TikTok, Instagram, and Facebook. Out of scope: images, carousels/albums, audio-only tracks, private/login-gated content, cookie/account integration.

## User flow

1. User starts the app (`python -m smvd`). It binds to `localhost` on a fixed port and auto-opens the browser.
2. User pastes a URL or share text into a single input box.
3. The app extracts the first URL and creates a Job.
4. The Job runs through a single-worker queue: `pending → downloading → done | failed`, with progress shown live.
5. On success the UI links the saved file (streamed via `/download/{job_id}`); on failure it shows a categorized error with a Retry button.
6. The browser notifies the user when a Job finishes or fails (permission-gated; in-page fallback).

## Behavior rules

- **Videos only.** Images, audio, and collections are not downloaded.
- **Best quality MP4 always.** yt-dlp fetches best video+audio and merges to MP4 via ffmpeg. No quality selection.
- **URL parsing.** Regex the first `http(s)` URL out of pasted text. Unsupported domains fail as Unsupported URL.
- **Single worker queue.** One Download at a time; queued Jobs wait. No auto-retry; user retries manually.
- **Filename.** Platform-provided title, sanitized via `--restrict-filenames`, auto-append counter on collision.
- **Private content.** Not attempted; fails with a clear "Private" message.
- **Failure categories.** Unsupported URL / Private / Unavailable (deleted, removed, geo-blocked, unextractable) / Network error / Failed (other).
- **Duplicates allowed.** Same URL may be queued again; the collision counter keeps files distinct.
- **Cancel & Retry.** Queued or downloading Jobs can be cancelled; failed Jobs can be retried.
- **Cleanup.** Partial/temp files are deleted on failure and on cancel. In-flight Jobs are marked failed ("interrupted") with partials removed when the server shuts down.
- **File serving.** Finished files served only via `/download/{job_id}`, resolved and validated inside the Download Directory (ADR-0002).

## Data & configuration

- **Download Directory.** Configurable in a Settings area; default `~/Downloads`. Stored in a JSON config file under `~/.config/smvd/`.
- **Job history.** Active Jobs in memory; finished Jobs persisted to SQLite under `~/.local/share/smvd/`. History kept to the most recent 100 Jobs.
- **Port.** Fixed port with a fallback if occupied.
- **ffmpeg.** Documented prerequisite; app shows a clear setup error if missing (ADR-0001).

## Architecture

- `src/smvd/` package: `main.py` (server), `downloader.py` (yt-dlp adapter), `jobs.py` (queue/state), `history.py` (SQLite), `static/index.html` (single page UI). Tests in `tests/`.
- Single HTML page, vanilla JS, no build step.

## Acceptance criteria

- [ ] `python -m smvd` starts a `localhost` server, prints the URL, auto-opens the browser.
- [ ] Pasting a TikTok/Instagram/Facebook URL or share text creates a visible Job that progresses to done with a link to the saved MP4 in the configured directory.
- [ ] Jobs reflect pending/downloading/done/failed states; progress updates live.
- [ ] Failed Jobs show one of the five categories and offer Retry; queued/downloading Jobs offer Cancel.
- [ ] Same-URL duplicates produce distinct files; filename collisions are auto-incremented.
- [ ] Private content fails cleanly without downloading; partial files are deleted on failure/cancel.
- [ ] Download Directory is configurable via the UI and persists across restarts; default is `~/Downloads`.
- [ ] Finished files are served via `/download/{job_id}` with path validation; path traversal is not possible.
- [ ] History persists across restarts (SQLite, last 100), including error messages and file paths.
- [ ] Missing ffmpeg produces a clear setup error, not a crash.
- [ ] Browser notification (or in-page fallback) fires on done/failed.
