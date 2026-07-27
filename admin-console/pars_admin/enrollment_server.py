import socket

from pars_admin.registry import Registry
from pars_admin.trust_root import AdminTrustRoot
from pars_shared import protocol
from pars_shared.constants import ROOM_TYPE_IT_LAB


def handle_registration(
    registry: Registry, trust_root: AdminTrustRoot, message, staging=None
):
    existing = registry.get(message.hostname)
    if existing:
        room_type = existing.room_type
    elif staging is not None and staging.get_room_type(message.hostname):
        room_type = staging.get_room_type(message.hostname)
    else:
        room_type = "unassigned"
    status = existing.enrollment_status if existing else "pending"

    result = registry.upsert(
        hostname=message.hostname,
        room_type=room_type,
        cert_fingerprint=message.cert_fingerprint,
        enrollment_status=status,
    )
    if result.conflict:
        return protocol.ConflictRejectionMessage(
            reason=f"{message.hostname} already bound to a different certificate fingerprint"
        )

    record = registry.get(message.hostname)
    if record.enrollment_status == "approved":
        return protocol.EnrollmentResultMessage(
            approved=True,
            admin_instance_id=trust_root.admin_instance_id,
            admin_pubkey=trust_root.public_key.hex(),
        )
    return None


def approve(registry: Registry, hostname: str) -> None:
    record = registry.get(hostname)
    registry.upsert(hostname, record.room_type, record.cert_fingerprint, "approved")


def reject(registry: Registry, hostname: str) -> None:
    registry.delete(hostname)


def handle_connection(
    conn: socket.socket,
    registry: Registry,
    trust_root: AdminTrustRoot,
    staging=None,
    health_store=None,
    accounts=None,
) -> None:
    data = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk

    try:
        message = protocol.from_json(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return

    if isinstance(message, protocol.HealthReportMessage):
        if health_store is not None:
            health_store.apply_report(message)
        return

    if isinstance(message, protocol.MachineListRequestMessage):
        hostnames = [
            record.hostname
            for record in registry.list_all()
            if record.room_type == ROOM_TYPE_IT_LAB
            and record.enrollment_status == "approved"
        ]
        response = protocol.MachineListResultMessage(hostnames=hostnames)
        conn.sendall(protocol.to_json(response).encode("utf-8"))
        return

    if isinstance(message, protocol.LoginRequestMessage):
        success = accounts is not None and accounts.verify_login(
            message.username, message.password
        )
        reason = "" if success else "invalid credentials"
        response = protocol.LoginResultMessage(success=success, reason=reason)
        conn.sendall(protocol.to_json(response).encode("utf-8"))
        return

    response = handle_registration(registry, trust_root, message, staging=staging)
    if response is not None:
        conn.sendall(protocol.to_json(response).encode("utf-8"))
