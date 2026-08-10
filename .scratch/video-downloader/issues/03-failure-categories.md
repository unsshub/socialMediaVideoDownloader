Status: done

# Failure categories + partial cleanup on failure

## Parent

[Video Downloader PRD](../PRD.md)

## What to build

Failed Downloads surface a precise, human-readable category instead of raw error text, and leave no partial files behind.

- The Job engine maps `Downloader` outcomes and errors onto the five failure categories: Unsupported URL, Private, Unavailable, Network error, Failed (other).
- The mapping is tolerant of message drift: unrecognized failures fall through to Failed (other) rather than crashing the Job.
- Each failed Job shows its category and a short message in the UI.
- On failure, leftover partial/temp files in the Download Directory are deleted.

## Acceptance criteria

- [ ] Each of the five failure categories is produced by the API and shown in the UI with a clear message (exercised with a fake `Downloader`).
- [ ] A Video that is private or login-gated fails as Private and is not downloaded.
- [ ] A deleted/removed/geo-blocked/unextractable Video fails as Unavailable.
- [ ] An unreachable platform fails as Network error.
- [ ] A paste with an unsupported domain or no URL fails as Unsupported URL.
- [ ] An unrecognized `Downloader` failure fails as Failed (other) without crashing the Job.
- [ ] After any failed Job, no partial/temp files remain in the Download Directory.

## Blocked by

- [#01 Tracer bullet: paste URL → Job → Download → done → serve file](01-tracer-bullet-download.md)
