from __future__ import annotations

import json
import os
from dataclasses import dataclass

_PIN_FILENAME = "admin_pin.json"


@dataclass(frozen=True)
class PinResult:
    accepted: bool
    conflict: bool


class AdminPinStore:
    def __init__(self, data_dir: str):
        self._path = os.path.join(data_dir, _PIN_FILENAME)
        os.makedirs(data_dir, exist_ok=True)
        self._pin = self._load()

    def _load(self) -> dict | None:
        if not os.path.exists(self._path):
            return None
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, admin_instance_id: str, admin_pubkey_hex: str) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "admin_instance_id": admin_instance_id,
                    "admin_pubkey_hex": admin_pubkey_hex,
                },
                f,
            )

    def is_pinned(self) -> bool:
        return self._pin is not None

    def pin_or_verify(self, admin_instance_id: str, admin_pubkey: bytes) -> PinResult:
        pubkey_hex = admin_pubkey.hex()

        if self._pin is None:
            self._save(admin_instance_id, pubkey_hex)
            self._pin = {
                "admin_instance_id": admin_instance_id,
                "admin_pubkey_hex": pubkey_hex,
            }
            return PinResult(accepted=True, conflict=False)

        matches = (
            self._pin["admin_instance_id"] == admin_instance_id
            and self._pin["admin_pubkey_hex"] == pubkey_hex
        )
        if matches:
            return PinResult(accepted=True, conflict=False)
        return PinResult(accepted=False, conflict=True)
