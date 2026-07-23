import pytest
from afridock_api.inference.credentials import (
    CredentialDecryptionError,
    decrypt_credential,
    encrypt_credential,
)


def test_encrypt_decrypt_roundtrip() -> None:
    plaintext = "sk-super-secret-provider-api-key"

    ciphertext = encrypt_credential(plaintext)

    assert ciphertext != plaintext
    assert decrypt_credential(ciphertext) == plaintext


def test_decrypting_garbage_raises_decryption_error() -> None:
    with pytest.raises(CredentialDecryptionError):
        decrypt_credential("not-a-valid-fernet-token")
