"""
🧬 core/understanding_layer.py — Understanding Layer (Patch 13 + 14)
====================================================================
= Causal Graph + Living Context = Understanding Layer v9.0.0

Velantrim сейчас: память (факты + ESM)
После Patch 13+14: понимание (факты + причины + практика)

Спек: VARIANT_B_CAUSAL_PLUS_LIVING-1.md
Version: v9.0.0 (Patch 13 + 14 combined)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from core.causal_graph import VALID_RELATION_TYPES, CausalGraph
from core.living_context import LivingContext, LivingContextStore

if TYPE_CHECKING:
    pass

# Все типы из Patch 13 + дополнительные из Living Context
ALL_RELATION_TYPES = list(VALID_RELATION_TYPES) + [
    "becomes",       # трансформация (дерево → дрова)
    "affords",       # прямая affordance связь
    "inhabited_by",  # кто там живёт
]

# Типы в causal summary (FIX: все 12 + 3 дополнительных)
CAUSAL_SUMMARY_TYPES = [
    "causes", "prevents", "requires", "enables",
    "implies", "contradicts", "generalizes", "specializes",
    "precedes", "follows", "composes", "analogous_to",
    "becomes",
]


class UnderstandingLayer:
    """
    Объединяет Causal Graph и Living Context в единый API понимания.

    Входная точка для запросов вида:
      - "Почему это так работает?" → causal
      - "Что с этим можно сделать?" → living
      - "Что будет если изменить?" → predict_intervention
      - "Объясни ребёнку/учёному/инженеру" → for_agent

    FIX (ChatGPT):
      - Inferred relations идут через Truth Gate в PENDING
      - _get_causal_summary покрывает все 12 типов
      - predict_intervention() заменяет what_if() — Pearl Level 2
    """

    def __init__(
        self,
        store,
        causal_graph: CausalGraph,
        living_store: LivingContextStore | None = None,
        linker=None,
    ) -> None:
        self._store = store
        self._causal = causal_graph
        self._living = living_store
        self._linker = linker

    # ── Основной API ──────────────────────────────────────────────────────────

    def understand(self, fact_id: str) -> dict:
        """
        Полное понимание факта: causal + living + joint implications.
        """
        fact = self._store.get_fact(fact_id)
        if not fact:
            return {"error": f"Факт {fact_id} не найден"}

        causal = self._get_causal_summary(fact_id)
        living = (
            self._living.get(fact_id) if self._living else None
        ) or LivingContext()
        implications = self._joint_reasoning(fact_id, causal, living)

        return {
            "fact_id":            fact_id,
            "fact":               fact,
            "causal":             causal,
            "living_context":     living.to_dict() if not living.is_empty() else {},
            "joint_implications": implications,
            "knowledge_summary":  self._causal.knowledge_summary(fact_id),
        }

    def for_agent(
        self,
        fact_id: str,
        agent_type: str = "default",
    ) -> dict:
        """
        Адаптивный ответ для разных агентов.

        agent_type: "child" | "scientist" | "ecologist" | "engineer" | "default"
        """
        full = self.understand(fact_id)
        if "error" in full:
            return full

        living = full.get("living_context", {})
        causal = full.get("causal", {})

        if agent_type == "child":
            return {
                "can_do":     living.get("how", [])[:5],
                "feels_like": list(living.get("feel", {}).keys())[:3],
                "joint":      full["joint_implications"][:2],
            }
        elif agent_type == "scientist":
            return {
                "causes":   causal.get("causes", []),
                "requires": causal.get("requires", []),
                "deep":     living.get("deep"),
                "time":     living.get("time"),
                "knowledge_summary": full["knowledge_summary"],
            }
        elif agent_type == "ecologist":
            return {
                "roles":         living.get("role", []),
                "who_depends":   living.get("who", []),
                "causal_impact": causal.get("enables", []) + causal.get("causes", []),
                "prevents":      causal.get("prevents", []),
            }
        elif agent_type == "engineer":
            return {
                "products": living.get("what", []),
                "how":      living.get("how", []),
                "becomes":  causal.get("becomes", []),
                "requires": causal.get("requires", []),
            }
        return full

    def why(self, fact_id: str) -> dict:
        """Backward causal reasoning: почему это так?"""
        return self._causal.explain(fact_id)

    def predict_intervention(
        self,
        fact_id: str,
        change: str,
    ) -> dict:
        """
        FIX: переименован из what_if() в predict_intervention().
        Pearl Level 2 (интервенция), НЕ Level 3 (контрфактуал).

        Pearl Level 1: ассоциация ("X часто с Y")
        Pearl Level 2: интервенция ("если изменить X → что с Y") ← МЫ ЗДЕСЬ
        Pearl Level 3: контрфактуал — требует SCM с уравнениями   ← НЕ РЕАЛИЗОВАНО
        """
        living = (
            self._living.get(fact_id) if self._living else None
        ) or LivingContext()
        causal_effects = self._causal.propagate_change(fact_id, change)

        return {
            "fact_id":       fact_id,
            "change":        change,
            "pearl_level":   2,
            "causal_chain":  causal_effects,
            "affected_count": len(causal_effects),
            "living_context": living.to_dict() if not living.is_empty() else {},
            "note": (
                "Pearl Level 2 (intervention). "
                "Для полного do-calculus (Level 3) нужна SCM с уравнениями "
                "и вероятностными распределениями."
            ),
        }

    def affordance_to_causal(
        self,
        affordance: str,
        fact_id: str,
    ) -> list[dict]:
        """
        Создать pending каузальные отношения из affordance.

        FIX (ChatGPT): affordances создают PENDING отношения,
        НЕ canonical отношения. Проходят через TruthGate перед принятием.
        """
        if not affordance or not fact_id:
            return []

        inferred_relations: list[dict] = []

        # Слова-маркеры → типы отношений
        type_keywords = {
            "срубить": "enables",
            "рубить":  "enables",
            "cut":     "enables",
            "дрова":   "becomes",
            "wood":    "becomes",
            "тень":    "enables",
            "shadow":  "enables",
            "укрыть":  "enables",
            "shelter": "enables",
            "кислород":"causes",
            "oxygen":  "causes",
        }

        words = affordance.lower().split()
        for word in words:
            rel_type = type_keywords.get(word)
            if rel_type:
                inferred_relations.append({
                    "from_fact_id":    fact_id,
                    "relation_type":   rel_type,
                    "confidence":      0.6,
                    "knowledge_status": "hypothetical",
                    "inference_source": "affordance_inference",
                    # FIX: всегда PENDING — не canonical
                    "truth_status":    "pending",
                    "review_state":    "pending",
                    "source":          "affordance_inference",
                    "note":            f"Inferred from affordance: '{affordance}'",
                })

        return inferred_relations

    # ── Internal ──────────────────────────────────────────────────────────────

    def _get_causal_summary(self, fact_id: str) -> dict:
        """
        FIX (ChatGPT): покрываем ВСЕ типы из CAUSAL_SUMMARY_TYPES.
        В оригинале было только 5 из 12.
        Показываем только validated/approved отношения.
        Pending отдельно для прозрачности.
        """
        summary: dict = {}
        pending: list[dict] = []

        for rel_type in CAUSAL_SUMMARY_TYPES:
            relations = self._causal.get_relations_from(
                fact_id,
                relation_type=rel_type,
            )
            validated = []
            for r in relations:
                status = getattr(r, "truth_status", "validated")
                if status in ("validated", "approved"):
                    validated.append({
                        "to":              r.to_fact_id,
                        "confidence":      r.confidence,
                        "knowledge_status": r.knowledge_status,
                    })
                elif status in ("hypothesis", "pending"):
                    pending.append({
                        "type":            rel_type,
                        "to":              r.to_fact_id,
                        "confidence":      r.confidence,
                        "status":          "pending_review",
                        "inference_source": r.inference_source,
                    })

            if validated:
                summary[rel_type] = validated

        if pending:
            summary["_pending_review"] = pending

        return summary

    def _joint_reasoning(
        self,
        fact_id: str,
        causal: dict,
        living: LivingContext,
    ) -> list[str]:
        """
        Совместный вывод из причинности и живого контекста.
        Шаблонный — для сложных вопросов нужна LLM (Patch 15+).
        """
        implications: list[str] = []

        # affordance "срубить" + causal BECOMES "дрова"
        if living and any(
            "срубить" in a or "рубить" in a or "cut" in a
            for a in living.affordances
        ):
            becomes = causal.get("becomes", [])
            for b in becomes[:2]:
                implications.append(f"Срубить → {b.get('to', 'ресурс')}")

        # Causal ENABLES → добавить в affordances
        for e in causal.get("enables", [])[:3]:
            impl = f"Делает возможным: {e.get('to', '?')}"
            if impl not in implications:
                implications.append(impl)

        # Кто REQUIRES этот факт
        requires_me = self._causal.get_relations_to(fact_id, relation_type="requires")
        for r in requires_me[:2]:
            implications.append(f"Без этого невозможно: {r.from_fact_id}")

        # Causal PREVENTS + living agents
        prevents = causal.get("prevents", [])
        if living.agents and prevents:
            agent_names = [a.entity for a in living.agents[:2]]
            implications.append(
                f"Защищает: {', '.join(agent_names)} зависят от этого"
            )

        # TIME: быстрое/медленное
        if living.time and living.time.duration:
            causes = causal.get("causes", [])
            if causes:
                implications.append(
                    f"Медленный процесс ({living.time.duration}): "
                    f"причины → {causes[0].get('to', '?')}"
                )

        # DEEP: химические реакции + causes
        if living.deep:
            causes = causal.get("causes", [])
            if causes:
                implications.append(
                    f"Механизм: {living.deep[:60]}..."
                    if len(living.deep) > 60 else f"Механизм: {living.deep}"
                )

        # Дедупликация
        return list(dict.fromkeys(implications))
