Status: done

# Interrupted Jobs on shutdown

## Parent

[Video Downloader PRD](../PRD.md)

## What to build

When the server stops (Ctrl+C, crash, reboot), any in-flight Downloads are accounted for honestly. On clean shutdown, active Jobs are marked failed with an "interrupted" outcome and their partial/temp files are removed, so history has no silent gap.

## Acceptance criteria

- [ ] Shutting down the server with a Job in flight marks that Job failed (interrupted) in history.
- [ ] Its partial/temp files are removed from the Download Directory.
- [ ] History remains consistent (no in-flight Jobs silently missing).

## Blocked by

- [#03 Failure categories + partial cleanup on failure](03-failure-categories.md)
