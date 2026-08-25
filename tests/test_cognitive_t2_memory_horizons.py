"""T2 cognitive baseline: distinguish retention horizons without inventing a new memory system.

T2 maps existing Titan mechanisms to four user-visible retention horizons:

- working: ``chat_history`` for the current session;
- temporary: console ``block_memory`` (explicitly separate from long-term DB);
- intermediate: ``previous_chat_summary`` carried into a successor session;
- durable: facts persisted in ``SQLiteGraphStore``.

The test deliberately keeps *retention horizon* separate from *epistemic state*.
An ``Observed`` fact can be durably stored; ``Validated`` does not mean "permanent
memory". Promotion policy is a different concern from storage lifetime.

No new runtime component or automatic promotion policy is introduced here.
"""
from __future__ import annotations

from core.console_memory import build_chat_context_for_prompt
from core.memory import make_store


WORKING_MARKER = "T2_WORKING_COPPER_19"
TEMPORARY_MARKER = "T2_TEMPORARY_JADE_27"
INTERMEDIATE_MARKER = "T2_INTERMEDIATE_AMBER_43"
DURABLE_FACT_ID = "t2_durable_fact"
DURABLE_MARKER = "T2_DURABLE_COBALT_61"


def test_working_history_exists_only_when_current_session_supplies_it() -> None:
    current = build_chat_context_for_prompt(
        history=[{"role": "user", "content": f"Current constraint: {WORKING_MARKER}"}],
        previous_summary=None,
        lang="en",
    )
    successor_without_history = build_chat_context_for_prompt(
        history=None,
        previous_summary=None,
        lang="en",
    )

    assert WORKING_MARKER in current
    assert "CURRENT DIALOGUE (this session)" in current
    assert WORKING_MARKER not in successor_without_history


def test_block_memory_is_temporary_context_not_implicit_durable_fact(tmp_path) -> None:
    db_path = str(tmp_path / "t2-temporary.db")
    store = make_store(db_path)
    try:
        context = build_chat_context_for_prompt(
            history=None,
            previous_summary=None,
            lang="en",
            block_memory=[
                {
                    "claim": f"Temporary task note: {TEMPORARY_MARKER}",
                    "category": "project",
                }
            ],
        )

        assert TEMPORARY_MARKER in context
        assert "MEMORY BLOCK" in context
        assert "separate from long-term DB" in context
        assert store.get_fact(DURABLE_FACT_ID) is None
    finally:
        store.close()


def test_previous_chat_summary_is_intermediate_handoff_not_automatic_retention() -> None:
    handoff = build_chat_context_for_prompt(
        history=None,
        previous_summary=f"Open decision from prior session: {INTERMEDIATE_MARKER}",
        lang="en",
    )
    successor_without_handoff = build_chat_context_for_prompt(
        history=None,
        previous_summary=None,
        lang="en",
    )

    assert INTERMEDIATE_MARKER in handoff
    assert "PREVIOUS CHAT" in handoff
    assert INTERMEDIATE_MARKER not in successor_without_handoff


def test_durable_fact_survives_store_reopen_while_remaining_observed(tmp_path) -> None:
    """Durability and epistemic confidence are orthogonal dimensions."""
    db_path = str(tmp_path / "t2-durable.db")

    first = make_store(db_path)
    try:
        created = first.store_fact(
            {
                "fact_id": DURABLE_FACT_ID,
                "claim": f"Durable project fact: {DURABLE_MARKER}",
                "source": "t2_controlled_context",
                "confidence": 0.95,
                "epistemic_state": "Observed",
                "metadata": {"memory_category": "project"},
            }
        )
        assert created is True
        before_restart = first.get_fact(DURABLE_FACT_ID)
        assert before_restart is not None
        assert before_restart["epistemic_state"] == "Observed"
    finally:
        first.close()

    reopened = make_store(db_path)
    try:
        after_restart = reopened.get_fact(DURABLE_FACT_ID)
        assert after_restart is not None
        assert DURABLE_MARKER in after_restart["claim"]
        assert after_restart["epistemic_state"] == "Observed"
    finally:
        reopened.close()


def test_horizons_do_not_implicitly_promote_into_each_other(tmp_path) -> None:
    """Supplying transient context must not create a durable fact as a side effect."""
    db_path = str(tmp_path / "t2-no-promotion.db")
    store = make_store(db_path)
    try:
        context = build_chat_context_for_prompt(
            history=[{"role": "user", "content": WORKING_MARKER}],
            previous_summary=INTERMEDIATE_MARKER,
            lang="en",
            block_memory=[{"claim": TEMPORARY_MARKER, "category": "project"}],
        )
        assert WORKING_MARKER in context
        assert TEMPORARY_MARKER in context
        assert INTERMEDIATE_MARKER in context

        # The context builder is read-only. None of these horizons silently gains
        # durable-fact authority merely because it was supplied to a prompt.
        assert store.get_fact(DURABLE_FACT_ID) is None
    finally:
        store.close()
