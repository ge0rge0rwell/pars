from pars_admin.broker.authz import GrantGatedBroker
from pars_shared.grant import from_wire_dict
from pars_shared.protocol import BrokerGrantDeliveryMessage, BrokerSessionRequestMessage

_VALID_ACTIONS = ("view", "control", "broadcast", "lock")


def process_broker_session_request(
    gated_broker: GrantGatedBroker, message: BrokerSessionRequestMessage
):
    if message.action not in _VALID_ACTIONS:
        raise ValueError(f"unknown action: {message.action!r}")

    grant = from_wire_dict(message.grant)
    handle = grant.target_hostname
    return gated_broker.forward_command(
        grant,
        handle=handle,
        command=message.action,
        expected_hostname=grant.target_hostname,
    )


def process_broker_grant_delivery(
    gated_broker: GrantGatedBroker, message: BrokerGrantDeliveryMessage
):
    grant = from_wire_dict(message.grant)
    handle = grant.target_hostname
    return gated_broker.deliver_grant(
        grant, handle=handle, expected_hostname=grant.target_hostname
    )
