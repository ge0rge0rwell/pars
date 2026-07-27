import csv
import sqlite3


class BulkImportStaging:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS staged_machines "
            "(hostname TEXT PRIMARY KEY, room_type TEXT NOT NULL)"
        )
        self._conn.commit()

    def import_csv(self, path: str) -> int:
        count = 0
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                self._conn.execute(
                    "INSERT INTO staged_machines (hostname, room_type) VALUES (?, ?) "
                    "ON CONFLICT(hostname) DO UPDATE SET room_type = excluded.room_type",
                    (row["hostname"], row["room_type"]),
                )
                count += 1
        self._conn.commit()
        return count

    def get_room_type(self, hostname: str):
        row = self._conn.execute(
            "SELECT room_type FROM staged_machines WHERE hostname = ?", (hostname,)
        ).fetchone()
        return row[0] if row else None
