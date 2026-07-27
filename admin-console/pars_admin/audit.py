import csv
import sqlite3
from dataclasses import dataclass

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

_CSV_FIELDS = ("subject", "hostname", "session_kind", "started_at", "ended_at")


@dataclass(frozen=True)
class AuditEvent:
    subject: str
    hostname: str
    session_kind: str
    started_at: str
    ended_at: str


class AuditLog:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                hostname TEXT NOT NULL,
                session_kind TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT
            )
            """
        )
        self._conn.commit()

    def record(
        self, subject: str, hostname: str, session_kind: str, started_at: str, ended_at
    ) -> None:
        self._conn.execute(
            "INSERT INTO events (subject, hostname, session_kind, started_at, ended_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (subject, hostname, session_kind, started_at, ended_at),
        )
        self._conn.commit()

    def list_events(self) -> list:
        rows = self._conn.execute(
            "SELECT subject, hostname, session_kind, started_at, ended_at "
            "FROM events ORDER BY id ASC"
        ).fetchall()
        return [AuditEvent(*row) for row in rows]

    def export_csv(self, path: str) -> None:
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
            writer.writeheader()
            for event in self.list_events():
                writer.writerow({field: getattr(event, field) for field in _CSV_FIELDS})

    def export_pdf(self, path: str) -> None:
        pdf = canvas.Canvas(path, pagesize=A4)
        _, page_height = A4
        y = page_height - 40
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "Pars audit log")
        pdf.setFont("Helvetica", 9)
        y -= 24
        for event in self.list_events():
            line = (
                f"{event.started_at}  {event.subject}  {event.hostname}  "
                f"{event.session_kind}  ended={event.ended_at or '-'}"
            )
            pdf.drawString(40, y, line)
            y -= 14
            if y < 40:
                pdf.showPage()
                y = page_height - 40
        pdf.save()
