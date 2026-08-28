"""
Credential manager for Agentcc — encrypts/decrypts sensitive values at rest.

Reuses the Fernet-based CredentialManager from integrations for the actual
crypto operations.  Adds helpers for single-value tokens (e.g. admin_token)
and for masking display values.
"""

from integrations.services.credentials import CredentialManager

ENCRYPTED_PREFIX = "enc::"


def encrypt_token(token: str) -> str:
    """Encrypt a single string token. Returns ``enc::``-prefixed ciphertext."""
    if not token or token.startswith(ENCRYPTED_PREFIX):
        return token
    blob = CredentialManager.encrypt({"v": token})
    return ENCRYPTED_PREFIX + (
        blob.decode("utf-8") if isinstance(blob, bytes) else blob
    )


def decrypt_token(token: str) -> str:
    """Decrypt an ``enc::``-prefixed ciphertext back to plaintext."""
    if not token or not token.startswith(ENCRYPTED_PREFIX):
        return token
    raw = token[len(ENCRYPTED_PREFIX) :]
    blob = raw.encode("utf-8") if isinstance(raw, str) else raw
    data = CredentialManager.decrypt(blob)
    return data.get("v", "")


def mask_key(key_str: str) -> str:
    """Mask a key string, showing only the first 4 and last 4 characters."""
    if not key_str:
        return ""
    if len(key_str) > 8:
        return f"{key_str[:4]}...{key_str[-4:]}"
    return "****"
