import base64
import json

_DEFAULT_INBOX_DIR = "/var/lib/pars-agent/inbox"


def build_delivery_command(
    wire_grant: dict, inbox_dir: str = _DEFAULT_INBOX_DIR
) -> str:
    payload = base64.b64encode(json.dumps(wire_grant).encode("utf-8")).decode("ascii")
    filename = f"{wire_grant['grant_id']}.json"
    return f"mkdir -p '{inbox_dir}' && echo '{payload}' | base64 -d > '{inbox_dir}/{filename}'"
