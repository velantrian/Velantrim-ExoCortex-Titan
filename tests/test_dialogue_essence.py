# tests/test_dialogue_essence.py
from core.dialogue_essence import build_essence_snapshot


def test_essence_read_name_and_topic():
    snap = build_essence_snapshot(
        "Меня зовут Руслан, живу в Вене. Запомни это.",
        lang="ru",
        phase="read",
    )
    assert snap["intent"] == "remember"
    assert any(n["kind"] == "person" and "Руслан" in n["label"] for n in snap["nodes"])
    assert snap["edges"]


def test_essence_commit_phase():
    snap = build_essence_snapshot(
        "Мне 40 лет",
        lang="ru",
        phase="commit",
        memory_saved=[{"claim": "Мне 40 лет", "memory_store": "block"}],
    )
    assert any(n["status"] == "committed" for n in snap["nodes"])
