from __future__ import annotations

import pytest

from api.mcp_gateway import _derive_batch_idempotency_key


def test_batch_derivation_rejects_overlong_source_header() -> None:
    with pytest.raises(ValueError, match="exceeds 128"):
        _derive_batch_idempotency_key("x" * 129, 1)


def test_batch_derivation_rejects_control_character_source_header() -> None:
    with pytest.raises(ValueError, match="visible ASCII"):
        _derive_batch_idempotency_key("bad\nkey", 1)
