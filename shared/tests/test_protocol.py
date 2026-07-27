import pytest

from pars_shared import crypto, grant, protocol


def _sample_grant():
    priv, pub = crypto.generate_keypair()
    return grant.build_and_sign(
        grant_id="g-1",
        issued_at="2026-07-23T00:00:00Z",
        admin_instance_id="school-42",
        admin_private_key=priv,
        admin_public_key=pub,
        subject="teacher.ayse",
        subject_kind="teacher",
        target_hostname="itlab-03",
        target_cert_fingerprint="ab:cd",
        session_mode="control",
        grant_kind="open",
    )


def test_register_message_roundtrip():
    msg = protocol.RegisterMessage(
        hostname="itlab-03",
        cert_fingerprint="ab:cd",
        cert_pubkey="deadbeef",
        current_ip="10.0.1.5",
        agent_version="0.1.0",
    )
    raw = protocol.to_json(msg)
    parsed = protocol.from_json(raw)
    assert parsed == msg
    assert isinstance(parsed, protocol.RegisterMessage)


def test_enrollment_result_roundtrip():
    msg = protocol.EnrollmentResultMessage(
        approved=True, admin_instance_id="school-42", admin_pubkey="cafe"
    )
    parsed = protocol.from_json(protocol.to_json(msg))
    assert parsed == msg


def test_machine_list_request_roundtrip():
    msg = protocol.MachineListRequestMessage(username="teacher.ayse")
    parsed = protocol.from_json(protocol.to_json(msg))
    assert parsed == msg
    assert isinstance(parsed, protocol.MachineListRequestMessage)


def test_machine_list_result_roundtrip():
    msg = protocol.MachineListResultMessage(hostnames=["itlab-03", "itlab-04"])
    parsed = protocol.from_json(protocol.to_json(msg))
    assert parsed == msg


def test_from_json_rejects_unknown_type():
    with pytest.raises(ValueError):
        protocol.from_json('{"msg_type": "nonsense"}')


def test_from_json_rejects_malformed_payload():
    with pytest.raises(ValueError):
        protocol.from_json('{"msg_type": "register", "hostname": "x"}')


def test_login_request_roundtrip():
    msg = protocol.LoginRequestMessage(username="teacher.ayse", password="s3cret")
    parsed = protocol.from_json(protocol.to_json(msg))
    assert parsed == msg
    assert isinstance(parsed, protocol.LoginRequestMessage)


def test_login_result_roundtrip():
    msg = protocol.LoginResultMessage(success=False, reason="invalid credentials")
    parsed = protocol.from_json(protocol.to_json(msg))
    assert parsed == msg


def test_broker_session_request_roundtrip():
    g = _sample_grant()
    msg = protocol.BrokerSessionRequestMessage(
        action="view", grant=grant.to_wire_dict(g)
    )
    parsed = protocol.from_json(protocol.to_json(msg))
    assert isinstance(parsed, protocol.BrokerSessionRequestMessage)
    assert parsed.action == "view"
    rebuilt_grant = grant.from_wire_dict(parsed.grant)
    assert rebuilt_grant == g
