import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path

_STOP_WAIT_TIMEOUT_SECONDS = 5


class SessionVideoRecorder:
    def __init__(
        self,
        storage_dir: Path,
        ffmpeg_binary: str = "ffmpeg",
        display: str = ":0",
        popen=subprocess.Popen,
    ):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._ffmpeg_binary = ffmpeg_binary
        self._display = display
        self._popen = popen
        self._process = None

    def start(self, label: str) -> Path:
        if self._process is not None:
            raise ValueError("recording already in progress")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        path = self._storage_dir / f"{label}-{timestamp}.mp4"
        cmd = [
            self._ffmpeg_binary,
            "-f",
            "x11grab",
            "-i",
            self._display,
            "-y",
            str(path),
        ]
        try:
            self._process = self._popen(cmd, stdin=subprocess.PIPE)
        except (FileNotFoundError, OSError):
            return None
        return path

    def stop(self) -> None:
        if self._process is None:
            return

        try:
            self._process.send_signal(signal.SIGINT)
            self._process.wait(timeout=_STOP_WAIT_TIMEOUT_SECONDS)
        except (TimeoutError, subprocess.TimeoutExpired):
            self._process.terminate()
        finally:
            self._process = None
