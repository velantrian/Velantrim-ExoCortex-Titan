"""
Страж импортов: КАЖДЫЙ модуль core/* должен импортироваться.

Зачем: `core/epistemic_pipeline.py` месяцами падал на импорте (`trace_summary`
не существовал в `core/trace.py`) и тянул за собой `core/concept_promote.py` —
а smoke-тест импортов был курирован так, что обходил именно эти два модуля.
Этот тест перечисляет модули с диска (без импорта при сборе) и импортирует каждый.

Правило различения «наш баг» vs «нет опциональной зависимости»:
  • ModuleNotFoundError на СТОРОННИЙ пакет (pypdf2, numpy, …) → skip (ядро на stdlib).
  • ModuleNotFoundError на НАШ пакет (core/api/…) → падение (реальный баг).
  • Любой иной ImportError (напр. «cannot import name X from core.Y»),
    NameError, SyntaxError → падение (именно так ловится баг класса trace_summary).
"""

from __future__ import annotations

import importlib
import os

import pytest

import core

_CORE_DIR = os.path.dirname(core.__file__)
_REPO_ROOT = os.path.dirname(_CORE_DIR)
_FIRST_PARTY = {"core", "api", "app", "localmind", "utils", "server"}


def _core_modules() -> list[str]:
    names: list[str] = []
    for root, _dirs, files in os.walk(_CORE_DIR):
        if "__pycache__" in root:
            continue
        for f in files:
            if not f.endswith(".py") or f.startswith("_"):
                continue
            rel = os.path.relpath(os.path.join(root, f), _REPO_ROOT)
            names.append(rel[:-3].replace(os.sep, ".").replace("/", "."))
    return sorted(names)


_MODULES = _core_modules()


def test_found_modules_sanity():
    # Защита от пустого параметра (если walk сломается — тест не должен «зеленеть» молча)
    assert len(_MODULES) > 100, f"подозрительно мало модулей core: {len(_MODULES)}"


@pytest.mark.parametrize("modname", _MODULES)
def test_core_module_imports(modname: str):
    try:
        importlib.import_module(modname)
    except ModuleNotFoundError as exc:
        top = (exc.name or "").split(".")[0]
        if top in _FIRST_PARTY:
            raise  # отсутствует НАШ модуль → реальный баг
        pytest.skip(f"опциональная сторонняя зависимость отсутствует: {exc.name}")
