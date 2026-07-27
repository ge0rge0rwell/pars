from pars_agent.health import collect_health


def test_collect_health_returns_expected_fields():
    report = collect_health()
    assert 0.0 <= report.disk_free_percent <= 100.0
    assert report.pending_apt_updates >= 0
    assert report.failed_systemd_units >= 0
