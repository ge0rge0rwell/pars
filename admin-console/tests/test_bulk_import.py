from pars_admin.bulk_import import BulkImportStaging


def _write_csv(path, rows):
    path.write_text(
        "hostname,room_type\n" + "\n".join(f"{h},{r}" for h, r in rows) + "\n"
    )


def test_import_csv_stages_room_types(tmp_path):
    csv_path = tmp_path / "machines.csv"
    _write_csv(csv_path, [("itlab-03", "it_lab"), ("office-01", "office")])
    staging = BulkImportStaging(str(tmp_path / "staging.sqlite3"))

    count = staging.import_csv(str(csv_path))

    assert count == 2
    assert staging.get_room_type("itlab-03") == "it_lab"
    assert staging.get_room_type("office-01") == "office"


def test_get_room_type_unknown_hostname_returns_none(tmp_path):
    staging = BulkImportStaging(str(tmp_path / "staging.sqlite3"))

    assert staging.get_room_type("ghost-01") is None


def test_reimport_overwrites_prior_staged_value(tmp_path):
    csv_path = tmp_path / "machines.csv"
    staging = BulkImportStaging(str(tmp_path / "staging.sqlite3"))
    _write_csv(csv_path, [("itlab-03", "office")])
    staging.import_csv(str(csv_path))

    _write_csv(csv_path, [("itlab-03", "it_lab")])
    staging.import_csv(str(csv_path))

    assert staging.get_room_type("itlab-03") == "it_lab"
