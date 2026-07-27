import pytest

from pars_admin.grant_issue import (
    GrantIssueError,
    issue_open_grant,
    issue_preempt_grant,
    issue_revoke_grant,
)
from pars_admin.registry import Registry
from pars_admin.trust_root import ensure_admin_trust_root
from pars_shared.grant import verify_grant


def _approved_registry(
    tmp_path, hostname="itlab-03", room_type="it_lab", fingerprint="ab:cd"
):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    registry.upsert(hostname, room_type, fingerprint, "approved")
    return registry


def test_teacher_request_for_it_lab_machine_produces_valid_grant(tmp_path):
    registry = _approved_registry(tmp_path)
    trust_root = ensure_admin_trust_root(str(tmp_path))

    grant = issue_open_grant(
        trust_root,
        registry,
        subject="teacher.ayse",
        subject_kind="teacher",
        target_hostname="itlab-03",
        session_mode="control",
    )

    assert verify_grant(grant, trust_root.public_key) is True
    assert grant.target_cert_fingerprint == "ab:cd"


def test_teacher_request_for_non_it_lab_machine_refused_before_signing(tmp_path):
    registry = _approved_registry(tmp_path, hostname="office-01", room_type="office")
    trust_root = ensure_admin_trust_root(str(tmp_path))

    with pytest.raises(GrantIssueError):
        issue_open_grant(
            trust_root,
            registry,
            subject="teacher.ayse",
            subject_kind="teacher",
            target_hostname="office-01",
            session_mode="control",
        )


def test_admin_request_for_non_it_lab_machine_is_allowed(tmp_path):
    registry = _approved_registry(tmp_path, hostname="office-01", room_type="office")
    trust_root = ensure_admin_trust_root(str(tmp_path))

    grant = issue_open_grant(
        trust_root,
        registry,
        subject="admin.root",
        subject_kind="admin",
        target_hostname="office-01",
        session_mode="view",
    )

    assert verify_grant(grant, trust_root.public_key) is True


def test_request_for_unknown_hostname_refused(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    trust_root = ensure_admin_trust_root(str(tmp_path))

    with pytest.raises(GrantIssueError):
        issue_open_grant(
            trust_root,
            registry,
            subject="teacher.ayse",
            subject_kind="teacher",
            target_hostname="ghost-01",
            session_mode="control",
        )


def test_issue_preempt_and_revoke_produce_valid_grants(tmp_path):
    registry = _approved_registry(tmp_path)
    trust_root = ensure_admin_trust_root(str(tmp_path))

    preempt = issue_preempt_grant(trust_root, registry, target_hostname="itlab-03")
    revoke = issue_revoke_grant(trust_root, registry, target_hostname="itlab-03")

    assert verify_grant(preempt, trust_root.public_key) is True
    assert preempt.grant_kind == "preempt"
    assert verify_grant(revoke, trust_root.public_key) is True
    assert revoke.grant_kind == "revoke"
