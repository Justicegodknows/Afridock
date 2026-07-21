import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from afridock_api.config import get_settings


class CredentialDecryptionError(Exception):
    """Stored provider credentials could not be decrypted (wrong/rotated key, or tampering)."""


@lru_cache
def _fernet() -> Fernet:
    settings = get_settings()
    key = settings.credential_encryption_key
    if not key:
        # Local-dev fallback: derive a stable key from api_secret_key so
        # `make dev` works out of the box. Every deployed environment must
        # set CREDENTIAL_ENCRYPTION_KEY explicitly and independently of
        # API_SECRET_KEY (rotating one should not silently rotate the other).
        key = base64.urlsafe_b64encode(
            hashlib.sha256(settings.api_secret_key.encode()).digest()
        ).decode()
    return Fernet(key.encode())


def encrypt_credential(plaintext: str) -> str:
    """Encrypt a provider credential for storage in ProviderCredential.encrypted_config."""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_credential(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise CredentialDecryptionError("stored credential could not be decrypted") from exc
