from __future__ import annotations

import os
import stat
from dataclasses import dataclass

from pars_shared import crypto
from pars_shared.crypto import fingerprint_of

_PRIVATE_KEY_FILENAME = "identity.key"
_PUBLIC_KEY_FILENAME = "identity.pub"
_PRIVATE_KEY_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR
_DATA_DIR_PERMISSIONS = stat.S_IRWXU


@dataclass(frozen=True)
class AgentIdentity:
    private_key: bytes
    public_key: bytes
    fingerprint: str


def ensure_agent_identity(data_dir: str) -> AgentIdentity:
    os.makedirs(data_dir, mode=_DATA_DIR_PERMISSIONS, exist_ok=True)
    private_key_path = os.path.join(data_dir, _PRIVATE_KEY_FILENAME)
    public_key_path = os.path.join(data_dir, _PUBLIC_KEY_FILENAME)

    if os.path.exists(private_key_path) and os.path.exists(public_key_path):
        with open(private_key_path, "rb") as f:
            private_key = f.read()
        with open(public_key_path, "rb") as f:
            public_key = f.read()
        return AgentIdentity(private_key, public_key, fingerprint_of(public_key))

    private_key, public_key = crypto.generate_keypair()

    fd = os.open(
        private_key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, _PRIVATE_KEY_PERMISSIONS
    )
    try:
        os.write(fd, private_key)
    finally:
        os.close(fd)

    with open(public_key_path, "wb") as f:
        f.write(public_key)

    return AgentIdentity(private_key, public_key, fingerprint_of(public_key))
