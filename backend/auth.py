"""
Password hashing using SHA-256 with a per-user random salt.
No third-party dependencies — uses only Python stdlib (hashlib, secrets).

Stored fields in the users table:
    username  — plaintext username
    salt      — 32-character hex string (16 random bytes)
    password  — 64-character hex string (SHA-256 digest of salt+password)
"""

import hashlib
import secrets


def hash_password(password: str) -> tuple[str, str]:
    """Hash a plaintext password with a fresh random salt.

    Returns:
        (salt_hex, hash_hex)
    """
    salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return salt, pw_hash


def verify_password(password: str, salt_hex: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored salt+hash pair.

    Uses :func:`secrets.compare_digest` to guard against timing attacks.
    """
    try:
        candidate = hashlib.sha256((salt_hex + password).encode('utf-8')).hexdigest()
        return secrets.compare_digest(candidate, stored_hash)
    except Exception:
        return False
