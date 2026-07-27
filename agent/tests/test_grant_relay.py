from pars_agent.grant_relay import apply_relayed_grant
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


def test_relayed_open_grant_sets_active_subject():
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    g = _issue(priv, pub)
    wire = grant.to_wire_dict(g)

    accepted = apply_relayed_grant(verifier, wire)

    assert accepted is True
    assert verifier.active_session_subject() == "teacher.ayse"


def test_relayed_revoke_grant_clears_active_subject():
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    apply_relayed_grant(verifier, grant.to_wire_dict(_issue(priv, pub, grant_id="g-1")))
    assert verifier.active_session_subject() == "teacher.ayse"

    revoke_wire = grant.to_wire_dict(
        _issue(priv, pub, grant_id="g-2", grant_kind="revoke")
    )
    accepted = apply_relayed_grant(verifier, revoke_wire)

    assert accepted is True
    assert verifier.active_session_subject() is None


def test_relayed_tampered_wire_grant_is_rejected():
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    wire = grant.to_wire_dict(_issue(priv, pub))
    wire["target_hostname"] = "itlab-99"

    accepted = apply_relayed_grant(verifier, wire)

    assert accepted is False
    assert verifier.active_session_subject() is None
