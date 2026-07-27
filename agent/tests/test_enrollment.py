import os
import stat
import tempfile

from pars_agent import enrollment


def test_generates_identity_on_first_run():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = os.path.join(tmp, "data")
        identity = enrollment.ensure_agent_identity(data_dir)
        assert len(identity.private_key) == 32
        assert len(identity.public_key) == 32
        assert identity.fingerprint.count(":") == 31


def test_idempotent_across_restarts():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = os.path.join(tmp, "data")
        first = enrollment.ensure_agent_identity(data_dir)
        second = enrollment.ensure_agent_identity(data_dir)
        assert first == second


def test_deleting_keys_produces_different_identity():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = os.path.join(tmp, "data")
        first = enrollment.ensure_agent_identity(data_dir)
        os.remove(os.path.join(data_dir, "identity.key"))
        os.remove(os.path.join(data_dir, "identity.pub"))
        second = enrollment.ensure_agent_identity(data_dir)
        assert first.fingerprint != second.fingerprint


def test_private_key_file_is_owner_only():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = os.path.join(tmp, "data")
        enrollment.ensure_agent_identity(data_dir)
        mode = os.stat(os.path.join(data_dir, "identity.key")).st_mode
        assert stat.S_IMODE(mode) == 0o600
