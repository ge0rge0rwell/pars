from twisted.protocols import amp
from twisted.test import iosim

from pars_admin.broker.epoptes_link import ClientCommand, EnumerateClients, EpoptesLink


class _StubGuiplex(amp.AMP):

    known_clients = ("10.0.1.5:44821", "10.0.1.6:51002")

    @EnumerateClients.responder
    def enumerate_clients(self):
        return {"handles": list(self.known_clients)}

    @ClientCommand.responder
    def client_command(self, handle, command):
        if handle not in self.known_clients:
            return {"result": b"", "filename": ""}
        return {"result": f"ran:{command}".encode(), "filename": ""}


def _connected_pair():
    client, _server, pump = iosim.connectedServerAndClient(_StubGuiplex, EpoptesLink)
    return client, pump


def test_enumerate_clients_returns_handles():
    client, pump = _connected_pair()
    dfr = client.enumerate_clients()
    pump.flush()
    assert dfr.result == ["10.0.1.5:44821", "10.0.1.6:51002"]


def test_send_command_to_known_handle():
    client, pump = _connected_pair()
    dfr = client.send_command("10.0.1.5:44821", "ping")
    pump.flush()
    assert dfr.result == b"ran:ping"


def test_send_command_to_unknown_handle_returns_empty():
    client, pump = _connected_pair()
    dfr = client.send_command("10.0.9.9:1", "ping")
    pump.flush()
    assert dfr.result == b""
