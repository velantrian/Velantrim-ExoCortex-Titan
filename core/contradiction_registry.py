"""
⚔️ core/contradiction_registry.py — ContradictionRegistry + NLI Scoring (V8.7 Titan)

Из velantrim_fixed v8.4.4. Двухуровневый детектор противоречий.

Проблема которую решает:
    Классический token-XOR детектор НЕ видит противоречие в:
    "Кошки быстрее собак" vs "Собаки быстрее кошек"
    Потому что нет отрицания, а токены одинаковые.

    NLI cross-encoder (DeBERTa-v3) понимает семантику и видит contradiction.

Архитектура (CRISPR-аналог):
    Tier 1:  Token pre-filter    O(1)       отбор кандидатов
    Tier 2a: NLI cross-encoder   ~100ms     семантическое обнаружение
    Tier 2b: Token+negation XOR   O(1)      fallback без sentence-transformers

    Spacer — запись о противоречии (как CRISPR-спейсер в иммунной системе бактерий).
    При повторном обнаружении — encounter_count++ → система "помнит" этот конфликт.

Инварианты:
    I-CR1: ContradictionRegistry — только in-memory. Не пишет в граф.
    I-CR2: NLI scorer — lazy load. Отсутствие модели = token+negation fallback.
    I-CR3: Spacer entry хранит detection_method (token_xor | nli) для аудита.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import FrozenSet, List, Optional

logger = logging.getLogger("velantrim.contradiction_registry")

# ─── NLI Cross-Encoder ───────────────────────────────────────────────────────

class NLIContradictionScorer:
    """
    Lazy-loaded NLI cross-encoder для семантического обнаружения противоречий.

    Модель: cross-encoder/nli-deberta-v3-small (~85 MB, ~100ms/pair CPU).
    SNLI accuracy ~88% vs ~55% token baseline.

    Что исправляет:
        "Кошки быстрее собак" vs "Собаки быстрее кошек"
        token-XOR: НЕ противоречие (нет отрицания)
        NLI:       contradiction prob ~0.91
    """

    MODEL_NAME = "cross-encoder/nli-deberta-v3-small"
    CONTRADICTION_THRESHOLD = 0.60

    def __init__(self) -> None:
        self._model = None
        self._available: Optional[bool] = None
        self._contradiction_idx: int = 0

    @property
    def available(self) -> bool:
        if self._available is None:
            self._try_load()
        return bool(self._available)

    def _try_load(self) -> None:
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.MODEL_NAME)
            cfg = getattr(getattr(self._model, "model", None), "config", None)
            if cfg is not None:
                label2id = getattr(cfg, "label2id", {})
                if label2id:
                    self._contradiction_idx = int(
                        label2id.get("contradiction",
                        label2id.get("CONTRADICTION", 0))
                    )
            self._available = True
            logger.info("NLI scorer loaded: %s", self.MODEL_NAME)
        except ImportError:
            logger.info("sentence-transformers не установлен — token+negation fallback.")
            self._available = False
        except Exception as exc:
            logger.warning("NLI model load failed: %s — fallback mode", exc)
            self._available = False

    def contradiction_score(self, claim_a: str, claim_b: str) -> float:
        """Probability [0.0, 1.0] что claim_b противоречит claim_a."""
        if not self.available or self._model is None:
            return 0.0
        try:
            raw = self._model.predict([(claim_a, claim_b)])
            logits = raw[0] if hasattr(raw[0], "__len__") else raw
            exp_l = [math.exp(float(l)) for l in logits]
            probs = [e / sum(exp_l) for e in exp_l]
            return float(probs[self._contradiction_idx])
        except Exception as exc:
            logger.warning("NLI scoring failed: %s", exc)
            return 0.0


# Глобальный scorer (для тестового мокинга)
_nli_scorer = NLIContradictionScorer()


def _get_nli_scorer() -> NLIContradictionScorer:
    return _nli_scorer


def _set_nli_scorer(scorer: NLIContradictionScorer) -> None:
    global _nli_scorer
    _nli_scorer = scorer


# ─── Нормализация claim ──────────────────────────────────────────────────────

def _normalize_claim(claim: str) -> FrozenSet[str]:
    """Токенная нормализация для Tier 1 pre-filter (без стоп-слов)."""
    stopwords = {
        "и", "в", "на", "с", "по", "для", "от", "до", "при", "из",
        "the", "a", "an", "is", "are", "was", "were", "of", "in",
        "to", "be", "that", "this", "it",
    }
    tokens = re.findall(r"\w+", claim.lower())
    return frozenset(t for t in tokens if t not in stopwords and len(t) > 2)


# ─── Spacer Entry ────────────────────────────────────────────────────────────

@dataclass
class SpacerEntry:
    """Запись в реестре противоречий — аналог CRISPR-спейсера."""
    fact_id_a: str
    fact_id_b: str
    claim_a: str
    claim_b: str
    encounter_count: int = 1
    first_seen: str = ""
    last_seen: str = ""
    detection_method: str = "token_xor"  # "token_xor" | "nli"


# ─── ContradictionRegistry ────────────────────────────────────────────────────

class ContradictionRegistry:
    """
    Реестр противоречий с двухуровневым детектором.

    CRISPR-аналогия:
        Spacer = запись о встреченном противоречии (иммунная память)
        При повторном обнаружении encounter_count++ — система "помнит" конфликт.

    Tier 1:  Token pre-filter     O(1)       overlap >= 1 → кандидат
    Tier 2a: NLI cross-encoder    ~100ms     contradiction_prob ≥ threshold → found
    Tier 2b: Token+negation XOR    O(1)       overlap >= 2 + negation XOR → found
    """

    _NEGATION = frozenset({"не", "нет", "no", "not", "never", "никогда", "без"})

    def __init__(self) -> None:
        self._spacers: dict[tuple[str, str], SpacerEntry] = {}
        self._index: dict[str, set[str]] = {}
        self._token_cache: dict[str, FrozenSet[str]] = {}
        self._stats = {
            "lookups": 0,
            "hits": 0,
            "spacers_added": 0,
            "nli_calls": 0,
            "nli_hits": 0,
            "token_xor_hits": 0,
        }

    # ── Регистрация ───────────────────────────────────────────────────────

    def record(
        self,
        fact_id_a: str, claim_a: str,
        fact_id_b: str, claim_b: str,
        method: str = "token_xor",
    ) -> None:
        """Зарегистрировать противоречие между двумя фактами."""
        key = (min(fact_id_a, fact_id_b), max(fact_id_a, fact_id_b))
        now = datetime.now(timezone.utc).isoformat()

        if key in self._spacers:
            self._spacers[key].encounter_count += 1
            self._spacers[key].last_seen = now
            logger.info(
                "ContradictionRegistry PRIMED: %s ↔ %s (encounter #%d)",
                fact_id_a[:8], fact_id_b[:8], self._spacers[key].encounter_count,
            )
        else:
            self._spacers[key] = SpacerEntry(
                fact_id_a=fact_id_a, fact_id_b=fact_id_b,
                claim_a=claim_a, claim_b=claim_b,
                first_seen=now, last_seen=now,
                detection_method=method,
            )
            self._index.setdefault(fact_id_a, set()).add(fact_id_b)
            self._index.setdefault(fact_id_b, set()).add(fact_id_a)
            self._stats["spacers_added"] += 1

        self._token_cache[fact_id_a] = _normalize_claim(claim_a)
        self._token_cache[fact_id_b] = _normalize_claim(claim_b)

    # ── Поиск ────────────────────────────────────────────────────────────

    def known_contradictions(self, fact_id: str) -> List[str]:
        """O(1) lookup: все известные противоречия для fact_id."""
        self._stats["lookups"] += 1
        partners = self._index.get(fact_id, set())
        if partners:
            self._stats["hits"] += 1
        return list(partners)

    def is_primed(self, fact_id_a: str, fact_id_b: str) -> bool:
        """True если пара уже встречалась раньше (encounter_count > 1)."""
        key = (min(fact_id_a, fact_id_b), max(fact_id_a, fact_id_b))
        entry = self._spacers.get(key)
        return entry is not None and entry.encounter_count > 1

    def find_new_contradictions(
        self,
        fact_id: str,
        claim: str,
        validated_facts: List[dict],
    ) -> List[str]:
        """
        Искать НОВЫЕ противоречия среди Validated фактов.

        Pipeline:
            Tier 1: token overlap ≥ 1 → кандидат
            Tier 2a (NLI available):   contradiction_prob ≥ threshold → found
            Tier 2b (NLI unavailable): overlap ≥ 2 + negation XOR → found
        """
        claim_tokens = _normalize_claim(claim)
        scorer = _get_nli_scorer()
        use_nli = scorer.available
        found: List[str] = []

        for stored in validated_facts:
            s_id = stored.get("fact_id", "")
            if s_id == fact_id:
                continue

            s_claim = stored.get("claim", "")
            s_tokens = _normalize_claim(s_claim)

            # Tier 1: token pre-filter
            overlap = len(claim_tokens & s_tokens)
            if overlap < 1:
                continue

            # Tier 2a: NLI
            if use_nli:
                self._stats["nli_calls"] += 1
                prob = scorer.contradiction_score(claim, s_claim)
                if prob >= NLIContradictionScorer.CONTRADICTION_THRESHOLD:
                    found.append(s_id)
                    self._stats["nli_hits"] += 1
                    self.record(fact_id, claim, s_id, s_claim, method="nli")
            else:
                # Tier 2b: token+negation XOR fallback
                if overlap >= 2:
                    has_neg_a = bool(self._NEGATION & set(re.findall(r"\w+", claim.lower())))
                    has_neg_b = bool(self._NEGATION & set(re.findall(r"\w+", s_claim.lower())))
                    if has_neg_a != has_neg_b:
                        found.append(s_id)
                        self._stats["token_xor_hits"] += 1
                        self.record(fact_id, claim, s_id, s_claim, method="token_xor")

        return found

    def stats(self) -> dict:
        return dict(self._stats)

    def spacer_count(self) -> int:
        return len(self._spacers)


# ─── Глобальный реестр ───────────────────────────────────────────────────────

_registry: Optional[ContradictionRegistry] = None


def get_contradiction_registry() -> ContradictionRegistry:
    global _registry
    if _registry is None:
        _registry = ContradictionRegistry()
    return _registry


def reset_contradiction_registry() -> None:
    global _registry
    _registry = None


__all__ = [
    "ContradictionRegistry",
    "NLIContradictionScorer",
    "SpacerEntry",
    "get_contradiction_registry",
    "reset_contradiction_registry",
]
