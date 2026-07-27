from __future__ import annotations

from pars_admin.broker.grant_delivery import build_delivery_command
from pars_shared.constants import GRANT_KIND_OPEN, GRANT_KIND_PREEMPT, GRANT_KIND_REVOKE
from pars_shared.grant import Grant, to_wire_dict, verify_grant


class BrokerAuthzError(Exception):
    pass


class GrantGatedBroker:
    def __init__(self, epoptes_link, admin_pubkey: bytes):
        self._epoptes_link = epoptes_link
        self._admin_pubkey = admin_pubkey
        self._consumed_grant_ids: set[str] = set()

    def forward_command(
        self, grant: Grant, handle: str, command: str, expected_hostname: str
    ):
        if grant.grant_kind != GRANT_KIND_OPEN:
            raise BrokerAuthzError(
                f"grant_kind {grant.grant_kind!r} cannot authorize a command"
            )
        if grant.target_hostname != expected_hostname:
            raise BrokerAuthzError(
                f"grant targets {grant.target_hostname!r}, not {expected_hostname!r}"
            )

        if not verify_grant(grant, self._admin_pubkey):
            raise BrokerAuthzError("grant signature does not verify")
        if grant.grant_id in self._consumed_grant_ids:
            raise BrokerAuthzError(f"grant already consumed: {grant.grant_id}")

        self._consumed_grant_ids.add(grant.grant_id)
        return self._epoptes_link.send_command(handle, command)

    def deliver_grant(self, grant: Grant, handle: str, expected_hostname: str):
        if grant.grant_kind not in (GRANT_KIND_PREEMPT, GRANT_KIND_REVOKE):
            raise BrokerAuthzError(
                f"grant_kind {grant.grant_kind!r} cannot be delivered as a preempt/revoke"
            )
        if grant.target_hostname != expected_hostname:
            raise BrokerAuthzError(
                f"grant targets {grant.target_hostname!r}, not {expected_hostname!r}"
            )

        if not verify_grant(grant, self._admin_pubkey):
            raise BrokerAuthzError("grant signature does not verify")
        if grant.grant_id in self._consumed_grant_ids:
            raise BrokerAuthzError(f"grant already consumed: {grant.grant_id}")

        self._consumed_grant_ids.add(grant.grant_id)
        command = build_delivery_command(to_wire_dict(grant))
        return self._epoptes_link.send_command(handle, command)
