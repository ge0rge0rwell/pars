from pars_admin.registry import Registry


def test_upsert_new_hostname_creates_record(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))

    result = registry.upsert(
        hostname="itlab-03",
        room_type="it_lab",
        cert_fingerprint="ab:cd",
        enrollment_status="pending",
    )

    assert result.conflict is False
    record = registry.get("itlab-03")
    assert record.hostname == "itlab-03"
    assert record.room_type == "it_lab"
    assert record.cert_fingerprint == "ab:cd"
    assert record.enrollment_status == "pending"


def test_upsert_same_fingerprint_updates_fields(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    registry.upsert("itlab-03", "it_lab", "ab:cd", "pending")

    result = registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")

    assert result.conflict is False
    assert registry.get("itlab-03").enrollment_status == "approved"


def test_upsert_different_fingerprint_is_a_conflict_not_overwritten(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")

    result = registry.upsert("itlab-03", "it_lab", "ff:ff", "pending")

    assert result.conflict is True
    record = registry.get("itlab-03")
    assert record.cert_fingerprint == "ab:cd"
    assert record.enrollment_status == "approved"


def test_get_unknown_hostname_returns_none(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))

    assert registry.get("nope") is None


def test_list_all_returns_every_record(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")
    registry.upsert("itlab-04", "it_lab", "11:22", "approved")

    hostnames = {r.hostname for r in registry.list_all()}

    assert hostnames == {"itlab-03", "itlab-04"}


def test_delete_removes_record(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")

    registry.delete("itlab-03")

    assert registry.get("itlab-03") is None
