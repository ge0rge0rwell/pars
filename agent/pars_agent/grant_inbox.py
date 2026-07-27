import json
from pathlib import Path

from pars_agent.grant_relay import apply_relayed_grant
from pars_agent.grant_verify import GrantVerifier


def check_inbox(verifier: GrantVerifier, inbox_dir: Path) -> list:
    results = []
    for path in sorted(Path(inbox_dir).glob("*.json")):
        try:
            wire_grant = json.loads(path.read_text())
            accepted = apply_relayed_grant(verifier, wire_grant)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            accepted = False
        results.append(accepted)
        path.unlink()
    return results
