"""Unit tests for CredentialManager."""

import pytest
from django.conf import settings

from integrations.services.credentials import CredentialManager

# ---------------------------------------------------------------------------
# Encrypt / Decrypt
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCredentialManagerEncryptDecrypt:
    def test_round_trip(self):
        creds = {"public_key": "pk-lf-abc", "secret_key": "sk-lf-xyz"}
        encrypted = CredentialManager.encrypt(creds)
        decrypted = CredentialManager.decrypt(encrypted)
        assert decrypted == creds

    def test_encrypt_returns_bytes(self):
        encrypted = CredentialManager.encrypt({"key": "val"})
        assert isinstance(encrypted, bytes)

    def test_decrypt_returns_dict(self):
        encrypted = CredentialManager.encrypt({"a": 1})
        result = CredentialManager.decrypt(encrypted)
        assert isinstance(result, dict)
        assert result["a"] == 1

    def test_encrypt_different_each_time(self):
        """Fernet uses a unique nonce per encryption."""
        creds = {"key": "value"}
        enc1 = CredentialManager.encrypt(creds)
        enc2 = CredentialManager.encrypt(creds)
        assert enc1 != enc2

    def test_decrypt_corrupted_blob_raises(self):
        with pytest.raises(ValueError, match="decrypt"):
            CredentialManager.decrypt(b"not-a-fernet-token")

    def test_decrypt_wrong_key_raises(self):
        """Encrypt with current key, then change key — decrypt should fail."""
        from cryptography.fernet import Fernet

        creds = {"k": "v"}
        encrypted = CredentialManager.encrypt(creds)

        original_key = settings.INTEGRATION_ENCRYPTION_KEY
        try:
            settings.INTEGRATION_ENCRYPTION_KEY = Fernet.generate_key().decode()
            with pytest.raises(ValueError, match="decrypt"):
                CredentialManager.decrypt(encrypted)
        finally:
            settings.INTEGRATION_ENCRYPTION_KEY = original_key

    def test_empty_dict_round_trip(self):
        encrypted = CredentialManager.encrypt({})
        assert CredentialManager.decrypt(encrypted) == {}

    def test_special_characters_preserved(self):
        creds = {"key": "val with 日本語 & spëcial chars!@#$%"}
        encrypted = CredentialManager.encrypt(creds)
        assert CredentialManager.decrypt(encrypted) == creds


# ---------------------------------------------------------------------------
# Key Masking
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCredentialManagerMasking:
    def test_mask_sk_lf_prefix(self):
        assert CredentialManager.mask_key("sk-lf-abcdef1234") == "sk-lf-****1234"

    def test_mask_pk_lf_prefix(self):
        assert CredentialManager.mask_key("pk-lf-abcdef1234") == "pk-lf-****1234"

    def test_mask_short_string(self):
        result = CredentialManager.mask_key("short")
        assert result == "****hort"

    def test_mask_empty_string(self):
        assert CredentialManager.mask_key("") == ""

    def test_mask_no_prefix_pattern(self):
        result = CredentialManager.mask_key("mykey12345678")
        assert result == "****5678"

    def test_mask_exactly_4_chars(self):
        """4-char string with no prefix: all 4 visible after ****."""
        assert CredentialManager.mask_key("abcd") == "****abcd"

    def test_mask_exactly_1_char(self):
        assert CredentialManager.mask_key("x") == "****x"

    def test_mask_prefix_with_no_rest(self):
        """Prefix only, nothing after it."""
        assert CredentialManager.mask_key("sk-lf-") == "sk-lf-****"

    def test_mask_prefix_with_short_rest(self):
        """Prefix with rest shorter than 4 chars."""
        assert CredentialManager.mask_key("sk-lf-ab") == "sk-lf-****ab"

    def test_mask_uppercase_prefix_no_match(self):
        """Uppercase prefix doesn't match the lowercase regex."""
        assert CredentialManager.mask_key("SK-LF-abcdefgh") == "****efgh"


# ---------------------------------------------------------------------------
# Decrypt edge cases
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCredentialManagerDecryptEdgeCases:
    def test_decrypt_empty_bytes_raises(self):
        with pytest.raises(ValueError, match="decrypt"):
            CredentialManager.decrypt(b"")

    def test_decrypt_none_raises(self):
        with pytest.raises((TypeError, ValueError)):
            CredentialManager.decrypt(None)

    def test_encrypt_non_serializable_raises(self):
        """Non-JSON-serializable objects should raise TypeError."""
        from datetime import datetime

        with pytest.raises(TypeError):
            CredentialManager.encrypt({"ts": datetime.now()})

    def test_missing_encryption_key_raises(self, settings):
        """If INTEGRATION_ENCRYPTION_KEY is empty, encrypt/decrypt must fail."""
        settings.INTEGRATION_ENCRYPTION_KEY = ""
        with pytest.raises(ValueError, match="INTEGRATION_ENCRYPTION_KEY"):
            CredentialManager.encrypt({"k": "v"})

    def test_none_encryption_key_raises(self, settings):
        """If INTEGRATION_ENCRYPTION_KEY is None, encrypt/decrypt must fail."""
        settings.INTEGRATION_ENCRYPTION_KEY = None
        with pytest.raises(ValueError, match="INTEGRATION_ENCRYPTION_KEY"):
            CredentialManager.encrypt({"k": "v"})
