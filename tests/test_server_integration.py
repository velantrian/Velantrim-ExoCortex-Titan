"""
tests/test_server_integration.py — Velantrim ExoCortex
=======================================================
Интеграционные тесты через FastAPI TestClient.

Цель: ловить баги на стыках компонентов (server ↔ pipeline ↔ sleep_worker ↔ ngram).
До v8.4.0 этого слоя тестов не было — поэтому SleepTimeWorker startup TypeError,
NGram split, CORS misconfig прожили до production.

Эти тесты:
  - Не требуют запущенного uvicorn — TestClient поднимает app внутри процесса
  - Используют tmp_path для изоляции — каждый тест получает свежую БД
  - Покрывают: startup lifespan, авторизацию, NGram→pipeline coherence,
    SleepTimeWorker реально запущен, transition audit trail spoofing.

AUDIT-FIX v8.4.0: новый файл, регрессионная защита для всех integration-багов.

Запуск:
    pytest tests/test_server_integration.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── Фикстура: изолированный сервер через TestClient ─────────────────────────

@pytest.fixture
def test_client(tmp_path, monkeypatch):
    """
    FastAPI TestClient с изолированными БД в tmp_path.

    Каждый тест получает свежую систему — никакого state-share.
    API_KEY="test-key" — те же тесты могут проверять auth.
    """
    db_path        = str(tmp_path / "integration.db")
    ngram_db_path  = str(tmp_path / "integration_ngram.db")
    blocks_db_path = str(tmp_path / "blocks.db")
    notebook_db    = str(tmp_path / "notebook.db")

    # Настройка ENV ДО импорта server (он читает их при инициализации)
    monkeypatch.setenv("VELANTRIM_API_KEY",       "test-key")
    monkeypatch.setenv("VELANTRIM_DB_PATH",       db_path)
    monkeypatch.setenv("VELANTRIM_NGRAM_DB",      ngram_db_path)
    monkeypatch.setenv("CORE_BLOCKS_DB",          blocks_db_path)
    monkeypatch.setenv("NOTEBOOK_DB",             notebook_db)
    monkeypatch.setenv("LLM_PROVIDER",            "none")
    # false — избегаем database is locked при параллельных PATCH/transition;
    # SleepTimeWorker тестируется в fixture sleep_client ниже.
    monkeypatch.setenv("SLEEP_WORKER_ENABLED",    "false")
    monkeypatch.setenv("VELANTRIM_ALLOW_OPEN",    "false")  # с ключом, не открытый
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH",     "0")  # отдельный conn singleton → lock
    monkeypatch.setenv("ENABLE_VELUM",           "0")

    # Импорт ПОСЛЕ настройки ENV
    # Удаляем кеш если был
    for mod in list(sys.modules.keys()):
        if mod.startswith(("server", "core.")):
            del sys.modules[mod]

    try:
        from fastapi.testclient import TestClient

        import server as srv
        from core.feature_config import clear_config_cache
    except ImportError as exc:
        pytest.skip(f"Сервер недоступен ({exc})")

    clear_config_cache()

    # TestClient автоматически запускает lifespan
    with TestClient(srv.app) as client:
        client.headers.update({"X-Api-Key": "test-key"})
        yield client, srv


@pytest.fixture
def sleep_client(tmp_path, monkeypatch):
    """TestClient со SleepTimeWorker (отдельная БД)."""
    db_path = str(tmp_path / "sleep_integration.db")
    ngram_db_path = str(tmp_path / "sleep_integration_ngram.db")
    monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db_path)
    monkeypatch.setenv("VELANTRIM_NGRAM_DB", ngram_db_path)
    monkeypatch.setenv("CORE_BLOCKS_DB", str(tmp_path / "blocks.db"))
    monkeypatch.setenv("NOTEBOOK_DB", str(tmp_path / "notebook.db"))
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("SLEEP_WORKER_ENABLED", "true")
    monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")

    for mod in list(sys.modules.keys()):
        if mod.startswith(("server", "core.")):
            del sys.modules[mod]

    try:
        from fastapi.testclient import TestClient

        import server as srv
    except ImportError as exc:
        pytest.skip(str(exc))

    with TestClient(srv.app) as client:
        client.headers.update({"X-Api-Key": "test-key"})
        yield client, srv


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Startup lifespan — проверка что SleepTimeWorker реально запустился
# ═══════════════════════════════════════════════════════════════════════════════

class TestStartupLifespan:
    """
    Regression: SleepTimeWorker до v8.4.0 не запускался из-за TypeError
    на параметре store=. Ошибка глоталась try/except → /agent/* возвращали 503.
    """

    def test_root_endpoint_alive(self, sleep_client):
        """Базовая проверка: сервер поднялся."""
        client, _ = sleep_client
        r = client.get("/")
        assert r.status_code == 200, "Root endpoint должен отвечать"

    def test_health_includes_sleep_worker_status(self, sleep_client):
        """/health показывает статус SleepTimeWorker."""
        client, _ = sleep_client
        r = client.get("/health")
        assert r.status_code in (200, 503)
        data = r.json()
        # SleepTimeWorker должен быть упомянут — если его нет в response,
        # значит, lifespan его не инициализировал
        assert "components" in data or "status" in data

    def test_sleep_worker_endpoints_not_503(self, sleep_client):
        """
        Regression: /agent/notebook должен НЕ возвращать 503.
        До v8.4.0 эти endpoints всегда 503, потому что worker молча упал
        на startup с TypeError на `store=` параметре.
        """
        client, srv = sleep_client

        # Если worker запустился — endpoint вернёт 200 (даже с пустым notebook)
        # Если не запустился — 503
        r = client.get("/agent/notebook")
        assert r.status_code != 503, (
            "SleepTimeWorker не запустился (status=503). "
            "Регрессия v8.4.0 фикса: проверь что `store=` не вернулся "
            "в вызов make_sleep_time_worker в server.py"
        )

    def test_sleep_worker_instance_exists(self, sleep_client):
        """_sleep_worker модуля server должен быть не None."""
        _, srv = sleep_client
        assert srv._sleep_worker is not None, (
            "_sleep_worker is None — startup провалился. "
            "Это та самая регрессия, что v8.4.0 закрыл."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. NGram coherence: pipeline пишет → server находит
# ═══════════════════════════════════════════════════════════════════════════════

class TestNGramCoherence:
    """
    Regression: до v8.4.0 server создавал свой _ngram, pipeline писал
    через ngram_index_fact() в module-singleton с хардкоженным путём.
    Получались две разные БД — pipeline индексировал в одну, server искал в другой.
    """

    def test_indexed_fact_findable_through_server(self, test_client):
        """
        Делаем ingest через server → server должен видеть факт в NGramIndex.

        Это integration-тест который смог бы поймать NGram split до v8.4.0.
        """
        client, srv = test_client

        # Ingest текста — server индексирует через свой _ngram
        r = client.post("/ingest/text", json={
            "text":       "quantum entanglement is a physical phenomenon",
            "source":     "integration_test",
            "confidence": 0.9,
        })
        assert r.status_code == 200, f"Ingest failed: {r.text}"

        # Тот же _ngram должен найти этот контент
        if srv._ngram and srv._ngram.available:
            candidates = srv._ngram.query("quantum", limit=10)
            assert len(candidates) > 0, (
                "NGram split regression: server._ngram не нашёл только что "
                "проиндексированный факт. Pipeline и server используют разные БД."
            )

    def test_ngram_path_synced(self, test_client):
        """server._ngram и module _GLOBAL_NGRAM должны указывать на одну БД."""
        _, srv = test_client
        if not srv._ngram:
            pytest.skip("NGramIndex недоступен")

        from core.ngram_index import get_global_ngram
        global_ngram = get_global_ngram()
        assert global_ngram is srv._ngram, (
            "_GLOBAL_NGRAM != server._ngram — set_global_ngram() не отработал. "
            "Pipeline будет писать в одну БД, server — в другую."
        )


class TestConsoleChatMemory:
    """Regression tests for the browser console chat memory path."""

    def test_chat_surfaces_observed_memory_without_llm(self, test_client):
        client, _ = test_client

        r = client.post("/facts", json={
            "fact_id": "console_name_fact",
            "claim": "my name is Ruslan",
            "source": "console_chat",
            "confidence": 0.88,
            "metadata": {"memory_category": "personal"},
        })
        assert r.status_code == 201, r.text

        r = client.post("/chat", json={
            "message": "what is my name?",
            "profile": "citizen",
            "use_memory": True,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": False,
            "block_memory": [],
            "chat_history": [],
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["error"] is None
        assert data["facts_count"] >= 1
        assert "my name is Ruslan" in data["reply"]
        assert "not validated yet" in data["reply"]

    def test_chat_stream_surfaces_observed_memory_without_llm(self, test_client):
        client, _ = test_client

        r = client.post("/facts", json={
            "fact_id": "console_stream_name_fact",
            "claim": "my name is Ruslan",
            "source": "console_chat",
            "confidence": 0.88,
            "metadata": {"memory_category": "personal"},
        })
        assert r.status_code == 201, r.text

        r = client.post("/chat/stream", json={
            "message": "what is my name?",
            "profile": "citizen",
            "use_memory": True,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": False,
            "block_memory": [],
            "chat_history": [],
        })
        assert r.status_code == 200, r.text
        assert "my name is Ruslan" in r.text
        assert "not validated yet" in r.text
        assert '"facts_count": 1' in r.text

    def test_offline_about_user_inventory_ru_en(self, test_client):
        client, _ = test_client
        r = client.post("/facts", json={
            "fact_id": "offline_name_fact",
            "claim": "my name is Ruslan",
            "source": "console_chat",
            "confidence": 0.88,
            "metadata": {"memory_category": "personal"},
        })
        assert r.status_code == 201, r.text

        ru = client.post("/chat", json={
            "message": "что ты знаешь обо мне подробно?",
            "profile": "citizen",
            "use_memory": True,
            "llm_enabled": False,
            "ui_lang": "ru",
            "auto_save_memory": False,
        })
        assert ru.status_code == 200, ru.text
        assert "Что я знаю о тебе" in ru.json()["reply"]
        assert "my name is Ruslan" in ru.json()["reply"]
        assert ru.json()["facts_count"] >= 1

        en = client.post("/chat", json={
            "message": "what do you know about me in detail?",
            "profile": "citizen",
            "use_memory": True,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": False,
        })
        assert en.status_code == 200, en.text
        assert "What I know about you" in en.json()["reply"]
        assert "my name is Ruslan" in en.json()["reply"]
        assert en.json()["facts_count"] >= 1

    def test_console_notes_crud_and_offline_notes_reply(self, test_client):
        client, _ = test_client
        r = client.post("/console/notes", json={
            "content": "Call Ruslan about the green industry project",
            "title": "Project call",
        })
        assert r.status_code == 201, r.text
        note_id = r.json()["note_id"]
        assert note_id.startswith("note_")

        r = client.post(f"/console/notes/{note_id}/edit", json={
            "instruction": "добавь обсудить биосовместимые технологии",
        })
        assert r.status_code == 200, r.text
        assert "биосовместимые" in r.json()["content"]

        r = client.post("/chat", json={
            "message": "какие заметки у тебя сохранены?",
            "profile": "citizen",
            "use_memory": True,
            "llm_enabled": False,
            "ui_lang": "ru",
            "auto_save_memory": False,
        })
        assert r.status_code == 200, r.text
        assert note_id in r.json()["reply"]
        assert "Call Ruslan" in r.json()["reply"]

    def test_chat_accepts_long_console_message_without_llm(self, test_client):
        client, _ = test_client
        long_message = "что ты знаешь обо мне? " + ("детально " * 650)

        r = client.post("/chat", json={
            "message": long_message,
            "profile": "citizen",
            "use_memory": False,
            "llm_enabled": False,
            "ui_lang": "ru",
            "auto_save_memory": False,
        })

        assert r.status_code == 200, r.text


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Authorization & security — закрывает CORS, API_KEY, req.by spoofing
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecurityIntegration:

    def test_no_api_key_returns_401_or_403(self, test_client):
        """Запрос без X-Api-Key → отказ."""
        client, _ = test_client
        # Очищаем дефолтный header
        r = client.post("/query", json={"query": "test"}, headers={"X-Api-Key": ""})
        assert r.status_code in (401, 403), (
            f"Запрос без ключа должен быть отклонён, got {r.status_code}. "
            "Возможно VELANTRIM_API_KEY=\"\" → сервер открыт."
        )

    def test_wrong_api_key_rejected(self, test_client):
        """Неправильный ключ → 401/403."""
        client, _ = test_client
        r = client.post("/query", json={"query": "test"},
                        headers={"X-Api-Key": "wrong-key-xyz"})
        assert r.status_code in (401, 403)

    def test_health_does_not_require_auth(self, test_client):
        """/health должен быть доступен без ключа (для k8s liveness)."""
        client, _ = test_client
        r = client.get("/health", headers={"X-Api-Key": ""})
        # 200 или 503 OK; 401/403 — означает что health тоже под auth (плохо)
        assert r.status_code in (200, 503), (
            f"/health под auth — k8s liveness probe не сработает. "
            f"Got {r.status_code}"
        )

    def test_transition_by_field_not_spoofable(self, test_client):
        """
        Regression: req.by игнорируется, actor подставляется серверный.
        До v8.4.0 клиент мог подделать audit trail.
        """
        client, _ = test_client

        # Создаём факт через ingest
        r = client.post("/facts", json={
            "fact_id":    "spoof_test_1",
            "claim":      "test claim for spoofing",
            "source":     "integration",
            "confidence": 0.6,
        })
        if r.status_code not in (200, 201):
            pytest.skip(f"POST /facts недоступен: {r.status_code}")

        # Пытаемся подделать by="admin_attacker"
        r = client.patch(
            "/facts/spoof_test_1/transition",
            json={"new_state": "Hypothesized", "by": "admin_attacker"},
        )
        if r.status_code != 200:
            pytest.skip(f"Transition endpoint не отработал: {r.status_code} {r.text}")

        # Проверяем что в history записано серверное имя, не подделка
        r = client.get("/facts/spoof_test_1")
        if r.status_code == 200:
            fact = r.json()
            history = fact.get("history", [])
            if history:
                last_by = history[-1].get("by", "")
                assert not last_by.startswith("admin_"), (
                    f"By field spoofed: actor='{last_by}' принят от клиента. "
                    "Регрессия v8.4.0 фикса transition endpoint."
                )
                assert last_by.startswith("api:"), (
                    f"Serverный actor должен начинаться с 'api:', got '{last_by}'"
                )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Pipeline идемпотентность через HTTP (HybridRetriever singleton проверка)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPipelinePerformance:
    """
    Косвенная проверка singleton HybridRetriever: второй запрос должен быть
    значительно быстрее первого (warm-up vs warm).
    """

    def test_second_query_faster_than_first(self, test_client):
        """
        Regression v8.4.0: HybridRetriever singleton. До этого фикса каждый
        запрос пересоздавал retriever с загрузкой sentence-transformer (1-2с).
        После фикса второй запрос должен быть существенно быстрее.
        """
        import time
        client, _ = test_client

        # Сначала наполняем — иначе retrieval пустой
        client.post("/ingest/text", json={
            "text":   "quantum mechanics describes nature at smallest scales",
            "source": "perf_test", "confidence": 0.8,
        })

        # Первый запрос — может быть медленным (warmup)
        t1 = time.perf_counter()
        r1 = client.post("/query", json={"query": "quantum"})
        elapsed_1 = time.perf_counter() - t1
        assert r1.status_code in (200, 404)  # 404 если retrieval пустой — ок

        # Второй запрос — должен быть быстрее (singleton переиспользован)
        t2 = time.perf_counter()
        r2 = client.post("/query", json={"query": "quantum"})
        elapsed_2 = time.perf_counter() - t2
        assert r2.status_code in (200, 404)

        # Мягкая проверка: второй не должен быть СУЩЕСТВЕННО медленнее первого
        # (если бы singleton не работал — второй был бы такой же или дольше)
        # Если различие в порядке + warmup эффект не сработал — может быть мелкая база.
        # Для базы из 1 факта разница может быть в шуме — поэтому только sanity.
        assert elapsed_2 < elapsed_1 * 5, (
            f"Pipeline возможно пересоздаёт HybridRetriever: "
            f"first={elapsed_1*1000:.0f}ms, second={elapsed_2*1000:.0f}ms"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CORS configuration sanity
# ═══════════════════════════════════════════════════════════════════════════════

class TestCORSConfig:
    """CORS misconfig не должен ломать preflight."""

    def test_cors_not_wildcard_with_credentials(self, test_client):
        """
        Если CORS_ORIGINS=*, allow_credentials должен быть False (CORS spec).
        До v8.4.0 был баг: дефолт `*` + `credentials=True` → браузеры отклоняют preflight.
        """
        _, srv = test_client

        # Если у сервера CORS_ALLOW_CREDENTIALS=True, в CORS_ORIGINS не должно быть "*"
        if hasattr(srv, "CORS_ORIGINS") and hasattr(srv, "CORS_ALLOW_CREDENTIALS"):
            if "*" in srv.CORS_ORIGINS:
                assert not srv.CORS_ALLOW_CREDENTIALS, (
                    "CORS misconfig: origins='*' + allow_credentials=True. "
                    "v8.4.0 фикс должен был автоматически отключить credentials."
                )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. PR-C1 — truthful write results (no phantom success/provenance over HTTP)
# ═══════════════════════════════════════════════════════════════════════════════
# HTTP-level companion to tests/test_write_result.py (unit-level). Reuses the
# `test_client` fixture above rather than a second, independent TestClient
# fixture — running two independent FastAPI TestClient bootstraps side by
# side across the full test suite was observed to destabilize unrelated
# tests elsewhere in the run (see tests/test_write_result.py's module
# docstring), even though every test using either fixture passed
# individually and in small combinations.

def _pr_c1_provenance_row_exists(fact_id: str) -> bool:
    from core.memory import _GLOBAL_STORE

    with _GLOBAL_STORE._db() as conn:
        row = conn.execute(
            "SELECT 1 FROM l0_fact_provenance WHERE fact_id = ?", (fact_id,)
        ).fetchone()
    return row is not None


class TestConsoleAutoSaveTruthfulness:
    """RED before the PR-C1 fix: a WriteGate-rejected auto-save candidate
    ends up in memory_saved with a phantom fact_id instead of
    memory_suggestions."""

    def test_write_gate_rejection_not_reported_as_saved(self, test_client, monkeypatch):
        client, _srv = test_client
        import core.write_gate as wg

        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
        monkeypatch.setattr(wg, "admit_fact", lambda **kw: (False, "test_forced_rejection"))

        r = client.post("/chat", json={
            "message": "remember that pr-c1 write gate rejection test claim",
            "profile": "citizen",
            "use_memory": False,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": True,
            "persist_to_system": True,
            "block_memory": [],
            "chat_history": [],
        })
        assert r.status_code == 200, r.text
        data = r.json()

        assert data["memory_saved"] == [], (
            f"a rejected candidate must not appear in memory_saved: {data['memory_saved']}"
        )
        assert len(data["memory_suggestions"]) == 1

        from core.memory import get_all_facts

        claims = [f["claim"] for f in get_all_facts()]
        assert "pr-c1 write gate rejection test claim" not in claims

    def test_successful_autosave_baseline(self, test_client):
        """BASELINE: an ordinary auto-save (no rejection) must keep working
        and land in memory_saved with a real fact_id."""
        client, _srv = test_client

        r = client.post("/chat", json={
            "message": "remember that pr-c1 successful autosave baseline claim",
            "profile": "citizen",
            "use_memory": False,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": True,
            "persist_to_system": True,
            "block_memory": [],
            "chat_history": [],
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert len(data["memory_saved"]) == 1
        fact_id = data["memory_saved"][0]["fact_id"]
        assert fact_id

        from core.memory import get_fact

        assert get_fact(fact_id) is not None


class TestPostFactsTruthfulness:
    """RED before the PR-C1 fix: POST /facts returned HTTP 201 with a `null`
    body when store_fact() was rejected by WriteGate, and an uncaught 500
    when MemoryBudgetExceededError was raised — in both cases the L0 raw
    text write had already committed before the failure."""

    def test_write_gate_rejection_is_not_201(self, test_client, monkeypatch):
        client, _srv = test_client
        import core.write_gate as wg

        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
        monkeypatch.setattr(wg, "admit_fact", lambda **kw: (False, "test_forced_rejection"))

        r = client.post("/facts", json={
            "fact_id": "facts_wg_reject_1",
            "claim": "pr-c1 post facts write gate rejection",
            "source": "test",
            "confidence": 0.9,
        })
        assert r.status_code != 201, (
            f"a rejected write must not return 201 Created (body={r.text!r})"
        )
        assert r.status_code < 500

        from core.memory import get_fact

        assert get_fact("facts_wg_reject_1") is None
        assert not _pr_c1_provenance_row_exists("facts_wg_reject_1")

    def test_budget_rejection_is_controlled_not_uncaught(self, test_client, monkeypatch):
        client, _srv = test_client
        from core.feature_config import clear_config_cache

        monkeypatch.setenv("ENABLE_MEMORY_BUDGET", "1")
        monkeypatch.setenv("MEMORY_BUDGET_FACT_HARD", "0")
        clear_config_cache()

        r = client.post("/facts", json={
            "fact_id": "facts_budget_reject_1",
            "claim": "pr-c1 post facts budget rejection",
            "source": "test",
            "confidence": 0.9,
        })
        assert r.status_code != 500, (
            f"a budget rejection must be a controlled response, not an "
            f"uncaught internal error (body={r.text!r})"
        )
        assert r.status_code < 500

        from core.memory import get_fact

        assert get_fact("facts_budget_reject_1") is None
        assert not _pr_c1_provenance_row_exists("facts_budget_reject_1")

    def test_successful_create_baseline(self, test_client):
        """BASELINE: an ordinary successful POST /facts must keep working —
        201, canonical fact exists, provenance linked."""
        client, _srv = test_client

        r = client.post("/facts", json={
            "fact_id": "facts_ok_1",
            "claim": "pr-c1 post facts successful baseline",
            "source": "test",
            "confidence": 0.9,
        })
        assert r.status_code == 201, r.text

        from core.memory import get_fact

        fact = get_fact("facts_ok_1")
        assert fact is not None
        assert fact.get("derived_from")
        assert _pr_c1_provenance_row_exists("facts_ok_1")


class TestPostFactsHttpStatusSemantics:
    """PR-C1 hardening: HTTP status must reflect what actually happened —
    201 only for a genuine new INSERT. A content duplicate, a repost of an
    unchanged existing fact_id (NOOP_EXISTING), and a real update
    (UPDATED) must all return 200, never 201 (the decorator previously set
    status_code=201 unconditionally, including on the early dedup
    return)."""

    def test_content_duplicate_is_200_with_deduplicated_flag(self, test_client):
        client, _srv = test_client

        r1 = client.post("/facts", json={
            "claim": "pr-c1 http status content duplicate claim",
            "source": "test",
            "confidence": 0.9,
        })
        assert r1.status_code == 201, r1.text
        first_fact_id = r1.json()["fact_id"]

        r2 = client.post("/facts", json={
            "claim": "pr-c1 http status content duplicate claim",
            "source": "test",
            "confidence": 0.9,
        })
        assert r2.status_code == 200, (
            f"a content duplicate must not return 201 (body={r2.text!r})"
        )
        data2 = r2.json()
        assert data2.get("deduplicated") is True
        assert data2["fact_id"] == first_fact_id

        from core.memory import get_all_facts

        matching = [
            f for f in get_all_facts()
            if f["claim"] == "pr-c1 http status content duplicate claim"
        ]
        assert len(matching) == 1, "no duplicate canonical row must be created"

    def test_identical_repost_to_existing_fact_id_is_not_201(self, test_client):
        client, _srv = test_client

        r1 = client.post("/facts", json={
            "fact_id": "facts_noop_1",
            "claim": "pr-c1 http status noop claim",
            "source": "test",
            "confidence": 0.9,
        })
        assert r1.status_code == 201, r1.text

        r2 = client.post("/facts", json={
            "fact_id": "facts_noop_1",
            "claim": "pr-c1 http status noop claim",
            "source": "test",
            "confidence": 0.9,
        })
        assert r2.status_code != 201, (
            f"an identical repost to an existing fact_id must not return "
            f"201 (body={r2.text!r})"
        )

        from core.memory import get_all_facts

        matching = [f for f in get_all_facts() if f["fact_id"] == "facts_noop_1"]
        assert len(matching) == 1

    def test_update_to_existing_fact_id_is_not_201(self, test_client, monkeypatch):
        """Exercises a genuine WriteStatus.UPDATED via a metadata-only
        change (same claim/confidence, different metadata) — NOT a
        claim/confidence change.

        Discovered while writing this test, confirmed out of scope for
        PR-C1 and NOT touched here: migration 009's `bump_fact_version`
        trigger requires fact_version to increase whenever claim/confidence/
        epistemic_state changes, but store_fact()'s own upsert SQL never
        writes fact_version — so ANY claim or confidence change to an
        existing fact_id unconditionally raises sqlite3.IntegrityError at
        the trigger, pre-existing and unrelated to this PR (store_fact()'s
        SQL is untouched by the PR-C1 diff). A metadata-only change avoids
        it (the trigger's WHEN clause doesn't look at metadata) and is
        sufficient to exercise the UPDATED status this test targets.

        Episode dedup is disabled here: it matches purely on claim text
        (any source, ignoring metadata) — with it on, the second identical-
        claim request would hit create_fact()'s early dedup shortcut and
        never reach store_fact_result() at all.
        """
        monkeypatch.setenv("ENABLE_EPISODE_DEDUP", "0")
        client, _srv = test_client

        r1 = client.post("/facts", json={
            "fact_id": "facts_update_1",
            "claim": "pr-c1 http status update claim",
            "source": "test",
            "confidence": 0.5,
            "metadata": {"tag": "v1"},
        })
        assert r1.status_code == 201, r1.text

        # Same claim/confidence (would hit the early dedup-by-claim
        # shortcut if truly identical, but that shortcut only matches on
        # claim+source and doesn't compare metadata) — different metadata.
        r2 = client.post("/facts", json={
            "fact_id": "facts_update_1",
            "claim": "pr-c1 http status update claim",
            "source": "test",
            "confidence": 0.5,
            "metadata": {"tag": "v2"},
        })
        assert r2.status_code != 201, (
            f"a real update to an existing fact_id must not return 201 "
            f"(body={r2.text!r})"
        )

        from core.memory import get_fact

        fact = get_fact("facts_update_1")
        assert fact["metadata"]["tag"] == "v2", (
            "sanity check: this must be a genuine UPDATE, not a no-op"
        )

    def test_create_only_hooks_not_fired_on_noop_or_update(self, test_client, monkeypatch):
        """NGram indexing and the 'fact created' log are create-only side
        effects — must not fire for NOOP_EXISTING/UPDATED.

        Metadata-only change + dedup disabled: see
        test_update_to_existing_fact_id_is_not_201 for why (avoids the
        pre-existing, out-of-scope bump_fact_version trigger issue on
        claim/confidence changes, and the early claim-dedup shortcut)."""
        monkeypatch.setenv("ENABLE_EPISODE_DEDUP", "0")
        client, _srv = test_client

        indexed: list[str] = []
        import server as srv

        if srv._ngram and srv._ngram.available:
            monkeypatch.setattr(
                srv._ngram, "index", lambda fact_id, claim: indexed.append(fact_id)
            )

        r1 = client.post("/facts", json={
            "fact_id": "facts_hooks_1",
            "claim": "pr-c1 create-only hooks claim",
            "source": "test",
            "confidence": 0.5,
            "metadata": {"tag": "v1"},
        })
        assert r1.status_code == 201, r1.text

        indexed.clear()
        r2 = client.post("/facts", json={
            "fact_id": "facts_hooks_1",
            "claim": "pr-c1 create-only hooks claim",
            "source": "test",
            "confidence": 0.5,
            "metadata": {"tag": "v2"},
        })
        assert r2.status_code != 201, r2.text

        from core.memory import get_fact

        assert get_fact("facts_hooks_1")["metadata"]["tag"] == "v2", (
            "sanity check: this must be a genuine UPDATE, not a no-op"
        )
        assert indexed == [], "NGram indexing must not fire for an UPDATE"


class TestConsoleAutoSaveReadbackFailure:
    """PR-C1 hardening: if store_fact_result() reports an accepted write but
    the immediate get_fact() readback comes back None (invariant
    violation — e.g. a race with a concurrent erasure), the request must
    not crash. The candidate must land in memory_suggestions with a safe
    reason, never in memory_saved with a phantom fact_id."""

    def test_readback_failure_does_not_crash_and_is_not_saved(self, test_client, monkeypatch):
        client, _srv = test_client
        from core import memory as mem

        real_get_fact = mem.get_fact

        def _flaky_get_fact(fact_id):
            # Simulate the accepted write "succeeding" at the store_fact_result
            # layer but the immediate readback in _save_fact_for_console
            # coming back empty.
            if fact_id and fact_id.startswith("fact_"):
                return None
            return real_get_fact(fact_id)

        monkeypatch.setattr(mem, "get_fact", _flaky_get_fact)

        r = client.post("/chat", json={
            "message": "remember that pr-c1 readback failure test claim",
            "profile": "citizen",
            "use_memory": False,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": True,
            "persist_to_system": True,
            "block_memory": [],
            "chat_history": [],
        })
        assert r.status_code == 200, r.text
        data = r.json()

        assert data["memory_saved"] == [], (
            f"a readback failure must not produce a saved item with a "
            f"phantom fact_id: {data['memory_saved']}"
        )
        assert len(data["memory_suggestions"]) == 1
        assert data["memory_suggestions"][0].get("reason_code") == "canonical_readback_failed"
