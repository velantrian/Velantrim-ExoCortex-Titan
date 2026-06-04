"""
Тесты wiring Working Notebook в pipeline (вариант 2):
pipeline.run_with_notebook аддитивно добавляет директиву «думай, как я» рядом с ответом.
run() застаблен (monkeypatch), чтобы не грузить retrieval/модель.
"""


def test_attaches_directive_when_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_WORKING_NOTEBOOK", "true")
    import core.pipeline as pl
    from core.working_notebook import reset_notebooks
    reset_notebooks()
    monkeypatch.setattr(pl, "run", lambda q, **k: {"answer": "stub", "facts": []})
    res = pl.run_with_notebook("Хочу дом, бюджет ограничен 9 млн", session_id="s1")
    assert "notebook_directive" in res
    assert "USER_STATED" in res["notebook_directive"]
    assert "notebook" in res and res["notebook"]["session_id"] == "s1"
    assert res["answer"] == "stub"          # ответ run() не тронут


def test_off_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_WORKING_NOTEBOOK", raising=False)
    import core.pipeline as pl
    monkeypatch.setattr(pl, "run", lambda q, **k: {"answer": "stub"})
    res = pl.run_with_notebook("Хочу дом", session_id="s2")
    assert "notebook_directive" not in res   # флаг выкл → ничего не добавлено


def test_no_session_no_directive(monkeypatch):
    monkeypatch.setenv("ENABLE_WORKING_NOTEBOOK", "true")
    import core.pipeline as pl
    monkeypatch.setattr(pl, "run", lambda q, **k: {"answer": "stub"})
    res = pl.run_with_notebook("Хочу дом")   # без session_id
    assert "notebook_directive" not in res


def test_directive_persists_across_turns(monkeypatch):
    monkeypatch.setenv("ENABLE_WORKING_NOTEBOOK", "true")
    import core.pipeline as pl
    from core.working_notebook import reset_notebooks
    reset_notebooks()
    monkeypatch.setattr(pl, "run", lambda q, **k: {"answer": "stub"})
    pl.run_with_notebook("Хочу построить дом", session_id="s3")
    res2 = pl.run_with_notebook("Бюджет ограничен 9 млн", session_id="s3")
    nb = res2["notebook"]
    assert nb["turn"] == 2                    # две реплики накопились в одной сессии
    types = {b["type"] for b in nb["blocks"]}
    assert "goal" in types and "constraint" in types
