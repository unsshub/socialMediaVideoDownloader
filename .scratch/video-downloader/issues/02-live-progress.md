Status: done

# Live progress & state display

## Parent

[Video Downloader PRD](../PRD.md)

## What to build

The UI reflects a Job's lifecycle in real time. The page polls Job status; each Job shows its current state (pending, downloading, done, failed) and, while downloading, a live progress indication (percentage from the `Downloader` adapter). Progress updates without a page reload.

## Acceptance criteria

- [ ] A newly submitted Job shows `pending`, then `downloading`, then `done` (or `failed`) in the UI without reloading.
- [ ] While downloading, the Job displays live progress that advances.
- [ ] State and progress come from polling the Job status endpoint; no server-push channel is required.

## Blocked by

- [#01 Tracer bullet: paste URL → Job → Download → done → serve file](01-tracer-bullet-download.md)
