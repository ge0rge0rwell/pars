from __future__ import annotations

from pars_shared.constants import GRANT_KIND_OPEN, GRANT_KIND_PREEMPT, GRANT_KIND_REVOKE
from pars_shared.grant import Grant, verify_grant


class GrantVerifier:

    def __init__(self, pinned_admin_pubkey: bytes, own_hostname: str):
        self._pinned_admin_pubkey = pinned_admin_pubkey
        self._own_hostname = own_hostname
        self._consumed_grant_ids: set[str] = set()
        self._active_subject: str | None = None

    def accept(self, grant: Grant) -> bool:
        if grant.grant_id in self._consumed_grant_ids:
            return False
        if grant.target_hostname != self._own_hostname:
            return False
        if not verify_grant(grant, self._pinned_admin_pubkey):
            return False

        self._consumed_grant_ids.add(grant.grant_id)

        if grant.grant_kind == GRANT_KIND_OPEN:
            self._active_subject = grant.subject
        elif grant.grant_kind in (GRANT_KIND_PREEMPT, GRANT_KIND_REVOKE):
            self._active_subject = None

        return True

    def active_session_subject(self) -> str | None:
        return self._active_subject
