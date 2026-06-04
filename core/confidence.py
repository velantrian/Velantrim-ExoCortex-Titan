"""
📐 core/confidence.py — Decomposed Confidence Formula (B1)
==========================================================
Разбивает монолитный confidence на 5 измеримых компонент.

КЛЮЧЕВОЙ ПРИНЦИП:
  retrieval_score ≠ доказательство истины!
  Высокая релевантность не означает что факт правдивый.
  Это разные вещи которые раньше смешивались.

final_confidence = f(
    source_confidence,     — насколько источнику доверяем
    evidence_strength,     — насколько доказательства сильные
    semantic_consistency,  — не противоречит ли другим фактам
    temporal_validity,     — не устарел ли факт
    retrieval_score,       — только как сигнал, не как доказательство
)

Sprint 1b — Этап B1
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# ── Источники и их базовое доверие ───────────────────────────────────────────

SOURCE_RELIABILITY: dict[str, float] = {
    # Peer-reviewed
    "peer_reviewed_paper":   0.90,
    "scientific_journal":    0.88,
    "meta_analysis":         0.92,
    # Официальные источники
    "government_official":   0.85,
    "who_cdc":               0.87,
    "court_document":        0.88,
    # Качественные медиа
    "reuters_ap":            0.80,
    "reputable_news":        0.72,
    # Корпоративные
    "company_official":      0.70,
    "press_release":         0.60,
    # Пользовательский контент
    "wikipedia":             0.65,
    "user_input":            0.55,
    "forum_post":            0.35,
    "anonymous":             0.20,
    # Системные
    "system_inferred":       0.60,
    "llm_extracted":         0.50,
    "atlas_sync":            0.75,
    # По умолчанию
    "unknown":               0.50,
}


# ── ConfidenceComponents ─────────────────────────────────────────────────────

@dataclass
class ConfidenceComponents:
    """
    Явные компоненты уверенности.
    Каждую можно измерить и объяснить независимо.
    """

    # 1. Насколько надёжен источник (справочная таблица + history)
    source_confidence: float = 0.5

    # 2. Сила доказательств (из EvidenceModel)
    evidence_strength: float = 0.5

    # 3. Семантическая согласованность (не противоречит Validated фактам)
    # 1.0 = нет противоречий, 0.0 = прямое противоречие
    semantic_consistency: float = 1.0

    # 4. Временная валидность (свежесть и применимость во времени)
    # 1.0 = актуально сейчас, 0.0 = явно устарело
    temporal_validity: float = 1.0

    # 5. Retrieval score — ТОЛЬКО как мягкий сигнал, НЕ доказательство
    # Влияет с весом 0.05 — едва заметно
    retrieval_score: float = 0.0

    # Метаданные для объяснимости
    source_type:   str = "unknown"
    explanation:   dict = field(default_factory=dict)

    def compute(self) -> ConfidenceResult:
        """
        Вычисляет итоговый confidence по взвешенной формуле.

        Веса:
          source_confidence    × 0.30  — источник важнее всего
          evidence_strength    × 0.30  — доказательства
          semantic_consistency × 0.25  — не противоречит ли
          temporal_validity    × 0.10  — свежесть
          retrieval_score      × 0.05  — едва заметный сигнал

        ИТОГО: 1.00
        """
        weights = {
            "source_confidence":    0.30,
            "evidence_strength":    0.30,
            "semantic_consistency": 0.25,
            "temporal_validity":    0.10,
            "retrieval_score":      0.05,
        }

        raw = (
            self.source_confidence    * weights["source_confidence"]
            + self.evidence_strength    * weights["evidence_strength"]
            + self.semantic_consistency * weights["semantic_consistency"]
            + self.temporal_validity    * weights["temporal_validity"]
            + self.retrieval_score      * weights["retrieval_score"]
        )

        # Ограничиваем [0.0, 1.0]
        final = max(0.0, min(1.0, raw))

        # Penalty за прямое противоречие
        if self.semantic_consistency < 0.3:
            final *= 0.6  # -40% при сильном противоречии
            explanation_note = "⚠️ Reduced: strong semantic contradiction detected"
        elif self.temporal_validity < 0.3:
            final *= 0.8  # -20% при устаревших данных
            explanation_note = "⚠️ Reduced: data appears outdated"
        else:
            explanation_note = "✅ Normal calculation"

        return ConfidenceResult(
            final_confidence=round(final, 4),
            components=self,
            weights=weights,
            note=explanation_note,
        )

    def validate(self) -> list[str]:
        """Проверяет что все компоненты в допустимых диапазонах."""
        errors = []
        for name, value in [
            ("source_confidence",    self.source_confidence),
            ("evidence_strength",    self.evidence_strength),
            ("semantic_consistency", self.semantic_consistency),
            ("temporal_validity",    self.temporal_validity),
            ("retrieval_score",      self.retrieval_score),
        ]:
            if not 0.0 <= value <= 1.0:
                errors.append(f"{name}={value} вне диапазона [0.0, 1.0]")
        return errors


@dataclass
class ConfidenceResult:
    """Результат вычисления confidence с полной объяснимостью."""
    final_confidence: float
    components: ConfidenceComponents
    weights: dict[str, float]
    note: str = ""

    def to_dict(self) -> dict:
        c = self.components
        return {
            "final_confidence":   self.final_confidence,
            "note":               self.note,
            "components": {
                "source_confidence":    {"value": c.source_confidence,    "weight": 0.30,
                                        "contribution": round(c.source_confidence * 0.30, 4)},
                "evidence_strength":    {"value": c.evidence_strength,    "weight": 0.30,
                                        "contribution": round(c.evidence_strength * 0.30, 4)},
                "semantic_consistency": {"value": c.semantic_consistency, "weight": 0.25,
                                        "contribution": round(c.semantic_consistency * 0.25, 4)},
                "temporal_validity":    {"value": c.temporal_validity,    "weight": 0.10,
                                        "contribution": round(c.temporal_validity * 0.10, 4)},
                "retrieval_score":      {"value": c.retrieval_score,      "weight": 0.05,
                                        "contribution": round(c.retrieval_score * 0.05, 4),
                                        "note": "Signal only — NOT evidence of truth"},
            },
            "source_type": c.source_type,
        }

    def explain(self) -> str:
        """Человекочитаемое объяснение confidence."""
        c = self.components
        lines = [
            f"📊 Confidence: {self.final_confidence:.3f}",
            f"   {self.note}",
            "",
            f"   source_confidence    = {c.source_confidence:.2f} × 0.30 = {c.source_confidence * 0.30:.3f}",
            f"   evidence_strength    = {c.evidence_strength:.2f} × 0.30 = {c.evidence_strength * 0.30:.3f}",
            f"   semantic_consistency = {c.semantic_consistency:.2f} × 0.25 = {c.semantic_consistency * 0.25:.3f}",
            f"   temporal_validity    = {c.temporal_validity:.2f} × 0.10 = {c.temporal_validity * 0.10:.3f}",
            f"   retrieval_score      = {c.retrieval_score:.2f} × 0.05 = {c.retrieval_score * 0.05:.3f}",
            "                                               ──────",
            f"   final_confidence                          = {self.final_confidence:.3f}",
        ]
        return "\n".join(lines)


# ── Фабричные методы ──────────────────────────────────────────────────────────

def compute_confidence(
    source_type:          str = "unknown",
    evidence_strength:    float = 0.5,
    semantic_consistency: float = 1.0,
    temporal_validity:    float = 1.0,
    retrieval_score:      float = 0.0,
) -> ConfidenceResult:
    """
    Главная точка входа для вычисления confidence.

    Пример:
        result = compute_confidence(
            source_type="peer_reviewed_paper",
            evidence_strength=0.85,
            semantic_consistency=0.90,
            temporal_validity=0.95,
            retrieval_score=0.77,
        )
        print(result.final_confidence)  # 0.8585
        print(result.explain())
    """
    source_conf = SOURCE_RELIABILITY.get(source_type, 0.50)
    components = ConfidenceComponents(
        source_confidence=source_conf,
        evidence_strength=evidence_strength,
        semantic_consistency=semantic_consistency,
        temporal_validity=temporal_validity,
        retrieval_score=retrieval_score,
        source_type=source_type,
    )
    errors = components.validate()
    if errors:
        raise ValueError(f"ConfidenceComponents invalid: {errors}")
    return components.compute()


def temporal_decay(
    created_days_ago: float,
    domain: str = "general",
) -> float:
    """
    Вычисляет temporal_validity с учётом возраста факта и домена.

    Разные домены стареют по-разному:
        medical:   факты устаревают быстро (6 месяцев → 0.5)
        physics:   почти не стареют (100 лет → 0.9)
        news:      очень быстро (2 недели → 0.5)
        general:   средне (1 год → 0.7)
    """
    # Полупериод полураспада в днях по домену
    # FIX v8.5.2 (Claude audit): physics было 36500 дней (100 лет), но при
    # half_life=100 лет, в возрасте 100 лет decay = e^(-ln(2)) = 0.5 ровно по
    # определению. Это противоречило docstring «100 лет → 0.9» и тесту,
    # который ждёт > 0.5. Расширено до 365000 дней (1000 лет): теперь при
    # 100 годах decay ≈ 0.933, что согласуется с «почти не стареют».
    half_life_days: dict[str, float] = {
        "medical":     180,
        "technology":  365,
        "news":        14,
        "legal":       730,
        "physics":     365000,  # 1000 лет — физические законы стареют веками
        "economics":   180,
        "general":     365,
    }
    hl = half_life_days.get(domain, 365)
    # Экспоненциальный распад: V(t) = e^(-λt) где λ = ln(2)/half_life
    lambd = math.log(2) / hl
    decay = math.exp(-lambd * created_days_ago)
    return round(max(0.1, min(1.0, decay)), 4)
