import os

from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    key = os.getenv("FERNET_SECRET_KEY")
    if not key:
        raise RuntimeError("FERNET_SECRET_KEY must be set to encrypt mail passwords")
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise RuntimeError("FERNET_SECRET_KEY must be a valid Fernet key") from exc


def encrypt_password(raw_password: str) -> str:
    return _fernet().encrypt(raw_password.encode()).decode()


def decrypt_password(encrypted_password: str) -> str:
    return _fernet().decrypt(encrypted_password.encode()).decode()
