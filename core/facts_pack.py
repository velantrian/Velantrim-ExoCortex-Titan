"""
🤖 core/facts_pack.py — FactsPack для LLM (G1)
================================================
Структурированный контейнер фактов который идёт к LLM вместо сырого текста.

Закрывает класс багов: "LLM использовал Contradicted факт и ответил на нём".

Принцип: LLM должен видеть явно:
  - какие факты Validated (можно использовать)
  - какие Contradicted/Collapsed (нельзя использовать)
  - какие Hypothesized (использовать с маркировкой)
  - почему что-то исключено (чтобы не "угадывал")

Sprint 1a — Этап G1
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

# ── Политики ответа по CognitiveMode ─────────────────────────────────────────

COGNITIVE_MODE_POLICIES: dict[str, dict] = {
    "PRECISION": {
        "allowed_states": ["Validated", "ImmutableCore"],
        "require_min_confidence": 0.75,
        "allow_hypotheses": False,
        "mark_uncertainty": True,
        "description": "Only verified facts. No hypotheses.",
    },
    "BALANCED": {
        "allowed_states": ["Validated", "ImmutableCore", "Supported"],
        "require_min_confidence": 0.55,
        "allow_hypotheses": False,
        "mark_uncertainty": True,
        "description": "Verified + supported facts with confidence markers.",
    },
    "EXPLORATION": {
        "allowed_states": ["Validated", "ImmutableCore", "Supported", "Hypothesized"],
        "require_min_confidence": 0.35,
        "allow_hypotheses": True,
        "mark_uncertainty": True,
        "description": "Can include hypotheses — must be clearly marked.",
    },
    "CREATIVE": {
        "allowed_states": ["Validated", "ImmutableCore", "Supported",
                           "Hypothesized", "Observed"],
        "require_min_confidence": 0.20,
        "allow_hypotheses": True,
        "mark_uncertainty": True,
        "description": "Maximum flexibility. All facts must be marked by status.",
    },
}

# Состояния которые НИКОГДА не попадают к LLM независимо от режима
ALWAYS_EXCLUDED_STATES = frozenset({"Contradicted", "Collapsed", "Deprecated"})


# ── PackedFact ────────────────────────────────────────────────────────────────

@dataclass
class PackedFact:
    """Один факт внутри FactsPack — с полным контекстом для LLM."""
    fact_id:              str
    claim:                str
    epistemic_state:      str
    confidence:           float
    source:               str
    retrieval_score:      float = 0.0
    context_applicability: float = 1.0   # насколько применим к текущему запросу
    causal_summary:       dict | None = None   # связи из Causal Graph
    living_context:       dict | None = None   # Living Context если есть

    def to_llm_dict(self, include_metadata: bool = True) -> dict:
        """Формат для подачи в LLM."""
        d: dict = {
            "fact_id":         self.fact_id,
            "claim":           self.claim,
            "status":          self.epistemic_state,
            "confidence":      self.confidence,
        }
        if include_metadata:
            d["source"] = self.source
            d["retrieval_score"] = self.retrieval_score
            d["context_applicability"] = self.context_applicability
            if self.causal_summary:
                d["causal_context"] = self.causal_summary
            if self.living_context:
                d["living_context"] = self.living_context
        return d


@dataclass
class ExcludedFact:
    """Факт исключённый из ответа — LLM видит почему."""
    fact_id:   str
    claim:     str                # краткое превью для объяснения
    reason:    str                # "Contradicted", "Below confidence threshold", etc.
    state:     str

    def to_dict(self) -> dict:
        return {
            "fact_id": self.fact_id,
            "claim_preview": self.claim[:80] + "..." if len(self.claim) > 80 else self.claim,
            "reason": self.reason,
            "state": self.state,
        }


# ── FactsPack ─────────────────────────────────────────────────────────────────

@dataclass
class FactsPack:
    """
    Структурированный пакет фактов для LLM.

    Вместо сырого текста — явная структура с метаданными.
    LLM видит: что включено, что исключено, почему, в каком режиме.

    FactsPack гарантирует:
    1. Contradicted/Collapsed факты никогда не попадают к LLM
    2. Hypothesized факты помечены как "не верифицировано"
    3. Каждый claim связан с fact_id для цитирования
    4. retrieval_score явно отделён от confidence
    """
    query:          str
    mode:           str
    facts:          list[PackedFact] = field(default_factory=list)
    excluded_facts: list[ExcludedFact] = field(default_factory=list)
    created_at:     str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    policy:         dict = field(default_factory=dict)

    # Флаг: нашли ли мы вообще что-то полезное
    has_useful_facts: bool = False
    warning:          str | None = None

    def to_dict(self) -> dict:
        """Полная сериализация для LLM."""
        return {
            "query":       self.query,
            "mode":        self.mode,
            "policy":      self.policy,
            "facts":       [f.to_llm_dict() for f in self.facts],
            "excluded_facts": [e.to_dict() for e in self.excluded_facts],
            "meta": {
                "total_facts_found":    len(self.facts) + len(self.excluded_facts),
                "facts_included":       len(self.facts),
                "facts_excluded":       len(self.excluded_facts),
                "has_useful_facts":     self.has_useful_facts,
                "created_at":           self.created_at,
            },
            "warning": self.warning,
        }

    def to_llm_prompt_section(self) -> str:
        """
        Формирует текстовую секцию для промпта LLM.
        Явно разделяет подтверждённые и исключённые факты.
        """
        lines = [
            f"=== VELANTRIM FACTS PACK (mode: {self.mode}) ===",
            "",
        ]

        if not self.facts:
            lines.append("⚠️ No verified facts found for this query.")
        else:
            lines.append("📋 VERIFIED FACTS (use these in your answer):")
            for i, fact in enumerate(self.facts, 1):
                state_marker = {
                    "ImmutableCore": "🔒",
                    "Validated":     "✅",
                    "Supported":     "🟡",
                    "Hypothesized":  "❓",
                    "Observed":      "👁️",
                }.get(fact.epistemic_state, "")
                lines.append(
                    f"  [{i}] {state_marker} [{fact.fact_id}] {fact.claim}"
                )
                lines.append(
                    f"       confidence={fact.confidence:.3f} | "
                    f"status={fact.epistemic_state} | "
                    f"source={fact.source}"
                )
                if fact.epistemic_state == "Hypothesized":
                    lines.append(
                        "       ⚠️ UNVERIFIED HYPOTHESIS — mark as such in answer"
                    )

        if self.excluded_facts:
            lines.append("")
            lines.append("🚫 EXCLUDED FACTS (do NOT use these):")
            for exc in self.excluded_facts:
                lines.append(
                    f"  - [{exc.fact_id}] {exc.reason}: "
                    f'"{exc.claim[:60]}..."'
                )

        lines.append("")
        lines.append(
            "INSTRUCTION: Base your answer ONLY on the verified facts above. "
            "Do not use excluded facts. "
            "Cite facts by their fact_id in brackets, e.g., [f_quantum_001]."
        )
        lines.append("=== END OF FACTS PACK ===")

        return "\n".join(lines)

    def citation_map(self) -> dict[str, str]:
        """Карта fact_id → claim для проверки цитат в ответе."""
        return {f.fact_id: f.claim for f in self.facts}


# ── FactsPackBuilder ──────────────────────────────────────────────────────────

class FactsPackBuilder:
    """
    Строит FactsPack из сырых фактов из памяти.

    Применяет политики CognitiveMode:
    - фильтрует по allowed_states
    - фильтрует по min_confidence
    - всегда исключает Contradicted/Collapsed/Deprecated
    """

    def __init__(self, mode: str = "BALANCED") -> None:
        if mode not in COGNITIVE_MODE_POLICIES:
            raise ValueError(
                f"Unknown mode: {mode!r}. "
                f"Available: {list(COGNITIVE_MODE_POLICIES.keys())}"
            )
        self.mode = mode
        self.policy = COGNITIVE_MODE_POLICIES[mode]
        self._candidates: list[dict] = []

    def add_facts(self, facts: list[dict]) -> FactsPackBuilder:
        """Добавить кандидаты-факты из retrieval."""
        self._candidates.extend(facts)
        return self

    @staticmethod
    def _dedup_semantic(facts: list[PackedFact]) -> list[PackedFact]:
        """
        V8.8: Семантическая дедупликация — удалить факты с почти идентичным смыслом.

        Алгоритм: pairwise Jaccard-сходство по токенам claim.
        Если два факта имеют >70% общих токенов — оставляем с большим confidence.
        Без LLM, без эмбеддингов — чистая токен-математика.
        """
        if len(facts) <= 1:
            return facts

        # Токенизировать все claims
        tokenized = []
        for f in facts:
            tokens = frozenset(f.claim.lower().split())
            tokenized.append(tokens)

        keep: list[bool] = [True] * len(facts)
        for i in range(len(facts)):
            if not keep[i]:
                continue
            for j in range(i + 1, len(facts)):
                if not keep[j]:
                    continue
                # Jaccard similarity
                a, b = tokenized[i], tokenized[j]
                if not a or not b:
                    continue
                overlap = len(a & b) / min(len(a), len(b))
                if overlap > 0.7:
                    # Оставить с большим confidence
                    if facts[j].confidence > facts[i].confidence:
                        keep[i] = False
                    else:
                        keep[j] = False

        return [f for f, k in zip(facts, keep) if k]

    def build(self, query: str) -> FactsPack:
        """
        Применить политики и построить FactsPack.

        Args:
            query: оригинальный запрос пользователя

        Returns:
            FactsPack готовый к подаче в LLM
        """
        allowed_states = set(self.policy["allowed_states"])
        min_conf = self.policy["require_min_confidence"]

        included: list[PackedFact] = []
        excluded: list[ExcludedFact] = []

        for fact in self._candidates:
            state = fact.get("epistemic_state", "Observed")
            conf = float(fact.get("confidence", 0.0))
            fact_id = fact.get("fact_id", "unknown")
            claim = fact.get("claim", "")
            source = fact.get("source", "unknown")

            # Проверка 1: всегда исключаемые состояния
            if state in ALWAYS_EXCLUDED_STATES:
                excluded.append(ExcludedFact(
                    fact_id=fact_id,
                    claim=claim,
                    reason=f"State is {state} — permanently excluded",
                    state=state,
                ))
                continue

            # Проверка 2: разрешено ли состояние в текущем режиме
            if state not in allowed_states:
                excluded.append(ExcludedFact(
                    fact_id=fact_id,
                    claim=claim,
                    reason=f"State '{state}' not allowed in {self.mode} mode",
                    state=state,
                ))
                continue

            # Проверка 3: минимальный confidence
            if conf < min_conf:
                excluded.append(ExcludedFact(
                    fact_id=fact_id,
                    claim=claim,
                    reason=f"Confidence {conf:.3f} < {min_conf} (mode threshold)",
                    state=state,
                ))
                continue

            # Прошло все фильтры
            included.append(PackedFact(
                fact_id=fact_id,
                claim=claim,
                epistemic_state=state,
                confidence=conf,
                source=source,
                retrieval_score=float(fact.get("retrieval_score", 0.0)),
                context_applicability=float(fact.get("context_applicability", 1.0)),
                causal_summary=fact.get("causal_summary"),
                living_context=fact.get("living_context"),
            ))

        # V8.8: Семантическая дедупликация — удалить дубликаты по смыслу
        # перед отправкой LLM. Экономия token budget + качество ответа.
        included = self._dedup_semantic(included)

        # Сортируем по confidence × retrieval_score DESC
        included.sort(key=lambda f: -(f.confidence * max(f.retrieval_score, 0.01)))

        # Предупреждение если нашли что-то плохое
        warning = None
        if not included and excluded:
            warning = (
                f"⚠️ All {len(excluded)} found facts were excluded "
                f"by {self.mode} policy. Consider using EXPLORATION mode."
            )
        elif any(f.epistemic_state == "Hypothesized" for f in included):
            warning = "⚠️ Some facts are unverified hypotheses — mark clearly in answer."

        return FactsPack(
            query=query,
            mode=self.mode,
            facts=included,
            excluded_facts=excluded,
            policy=self.policy,
            has_useful_facts=bool(included),
            warning=warning,
        )


# ── CitationVerifier ──────────────────────────────────────────────────────────

class CitationVerifier:
    """
    Проверяет что LLM-ответ цитирует только факты из FactsPack.

    G3 — Citation Discipline:
    Каждый claim → fact_id → source → trace
    """

    def __init__(self, pack: FactsPack) -> None:
        self._pack = pack
        self._valid_ids = {f.fact_id for f in pack.facts}
        self._excluded_ids = {e.fact_id for e in pack.excluded_facts}

    def verify_answer(self, llm_answer: str) -> dict:
        """
        Проверяет ответ LLM на корректность цитирования.

        Ищет [fact_id] паттерны в тексте ответа.
        """
        import re
        cited_ids = set(re.findall(r'\[([a-zA-Z0-9_\-]+)\]', llm_answer))

        invalid_citations = []
        excluded_citations = []
        valid_citations = []

        for fid in cited_ids:
            if fid in self._valid_ids:
                valid_citations.append(fid)
            elif fid in self._excluded_ids:
                excluded_citations.append(fid)
                # Это серьёзная проблема — LLM использовал исключённый факт!
            else:
                invalid_citations.append(fid)

        is_valid = not excluded_citations and not invalid_citations

        return {
            "is_valid":           is_valid,
            "valid_citations":    valid_citations,
            "invalid_citations":  invalid_citations,
            "excluded_citations": excluded_citations,
            "warning": (
                f"🚨 LLM cited EXCLUDED facts: {excluded_citations}"
                if excluded_citations else None
            ),
        }
