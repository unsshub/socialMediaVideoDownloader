Status: done

# History persistence

## Parent

[Video Downloader PRD](../PRD.md)

## What to build

Past Downloads are remembered across restarts. Finished Jobs (including their file paths and error messages) are recorded in a local SQLite store; the UI shows recent history; history is capped at the most recent ~100 Jobs.

- Active Jobs live in memory; finished Jobs are persisted.
- History is loaded and shown after a restart.
- The record is pruned to the last ~100 Jobs.

## Acceptance criteria

- [ ] Done and failed Jobs persist to the SQLite store.
- [ ] After a server restart, history shows previously finished Jobs with their file paths and error messages.
- [ ] History is capped at the most recent ~100 Jobs (older entries are pruned).
- [ ] Retrying from persisted history re-uses the original URL.

## Blocked by

- [#01 Tracer bullet: paste URL → Job → Download → done → serve file](01-tracer-bullet-download.md)
