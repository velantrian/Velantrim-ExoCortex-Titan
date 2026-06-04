"""
⚖️ core/contradiction_resolver.py — разрешение противоречий (P0.2)
==================================================================

Цель: ловить «новое противоречит старому» и разрешать, чтобы память не «гнила»
(не таскала одновременно «дерево подходит» и «дерево не подходит»).

P0 (детерминированно, без LLM):
  • СУБЪЕКТ = нормализованный claim с УБРАННЫМ отрицанием → «дерево подходит» и
    «дерево не подходит» дают один субъект-ключ;
  • ПОЛЯРНОСТЬ (+/−) считается на ИСХОДНОМ claim (по negation-маркерам);
  • один субъект + ПРОТИВОПОЛОЖНАЯ полярность = противоречие;
  • более НОВЫЙ факт (по t_ingestion / порядку) — текущее убеждение, вытесняет старый.

Разрешение (matrix-safe, no-DELETE, Truth Gate не обходим):
  • старый факт `Validated` → `Contradicted` (единственный легальный переход по матрице ESM);
  • старый факт не-Validated → НЕ форсим состояние, помечаем `requires_review` + ребро `superseded_by`;
  • ничего не удаляем; намерения пользователя в FACT не превращаем.

Полный семантический NLI («встреча в пн» vs «во вт» — без отрицания) — P1, нужен LLM.
Аддитивно, за флагом `ENABLE_CONTRADICTION_RESOLVER` (по умолчанию ВЫКЛ).
"""
from __future__ import annotations

import os
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

# Маркеры отрицания → полярность (ru + en).
_NEG_RE = re.compile(
    r"(?:\bне\b|\bнет\b|\bнель[зз]я\b|\bбез\b|больше не|уже не|отказ|"
    r"\bnot\b|\bno\b|\bnever\b|\bwithout\b|n't|\bcannot\b|no longer)",
    re.IGNORECASE,
)
# Слова-отрицания, которые убираем при вычислении субъект-ключа.
_NEG_TOKENS = {"не", "нет", "нельзя", "без", "not", "no", "never", "without", "cannot", "n't"}


def is_contradiction_resolver_enabled() -> bool:
    return os.getenv("ENABLE_CONTRADICTION_RESOLVER", "false").strip().lower() in {"1", "true", "yes", "on"}


def _normalize(claim: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (claim or "").lower())).strip()


def _subject_key(claim: str) -> str:
    """Субъект = нормализованный claim без слов-отрицаний (чтобы «X» и «не X» совпали)."""
    return " ".join(t for t in _normalize(claim).split() if t not in _NEG_TOKENS)


def _polarity(claim: str) -> int:
    return -1 if _NEG_RE.search(claim or "") else 1


def _recency(fact: dict[str, Any], index: int) -> tuple:
    """Ключ новизны: (t_ingestion_start ISO | '', порядковый индекс). Больше = новее."""
    return (str(fact.get("t_ingestion_start", "") or ""), index)


# Ранг эпистемического состояния + доверенные источники для выбора победителя.
_STATE_RANK = {
    "Observed": 0, "Hypothesized": 1, "Supported": 2, "Validated": 3,
    "ImmutableCore": 4, "Contradicted": -1, "Collapsed": -2, "Deprecated": -1,
}
_TRUSTED_SOURCES = {"ring_zero", "domain_seed", "system_axiom"}


def _belief_strength(fact: dict[str, Any], index: int) -> tuple:
    """Сила убеждения для выбора победителя (trust-aware — фикс H2/M3).

    Победитель = сильнейший по (epistemic_state, trust, confidence), и лишь при
    равенстве — по новизне. Так Validated/доверенный факт НЕ проигрывает более
    новому, но менее достоверному (раньше выбор шёл ТОЛЬКО по recency → новый
    low-trust демотировал старый Validated).
    """
    state = str(fact.get("epistemic_state", "Observed"))
    src = str(fact.get("source", "")).strip().lower()
    trust = 2 if src in _TRUSTED_SOURCES else (1 if src and src != "unknown" else 0)
    try:
        conf = float(fact.get("confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    return (_STATE_RANK.get(state, 0), trust, conf, _recency(fact, index))


@dataclass
class Contradiction:
    older_id: str
    newer_id: str
    subject: str
    relation_type: str = "superseded_by"   # older --superseded_by--> newer
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "older_id": self.older_id,
            "newer_id": self.newer_id,
            "subject": self.subject,
            "relation_type": self.relation_type,
            "reason": self.reason,
        }


def detect_contradictions(facts: Sequence[dict[str, Any]]) -> list[Contradiction]:
    """
    Найти противоречия: один субъект + противоположная полярность. В каждой группе самый
    НОВЫЙ факт = текущее убеждение; противоположно-полярные старые → superseded_by → newest.
    Чистая функция, без мутаций.
    """
    groups: dict[str, list[int]] = {}
    for i, f in enumerate(facts):
        key = _subject_key(f.get("claim", ""))
        if key:
            groups.setdefault(key, []).append(i)

    out: list[Contradiction] = []
    for key, idxs in groups.items():
        if len(idxs) < 2:
            continue
        pol = {i: _polarity(facts[i].get("claim", "")) for i in idxs}
        if len({pol[i] for i in idxs}) < 2:
            continue  # все одной полярности → это корроборация, не противоречие
        # Победитель — сильнейший по убеждению (trust-aware), а не просто самый новый.
        winner = max(idxs, key=lambda i: _belief_strength(facts[i], i))
        for i in idxs:
            if i == winner or pol[i] == pol[winner]:
                continue
            out.append(Contradiction(
                older_id=str(facts[i].get("fact_id", "")),       # проигравший (слабее)
                newer_id=str(facts[winner].get("fact_id", "")),  # победитель (сильнее)
                subject=key,
                reason=(f"opposite polarity on subject «{key}»: "
                        f"{'+' if pol[i] > 0 else '−'} (loser) vs "
                        f"{'+' if pol[winner] > 0 else '−'} (winner, trust-aware)"),
            ))
    return out


@dataclass
class ResolutionReport:
    detected: int = 0
    demoted: int = 0            # Validated → Contradicted
    flagged_review: int = 0     # не-Validated → requires_review (без форс-перехода)
    edges: list[dict[str, Any]] = field(default_factory=list)
    errors: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "demoted": self.demoted,
            "flagged_review": self.flagged_review,
            "edges": list(self.edges),
            "errors": self.errors,
        }


def resolve_contradictions(store: Any) -> ResolutionReport:
    """
    Применить разрешение к стору (matrix-safe). Только `Validated` старый факт переводится
    в `Contradicted` через `transition_esm`; иначе — `requires_review` без форс-перехода.
    Всегда добавляет ребро `superseded_by` (older→newer). Ничего не удаляет.
    """
    report = ResolutionReport()
    try:
        facts = store.get_all_facts()
    except Exception:  # noqa: BLE001
        return report

    contradictions = detect_contradictions(facts)
    report.detected = len(contradictions)

    for c in contradictions:
        report.edges.append({
            "source_id": c.older_id, "target_id": c.newer_id,
            "relation_type": c.relation_type, "knowledge_status": "inferred",
        })
        try:
            older = store.get_fact(c.older_id)
        except Exception:  # noqa: BLE001
            older = None
        if not older:
            continue
        if older.get("epistemic_state") == "Validated":
            try:
                if store.transition_esm(c.older_id, "Contradicted", by="contradiction_resolver"):
                    report.demoted += 1
            except Exception:  # noqa: BLE001
                report.errors += 1
        else:
            report.flagged_review += 1  # не-Validated: матрица не пускает в Contradicted напрямую
    return report


__all__ = [
    "Contradiction",
    "ResolutionReport",
    "detect_contradictions",
    "resolve_contradictions",
    "is_contradiction_resolver_enabled",
]
