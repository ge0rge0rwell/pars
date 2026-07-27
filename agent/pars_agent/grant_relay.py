from pars_agent.grant_verify import GrantVerifier
from pars_shared.grant import from_wire_dict


def apply_relayed_grant(verifier: GrantVerifier, wire_grant: dict) -> bool:
    grant = from_wire_dict(wire_grant)
    return verifier.accept(grant)
