"""
Secure password hashing and verification using PBKDF2-HMAC-SHA256.
No third-party dependencies — uses only Python stdlib (hashlib, secrets).

Stored format in users.csv:
    username  — plaintext username
    salt      — 64-character hex string (32 random bytes)
    password  — 64-character hex string (PBKDF2-HMAC-SHA256 digest)
"""

import hashlib
import secrets

_ITERATIONS = 260_000  # OWASP 2023 recommendation for PBKDF2-SHA256


def hash_password(password: str) -> tuple[str, str]:
    """Hash a plaintext password with a fresh random salt.

    Returns:
        (salt_hex, hash_hex) — both are 64-char hex strings.
    """
    salt = secrets.token_hex(32)          # 32 bytes → 64 hex chars
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        _ITERATIONS,
    ).hex()
    return salt, pw_hash


def verify_password(password: str, salt_hex: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored salt+hash pair.

    Uses :func:`secrets.compare_digest` to guard against timing attacks.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        candidate = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt_hex.encode('utf-8'),
            _ITERATIONS,
        ).hex()
        return secrets.compare_digest(candidate, stored_hash)
    except Exception:
        return False
