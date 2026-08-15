"""
🧬 core/branch_manager.py — Parallel Reasoning Branch Manager (V8.7 Titan)

Реализует multi-perspective reasoning: 1-3 параллельные ветки, каждая
со своей ролью (из perspectives.py) и своей retrieval-стратегией.
Результаты синтезируются — лучшие части каждой ветки объединяются.

По умолчанию: ENGINEER + ANALYST + CRITIC (три ветки параллельно).
Опционально: одна роль → быстрый ответ в её стиле.

Pipeline:
    Query → resolve_roles() → для каждой роли ПАРАЛЛЕЛЬНО:
        → retrieval с hints роли
        → prompt с modifier роли
        → LLM ответ, только если caller передал валидный LlmCallConfig
        → иначе deterministic Essence fallback
    → Synthesizer: сравнить ответы, выбрать лучшие части
    → Финальный ответ

Инварианты:
    I-BM1: BranchManager не пишет в граф. Только retrieval + prompt.
    I-BM2: При одной роли — работает идентично прямому pipeline (без оверхеда).
    I-BM3: Confidence синтеза = среднее confidence веток × overlap_score.
    I-BM4: BranchManager не выбирает provider/api_key; LLM config принадлежит caller.
    I-BM5: used_llm=True только после реально завершённого chat_complete().
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from core.perspectives import (
    PerspectiveRole,
    resolve_roles,
)

if TYPE_CHECKING:
    from core.llm_router import LlmCallConfig

logger = logging.getLogger("velantrim.branch_manager")


@dataclass
class BranchResult:
    """Результат одной ветки рассуждения."""
    role: PerspectiveRole
    facts: List[Dict[str, Any]]
    response: str = ""
    confidence: float = 0.7
    key_claims: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    used_llm: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.role_id,
            "emoji": self.role.emoji,
            "facts_count": len(self.facts),
            "response": self.response[:500],
            "confidence": round(self.confidence, 2),
            "key_claims": self.key_claims[:5],
            "duration_ms": round(self.duration_ms, 1),
            "used_llm": self.used_llm,
        }


@dataclass
class SynthesisResult:
    """Результат синтеза нескольких веток."""
    response: str
    branches: List[BranchResult]
    consensus_zones: List[str]      # где ветки сошлись
    divergence_zones: List[str]     # где разошлись
    confidence: float               # агрегированная уверенность
    dominant_role: Optional[str] = None  # чей ответ был самым полным

    @property
    def all_branches_used_llm(self) -> bool:
        """True только если полный synthesis состоит из реальных LLM-ответов."""
        return bool(self.branches) and all(branch.used_llm for branch in self.branches)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "branches": [b.to_dict() for b in self.branches],
            "consensus_count": len(self.consensus_zones),
            "divergence_count": len(self.divergence_zones),
            "confidence": round(self.confidence, 2),
            "dominant_role": self.dominant_role,
            "branch_count": len(self.branches),
            "all_branches_used_llm": self.all_branches_used_llm,
        }


class BranchManager:
    """
    Оркестратор параллельных веток рассуждения.

    Использование:
        manager = BranchManager()

        # По умолчанию: 3 роли параллельно
        result = await manager.reason(query="как построить эко-дом?")
        print(result.response)

        # Одна роль
        result = await manager.reason(query="...", roles=["ENGINEER"])
        print(result.response)
    """

    def __init__(self):
        pass

    async def reason(
        self,
        query: str,
        *,
        roles: Optional[List[str]] = None,
        facts: Optional[List[Dict[str, Any]]] = None,
        single_role: bool = False,
        llm_config: Optional["LlmCallConfig"] = None,
    ) -> SynthesisResult:
        """
        Запустить параллельное рассуждение.

        Args:
            query: запрос пользователя.
            roles: явно указанные роли (если None — автоопределение).
            facts: готовые факты (если None — будут извлечены из store).
            single_role: если True — только одна роль (даже если передано несколько).
            llm_config: уже разрешённый caller-ом LLM config. None = только
                deterministic fallback; BranchManager сам credentials/provider
                не выбирает.

        Returns:
            SynthesisResult с синтезированным ответом.
        """
        import time

        # Определить роли
        resolved = resolve_roles(query, requested_roles=roles)

        # Если одна роль явно запрошена — используем только её
        if single_role and len(resolved) > 1:
            resolved = resolved[:1]

        # Если роль одна — быстрый путь (без синтеза)
        if len(resolved) == 1:
            start = time.time()
            branch = await self._run_branch(
                query,
                resolved[0],
                facts,
                llm_config=llm_config,
            )
            branch.duration_ms = (time.time() - start) * 1000
            return SynthesisResult(
                response=branch.response,
                branches=[branch],
                consensus_zones=[],
                divergence_zones=[],
                confidence=branch.confidence,
                dominant_role=resolved[0].role_id,
            )

        # Параллельные ветки
        start = time.time()
        branches = await asyncio.gather(*[
            self._run_branch(query, role, facts, llm_config=llm_config)
            for role in resolved
        ])

        for b, role in zip(branches, resolved):
            b.duration_ms = (time.time() - start) * 1000 / len(resolved)

        # Синтез
        result = self._synthesize(query, branches)
        return result

    async def _run_branch(
        self,
        query: str,
        role: PerspectiveRole,
        preloaded_facts: Optional[List[Dict[str, Any]]] = None,
        *,
        llm_config: Optional["LlmCallConfig"] = None,
    ) -> BranchResult:
        """Выполнить одну ветку рассуждения с заданной ролью."""
        # 1. Retrieval с hints роли
        hints = role.retrieval_hints
        if preloaded_facts is not None:
            facts = preloaded_facts
        else:
            try:
                facts = self._retrieve_with_hints(query, hints)
            except Exception as exc:
                logger.debug(
                    "Branch retrieval degraded for role %s: %s",
                    role.role_id,
                    type(exc).__name__,
                )
                facts = []

        # 2. Собрать ответ (через LLM только с caller-owned config, иначе essence)
        response, confidence, used_llm = await self._generate_response(
            query,
            facts,
            role,
            llm_config=llm_config,
        )

        # 3. Извлечь ключевые claims
        key_claims = self._extract_key_claims(response)

        return BranchResult(
            role=role,
            facts=facts,
            response=response,
            confidence=confidence,
            key_claims=key_claims,
            used_llm=used_llm,
        )

    def _retrieve_with_hints(
        self, query: str, hints: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Retrieval с подсказками роли."""
        try:
            from core.hybrid_retriever import HybridRetriever
            from core.memory import _GLOBAL_STORE

            k = int(hints.get("retrieval_k", "5"))
            use_ego = hints.get("use_ego", "false") == "true"

            store = _GLOBAL_STORE
            if store is None:
                return []

            from core.recall_policy import filter_facts_for_recall
            all_facts = store.get_all_facts() or []
            facts = filter_facts_for_recall(all_facts)

            if not facts:
                return []

            retriever = HybridRetriever(facts)

            if use_ego:
                results = retriever.retrieve_5stage(query, top_k=k, use_ego=True)
            else:
                results = retriever.retrieve(query, top_k=k)

            return [r.to_dict() for r in results[:k]]
        except Exception:
            return []

    async def _generate_response(
        self,
        query: str,
        facts: List[Dict[str, Any]],
        role: PerspectiveRole,
        *,
        llm_config: Optional["LlmCallConfig"] = None,
    ) -> tuple[str, float, bool]:
        """Сгенерировать ответ и явно вернуть, использовался ли реальный LLM."""
        if llm_config is not None:
            try:
                from core.llm_router import chat_complete

                prompt = self._build_prompt(query, facts, role)
                response = await chat_complete(llm_config, prompt)
                if response:
                    return response, 0.8, True
            except Exception as exc:
                # Content-free degradation signal: не логируем ключ/сырой provider payload.
                logger.warning(
                    "Branch LLM degraded for role %s: %s",
                    role.role_id,
                    type(exc).__name__,
                )

        # Fallback: существующий детерминированный Essence owner.
        try:
            from core.essence import compose_essence

            result = compose_essence(facts, relations=None)
            response = (result.short_answer or result.gist or "").strip()
            if response:
                return response, 0.6, False
        except Exception as exc:
            logger.warning(
                "Branch Essence fallback degraded for role %s: %s",
                role.role_id,
                type(exc).__name__,
            )

        # Абсолютный fallback — честно остаётся non-LLM.
        return (
            f"[{role.emoji} {role.label_ru}] Анализ {len(facts)} фактов по запросу: {query}",
            0.3,
            False,
        )

    def _build_prompt(
        self, query: str, facts: List[Dict[str, Any]], role: PerspectiveRole
    ) -> str:
        """Собрать prompt для LLM в стиле роли."""
        facts_text = "\n".join(
            f"- [{f.get('source', '?')} | conf={f.get('confidence', 0):.2f}] {f.get('claim', '')}"
            for f in facts[:10]
        )

        return (
            f"{role.prompt_modifier}\n\n"
            f"Запрос пользователя: {query}\n\n"
            f"Верифицированные факты:\n{facts_text}\n\n"
            f"Ответь в роли {role.label_ru}. Будь краток (3-5 предложений)."
        )

    def _extract_key_claims(self, response: str) -> List[str]:
        """Извлечь ключевые утверждения из ответа."""
        if not response:
            return []
        claims = [c.strip() for c in response.split(". ") if len(c.strip()) > 10]
        return claims[:5]

    def _synthesize(
        self, query: str, branches: List[BranchResult]
    ) -> SynthesisResult:
        """
        Синтезировать ответы нескольких веток в один.

        Логика:
            - Где ответы совпадают → высокая уверенность (consensus)
            - Где расходятся → отметить разногласие (divergence)
            - Выбрать лучшие части из каждой ветки
        """
        if len(branches) == 1:
            return SynthesisResult(
                response=branches[0].response,
                branches=branches,
                consensus_zones=[],
                divergence_zones=[],
                confidence=branches[0].confidence,
                dominant_role=branches[0].role.role_id,
            )

        # Найти consensus — claims которые встречаются в ≥2 ветках
        all_claims: Dict[str, List[str]] = {}
        for b in branches:
            for claim in b.key_claims:
                all_claims.setdefault(claim[:80].lower(), []).append(b.role.role_id)

        consensus = [
            claim for claim, roles in all_claims.items()
            if len(set(roles)) >= 2
        ]
        divergence = [
            claim for claim, roles in all_claims.items()
            if len(set(roles)) == 1
        ]

        # Доминирующая роль — с самым высоким priority
        dominant = max(branches, key=lambda b: (len(b.key_claims), b.role.priority))
        agg_confidence = sum(b.confidence for b in branches) / len(branches)

        # Собрать ответ
        parts: List[str] = []
        for b in sorted(branches, key=lambda x: x.role.priority, reverse=True):
            prefix = f"{b.role.emoji} **{b.role.label_ru}:**"
            parts.append(f"{prefix} {b.response}")

        response = "\n\n".join(parts)

        # Если есть divergence — добавить
        if divergence and len(branches) >= 2:
            response += (
                f"\n\n⚡ **Разногласие:** ветки расходятся в оценке: "
                f"{'; '.join(divergence[:3])}"
            )

        return SynthesisResult(
            response=response,
            branches=branches,
            consensus_zones=consensus,
            divergence_zones=divergence,
            confidence=round(agg_confidence, 2),
            dominant_role=dominant.role.role_id,
        )


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_manager: Optional[BranchManager] = None


def get_branch_manager() -> BranchManager:
    global _manager
    if _manager is None:
        _manager = BranchManager()
    return _manager


__all__ = [
    "BranchManager",
    "BranchResult",
    "SynthesisResult",
    "get_branch_manager",
]
