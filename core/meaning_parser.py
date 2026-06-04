"""
🧬 core/meaning_parser.py — MeaningParser: Verbatim + Gist Dual Encoding (V8.7 Titan)

Из velantrim_fixed v1.0.0. Реализует принцип Fuzzy-Trace Theory (Brainerd & Reyna):
    Мозг кодирует информацию в ДВУХ независимых представлениях ОДНОВРЕМЕННО:
      VERBATIM  — точная копия слов. Быстро угасает (дни-недели).
      GIST      — суть, смысл, инвариант. Угасает медленно (месяцы-годы).

Применение в Velantrim:
    При ingestion создаются ДВА факта:
      1. VERBATIM — точный текст, короткий TTL, node_type=FACT
      2. GIST     — суть, длинный TTL, node_type=PRINCIPLE или CONCEPT

    Поиск идёт сначала по GIST-слою (быстро, суть).
    Детали запрашиваются из VERBATIM при необходимости (drill-down).

Отличие от essence.py:
    essence.py — детерминированный gist extractor (на существующих фактах).
    MeaningParser — LLM-based создание verbatim+gist ПРИ INGEST (на входе).

Совместимость:
    При LLM_PROVIDER=none → MockLLMClient с детерминированными заглушками.
    Не ломает essence.py — они работают на разных этапах.

Инварианты:
    I-MP1: Оба факта проходят через TruthGate перед сохранением.
    I-MP2: Verbatim факт всегда имеет source = исходный текст (traceability).
    I-MP3: Gist факт маркирован как производный (derived_from = verbatim_id).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("velantrim.meaning_parser")

# ─── Системные промпты ───────────────────────────────────────────────────────

_GIST_SYSTEM = """Ты — компонент памяти Velantrim. Твоя задача: извлечь СУТЬ текста.

Правила:
1. Суть = 1-2 предложения, не больше
2. Никаких конкретных дат, имён, чисел — только принципы и смыслы
3. Начни с того «зачем это нужно» или «что из этого следует»
4. Не пересказывай, а ОБОБЩАЙ

Пример:
Текст: «Клетка использует АТФ как универсальный носитель энергии для всех биохимических процессов»
Суть: «Жизнь основана на универсальных носителях энергии, позволяющих клеткам поддерживать организацию»

Отвечай ТОЛЬКО сутью, без вводных слов."""

_NODE_TYPE_SYSTEM = """Определи тип знания из текста. Ответь ТОЛЬКО одним словом:
INVARIANT  — если это вечный принцип применимый в любой области
PRINCIPLE  — если это правило или закон в конкретной области
CONCEPT    — если это понятие или идея
FACT       — если это конкретный изолированный факт

Примеры ответов: INVARIANT, PRINCIPLE, CONCEPT, FACT"""


# ─── Результат ────────────────────────────────────────────────────────────────

@dataclass
class ParsedMeaning:
    """
    Результат разбора текста на verbatim и gist.

    verbatim_fact — точный текст (node_type=FACT, короткий TTL)
    gist_fact     — суть (node_type=PRINCIPLE/CONCEPT, длинный TTL)

    Оба готовы к передаче в store_fact().
    """
    verbatim_fact: dict
    gist_fact: dict
    source: str
    confidence: float

    def both(self) -> list[dict]:
        """Вернуть оба факта в порядке gist→verbatim (суть первой)."""
        return [self.gist_fact, self.verbatim_fact]


# ─── Mock LLM для детерминированного режима ─────────────────────────────────

class _MockLLM:
    """Детерминированные заглушки для режима без реального LLM."""

    async def complete(self, prompt: str, max_tokens: int = 500, system: Optional[str] = None) -> str:
        if system and "СУТЬ" in system:
            return prompt[:150].strip() + "..."
        if system and "тип знания" in system.lower():
            if any(w in prompt.lower() for w in ["всегда", "никогда", "любой", "везде"]):
                return "INVARIANT"
            if any(w in prompt.lower() for w in ["правило", "закон", "принцип"]):
                return "PRINCIPLE"
            if any(w in prompt.lower() for w in ["понятие", "идея", "концепция"]):
                return "CONCEPT"
            return "FACT"
        return prompt[:200].strip()


# ─── Основной класс ──────────────────────────────────────────────────────────

class MeaningParser:
    """
    Парсер смысла: verbatim + gist параллельно при ingestion.

    Fuzzy-Trace Theory (Brainerd & Reyna):
        Два следа памяти создаются ОДНОВРЕМЕННО при восприятии.
        Verbatim — точный, быстро угасает.
        Gist — суть, медленно угасает.

    Использование:
        parser = MeaningParser(llm_client=my_llm_client)

        result = await parser.parse(
            text="Клетка — базовая единица жизни...",
            source="biology_textbook",
            confidence=0.9,
        )

        store.store_fact(result.verbatim_fact)
        store.store_fact(result.gist_fact)
    """

    def __init__(
        self,
        llm_client=None,
        *,
        auto_detect_node_type: bool = True,
    ) -> None:
        self._llm = llm_client or _MockLLM()
        self._auto_node_type = auto_detect_node_type

    async def parse(
        self,
        text: str,
        source: str,
        confidence: float = 0.7,
        domain: Optional[str] = None,
    ) -> ParsedMeaning:
        """
        Разобрать текст на verbatim и gist.

        Args:
            text: исходный текст (предложение, абзац)
            source: откуда пришёл текст
            confidence: уверенность в достоверности источника
            domain: область знаний (опционально)

        Returns:
            ParsedMeaning с двумя готовыми фактами.
        """
        text = text.strip()
        if not text:
            raise ValueError("MeaningParser.parse: пустой текст")

        text_hash = hashlib.sha256(text.encode()).hexdigest()[:12]
        verbatim_id = f"verb_{text_hash}"
        gist_id = f"gist_{text_hash}"

        # Параллельное извлечение gist и node_type (как в биологии — одновременно)
        gist, node_type = await asyncio.gather(
            self._extract_gist(text),
            self._detect_node_type(text) if self._auto_node_type
            else asyncio.sleep(0, result="CONCEPT"),
        )
        if isinstance(node_type, float):
            node_type = "CONCEPT"

        metadata_base = {
            "source_text_hash": text_hash,
            "domain": domain or "unknown",
            "parser": "MeaningParser v1.0",
        }

        # VERBATIM: точный текст, node_type=FACT, быстрый decay
        verbatim_fact = {
            "fact_id": verbatim_id,
            "claim": text,
            "source": source,
            "confidence": confidence,
            "epistemic_state": "Observed",
            "node_type": "FACT",
            "metadata": {
                **metadata_base,
                "encoding": "verbatim",
                "ttl": "short",
            },
            "derived_from": None,
            "provenance": [f"ingest:{source}"],
        }

        # GIST: суть, node_type=PRINCIPLE/CONCEPT, длинный decay
        gist_fact = {
            "fact_id": gist_id,
            "claim": gist,
            "source": source,
            "confidence": min(1.0, confidence * 0.9),
            "epistemic_state": "Observed",
            "node_type": node_type,
            "metadata": {
                **metadata_base,
                "encoding": "gist",
                "ttl": "long",
            },
            "derived_from": verbatim_id,
            "provenance": [f"ingest:{source}", f"gist_of:{verbatim_id}"],
        }

        logger.info(
            "MeaningParser: %s → verbatim+%s gist",
            text_hash, node_type,
        )
        return ParsedMeaning(
            verbatim_fact=verbatim_fact,
            gist_fact=gist_fact,
            source=source,
            confidence=confidence,
        )

    async def _extract_gist(self, text: str) -> str:
        """Извлечь суть текста через LLM."""
        try:
            result = await self._llm.complete(
                prompt=text,
                max_tokens=200,
                system=_GIST_SYSTEM,
            )
            return (result or text[:150]).strip()
        except Exception as exc:
            logger.warning("MeaningParser._extract_gist: %s — fallback на первые 150 символов", exc)
            return text[:150].strip() + "..."

    async def _detect_node_type(self, text: str) -> str:
        """Определить тип знания через LLM."""
        try:
            result = await self._llm.complete(
                prompt=text,
                max_tokens=10,
                system=_NODE_TYPE_SYSTEM,
            )
            result = (result or "FACT").strip().upper()
            valid = {"INVARIANT", "PRINCIPLE", "CONCEPT", "FACT", "DOMAIN"}
            return result if result in valid else "FACT"
        except Exception:
            return "FACT"


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_parser: Optional[MeaningParser] = None


def get_meaning_parser(llm_client=None) -> MeaningParser:
    global _parser
    if _parser is None:
        _parser = MeaningParser(llm_client=llm_client)
    return _parser


__all__ = [
    "MeaningParser",
    "ParsedMeaning",
    "get_meaning_parser",
]
