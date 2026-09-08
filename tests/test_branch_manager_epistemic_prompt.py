from core.branch_manager import BranchManager
from core.perspectives import resolve_roles


def test_branch_prompt_does_not_globally_verify_retrieval_context() -> None:
    manager = BranchManager()
    role = resolve_roles("проанализируй систему")[0]
    facts = [
        {
            "source": "memory",
            "confidence": 0.40,
            "claim": "Observed claim.",
            "epistemic_state": "Observed",
        },
        {
            "source": "memory",
            "confidence": 0.95,
            "claim": "Validated claim.",
            "epistemic_state": "Validated",
        },
    ]

    prompt = manager._build_prompt("Что известно?", facts, role)

    assert "Верифицированные факты:" not in prompt
    assert "Записи памяти (могут иметь разный уровень подтверждения):" in prompt
    assert "Не повышай достоверность записей только из-за их присутствия в контексте." in prompt
    assert "Observed claim." in prompt
    assert "Validated claim." in prompt

    # This bounded fix changes wording only. Serialization shape remains unchanged.
    assert "epistemic_state" not in prompt
