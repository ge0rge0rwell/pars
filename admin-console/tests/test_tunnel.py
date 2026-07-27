from pars_admin.broker.tunnel import (
    SessionTunnelManager,
    TunnelEndpoint,
    render_stunnel_config,
)


def _client_endpoint():
    return TunnelEndpoint(
        listen_host="127.0.0.1",
        listen_port=5910,
        connect_host="broker.school.lan",
        connect_port=9001,
        cert_path="/etc/epoptes/server.crt",
        key_path="/etc/epoptes/server.key",
        role="client",
    )


def _server_endpoint():
    return TunnelEndpoint(
        listen_host="0.0.0.0",
        listen_port=9001,
        connect_host="127.0.0.1",
        connect_port=5500,
        cert_path="/etc/epoptes/server.crt",
        key_path="/etc/epoptes/server.key",
        role="server",
    )


def test_render_client_config_has_tls_initiator_directives():
    text = render_stunnel_config(_client_endpoint())
    assert "client = yes" in text
    assert "accept = 127.0.0.1:5910" in text
    assert "connect = broker.school.lan:9001" in text
    assert "CAfile = /etc/epoptes/server.crt" in text


def test_render_server_config_has_tls_terminator_directives():
    text = render_stunnel_config(_server_endpoint())
    assert "client = yes" not in text
    assert "accept = 0.0.0.0:9001" in text
    assert "connect = 127.0.0.1:5500" in text
    assert "key = /etc/epoptes/server.key" in text


class _FakeProcess:
    def __init__(self):
        self.terminated = False

    def terminate(self):
        self.terminated = True


class _FakePopen:
    def __init__(self):
        self.calls = []

    def __call__(self, args):
        self.calls.append(args)
        return _FakeProcess()


def test_start_session_launches_one_process_per_endpoint():
    fake_popen = _FakePopen()
    manager = SessionTunnelManager(stunnel_binary="stunnel", popen=fake_popen)

    manager.start_session("g-1", [_client_endpoint(), _server_endpoint()])

    assert len(fake_popen.calls) == 2
    assert all(call[0] == "stunnel" for call in fake_popen.calls)


def test_starting_same_session_twice_raises():
    fake_popen = _FakePopen()
    manager = SessionTunnelManager(stunnel_binary="stunnel", popen=fake_popen)
    manager.start_session("g-1", [_client_endpoint()])

    try:
        manager.start_session("g-1", [_client_endpoint()])
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_stop_session_terminates_its_processes():
    fake_popen = _FakePopen()
    manager = SessionTunnelManager(stunnel_binary="stunnel", popen=fake_popen)
    manager.start_session("g-1", [_client_endpoint(), _server_endpoint()])

    manager.stop_session("g-1")

    manager.start_session("g-1", [_client_endpoint()])


def test_stop_unknown_session_is_a_safe_noop():
    fake_popen = _FakePopen()
    manager = SessionTunnelManager(stunnel_binary="stunnel", popen=fake_popen)
    manager.stop_session("never-started")
