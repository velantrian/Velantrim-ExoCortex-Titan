"""Contract tests for adaptive retrieval execution hints."""
from __future__ import annotations

from core.budget_planner import plan


def test_lexical_plan_disables_dense_and_graph_execution() -> None:
    retrieval_plan = plan("вода", base_k=3)

    assert retrieval_plan.mode == "lexical"
    assert retrieval_plan.use_dense is False
    assert retrieval_plan.use_graph is False
    assert retrieval_plan.to_execution_kwargs() == {
        "retrieval_mode": "lexical",
        "k": 3,
        "max_hops": 1,
    }


def test_complex_plan_enables_dense_and_graph_execution() -> None:
    retrieval_plan = plan(
        "почему использование закалённого металла снижает энергозатраты "
        "при сравнении с бетоном и какие риски пожара возникают",
        base_k=3,
    )

    assert retrieval_plan.mode == "hybrid"
    assert retrieval_plan.use_dense is True
    assert retrieval_plan.use_graph is True
    assert retrieval_plan.to_execution_kwargs() == {
        "retrieval_mode": "hybrid",
        "k": 6,
        "max_hops": 2,
    }


def test_empty_plan_has_no_expensive_execution_path() -> None:
    retrieval_plan = plan("   ", base_k=3)

    assert retrieval_plan.mode == "none"
    assert retrieval_plan.use_dense is False
    assert retrieval_plan.use_graph is False
