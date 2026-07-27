from twisted.test import proto_helpers

from pars_admin.broker.authz import GrantGatedBroker
from pars_admin.broker.main import BrokerSessionFactory
from pars_shared import crypto, grant
from pars_shared.grant import to_wire_dict
from pars_shared.protocol import BrokerSessionRequestMessage, from_json, to_json


class _FakeEpoptesLink:
    def __init__(self):
        self.forwarded_calls = []

    def send_command(self, handle, command):
        self.forwarded_calls.append((handle, command))
        return f"ran:{command}"


def _issue(priv, pub, target_hostname="itlab-03"):
    return grant.build_and_sign(
        grant_id="g-1",
        issued_at="2026-07-23T00:00:00Z",
        admin_instance_id="school-42",
        admin_private_key=priv,
        admin_public_key=pub,
        subject="teacher.ayse",
        subject_kind="teacher",
        target_hostname=target_hostname,
        target_cert_fingerprint="ab:cd",
        session_mode="control",
        grant_kind="open",
    )


def _make_protocol(gated_broker):
    factory = BrokerSessionFactory(gated_broker)
    proto = factory.buildProtocol(("127.0.0.1", 0))
    transport = proto_helpers.StringTransport()
    proto.makeConnection(transport)
    return proto, transport


def test_valid_session_request_forwards_and_replies_success():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    gated = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)
    proto, transport = _make_protocol(gated)

    g = _issue(priv, pub)
    message = BrokerSessionRequestMessage(action="control", grant=to_wire_dict(g))
    proto.lineReceived(to_json(message).encode("utf-8"))

    sent = transport.value()
    response = from_json(sent.split(b"\r\n")[0].decode("utf-8"))
    assert response.success is True
    assert link.forwarded_calls == [("itlab-03", "control")]


def test_invalid_grant_replies_failure_not_forwarded():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    gated = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)
    proto, transport = _make_protocol(gated)

    g = _issue(priv, pub)
    wire = to_wire_dict(g)
    wire["target_hostname"] = "itlab-99"
    message = BrokerSessionRequestMessage(action="control", grant=wire)
    proto.lineReceived(to_json(message).encode("utf-8"))

    sent = transport.value()
    response = from_json(sent.split(b"\r\n")[0].decode("utf-8"))
    assert response.success is False
    assert response.error != ""
    assert link.forwarded_calls == []


def test_malformed_input_replies_failure_not_raise():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    gated = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)
    proto, transport = _make_protocol(gated)

    proto.lineReceived(b"not json")

    sent = transport.value()
    response = from_json(sent.split(b"\r\n")[0].decode("utf-8"))
    assert response.success is False
