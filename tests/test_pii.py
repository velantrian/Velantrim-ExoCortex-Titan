"""PII detection & redaction (GDPR Art. 5 data minimisation)."""
from core import pii


def test_detect_and_redact_email():
    text = "contact a.b@example.com please"
    assert any(f["type"] == "EMAIL" for f in pii.detect(text))
    red, found = pii.redact(text)
    assert "[EMAIL]" in red and "@" not in red
    assert found and "value" not in found[0]  # content-free findings


def test_credit_card_luhn_filtering():
    # Valid Luhn test card is detected.
    _red, found = pii.redact("card 4111 1111 1111 1111 end")
    assert any(f["type"] == "CREDIT_CARD" for f in found)
    # A 16-digit run that fails Luhn is NOT flagged as a card.
    assert not any(f["type"] == "CREDIT_CARD"
                   for f in pii.detect("num 1234567890123456 x"))


def test_email_wins_over_phone_on_overlap():
    found = pii.detect("reach me at john123@mail.com")
    assert "EMAIL" in [f["type"] for f in found]


def test_ipv4_and_summary():
    red, found = pii.redact("server 192.168.0.1 down")
    assert "[IPV4]" in red
    assert pii.summary(found).get("IPV4") == 1


def test_no_pii_unchanged():
    red, found = pii.redact("just a normal sentence")
    assert red == "just a normal sentence" and found == []


def test_redaction_flag_env(monkeypatch):
    monkeypatch.delenv("VELANTRIM_REDACT_PII", raising=False)
    assert pii.redaction_enabled() is False
    monkeypatch.setenv("VELANTRIM_REDACT_PII", "1")
    assert pii.redaction_enabled() is True
