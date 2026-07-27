from __future__ import annotations

import socket

from pars_agent.config import AgentConfig
from pars_agent.enrollment import AgentIdentity
from pars_shared import protocol
from pars_shared.constants import ENROLLMENT_TIMEOUT_SECONDS


def send_register_message(
    config: AgentConfig, identity: AgentIdentity, hostname: str, current_ip: str
):
    message = protocol.RegisterMessage(
        hostname=hostname,
        cert_fingerprint=identity.fingerprint,
        cert_pubkey=identity.public_key.hex(),
        current_ip=current_ip,
        agent_version="0.1.0",
    )
    payload = protocol.to_json(message).encode("utf-8")

    with socket.create_connection(
        (config.admin_console_host, config.admin_console_port),
        timeout=ENROLLMENT_TIMEOUT_SECONDS,
    ) as sock:
        sock.sendall(payload)
        sock.shutdown(socket.SHUT_WR)
        response_bytes = sock.recv(65536)

    if not response_bytes:
        return None
    return protocol.from_json(response_bytes.decode("utf-8"))
