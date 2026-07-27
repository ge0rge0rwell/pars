from pars_admin.trust_root import ensure_admin_trust_root


def test_first_run_creates_keypair_and_instance_id(tmp_path):
    root = ensure_admin_trust_root(str(tmp_path))

    assert root.admin_instance_id
    assert len(root.public_key) == 32
    assert len(root.private_key) == 32
    assert root.fingerprint


def test_rerun_does_not_overwrite_trust_root(tmp_path):
    first = ensure_admin_trust_root(str(tmp_path))

    second = ensure_admin_trust_root(str(tmp_path))

    assert second.admin_instance_id == first.admin_instance_id
    assert second.public_key == first.public_key
    assert second.private_key == first.private_key
