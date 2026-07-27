import csv

from pars_admin.audit import AuditLog


def _log(tmp_path):
    return AuditLog(str(tmp_path / "audit.sqlite3"))


def test_record_and_list_round_trip(tmp_path):
    log = _log(tmp_path)

    log.record(
        subject="teacher.ayse",
        hostname="itlab-03",
        session_kind="open",
        started_at="2026-07-25T09:00:00Z",
        ended_at=None,
    )

    events = log.list_events()
    assert len(events) == 1
    assert events[0].subject == "teacher.ayse"
    assert events[0].hostname == "itlab-03"
    assert events[0].session_kind == "open"
    assert events[0].ended_at is None


def test_events_preserve_insertion_order(tmp_path):
    log = _log(tmp_path)
    log.record("teacher.ayse", "itlab-03", "open", "2026-07-25T09:00:00Z", None)
    log.record("admin.root", "itlab-03", "preempt", "2026-07-25T09:05:00Z", None)
    log.record(
        "teacher.ayse",
        "itlab-03",
        "open",
        "2026-07-25T09:00:00Z",
        "2026-07-25T09:05:00Z",
    )

    events = log.list_events()

    assert [e.session_kind for e in events] == ["open", "preempt", "open"]


def test_no_update_or_delete_api_exists():
    assert not hasattr(AuditLog, "update")
    assert not hasattr(AuditLog, "delete")


def test_export_csv_contains_every_event_in_order(tmp_path):
    log = _log(tmp_path)
    log.record("teacher.ayse", "itlab-03", "open", "2026-07-25T09:00:00Z", None)
    log.record(
        "admin.root",
        "itlab-04",
        "revoke",
        "2026-07-25T09:10:00Z",
        "2026-07-25T09:10:00Z",
    )
    csv_path = tmp_path / "export.csv"

    log.export_csv(str(csv_path))

    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["subject"] == "teacher.ayse"
    assert rows[1]["hostname"] == "itlab-04"


def test_export_pdf_produces_nonempty_file(tmp_path):
    log = _log(tmp_path)
    log.record("teacher.ayse", "itlab-03", "open", "2026-07-25T09:00:00Z", None)
    pdf_path = tmp_path / "export.pdf"

    log.export_pdf(str(pdf_path))

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
    assert pdf_path.read_bytes().startswith(b"%PDF")
