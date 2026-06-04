"""Telegram → L0/L1 ingest (Спринт 2.6)."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mem_db(tmp_path, monkeypatch):
    import core.memory as mem

    db = str(tmp_path / "tg.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    monkeypatch.setenv("ENABLE_TELEGRAM_INGEST", "1")
    monkeypatch.setenv("ENABLE_COGNITIVE_STORE", "0")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    monkeypatch.setattr(mem, "_L0", store._l0)
    yield store
    clear_config_cache()


class TestTelegramIngestCore:
    def test_ingest_creates_raw_and_fact(self, mem_db):
        from app.telegram_ingest import ingest_telegram_message
        from core.memory import get_fact

        r = ingest_telegram_message(
            "Velantrim запомнил сообщение из Telegram",
            chat_id="1001",
            user_id="42",
            message_id="99",
            username="velan",
        )
        assert r["ok"] is True
        assert r["raw_id"].startswith("raw_") or r.get("via") == "cognitive_store"
        fact = get_fact(r["fact_id"])
        assert fact is not None
        assert fact["metadata"]["channel"] == "telegram"
        assert fact.get("derived_from") or r.get("raw_id")

    def test_ingest_via_cognitive_store(self, mem_db, monkeypatch):
        monkeypatch.setenv("ENABLE_COGNITIVE_STORE", "1")
        from core.feature_config import clear_config_cache

        clear_config_cache()
        from app.telegram_ingest import ingest_telegram_message

        r = ingest_telegram_message("через CognitiveFactStore", chat_id="cs")
        assert r.get("via") == "cognitive_store"
        assert r["fact_id"].startswith("tg_")

    def test_parse_update(self):
        from app.telegram_ingest import parse_telegram_update

        upd = {
            "update_id": 1,
            "message": {
                "message_id": 5,
                "text": "привет память",
                "chat": {"id": -100},
                "from": {"id": 7, "username": "u"},
            },
        }
        p = parse_telegram_update(upd)
        assert p["text"] == "привет память"
        assert p["chat_id"] == -100


class TestTelegramAPI:
    @pytest.fixture
    def client(self, mem_db, monkeypatch):
        monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
        monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
        monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
        monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
        for mod in list(sys.modules.keys()):
            if mod.startswith(("server", "core.", "app.")):
                del sys.modules[mod]
        from fastapi.testclient import TestClient

        import server as srv

        with TestClient(srv.app) as c:
            c.headers.update({"X-Api-Key": "test-key"})
            yield c

    def test_ingest_endpoint(self, client):
        r = client.post(
            "/telegram/ingest",
            json={
                "text": "Тестовое сообщение для L0",
                "chat_id": "test_chat",
                "message_id": "m1",
            },
        )
        assert r.status_code == 201
        assert r.json()["fact_id"].startswith("tg_")

    def test_webhook_no_text(self, client, monkeypatch):
        # секрет задан и передан → проходим до пути «нет текста»
        monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "sec")
        r = client.post(
            "/telegram/webhook", json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "sec"},
        )
        assert r.status_code == 200
        assert r.json().get("skipped")

    def test_webhook_rejects_without_secret(self, client, monkeypatch):
        # SECURITY (audit fix): fail-closed — без заданного секрета вебхук отвергает анонимов
        monkeypatch.delenv("TELEGRAM_WEBHOOK_SECRET", raising=False)
        r = client.post("/telegram/webhook", json={"update_id": 1})
        assert r.status_code == 403

    def test_webhook_with_message(self, client, monkeypatch):
        monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "sec")
        r = client.post(
            "/telegram/webhook",
            json={
                "message": {
                    "message_id": 2,
                    "text": "webhook текст",
                    "chat": {"id": 55},
                    "from": {"id": 1},
                }
            },
            headers={"X-Telegram-Bot-Api-Secret-Token": "sec"},
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True
