import pytest

from pars_admin.broker.authz import BrokerAuthzError, GrantGatedBroker
from pars_admin.broker.broker_server import (
    process_broker_grant_delivery,
    process_broker_session_request,
)
from pars_admin.broker.grant_delivery import build_delivery_command
from pars_shared import crypto, grant
from pars_shared.grant import to_wire_dict
from pars_shared.protocol import BrokerGrantDeliveryMessage, BrokerSessionRequestMessage


class _FakeEpoptesLink:
    def __init__(self):
        self.forwarded_calls = []

    def send_command(self, handle, command):
        self.forwarded_calls.append((handle, command))
        return f"ran:{command}"


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


def test_valid_session_request_forwards_control_command():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    gated = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)
    g = _issue(priv, pub)
    message = BrokerSessionRequestMessage(action="control", grant=to_wire_dict(g))

    result = process_broker_session_request(gated, message)

    assert result == "ran:control"
    assert link.forwarded_calls == [("itlab-03", "control")]


def test_tampered_grant_raises_before_forwarding():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    gated = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)
    g = _issue(priv, pub)
    wire = to_wire_dict(g)
    wire["target_hostname"] = "itlab-99"
    message = BrokerSessionRequestMessage(action="control", grant=wire)

    with pytest.raises(BrokerAuthzError):
        process_broker_session_request(gated, message)
    assert link.forwarded_calls == []


def test_unknown_action_raises():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    gated = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)
    g = _issue(priv, pub)
    message = BrokerSessionRequestMessage(action="detonate", grant=to_wire_dict(g))

    with pytest.raises(ValueError):
        process_broker_session_request(gated, message)
    assert link.forwarded_calls == []


def test_grant_delivery_pushes_revoke_grant_to_target_hostname():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    gated = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)
    g = _issue(priv, pub, grant_kind="revoke", target_hostname="itlab-05")
    message = BrokerGrantDeliveryMessage(grant=to_wire_dict(g))

    result = process_broker_grant_delivery(gated, message)

    expected_command = build_delivery_command(to_wire_dict(g))
    assert result == f"ran:{expected_command}"
    assert link.forwarded_calls == [("itlab-05", expected_command)]


def test_grant_delivery_rejects_open_grant():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    gated = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)
    g = _issue(priv, pub, grant_kind="open", target_hostname="itlab-05")
    message = BrokerGrantDeliveryMessage(grant=to_wire_dict(g))

    with pytest.raises(BrokerAuthzError):
        process_broker_grant_delivery(gated, message)
    assert link.forwarded_calls == []
