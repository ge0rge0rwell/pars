from __future__ import annotations

import configparser
from dataclasses import dataclass

from pars_shared.constants import ENROLLMENT_PORT

_SECTION = "agent"
_REQUIRED_KEYS = ("admin_console_host",)


@dataclass(frozen=True)
class AgentConfig:
    admin_console_host: str
    admin_console_port: int
    hostname_override: str | None


def load_config(path: str) -> AgentConfig:
    parser = configparser.ConfigParser()
    read_files = parser.read(path)
    if not read_files:
        raise ValueError(f"answer file not found or unreadable: {path}")

    if not parser.has_section(_SECTION):
        raise ValueError(f"answer file missing [{_SECTION}] section: {path}")

    section = parser[_SECTION]
    for key in _REQUIRED_KEYS:
        if key not in section or not section[key].strip():
            raise ValueError(f"answer file missing required key: {key}")

    return AgentConfig(
        admin_console_host=section["admin_console_host"].strip(),
        admin_console_port=section.getint("admin_console_port", ENROLLMENT_PORT),
        hostname_override=section.get("hostname_override", fallback=None),
    )
