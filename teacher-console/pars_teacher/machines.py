import socket

from pars_shared import protocol
from pars_shared.constants import ENROLLMENT_TIMEOUT_SECONDS


def request_machine_list(host: str, port: int, username: str):
    message = protocol.MachineListRequestMessage(username=username)
    payload = protocol.to_json(message).encode("utf-8")

    with socket.create_connection(
        (host, port), timeout=ENROLLMENT_TIMEOUT_SECONDS
    ) as sock:
        sock.sendall(payload)
        sock.shutdown(socket.SHUT_WR)
        response_bytes = sock.recv(65536)

    if not response_bytes:
        return []
    response = protocol.from_json(response_bytes.decode("utf-8"))
    return response.hostnames
