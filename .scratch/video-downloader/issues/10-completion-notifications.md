Status: done

# Completion notifications

## Parent

[Video Downloader PRD](../PRD.md)

## What to build

The user is notified when a Download finishes or fails so they can work elsewhere. Use the browser Notification API with a permission request; if permission is denied or unavailable, degrade to an in-page banner.

## Acceptance criteria

- [ ] A system notification fires when a Job reaches done or failed (permission granted).
- [ ] If permission is denied/unavailable, the same completion/failure is shown as an in-page banner.
- [ ] No notification is requested at page load without user intent.

## Blocked by

- [#02 Live progress & state display](02-live-progress.md)
