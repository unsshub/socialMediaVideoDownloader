# Video Downloader

A local web application that downloads videos from social media platforms to the user's computer.

## Language

**Video**:
A moving-picture media item posted on a supported social platform, downloaded to the user's computer. Images, audio-only tracks, and entire post collections (carousels/albums) are out of scope.
_Avoid_: Media, clip, asset

**Platform**:
A supported social media site from which videos can be downloaded. Currently: YouTube, TikTok, Instagram, Facebook.
_Avoid_: Site, social network, source

**Download**:
The operation of fetching a single Video from a Platform and saving it locally.
_Avoid_: Grab, save, fetch

**Job**:
The tracked unit of work for a single Download, carrying a lifecycle state (pending, downloading, done, failed), progress, and an outcome. Lives in memory while active and is recorded in history when finished.
_Avoid_: Task, entry, request

**Download Directory**:
The local folder where finished Videos are saved. Configurable by the user, defaulting to their downloads folder.
_Avoid_: Output folder, save location

## Failure states

**Unsupported URL**:
The pasted text contained no URL, or the URL's platform is not supported by the downloader.
_Avoid_: Bad link

**Private**:
The Video requires a login or is otherwise not publicly accessible. Downloading is not attempted.
_Avoid_: Login required, gated

**Unavailable**:
The Video was deleted, removed, geo-blocked, or could not be extracted from the platform.
_Avoid_: Missing, broken

**Network error**:
The downloader could not reach the platform to fetch the Video.

**Failed (other)**:
Any failure that does not fit the categories above.
