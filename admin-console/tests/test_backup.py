import tarfile

import pytest

from pars_admin.backup import create_backup, restore_backup
from pars_admin.registry import Registry
from pars_admin.trust_root import ensure_admin_trust_root


def test_backup_and_restore_recovers_registry_and_trust_root(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    registry = Registry(str(source_dir / "registry.sqlite3"))
    registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")
    original_root = ensure_admin_trust_root(str(source_dir))

    archive_path = tmp_path / "backup.tar.gz"
    create_backup(
        [
            str(source_dir / "registry.sqlite3"),
            str(source_dir / "admin_instance_id"),
            str(source_dir / "trust_root.key"),
            str(source_dir / "trust_root.pub"),
        ],
        str(archive_path),
    )

    restore_dir = tmp_path / "restored"
    restore_backup(str(archive_path), str(restore_dir))

    restored_registry = Registry(str(restore_dir / "registry.sqlite3"))
    assert restored_registry.get("itlab-03").cert_fingerprint == "ab:cd"

    restored_root = ensure_admin_trust_root(str(restore_dir))
    assert restored_root.admin_instance_id == original_root.admin_instance_id
    assert restored_root.private_key == original_root.private_key


def test_restore_into_fresh_dir_creates_it(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    ensure_admin_trust_root(str(source_dir))
    archive_path = tmp_path / "backup.tar.gz"
    create_backup([str(source_dir / "admin_instance_id")], str(archive_path))

    restore_dir = tmp_path / "does" / "not" / "exist" / "yet"
    restore_backup(str(archive_path), str(restore_dir))

    assert (restore_dir / "admin_instance_id").exists()


def test_restore_rejects_path_traversal_member(tmp_path):
    evil_file = tmp_path / "evil.txt"
    evil_file.write_text("pwned")
    archive_path = tmp_path / "evil.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(str(evil_file), arcname="../../etc/pwned")

    with pytest.raises(ValueError):
        restore_backup(str(archive_path), str(tmp_path / "restore_target"))
