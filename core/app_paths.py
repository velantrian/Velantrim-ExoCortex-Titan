"""
Единый resolver рантайм-корня приложения.

Несколько модулей (api/web_console.py, core/deployment_profiles.py,
core/umwelt_store.py) читают статические ассеты (static/console/*,
docs/*, config/profiles/*.env) по пути относительно расположения
исходного файла — Path(__file__).resolve().parents[1]. Это работает в
source/editable checkout, но ломается после установки как non-editable
wheel (см. Dockerfile): __file__ тогда указывает в site-packages, а не
в /app, где реально лежат эти ассеты.

VELANTRIM_APP_ROOT делает рантайм-корень явным вместо угадывания по
__file__ или (что ещё хуже) текущей рабочей директории.
"""

from __future__ import annotations

import os
from pathlib import Path


def resolve_app_root(fallback_file: str) -> Path:
    """
    fallback_file: __file__ вызывающего модуля (core/X.py или api/X.py —
    оба на один уровень глубже корня репозитория).

    Порядок:
      1. VELANTRIM_APP_ROOT, если задан — авторитетный (Dockerfile
         устанавливает его в /app).
      2. Path(fallback_file).resolve().parents[1] — репозиторий-корень
         для source/editable checkout.
    Не обращается к текущей рабочей директории.
    """
    env_root = os.getenv("VELANTRIM_APP_ROOT", "").strip()
    if env_root:
        return Path(env_root).resolve()
    return Path(fallback_file).resolve().parents[1]


__all__ = ["resolve_app_root"]
