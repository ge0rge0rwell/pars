import shutil
import subprocess
from dataclasses import dataclass

_SUBPROCESS_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class HealthReport:
    disk_free_percent: float
    pending_apt_updates: int
    failed_systemd_units: int


def _disk_free_percent(path: str = "/") -> float:
    usage = shutil.disk_usage(path)
    return (usage.free / usage.total) * 100.0


def _run_output_lines(cmd: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=_SUBPROCESS_TIMEOUT_SECONDS
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
    if result.returncode not in (0, 1):
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _pending_apt_updates() -> int:
    lines = _run_output_lines(["apt", "list", "--upgradable"])
    if not lines:
        return 0
    return max(len(lines) - 1, 0)


def _failed_systemd_units() -> int:
    return len(_run_output_lines(["systemctl", "--failed", "--no-legend"]))


def collect_health() -> HealthReport:
    return HealthReport(
        disk_free_percent=_disk_free_percent(),
        pending_apt_updates=_pending_apt_updates(),
        failed_systemd_units=_failed_systemd_units(),
    )
