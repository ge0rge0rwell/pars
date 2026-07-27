import socket
import threading

from pars_agent.config import AgentConfig
from pars_agent.enrollment import AgentIdentity
from pars_agent.register import send_register_message
from pars_shared import protocol


def _stub_listener(received: list, response: bytes = b""):
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
        if response:
            conn.sendall(response)
        conn.close()
        server.close()

    thread = threading.Thread(target=accept_one, daemon=True)
    thread.start()
    return port, thread


def test_sends_well_formed_register_message():
    received = []
    port, thread = _stub_listener(received)

    config = AgentConfig(
        admin_console_host="127.0.0.1", admin_console_port=port, hostname_override=None
    )
    identity = AgentIdentity(
        private_key=b"\x00" * 32, public_key=b"\x01" * 32, fingerprint="01:01:01"
    )

    response = send_register_message(
        config, identity, hostname="itlab-03", current_ip="10.0.1.5"
    )
    thread.join(timeout=2)

    assert response is None
    assert len(received) == 1
    parsed = protocol.from_json(received[0])
    assert isinstance(parsed, protocol.RegisterMessage)
    assert parsed.hostname == "itlab-03"
    assert parsed.cert_fingerprint == "01:01:01"
    assert parsed.cert_pubkey == identity.public_key.hex()
    assert parsed.current_ip == "10.0.1.5"


def test_returns_parsed_enrollment_result_response():
    received = []
    reply = protocol.to_json(
        protocol.EnrollmentResultMessage(
            approved=True, admin_instance_id="school-42", admin_pubkey="ab" * 32
        )
    ).encode("utf-8")
    port, thread = _stub_listener(received, response=reply)

    config = AgentConfig(
        admin_console_host="127.0.0.1", admin_console_port=port, hostname_override=None
    )
    identity = AgentIdentity(
        private_key=b"\x00" * 32, public_key=b"\x01" * 32, fingerprint="01:01:01"
    )

    response = send_register_message(
        config, identity, hostname="itlab-03", current_ip="10.0.1.5"
    )
    thread.join(timeout=2)

    assert isinstance(response, protocol.EnrollmentResultMessage)
    assert response.approved is True
    assert response.admin_instance_id == "school-42"
