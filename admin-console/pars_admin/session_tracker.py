from dataclasses import dataclass

from pars_admin.grant_issue import (
    issue_open_grant,
    issue_preempt_grant,
    issue_revoke_grant,
)
from pars_admin.registry import Registry
from pars_admin.trust_root import AdminTrustRoot
from pars_shared.constants import SUBJECT_KIND_ADMIN, SUBJECT_KIND_TEACHER
from pars_shared.grant import Grant


class SessionConflictError(Exception):
    pass


@dataclass
class _ActiveSession:
    subject: str
    subject_kind: str


class SessionTracker:
    def __init__(self, trust_root: AdminTrustRoot, registry: Registry):
        self._trust_root = trust_root
        self._registry = registry
        self._active: dict = {}
        self._teacher_hostname: dict = {}

    def active_subject(self, hostname: str):
        session = self._active.get(hostname)
        return session.subject if session else None

    def request_open(
        self, subject: str, subject_kind: str, target_hostname: str, session_mode: str
    ) -> list:
        grants = []

        occupant = self._active.get(target_hostname)
        if occupant is not None and occupant.subject != subject:
            if subject_kind != SUBJECT_KIND_ADMIN:
                raise SessionConflictError(
                    f"{target_hostname} is in use by {occupant.subject}"
                )
            grants.append(
                issue_preempt_grant(self._trust_root, self._registry, target_hostname)
            )
            self._clear(target_hostname)

        if subject_kind == SUBJECT_KIND_TEACHER:
            prior_hostname = self._teacher_hostname.get(subject)
            if prior_hostname and prior_hostname != target_hostname:
                grants.append(
                    issue_revoke_grant(self._trust_root, self._registry, prior_hostname)
                )
                self._clear(prior_hostname)

        grant = issue_open_grant(
            self._trust_root,
            self._registry,
            subject,
            subject_kind,
            target_hostname,
            session_mode,
        )
        grants.append(grant)

        self._active[target_hostname] = _ActiveSession(subject, subject_kind)
        if subject_kind == SUBJECT_KIND_TEACHER:
            self._teacher_hostname[subject] = target_hostname

        return grants

    def revoke(self, target_hostname: str) -> Grant:
        grant = issue_revoke_grant(self._trust_root, self._registry, target_hostname)
        self._clear(target_hostname)
        return grant

    def _clear(self, hostname: str) -> None:
        occupant = self._active.pop(hostname, None)
        if occupant and occupant.subject_kind == SUBJECT_KIND_TEACHER:
            self._teacher_hostname.pop(occupant.subject, None)
