"""Evidence availability and repetition must not bypass existing admission policy."""
from copy import deepcopy

import pytest

from core import pipeline
from core.consolidation_engine import ConsolidationEngine
from core.memory import SQLiteGraphStore


@pytest.mark.parametrize("unavailable", ["missing", "raises"])
def test_pipeline_withholds_answer_when_pack_policy_unavailable(monkeypatch, unavailable):
    # A canonical-looking low-confidence candidate used to survive the raw fallback.
    monkeypatch.setattr(pipeline, "retrieve", lambda *a, **k: [{
        "id": "unsafe", "fact_id": "unsafe", "claim": "untrusted candidate",
        "source": "external", "confidence": .1, "epistemic_state": "Validated",
    }])
    monkeypatch.setattr("core.cross_domain.is_cross_domain_enabled", lambda: False)
    if unavailable == "missing":
        monkeypatch.setattr(pipeline, "_FACTS_PACK_BUILDER_AVAILABLE", False)
    else:
        def fail(*args, **kwargs):
            raise RuntimeError("private-policy-detail")
        monkeypatch.setattr(pipeline.FactsPackBuilder, "build", fail)
    monkeypatch.setattr(pipeline, "generate_answer", lambda *a, **k: pytest.fail("answer generated"))
    result = pipeline.run("candidate")
    assert result["insufficient_evidence"] is True
    assert result["reason_code"] == "facts_pack_policy_unavailable"
    assert not result["facts"]
    assert "private-policy-detail" not in repr(result)


def test_repetition_cannot_raise_confidence_or_unlock_consolidation(tmp_path):
    store = SQLiteGraphStore(str(tmp_path / "repeat.db"))
    try:
        for index, claim in enumerate([
            "Service access is permitted for registered users",
            "Service access is not permitted for registered users",
            "Service access is permitted for registered users after approval",
        ]):
            assert store.store_fact({"fact_id": str(index), "claim": claim,
                                     "source": "manual", "confidence": .74,
                                     "metadata": {"evidence_refs": ["same-source", "same-copy"]}})
        before = deepcopy(store.get_all_facts())
        report = ConsolidationEngine(store, min_confidence=.8).run()
        assert report.promoted_validated == report.promoted_hypothesized == 0
        assert report.skipped_low_confidence == 3
        assert store.get_all_facts() == before
    finally:
        store.close()


@pytest.mark.parametrize("mode", ["STRICTT", "", 17, object()])
def test_invalid_promotion_mode_rejected_before_read_or_mutation(tmp_path, monkeypatch, mode):
    store = SQLiteGraphStore(str(tmp_path / "mode.db"))
    try:
        monkeypatch.setattr(store, "_get_fact_durable", lambda *a: pytest.fail("read before validation"))
        with pytest.raises(ValueError, match="Unknown cognitive mode"):
            store.validate_and_promote("any", mode=mode)
    finally:
        store.close()
