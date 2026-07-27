import uuid
from datetime import datetime, timezone

from pars_admin.registry import Registry
from pars_admin.trust_root import AdminTrustRoot
from pars_shared.constants import (
    GRANT_KIND_OPEN,
    GRANT_KIND_PREEMPT,
    GRANT_KIND_REVOKE,
    ROOM_TYPE_IT_LAB,
    SESSION_MODE_CONTROL,
    SUBJECT_KIND_ADMIN,
    SUBJECT_KIND_TEACHER,
)
from pars_shared.grant import Grant, build_and_sign


class GrantIssueError(Exception):
    pass


def _issued_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_target(registry: Registry, target_hostname: str, subject_kind: str):
    record = registry.get(target_hostname)
    if record is None or record.enrollment_status != "approved":
        raise GrantIssueError(f"{target_hostname} is not an approved, enrolled machine")
    if subject_kind == SUBJECT_KIND_TEACHER and record.room_type != ROOM_TYPE_IT_LAB:
        raise GrantIssueError(f"{target_hostname} is not an it_lab machine")
    return record


def issue_open_grant(
    trust_root: AdminTrustRoot,
    registry: Registry,
    subject: str,
    subject_kind: str,
    target_hostname: str,
    session_mode: str,
) -> Grant:
    record = _require_target(registry, target_hostname, subject_kind)
    return build_and_sign(
        grant_id=uuid.uuid4().hex,
        issued_at=_issued_at(),
        admin_instance_id=trust_root.admin_instance_id,
        admin_private_key=trust_root.private_key,
        admin_public_key=trust_root.public_key,
        subject=subject,
        subject_kind=subject_kind,
        target_hostname=target_hostname,
        target_cert_fingerprint=record.cert_fingerprint,
        session_mode=session_mode,
        grant_kind=GRANT_KIND_OPEN,
    )


def _issue_admin_override(
    trust_root: AdminTrustRoot,
    registry: Registry,
    target_hostname: str,
    grant_kind: str,
) -> Grant:
    record = _require_target(registry, target_hostname, SUBJECT_KIND_ADMIN)
    return build_and_sign(
        grant_id=uuid.uuid4().hex,
        issued_at=_issued_at(),
        admin_instance_id=trust_root.admin_instance_id,
        admin_private_key=trust_root.private_key,
        admin_public_key=trust_root.public_key,
        subject="admin",
        subject_kind=SUBJECT_KIND_ADMIN,
        target_hostname=target_hostname,
        target_cert_fingerprint=record.cert_fingerprint,
        session_mode=SESSION_MODE_CONTROL,
        grant_kind=grant_kind,
    )


def issue_preempt_grant(
    trust_root: AdminTrustRoot, registry: Registry, target_hostname: str
) -> Grant:
    return _issue_admin_override(
        trust_root, registry, target_hostname, GRANT_KIND_PREEMPT
    )


def issue_revoke_grant(
    trust_root: AdminTrustRoot, registry: Registry, target_hostname: str
) -> Grant:
    return _issue_admin_override(
        trust_root, registry, target_hostname, GRANT_KIND_REVOKE
    )
