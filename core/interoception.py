"""
Innenwelt MVP — интероцепция: somatic_marker в metadata фактов.

Нормализует телесные маркеры и при ENABLE_L6_WELFARE передаёт сигнал в WelfareMonitor.
"""

from __future__ import annotations

import re
from typing import Any

_VALID_MARKERS = frozenset(
    {"neutral", "curiosity", "anxiety", "discomfort", "urgency", "relief"}
)
_MARKER_ALIASES = {
    "тревога": "anxiety",
    "тревожность": "anxiety",
    "дискомфорт": "discomfort",
    "срочность": "urgency",
    "интерес": "curiosity",
}

_DISTRESS_BY_MARKER = {
    "neutral": 0.0,
    "curiosity": 0.05,
    "relief": 0.0,
    "anxiety": 0.55,
    "discomfort": 0.65,
    "urgency": 0.45,
}

_WS = re.compile(r"\s+")


def normalize_somatic_marker(raw: Any) -> str | None:
    """Привести маркер к каноническому имени или None."""
    if raw is None:
        return None
    s = _WS.sub(" ", str(raw).strip().lower())
    if not s:
        return None
    if s in _VALID_MARKERS:
        return s
    if s in _MARKER_ALIASES:
        return _MARKER_ALIASES[s]
    return None


def somatic_distress(marker: str, *, intensity: float | None = None) -> float:
    """Оценка дистресса 0..1 по маркеру и опциональной интенсивности."""
    base = _DISTRESS_BY_MARKER.get(marker, 0.2)
    if intensity is None:
        return base
    try:
        i = max(0.0, min(1.0, float(intensity)))
    except (TypeError, ValueError):
        i = 0.5
    return min(1.0, base * (0.5 + 0.5 * i))


def attach_somatic_metadata(
    metadata: dict[str, Any] | None,
) -> tuple[dict[str, Any], str | None]:
    """
    Если в metadata есть somatic_marker / somatic_intensity — нормализовать.

    Возвращает (обновлённый metadata, канонический маркер или None).
    """
    meta = dict(metadata or {})
    raw = meta.pop("somatic_marker", None)
    if raw is None:
        raw = meta.get("somatic_marker")
    if raw is None:
        return meta, None

    marker = normalize_somatic_marker(raw)
    if not marker:
        return meta, None

    intensity = meta.pop("somatic_intensity", None)
    meta["somatic_marker"] = marker
    if intensity is not None:
        try:
            meta["somatic_intensity"] = max(0.0, min(1.0, float(intensity)))
        except (TypeError, ValueError):
            pass
    meta["somatic_distress"] = round(
        somatic_distress(marker, intensity=meta.get("somatic_intensity")),
        3,
    )
    return meta, marker


def notify_somatic(
    marker: str,
    *,
    user_id: str = "default",
    distress: float | None = None,
    source: str = "fact_ingest",
) -> None:
    """Записать соматический сигнал в L6 welfare (если включён)."""
    from core.runtime_flags import is_l6_welfare_enabled

    if not is_l6_welfare_enabled():
        return
    d = distress if distress is not None else somatic_distress(marker)
    if d < 0.2:
        return
    from core.welfare_monitor import get_welfare_monitor

    get_welfare_monitor(user_id).record(
        "somatic",
        meta={"marker": marker, "distress": d, "source": source},
    )


__all__ = [
    "attach_somatic_metadata",
    "normalize_somatic_marker",
    "notify_somatic",
    "somatic_distress",
]


# ─── V8.7 Titan: PAD-модель эмоций (непрерывное трёхмерное пространство) ────

import math as _math
from dataclasses import dataclass as _dataclass

@_dataclass
class PADState:
    """Valence-Arousal-Dominance: непрерывное эмоциональное пространство."""
    valence: float = 0.5
    arousal: float = 0.5
    dominance: float = 0.5

    @property
    def distress(self) -> float:
        return max(0.0, min(1.0, (1.0 - self.valence) * 0.5 + self.arousal * 0.3 + (1.0 - self.dominance) * 0.2))

    @property
    def is_crisis(self) -> bool:
        return self.valence < 0.3 and self.arousal > 0.7

    @property
    def is_overloaded(self) -> bool:
        return self.distress > 0.75

    @property
    def marker(self) -> str:
        if self.is_crisis: return "anxiety"
        if self.distress > 0.5: return "discomfort"
        if self.arousal < 0.3 and self.valence < 0.4: return "neutral"
        if self.arousal > 0.6 and self.valence > 0.5: return "curiosity"
        if self.valence > 0.6 and self.arousal < 0.4: return "relief"
        return "neutral"

    def to_dict(self):
        return {"valence": round(self.valence, 3), "arousal": round(self.arousal, 3), "dominance": round(self.dominance, 3), "distress": round(self.distress, 3)}

    def distance(self, other):
        return _math.sqrt((self.valence - other.valence)**2 + (self.arousal - other.arousal)**2 + (self.dominance - other.dominance)**2)


def pad_from_marker(marker: str, intensity: float = 0.5):
    mapping = {"neutral": PADState(0.5, 0.5, 0.5), "curiosity": PADState(0.6, 0.55, 0.6), "anxiety": PADState(0.25, 0.75, 0.3), "discomfort": PADState(0.3, 0.6, 0.35), "urgency": PADState(0.4, 0.7, 0.4), "relief": PADState(0.7, 0.35, 0.55)}
    return mapping.get(marker, PADState())


def detect_pad_from_text(text: str):
    if not text or not text.strip():
        return None
    t = text.lower()
    vp = sum(1 for w in ["excellent", "great", "love", "happy", "amazing", "wonderful", "excellent"] if w in t)
    vn = sum(1 for w in ["terrible", "hate", "awful", "bad", "horrible", "infuriates"] if w in t)
    valence = max(0.1, min(0.9, 0.5 + (vp - vn) * 0.15))
    ah = t.count("!") + sum(1 for w in ["urgent", "critical", "now", "fast", "fix it"] if w in t)
    al = sum(1 for w in ["calm", "slow", "easy"] if w in t)
    arousal = max(0.1, min(0.9, 0.5 + (ah - al) * 0.12))
    dp = sum(1 for w in ["create", "write", "find", "show", "explain", "fix", "make"] if w in t)
    dn = t.count("?") * 0.5 + sum(1 for w in ["help", "unsure", "maybe", "possibly"] if w in t)
    dominance = max(0.1, min(0.9, 0.5 + (dp - dn) * 0.1))
    return PADState(valence=valence, arousal=arousal, dominance=dominance)
