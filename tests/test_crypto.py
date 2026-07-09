"""Encryption at rest (GDPR Art. 32) — field-level crypto primitive."""
import pytest

from core import crypto


def test_disabled_is_identity(monkeypatch):
    monkeypatch.delenv("VELANTRIM_ENCRYPTION_KEY", raising=False)
    assert crypto.is_enabled() is False
    assert crypto.encrypt("hello") == "hello"      # identity when off
    assert crypto.decrypt("hello") == "hello"
    assert crypto.backend_name() is None


def test_roundtrip(monkeypatch):
    monkeypatch.setenv("VELANTRIM_ENCRYPTION_KEY", "test-passphrase-123")
    assert crypto.is_enabled() is True
    token = crypto.encrypt("secret personal data")
    assert token != "secret personal data"
    assert token.startswith((crypto._MARK_FERNET, crypto._MARK_HMAC))
    assert crypto.decrypt(token) == "secret personal data"
    assert crypto.backend_name() in ("fernet", "hmac-sha256")


def test_plaintext_passthrough_on_decrypt(monkeypatch):
    monkeypatch.setenv("VELANTRIM_ENCRYPTION_KEY", "k")
    # A value with no scheme marker is legacy plaintext → returned unchanged.
    assert crypto.decrypt("just text, no marker") == "just text, no marker"


def test_tamper_detection(monkeypatch):
    monkeypatch.setenv("VELANTRIM_ENCRYPTION_KEY", "k1")
    token = crypto.encrypt("data to protect")
    if not token.startswith(crypto._MARK_HMAC):
        pytest.skip("Fernet backend active; stdlib tamper path not exercised here")
    body = token[len(crypto._MARK_HMAC):]
    i = len(body) // 2
    flipped = "A" if body[i] != "A" else "B"
    tampered = crypto._MARK_HMAC + body[:i] + flipped + body[i + 1:]
    with pytest.raises(ValueError):
        crypto.decrypt(tampered)


def test_wrong_key_fails(monkeypatch):
    monkeypatch.setenv("VELANTRIM_ENCRYPTION_KEY", "right-key")
    token = crypto.encrypt("payload")
    if not token.startswith(crypto._MARK_HMAC):
        pytest.skip("Fernet backend active; deterministic wrong-key path skipped")
    monkeypatch.setenv("VELANTRIM_ENCRYPTION_KEY", "wrong-key")
    with pytest.raises(ValueError):
        crypto.decrypt(token)
