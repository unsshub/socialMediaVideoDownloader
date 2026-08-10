# yt-dlp as the download engine

We delegate video extraction to the `yt-dlp` library instead of writing per-platform scrapers, because yt-dlp is actively maintained against TikTok, Instagram, and Facebook's ever-changing internal APIs and obfuscation. The app wraps yt-dlp in a thin adapter so the extraction layer can be swapped without touching the Job engine.

This carries real lock-in: our error-category mapping and progress reporting key off yt-dlp's output shapes. That is accepted in exchange for not re-implementing platform reverse-engineering. We also require `ffmpeg` on the host, because merging best-quality video+audio into MP4 is done by yt-dlp's post-processors.
