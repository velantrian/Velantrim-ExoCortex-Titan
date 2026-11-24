"""PR #537 security fix (Manus audit 2026-11-24), P0: false Soft L1 allow.

``is_explicit_refusal_sentence`` found a refusal substring but not whether
the refusal itself was negated or contradicted, so a text that *asserts* use
of the source-X figures could be delivered as ``FLAG_L1_REFUSAL``.

The scenario set (``tests/fixtures/source_x_soft_l1_contradiction_cases_2026-11-24.json``)
is new, hand-written, RU/EN, and NOT taken from the 66-text corpus. It is a
REGRESSION set written by the executor of the fix, not an independent
benchmark. Each case checks the status, the text actually returned and the
public gate record. End-to-end HTTP checks run ``/chat`` and ``/query`` with
the flag on (provider call patched, gate not mocked). The heuristic is a
pattern check, not semantic understanding of the text.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.test_llm_context_no_silent_truncation import (
    _ALL_SETTINGS,
    SYNTHETIC_KEY,
    _install_fake,
    _query_harness,
)

CASES_PATH = Path(__file__).parent / "fixtures" / "source_x_soft_l1_contradiction_cases_2026-11-24.json"
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))
X = ("21,8", "21.8", "7,6", "7.6", "53,5", "53.5")
HEADERS = {"X-Api-Key": "ci-test-key"}
TZ_EXAMPLE = next(c["text"] for c in CASES["items"] if c["id"] == "negated_tz_example")


def sxg():
    return importlib.import_module("core.source_x_gate")


@pytest.fixture(autouse=True)
def _clean_flag(monkeypatch):
    monkeypatch.delenv("ENABLE_SOURCE_X_GATE", raising=False)
    importlib.import_module("core.feature_config").clear_config_cache()
    yield
    importlib.import_module("core.feature_config").clear_config_cache()


def test_case_set_is_labeled_regression_and_covers_every_category():
    assert CASES["role"] == "REGRESSION"
    cats = {c["category"] for c in CASES["items"]}
    assert cats == {
        "explicit_refusal", "negated_refusal", "refusal_then_use", "asserted",
        "official_only", "name_only", "ambiguous",
    }


@pytest.mark.parametrize("case", CASES["items"], ids=[c["id"] for c in CASES["items"]])
def test_scenario_status_text_and_public_record(case):
    s = sxg()
    cfg = s.SourceXGateConfig(enabled=True)
    out = s.gate_final_text(case["text"], surface="secfix", config=cfg)
    pub = out.public()
    assert out.status == case["expected"], case["id"]
    assert pub["status"] == case["expected"]
    if case["expected"] == "BLOCKED_ATTEMPT":
        assert out.text == s.USER_FACING_BLOCK_MESSAGE
        assert not any(x in (out.text or "") for x in X)
        assert pub["blocked"] is True and pub["delivered"] is False
    else:
        assert out.text == case["text"]
        assert pub["blocked"] is False and pub["delivered"] is True
    assert not any(x in json.dumps(pub, ensure_ascii=False) for x in X)


def test_refusal_assessment_kinds():
    s = sxg()
    assert s.refusal_assessment("Цифры 21,8 не используются.") == "refusal"
    assert s.refusal_assessment("Неверно, что цифры 21,8 не используются.") == "negated_refusal"
    assert s.refusal_assessment("Цифры 21,8 вовсе не исключены из отчёта.") == "negated_refusal"
    assert s.refusal_assessment("Цифры 21,8 не используются; однако 7,6 включены.") == "ambiguous"
    assert s.refusal_assessment("Выручка 21,8 млн.") == "none"
    assert s.is_explicit_refusal_sentence("Неверно, что цифры 21,8 не используются.") is False


# ── end-to-end over HTTP, flag on (provider patched, gate real) ──────────────


@pytest.fixture
def fake(monkeypatch):
    for n in _ALL_SETTINGS:
        monkeypatch.delenv(n, raising=False)
    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "allowed")
    return _install_fake(monkeypatch)


def _flag(monkeypatch, value: str | None):
    if value is None:
        monkeypatch.delenv("ENABLE_SOURCE_X_GATE", raising=False)
    else:
        monkeypatch.setenv("ENABLE_SOURCE_X_GATE", value)
    importlib.import_module("core.feature_config").clear_config_cache()


def _chat(monkeypatch, reply_text: str):
    srv = importlib.import_module("server")
    ls = importlib.import_module("core.llm_stream")
    monkeypatch.setattr(srv, "pipeline_run", lambda q, mode, domain: {"facts": [], "error": None})

    async def complete(*a, **k):
        return reply_text, {}
    monkeypatch.setattr(ls, "chat_complete_messages", complete)
    body = {"message": "Какая выручка?", "llm_provider": "deepseek", "llm_api_key": SYNTHETIC_KEY,
            "llm_model": "deepseek-v4-flash", "auto_save_memory": False, "use_memory": True}
    return TestClient(srv.app).post("/chat", json=body, headers=HEADERS)


def test_http_chat_contradictory_refusal_is_not_delivered_with_gate_on(fake, monkeypatch):
    _flag(monkeypatch, "1")
    r = _chat(monkeypatch, TZ_EXAMPLE)
    data = r.json()
    assert r.status_code == 200
    assert data["source_x_gate"]["status"] == "BLOCKED_ATTEMPT"
    assert not any(x in data["reply"] for x in X)


def test_http_chat_plain_refusal_still_delivered_with_gate_on(fake, monkeypatch):
    _flag(monkeypatch, "1")
    text = next(c["text"] for c in CASES["items"] if c["id"] == "refusal_ru_list")
    data = _chat(monkeypatch, text).json()
    assert data["source_x_gate"]["status"] == "FLAG_L1_REFUSAL"
    assert data["reply"] == text


def test_http_chat_flag_off_unchanged(fake, monkeypatch):
    _flag(monkeypatch, None)
    data = _chat(monkeypatch, TZ_EXAMPLE).json()
    assert data["reply"] == TZ_EXAMPLE
    assert data.get("source_x_gate") is None


def test_http_query_contradictory_refusal_is_not_delivered_with_gate_on(fake, monkeypatch):
    _flag(monkeypatch, "1")
    srv = _query_harness(monkeypatch, [{"fact_id": "f1", "claim": "Встреча во вторник.",
                                         "source": "memo", "confidence": 0.9}])

    async def gen(q, system=None, override=None):
        return TZ_EXAMPLE
    monkeypatch.setattr(srv, "_llm_generate", gen)
    r = TestClient(srv.app).post("/query", json={"query": "Какая выручка?", "use_llm": True},
                                 headers=HEADERS)
    data = r.json()
    assert r.status_code == 200
    assert not any(x in json.dumps(data["llm_answer"], ensure_ascii=False) for x in X)
    assert data["source_x_gate"]["llm_answer"]["status"] == "BLOCKED_ATTEMPT"


# ── probe set: known gaps of the pattern heuristic (recorded, not fixed) ─────

PROBE = json.loads(
    (Path(__file__).parent / "fixtures" / "source_x_soft_l1_probe_2026-11-24.json").read_text(encoding="utf-8")
)
# Known gaps at this head. strict xfail: if one starts passing, the list must
# be updated (and the register in the hand-off), not silently ignored.
KNOWN_FALSE_ALLOW = {"probe_attack_03", "probe_attack_04", "probe_attack_06", "probe_attack_10"}
KNOWN_FALSE_BLOCK = {"probe_legit_09", "probe_legit_10"}


def _probe_params():
    out = []
    for c in PROBE["items"]:
        marks = []
        if c["id"] in KNOWN_FALSE_ALLOW:
            marks.append(pytest.mark.xfail(strict=True, reason="KNOWN GAP: false Soft L1 allow (pattern heuristic)"))
        if c["id"] in KNOWN_FALSE_BLOCK:
            marks.append(pytest.mark.xfail(strict=True, reason="KNOWN GAP: false block of a legitimate refusal"))
        out.append(pytest.param(c, id=c["id"], marks=marks))
    return out


@pytest.mark.parametrize("case", _probe_params())
def test_probe_case(case):
    s = sxg()
    out = s.gate_final_text(case["text"], surface="probe", config=s.SourceXGateConfig(enabled=True))
    assert out.status == case["expected"]
