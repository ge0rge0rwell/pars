import socket
import threading

from pars_teacher.login import send_login
from pars_shared import protocol


def _stub_listener(received, response_message=None):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_one():
        conn, _addr = server.accept()
        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        received.append(data.decode("utf-8"))
        if response_message is not None:
            conn.sendall(protocol.to_json(response_message).encode("utf-8"))
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()
    return port, thread


def test_sends_well_formed_login_request_and_returns_result():
    received = []
    reply = protocol.LoginResultMessage(success=True, reason="")
    port, thread = _stub_listener(received, response_message=reply)

    result = send_login("127.0.0.1", port, username="teacher.ayse", password="secret")
    thread.join(timeout=2)

    assert len(received) == 1
    parsed = protocol.from_json(received[0])
    assert isinstance(parsed, protocol.LoginRequestMessage)
    assert parsed.username == "teacher.ayse"
    assert parsed.password == "secret"
    assert result.success is True


def test_no_response_returns_none():
    received = []
    port, thread = _stub_listener(received, response_message=None)

    result = send_login("127.0.0.1", port, username="teacher.ayse", password="secret")
    thread.join(timeout=2)

    assert result is None
