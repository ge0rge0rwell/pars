from dataclasses import dataclass

from pars_shared import crypto
from pars_shared.constants import GRANT_KINDS, SESSION_MODES, SUBJECT_KINDS

_CANONICAL_FIELDS = (
    "grant_id",
    "issued_at",
    "admin_instance_id",
    "issuer_pubkey_hex",
    "subject",
    "subject_kind",
    "target_hostname",
    "target_cert_fingerprint",
    "session_mode",
    "grant_kind",
)


@dataclass(frozen=True)
class Grant:
    grant_id: str
    issued_at: str
    admin_instance_id: str
    issuer_pubkey: bytes
    subject: str
    subject_kind: str
    target_hostname: str
    target_cert_fingerprint: str
    session_mode: str
    grant_kind: str
    signature: bytes

    def __post_init__(self):
        if self.subject_kind not in SUBJECT_KINDS:
            raise ValueError(f"invalid subject_kind: {self.subject_kind!r}")
        if self.session_mode not in SESSION_MODES:
            raise ValueError(f"invalid session_mode: {self.session_mode!r}")
        if self.grant_kind not in GRANT_KINDS:
            raise ValueError(f"invalid grant_kind: {self.grant_kind!r}")


def _canonical_bytes(fields: dict) -> bytes:
    parts = []
    for name in _CANONICAL_FIELDS:
        value = fields[name].encode("utf-8")
        parts.append(f"{len(value)}:".encode("ascii"))
        parts.append(value)
    return b"".join(parts)


def build_and_sign(
    *,
    grant_id: str,
    issued_at: str,
    admin_instance_id: str,
    admin_private_key: bytes,
    admin_public_key: bytes,
    subject: str,
    subject_kind: str,
    target_hostname: str,
    target_cert_fingerprint: str,
    session_mode: str,
    grant_kind: str,
) -> Grant:
    fields = {
        "grant_id": grant_id,
        "issued_at": issued_at,
        "admin_instance_id": admin_instance_id,
        "issuer_pubkey_hex": admin_public_key.hex(),
        "subject": subject,
        "subject_kind": subject_kind,
        "target_hostname": target_hostname,
        "target_cert_fingerprint": target_cert_fingerprint,
        "session_mode": session_mode,
        "grant_kind": grant_kind,
    }
    signature = crypto.sign(admin_private_key, _canonical_bytes(fields))
    return Grant(
        grant_id=grant_id,
        issued_at=issued_at,
        admin_instance_id=admin_instance_id,
        issuer_pubkey=admin_public_key,
        subject=subject,
        subject_kind=subject_kind,
        target_hostname=target_hostname,
        target_cert_fingerprint=target_cert_fingerprint,
        session_mode=session_mode,
        grant_kind=grant_kind,
        signature=signature,
    )


def to_wire_dict(grant: Grant) -> dict:
    return {
        "grant_id": grant.grant_id,
        "issued_at": grant.issued_at,
        "admin_instance_id": grant.admin_instance_id,
        "issuer_pubkey_hex": grant.issuer_pubkey.hex(),
        "subject": grant.subject,
        "subject_kind": grant.subject_kind,
        "target_hostname": grant.target_hostname,
        "target_cert_fingerprint": grant.target_cert_fingerprint,
        "session_mode": grant.session_mode,
        "grant_kind": grant.grant_kind,
        "signature_hex": grant.signature.hex(),
    }


def from_wire_dict(data: dict) -> Grant:
    return Grant(
        grant_id=data["grant_id"],
        issued_at=data["issued_at"],
        admin_instance_id=data["admin_instance_id"],
        issuer_pubkey=bytes.fromhex(data["issuer_pubkey_hex"]),
        subject=data["subject"],
        subject_kind=data["subject_kind"],
        target_hostname=data["target_hostname"],
        target_cert_fingerprint=data["target_cert_fingerprint"],
        session_mode=data["session_mode"],
        grant_kind=data["grant_kind"],
        signature=bytes.fromhex(data["signature_hex"]),
    )


def verify_grant(grant: Grant, pinned_admin_pubkey: bytes) -> bool:
    fields = {
        "grant_id": grant.grant_id,
        "issued_at": grant.issued_at,
        "admin_instance_id": grant.admin_instance_id,
        "issuer_pubkey_hex": grant.issuer_pubkey.hex(),
        "subject": grant.subject,
        "subject_kind": grant.subject_kind,
        "target_hostname": grant.target_hostname,
        "target_cert_fingerprint": grant.target_cert_fingerprint,
        "session_mode": grant.session_mode,
        "grant_kind": grant.grant_kind,
    }
    return crypto.verify(pinned_admin_pubkey, _canonical_bytes(fields), grant.signature)
