from __future__ import annotations

import json
import os
from pathlib import Path


def _default_download_dir() -> Path:
    return Path(os.environ.get("SMVD_DOWNLOAD_DIR", Path.home() / "Downloads"))


class Config:
    """User-facing settings, persisted as JSON under the XDG config dir."""

    def __init__(self, config_dir: Path | None = None, data_dir: Path | None = None, download_dir: Path | None = None):
        self.config_dir = config_dir or Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "smvd"
        self.data_dir = data_dir or Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "smvd"
        self._config_file = self.config_dir / "config.json"
        self._settings: dict = {}
        self._download_dir = download_dir or _default_download_dir()
        self._load()

    def _load(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if self._config_file.exists():
            try:
                self._settings = json.loads(self._config_file.read_text())
            except (json.JSONDecodeError, OSError):
                self._settings = {}
        if self._settings.get("download_dir"):
            self._download_dir = Path(self._settings["download_dir"])
        if not self._config_file.exists():
            self._save()

    def _save(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._config_file.write_text(json.dumps(self._settings, indent=2))

    @property
    def download_dir(self) -> Path:
        return self._download_dir

    def set_download_dir(self, path: Path) -> None:
        self._download_dir = Path(path).expanduser()
        self._settings["download_dir"] = str(self._download_dir)
        self._save()
