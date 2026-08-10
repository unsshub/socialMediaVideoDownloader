Status: done

# Launch experience

## Parent

[Video Downloader PRD](../PRD.md)

## What to build

Starting the app is one command with zero ceremony. `python -m smvd` starts the server, binds to `localhost` only, prints the URL, and auto-opens the default browser. Uses a fixed port with a fallback if that port is occupied.

## Acceptance criteria

- [ ] `python -m smvd` starts the server.
- [ ] The server binds to `localhost` only (not reachable from the LAN).
- [ ] The URL is printed to stdout.
- [ ] The default browser opens to the app automatically.
- [ ] If the fixed port is occupied, a fallback port is used.

## Blocked by

- [#01 Tracer bullet: paste URL → Job → Download → done → serve file](01-tracer-bullet-download.md)
