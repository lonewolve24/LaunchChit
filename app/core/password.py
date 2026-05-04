"""Password hashing — using simple PBKDF2 (standard library)."""
import hashlib
import secrets


def hash_password(plain: str) -> str:
    """Hash a plaintext password using PBKDF2."""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac(
        "sha256", plain.encode("utf-8"), salt.encode("utf-8"), iterations=100_000
    )
    return f"{salt}${hash_obj.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a hash."""
    try:
        salt, stored_hash = hashed.split("$")
        hash_obj = hashlib.pbkdf2_hmac(
            "sha256", plain.encode("utf-8"), salt.encode("utf-8"), iterations=100_000
        )
        return hash_obj.hex() == stored_hash
    except (ValueError, AttributeError):
        return False
