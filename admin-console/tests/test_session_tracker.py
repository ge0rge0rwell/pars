import pytest

from pars_admin.grant_issue import GrantIssueError
from pars_admin.registry import Registry
from pars_admin.session_tracker import SessionConflictError, SessionTracker
from pars_admin.trust_root import ensure_admin_trust_root


def _tracker(tmp_path, hostname="itlab-03"):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    registry.upsert(hostname, "it_lab", "ab:cd", "approved")
    trust_root = ensure_admin_trust_root(str(tmp_path))
    return SessionTracker(trust_root, registry)


def test_teacher_opens_free_machine(tmp_path):
    tracker = _tracker(tmp_path)

    grants = tracker.request_open("teacher.ayse", "teacher", "itlab-03", "control")

    assert len(grants) == 1
    assert grants[0].grant_kind == "open"
    assert tracker.active_subject("itlab-03") == "teacher.ayse"


def test_second_teacher_on_same_machine_is_refused(tmp_path):
    tracker = _tracker(tmp_path)
    tracker.request_open("teacher.ayse", "teacher", "itlab-03", "control")

    with pytest.raises(SessionConflictError):
        tracker.request_open("teacher.mehmet", "teacher", "itlab-03", "control")

    assert tracker.active_subject("itlab-03") == "teacher.ayse"


def test_admin_open_on_in_use_machine_preempts_and_takes_over(tmp_path):
    tracker = _tracker(tmp_path)
    tracker.request_open("teacher.ayse", "teacher", "itlab-03", "control")

    grants = tracker.request_open("admin.root", "admin", "itlab-03", "view")

    kinds = [g.grant_kind for g in grants]
    assert kinds == ["preempt", "open"]
    assert tracker.active_subject("itlab-03") == "admin.root"


def test_admin_revoke_clears_session_no_new_grant(tmp_path):
    tracker = _tracker(tmp_path)
    tracker.request_open("teacher.ayse", "teacher", "itlab-03", "control")

    grant = tracker.revoke("itlab-03")

    assert grant.grant_kind == "revoke"
    assert tracker.active_subject("itlab-03") is None


def test_teacher_moving_to_new_machine_closes_prior_session(tmp_path):
    tmp = tmp_path
    registry = Registry(str(tmp / "registry.sqlite3"))
    registry.upsert("itlab-03", "it_lab", "ab:cd", "approved")
    registry.upsert("itlab-04", "it_lab", "11:22", "approved")
    trust_root = ensure_admin_trust_root(str(tmp))
    tracker = SessionTracker(trust_root, registry)
    tracker.request_open("teacher.ayse", "teacher", "itlab-03", "control")

    grants = tracker.request_open("teacher.ayse", "teacher", "itlab-04", "control")

    kinds = [g.grant_kind for g in grants]
    assert kinds == ["revoke", "open"]
    assert tracker.active_subject("itlab-03") is None
    assert tracker.active_subject("itlab-04") == "teacher.ayse"


def test_teacher_request_for_non_it_lab_machine_still_refused(tmp_path):
    registry = Registry(str(tmp_path / "registry.sqlite3"))
    registry.upsert("office-01", "office", "ab:cd", "approved")
    trust_root = ensure_admin_trust_root(str(tmp_path))
    tracker = SessionTracker(trust_root, registry)

    with pytest.raises(GrantIssueError):
        tracker.request_open("teacher.ayse", "teacher", "office-01", "control")
