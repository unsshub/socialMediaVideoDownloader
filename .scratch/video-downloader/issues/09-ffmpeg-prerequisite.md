Status: done

# ffmpeg prerequisite check

## Parent

[Video Downloader PRD](../PRD.md)

## What to build

ffmpeg is required to merge best-quality video+audio into MP4 (ADR-0001). If it is missing, the app fails with a clear, actionable setup error instead of a cryptic crash.

- Check for ffmpeg availability (e.g. at startup or first merge).
- Surface a clear message telling the user to install ffmpeg.

## Acceptance criteria

- [ ] With ffmpeg absent, the app surfaces a clear "ffmpeg is required — install it" message rather than crashing obscurely.
- [ ] With ffmpeg present, no such error appears and Downloads proceed normally.

## Blocked by

- [#01 Tracer bullet: paste URL → Job → Download → done → serve file](01-tracer-bullet-download.md)
