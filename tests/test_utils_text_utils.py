"""Packaging regression test for utils/text_utils.py.

utils/ is a top-level module (not under core/ or api/) that
core/affordance_linker.py and core/living_context.py import as
`utils.text_utils` at runtime. Until PR-A's follow-up it had no
__init__.py and wasn't in pyproject.toml's packages.find include list,
so it was silently absent from any non-editable install (Docker) —
ModuleNotFoundError the moment affordance extraction or living-context
lemmatization actually ran. See pyproject.toml [tool.setuptools.packages.find].
"""

import utils
from utils.text_utils import is_morphology_available, tokenize, tokenize_lemmatized


def test_utils_is_a_real_package():
    assert utils.__file__ is not None


def test_tokenize_basic():
    assert tokenize("Дерево растёт в лесу") == ["дерево", "растёт", "лесу"]


def test_tokenize_lemmatized_does_not_raise():
    # Falls back to plain tokenize() if pymorphy2/pymorphy3 isn't available —
    # either way, this must not raise.
    result = tokenize_lemmatized("Птицы вьют гнёзда")
    assert isinstance(result, list)
    assert len(result) >= 1


def test_is_morphology_available_returns_bool():
    assert isinstance(is_morphology_available(), bool)


def test_affordance_linker_imports_utils_text_utils_successfully():
    """Exercises AffordanceLinker.extract(), which does
    `from utils.text_utils import tokenize, tokenize_lemmatized`
    (core/affordance_linker.py:169) — this raised ModuleNotFoundError in
    the container before utils/ was added to the wheel."""
    from core.affordance_linker import AffordanceLinker

    result = AffordanceLinker().extract("fact-1", "Дерево растёт в лесу")
    assert result.fact_id == "fact-1"
