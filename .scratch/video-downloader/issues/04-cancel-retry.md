Status: done

# Cancel & Retry

## Parent

[Video Downloader PRD](../PRD.md)

## What to build

The user can stop a Download they no longer want and re-run a Download that failed.

- Cancel: a queued or downloading Job can be cancelled; a downloading Job's process is stopped and partial/temp files are deleted.
- Retry: a failed Job can be retried with one click, re-using its original URL without re-pasting.

## Acceptance criteria

- [ ] A queued Job can be cancelled and removed from the queue.
- [ ] A downloading Job can be cancelled; it ends failed (cancelled) and its partial files are deleted.
- [ ] A failed Job shows a Retry action that re-enqueues it with the same URL.
- [ ] A retried Job runs through the normal lifecycle and can succeed.

## Blocked by

- [#03 Failure categories + partial cleanup on failure](03-failure-categories.md)
