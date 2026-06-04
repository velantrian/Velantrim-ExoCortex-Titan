"""
Тесты Working Notebook (core/working_notebook.py, RFC-0081 P0).
Экстракция блоков, turn-based затухание, реактивация (mention boost), директива,
инвариант truth_status=USER_STATED.
"""
from core.working_notebook import (
    BlockType,
    WorkingNotebook,
    extract_blocks,
    is_working_notebook_enabled,
)


def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_WORKING_NOTEBOOK", raising=False)
    assert is_working_notebook_enabled() is False


# ── экстракция ──────────────────────────────────────────────────────────────────

def test_extract_classifies_types():
    blocks = extract_blocks("Хочу построить дом, бюджет ограничен 9 млн, важно тепло", turn=1)
    types = {b.type for b in blocks}
    assert BlockType.GOAL.value in types
    assert BlockType.CONSTRAINT.value in types       # «бюджет … млн»
    assert BlockType.PRIORITY.value in types         # «важно»


def test_blocks_are_user_stated_not_facts():
    for b in extract_blocks("Хочу построить дом", turn=1):
        assert b.truth_status == "USER_STATED"        # мысль пользователя, не факт мира


# ── core_goal ──────────────────────────────────────────────────────────────────

def test_core_goal_set_from_goal_block():
    nb = WorkingNotebook()
    nb.update_from_message("Хочу построить экономичный дом, бюджет ограничен 9 млн")
    assert "дом" in nb.core_goal.lower()


# ── затухание (Decay) ────────────────────────────────────────────────────────────

def test_block_decays_when_untouched():
    nb = WorkingNotebook()
    nb.update_from_message("Хочу построить дом")
    gid = next(b.id for b in nb.blocks.values() if b.type == "goal")
    start = nb.blocks[gid].current_score
    for _ in range(20):
        nb.update_from_message("Поговорим о погоде сегодня вечером")
    decayed = nb.blocks[gid]
    assert decayed.current_score < start            # тускнеет
    assert decayed.state != "ACTIVE"                # ушёл из фокуса
    assert decayed.current_score > 0.0              # но не исчез (внимание, не истина)


def test_constraint_decays_slower_than_topic():
    nb = WorkingNotebook()
    nb.update_from_message("Бюджет ограничен 9 млн рублей")     # constraint (λ 0.03)
    nb.update_from_message("Сегодня обсуждаем синюю краску")    # topic (λ 0.12)
    cid = next(b.id for b in nb.blocks.values() if b.type == "constraint")
    tid = next(b.id for b in nb.blocks.values() if b.type == "topic")
    for _ in range(10):
        nb.update_from_message("Совсем другая отвлечённая тема разговора")
    assert nb.blocks[cid].current_score > nb.blocks[tid].current_score


# ── реактивация (mention boost) ──────────────────────────────────────────────────

def test_reactivation_brings_block_back():
    nb = WorkingNotebook()
    nb.update_from_message("Хочу построить дом")
    gid = next(b.id for b in nb.blocks.values() if b.type == "goal")
    for _ in range(20):
        nb.update_from_message("Поговорим о погоде сегодня вечером")
    assert nb.blocks[gid].state in ("COLD", "DORMANT")    # остыл
    before_access = nb.blocks[gid].access_count
    nb.update_from_message("Вернёмся к делу, хочу построить дом")
    back = nb.blocks[gid]
    assert back.state in ("ACTIVE", "WARM")               # воскрес
    assert back.missed_turns == 0
    assert back.access_count > before_access


# ── директива ──────────────────────────────────────────────────────────────────

def test_directive_includes_goal_constraints_and_user_stated():
    nb = WorkingNotebook()
    nb.update_from_message("Хочу построить экономичный дом, бюджет ограничен 9 млн")
    d = nb.directive()
    assert "USER_STATED" in d
    assert "Ограничения" in d                  # constraint попал
    assert "дом" in d.lower()                   # core_goal в директиве
