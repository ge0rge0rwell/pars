import subprocess
from datetime import datetime, timezone
from pathlib import Path

_CAPTURE_TIMEOUT_SECONDS = 10


class ScreenshotRecorder:
    def __init__(
        self,
        storage_dir: Path,
        capture_cmd=("gnome-screenshot", "-f"),
        runner=subprocess.run,
    ):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._capture_cmd = capture_cmd
        self._runner = runner

    def capture(self, label: str) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        path = self._storage_dir / f"{label}-{timestamp}.png"
        try:
            result = self._runner(
                [*self._capture_cmd, str(path)],
                capture_output=True,
                timeout=_CAPTURE_TIMEOUT_SECONDS,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return None
        if result.returncode != 0:
            return None
        return path
