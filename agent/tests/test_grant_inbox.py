import json

from pars_agent.grant_inbox import check_inbox
from pars_agent.grant_verify import GrantVerifier
from pars_shared import crypto, grant


def _issue(priv, pub, grant_id="g-1", grant_kind="open", target_hostname="itlab-03"):
    return grant.build_and_sign(
        grant_id=grant_id,
        issued_at="2026-07-23T00:00:00Z",
        admin_instance_id="school-42",
        admin_private_key=priv,
        admin_public_key=pub,
        subject="teacher.ayse",
        subject_kind="teacher",
        target_hostname=target_hostname,
        target_cert_fingerprint="ab:cd",
        session_mode="control",
        grant_kind=grant_kind,
    )


def _drop(inbox_dir, name, wire_grant):
    (inbox_dir / name).write_text(json.dumps(wire_grant))


def test_check_inbox_applies_dropped_grant_and_consumes_file(tmp_path):
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    _drop(tmp_path, "g-1.json", grant.to_wire_dict(_issue(priv, pub)))

    results = check_inbox(verifier, tmp_path)

    assert results == [True]
    assert verifier.active_session_subject() == "teacher.ayse"
    assert list(tmp_path.glob("*.json")) == []


def test_check_inbox_empty_dir_returns_empty(tmp_path):
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")

    assert check_inbox(verifier, tmp_path) == []


def test_check_inbox_malformed_file_is_consumed_not_raised(tmp_path):
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    (tmp_path / "bad.json").write_text("not json")

    results = check_inbox(verifier, tmp_path)

    assert results == [False]
    assert list(tmp_path.glob("*.json")) == []
