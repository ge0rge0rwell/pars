import socket
import threading

from pars_teacher.machines import request_machine_list
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


def test_returns_it_lab_only_hostnames_from_server():
    received = []
    reply = protocol.MachineListResultMessage(hostnames=["itlab-03", "itlab-04"])
    port, thread = _stub_listener(received, reply)

    hostnames = request_machine_list("127.0.0.1", port, username="teacher.ayse")
    thread.join(timeout=2)

    assert len(received) == 1
    parsed = protocol.from_json(received[0])
    assert isinstance(parsed, protocol.MachineListRequestMessage)
    assert parsed.username == "teacher.ayse"
    assert hostnames == ["itlab-03", "itlab-04"]
