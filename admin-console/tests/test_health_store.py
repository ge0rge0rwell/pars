from pars_admin.health_store import HealthStore
from pars_shared.protocol import HealthReportMessage


def test_apply_report_then_get_returns_latest(tmp_path):
    store = HealthStore(str(tmp_path / "health.sqlite3"))
    message = HealthReportMessage(
        hostname="itlab-03",
        disk_free_percent=42.5,
        pending_apt_updates=3,
        failed_systemd_units=0,
    )

    store.apply_report(message)

    record = store.get("itlab-03")
    assert record.disk_free_percent == 42.5
    assert record.pending_apt_updates == 3
    assert record.failed_systemd_units == 0


def test_second_report_overwrites_first(tmp_path):
    store = HealthStore(str(tmp_path / "health.sqlite3"))
    store.apply_report(
        HealthReportMessage(
            hostname="itlab-03",
            disk_free_percent=42.5,
            pending_apt_updates=3,
            failed_systemd_units=0,
        )
    )

    store.apply_report(
        HealthReportMessage(
            hostname="itlab-03",
            disk_free_percent=10.0,
            pending_apt_updates=0,
            failed_systemd_units=1,
        )
    )

    record = store.get("itlab-03")
    assert record.disk_free_percent == 10.0
    assert record.failed_systemd_units == 1


def test_get_unknown_hostname_returns_none(tmp_path):
    store = HealthStore(str(tmp_path / "health.sqlite3"))

    assert store.get("ghost-01") is None
