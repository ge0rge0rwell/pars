import tempfile

from pars_agent.admin_pin import AdminPinStore
from pars_shared import crypto


def test_first_admin_contact_is_pinned():
    _priv, pub = crypto.generate_keypair()
    with tempfile.TemporaryDirectory() as tmp:
        store = AdminPinStore(data_dir=tmp)
        result = store.pin_or_verify(admin_instance_id="school-42", admin_pubkey=pub)
        assert result.accepted is True
        assert store.is_pinned() is True


def test_same_admin_instance_matches_on_later_contact():
    _priv, pub = crypto.generate_keypair()
    with tempfile.TemporaryDirectory() as tmp:
        store = AdminPinStore(data_dir=tmp)
        store.pin_or_verify(admin_instance_id="school-42", admin_pubkey=pub)

        result = store.pin_or_verify(admin_instance_id="school-42", admin_pubkey=pub)
        assert result.accepted is True


def test_different_admin_instance_id_is_rejected_as_conflict():
    _priv1, pub1 = crypto.generate_keypair()
    _priv2, pub2 = crypto.generate_keypair()
    with tempfile.TemporaryDirectory() as tmp:
        store = AdminPinStore(data_dir=tmp)
        store.pin_or_verify(admin_instance_id="school-42", admin_pubkey=pub1)

        result = store.pin_or_verify(
            admin_instance_id="school-99-rogue", admin_pubkey=pub2
        )
        assert result.accepted is False
        assert result.conflict is True


def test_same_instance_id_different_pubkey_is_rejected_as_conflict():
    _priv1, pub1 = crypto.generate_keypair()
    _priv2, pub2 = crypto.generate_keypair()
    with tempfile.TemporaryDirectory() as tmp:
        store = AdminPinStore(data_dir=tmp)
        store.pin_or_verify(admin_instance_id="school-42", admin_pubkey=pub1)

        result = store.pin_or_verify(admin_instance_id="school-42", admin_pubkey=pub2)
        assert result.accepted is False
        assert result.conflict is True


def test_pin_persists_across_restarts():
    _priv, pub = crypto.generate_keypair()
    with tempfile.TemporaryDirectory() as tmp:
        AdminPinStore(data_dir=tmp).pin_or_verify(
            admin_instance_id="school-42", admin_pubkey=pub
        )

        reloaded = AdminPinStore(data_dir=tmp)
        assert reloaded.is_pinned() is True
        result = reloaded.pin_or_verify(admin_instance_id="school-42", admin_pubkey=pub)
        assert result.accepted is True
