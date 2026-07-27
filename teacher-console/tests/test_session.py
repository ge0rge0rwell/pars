import socket
import threading

from pars_teacher.session import request_session
from pars_shared import protocol


def _stub_listener(received, response_message):
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
        conn.sendall(protocol.to_json(response_message).encode("utf-8"))
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()
    return port, thread


def test_sends_well_formed_session_request_and_returns_result():
    received = []
    reply = protocol.SessionRequestResultMessage(
        grant={"target_hostname": "itlab-03"}, error=""
    )
    port, thread = _stub_listener(received, reply)

    result = request_session(
        "127.0.0.1",
        port,
        username="teacher.ayse",
        hostname="itlab-03",
        action="control",
        session_mode="control",
    )
    thread.join(timeout=2)

    assert len(received) == 1
    parsed = protocol.from_json(received[0])
    assert isinstance(parsed, protocol.SessionRequestMessage)
    assert parsed.hostname == "itlab-03"
    assert result.error == ""
    assert result.grant["target_hostname"] == "itlab-03"
