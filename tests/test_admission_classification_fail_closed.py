"""Single/batch canonical admission must use the same final modality axes."""
import copy

import pytest

from core.memory import SQLiteGraphStore
from core.write_result import WriteStatus


@pytest.fixture
def store(tmp_path):
    instance = SQLiteGraphStore(str(tmp_path / "admission.db"))
    yield instance
    instance.close()


@pytest.mark.parametrize("batch", [False, True])
@pytest.mark.parametrize("origin", [None, "", "UNKNOWN", "LLM_OUTPUT"])
def test_llm_world_requires_evidence_for_all_origin_shapes(store, batch, origin):
    fact = {"fact_id": "llm-world", "claim": "Вода кипит при ста градусах",
            "source": "gpt-4", "claim_type": "WORLD_FACT", "metadata": {}}
    if origin is not None:
        fact["origin_type"] = origin
    if batch:
        assert store.store_facts_batch([fact])["errors"] == 1
    else:
        result = store.store_fact_result(fact)
        assert result.status is WriteStatus.REJECTED_WRITE_GATE
        assert result.safe_reason_code == "world_fact_from_llm_requires_evidence"
        assert not result.created and not result.durable_write and not result.canonical_exists
    assert store.get_fact(fact["fact_id"]) is None


@pytest.mark.parametrize("batch", [False, True])
@pytest.mark.parametrize("existing", [False, True])
def test_classifier_failure_preserves_durable_record(store, monkeypatch, batch, existing):
    original = {"fact_id": "failure", "claim": "Мне тревожно", "source": "user",
                "claim_type": "EMOTION", "origin_type": "USER_REPORTED"}
    if existing:
        assert store.store_fact(original)
    before = copy.deepcopy(store.get_fact("failure"))

    def fail(*args, **kwargs):
        raise RuntimeError("private-claim-secret-must-not-escape")

    monkeypatch.setattr("core.claim_classifier.classify_claim", fail)
    candidate = {"fact_id": "failure", "claim": "changed", "source": "gpt-4"}
    if batch:
        assert store.store_facts_batch([candidate])["errors"] == 1
    else:
        result = store.store_fact_result(candidate)
        assert result.status is WriteStatus.REJECTED_WRITE_GATE
        assert result.safe_reason_code == "claim_classification_failed"
        assert not result.created and not result.durable_write
        assert result.canonical_exists is existing
        assert "private-claim" not in repr(result)
    assert store.get_fact("failure") == before


@pytest.mark.parametrize("batch", [False, True])
def test_llm_evidence_and_subjective_overrides_are_preserved(store, batch):
    facts = [
        {"fact_id": "world", "claim": "Вода кипит", "source": "gpt-4",
         "claim_type": "WORLD_FACT", "metadata": {"evidence_refs": ["source-1"]}},
        {"fact_id": "emotion", "claim": "Мне тревожно", "source": "user",
         "claim_type": "EMOTION"},
    ]
    if batch:
        assert store.store_facts_batch(facts)["stored"] == 2
    else:
        for fact in facts:
            assert store.store_fact_result(fact).status is WriteStatus.CREATED
    assert store.get_fact("world")["origin_type"] == "LLM_OUTPUT"
    assert store.get_fact("emotion")["claim_type"] == "EMOTION"
    assert store.get_fact("emotion")["origin_type"] == "USER_REPORTED"


@pytest.mark.parametrize("batch", [False, True])
@pytest.mark.parametrize("field,value", [("claim_type", "WORLD_FACTS"), ("origin_type", "invented")])
def test_invalid_explicit_modality_is_not_unknown_permission(store, batch, field, value):
    fact = {"fact_id": "invalid", "claim": "Вода кипит", "source": "gpt-4",
            "claim_type": "WORLD_FACT", "origin_type": "LLM_OUTPUT", field: value}
    if batch:
        assert store.store_facts_batch([fact])["errors"] == 1
    else:
        result = store.store_fact_result(fact)
        assert result.status is WriteStatus.REJECTED_WRITE_GATE
        assert result.safe_reason_code == "invalid_modality_type"
    assert store.get_fact("invalid") is None
