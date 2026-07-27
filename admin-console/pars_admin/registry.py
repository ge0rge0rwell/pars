from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class MachineRecord:
    hostname: str
    room_type: str
    cert_fingerprint: str
    enrollment_status: str


@dataclass(frozen=True)
class UpsertResult:
    conflict: bool


class Registry:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS machines (
                hostname TEXT PRIMARY KEY,
                room_type TEXT NOT NULL,
                cert_fingerprint TEXT NOT NULL,
                enrollment_status TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def upsert(
        self,
        hostname: str,
        room_type: str,
        cert_fingerprint: str,
        enrollment_status: str,
    ) -> UpsertResult:
        existing = self.get(hostname)
        if existing is not None and existing.cert_fingerprint != cert_fingerprint:
            return UpsertResult(conflict=True)

        self._conn.execute(
            """
            INSERT INTO machines (hostname, room_type, cert_fingerprint, enrollment_status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(hostname) DO UPDATE SET
                room_type = excluded.room_type,
                enrollment_status = excluded.enrollment_status
            """,
            (hostname, room_type, cert_fingerprint, enrollment_status),
        )
        self._conn.commit()
        return UpsertResult(conflict=False)

    def get(self, hostname: str) -> MachineRecord | None:
        row = self._conn.execute(
            "SELECT hostname, room_type, cert_fingerprint, enrollment_status "
            "FROM machines WHERE hostname = ?",
            (hostname,),
        ).fetchone()
        return MachineRecord(*row) if row else None

    def list_all(self) -> list[MachineRecord]:
        rows = self._conn.execute(
            "SELECT hostname, room_type, cert_fingerprint, enrollment_status FROM machines"
        ).fetchall()
        return [MachineRecord(*row) for row in rows]

    def delete(self, hostname: str) -> None:
        self._conn.execute("DELETE FROM machines WHERE hostname = ?", (hostname,))
        self._conn.commit()
