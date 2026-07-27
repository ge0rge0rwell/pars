from pars_admin.app import AdminApp
from pars_shared.protocol import HealthReportMessage, RegisterMessage


def _app(tmp_path):
    return AdminApp(
        data_dir=str(tmp_path / "trust"),
        registry_db_path=str(tmp_path / "registry.sqlite3"),
        audit_db_path=str(tmp_path / "audit.sqlite3"),
        staging_db_path=str(tmp_path / "staging.sqlite3"),
    )


def test_bulk_import_then_enrollment_auto_applies_room_type(tmp_path):
    app = _app(tmp_path)
    csv_path = tmp_path / "machines.csv"
    csv_path.write_text("hostname,room_type\nitlab-03,it_lab\n")

    count = app.bulk_import(str(csv_path))
    app.handle_registration(
        RegisterMessage(
            hostname="itlab-03",
            cert_fingerprint="ab:cd",
            cert_pubkey="00" * 32,
            current_ip="10.0.1.5",
            agent_version="0.1.0",
        )
    )

    assert count == 1
    assert app.list_machines()[0].room_type == "it_lab"


def test_approve_then_open_session_records_audit_event(tmp_path):
    app = _app(tmp_path)
    app.registry.upsert("itlab-03", "it_lab", "ab:cd", "pending")
    app.approve_enrollment("itlab-03")

    grants = app.open_session("teacher.ayse", "teacher", "itlab-03", "control")

    assert len(grants) == 1
    events = app.audit.list_events()
    assert len(events) == 1
    assert events[0].subject == "teacher.ayse"
    assert events[0].session_kind == "open"
    assert events[0].ended_at is None


def test_kill_session_records_terminal_audit_event(tmp_path):
    app = _app(tmp_path)
    app.registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")
    app.open_session("teacher.ayse", "teacher", "itlab-03", "control")

    grant = app.kill_session("itlab-03")

    assert grant.grant_kind == "revoke"
    events = app.audit.list_events()
    assert events[-1].session_kind == "revoke"
    assert events[-1].ended_at is not None


def test_export_and_backup_produce_files(tmp_path):
    app = _app(tmp_path)
    app.registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")
    app.open_session("teacher.ayse", "teacher", "itlab-03", "control")
    csv_path = tmp_path / "out.csv"
    backup_path = tmp_path / "backup.tar.gz"

    app.export_audit_csv(str(csv_path))
    app.create_backup(str(backup_path))

    assert csv_path.exists()
    assert backup_path.exists()


def test_get_health_reflects_applied_report(tmp_path):
    app = _app(tmp_path)

    app.health.apply_report(
        HealthReportMessage(
            hostname="itlab-03",
            disk_free_percent=42.5,
            pending_apt_updates=3,
            failed_systemd_units=0,
        )
    )

    record = app.get_health("itlab-03")
    assert record.disk_free_percent == 42.5


def test_create_teacher_account_then_handle_login_succeeds(tmp_path):
    from pars_shared.protocol import LoginRequestMessage

    app = _app(tmp_path)
    app.create_teacher_account("teacher.ayse", "correct horse battery staple")

    result = app.handle_login(
        LoginRequestMessage(
            username="teacher.ayse", password="correct horse battery staple"
        )
    )

    assert result.success is True


def test_handle_login_wrong_password_fails(tmp_path):
    from pars_shared.protocol import LoginRequestMessage

    app = _app(tmp_path)
    app.create_teacher_account("teacher.ayse", "correct horse battery staple")

    result = app.handle_login(
        LoginRequestMessage(username="teacher.ayse", password="wrong")
    )

    assert result.success is False


def test_handle_login_unknown_account_fails(tmp_path):
    from pars_shared.protocol import LoginRequestMessage

    app = _app(tmp_path)

    result = app.handle_login(
        LoginRequestMessage(username="ghost", password="anything")
    )

    assert result.success is False
