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


def test_valid_open_grant_is_accepted():
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    g = _issue(priv, pub)
    assert verifier.accept(g) is True


def test_grant_for_wrong_hostname_is_rejected():
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-99")
    g = _issue(priv, pub, target_hostname="itlab-03")
    assert verifier.accept(g) is False


def test_replayed_grant_id_is_rejected():
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    g = _issue(priv, pub, grant_id="g-1")
    assert verifier.accept(g) is True
    assert verifier.accept(g) is False


def test_badly_signed_grant_is_rejected():
    priv, pub = crypto.generate_keypair()
    _other_priv, other_pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=other_pub, own_hostname="itlab-03")
    g = _issue(priv, pub)
    assert verifier.accept(g) is False


def test_preempt_invalidates_active_open_session():
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    open_grant = _issue(priv, pub, grant_id="g-1", grant_kind="open")
    assert verifier.accept(open_grant) is True
    assert verifier.active_session_subject() == "teacher.ayse"

    preempt_grant = _issue(priv, pub, grant_id="g-2", grant_kind="preempt")
    assert verifier.accept(preempt_grant) is True
    assert verifier.active_session_subject() is None


def test_revoke_ends_active_session_outright():
    priv, pub = crypto.generate_keypair()
    verifier = GrantVerifier(pinned_admin_pubkey=pub, own_hostname="itlab-03")
    verifier.accept(_issue(priv, pub, grant_id="g-1", grant_kind="open"))
    assert verifier.active_session_subject() == "teacher.ayse"

    verifier.accept(_issue(priv, pub, grant_id="g-2", grant_kind="revoke"))
    assert verifier.active_session_subject() is None
