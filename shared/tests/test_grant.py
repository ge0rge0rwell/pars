import dataclasses

from pars_shared import crypto, grant


def _make_grant(priv, pub, **overrides):
    fields = dict(
        grant_id="g-1",
        issued_at="2026-07-23T00:00:00Z",
        admin_instance_id="school-42",
        admin_private_key=priv,
        admin_public_key=pub,
        subject="teacher.ayse",
        subject_kind="teacher",
        target_hostname="itlab-03",
        target_cert_fingerprint="ab:cd:ef",
        session_mode="control",
        grant_kind="open",
    )
    fields.update(overrides)
    return grant.build_and_sign(**fields)


def test_valid_grant_verifies():
    priv, pub = crypto.generate_keypair()
    g = _make_grant(priv, pub)
    assert grant.verify_grant(g, pub) is True


def test_tampered_field_fails_verify():
    priv, pub = crypto.generate_keypair()
    g = _make_grant(priv, pub)
    tampered = dataclasses.replace(g, target_hostname="itlab-99")
    assert grant.verify_grant(tampered, pub) is False


def test_forged_issuer_pubkey_does_not_bypass_verify():
    priv, pub = crypto.generate_keypair()
    _other_priv, other_pub = crypto.generate_keypair()
    g = _make_grant(priv, pub)
    forged = dataclasses.replace(g, issuer_pubkey=other_pub)
    assert grant.verify_grant(forged, pub) is False
    assert grant.verify_grant(forged, other_pub) is False


def test_invalid_grant_kind_rejected_at_construction():
    priv, pub = crypto.generate_keypair()
    try:
        _make_grant(priv, pub, grant_kind="delete_everything")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_wire_dict_roundtrip_preserves_verification():
    priv, pub = crypto.generate_keypair()
    g = _make_grant(priv, pub)

    wire = grant.to_wire_dict(g)
    assert all(isinstance(v, str) for v in wire.values())

    rebuilt = grant.from_wire_dict(wire)
    assert rebuilt == g
    assert grant.verify_grant(rebuilt, pub) is True


def test_wire_dict_tamper_is_caught_after_rebuild():
    priv, pub = crypto.generate_keypair()
    g = _make_grant(priv, pub)
    wire = grant.to_wire_dict(g)
    wire["target_hostname"] = "itlab-99"
    rebuilt = grant.from_wire_dict(wire)
    assert grant.verify_grant(rebuilt, pub) is False
