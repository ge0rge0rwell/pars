from __future__ import annotations

import os
import stat
import uuid
from dataclasses import dataclass

from pars_shared import crypto
from pars_shared.crypto import fingerprint_of

_INSTANCE_ID_FILENAME = "admin_instance_id"
_PRIVATE_KEY_FILENAME = "trust_root.key"
_PUBLIC_KEY_FILENAME = "trust_root.pub"
_PRIVATE_KEY_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR
_DATA_DIR_PERMISSIONS = stat.S_IRWXU


@dataclass(frozen=True)
class AdminTrustRoot:
    admin_instance_id: str
    private_key: bytes
    public_key: bytes
    fingerprint: str


def ensure_admin_trust_root(data_dir: str) -> AdminTrustRoot:
    os.makedirs(data_dir, mode=_DATA_DIR_PERMISSIONS, exist_ok=True)
    instance_id_path = os.path.join(data_dir, _INSTANCE_ID_FILENAME)
    private_key_path = os.path.join(data_dir, _PRIVATE_KEY_FILENAME)
    public_key_path = os.path.join(data_dir, _PUBLIC_KEY_FILENAME)

    if all(
        os.path.exists(p) for p in (instance_id_path, private_key_path, public_key_path)
    ):
        with open(instance_id_path) as f:
            admin_instance_id = f.read().strip()
        with open(private_key_path, "rb") as f:
            private_key = f.read()
        with open(public_key_path, "rb") as f:
            public_key = f.read()
        return AdminTrustRoot(
            admin_instance_id, private_key, public_key, fingerprint_of(public_key)
        )

    admin_instance_id = uuid.uuid4().hex
    private_key, public_key = crypto.generate_keypair()

    with open(instance_id_path, "w") as f:
        f.write(admin_instance_id)

    fd = os.open(
        private_key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, _PRIVATE_KEY_PERMISSIONS
    )
    try:
        os.write(fd, private_key)
    finally:
        os.close(fd)

    with open(public_key_path, "wb") as f:
        f.write(public_key)

    return AdminTrustRoot(
        admin_instance_id, private_key, public_key, fingerprint_of(public_key)
    )
