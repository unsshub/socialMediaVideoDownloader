Status: done

# Configurable Download Directory

## Parent

[Video Downloader PRD](../PRD.md)

## What to build

The Download Directory is a user setting, not a constant. A small Settings area in the UI lets the user pick the folder; the choice persists across restarts; the default is the system downloads folder.

- Setting is stored in a JSON config file under the app's XDG config directory.
- API to read and update the setting; the Job engine reads the current setting when a Download starts.

## Acceptance criteria

- [ ] The UI exposes a Settings area showing the current Download Directory.
- [ ] Changing it takes effect for subsequent Downloads and persists across restarts.
- [ ] The default is the system downloads folder.
- [ ] The config file is created on first run.

## Blocked by

- [#01 Tracer bullet: paste URL → Job → Download → done → serve file](01-tracer-bullet-download.md)
