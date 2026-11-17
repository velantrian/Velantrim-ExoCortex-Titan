"""
Telegram → L0 Raw Memory → L1 Fact (Спринт 2.6).

Минимальный ingest без обязательного long-polling: webhook или прямой вызов.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

logger = logging.getLogger(__name__)

MIN_TEXT_LEN = 2
MAX_TEXT_LEN = 8000


def is_telegram_enabled() -> bool:
    from core.feature_config import get_config

    return get_config().app.enable_telegram_ingest


def get_bot_token() -> str:
    return (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()


def ingest_telegram_message(
    text: str,
    *,
    chat_id: str | int,
    user_id: str | int | None = None,
    message_id: str | int | None = None,
    username: str | None = None,
) -> dict[str, Any]:
    """
    L0 → L1: сохранить сообщение Telegram как raw + Observed fact.

    source = telegram:{chat_id}
    metadata: channel, chat_id, user_id, message_id, username
    """
    body = (text or "").strip()
    if len(body) < MIN_TEXT_LEN:
        raise ValueError(f"Слишком короткое сообщение (мин. {MIN_TEXT_LEN} символа)")
    if len(body) > MAX_TEXT_LEN:
        body = body[:MAX_TEXT_LEN]

    chat_s = str(chat_id)
    user_s = str(user_id) if user_id is not None else "unknown"
    source = f"telegram:{chat_s}"

    from core.memory import get_fact, store_raw_text
    from core.cognitive_store import is_cognitive_store_enabled, save_fact_dict_result
    from core.write_result import ACCEPTED_WRITE_STATUSES

    # Stable delivery identity; 0 is a valid message id. No random retry identity.
    delivery = str(message_id) if message_id is not None else uuid.uuid4().hex
    fact_id = f"tg_{chat_s}_{delivery}"
    metadata: dict[str, Any] = {
        "channel": "telegram", "chat_id": chat_s, "user_id": user_s,
        "ingest_path": "telegram_l0",
    }
    if message_id is not None:
        metadata["message_id"] = str(message_id)
    if username:
        metadata["username"] = username[:128]
    if user_s != "unknown":
        metadata["somatic_marker"] = "neutral"

    # L0 is immutable and content-addressed. Its unique hash also deduplicates
    # concurrent deliveries; it may remain as input evidence after L1 rejection.
    raw_id = store_raw_text(body, source=source, source_type="telegram")
    result = save_fact_dict_result(
        {"fact_id": fact_id, "claim": body, "source": source,
         "confidence": .75, "metadata": metadata, "raw_input": body,
         "derived_from": raw_id},
        ensure_raw=False, link_provenance=False, create_only=True,
    )
    stored = get_fact(fact_id)
    accepted = result.status in ACCEPTED_WRITE_STATUSES
    matches = bool(stored and stored.get("claim") == body and stored.get("source") == source
                   and stored.get("derived_from") == raw_id)
    ok = accepted and matches
    reason = result.safe_reason_code
    if accepted and not matches:
        reason = "telegram_delivery_conflict"
    return {
        "ok": ok, "raw_id": raw_id, "fact_id": fact_id, "source": source,
        "fact": stored if ok else None,
        "write_status": result.status.value, "durable_write": result.durable_write,
        "reason_code": reason,
        # The L0 API returns an ID, not an insertion receipt; do not invent a metric.
        "deduplicated_raw": None,
        "deduplicated_delivery": accepted and not result.created and matches,
        **({"via": "cognitive_store"} if is_cognitive_store_enabled() else {}),
    }


def parse_telegram_update(update: dict[str, Any]) -> dict[str, Any] | None:
    """Извлечь текст из объекта Update Telegram Bot API."""
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return None
    text = msg.get("text") or msg.get("caption")
    if not text or not str(text).strip():
        return None
    chat = msg.get("chat") or {}
    from_user = msg.get("from") or {}
    return {
        "text": str(text).strip(),
        "chat_id": chat.get("id", "unknown"),
        "user_id": from_user.get("id"),
        "message_id": msg.get("message_id"),
        "username": from_user.get("username"),
    }


async def send_telegram_reply(
    chat_id: str | int,
    text: str,
    *,
    token: str | None = None,
) -> bool:
    """Отправить короткий ответ в чат (опционально после ingest)."""
    tok = token or get_bot_token()
    if not tok:
        return False
    try:
        import httpx
    except ImportError:
        logger.warning("httpx не установлен — ответ в Telegram пропущен")
        return False

    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text[:4000],
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(url, json=payload)
            return r.status_code == 200
    except Exception as exc:  # noqa: BLE001
        logger.warning("telegram sendMessage: %s", exc)
        return False


__all__ = [
    "ingest_telegram_message",
    "is_telegram_enabled",
    "parse_telegram_update",
    "send_telegram_reply",
    "get_bot_token",
]
