"""
core/__init__.py — Velantrim ExoCortex public API
==================================================
Единственный источник истины для __version__.

Используем importlib.metadata.version() вместо хардкода — версия читается
из pyproject.toml. Это закрывает класс багов «разные версии в разных файлах»,
который был в проекте до v8.4.0 (README v8.5.0, pyproject 8.3.0,
INVARIANTS v8.4.4 — расхождение на трёх уровнях).

Использование:
    from core import __version__
    print(f"Velantrim {__version__}")

    # или из любого файла
    import core
    if core.__version__ < "9.0.0":
        ...

AUDIT-FIX v8.4.0: до этого релиза core/__init__.py был пустой (0 байт).
"""

from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("velantrim-exocortex-crystal")
except _PackageNotFoundError:
    # Fallback для случая когда пакет не установлен (development clone)
    # Должно совпадать с pyproject.toml — но обычно использует metadata выше.
    __version__ = "8.4.0+dev"

__all__ = [
    "__version__",
]

# Ленивый re-export ключевых классов: ничего не импортируем при `import core`,
# чтобы избежать circular imports и медленного старта. Используй явные импорты:
#   from core.memory import store_fact, get_fact, transition_esm
#   from core.truth_gate import TruthGate, CognitiveMode
#   from core.pipeline import run
