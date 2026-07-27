import base64
import json

from pars_admin.broker.grant_delivery import build_delivery_command


def test_command_writes_decoded_grant_json_to_inbox_dir():
    wire_grant = {"grant_id": "g-1", "target_hostname": "itlab-04"}

    command = build_delivery_command(wire_grant, inbox_dir="/var/lib/pars-agent/inbox")

    assert "/var/lib/pars-agent/inbox" in command
    assert "g-1.json" in command
    payload = base64.b64encode(json.dumps(wire_grant).encode()).decode()
    assert payload in command


def test_command_uses_default_inbox_dir_when_not_given():
    wire_grant = {"grant_id": "g-2", "target_hostname": "itlab-05"}

    command = build_delivery_command(wire_grant)

    assert "/var/lib/pars-agent/inbox" in command
