Status: done

# Tracer bullet: paste URL → Job → Download → done → serve file

## Parent

[Video Downloader PRD](../PRD.md)

## What to build

The thinnest complete path through every layer. A user opens the app in a browser, pastes a URL or share text containing a URL, and gets a downloadable MP4 back on disk.

- Serve a single static HTML page with one URL input box (vanilla JS, no build step).
- Accept a POSTed paste; extract the first URL from the text; if there is no URL, reject immediately with a clear message (do not create a Job).
- Create a Job that carries the lifecycle state and an id.
- A single-worker queue runs one Job at a time (FIFO); the Job engine calls the injected `Downloader` adapter, which downloads the Video at best quality merged to a single MP4 (requires ffmpeg) into the Download Directory.
- Filename is the platform-provided title, sanitized, with an auto-incrementing counter on name collision.
- When the Job is done, the UI shows a link that streams the file from `/download/{job_id}`. The handler resolves the Job's stored filename, verifies the real path stays inside the Download Directory, then streams it (ADR-0002) — no raw filename input from the browser.
- Default Download Directory is the system downloads folder.

## Acceptance criteria

- [ ] Starting the app and opening the browser shows a page with a URL box.
- [ ] Pasting text with no URL is rejected immediately with a clear message and creates no Job.
- [ ] Pasting a valid URL (or share text containing one) creates a Job that ends in `done`.
- [ ] A done Job produces a file in the Download Directory named after the Video title, sanitized.
- [ ] Downloading the same title twice yields distinct files (auto-increment counter).
- [ ] The finished file is streamable from `/download/{job_id}`.
- [ ] Requesting a path outside the Download Directory via the download endpoint is not possible (path traversal blocked).
- [ ] The full flow is covered by API-level tests with a fake `Downloader` injected and a temporary Download Directory.

## Blocked by

None - can start immediately
