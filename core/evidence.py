"""
📚 core/evidence.py — Evidence Scoring Model (B3)
===================================================
5 одинаковых ссылок из одного источника ≠ 5 независимых.

evidence_strength = f(
    source_reliability,   — насколько источник надёжен
    independence_score,   — насколько источники независимы
    recency_score,        — насколько данные свежие
    directness_score,     — прямое или косвенное свидетельство
    corroboration_score,  — сколько разных источников подтверждают
)

Это закрывает класс манипуляций типа:
"Вот 10 статей" (все с одного сайта) → independence_score = 0.15

Sprint 1b — Этап B3
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

# ── EvidenceItem ──────────────────────────────────────────────────────────────

@dataclass
class EvidenceItem:
    """Одна единица доказательства."""
    source_id:      str                    # уникальный ID источника/домена
    source_type:    str = "unknown"        # тип источника
    source_domain:  str = "unknown"        # домен (bbc.com, pubmed.ncbi, etc.)
    published_at:   str | None = None   # дата публикации ISO
    directness:     float = 0.5            # 1.0 = прямой эксперимент, 0.0 = слухи
    content_hash:   str | None = None   # для дедупликации дублей
    # T1.3 (P2): структурный EvidenceRef — привязка claim к источнику на уровне
    # фрагмента, а не только названия. Опционально и обратносовместимо.
    chunk_id:       str | None = None   # ID фрагмента документа
    span:           str | None = None   # диапазон в источнике, напр. "120-340"
    quote:          str | None = None   # дословная цитата под claim

    # Directness levels для удобства
    DIRECT_EXPERIMENT    = 1.00  # "мы измерили сами"
    DIRECT_OBSERVATION   = 0.85  # "мы видели"
    SECONDARY_ANALYSIS   = 0.65  # "мы проанализировали данные"
    THIRD_PARTY_REPORT   = 0.50  # "по данным организации X"
    EXPERT_OPINION       = 0.45  # "эксперт считает что"
    INDIRECT_INFERENCE   = 0.30  # "можно предположить что"
    RUMOR_ANECDOTE       = 0.10  # "говорят что"


# ── EvidenceModel ─────────────────────────────────────────────────────────────

class EvidenceModel:
    """
    Вычисляет evidence_strength из набора свидетельств.

    Использование:
        model = EvidenceModel()
        model.add(EvidenceItem("bbc.com", "reputable_news", directness=0.7, published_at="2024-01"))
        model.add(EvidenceItem("pubmed.ncbi", "peer_reviewed_paper", directness=0.9, published_at="2024-03"))
        result = model.compute()
        print(result.evidence_strength)    # 0.76
        print(result.independence_score)   # 0.90  (разные домены)
    """

    def __init__(self) -> None:
        self._items: list[EvidenceItem] = []

    def add(self, item: EvidenceItem) -> EvidenceModel:
        self._items.append(item)
        return self

    def add_raw(
        self,
        source_id:   str,
        source_type: str = "unknown",
        source_domain: str = "unknown",
        directness:  float = 0.5,
        published_at: str | None = None,
    ) -> EvidenceModel:
        """Удобный метод для добавления без создания EvidenceItem."""
        self._items.append(EvidenceItem(
            source_id=source_id,
            source_type=source_type,
            source_domain=source_domain,
            directness=directness,
            published_at=published_at,
        ))
        return self

    def compute(self) -> EvidenceResult:
        """Вычислить evidence_strength из всех добавленных свидетельств."""
        if not self._items:
            return EvidenceResult(
                evidence_strength=0.0,
                item_count=0,
                independence_score=0.0,
                recency_score=0.0,
                directness_score=0.0,
                corroboration_score=0.0,
                source_reliability_avg=0.0,
                note="Нет доказательств",
            )

        # 1. source_reliability — средняя надёжность источников
        from core.confidence import SOURCE_RELIABILITY
        reliabilities = [
            SOURCE_RELIABILITY.get(item.source_type, 0.50)
            for item in self._items
        ]
        source_reliability_avg = sum(reliabilities) / len(reliabilities)

        # 2. independence_score — насколько источники независимы
        independence = self._compute_independence()

        # 3. recency_score — свежесть доказательств
        recency = self._compute_recency()

        # 4. directness_score — взвешенная прямота свидетельств
        directness = sum(item.directness for item in self._items) / len(self._items)

        # 5. corroboration_score — количество независимых подтверждений
        corroboration = self._compute_corroboration()

        # Итоговая формула с весами
        strength = (
            source_reliability_avg * 0.25
            + independence         * 0.30
            + recency              * 0.15
            + directness           * 0.20
            + corroboration        * 0.10
        )
        strength = max(0.0, min(1.0, strength))

        return EvidenceResult(
            evidence_strength=round(strength, 4),
            item_count=len(self._items),
            independence_score=round(independence, 4),
            recency_score=round(recency, 4),
            directness_score=round(directness, 4),
            corroboration_score=round(corroboration, 4),
            source_reliability_avg=round(source_reliability_avg, 4),
            note=self._build_note(independence, corroboration),
        )

    # ── Внутренние вычисления ─────────────────────────────────────────────────

    def _compute_independence(self) -> float:
        """
        Насколько источники независимы друг от друга.

        Алгоритм:
        - Группируем по domain (bbc.com, pubmed.ncbi, ...)
        - 5 статей с bbc.com = 1 независимый источник, не 5
        - Результат: unique_domains / total_items (с бонусом за разнообразие)
        """
        if len(self._items) == 1:
            return 0.6  # одно свидетельство — умеренная независимость

        domains = [item.source_domain for item in self._items]
        unique_domains = len(set(domains))
        total = len(domains)

        # Базовый score: доля уникальных доменов
        base = unique_domains / total

        # Бонус за разнообразие типов источников
        types = set(item.source_type for item in self._items)
        type_bonus = min(0.15, len(types) * 0.05)

        # Дедупликация по content_hash
        hashes = [item.content_hash for item in self._items if item.content_hash]
        if len(hashes) > len(set(hashes)):
            # Есть дубликаты — штраф
            duplicate_ratio = 1 - len(set(hashes)) / len(hashes)
            base *= (1 - duplicate_ratio * 0.5)

        return min(1.0, base + type_bonus)

    def _compute_recency(self) -> float:
        """Средняя свежесть доказательств."""
        now = datetime.now(UTC)
        scores = []
        for item in self._items:
            if not item.published_at:
                scores.append(0.5)  # неизвестная дата — нейтрально
                continue
            try:
                # FIX v8.5.1 (ChatGPT/Gemini): нормализация дат
                # datetime.fromisoformat("2024-06-01") → naive datetime
                # Сравнение naive vs aware → TypeError → уходило в 0.5
                # Теперь: date-only строки явно конвертируются в aware datetime
                raw = item.published_at.replace("Z", "+00:00")
                try:
                    pub = datetime.fromisoformat(raw)
                    # Если naive (нет timezone) — добавляем UTC
                    if pub.tzinfo is None:
                        pub = pub.replace(tzinfo=UTC)
                except ValueError:
                    # Попробовать как date-only "2024-06-01"
                    from datetime import date
                    from datetime import time as dt_time
                    d = date.fromisoformat(raw.split("T")[0].split("+")[0])
                    pub = datetime.combine(d, dt_time.min, tzinfo=UTC)
                days_ago = (now - pub).days
                score = math.exp(-0.002 * days_ago)
                scores.append(max(0.1, min(1.0, score)))
            except (ValueError, TypeError, OverflowError):
                scores.append(0.5)
        return sum(scores) / len(scores) if scores else 0.5

    def _compute_corroboration(self) -> float:
        """
        Сила множественного подтверждения.
        Убывающая отдача: первые 3 источника важнее последующих.
        """
        unique_domains = len(set(item.source_domain for item in self._items))
        # Логарифмическая функция: много источников → убывающая отдача
        return min(1.0, math.log(1 + unique_domains) / math.log(1 + 5))

    @staticmethod
    def _build_note(independence: float, corroboration: float) -> str:
        notes = []
        if independence < 0.3:
            notes.append("⚠️ Низкая независимость — источники дублируют друг друга")
        if corroboration < 0.3:
            notes.append("⚠️ Мало независимых подтверждений")
        if not notes:
            notes.append("✅ Evidence quality acceptable")
        return " | ".join(notes)


# ── EvidenceResult ────────────────────────────────────────────────────────────

@dataclass
class EvidenceResult:
    """Результат оценки доказательств."""
    evidence_strength:      float
    item_count:             int
    independence_score:     float
    recency_score:          float
    directness_score:       float
    corroboration_score:    float
    source_reliability_avg: float
    note:                   str = ""

    def to_dict(self) -> dict:
        return {
            "evidence_strength":      self.evidence_strength,
            "item_count":             self.item_count,
            "independence_score":     self.independence_score,
            "recency_score":          self.recency_score,
            "directness_score":       self.directness_score,
            "corroboration_score":    self.corroboration_score,
            "source_reliability_avg": self.source_reliability_avg,
            "note":                   self.note,
        }

    def explain(self) -> str:
        lines = [
            f"📚 Evidence Strength: {self.evidence_strength:.3f}",
            f"   {self.note}",
            "",
            f"   source_reliability  = {self.source_reliability_avg:.3f} × 0.25",
            f"   independence_score  = {self.independence_score:.3f} × 0.30",
            f"   recency_score       = {self.recency_score:.3f} × 0.15",
            f"   directness_score    = {self.directness_score:.3f} × 0.20",
            f"   corroboration_score = {self.corroboration_score:.3f} × 0.10",
            f"   sources: {self.item_count} item(s)",
        ]
        return "\n".join(lines)


# ── Source Authenticity Score (Eywa "evidence before belief") ───────────────────
# A single [0,1] trust score for a source, distinct from per-claim evidence_strength:
#   authenticity = reliability · (1 + verification bonus) · (1 − contradiction penalty)
# Used by TruthGate/truth_policy as an extra weight when a fact carries structured
# EvidenceRefs. Pure function; reuses SOURCE_RELIABILITY. Never raises.

def compute_source_authenticity(
    source_type: str = "unknown",
    *,
    verification_count: int = 0,
    contradiction_rate: float = 0.0,
) -> float:
    """Trust in a SOURCE (not a claim). Returns [0,1].

    - reliability: from SOURCE_RELIABILITY catalogue (default 0.50).
    - verification_count: independent confirmations → diminishing-returns bonus up to +0.25.
    - contradiction_rate: fraction of times this source was contradicted [0,1] → linear penalty.
    """
    from core.confidence import SOURCE_RELIABILITY

    reliability = SOURCE_RELIABILITY.get(source_type, 0.50)
    vc = max(0, int(verification_count))
    verify_bonus = 0.25 * (1.0 - math.exp(-vc / 3.0))      # 0 at 0, →0.25 asymptote
    penalty = max(0.0, min(1.0, float(contradiction_rate)))
    score = reliability * (1.0 + verify_bonus) * (1.0 - penalty)
    return round(max(0.0, min(1.0, score)), 4)


__all__ = [
    "EvidenceItem",
    "EvidenceModel",
    "EvidenceResult",
    "compute_source_authenticity",
]
