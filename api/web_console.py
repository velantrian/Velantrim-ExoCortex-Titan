"""
Веб-консоль Velantrim — регистрация маршрутов /console, /ui.
"""

from __future__ import annotations

import hmac
import logging
import os
import time
from pathlib import Path

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse

logger = logging.getLogger(__name__)

def _resolve_app_root() -> Path:
    """
    Root directory that holds static/console/* and the console's docs/*.

    In a source checkout, api/web_console.py lives at <root>/api/, so
    parents[1] is <root>. That relationship breaks once api/ is installed
    as a wheel into site-packages (PR-A): __file__ then points inside
    site-packages, which has no static/ or docs/ next to it — those are
    copied to /app by the Dockerfile instead. VELANTRIM_APP_ROOT makes the
    real runtime root explicit instead of guessing from __file__ or (worse)
    the current working directory, which a request handler must not
    silently depend on.
    """
    env_root = os.getenv("VELANTRIM_APP_ROOT", "").strip()
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[1]


_REPO_ROOT = _resolve_app_root()
_CONSOLE_INDEX = _REPO_ROOT / "static" / "console" / "index.html"
_CONSOLE_ROADMAP = _REPO_ROOT / "static" / "console" / "roadmap.html"
_CONSOLE_RESEARCH = _REPO_ROOT / "static" / "console" / "research.html"
_CONSOLE_RESEARCH_APP = _REPO_ROOT / "static" / "console" / "research-app.html"
_CONSOLE_RESEARCH_APP_JS = _REPO_ROOT / "static" / "console" / "research-app.js"
_CONSOLE_RESEARCH_ROADMAP = _REPO_ROOT / "static" / "console" / "research-roadmap.html"
_CONSOLE_RESEARCH_MODE = _REPO_ROOT / "static" / "console" / "research-mode.html"
_CONSOLE_HELP_DOC = _REPO_ROOT / "docs" / "CONSOLE_BROWSER_TEST.ru.md"
_CONSOLE_RESEARCH_MODE_DOC = _REPO_ROOT / "docs" / "RESEARCH_MODE.ru.md"
_CONSOLE_RESEARCH_ROADMAP_DOC = _REPO_ROOT / "docs" / "EITI_PWA_RESEARCH_ROADMAP.ru.md"


def console_index_path() -> Path:
    return _CONSOLE_INDEX


def console_available() -> bool:
    return _CONSOLE_INDEX.is_file()


def _velantrim_key_analysis(key: str, expected: str) -> dict:
    """Локальный разбор ключа (подсказки без сетевого запроса)."""
    allow_open = os.getenv("VELANTRIM_ALLOW_OPEN", "false").lower() == "true"
    looks_llm = bool(
        key
        and (
            key.startswith("sk-")
            or key.startswith("sk_or-")
            or key.startswith("AIza")
            or key.startswith("sk-ant-")
        )
    )
    if not expected:
        return {
            "auth_required": False,
            "allow_open": allow_open,
            "looks_like_llm_key": looks_llm,
            "matches_env": True,
        }
    if not key:
        return {
            "auth_required": True,
            "allow_open": allow_open,
            "looks_like_llm_key": False,
            "matches_env": False,
            "hint": "Ключ Velantrim не передан. Заполните верхнее поле (VELANTRIM_API_KEY из .env).",
        }
    # SECURITY (audit P1): constant-time compare to avoid a timing side-channel
    # (mirrors server.require_api_key). Both are non-empty str by this point.
    if hmac.compare_digest(key, expected):
        return {
            "auth_required": True,
            "allow_open": allow_open,
            "looks_like_llm_key": looks_llm,
            "matches_env": True,
        }
    hint = (
        "Неверный VELANTRIM_API_KEY. Скопируйте значение из .env "
        "(не ключ DeepSeek/Gemini)."
    )
    if looks_llm:
        hint = (
            "В верхнем поле указан ключ LLM (sk-… / AIza…). "
            "Перенесите его в блок «API LLM», вверху — VELANTRIM_API_KEY из .env."
        )
    return {
        "auth_required": True,
        "allow_open": allow_open,
        "looks_like_llm_key": looks_llm,
        "matches_env": False,
        "hint": hint,
    }


async def _probe_velantrim_api(request: Request, key: str) -> dict:
    """Реальный запрос к защищённым эндпоинтам (как в чате)."""
    base = str(request.base_url).rstrip("/")
    headers: dict[str, str] = {}
    if key:
        headers["X-Api-Key"] = key
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            facts_r = await client.get(
                f"{base}/facts",
                headers=headers,
                params={"limit": 1},
            )
            if facts_r.status_code == 401:
                return {
                    "ok": False,
                    "status": 401,
                    "hint": "Сервер отклонил ключ (401) на GET /facts.",
                }
            if facts_r.status_code >= 400:
                return {
                    "ok": False,
                    "status": facts_r.status_code,
                    "hint": f"GET /facts вернул HTTP {facts_r.status_code}.",
                }
            facts_data = facts_r.json()
            facts_total = int(facts_data.get("total", 0))

            query_r = await client.post(
                f"{base}/query",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "query": "проверка связи",
                    "profile": "citizen",
                    "use_llm": False,
                },
            )
            if query_r.status_code == 401:
                return {
                    "ok": False,
                    "status": 401,
                    "hint": "Сервер отклонил ключ (401) на POST /query — чат недоступен.",
                }
            if query_r.status_code >= 400:
                body = query_r.text[:200]
                return {
                    "ok": False,
                    "status": query_r.status_code,
                    "hint": f"POST /query вернул HTTP {query_r.status_code}: {body}",
                }
            query_data = query_r.json()
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            return {
                "ok": True,
                "status": 200,
                "facts_total": facts_total,
                "latency_ms": latency_ms,
                "query_latency_ms": query_data.get("latency_ms"),
                "hint": (
                    f"Ключ проверен реальными запросами (память + чат). "
                    f"Фактов в памяти: {facts_total}. Можно писать в чат."
                ),
            }
    except httpx.TimeoutException:
        return {
            "ok": False,
            "status": 0,
            "hint": "Таймаут при проверке API. Сервер перегружен или не отвечает.",
        }
    except Exception as exc:
        logger.warning("console auth probe failed: %s", exc)
        return {
            "ok": False,
            "status": 0,
            "hint": f"Ошибка проверки API: {exc}",
        }


def register_console_routes(app) -> bool:
    """
    Подключить UI к FastAPI-приложению.
    Возвращает True, если index.html найден.
    """
    router = APIRouter(include_in_schema=False)

    @router.get("/console")
    @router.get("/console/")
    async def console_page():
        if not console_available():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Консоль не найдена: {_CONSOLE_INDEX}. "
                    "Запускайте uvicorn из папки VELANTRIM_ExoCortex_V8.7_Titan."
                ),
            )
        return FileResponse(
            _CONSOLE_INDEX,
            media_type="text/html; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Velantrim-Console-Build": "llm-openai-55-v24",
            },
        )

    @router.get("/console/help")
    async def console_help():
        """Документация тестовой браузерной консоли (Markdown)."""
        if not _CONSOLE_HELP_DOC.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Нет {_CONSOLE_HELP_DOC}",
            )
        return FileResponse(
            _CONSOLE_HELP_DOC,
            media_type="text/markdown; charset=utf-8",
            headers={"Cache-Control": "no-cache"},
        )

    @router.get("/console/roadmap")
    async def console_roadmap():
        """Интерактивная roadmap-страница для задач по улучшению ядра."""
        if not _CONSOLE_ROADMAP.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Нет {_CONSOLE_ROADMAP}",
            )
        return FileResponse(
            _CONSOLE_ROADMAP,
            media_type="text/html; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    @router.get("/console/research")
    async def console_research():
        """Compact Research Mode overview page."""
        if not _CONSOLE_RESEARCH.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Нет {_CONSOLE_RESEARCH}",
            )
        return FileResponse(
            _CONSOLE_RESEARCH,
            media_type="text/html; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    @router.get("/console/research-app")
    async def console_research_app():
        """Interactive browser Research App with local experimental memory."""
        if not _CONSOLE_RESEARCH_APP.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Нет {_CONSOLE_RESEARCH_APP}",
            )
        return FileResponse(
            _CONSOLE_RESEARCH_APP,
            media_type="text/html; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    @router.get("/console/research-app.js")
    async def console_research_app_js():
        """JavaScript bundle for the browser Research App."""
        if not _CONSOLE_RESEARCH_APP_JS.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Нет {_CONSOLE_RESEARCH_APP_JS}",
            )
        return FileResponse(
            _CONSOLE_RESEARCH_APP_JS,
            media_type="application/javascript; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    @router.get("/console/research-mode")
    async def console_research_mode():
        """Compatibility URL for older docs."""
        return RedirectResponse(url="/console/research?v=2")

    @router.get("/console/research-roadmap")
    async def console_research_roadmap():
        """Compact Research PWA roadmap page."""
        if not _CONSOLE_RESEARCH_ROADMAP.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Нет {_CONSOLE_RESEARCH_ROADMAP}",
            )
        return FileResponse(
            _CONSOLE_RESEARCH_ROADMAP,
            media_type="text/html; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    @router.get("/console/research-mode.md")
    async def console_research_mode_markdown():
        """Raw Markdown source for Research Mode overview."""
        if not _CONSOLE_RESEARCH_MODE_DOC.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Нет {_CONSOLE_RESEARCH_MODE_DOC}",
            )
        return FileResponse(
            _CONSOLE_RESEARCH_MODE_DOC,
            media_type="text/markdown; charset=utf-8",
            headers={"Cache-Control": "no-cache"},
        )

    @router.get("/console/research-roadmap.md")
    async def console_research_roadmap_markdown():
        """Raw Markdown source for Research PWA roadmap."""
        if not _CONSOLE_RESEARCH_ROADMAP_DOC.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Нет {_CONSOLE_RESEARCH_ROADMAP_DOC}",
            )
        return FileResponse(
            _CONSOLE_RESEARCH_ROADMAP_DOC,
            media_type="text/markdown; charset=utf-8",
            headers={"Cache-Control": "no-cache"},
        )

    @router.get("/ui")
    async def ui_alias():
        return RedirectResponse(url="/console/")

    @router.get("/velantrim")
    async def velantrim_alias():
        """Запасной URL, если /console перехватывается прокси."""
        return RedirectResponse(url="/console/")

    @router.get("/debug/console")
    async def debug_console():
        api_key = os.getenv("VELANTRIM_API_KEY", "")
        allow_open = os.getenv("VELANTRIM_ALLOW_OPEN", "false").lower() == "true"
        return {
            "available": console_available(),
            "index_path": str(_CONSOLE_INDEX),
            "repo_root": str(_REPO_ROOT),
            "urls": [
                "/console/",
                "/console",
                "/console/roadmap",
                "/console/research",
                "/console/research-app",
                "/console/research-app.js",
                "/console/research-roadmap",
                "/console/research-mode",
                "/console/research-mode.md",
                "/console/research-roadmap.md",
                "/ui",
                "/velantrim",
            ],
            "features": {
                "llm_router": True,
                "chat_endpoint": True,
                "dialogue_essence_sse": True,
                "console_help": "/console/help",
                "console_roadmap": "/console/roadmap",
                "console_research": "/console/research",
                "console_research_app": "/console/research-app",
                "console_research_app_js": "/console/research-app.js",
                "console_research_roadmap": "/console/research-roadmap",
                "console_research_mode": "/console/research-mode",
                "console_research_mode_markdown": "/console/research-mode.md",
                "console_research_roadmap_markdown": "/console/research-roadmap.md",
                "llm_test": "POST /console/llm/test",
                "llm_providers": "GET /console/llm/providers",
            },
            "auth": {
                "required": bool(api_key),
                "allow_open": allow_open,
            },
            "hint": "Если LLM не работает — перезапустите: scripts/start_console.ps1",
        }

    @router.get("/console/bootstrap")
    async def console_bootstrap(request: Request):
        """
        Настройки консоли для браузера (без LLM-ключей).
        На localhost отдаёт VELANTRIM_API_KEY для верхнего поля — только loopback.
        """
        api_key = os.getenv("VELANTRIM_API_KEY", "")
        allow_open = os.getenv("VELANTRIM_ALLOW_OPEN", "false").lower() == "true"
        client_host = (request.client.host if request.client else "") or ""
        is_local = client_host in ("127.0.0.1", "::1", "localhost")

        payload: dict = {
            "auth_required": bool(api_key),
            "allow_open": allow_open,
            "is_local": is_local,
            "console_api_key": None,
            "hint": (
                "Два разных ключа: (1) VELANTRIM_API_KEY — верхнее поле; "
                "(2) DeepSeek/Gemini/OpenAI — блок «API LLM» ниже."
            ),
        }
        # AUDIT-FIX P1: NEVER return the server key over HTTP. request.client.host
        # reflects the immediate peer — behind a reverse proxy (uvicorn --host 0.0.0.0)
        # it is loopback, so an "is_local" gate would leak VELANTRIM_API_KEY to every
        # remote client. console_api_key therefore stays None; localhost users paste
        # the key from .env into the top field manually.
        return payload

    @router.get("/console/auth/check")
    async def console_auth_check(x_api_key: str = Header(default="")):
        """Быстрая локальная проверка (без запроса к /facts)."""
        expected = os.getenv("VELANTRIM_API_KEY", "")
        key = (x_api_key or "").strip()
        analysis = _velantrim_key_analysis(key, expected)
        valid = analysis.get("matches_env", False) or not analysis.get("auth_required")
        return {
            "valid": valid,
            "probed": False,
            "chat_ready": False,
            **analysis,
            "hint": analysis.get("hint")
            or ("Ключ совпадает с .env" if valid else "Ключ не совпадает с VELANTRIM_API_KEY на сервере."),
        }

    @router.get("/console/auth/verify")
    async def console_auth_verify(request: Request, x_api_key: str = Header(default="")):
        """
        Полная проверка: совпадение с .env + реальные GET /facts и POST /query
        (тот же X-Api-Key, что использует чат).
        """
        expected = os.getenv("VELANTRIM_API_KEY", "")
        key = (x_api_key or "").strip()
        analysis = _velantrim_key_analysis(key, expected)

        if analysis.get("looks_like_llm_key"):
            return {
                "valid": False,
                "probed": False,
                "chat_ready": False,
                **analysis,
            }

        if analysis.get("auth_required") and not analysis.get("matches_env"):
            return {
                "valid": False,
                "probed": False,
                "chat_ready": False,
                **analysis,
            }

        if not analysis.get("auth_required"):
            probe = await _probe_velantrim_api(request, key)
            ok = probe.get("ok", False)
            return {
                "valid": ok,
                "probed": True,
                "chat_ready": ok,
                **analysis,
                **probe,
                "hint": probe.get("hint") if ok else probe.get("hint"),
            }

        probe = await _probe_velantrim_api(request, key)
        ok = probe.get("ok", False)
        return {
            "valid": ok,
            "probed": True,
            "chat_ready": ok,
            **analysis,
            "facts_total": probe.get("facts_total"),
            "latency_ms": probe.get("latency_ms"),
            "query_latency_ms": probe.get("query_latency_ms"),
            "hint": probe.get("hint", "Проверка не удалась."),
        }

    app.include_router(router)

    if console_available():
        logger.info("Web console: /console/  (файл %s)", _CONSOLE_INDEX)
    else:
        logger.warning("Web console: файл не найден — %s", _CONSOLE_INDEX)
    return console_available()


__all__ = ["console_available", "console_index_path", "register_console_routes"]
