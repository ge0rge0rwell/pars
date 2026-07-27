import socket
import threading

from pars_admin.broker.broker_client import send_grant_delivery
from pars_shared import protocol


def _stub_broker(received, response_message):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        data = b""
        while not data.endswith(b"\r\n"):
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        received.append(data.rstrip(b"\r\n").decode("utf-8"))
        conn.sendall(protocol.to_json(response_message).encode("utf-8") + b"\r\n")
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()
    return port, thread


def test_sends_grant_delivery_message_and_returns_result():
    received = []
    reply = protocol.BrokerSessionResultMessage(success=True, error="")
    port, thread = _stub_broker(received, reply)

    result = send_grant_delivery("127.0.0.1", port, {"grant_id": "g-1"})
    thread.join(timeout=2)

    assert len(received) == 1
    parsed = protocol.from_json(received[0])
    assert isinstance(parsed, protocol.BrokerGrantDeliveryMessage)
    assert parsed.grant == {"grant_id": "g-1"}
    assert result.success is True
