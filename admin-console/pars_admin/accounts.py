import hashlib
import secrets
import sqlite3

_PBKDF2_ITERATIONS = 600_000
_SALT_BYTES = 16


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )


class AccountStore:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS accounts "
            "(username TEXT PRIMARY KEY, salt BLOB NOT NULL, password_hash BLOB NOT NULL)"
        )
        self._conn.commit()

    def create_account(self, username: str, password: str) -> None:
        existing = self._conn.execute(
            "SELECT 1 FROM accounts WHERE username = ?", (username,)
        ).fetchone()
        if existing is not None:
            raise ValueError(f"account already exists: {username}")

        salt = secrets.token_bytes(_SALT_BYTES)
        password_hash = _hash_password(password, salt)
        self._conn.execute(
            "INSERT INTO accounts (username, salt, password_hash) VALUES (?, ?, ?)",
            (username, salt, password_hash),
        )
        self._conn.commit()

    def verify_login(self, username: str, password: str) -> bool:
        row = self._conn.execute(
            "SELECT salt, password_hash FROM accounts WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            return False
        salt, expected_hash = row
        return secrets.compare_digest(_hash_password(password, salt), expected_hash)
