import socket

from pars_shared import protocol
from pars_shared.constants import ENROLLMENT_TIMEOUT_SECONDS


def send_grant_delivery(host: str, port: int, wire_grant: dict):
    message = protocol.BrokerGrantDeliveryMessage(grant=wire_grant)
    payload = protocol.to_json(message).encode("utf-8") + b"\r\n"

    with socket.create_connection(
        (host, port), timeout=ENROLLMENT_TIMEOUT_SECONDS
    ) as sock:
        sock.sendall(payload)
        data = b""
        while not data.endswith(b"\r\n"):
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk

    if not data:
        return None
    return protocol.from_json(data.rstrip(b"\r\n").decode("utf-8"))
