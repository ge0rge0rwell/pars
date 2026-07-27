import dataclasses

from pars_admin.broker.authz import BrokerAuthzError, GrantGatedBroker
from pars_shared import crypto, grant


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


def test_valid_grant_forwards_command():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    authz = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)

    g = _issue(priv, pub, target_hostname="itlab-03")
    result = authz.forward_command(
        g, handle="10.0.1.5:1234", command="ping", expected_hostname="itlab-03"
    )

    assert result == "ran:ping"
    assert link.forwarded_calls == [("10.0.1.5:1234", "ping")]


def test_tampered_grant_is_refused_before_forwarding():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    authz = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)

    g = _issue(priv, pub, target_hostname="itlab-03")
    tampered = dataclasses.replace(g, target_hostname="itlab-99")

    try:
        authz.forward_command(
            tampered,
            handle="10.0.1.5:1234",
            command="ping",
            expected_hostname="itlab-99",
        )
        assert False, "expected BrokerAuthzError"
    except BrokerAuthzError:
        pass
    assert link.forwarded_calls == []


def test_wrong_admin_key_is_refused():
    priv, pub = crypto.generate_keypair()
    _other_priv, other_pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    authz = GrantGatedBroker(epoptes_link=link, admin_pubkey=other_pub)

    g = _issue(priv, pub, target_hostname="itlab-03")

    try:
        authz.forward_command(
            g, handle="10.0.1.5:1234", command="ping", expected_hostname="itlab-03"
        )
        assert False, "expected BrokerAuthzError"
    except BrokerAuthzError:
        pass
    assert link.forwarded_calls == []


def test_revoke_grant_cannot_forward_control_command():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    authz = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)

    g = _issue(priv, pub, grant_kind="revoke", target_hostname="itlab-03")

    try:
        authz.forward_command(
            g, handle="10.0.1.5:1234", command="ping", expected_hostname="itlab-03"
        )
        assert False, "expected BrokerAuthzError"
    except BrokerAuthzError:
        pass
    assert link.forwarded_calls == []


def test_replayed_grant_id_is_refused_second_time():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    authz = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)

    g = _issue(priv, pub, grant_id="g-replay", target_hostname="itlab-03")
    authz.forward_command(
        g, handle="10.0.1.5:1234", command="ping", expected_hostname="itlab-03"
    )

    try:
        authz.forward_command(
            g, handle="10.0.1.5:1234", command="ping", expected_hostname="itlab-03"
        )
        assert False, "expected BrokerAuthzError"
    except BrokerAuthzError:
        pass
    assert link.forwarded_calls == [("10.0.1.5:1234", "ping")]


def test_grant_for_different_hostname_cannot_target_this_handle():
    priv, pub = crypto.generate_keypair()
    link = _FakeEpoptesLink()
    authz = GrantGatedBroker(epoptes_link=link, admin_pubkey=pub)

    g = _issue(priv, pub, target_hostname="itlab-03")

    try:
        authz.forward_command(
            g, handle="10.0.1.5:1234", command="ping", expected_hostname="itlab-99"
        )
        assert False, "expected BrokerAuthzError"
    except BrokerAuthzError:
        pass
    assert link.forwarded_calls == []
