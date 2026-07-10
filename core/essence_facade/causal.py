"""🧬 core/essence_facade/causal.py — CausalGraph bridge + path explanation"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


def get_causal_bridge():
    """Мост к causal_graph.py. Файл не перемещён."""
    try:
        from core.causal_graph import get_causal_graph
        return get_causal_graph()
    except Exception:
        return None


def explain_path(
    fact_a: str,
    fact_b: str,
    *,
    max_depth: int = 5,
    min_confidence: float = 0.3,
) -> Optional[Dict[str, Any]]:
    """
    Объяснить как fact_a связан с fact_b через граф.

    Использует bfs-поиск пути в CausalGraph, затем explain_path()
    ChainResult для человекочитаемого объяснения.

    Возвращает dict с ключами: path_text, chains, total_weight,
    или None если путь не найден.

    Пример:
        >>> explain_path("phys.force", "chem.reaction")
        {
            "path_text": "phys.force →[causes, 0.95]→ ... (3 рёбер)",
            "chains": [...],
            "total_weight": 0.71,
        }
    """
    bridge = get_causal_bridge()
    if bridge is None:
        return None

    from core.causal_graph import ChainResult

    # Найти все цепочки от A
    chains: List[ChainResult] = bridge.causal_chain(
        fact_a, max_depth=max_depth, min_confidence=min_confidence,
    )

    # Фильтровать: только те что заканчиваются на B
    matching = [
        c for c in chains
        if c.chain and c.chain[-1].to_fact_id == fact_b
    ]

    if not matching:
        # Попробовать обратное направление
        chains_b = bridge.causal_chain(
            fact_b, max_depth=max_depth, min_confidence=min_confidence,
        )
        matching = [
            c for c in chains_b
            if c.chain and c.chain[-1].to_fact_id == fact_a
        ]

    if not matching:
        return None

    # Выбрать лучший путь (по weighted_confidence)
    best = max(matching, key=lambda c: c.weighted_confidence)

    return {
        "path_text": best.explain_path(),
        "chain": best.to_dict(),
        "total_weight": best.weighted_confidence,
        "from_fact": fact_a,
        "to_fact": fact_b,
        "depth": len(best.chain),
    }


__all__ = [
    "get_causal_bridge",
    "explain_path",
]
