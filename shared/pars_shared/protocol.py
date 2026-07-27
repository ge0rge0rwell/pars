import json
from dataclasses import asdict, dataclass

from pars_shared.constants import (
    MSG_TYPE_BROKER_SESSION_REQUEST,
    MSG_TYPE_BROKER_SESSION_RESULT,
    MSG_TYPE_CONFLICT_REJECTION,
    MSG_TYPE_ENROLLMENT_RESULT,
    MSG_TYPE_HEALTH_REPORT,
    MSG_TYPE_HEARTBEAT,
    MSG_TYPE_LOGIN_REQUEST,
    MSG_TYPE_LOGIN_RESULT,
    MSG_TYPE_MACHINE_LIST_REQUEST,
    MSG_TYPE_MACHINE_LIST_RESULT,
    MSG_TYPE_REGISTER,
    MSG_TYPE_SESSION_REQUEST,
    MSG_TYPE_SESSION_REQUEST_RESULT,
)


@dataclass(frozen=True)
class RegisterMessage:

    hostname: str
    cert_fingerprint: str
    cert_pubkey: str
    current_ip: str
    agent_version: str
    msg_type: str = MSG_TYPE_REGISTER


@dataclass(frozen=True)
class HeartbeatMessage:

    hostname: str
    cert_fingerprint: str
    current_ip: str
    msg_type: str = MSG_TYPE_HEARTBEAT


@dataclass(frozen=True)
class EnrollmentResultMessage:

    approved: bool
    admin_instance_id: str
    admin_pubkey: str
    msg_type: str = MSG_TYPE_ENROLLMENT_RESULT


@dataclass(frozen=True)
class ConflictRejectionMessage:

    reason: str
    msg_type: str = MSG_TYPE_CONFLICT_REJECTION


@dataclass(frozen=True)
class HealthReportMessage:
    hostname: str
    disk_free_percent: float
    pending_apt_updates: int
    failed_systemd_units: int
    msg_type: str = MSG_TYPE_HEALTH_REPORT


@dataclass(frozen=True)
class BrokerSessionRequestMessage:

    action: str
    grant: dict
    msg_type: str = MSG_TYPE_BROKER_SESSION_REQUEST


@dataclass(frozen=True)
class BrokerSessionResultMessage:
    success: bool
    error: str = ""
    msg_type: str = MSG_TYPE_BROKER_SESSION_RESULT


@dataclass(frozen=True)
class LoginRequestMessage:

    username: str
    password: str
    msg_type: str = MSG_TYPE_LOGIN_REQUEST


@dataclass(frozen=True)
class LoginResultMessage:
    success: bool
    reason: str = ""
    msg_type: str = MSG_TYPE_LOGIN_RESULT


@dataclass(frozen=True)
class MachineListRequestMessage:
    username: str
    msg_type: str = MSG_TYPE_MACHINE_LIST_REQUEST


@dataclass(frozen=True)
class MachineListResultMessage:
    hostnames: list
    msg_type: str = MSG_TYPE_MACHINE_LIST_RESULT


@dataclass(frozen=True)
class SessionRequestMessage:
    username: str
    hostname: str
    action: str
    session_mode: str
    msg_type: str = MSG_TYPE_SESSION_REQUEST


@dataclass(frozen=True)
class SessionRequestResultMessage:
    grant: dict
    error: str = ""
    msg_type: str = MSG_TYPE_SESSION_REQUEST_RESULT


def to_json(message) -> str:
    return json.dumps(asdict(message))


_MESSAGE_TYPES_BY_TAG = {
    MSG_TYPE_REGISTER: RegisterMessage,
    MSG_TYPE_HEARTBEAT: HeartbeatMessage,
    MSG_TYPE_ENROLLMENT_RESULT: EnrollmentResultMessage,
    MSG_TYPE_CONFLICT_REJECTION: ConflictRejectionMessage,
    MSG_TYPE_HEALTH_REPORT: HealthReportMessage,
    MSG_TYPE_BROKER_SESSION_REQUEST: BrokerSessionRequestMessage,
    MSG_TYPE_BROKER_SESSION_RESULT: BrokerSessionResultMessage,
    MSG_TYPE_LOGIN_REQUEST: LoginRequestMessage,
    MSG_TYPE_LOGIN_RESULT: LoginResultMessage,
    MSG_TYPE_MACHINE_LIST_REQUEST: MachineListRequestMessage,
    MSG_TYPE_MACHINE_LIST_RESULT: MachineListResultMessage,
    MSG_TYPE_SESSION_REQUEST: SessionRequestMessage,
    MSG_TYPE_SESSION_REQUEST_RESULT: SessionRequestResultMessage,
}


def from_json(raw: str):
    data = json.loads(raw)
    tag = data.get("msg_type")
    message_cls = _MESSAGE_TYPES_BY_TAG.get(tag)
    if message_cls is None:
        raise ValueError(f"unknown msg_type: {tag!r}")
    try:
        return message_cls(**data)
    except TypeError as exc:
        raise ValueError(f"malformed {tag} message: {exc}") from exc
