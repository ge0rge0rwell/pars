import sqlite3
from dataclasses import dataclass

from pars_shared.protocol import HealthReportMessage


@dataclass(frozen=True)
class HealthRecord:
    hostname: str
    disk_free_percent: float
    pending_apt_updates: int
    failed_systemd_units: int


class HealthStore:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS health (
                hostname TEXT PRIMARY KEY,
                disk_free_percent REAL NOT NULL,
                pending_apt_updates INTEGER NOT NULL,
                failed_systemd_units INTEGER NOT NULL
            )
            """
        )
        self._conn.commit()

    def apply_report(self, message: HealthReportMessage) -> None:
        self._conn.execute(
            """
            INSERT INTO health
                (hostname, disk_free_percent, pending_apt_updates, failed_systemd_units)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(hostname) DO UPDATE SET
                disk_free_percent = excluded.disk_free_percent,
                pending_apt_updates = excluded.pending_apt_updates,
                failed_systemd_units = excluded.failed_systemd_units
            """,
            (
                message.hostname,
                message.disk_free_percent,
                message.pending_apt_updates,
                message.failed_systemd_units,
            ),
        )
        self._conn.commit()

    def get(self, hostname: str):
        row = self._conn.execute(
            "SELECT hostname, disk_free_percent, pending_apt_updates, failed_systemd_units "
            "FROM health WHERE hostname = ?",
            (hostname,),
        ).fetchone()
        return HealthRecord(*row) if row else None
