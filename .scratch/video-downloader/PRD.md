Status: done

# Video Downloader — PRD

## Problem Statement

The user wants to save Videos from TikTok, Instagram, and Facebook to their Linux computer, but the platforms provide no easy, non-app way to download a single Video. Existing download tools are either web services (privacy and trust concerns) or CLI tools with no interface for casual pasting. The user needs a local, private way to paste a Video URL and get the Video file on their own disk.

## Solution

A local web application (`python -m smvd`) that binds to `localhost`, auto-opens the browser, and presents a single page with a URL box. The user pastes a URL or share text, and the app extracts the first URL, queues a Download as a tracked Job, downloads the Video at best quality as an MP4 into a configurable Download Directory, and reports progress live. Finished Videos are served back through the browser with a link; failures surface as one of five clear categories with a Retry option. The user can also Cancel queued or in-flight Jobs.

## User Stories

1. As a user, I want to paste a TikTok/Instagram/Facebook URL (or share text containing one) into a single input, so that I can start a Download without learning any tool syntax.
2. As a user, I want the app to extract the URL from pasted share text (e.g. "Check out this video https://vm.tiktok.com/xyz"), so that I don't have to clean up text before pasting.
3. As a user, I want the app to tell me immediately when the pasted text contains no URL, so that I can correct my input instead of waiting.
4. As a user, I want the app to tell me when a URL's Platform is not supported, so that I understand why the Download failed.
5. As a user, I want every Download to appear as a Job with a clear state (pending, downloading, done, failed), so that I can see what's happening.
6. As a user, I want live progress on a downloading Job, so that I know how long to wait.
7. As a user, I want only one Download to run at a time, with further Jobs queued in order, so that the app behaves predictably and doesn't trip platform rate limits.
8. As a user, I want the best-available quality merged to a single MP4, so that I get a high-quality file without making format choices.
9. As a user, I want the finished Video saved in a Download Directory I can configure, defaulting to my system downloads folder, so that I find my files where I expect them.
10. As a user, I want a link to the finished Video in the UI so that I can open or save it from the browser.
11. As a user, I want downloaded files named after the Video's title (sanitized), with an auto-incrementing counter on name collisions, so that I can recognize files without losing earlier Downloads.
12. As a user, I want to Cancel a queued or downloading Job, so that I can stop a Download I no longer want.
13. As a user, I want to Retry a failed Job with one click, so that I don't have to re-paste the URL.
14. As a user, I want clear, categorized failure messages (Unsupported URL, Private, Unavailable, Network error, Failed other), so that I know why a Download failed and what I can do about it.
15. As a user, I want to be told when a Video is private or login-gated, without the app trying to bypass it, so that I understand it simply can't be downloaded.
16. As a user, I want the app to treat deleted, removed, or geo-blocked Videos as Unavailable, so that the failure is honest and descriptive.
17. As a user, I want network failures reported distinctly from other failures, so that I know a retry might help.
18. As a user, I want past Downloads remembered across restarts (including their file paths and error messages), so that I can find or retry something from earlier.
19. As a user, I want my Download Directory setting to persist across restarts, so that I don't reconfigure it every launch.
20. As a user, I want the app to keep only recent history (last ~100 Jobs), so that the record stays tidy.
21. As a user, I want partial files cleaned up when a Download fails or is cancelled, so that the Download Directory stays clean.
22. As a user, I want in-flight Jobs marked as failed with partials removed if the server stops, so that my history is honest.
23. As a user, I want the app to start with one command and open the browser automatically, so that I don't fiddle with URLs and ports.
24. As a user, I want to choose whether the app reaches only this machine, so that my Downloads stay private.
25. As a user, I want a browser notification when a Download finishes or fails (with an in-page fallback), so that I can work elsewhere while waiting.
26. As a user, I want the app to tell me clearly if ffmpeg is missing, so that I know what to install rather than seeing a cryptic crash.
27. As a user, I want the file-serving endpoint to be safe against path traversal, so that my machine's other files aren't exposed.

## Implementation Decisions

- **Stack.** Python + FastAPI serving a single static HTML page (vanilla JS, no build step). `yt-dlp` is the download engine (ADR-0001), wrapped in a thin `Downloader` adapter.
- **Package layout.** Single `smvd` package with modules for the server, the Downloader adapter, the Job queue/state, and SQLite history. Tests in a separate `tests/` package.
- **API contract.** `POST` a URL/share-text body → creates a Job and returns its id. `GET` job status/progress and recent history. `GET /download/{job_id}` streams the finished file (ADR-0002). `POST` cancel and `POST` retry endpoints operate on an existing Job. `GET`/`PUT` a Download Directory setting.
- **Job state machine.** `pending → downloading → done | failed`. A single-worker queue runs one Job at a time; queued Jobs wait in FIFO order. No automatic retry — retry is always user-initiated.
- **Downloader boundary.** The `Downloader` adapter is injected into the app. It accepts a URL and a target directory and reports progress callbacks; the Job engine maps its outcomes and errors onto the five failure categories.
- **Error categorization.** yt-dlp output is mapped to: Unsupported URL (no URL / unsupported domain), Private (login-gated), Unavailable (deleted, removed, geo-blocked, unextractable), Network error, Failed (other).
- **File handling.** Best quality video+audio merged to MP4 via yt-dlp post-processor (requires ffmpeg). Filename = sanitized platform title with auto-increment counter on collision. Partials deleted on failure and cancel. On shutdown, active Jobs are marked failed ("interrupted") and partials removed.
- **Persistence.** Active Jobs in memory; finished Jobs persisted to SQLite. History capped at the most recent ~100 Jobs. Download Directory stored in a JSON config file.
- **Config & paths.** Config and DB live under XDG directories (`~/.config/smvd/`, `~/.local/share/smvd/`). Default Download Directory is the system downloads folder. Fixed port with fallback if occupied.
- **Launch.** `python -m smvd` starts the server, prints the URL, and auto-opens the browser. Binds to `localhost` only.
- **Notifications.** Browser Notification API with permission request; degrades to an in-page banner.

## Testing Decisions

- **Good tests** exercise only external behavior through the public HTTP API — they do not reach into Job-internal state or call private methods. A test describes what the user experiences (e.g. "pasting a valid URL produces a done Job with a downloadable file"), so it survives internal refactors.
- **Single seam.** All automated tests run against the FastAPI test client with a fake `Downloader` injected (substituting yt-dlp) and the Download Directory pointed at a temporary directory per test run. This covers URL extraction, the Job state machine, progress, the five failure categories, cancel/retry, history persistence, config persistence, and the file-serving endpoint in one go.
- **Modules covered.** The whole `smvd` package through its API; nothing is tested by reaching into internals. URL parsing is exercised via the API (a paste with share text produces a Job for the extracted URL).
- **Prior art.** None exists yet — this is a greenfield repo. The pattern (API-level tests with an injected seam and temp directories) is the standard FastAPI test-client approach.
- **Live verification.** Real downloads against TikTok/Instagram/Facebook are verified manually (live tests are flaky and rate-limited), as agreed during design.

## Out of Scope

- Downloading images, carousels/albums, or audio-only tracks — Videos only.
- Private or login-gated content: no cookie import, no OAuth flows.
- Quality/format selection in the UI — always best-quality MP4.
- Platform rate-limit management beyond the single-worker queue.
- Automatic retries, duplicate-URL deduplication.
- System packaging (deb/rpm/flatpak), systemd service, or LAN access.
- A build pipeline or frontend framework — single static page, no Node toolchain.
- Multi-user support, authentication, or anything beyond a personal `localhost` tool.

## Further Notes

- Glossary vocabulary defined in `CONTEXT.md` (Video, Platform, Download, Job, Download Directory, and the failure states) is authoritative; use it in issues, tests, and code.
- ADR-0001 (yt-dlp as download engine) and ADR-0002 (serve files by Job ID) constrain the design.
- The downloader's error mapping must be tolerant of yt-dlp message drift; unrecognized failures fall through to "Failed (other)" rather than crashing the Job.
