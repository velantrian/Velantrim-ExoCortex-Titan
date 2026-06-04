"""
Именование ProtoConcept — Phase 3 (RFC0066 #20).

Стратегия:
  1. lazy_name (0 токенов) — по умолчанию
  2. LLM (опционально) — при ENABLE_CONCEPT_LLM_NAMING и confidence ≥ порога
"""

from __future__ import annotations

import logging
import re

from core.concept_emergence import ProtoConcept, get_concept_detector
from core.feature_config import get_config

logger = logging.getLogger(__name__)

_NAME_SANITIZE = re.compile(r"[^\wА-Яа-яЁё\s\-]", re.UNICODE)


def is_concept_llm_naming_enabled() -> bool:
    cfg = get_config().app
    return bool(
        getattr(cfg, "enable_concept_llm_naming", False)
        and getattr(cfg, "enable_concept_emergence", False)
    )


def _llm_name_min_confidence() -> float:
    return float(get_config().app.emergence_llm_name_min_confidence)


def _sanitize_name(raw: str, *, max_len: int = 80) -> str:
    text = (raw or "").strip().strip('"\'')
    text = _NAME_SANITIZE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    if len(text) > max_len:
        text = text[:max_len].strip()
    return text


async def name_proto_with_llm(proto: ProtoConcept) -> str | None:
    """
    Сгенерировать короткое имя концепта через LLM.
    Возвращает None при ошибке / отсутствии API key.
    """
    from core.llm import get_async_client, llm_chat_response

    if not get_async_client():
        return None

    entities = ", ".join(sorted(proto.entities))
    prompt = (
        "Ты система памяти AI. Дан набор сущностей, которые часто появляются вместе.\n"
        f"Сущности: {entities}\n\n"
        "Придумай КОРОТКОЕ имя концепта (2–5 слов) на русском или английском, "
        "без кавычек и пояснений. Только имя."
    )
    try:
        raw = await llm_chat_response(
            [{"role": "user", "content": prompt}],
            context="concept_naming",
        )
        name = _sanitize_name(raw)
        if name and not name.startswith("Извините"):
            return name
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM proto naming failed %s: %s", proto.proto_id, exc)
    return None


async def resolve_proto_name(
    proto: ProtoConcept,
    *,
    use_llm: bool | None = None,
) -> str:
    """
    Итоговое имя: LLM (если разрешено и уверенность высокая) или lazy_name.
    """
    if proto.name:
        return proto.name

    if use_llm is None:
        use_llm = (
            is_concept_llm_naming_enabled()
            and proto.confidence >= _llm_name_min_confidence()
        )

    if use_llm:
        llm_name = await name_proto_with_llm(proto)
        if llm_name:
            proto.name = llm_name
            logger.info("proto named via LLM: %s -> %s", proto.proto_id, llm_name)
            return llm_name

    detector = get_concept_detector()
    lazy = detector.lazy_name(proto.proto_id) or proto.proto_id
    return lazy


__all__ = [
    "is_concept_llm_naming_enabled",
    "name_proto_with_llm",
    "resolve_proto_name",
]
