# server.py
# VELANTRIM V8.7 Titan — HTTP API Server
# v8.7.0
#
# Запуск:
#   pip install fastapi uvicorn[standard] python-dotenv httpx
#   uvicorn server:app --host 0.0.0.0 --port 8000 --reload
#
# Переменные окружения (.env):
#   VELANTRIM_API_KEY=your-secret-key        # обязательно
#   LLM_PROVIDER=anthropic                   # anthropic | openai | none
#   ANTHROPIC_API_KEY=sk-ant-...             # если provider=anthropic
#   OPENAI_API_KEY=sk-...                    # если provider=openai
#   OPENAI_MODEL=gpt-4o                      # опционально
#   ANTHROPIC_MODEL=claude-sonnet-4-20250514 # опционально
#   VELANTRIM_DB_PATH=./data/velantrim_house.db # путь к БД
#   VELANTRIM_NGRAM_DB=./data/ngram_house.db    # путь к NGram индексу
#   LOG_LEVEL=INFO                           # DEBUG | INFO | WARNING
#   CORS_ORIGINS=*                           # разрешённые origins
#   SLEEP_WORKER_ENABLED=true                # включить SleepTimeWorker

import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from pydantic import BaseModel, Field, field_validator

load_dotenv()

# ─── Логирование ──────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("velantrim.server")

# ─── Конфигурация ─────────────────────────────────────────────────────────────
API_KEY          = os.getenv("VELANTRIM_API_KEY", "")
LLM_PROVIDER     = os.getenv("LLM_PROVIDER", "none").lower()
ANTHROPIC_KEY    = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL  = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
OPENAI_KEY       = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL     = os.getenv("OPENAI_MODEL", "gpt-4o")
DB_PATH          = os.getenv("VELANTRIM_DB_PATH", "./data/velantrim_house.db")
NGRAM_DB         = os.getenv("VELANTRIM_NGRAM_DB", "./data/ngram_house.db")
SLEEP_ENABLED    = os.getenv("SLEEP_WORKER_ENABLED", "true").lower() == "true"
# AUDIT-FIX v8.4.0: CORS дефолт — пустой список (CORS отключён), не "*"
# С credentials=True старый дефолт "*" нарушал CORS spec.
CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "").strip()
CORS_ORIGINS     = [o.strip() for o in CORS_ORIGINS_RAW.split(",") if o.strip()] if CORS_ORIGINS_RAW else []
# Если явно "*" — отключаем credentials, иначе браузеры отклонят preflight
CORS_ALLOW_CREDENTIALS = "*" not in CORS_ORIGINS
# AUDIT-FIX v8.4.0: разрешаем "open mode" только через явный ENV — иначе
# забытый VELANTRIM_API_KEY = открытый сервер.
ALLOW_NO_API_KEY = os.getenv("VELANTRIM_ALLOW_OPEN", "false").lower() == "true"

_profile_boot = (os.getenv("VELANTRIM_PROFILE") or "").strip().lower()
if _profile_boot:
    try:
        from core.deployment_profiles import load_profile_env

        load_profile_env(_profile_boot)
        API_KEY = os.getenv("VELANTRIM_API_KEY", "")
        ALLOW_NO_API_KEY = os.getenv("VELANTRIM_ALLOW_OPEN", "false").lower() == "true"
        LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower()
        SLEEP_ENABLED = os.getenv("SLEEP_WORKER_ENABLED", "true").lower() == "true"
    except Exception as _prof_exc:
        logger.warning("VELANTRIM_PROFILE=%s не загружен: %s", _profile_boot, _prof_exc)

if not API_KEY:
    if not ALLOW_NO_API_KEY:
        raise RuntimeError(
            "VELANTRIM_API_KEY обязателен. "
            "Для development без auth установи VELANTRIM_ALLOW_OPEN=true (НЕ для production!)"
        )
    logger.warning(
        "⚠️  VELANTRIM_API_KEY не задан — сервер открыт без аутентификации (development-режим). "
        "В production это БАГ. Установи VELANTRIM_API_KEY."
    )

# ─── Импорт Velantrim ─────────────────────────────────────────────────────────
from core.memory import (
    _GLOBAL_STORE,
    ImmutableStateError,
    SQLiteGraphStore,
    find_fact_id_by_episode_hash,
    get_all_facts,
    get_fact,
    get_fact_at,
    invalidate_edge,
    link_raw_to_fact,
    store_fact,
    store_facts_batch,
    store_raw_text,
    transition_esm,
)
from core.mhi import MHICalculator, MHIStatus, check_mhi
from core.pipeline import run as pipeline_run

try:
    from core.ngram_index import NGramIndex, set_global_ngram
    _ngram = NGramIndex(NGRAM_DB)
    # AUDIT-FIX v8.4.0: регистрируем как глобальный singleton — теперь pipeline
    # тоже пишет в эту же БД (раньше pipeline имел свой _GLOBAL_NGRAM с
    # хардкоженным путём → две разные БД, факты не находились).
    set_global_ngram(_ngram)
    logger.info("NGramIndex: %s", "✅ FTS5 доступен" if _ngram.available else "⚠️ FTS5 недоступен")
except Exception as exc:
    _ngram = None
    logger.warning("NGramIndex недоступен: %s", exc)

try:
    from core.sleep_time_worker import SleepTimeWorker, make_sleep_time_worker
    _sleep_worker_class = SleepTimeWorker
    _sleep_worker_available = True
except Exception as exc:
    _sleep_worker_available = False
    logger.warning("SleepTimeWorker недоступен: %s", exc)

# ─── Глобальные объекты ───────────────────────────────────────────────────────
_store: SQLiteGraphStore = _GLOBAL_STORE
_sleep_worker: Optional["SleepTimeWorker"] = None
_startup_time = time.time()

# MHI кэш — пересчёт не чаще раз в 60 секунд (236 инструкций на каждый вызов)
_mhi_cache: dict[str, Any] = {"data": None, "at": 0.0}
_MHI_TTL = 60.0  # секунд


# ─── LLM клиент ───────────────────────────────────────────────────────────────

def _env_llm_config():
    """Конфиг LLM из переменных окружения (без ключей в логах)."""
    from core.llm_router import LlmCallConfig

    prov = LLM_PROVIDER
    if prov == "anthropic" and ANTHROPIC_KEY:
        return LlmCallConfig(provider="anthropic", api_key=ANTHROPIC_KEY, model=ANTHROPIC_MODEL)
    if prov == "openai" and OPENAI_KEY:
        return LlmCallConfig(provider="openai", api_key=OPENAI_KEY, model=OPENAI_MODEL)
    deepseek = os.getenv("DEEPSEEK_API_KEY", "")
    if prov == "deepseek" and deepseek:
        return LlmCallConfig(
            provider="deepseek",
            api_key=deepseek,
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        )
    gemini = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if prov == "gemini" and gemini:
        return LlmCallConfig(
            provider="gemini",
            api_key=gemini,
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        )
    or_key = os.getenv("OPENROUTER_API_KEY", "")
    if prov == "openrouter" and or_key:
        return LlmCallConfig(
            provider="openrouter",
            api_key=or_key,
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        )
    return None


async def _llm_generate(
    prompt: str,
    system: str = "",
    *,
    override=None,
) -> str:
    """
    Вызвать LLM API для генерации ответа.
    override — LlmCallConfig из запроса консоли (приоритет над ENV).
    """
    from core.llm_router import chat_complete

    cfg = override
    if cfg is None:
        cfg = _env_llm_config()

    if cfg and cfg.api_key:
        async def _do() -> str:
            return await chat_complete(cfg, prompt, system)

        return await _with_llm_circuit(_do)

    # legacy fallback (старые ENV anthropic/openai без llm_router)
    if LLM_PROVIDER == "anthropic" and ANTHROPIC_KEY:
        return await _anthropic_complete(prompt, system)
    if LLM_PROVIDER == "openai" and OPENAI_KEY:
        return await _openai_complete(prompt, system)
    raise ValueError(
        "LLM не настроен: укажите llm_provider + llm_api_key в консоли "
        "или задайте LLM_PROVIDER и ключ в .env"
    )


def _resolve_llm_config_for_request(req: "QueryRequest"):
    """Конфиг LLM: сначала ключ из запроса, иначе .env."""
    override = _llm_config_from_request(req)
    if override:
        return override
    return _env_llm_config()


async def _with_llm_circuit(coro_factory):
    """Обёртка CircuitBreaker для LLM (Titan HYPERIA-8)."""
    from core.feature_config import get_config

    if not get_config().app.enable_circuit_breaker:
        return await coro_factory()

    from core.circuit_breaker import CircuitBreakerOpenError, get_circuit_breaker

    try:
        return await get_circuit_breaker("llm").call(coro_factory)
    except CircuitBreakerOpenError:
        logger.warning("LLM CircuitBreaker OPEN — degraded mode (без API)")
        raise


async def _anthropic_complete(prompt: str, system: str = "") -> str:
    async def _do() -> str:
        messages = [{"role": "user", "content": prompt}]
        body: dict[str, Any] = {
            "model":      ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "messages":   messages,
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key":         ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type":      "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    return await _with_llm_circuit(_do)


async def _openai_complete(prompt: str, system: str = "") -> str:
    async def _do() -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_KEY}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":      OPENAI_MODEL,
                    "messages":   messages,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    return await _with_llm_circuit(_do)


def _build_system_prompt(
    facts: list[dict],
    *,
    lens_instructions: str | None = None,
) -> str:
    """Собрать system prompt из верифицированных фактов для LLM."""
    if not facts:
        base = "Ты — Velantrim ExoCortex. Отвечай честно. Если не знаешь — скажи."
        if lens_instructions:
            return f"{base}\n\n{lens_instructions}"
        return base

    facts_text = "\n".join(
        f"- [{f.get('source', '?')} | conf={f.get('confidence', 0):.2f}] {f.get('claim', '')}"
        for f in facts
    )
    prompt = (
        "Ты — Velantrim ExoCortex, AI-агент с верифицированной памятью.\n"
        "Отвечай ТОЛЬКО на основе следующих фактов из памяти. "
        "Если факты не содержат ответа — скажи об этом честно.\n\n"
        f"Верифицированные факты:\n{facts_text}"
    )
    if lens_instructions:
        prompt += f"\n\n{lens_instructions}"
    return prompt


# ─── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _sleep_worker

    logger.info("🚀 Velantrim Server запускается...")
    logger.info("   DB: %s", DB_PATH)
    logger.info("   LLM: %s (%s)", LLM_PROVIDER,
                ANTHROPIC_MODEL if LLM_PROVIDER == "anthropic" else OPENAI_MODEL)

    # FIX v8.5.3 (Claude audit + DeepSeek/Qwen consensus): автоприменение
    # миграций 008/009/010 при старте. Раньше миграции существовали как
    # SQL-файлы, но никто их не запускал — на чистой машине таблицы
    # relations, memory_events, l0_raw_memory физически отсутствовали,
    # что ломало Patch 13 graph, TruthKernel triggers, L0 Raw Memory.
    # Идемпотентно через PRAGMA user_version — на уже мигрированной БД
    # ничего не делает.
    try:
        from pathlib import Path

        from scripts.apply_migrations import apply_migrations
        applied = await asyncio.to_thread(
            apply_migrations, Path(DB_PATH).resolve()
        )
        if applied:
            logger.info("   Migrations: применены %s", ", ".join(applied))
        else:
            logger.info("   Migrations: БД актуальна")
    except Exception as exc:
        # Падаем громко: лучше отказ при старте, чем работа с битой схемой.
        logger.error("   Migrations: ❌ FATAL — %s", exc)
        raise

    # Перестроить NGram индекс при старте — только Validated факты
    # AUDIT-FIX v8.4.0: фильтр Validated — раньше индексировались Collapsed/Deprecated
    # тоже, что при миллионе фактов делало startup минутами.
    if _ngram and _ngram.available:
        all_validated = await asyncio.to_thread(get_all_facts, "Validated")
        count = _ngram.rebuild(all_validated)
        logger.info("   NGramIndex: перестроен (%d validated фактов)", count)

    # SleepTimeWorker
    if SLEEP_ENABLED and _sleep_worker_available:
        try:
            llm_fn = None
            if LLM_PROVIDER != "none":
                # AUDIT-FIX v8.4.0: передаём async-функцию напрямую.
                # SleepTimeWorker._llm_complete теперь умеет распознавать
                # async-callable через inspect.iscoroutine.
                llm_fn = _llm_generate
            # AUDIT-FIX v8.4.0: убран параметр store=_store — make_sleep_time_worker
            # его не принимает (см. sleep_time_worker.py:672). До v8.4.0 это
            # вызывало TypeError на старте, обёрнутый в try/except → SleepTimeWorker
            # тихо не запускался, /agent/notebook возвращал 503.
            _sleep_worker = make_sleep_time_worker(
                llm_fn=llm_fn,
            )
            await _sleep_worker.start()
            logger.info("   SleepTimeWorker: ✅ запущен")
        except Exception as exc:
            logger.warning("   SleepTimeWorker: ❌ не удалось запустить: %s", exc)

    try:
        from core.exocortex_hooks import register_exocortex_handlers
        from core.feature_config import get_config

        register_exocortex_handlers()
        cfg = get_config().app
        if cfg.enable_velum:
            logger.info("   Velum L1.5: ✅")
        if cfg.enable_etir:
            logger.info("   Etir L3.5a: ✅")
        if cfg.enable_l6_welfare:
            logger.info("   L6 Welfare: ✅")
        if cfg.enable_event_bus:
            logger.info("   EventBus: ✅")
        if cfg.enable_cognitive_store:
            logger.info("   CognitiveFactStore: ✅")
        if cfg.enable_cognitive_runtime:
            from core.cognitive_runtime import register_cognitive_runtime_handlers

            register_cognitive_runtime_handlers()
            logger.info("   CognitiveRuntime V10: ✅")
        if cfg.enable_umwelt_store:
            from core.umwelt_registry import ensure_seed_loaded

            if await asyncio.to_thread(ensure_seed_loaded):
                logger.info("   Umwelt store: seed загружен (layer 99)")
            else:
                from core.umwelt_store import get_umwelt_store

                n = await asyncio.to_thread(get_umwelt_store().count)
                logger.info("   Umwelt store: ✅ (%d perceptions)", n)
    except Exception as exc:
        logger.warning("   ExoCortex init: %s", exc)

    # V8.7 Titan: Multilingual router — auto-detect RU/EN, lemmatize, dual-index
    try:
        from core.multilingual_router import is_multilingual_enabled, patch_pipeline_retrieval
        if is_multilingual_enabled():
            patch_pipeline_retrieval()
            logger.info("   Multilingual Router: ✅ RU+EN лемматизация")
    except Exception as exc:
        logger.warning("   Multilingual Router: %s", exc)

    if _CONSOLE_OK:
        _port = os.getenv("PORT", "8000")
        logger.info(
            "   Web UI: http://127.0.0.1:%s/console/  (/ui, /debug/console)",
            _port,
        )

    _route_paths = {
        getattr(r, "path", "")
        for r in app.routes
        if hasattr(r, "path")
    }
    for _llm_path in ("/console/llm/test", "/console/llm/providers"):
        if _llm_path in _route_paths:
            logger.info("   LLM API: %s ✅", _llm_path)
        else:
            logger.error("   LLM API: %s ❌ не зарегистрирован", _llm_path)

    logger.info("✅ VELANTRIM V8.7 Titan готов")
    yield

    # Shutdown
    logger.info("🛑 Velantrim Server останавливается...")
    if _sleep_worker:
        await _sleep_worker.stop()
    logger.info("👋 Velantrim Server остановлен")


# ─── FastAPI App ───────────────────────────────────────────────────────────────

# SECURITY (audit fix): Swagger/OpenAPI скрыты по умолчанию (это админ-поверхность).
# Включить для разработки: ENABLE_API_DOCS=true.
_API_DOCS = os.getenv("ENABLE_API_DOCS", "false").lower() == "true"
app = FastAPI(
    title="VELANTRIM V8.7 Titan API",
    description=(
        "Долговременная память для AI-агентов с каузальным графом.\n\n"
        "**Принципы:** Graph = Truth · LLM = Language · Memory = Physiology"
    ),
    version="8.7.0",
    lifespan=lifespan,
    docs_url="/docs" if _API_DOCS else None,
    redoc_url="/redoc" if _API_DOCS else None,
    openapi_url="/openapi.json" if _API_DOCS else None,
)

from api.llm_routes import register_llm_routes
from api.web_console import console_available as _console_available
from api.web_console import register_console_routes
from core.provider_catalog import CATALOG_BUILD_ID, catalog_debug_info, list_providers


@app.get("/console/llm/providers", tags=["LLM", "Console"])
@app.get("/llm/providers", tags=["LLM"])
async def serve_llm_providers_catalog():
    """Актуальный каталог (provider_catalog.py) — приоритет над устаревшими маршрутами."""
    meta = catalog_debug_info()
    return {
        "providers": list_providers(),
        "catalog_build_id": CATALOG_BUILD_ID,
        "gemini_catalog_revision": meta.get("gemini_catalog_revision"),
        "catalog_module": meta.get("catalog_module"),
    }


# ─── Auth ────────────────────────────────────────────────────────────────────
# Defined here (above register_llm_routes) so the outbound LLM/STT/TTS routes can
# require it. No-op when VELANTRIM_API_KEY is unset (dev/open mode unaffected).
async def require_api_key(x_api_key: str = Header(default="")):
    # SECURITY (audit fix): constant-time сравнение против timing-атак.
    import hmac

    if API_KEY and not hmac.compare_digest(x_api_key or "", API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный API ключ. Передай заголовок X-Api-Key.",
        )


# AUDIT-FIX P1: secure_router (outbound LLM/STT/TTS routes that consume a provider
# api_key) now requires VELANTRIM_API_KEY — closes the unauth key-oracle + quota burn.
register_llm_routes(app, auth_dependency=require_api_key)
logger.info(
    "LLM API: POST /console/llm/test, catalog_build_id=%s",
    CATALOG_BUILD_ID,
)

_CONSOLE_OK = register_console_routes(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # AUDIT-FIX v8.4.0: автоматически отключаем credentials если origin="*"
    # (CORS spec: allow_credentials=True + allow_origins=["*"] → отклоняется браузерами)
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    # AUDIT-FIX (security tail): explicit method/header allowlists instead of "*".
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["X-Api-Key", "Content-Type", "Authorization"],
)


# ─── Security headers (always-on; safe, no behavior change) ─────────────────────
@app.middleware("http")
async def _security_headers_mw(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-XSS-Protection", "0")
    host = (request.client.host if request.client else "") or ""
    if host not in ("127.0.0.1", "::1", "localhost"):
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


# ─── Rate limiting (per-IP token bucket; gated by ENABLE_RATE_LIMIT, default off) ─
@app.middleware("http")
async def _rate_limit_mw(request, call_next):
    try:
        from core.runtime_flags import is_rate_limit_enabled
    except Exception:  # noqa: BLE001
        return await call_next(request)
    if not is_rate_limit_enabled():
        return await call_next(request)
    from core.rate_limit import check_rate_limit

    host = (request.client.host if request.client else "") or "unknown"
    allowed, retry_after = check_rate_limit(host)
    if not allowed:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=429,
            content={"error": "rate_limited", "retry_after": retry_after},
            headers={"Retry-After": str(retry_after)},
        )
    return await call_next(request)


# ─── Export endpoints registration ─────────────────────────────────────────────
# FIX v8.5.3 (Claude audit + Qwen finding): server_patch/export_endpoints.py
# определяет функцию register_export_endpoints(app, require_api_key=None),
# но никогда не вызывалась — это был orphan-модуль. Здесь подключаем его
# с обязательной auth через require_api_key, чтобы /export/* endpoints
# требовали X-Api-Key (закрывает потенциальную дыру, описанную в аудите).
try:
    from server_patch.export_endpoints import register_export_endpoints
    register_export_endpoints(app, require_api_key=require_api_key)
    logger.info("   Export endpoints: ✅ подключены с auth")
except Exception as exc:
    # Не критично для основной функциональности — логируем и продолжаем.
    # Это нужно изолировать, потому что export — опциональная фича.
    logger.warning("   Export endpoints: ⚠️ не подключены: %s", exc)


# ─── Pydantic модели ──────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query:          str              = Field(..., min_length=1, max_length=2000)
    profile:        str | None    = Field(
        None,
        description=(
            "Профиль: citizen|personal|company|science|education|research|developer. "
            "См. GET /profiles и /console"
        ),
    )
    mode:           str              = Field("BALANCED", description="PRECISION|BALANCED|EXPLORATION|CREATIVE")
    response_lens:  str              = Field(
        "VELANTRIM",
        description="Линза ответа ModeRouter: PERSONAL|VELANTRIM|UMWELT",
    )
    domain:         str | None    = Field(
        None,
        description="Фильтр retrieval: science|engineering|perception|personal|system|general",
    )
    top_k:          int              = Field(3, ge=1, le=20)
    use_llm:        bool | None   = Field(
        None,
        description="Генерировать ответ через LLM (null = по профилю / да)",
    )
    llm_provider:   str | None    = Field(
        None,
        description="LLM из консоли: openai|deepseek|gemini|openrouter|anthropic",
    )
    llm_api_key:    str | None    = Field(
        None,
        description="API ключ LLM (только для запроса; не сохраняется на сервере)",
    )
    llm_model:      str | None    = Field(None, description="Модель LLM (опционально)")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        allowed = {"PRECISION", "BALANCED", "EXPLORATION", "CREATIVE"}
        if v.upper() not in allowed:
            raise ValueError(f"mode должен быть одним из: {allowed}")
        return v.upper()

    @field_validator("response_lens")
    @classmethod
    def validate_response_lens(cls, v: str) -> str:
        from core.router.mode_router import normalize_lens

        return normalize_lens(v)

    @field_validator("domain")
    @classmethod
    def validate_query_domain(cls, v: str | None) -> str | None:
        if v is None or not str(v).strip():
            return None
        from core.domain_tags import normalize_domain

        return normalize_domain(v)

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v: str | None) -> str | None:
        if v is None or not str(v).strip():
            return None
        from core.deployment_profiles import get_profile

        get_profile(v)
        return v.strip().lower()

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str | None) -> str | None:
        if v is None or not str(v).strip():
            return None
        from core.llm_router import get_provider_info

        pid = v.strip().lower()
        if not get_provider_info(pid):
            raise ValueError(f"llm_provider неизвестен: {v}")
        return pid


class LlmTestRequest(BaseModel):
    provider: str = Field(..., min_length=2)
    api_key:  str = Field(..., min_length=8)
    model:    str | None = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        from core.llm_router import get_provider_info

        pid = v.strip().lower()
        if not get_provider_info(pid):
            raise ValueError(f"provider неизвестен: {v}")
        return pid


class QueryResponse(BaseModel):
    query:          str
    answer:         str | None
    llm_answer:     str | None
    facts:          list[dict]
    total_facts:    int
    mode:           str
    error:          str | None
    latency_ms:     float
    causal_hints:   list[dict[str, Any]] | None = Field(
        None, description="Каузальные подсказки из CausalGraph (шаг pipeline 7)"
    )
    exocortex_sections: list[dict[str, Any]] | None = Field(
        None, description="Секции Velum/Etir/Fusion при ENABLE_*=1"
    )
    gaps: list[dict[str, Any]] | None = Field(
        None, description="Пробелы памяти vs Goal Stack (ENABLE_INNENWELT)"
    )
    innenwelt: dict[str, Any] | None = Field(
        None, description="Сводка Innenwelt: цели, welfare, alignment"
    )
    response_lens: str | None = Field(
        None, description="Активная линза ModeRouter"
    )
    lens_context: dict[str, Any] | None = Field(
        None, description="Метаданные линзы (перспективы Umwelt и т.д.)"
    )
    cross_domain: dict[str, Any] | None = Field(
        None, description="Междоменный план и сводка (ENABLE_CROSS_DOMAIN)"
    )
    profile_landmark: dict[str, Any] | None = Field(
        None, description="Ориентиры выбранного профиля (если передан profile)"
    )
    effective_params: dict[str, Any] | None = Field(
        None, description="Итоговые mode/lens/domain после применения профиля"
    )
    llm_meta: dict[str, Any] | None = Field(
        None, description="Провайдер/модель LLM для отладки консоли"
    )
    reasoning_trace_id: str | None = Field(
        None, description="ID trace-записи: какие факты поддержали ответ"
    )
    truth: dict[str, Any] | None = Field(
        None,
        description="Вердикт truth_policy: allow|gap_notice|reject (только при ENABLE_TRUTH_POLICY)",
    )
    observer: dict[str, Any] | None = Field(
        None,
        description="Пассивный вердикт Observer: allow|warn|gap_notice|reject + flags (ENABLE_OBSERVER)",
    )


class ChatRequest(BaseModel):
    """Упрощённый чат для веб-консоли."""
    message:        str              = Field(..., min_length=1, max_length=12000)
    profile:        str | None    = None
    use_memory:     bool             = Field(True, description="Искать факты в памяти перед LLM")
    llm_enabled:    bool             = Field(True)
    llm_provider:   str | None    = None
    llm_api_key:    str | None    = None
    llm_model:      str | None    = None
    console_instructions: str | None = Field(
        None,
        max_length=8000,
        description="Доп. инструкции оператора из правой колонки консоли",
    )
    ui_lang: str | None = Field(
        "ru",
        description="Язык UI консоли (ru|en) для гайда и подписей памяти",
    )
    auto_save_memory: bool = Field(
        True,
        description="Автосохранение уверенных фактов из сообщения пользователя",
    )
    include_system_guide: bool = Field(
        False,
        description="Включить в system prompt гайд «как работает Velantrim»",
    )
    chat_history: list[dict[str, str]] | None = Field(
        None,
        description="История текущей сессии [{role: user|assistant, content}]",
    )
    previous_chat_summary: str | None = Field(
        None,
        max_length=8000,
        description="Краткое содержание предыдущего чата (новая сессия)",
    )
    block_memory: list[dict[str, Any]] | None = Field(
        None,
        description="Блок временной памяти из консоли (не POST /facts)",
    )
    persist_to_system: bool = Field(
        False,
        description="Дублировать автосохранение в долгую память Velantrim (facts)",
    )
    llm_max_tokens: int = Field(
        8192,
        ge=256,
        le=40000,
        description="Максимум токенов в ответе LLM (консоль)",
    )
    deepseek_thinking: str | None = Field(
        "off",
        description="DeepSeek thinking: off | high | max (xhigh → max)",
    )

    @field_validator("llm_provider")
    @classmethod
    def validate_chat_llm_provider(cls, v: str | None) -> str | None:
        if v is None or not str(v).strip():
            return None
        from core.llm_router import get_provider_info

        pid = v.strip().lower()
        if not get_provider_info(pid):
            raise ValueError(f"llm_provider неизвестен: {v}")
        return pid

    @field_validator("profile")
    @classmethod
    def validate_chat_profile(cls, v: str | None) -> str | None:
        if v is None or not str(v).strip():
            return None
        from core.deployment_profiles import get_profile

        get_profile(v)
        return v.strip().lower()

    @field_validator(
        "llm_enabled",
        "use_memory",
        "auto_save_memory",
        "include_system_guide",
        "persist_to_system",
        mode="before",
    )
    @classmethod
    def coerce_chat_bools(cls, v: Any) -> Any:
        """Защита от JS `true && 'sk-…'` → строка вместо bool."""
        if isinstance(v, bool) or v is None:
            return v
        if isinstance(v, str):
            low = v.strip().lower()
            if low in ("true", "1", "yes", "on"):
                return True
            if low in ("false", "0", "no", "off", ""):
                return False
        return v


class ChatResponse(BaseModel):
    reply:          str
    from_llm:       bool
    llm_provider:   str | None = None
    llm_model:      str | None = None
    facts_count:    int = 0
    profile:        str | None = None
    latency_ms:     float = 0.0
    error:          str | None = None
    memory_highlights: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Факты из памяти, использованные при ответе",
    )
    memory_saved: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Факты, сохранённые в этом запросе",
    )
    memory_suggestions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Кандидаты на сохранение (не прошли порог автосохранения)",
    )
    memory_auto_status: str | None = Field(
        None,
        description="Статус автосохранения: saved_N | suggestions_N | none | off",
    )
    llm_usage: dict[str, Any] | None = Field(
        None,
        description="Токены и KV/cache (DeepSeek prompt_cache_hit_tokens, Gemini cachedContentTokenCount)",
    )
    dialogue_essence: dict[str, Any] | None = Field(
        None,
        description="Граф эссенции диалога (узлы/связи) для панели мониторинга консоли",
    )


def _chat_essence_snapshot(
    req: ChatRequest,
    lang: str,
    phase: str,
    *,
    facts: list[dict] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    memory_saved: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    from core.dialogue_essence import build_essence_snapshot

    return build_essence_snapshot(
        req.message,
        lang=lang,
        phase=phase,
        block_memory=req.block_memory,
        retrieved_facts=facts,
        candidates=candidates,
        memory_saved=memory_saved,
    )


def _console_observed_memory_fallback(
    message: str,
    domain: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Console-only fallback: surface retrieved Observed facts as unverified memory.

    The strict pipeline may block Observed facts before they become Validated.
    That is correct for TruthGate, but in the chat UI it reads as "memory is
    empty" even when the user just saved a fact.
    """
    try:
        from core.pipeline import retrieve
    except Exception as exc:
        logger.debug("console observed fallback import failed: %s", exc)
        return []

    retrieved: list[dict[str, Any]] = []
    for dom in (domain, None):
        if retrieved:
            break
        try:
            retrieved = retrieve(message, k=limit, domain=dom)
        except Exception as exc:
            logger.debug("console observed fallback failed (domain=%s): %s", dom, exc)
            retrieved = []

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in retrieved[:limit]:
        fact_id = str(item.get("fact_id") or item.get("id") or "").strip()
        claim = str(item.get("claim") or item.get("text") or "").strip()
        if not claim:
            continue
        dedupe_key = fact_id or claim.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        meta = item.get("metadata") or {}
        if not isinstance(meta, dict):
            meta = {}
        out.append(
            {
                "fact_id": fact_id,
                "claim": claim,
                "source": item.get("source", "memory"),
                "confidence": float(item.get("confidence") or 0),
                "retrieval_score": item.get("retrieval_score") or item.get("score") or 0,
                "epistemic_state": item.get("epistemic_state") or "Observed",
                "metadata": {**meta, "console_observed_fallback": True},
            }
        )
    return out


def _console_all_memory(limit: int = 80) -> list[dict[str, Any]]:
    try:
        from core.memory import get_all_facts

        facts = get_all_facts()
    except Exception as exc:
        logger.debug("console all memory failed: %s", exc)
        return []
    return list(facts or [])[: max(1, min(limit, 500))]


def _console_recent_notes(limit: int = 50) -> list[dict[str, Any]]:
    try:
        from core.console_notes import ConsoleNotesStore

        return ConsoleNotesStore().list_notes(limit=limit)
    except Exception as exc:
        logger.debug("console notes read failed: %s", exc)
        return []


def _console_offline_reply(
    message: str,
    facts: list[dict[str, Any]],
    lang: str | None = "ru",
) -> str | None:
    try:
        from localmind.answer_composer import build_offline_reply
    except Exception as exc:
        logger.debug("offline console import failed: %s", exc)
        return None
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for fact in list(facts or []) + _console_all_memory():
        fid = str(fact.get("fact_id") or fact.get("id") or fact.get("claim") or "")
        if not fid or fid in seen:
            continue
        seen.add(fid)
        merged.append(fact)
    return build_offline_reply(
        message,
        merged,
        notes=_console_recent_notes(),
        lang=lang,
    )


def _console_needs_offline_inventory(message: str) -> bool:
    try:
        from localmind.intent_router import intent_for

        return intent_for(message) not in {"none", "empty"}
    except Exception:
        return False


def _format_console_memory_reply(
    message: str,
    facts: list[dict[str, Any]],
    pipeline_error: str | None,
    lang: str | None = "ru",
) -> str:
    lang = (lang or "ru").strip().lower()
    if lang not in ("ru", "en"):
        lang = "ru"
    offline = _console_offline_reply(message, facts, lang)
    if offline:
        return offline
    if facts:
        has_observed_fallback = any(
            isinstance(f.get("metadata") or {}, dict)
            and (f.get("metadata") or {}).get("console_observed_fallback")
            for f in facts
        )
        if has_observed_fallback:
            title = (
                "Found in memory, not validated yet:"
                if lang == "en"
                else "Нашёл в памяти, но это ещё не валидировано:"
            )
            return title + "\n" + "\n".join(
                f"• {f.get('claim', '')}" for f in facts[:5]
            )
        return "\n".join(f"• {f.get('claim', '')}" for f in facts[:5])
    if pipeline_error:
        return (
            f"Memory error: {pipeline_error}"
            if lang == "en"
            else f"Ошибка памяти: {pipeline_error}"
        )
    return (
        "LLM is off. Enable LLM or add facts to memory."
        if lang == "en"
        else "LLM выключен. Включите LLM или добавьте факты в память."
    )


class FactCreate(BaseModel):
    fact_id:        str | None    = None
    claim:          str              = Field(..., min_length=1)
    source:         str              = Field(..., min_length=1)
    confidence:     float            = Field(0.8, ge=0.0, le=1.0)
    domain:         str | None    = Field(None, description="science|engineering|...")
    metadata:       dict[str, Any]   = Field(default_factory=dict)

    @field_validator("domain")
    @classmethod
    def validate_fact_domain(cls, v: str | None) -> str | None:
        if v is None:
            return None
        from core.domain_tags import normalize_domain

        return normalize_domain(v)


class CrossDomainPlanRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    domain: str | None = None


class CognitiveFactCreate(BaseModel):
    claim: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    fact_id: str | None = None
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    domain: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_input: str | None = Field(None, description="L0 оригинал; по умолчанию = claim")

    @field_validator("domain")
    @classmethod
    def validate_cf_domain(cls, v: str | None) -> str | None:
        if v is None:
            return None
        from core.domain_tags import normalize_domain

        return normalize_domain(v)


class FactResponse(BaseModel):
    fact_id:        str
    claim:          str
    source:         str
    confidence:     float
    epistemic_state: str
    created_at:     str | None
    updated_at:     str | None
    t_event_valid_start: str | None
    t_event_valid_end:   str | None
    t_ingestion_start:   str | None
    t_ingestion_end:     str | None
    history:        list[dict]
    metadata:       dict


class TransitionRequest(BaseModel):
    new_state:      str
    by:             str              = Field("api", description="Кто инициировал переход")


class IngestRequest(BaseModel):
    text:           str              = Field(..., min_length=1)
    source:         str              = Field(..., min_length=1)
    confidence:     float            = Field(0.8, ge=0.0, le=1.0)
    chunk_size:     int              = Field(500, ge=50, le=5000)
    metadata:       dict[str, Any]   = Field(default_factory=dict)


class InvalidateRequest(BaseModel):
    t_event_valid_end: str | None = None
    t_ingestion_end:   str | None = None


class GoalCreate(BaseModel):
    title:       str = Field(..., min_length=1, max_length=500)
    description: str = Field("", max_length=5000)
    priority:    int = Field(0, ge=0, le=100)
    keywords:    list[str] = Field(default_factory=list)
    user_id:     str = Field("default", max_length=128)


class GoalStatusUpdate(BaseModel):
    status: str = Field(..., description="active | done | cancelled")


class RouterRouteRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    response_lens: str = Field("VELANTRIM")
    user_id: str = Field("default", max_length=128)

    @field_validator("response_lens")
    @classmethod
    def validate_response_lens(cls, v: str) -> str:
        from core.router.mode_router import normalize_lens

        return normalize_lens(v)


class UmweltPerceptionCreate(BaseModel):
    perception_id: str | None = None
    object_key: str = Field(..., min_length=1, max_length=64)
    object_label_ru: str = Field("", max_length=128)
    perceiver_id: str = Field(..., min_length=1, max_length=128)
    perceiver: str = Field(..., min_length=1, max_length=128)
    perceiver_category: str = Field("", max_length=64)
    statement: str = Field(..., min_length=1, max_length=5000)
    affordances: list[str] = Field(default_factory=list)
    knowledge_status: str = Field("interpreted")
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    related_perceptions: list[str] = Field(default_factory=list)


class UmweltSeedRequest(BaseModel):
    sync_to_memory: bool = Field(
        False, description="Дублировать perceptions как факты L1 (Observed)"
    )
    object_key: str | None = Field(
        None, description="Синхронизировать только объект (если sync_to_memory)"
    )


class TelegramIngestRequest(BaseModel):
    text: str = Field(..., min_length=2, max_length=8000)
    chat_id: str = Field("dev_chat", max_length=64)
    user_id: str | None = Field(None, max_length=64)
    message_id: str | None = Field(None, max_length=64)
    username: str | None = Field(None, max_length=128)
    reply: bool = Field(False, description="Отправить ответ в Telegram (нужен token)")


class EpisodeRequest(BaseModel):
    """
    AUDIT-FIX v8.4.0: была Dict[str, Any] — никакой валидации,
    открытая дверь для prompt injection в LLM через SleepTimeWorker.
    Теперь явная схема с ограничениями на длину.
    """
    content:    str              = Field(..., min_length=1, max_length=10_000)
    source:     str              = Field("user", min_length=1, max_length=200)
    query:      str | None    = Field(None, max_length=2000)
    answer:     str | None    = Field(None, max_length=10_000)
    metadata:   dict[str, Any]   = Field(default_factory=dict)


class SourceRegisterRequest(BaseModel):
    source_type: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=1, max_length=300)
    uri: str = Field("", max_length=2000)
    trust: float = Field(0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FactInboxCreateRequest(BaseModel):
    claim: str = Field(..., min_length=1, max_length=8000)
    source_id: str | None = Field(None, max_length=128)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_id: str | None = Field(None, max_length=128)


class FactInboxStatusRequest(BaseModel):
    status: str = Field(..., description="pending | accepted | rejected | promoted | archived")
    reason: str = Field("", max_length=1000)


class FactInboxPromoteRequest(BaseModel):
    fact_id: str | None = Field(None, max_length=128)


class ReasoningTraceCreateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    answer: str = Field("", max_length=12000)
    mode: str = Field("", max_length=64)
    response_lens: str = Field("", max_length=64)
    source_fact_ids: list[str] = Field(default_factory=list)
    rejected_fact_ids: list[str] = Field(default_factory=list)
    notes: str = Field("", max_length=4000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConsoleNoteCreateRequest(BaseModel):
    title: str = Field("", max_length=300)
    content: str = Field(..., min_length=1, max_length=8000)
    tags: list[str] = Field(default_factory=list)


class ConsoleNoteUpdateRequest(BaseModel):
    title: str | None = Field(None, max_length=300)
    content: str | None = Field(None, max_length=8000)
    tags: list[str] | None = None


class ConsoleNoteEditRequest(BaseModel):
    instruction: str = Field(..., min_length=1, max_length=4000)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    """Веб-консоль — главная точка входа для людей."""
    if _console_available():
        return RedirectResponse(url="/console/")
    return {
        "name": "VELANTRIM V8.7 Titan",
        "version": "8.7.0",
        "console": "/console/",
        "api_docs": "/docs",
        "error": "static/console/index.html не найден — проверьте каталог запуска",
    }


@app.get("/api", tags=["System"])
async def api_info():
    """JSON-информация о сервере (для скриптов)."""
    return {
        "name":     "VELANTRIM V8.7 Titan",
        "version":  "8.7.0",
        "status":   "running",
        "uptime_s": round(time.time() - _startup_time, 1),
        "llm":      LLM_PROVIDER,
        "console":  "/console/" if _console_available() else None,
        "profiles": "/profiles",
        "docs":     "/docs",
    }


@app.get("/setup/llm", tags=["System"])
async def setup_llm():
    """Как подключить LLM к серверу (без секретов)."""
    from core.llm_router import list_providers

    env_cfg = _env_llm_config()
    ready = env_cfg is not None
    model = env_cfg.model if env_cfg else None
    return {
        "provider": LLM_PROVIDER,
        "ready": ready,
        "model": model,
        "providers": list_providers(),
        "hint": (
            "В консоли /console выберите провайдер (DeepSeek, Gemini, OpenAI, OpenRouter), "
            "вставьте API ключ и нажмите «Включить LLM». Либо задайте ключи в .env и перезапустите сервер."
        ),
        "env_file": "config/llm.example.env",
        "console_url": "/console/",
    }


def _llm_config_from_request(req) -> Optional["LlmCallConfig"]:  # noqa: F821 (forward-ref; импорт внутри функции)
    """Собрать override LLM из тела запроса или None."""
    from core.llm_router import (
        LlmCallConfig,
        llm_timeout_for_max_tokens,
        normalize_deepseek_thinking,
    )

    key = (getattr(req, "llm_api_key", None) or "").strip()
    prov = getattr(req, "llm_provider", None)
    model = getattr(req, "llm_model", None)
    max_tokens = int(getattr(req, "llm_max_tokens", None) or 8192)
    max_tokens = max(256, min(max_tokens, 40000))
    thinking = normalize_deepseek_thinking(getattr(req, "deepseek_thinking", "off"))
    if key and prov:
        return LlmCallConfig(
            provider=prov,
            api_key=key,
            model=model,
            max_tokens=max_tokens,
            timeout=llm_timeout_for_max_tokens(max_tokens),
            deepseek_thinking=thinking,
        )
    if key and not prov:
        raise HTTPException(
            status_code=400,
            detail="Укажите llm_provider вместе с llm_api_key",
        )
    return None


def _episode_dedup_enabled() -> bool:
    return os.getenv("ENABLE_EPISODE_DEDUP", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


async def _find_duplicate_fact(claim: str, source: str) -> dict[str, Any] | None:
    """Найти существующий факт: по claim (любой source) или episode_hash."""
    from core.fact_integrity import compute_episode_hash
    from core.memory import (
        find_fact_id_by_claim_dedup,
        get_fact,
    )

    if not _episode_dedup_enabled():
        return None
    existing_id = await asyncio.to_thread(find_fact_id_by_claim_dedup, claim)
    if not existing_id:
        episode_hash = compute_episode_hash(claim, source)
        existing_id = await asyncio.to_thread(
            find_fact_id_by_episode_hash, episode_hash
        )
    if not existing_id:
        return None
    dup = await asyncio.to_thread(get_fact, existing_id)
    if dup:
        return {**dup, "deduplicated": True}
    return None


async def _save_fact_for_console(cand: dict[str, Any]) -> dict[str, Any]:
    """Сохранить факт из консоли (дедуп по содержанию claim + episode_hash)."""
    import uuid

    from core.memory import get_fact, store_fact

    claim = cand["claim"]
    source = "console_chat"
    dup = await _find_duplicate_fact(claim, source)
    if dup:
        return dup

    fact_id = f"fact_{uuid.uuid4().hex[:12]}"
    meta = {
        "memory_category": cand.get("category", "general"),
        "console_auto": True,
    }
    fact = {
        "fact_id": fact_id,
        "claim": claim,
        "source": source,
        "confidence": float(cand.get("confidence", 0.85)),
        "metadata": meta,
    }
    await asyncio.to_thread(store_fact, fact)
    stored = await asyncio.to_thread(get_fact, fact_id)
    return stored or fact


@app.post("/chat", response_model=ChatResponse, tags=["LLM"],
          dependencies=[Depends(require_api_key)])
async def chat_endpoint(req: ChatRequest):
    """Чат для консоли: память + выбранный LLM."""
    from core.llm_router import get_provider_info

    t0 = time.time()
    facts: list[dict] = []
    pipeline_error: str | None = None

    try:
        from core.deployment_profiles import resolve_query_params

        effective, landmark = resolve_query_params(
            profile=req.profile,
            mode="BALANCED",
            response_lens="VELANTRIM",
            domain=None,
            top_k=3,
            use_llm=req.llm_enabled,
        )
        eff_mode = effective["mode"]
        eff_domain = effective["domain"]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if req.use_memory:
        try:
            result = await asyncio.to_thread(
                pipeline_run, req.message, eff_mode, eff_domain
            )
            facts = result.get("facts", []) or []
            pipeline_error = result.get("error")
        except Exception as exc:
            logger.exception("chat pipeline: %s", exc)
            pipeline_error = str(exc)
        if pipeline_error and not facts:
            facts = await asyncio.to_thread(
                _console_observed_memory_fallback, req.message, eff_domain
            )
            if facts:
                pipeline_error = None
        if not facts and _console_needs_offline_inventory(req.message):
            facts = await asyncio.to_thread(_console_all_memory)
            if facts:
                pipeline_error = None

    reply: str = ""
    from_llm = False
    llm_provider_out: str | None = None
    llm_model_out: str | None = None
    llm_usage: dict[str, Any] | None = None

    if req.llm_enabled:
        cfg = _llm_config_from_request(req) or _env_llm_config()
        if not cfg or not cfg.api_key:
            raise HTTPException(
                status_code=400,
                detail=(
                    "LLM: выберите провайдера и вставьте API ключ в консоли, "
                    "или настройте LLM_PROVIDER в .env"
                ),
            )
        llm_provider_out = cfg.provider
        pinfo = get_provider_info(cfg.provider)
        llm_model_out = (cfg.model or "").strip() or (
            pinfo["default_model"] if pinfo else "?"
        )

        from core.console_memory import (
            build_chat_context_for_prompt,
            build_console_operator_guide,
            fact_to_highlight,
        )

        lang = (req.ui_lang or "ru").strip().lower()
        if lang not in ("ru", "en"):
            lang = "ru"
        extra_parts: list[str] = []
        if req.include_system_guide:
            extra_parts.append(
                build_console_operator_guide(lang, profile=req.profile)
            )
        # Только прошлый чат в system; текущая сессия — в messages[] (KV-cache DeepSeek / Gemini)
        ctx = build_chat_context_for_prompt(
            None, req.previous_chat_summary, lang, req.block_memory
        )
        if ctx:
            extra_parts.append(ctx)
        op = (req.console_instructions or "").strip()
        if op:
            extra_parts.append(
                "Инструкции оператора:\n" + op
                if lang == "ru"
                else "Operator instructions:\n" + op
            )
        lens_extra = "\n\n".join(extra_parts) if extra_parts else None
        system = _build_system_prompt(facts, lens_instructions=lens_extra)
        llm_usage: dict[str, Any] | None = None
        try:
            from core.llm_stream import chat_complete_messages

            reply, llm_usage = await chat_complete_messages(
                cfg,
                system,
                req.message,
                req.chat_history,
            )
            from_llm = True
        except Exception as exc:
            offline = _console_offline_reply(req.message, facts, req.ui_lang)
            if offline:
                reply = offline
                from_llm = False
                pipeline_error = None
            else:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        reply = _format_console_memory_reply(req.message, facts, pipeline_error, lang=req.ui_lang)

    from core.console_memory import (
        extract_memory_candidates,
        fact_to_highlight,
    )

    lang = (req.ui_lang or "ru").strip().lower()
    if lang not in ("ru", "en"):
        lang = "ru"
    highlights = [fact_to_highlight(f, lang) for f in facts[:12]]
    candidates = extract_memory_candidates(req.message)
    memory_saved, memory_suggestions, memory_auto_status = (
        await _console_autosave_memory(req, candidates, highlights, lang)
    )
    dialogue_essence = _chat_essence_snapshot(
        req,
        lang,
        "commit",
        facts=facts,
        candidates=candidates,
        memory_saved=memory_saved,
    )

    return ChatResponse(
        reply=reply,
        from_llm=from_llm,
        llm_provider=llm_provider_out,
        llm_model=llm_model_out,
        facts_count=len(facts),
        profile=req.profile,
        latency_ms=round((time.time() - t0) * 1000, 2),
        error=pipeline_error,
        memory_highlights=highlights[:16],
        memory_saved=memory_saved,
        memory_suggestions=memory_suggestions,
        memory_auto_status=memory_auto_status,
        llm_usage=llm_usage,
        dialogue_essence=dialogue_essence,
    )


async def _console_autosave_memory(
    req: ChatRequest,
    candidates: list[dict[str, Any]],
    highlights: list[dict[str, Any]],
    lang: str,
) -> tuple:
    """Автосохранение фактов из сообщения пользователя (чат / stream)."""
    from core.console_memory import category_emoji, category_label, fact_to_highlight

    memory_saved: list[dict[str, Any]] = []
    memory_suggestions: list[dict[str, Any]] = []
    save_threshold = 0.65
    if not req.auto_save_memory:
        memory_suggestions = candidates
        return memory_saved, memory_suggestions, "off"
    if not candidates:
        return memory_saved, memory_suggestions, "none"

    for cand in candidates:
        if cand.get("confidence", 0) < save_threshold:
            memory_suggestions.append(cand)
            continue
        if not getattr(req, "persist_to_system", False):
            cat = cand.get("category", "general")
            saved_item = {
                **cand,
                "memory_store": "block",
                "category_label": category_label(cat, lang),
                "emoji": cand.get("emoji") or category_emoji(cat),
            }
            memory_saved.append(saved_item)
            continue
        try:
            created = await _save_fact_for_console(cand)
            hi = fact_to_highlight(created, lang)
            saved_item = {
                **cand,
                "fact_id": created.get("fact_id", ""),
                "category_label": hi.get("category_label", ""),
                "emoji": cand.get("emoji") or hi.get("emoji", "💾"),
                "memory_store": "facts",
                "deduplicated": bool(created.get("deduplicated")),
            }
            memory_saved.append(saved_item)
            if not created.get("deduplicated"):
                highlights.insert(0, hi)
        except Exception as exc:
            logger.warning("console auto-save fact: %s", exc)
            memory_suggestions.append({**cand, "error": str(exc)})

    if memory_saved:
        status = f"saved_{len(memory_saved)}"
    elif memory_suggestions:
        status = f"suggestions_{len(memory_suggestions)}"
    else:
        status = "none"
    return memory_saved, memory_suggestions, status


async def _chat_prepare(req: ChatRequest):
    """Общая подготовка /chat и /chat/stream."""
    from core.llm_router import get_provider_info

    facts: list[dict] = []
    pipeline_error: str | None = None
    try:
        from core.deployment_profiles import resolve_query_params

        effective, _landmark = resolve_query_params(
            profile=req.profile,
            mode="BALANCED",
            response_lens="VELANTRIM",
            domain=None,
            top_k=3,
            use_llm=req.llm_enabled,
        )
        eff_mode = effective["mode"]
        eff_domain = effective["domain"]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if req.use_memory:
        try:
            result = await asyncio.to_thread(
                pipeline_run, req.message, eff_mode, eff_domain
            )
            facts = result.get("facts", []) or []
            pipeline_error = result.get("error")
        except Exception as exc:
            logger.exception("chat pipeline: %s", exc)
            pipeline_error = str(exc)
        if pipeline_error and not facts:
            facts = await asyncio.to_thread(
                _console_observed_memory_fallback, req.message, eff_domain
            )
            if facts:
                pipeline_error = None
        if not facts and _console_needs_offline_inventory(req.message):
            facts = await asyncio.to_thread(_console_all_memory)
            if facts:
                pipeline_error = None

    cfg = None
    system = ""
    lang = (req.ui_lang or "ru").strip().lower()
    if lang not in ("ru", "en"):
        lang = "ru"
    llm_provider_out: str | None = None
    llm_model_out: str | None = None

    if req.llm_enabled:
        cfg = _llm_config_from_request(req) or _env_llm_config()
        if not cfg or not cfg.api_key:
            raise HTTPException(
                status_code=400,
                detail=(
                    "LLM: выберите провайдера и вставьте API ключ в консоли, "
                    "или настройте LLM_PROVIDER в .env"
                ),
            )
        llm_provider_out = cfg.provider
        pinfo = get_provider_info(cfg.provider)
        llm_model_out = (cfg.model or "").strip() or (
            pinfo["default_model"] if pinfo else "?"
        )
        from core.console_memory import (
            build_chat_context_for_prompt,
            build_console_operator_guide,
        )

        extra_parts: list[str] = []
        if req.include_system_guide:
            extra_parts.append(
                build_console_operator_guide(lang, profile=req.profile)
            )
        ctx = build_chat_context_for_prompt(
            None, req.previous_chat_summary, lang, req.block_memory
        )
        if ctx:
            extra_parts.append(ctx)
        op = (req.console_instructions or "").strip()
        if op:
            extra_parts.append(
                "Инструкции оператора:\n" + op
                if lang == "ru"
                else "Operator instructions:\n" + op
            )
        lens_extra = "\n\n".join(extra_parts) if extra_parts else None
        system = _build_system_prompt(facts, lens_instructions=lens_extra)

    return facts, pipeline_error, cfg, system, lang, llm_provider_out, llm_model_out


async def _chat_memory_side_effects(
    req: ChatRequest, facts: list[dict], lang: str
) -> tuple:
    from core.console_memory import extract_memory_candidates, fact_to_highlight

    highlights = [fact_to_highlight(f, lang) for f in facts[:12]]
    candidates = extract_memory_candidates(req.message)
    memory_saved, memory_suggestions, memory_auto_status = (
        await _console_autosave_memory(req, candidates, highlights, lang)
    )
    return (
        highlights,
        memory_saved,
        memory_suggestions,
        memory_auto_status,
    )


@app.post("/chat/stream", tags=["LLM"], dependencies=[Depends(require_api_key)])
async def chat_stream_endpoint(req: ChatRequest):
    """Потоковый чат (SSE): токены по мере генерации + память в конце."""
    import json as _json

    t0 = time.time()
    facts, pipeline_error, cfg, system, lang, llm_provider_out, llm_model_out = (
        await _chat_prepare(req)
    )

    async def event_generator():
        nonlocal pipeline_error
        reply = ""
        llm_usage: dict[str, Any] | None = None
        from_llm = False
        try:
            yield ": connected\n\n"
            for phase in ("read", "link"):
                snap = _chat_essence_snapshot(req, lang, phase, facts=facts)
                yield (
                    f"data: {_json.dumps({'type': 'essence', 'snapshot': snap}, ensure_ascii=False)}\n\n"
                )
            if req.llm_enabled and cfg:
                from core.llm_stream import stream_chat_events

                try:
                    async for ev in stream_chat_events(
                        cfg, system, req.message, req.chat_history
                    ):
                        if ev.get("type") == "token":
                            yield f"data: {_json.dumps(ev, ensure_ascii=False)}\n\n"
                        elif ev.get("type") == "done":
                            reply = ev.get("reply") or ""
                            llm_usage = ev.get("usage")
                            yield f"data: {_json.dumps(ev, ensure_ascii=False)}\n\n"
                        elif ev.get("type") == "error":
                            raise RuntimeError(ev.get("message") or "LLM stream error")
                    from_llm = True
                except Exception as exc:
                    offline = _console_offline_reply(req.message, facts, lang)
                    if not offline:
                        raise exc
                    reply = offline
                    from_llm = False
                    pipeline_error = None
                    yield f"data: {_json.dumps({'type': 'token', 'text': reply}, ensure_ascii=False)}\n\n"
                    yield f"data: {_json.dumps({'type': 'done', 'reply': reply, 'usage': {'offline_fallback': True}}, ensure_ascii=False)}\n\n"
            else:
                reply = _format_console_memory_reply(req.message, facts, pipeline_error, lang)
                yield f"data: {_json.dumps({'type': 'token', 'text': reply}, ensure_ascii=False)}\n\n"
                yield f"data: {_json.dumps({'type': 'done', 'reply': reply, 'usage': {}}, ensure_ascii=False)}\n\n"

            highlights, memory_saved, memory_suggestions, memory_auto_status = (
                await _chat_memory_side_effects(req, facts, lang)
            )
            from core.console_memory import extract_memory_candidates

            essence_commit = _chat_essence_snapshot(
                req,
                lang,
                "commit",
                facts=facts,
                candidates=extract_memory_candidates(req.message),
                memory_saved=memory_saved,
            )
            yield (
                f"data: {_json.dumps({'type': 'essence', 'snapshot': essence_commit}, ensure_ascii=False)}\n\n"
            )
            final = {
                "type": "final",
                "reply": reply,
                "from_llm": from_llm,
                "llm_provider": llm_provider_out,
                "llm_model": llm_model_out,
                "facts_count": len(facts),
                "profile": req.profile,
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "error": pipeline_error,
                "memory_highlights": highlights[:16],
                "memory_saved": memory_saved,
                "memory_suggestions": memory_suggestions,
                "memory_auto_status": memory_auto_status,
                "llm_usage": llm_usage,
                "dialogue_essence": essence_commit,
            }
            yield f"data: {_json.dumps(final, ensure_ascii=False)}\n\n"
        except Exception as exc:
            yield f"data: {_json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── V8.7 Titan — Новые эндпоинты ─────────────────────────────────────────────

# Модели для V8.7
from pydantic import BaseModel as _PydanticBaseModel


class _QueryRolesRequest(_PydanticBaseModel):
    query: str
    roles: str | None = None        # comma-separated: "ENGINEER,CRITIC"
    cognitive_mode: str | None = None
    domain: str | None = None


@app.post("/query/roles", tags=["V8.7 Titan"],
          response_model=QueryResponse, dependencies=[Depends(require_api_key)])
async def query_with_roles(req: _QueryRolesRequest):
    """
    Запрос с multi-perspective reasoning.

    Параметр `roles` — список ролей через запятую:
        ENGINEER, SCIENTIST, ANALYST, CRITIC, ADVISOR, FRIEND, PHILOSOPHER,
        CREATIVE, CHILD

    Если не указан — система выберет автоматически по запросу.
    """
    role_list = [r.strip().upper() for r in (req.roles or "").split(",") if r.strip()] or None
    try:
        from core.branch_manager import get_branch_manager
        bm = get_branch_manager()
        # FIX P1 (v8.7 audit): asyncio.to_thread + get_event_loop + run_until_complete
        # создавало новый event loop в треде → «no current event loop in thread».
        # branch_manager.reason() — async, вызываем напрямую из async-обработчика.
        synthesis = await bm.reason(query=req.query, roles=role_list)
        return QueryResponse(
            answer=synthesis.response,
            facts=synthesis.facts,
            query=req.query,
            confidence=synthesis.confidence,
            roles_used=[r.role_id for r in (synthesis.roles_used or [])],
        )
    except Exception as exc:
        logger.exception("query/roles failed: %s", exc)
        # FIX #20 (Claude audit): не раскрывать детали внутренних ошибок
        # в ответе клиенту — security/privacy leak.
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/system/epigenetic", tags=["V8.7 Titan"])
async def epigenetic_state():
    """Текущее эпигенетическое состояние системы."""
    try:
        from core.epigenetic_adaptation import get_epigenetic_engine
        engine = get_epigenetic_engine()
        return engine.stats()
    except Exception as exc:
        logger.exception("system/epigenetic failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/metrics/eval", tags=["V8.7 Titan"],
          dependencies=[Depends(require_api_key)])
async def eval_metrics():
    """
    Лёгкие метрики: grounding_score, trace_completeness, latency.

    FIX P1 (v8.7 audit): эндпоинт теперь требует X-Api-Key — read_recent(10)
    отдаёт последние запросы пользователя (до 200 символов каждый), что без
    авторизации является утечкой приватных данных.
    """
    try:
        from core.lightweight_metrics import get_lightweight_metrics
        lm = get_lightweight_metrics()
        return {
            "summary": lm.summary(),
            "aggregate": lm.aggregate(),
            "recent": lm.read_recent(10),
        }
    except Exception as exc:
        logger.exception("metrics/eval failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health", tags=["System"])
async def health():
    """
    Проверка здоровья системы.
    Возвращает MHI (Memory Health Index) и статус всех компонентов.
    MHI кэшируется на 60 секунд — тяжёлый расчёт (236 инструкций).
    """
    t0 = time.time()

    # MHI с кэшем
    now = time.time()
    if _mhi_cache["data"] is not None and (now - _mhi_cache["at"]) < _MHI_TTL:
        mhi_data = _mhi_cache["data"]
        http_status = 200 if mhi_data.get("status") != "SAFE_MODE" else 503
        mhi_data = {**mhi_data, "cached": True}
    else:
        try:
            from core.storage_facade import get_storage_kind

            l3_kind = get_storage_kind()
            l3_connected = l3_kind in ("kuzu", "ladybug", "neo4j")
            mhi_calc = MHICalculator(_store, l3_connected=l3_connected)
            mhi_report = await asyncio.to_thread(mhi_calc.calculate)
            mhi_data = {
                "score":   round(mhi_report.mhi, 3),
                "status":  mhi_report.status.value,
                "details": {
                    "validated_ratio":     round(mhi_report.validated_ratio, 3),
                    "freshness_score":     round(mhi_report.freshness_score, 3),
                    "retrieval_precision": round(mhi_report.retrieval_precision, 3),
                    "graph_coverage":      round(mhi_report.graph_coverage, 3),
                },
                "recommendations": mhi_report.recommendations,
                "cached": False,
            }
            _mhi_cache["data"] = mhi_data
            _mhi_cache["at"]   = now
            http_status = 200 if mhi_report.status != MHIStatus.SAFE_MODE else 503
        except Exception as exc:
            mhi_data = {"error": str(exc), "cached": False}
            http_status = 500

    # Количество фактов
    try:
        all_facts = await asyncio.to_thread(get_all_facts)
        facts_by_state: dict[str, int] = {}
        for f in all_facts:
            state = f.get("epistemic_state", "unknown")
            facts_by_state[state] = facts_by_state.get(state, 0) + 1
    except Exception:
        facts_by_state = {}

    return JSONResponse(
        status_code=http_status,
        content={
            "status":        "healthy" if http_status == 200 else "degraded",
            "uptime_s":      round(time.time() - _startup_time, 1),
            "latency_ms":    round((time.time() - t0) * 1000, 2),
            "mhi":           mhi_data,
            "facts":         facts_by_state,
            "components": {
                "sqlite":       "ok",
                "ngram_index":  "ok" if (_ngram and _ngram.available) else "degraded",
                "llm":          LLM_PROVIDER if LLM_PROVIDER != "none" else "disabled",
                "sleep_worker": "running" if _sleep_worker else "disabled",
            },
        },
    )


# ── Query ─────────────────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse, tags=["Query"],
          dependencies=[Depends(require_api_key)])
async def query(req: QueryRequest):
    """
    Главный endpoint. Запрос → Velantrim Memory → (LLM) → Ответ.

    Пайплайн:
    1. NGram pre-filter кандидатов
    2. HybridRetriever (BM25 + Dense + RRF)
    3. Guardian + TruthGate (CognitiveMode)
    4. ESM: Observed → Validated
    5. LLM генерация на основе верифицированных фактов
    """
    t0 = time.time()

    try:
        from core.deployment_profiles import resolve_query_params

        effective, landmark = resolve_query_params(
            profile=req.profile,
            mode=req.mode,
            response_lens=req.response_lens,
            domain=req.domain,
            top_k=req.top_k,
            use_llm=req.use_llm,
        )
        eff_mode = effective["mode"]
        eff_lens = effective["response_lens"]
        eff_domain = effective["domain"]
        eff_use_llm = effective["use_llm"]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Шаг 1-4: Velantrim pipeline (sync → thread)
    try:
        result = await asyncio.to_thread(
            pipeline_run, req.query, eff_mode, eff_domain
        )
    except Exception as exc:
        logger.exception("pipeline.run() упал: %s", exc)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

    pipeline_facts = result.get("facts", [])
    pipeline_answer = result.get("answer")
    pipeline_error = result.get("error")

    response_lens_out: str | None = eff_lens
    lens_context_out: dict[str, Any] | None = None
    routed = None
    try:
        from core.router.mode_router import (
            apply_lens,
            format_lens_answer,
            is_mode_router_enabled,
        )

        if is_mode_router_enabled():
            routed = apply_lens(
                req.query,
                pipeline_facts,
                eff_lens,
                user_id="default",
                cognitive_mode=eff_mode,
            )
            pipeline_facts = routed.facts
            response_lens_out = routed.lens
            lens_context_out = {
                "lens": routed.lens,
                "meta": routed.lens_meta,
                "cognitive_mode_hint": routed.cognitive_mode_hint,
            }
            if pipeline_answer and not pipeline_error:
                pipeline_answer = format_lens_answer(pipeline_answer, routed)
    except Exception as exc:  # noqa: BLE001
        logger.debug("mode_router: %s", exc)

    # P2 (T1.4): явный вердикт truth_policy по пакету фактов. Аддитивно и за флагом
    # (ENABLE_TRUTH_POLICY, по умолчанию off → truth_block=None, поток управления не меняется).
    truth_block: dict[str, Any] | None = None
    truth_rejects_answer = False
    try:
        from core.runtime_flags import is_truth_policy_enabled

        if is_truth_policy_enabled():
            from core.truth_policy import decide as _truth_decide

            _verdict = _truth_decide(req.query, pipeline_facts, mode=eff_mode)
            truth_block = _verdict.to_dict()
            # reject ⇒ нет допустимых фактов ⇒ не выдумываем ответ через LLM
            truth_rejects_answer = _verdict.is_reject
    except Exception as exc:  # noqa: BLE001 — аддитивно; никогда не ломаем ответ
        logger.debug("truth_policy verdict skipped: %s", exc)

    # Шаг 5: LLM генерация
    llm_answer: str | None = None
    llm_meta: dict[str, Any] | None = None
    if eff_use_llm and not pipeline_error and not truth_rejects_answer:
        try:
            cfg = _resolve_llm_config_for_request(req)
            extra = routed.system_instructions if routed else None
            system = _build_system_prompt(
                pipeline_facts, lens_instructions=extra
            )
            llm_answer = await _llm_generate(req.query, system=system, override=cfg)
            if cfg:
                from core.llm_router import _resolve_model as _rm

                llm_meta = {
                    "provider": cfg.provider,
                    "model": _rm(cfg),
                    "source": "request" if _llm_config_from_request(req) else "env",
                }
        except Exception as exc:
            logger.warning("LLM генерация упала: %s", exc)
            llm_answer = f"[LLM error: {exc}]"
            llm_meta = {"error": str(exc)}

    latency = round((time.time() - t0) * 1000, 2)
    logger.info("query: '%s' | facts=%d | llm=%s | %.0fms",
                req.query[:50], len(pipeline_facts),
                "ok" if llm_answer else "skip", latency)

    try:
        from core.event_bridge import on_query_completed

        preview = (llm_answer or pipeline_answer or "")[:500]
        await on_query_completed(
            user_id="default",
            query=req.query,
            answer_preview=preview,
            importance=min(1.0, len(pipeline_facts) / 10.0),
        )
    except Exception:  # noqa: BLE001
        pass

    gaps_out: list[dict[str, Any]] | None = None
    innenwelt_out: dict[str, Any] | None = None
    try:
        from core.runtime_flags import is_innenwelt_enabled, is_l6_welfare_enabled

        if is_innenwelt_enabled():
            from core.gap_detector import detect_gaps, query_goal_alignment
            from core.goal_stack import get_goal_stack

            uid = "default"
            gaps_out = await asyncio.to_thread(detect_gaps, uid)
            alignment = query_goal_alignment(req.query, uid)
            innenwelt_out = {
                "active_goals": len(
                    await asyncio.to_thread(
                        get_goal_stack().list_goals, uid, status="active", limit=50
                    )
                ),
                "gaps_count": len(gaps_out),
                "query_goal_alignment": round(alignment, 3),
            }
            if is_l6_welfare_enabled():
                from core.welfare_monitor import get_welfare_monitor

                get_welfare_monitor(uid).record(
                    "focus_sync",
                    meta={"goal_alignment": alignment},
                )
                innenwelt_out["welfare"] = get_welfare_monitor(uid).snapshot().to_dict()
    except Exception as exc:  # noqa: BLE001
        logger.debug("innenwelt enrich query: %s", exc)

    reasoning_trace_id: str | None = None
    try:
        from core.memory_ops import get_memory_ops

        trace = await asyncio.to_thread(
            get_memory_ops().save_trace,
            query=req.query,
            answer=llm_answer or pipeline_answer or "",
            mode=eff_mode,
            response_lens=response_lens_out or "",
            source_fact_ids=[
                str(f.get("fact_id"))
                for f in pipeline_facts
                if f.get("fact_id")
            ],
            rejected_fact_ids=[],
            notes="auto_trace_from_query",
            metadata={
                "profile": req.profile,
                "domain": eff_domain,
                "use_llm": eff_use_llm,
                "pipeline_error": pipeline_error,
            },
        )
        reasoning_trace_id = trace["trace_id"]
    except Exception as exc:  # noqa: BLE001
        logger.debug("reasoning trace save skipped: %s", exc)

    # Observer P0 (пассивный мета-монитор). Аддитивно + за флагом (ENABLE_OBSERVER, default off).
    # Работает ПОСЛЕ формирования ответа; пассивен — только вердикт, не пишет факты и не меняет поток.
    observer_block: dict[str, Any] | None = None
    try:
        from core.runtime_flags import is_observer_enabled

        if is_observer_enabled():
            from core.observer import observe as _observe

            observer_block = _observe(
                req.query,
                pipeline_facts,
                llm_answer or pipeline_answer or "",
                mode=eff_mode,
            ).to_dict()
    except Exception as exc:  # noqa: BLE001 — аддитивно; никогда не ломаем ответ
        logger.debug("observer skipped: %s", exc)

    return QueryResponse(
        query=req.query,
        answer=pipeline_answer,
        llm_answer=llm_answer,
        facts=pipeline_facts,
        total_facts=len(pipeline_facts),
        mode=eff_mode,
        error=pipeline_error,
        latency_ms=latency,
        causal_hints=result.get("causal_hints"),
        exocortex_sections=result.get("exocortex_sections"),
        gaps=gaps_out,
        innenwelt=innenwelt_out,
        response_lens=response_lens_out,
        lens_context=lens_context_out,
        cross_domain=result.get("cross_domain"),
        profile_landmark=landmark,
        effective_params=effective,
        llm_meta=llm_meta,
        reasoning_trace_id=reasoning_trace_id,
        truth=truth_block,
        observer=observer_block,
    )


# ── Facts CRUD ────────────────────────────────────────────────────────────────

@app.get("/facts", tags=["Facts"], dependencies=[Depends(require_api_key)])
async def list_facts(
    epistemic_state: str | None = None,
    domain: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    Список фактов с фильтрацией по epistemic_state и domain (metadata.domain).
    """
    facts = await asyncio.to_thread(get_all_facts, epistemic_state, domain)
    total = len(facts)
    page = facts[offset:offset + limit]
    return {
        "total":   total,
        "limit":   limit,
        "offset":  offset,
        "facts":   page,
    }


@app.get("/facts/{fact_id}", tags=["Facts"], dependencies=[Depends(require_api_key)])
async def get_fact_by_id(fact_id: str):
    """Получить факт по ID."""
    fact = await asyncio.to_thread(get_fact, fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail=f"Факт '{fact_id}' не найден")
    return fact


@app.get(
    "/facts/{fact_id}/cognitive",
    tags=["Facts", "CognitiveFact"],
    dependencies=[Depends(require_api_key)],
)
async def get_cognitive_fact(
    fact_id: str,
    include_relations: bool = False,
    include_raw: bool = True,
):
    """CognitiveFact v9.1+ — через CognitiveFactStore при ENABLE_COGNITIVE_STORE."""
    from core.cognitive_store import get_cognitive_store, is_cognitive_store_enabled
    from core.feature_config import get_config

    if not get_config().app.enable_cognitive_fact:
        fact = await asyncio.to_thread(get_fact, fact_id)
        if not fact:
            raise HTTPException(status_code=404, detail=f"Факт '{fact_id}' не найден")
        return {"enabled": False, "fact": fact}

    if is_cognitive_store_enabled():
        cf = await asyncio.to_thread(
            get_cognitive_store().get,
            fact_id,
            include_relations=include_relations,
            include_raw=include_raw,
        )
    else:
        from core.cognitive_fact import cognitive_fact_from_store, load_relations_for_fact

        fact = await asyncio.to_thread(get_fact, fact_id)
        if not fact:
            cf = None
        else:
            rels = (
                await asyncio.to_thread(load_relations_for_fact, fact_id)
                if include_relations
                else []
            )
            cf = cognitive_fact_from_store(fact, relations=rels)

    if not cf:
        raise HTTPException(status_code=404, detail=f"Факт '{fact_id}' не найден")
    return {"enabled": True, "cognitive_fact": cf.to_dict()}


@app.get(
    "/facts/{fact_id}/relations",
    tags=["Facts", "CognitiveFact", "Causal"],
    dependencies=[Depends(require_api_key)],
)
async def get_fact_relations_endpoint(fact_id: str, limit: int = 20):
    """Preview relations[] из CausalGraph (v9.7 / спринт 3.3)."""
    from core.cognitive_fact import is_relations_preview_enabled, load_relations_for_fact

    if not is_relations_preview_enabled():
        return {
            "enabled": False,
            "hint": "ENABLE_COGNITIVE_FACT=1 и ENABLE_CAUSAL_GRAPH=1",
            "relations": [],
        }
    rels = load_relations_for_fact(fact_id, limit)
    return {
        "enabled": True,
        "fact_id": fact_id,
        "total": len(rels),
        "relations": [r.to_dict() for r in rels],
    }


@app.get(
    "/cognitive/facts",
    tags=["CognitiveFact"],
    dependencies=[Depends(require_api_key)],
)
async def list_cognitive_facts(
    epistemic_state: str | None = None,
    domain: str | None = None,
    include_relations: bool = False,
    limit: int = 100,
    offset: int = 0,
):
    from core.cognitive_store import get_cognitive_store, is_cognitive_store_enabled

    if not is_cognitive_store_enabled():
        return {"enabled": False, "hint": "ENABLE_COGNITIVE_STORE=1"}
    items = await asyncio.to_thread(
        get_cognitive_store().list,
        epistemic_state=epistemic_state,
        domain=domain,
        include_relations=include_relations,
    )
    page = items[offset : offset + limit]
    return {
        "enabled": True,
        "total": len(items),
        "facts": [cf.to_dict() for cf in page],
    }


@app.post(
    "/cognitive/facts",
    tags=["CognitiveFact"],
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def create_cognitive_fact(req: CognitiveFactCreate):
    from core.cognitive_store import (
        CognitiveFactStore,
        get_cognitive_store,
        is_cognitive_store_enabled,
    )

    if not is_cognitive_store_enabled():
        raise HTTPException(status_code=503, detail="ENABLE_COGNITIVE_STORE=1")
    meta = dict(req.metadata)
    if req.domain:
        meta["domain"] = req.domain
    cf = CognitiveFactStore.create_observed(
        req.claim,
        req.source,
        fact_id=req.fact_id,
        confidence=req.confidence,
        metadata=meta,
        raw_input=req.raw_input,
    )
    is_new = await asyncio.to_thread(get_cognitive_store().save, cf)
    saved = await asyncio.to_thread(
        get_cognitive_store().get, cf.id, include_raw=True
    )
    return {
        "created": is_new,
        "cognitive_fact": saved.to_dict() if saved else cf.to_dict(),
    }


@app.post("/facts", tags=["Facts"], status_code=201,
          dependencies=[Depends(require_api_key)])
async def create_fact(req: FactCreate, background_tasks: BackgroundTasks):
    """
    Создать новый факт в памяти.
    Новые факты всегда начинают в состоянии Observed (I50).
    """
    dup = await _find_duplicate_fact(req.claim, req.source)
    if dup:
        logger.info(
            "fact dedup claim → %s", dup.get("fact_id", "?")
        )
        return dup

    fact_id = req.fact_id or f"fact_{uuid.uuid4().hex[:12]}"

    # TASK-09: L0 Raw Memory — сохраняем оригинал ПЕРЕД store_fact
    raw_id: str | None = None
    try:
        raw_id = await asyncio.to_thread(
            store_raw_text, req.claim, req.source, "api_post_fact"
        )
    except Exception as exc:
        logger.warning("L0 raw write failed (non-blocking): %s", exc)

    meta = dict(req.metadata)
    if req.domain:
        meta["domain"] = req.domain
    fact = {
        "fact_id":      fact_id,
        "claim":        req.claim,
        "source":       req.source,
        "confidence":   req.confidence,
        "metadata":     meta,
        "derived_from": raw_id,   # провенанс из L0
    }

    try:
        from core.cognitive_store import (
            CognitiveFactStore,
            get_cognitive_store,
            is_cognitive_store_enabled,
        )

        if is_cognitive_store_enabled():
            cf = CognitiveFactStore.create_observed(
                req.claim,
                req.source,
                fact_id=fact_id,
                confidence=req.confidence,
                metadata=meta,
                raw_input=req.claim,
                derived_from=raw_id,
            )
            if raw_id:
                cf.raw_input = None
            await asyncio.to_thread(
                get_cognitive_store().save,
                cf,
                ensure_raw=not bool(raw_id),
                link_provenance=bool(raw_id),
            )
        else:
            await asyncio.to_thread(store_fact, fact)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if raw_id and not is_cognitive_store_enabled():
        try:
            await asyncio.to_thread(link_raw_to_fact, raw_id, fact_id)
        except Exception as exc:
            logger.warning("L0 provenance link failed (non-blocking): %s", exc)

    # Индексировать в NGram в фоне
    if _ngram and _ngram.available:
        background_tasks.add_task(_ngram.index, fact_id, req.claim)

    stored = await asyncio.to_thread(get_fact, fact_id)
    logger.info("fact created: %s (source=%s)", fact_id, req.source)

    try:
        from core.exocortex_hooks import observe_ingest_chunk

        await observe_ingest_chunk(chunk=req.claim, episode_id=fact_id)
    except Exception as exc:  # noqa: BLE001
        logger.debug("exocortex observe fact: %s", exc)

    return stored


@app.patch("/facts/{fact_id}/transition", tags=["Facts"],
           dependencies=[Depends(require_api_key)])
async def transition_fact(
    fact_id: str,
    req: TransitionRequest,
    x_api_key: str = Header(default=""),
):
    """
    Изменить epistemic state факта (I50 — только через transition_esm).

    AUDIT-FIX v8.4.0: req.by игнорируется. Actor подставляется серверный
    (по hash API-ключа) — защита от подделки audit trail клиентом.

    Разрешённые переходы:
    - Observed → Hypothesized, Supported, Validated, Collapsed
    - Hypothesized → Supported, Validated, Collapsed
    - Supported → Validated, Collapsed
    - Validated → Contradicted, ImmutableCore, Collapsed
    - Contradicted → Deprecated, Collapsed
    - Deprecated → Collapsed
    """
    # AUDIT-FIX v8.4.0: actor = "api:" + первые 8 hex-символов sha256(api_key)
    # Клиент не может подделать историю — req.by игнорируется.
    import hashlib
    actor_id = "api:anon"
    if x_api_key:
        digest = hashlib.sha256(x_api_key.encode("utf-8")).hexdigest()[:8]
        actor_id = f"api:{digest}"

    try:
        ok = await asyncio.to_thread(transition_esm, fact_id, req.new_state, actor_id)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Факт '{fact_id}' не найден")
    except ImmutableStateError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    fact = await asyncio.to_thread(get_fact, fact_id)
    logger.info("fact transition: %s → %s (by=%s, req.by=%r ignored)",
                fact_id, req.new_state, actor_id, req.by)
    return fact


@app.patch("/facts/{fact_id}/invalidate", tags=["Facts"],
           dependencies=[Depends(require_api_key)])
async def invalidate_fact(fact_id: str, req: InvalidateRequest):
    """
    Инвалидировать факт без удаления (I96-a — no DELETE).
    Выставляет t_event_valid_end и/или t_ingestion_end.
    """
    ok = await asyncio.to_thread(
        invalidate_edge, fact_id,
        req.t_event_valid_end, req.t_ingestion_end,
    )
    if not ok:
        raise HTTPException(status_code=404, detail=f"Факт '{fact_id}' не найден")

    fact = await asyncio.to_thread(get_fact, fact_id)
    logger.info("fact invalidated: %s", fact_id)
    return fact


@app.get("/facts/{fact_id}/time-travel", tags=["Facts"],
         dependencies=[Depends(require_api_key)])
async def time_travel(fact_id: str, known_at: str, world_at: str):
    """
    Time-travel запрос (I96): что система знала о факте в момент known_at
    для состояния мира world_at.

    Формат дат: ISO 8601 UTC, например 2026-01-15T12:00:00
    """
    fact = await asyncio.to_thread(get_fact_at, fact_id, known_at, world_at)
    if not fact:
        raise HTTPException(
            status_code=404,
            detail=f"Факт '{fact_id}' не найден для known_at={known_at}, world_at={world_at}",
        )
    return fact


# ── Ingest ────────────────────────────────────────────────────────────────────

@app.post("/ingest/text", tags=["Ingest"], dependencies=[Depends(require_api_key)])
async def ingest_text(req: IngestRequest, background_tasks: BackgroundTasks):
    """
    Загрузить текст в память.
    Текст разбивается на чанки, каждый сохраняется как отдельный факт в Observed.

    Для production: используй FileIngester (RFC0063) напрямую для PDF/DOCX/etc.
    """
    # TASK-09: L0 Raw Memory — сохраняем ПОЛНЫЙ оригинальный текст один раз
    ingest_raw_id: str | None = None
    try:
        ingest_raw_id = await asyncio.to_thread(
            store_raw_text, req.text, req.source, "api_ingest_text"
        )
    except Exception as exc:
        logger.warning("L0 raw write failed for ingest (non-blocking): %s", exc)

    # Разбиваем текст на чанки
    words = req.text.split()
    chunks: list[str] = []
    chunk_words: list[str] = []

    for word in words:
        chunk_words.append(word)
        if len(" ".join(chunk_words)) >= req.chunk_size:
            chunks.append(" ".join(chunk_words))
            chunk_words = []
    if chunk_words:
        chunks.append(" ".join(chunk_words))

    # Собираем все факты и сохраняем одним batch (v8.2.1 оптимизация)
    batch: list[dict] = []
    for i, chunk in enumerate(chunks):
        fact_id = f"ingest_{uuid.uuid4().hex[:10]}"
        batch.append({
            "fact_id":      fact_id,
            "claim":        chunk,
            "source":       req.source,
            "confidence":   req.confidence,
            "metadata":     {**req.metadata, "chunk_index": i, "total_chunks": len(chunks)},
            "derived_from": ingest_raw_id,   # TASK-09: провенанс к оригиналу
        })

    try:
        result = await asyncio.to_thread(store_facts_batch, batch)
        # AUDIT-FIX v8.4.0: используем реальные счётчики из batch_result,
        # а не len(stored_ids) (раньше показывало все ID включая errors).
        real_stored = result.get("stored", 0) + result.get("updated", 0)
        stored_ids = [f["fact_id"] for f in batch[:real_stored]]
        errors = (
            [f"batch error: {result.get('errors', 0)} фактов"]
            if result.get("errors") else []
        )
    except Exception as exc:
        real_stored = 0
        stored_ids = []
        errors = [str(exc)]

    # NGram индексация в фоне — один task на весь batch, не N
    # AUDIT-FIX v8.4.0: было N background_tasks с N SQLite connections.
    # Теперь один task с одним connection.
    if _ngram and _ngram.available:
        async def _batch_index():
            for fact in batch:
                try:
                    _ngram.index(fact["fact_id"], fact["claim"])
                except Exception as exc:
                    logger.debug("NGram index fail %s: %s", fact["fact_id"], exc)
        background_tasks.add_task(_batch_index)

    if real_stored > 0:
        async def _exocortex_observe():
            from core.exocortex_hooks import observe_ingest_chunk

            for fact in batch[:real_stored]:
                try:
                    await observe_ingest_chunk(
                        chunk=fact["claim"],
                        episode_id=fact["fact_id"],
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.debug("exocortex observe chunk %s: %s", fact["fact_id"], exc)

        background_tasks.add_task(_exocortex_observe)

    logger.info("ingest_text: source=%s chunks=%d stored=%d errors=%d",
                req.source, len(chunks), real_stored, len(errors))

    return {
        "stored":   real_stored,
        "fact_ids": stored_ids,
        "chunks":   len(chunks),
        "errors":   errors,
        "source":   req.source,
    }


# ── L6 Horizons MVP / Layers ───────────────────────────────────────────────────

class VolitionBody(BaseModel):
    content: str = Field(..., min_length=1, max_length=50_000)
    user_id: str = Field("default", max_length=128)
    confidence: float = Field(0.85, ge=0.0, le=1.0)
    reason: str = Field("api_volition", max_length=200)
    fact_id: str | None = None


class EtirActivateBody(BaseModel):
    seeds: list[str] = Field(default_factory=list)
    query: str = ""


class ImmutableSnapshotBody(BaseModel):
    node_ids: list[str]
    reason: str = "api_snapshot"


@app.get(
    "/layers/status",
    tags=["Layers", "Horizons"],
    summary="Статус слоёв L0–L6 и Horizons",
    description=(
        "Runtime-слои (on / available_off) и блок `horizons` "
        "(research / experimental). См. docs/LAYERS_AND_HORIZONS.ru.md"
    ),
)
async def layers_status_endpoint():
    from api.exocortex_api import full_layers_status

    return full_layers_status()


@app.get(
    "/profiles",
    tags=["Profiles"],
    summary="Витрина профилей — для кого этот сервер",
    description=(
        "citizen · personal · company · science · research · developer. "
        "Выберите профиль при старте (VELANTRIM_PROFILE) или в POST /query."
    ),
)
async def profiles_list_endpoint():
    from core.deployment_profiles import get_current_profile, list_profiles

    return {
        "hint": "Передайте profile в POST /query или задайте VELANTRIM_PROFILE при старте",
        "current": get_current_profile(),
        "profiles": list_profiles(),
    }


@app.get(
    "/profiles/current",
    tags=["Profiles"],
    summary="Активный профиль сервера (из VELANTRIM_PROFILE)",
)
async def profiles_current_endpoint():
    from core.deployment_profiles import get_current_profile

    cur = get_current_profile()
    if not cur:
        return {
            "active_on_server": False,
            "hint": "Задайте VELANTRIM_PROFILE=citizen|personal|… или config/profiles/*.env",
        }
    return cur


@app.get(
    "/profiles/{profile_id}",
    tags=["Profiles"],
    summary="Один профиль: ориентиры и рекомендуемые API",
)
async def profiles_detail_endpoint(profile_id: str):
    from core.deployment_profiles import get_current_profile_id, get_profile

    try:
        detail = get_profile(profile_id).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    detail["matches_server"] = get_current_profile_id() == detail["id"]
    return detail


@app.get(
    "/titan/status",
    tags=["Titan", "Layers"],
    summary="Статус компонентов Titan v7.5",
    description=(
        "Бюджет фактов (MemoryBudgetPlanner), circuit breakers (LLM), "
        "ACT-R activation, ENV-флаги ENABLE_*."
    ),
    dependencies=[Depends(require_api_key)],
)
async def titan_status_endpoint():
    from api.exocortex_api import titan_status

    return await asyncio.to_thread(titan_status)


@app.get(
    "/horizons",
    tags=["Horizons"],
    summary="Индекс документации Horizons",
    description="Список карточек research/experimental с путями к markdown в репозитории.",
)
async def horizons_index_endpoint():
    from api.exocortex_api import horizons_index

    return horizons_index()


@app.post(
    "/etir/activate",
    tags=["Layers", "ExoCortex"],
    summary="Активация Etir (L3.5a)",
    description="Требует `ENABLE_ETIR=1`. Spreading activation по seeds/query.",
)
async def etir_activate_endpoint(
    body: EtirActivateBody,
    _auth: None = Depends(require_api_key),
):
    from api.exocortex_api import EtirActivateRequest, etir_activate

    return etir_activate(EtirActivateRequest(seeds=body.seeds, query=body.query))


@app.get(
    "/focus",
    tags=["Layers", "ExoCortex"],
    summary="Вектор фокуса (L4.5)",
    description="Требует `ENABLE_L45=1` или `ENABLE_FOCUS_ENGINE=1`.",
)
async def focus_endpoint(user_id: str = "default", _auth: None = Depends(require_api_key)):
    from api.exocortex_api import focus_get

    return focus_get(user_id)


@app.get(
    "/audit/recent",
    tags=["Layers", "ExoCortex"],
    summary="Последние аудиты ответов (L4.5)",
    description="Требует `ENABLE_RESPONSE_AUDIT=1` или `ENABLE_L45=1`.",
)
async def audit_recent_endpoint(limit: int = 20, _auth: None = Depends(require_api_key)):
    from api.exocortex_api import audit_list

    return audit_list(limit)


@app.get(
    "/immutable/snapshots",
    tags=["Layers", "ExoCortex"],
    summary="Список снимков Immutable Core (L3.5b)",
    description="Требует `ENABLE_IMMUTABLE_CORE=1`.",
)
async def immutable_list_endpoint(limit: int = 20, _auth: None = Depends(require_api_key)):
    from api.exocortex_api import immutable_list

    return immutable_list(limit)


@app.post(
    "/immutable/snapshots",
    tags=["Layers", "ExoCortex"],
    summary="Создать снимок Immutable Core",
    description="Требует `ENABLE_IMMUTABLE_CORE=1`. Ring Zero / политики.",
)
async def immutable_create_endpoint(
    body: ImmutableSnapshotBody,
    _auth: None = Depends(require_api_key),
):
    from api.exocortex_api import ImmutableSnapshotRequest, immutable_create

    return await immutable_create(ImmutableSnapshotRequest(**body.model_dump()))


@app.get("/runtime/status", tags=["Runtime", "CognitiveFact"], dependencies=[Depends(require_api_key)])
async def cognitive_runtime_status_endpoint():
    """Unified Cognitive Runtime V10 MVP — store + EventBus + NGram."""
    from core.cognitive_runtime import get_cognitive_runtime, is_cognitive_runtime_enabled

    if not is_cognitive_runtime_enabled():
        return {
            "enabled": False,
            "hint": "ENABLE_COGNITIVE_RUNTIME=1 и ENABLE_COGNITIVE_STORE=1",
        }
    return await asyncio.to_thread(get_cognitive_runtime().status)


@app.get("/graph/analyze", tags=["GraphLab"], dependencies=[Depends(require_api_key)])
async def graph_analyze_endpoint(top_k: int = 20, max_nodes: int = 2000):
    """NetworkX Graph-Analysis Lab — read-only structural analytics over the causal
    graph (centrality / communities / cycles / pagerank). Passive: never writes.
    Gated by ENABLE_GRAPH_LAB; requires the optional `networkx` extra."""
    from core.runtime_flags import is_graph_lab_enabled

    if not is_graph_lab_enabled():
        return {
            "enabled": False,
            "hint": "ENABLE_GRAPH_LAB=1 + pip install -e '.[graph-lab]'",
        }
    from core import graph_lab

    report = await asyncio.to_thread(
        graph_lab.analyze, None, top_k=top_k, max_nodes=max_nodes
    )
    return {"enabled": True, **report}


@app.get("/graph/path", tags=["GraphLab"], dependencies=[Depends(require_api_key)])
async def graph_path_endpoint(
    from_id: str = Query(..., alias="from"),
    to: str | None = None,
    mode: str = "shortest",
    cutoff: int = 5,
    limit: int = 20,
    direction: str = "to",
    max_nodes: int = 2000,
):
    """Causal "why-path" over the graph (read-only):
      mode=shortest → shortest from→to ; mode=all → simple paths from→to ;
      mode=reaches  → ancestors/descendants of `from` (direction=to|from).
    Passive: never writes. Gated by ENABLE_GRAPH_LAB; needs the `networkx` extra."""
    from core.runtime_flags import is_graph_lab_enabled

    if not is_graph_lab_enabled():
        return {
            "enabled": False,
            "hint": "ENABLE_GRAPH_LAB=1 + pip install -e '.[graph-lab]'",
        }
    from core import graph_lab

    if mode == "reaches":
        result = await asyncio.to_thread(
            graph_lab.reaches, from_id, direction=direction, limit=limit, max_nodes=max_nodes
        )
    elif mode == "all":
        if not to:
            raise HTTPException(status_code=400, detail="mode=all requires 'to'")
        result = await asyncio.to_thread(
            graph_lab.all_paths, from_id, to, cutoff=cutoff, limit=limit, max_nodes=max_nodes
        )
    else:  # shortest (default)
        if not to:
            raise HTTPException(status_code=400, detail="mode=shortest requires 'to'")
        result = await asyncio.to_thread(
            graph_lab.shortest_why_path, from_id, to, max_nodes=max_nodes
        )
    return {"enabled": True, "mode": mode, **result}


@app.get("/cross-domain/bridges", tags=["CrossDomain"], dependencies=[Depends(require_api_key)])
async def cross_domain_bridges_endpoint():
    from core.cross_domain import is_cross_domain_enabled, list_bridges

    return {
        "enabled": is_cross_domain_enabled(),
        "bridges": list_bridges(),
        "hint": "ENABLE_CROSS_DOMAIN=1 для multi-domain retrieval в POST /query",
    }


@app.post("/cross-domain/plan", tags=["CrossDomain"], dependencies=[Depends(require_api_key)])
async def cross_domain_plan_endpoint(req: CrossDomainPlanRequest):
    from core.cross_domain import is_cross_domain_enabled, plan_query_async
    from core.domain_tags import normalize_domain

    if not is_cross_domain_enabled():
        return {"enabled": False, "hint": "ENABLE_CROSS_DOMAIN=1"}
    dom = normalize_domain(req.domain) if req.domain else None
    plan = await plan_query_async(req.query, dom)
    return {"enabled": True, "plan": plan.to_dict()}


@app.post("/cross-domain/link-causal", tags=["CrossDomain"], dependencies=[Depends(require_api_key)])
async def cross_domain_link_causal_endpoint(req: CrossDomainPlanRequest):
    """Создать analogous_to рёбра между фактами разных доменов в памяти."""
    from core.cross_domain import (
        is_cross_domain_causal_enabled,
        plan_query,
        sync_cross_domain_edges,
    )
    from core.memory import get_all_facts

    if not is_cross_domain_causal_enabled():
        return {"enabled": False, "hint": "ENABLE_CROSS_DOMAIN_CAUSAL=1"}
    plan = plan_query(req.query, req.domain)
    facts = await asyncio.to_thread(get_all_facts, None, plan.primary_domain)
    for dom in plan.secondary_domains:
        facts.extend(await asyncio.to_thread(get_all_facts, None, dom))
    links = await asyncio.to_thread(sync_cross_domain_edges, facts[:20], plan)
    return {"enabled": True, "plan": plan.to_dict(), "causal_links": links}


@app.get("/umwelt/agents", tags=["Umwelt"], dependencies=[Depends(require_api_key)])
async def umwelt_agents_endpoint():
    """PolyWeltRegistry — 6 MVP-перцепторов."""
    from core.poly_welt_registry import list_agents
    from core.runtime_flags import is_umwelt_store_enabled

    return {
        "enabled": is_umwelt_store_enabled(),
        "total": 6,
        "agents": list_agents(),
    }


@app.get("/umwelt/objects", tags=["Umwelt"], dependencies=[Depends(require_api_key)])
async def umwelt_objects_endpoint():
    from core.runtime_flags import is_umwelt_store_enabled
    from core.umwelt_store import get_umwelt_store

    if not is_umwelt_store_enabled():
        return {"enabled": False, "hint": "ENABLE_UMWELT_STORE=1"}
    objects = await asyncio.to_thread(get_umwelt_store().list_objects)
    return {"enabled": True, "objects": objects, "total": len(objects)}


@app.get("/umwelt/perceptions", tags=["Umwelt"], dependencies=[Depends(require_api_key)])
async def umwelt_perceptions_endpoint(
    object_key: str | None = None,
    query: str | None = None,
    limit: int = 20,
):
    from core.runtime_flags import is_umwelt_store_enabled
    from core.umwelt_registry import (
        detect_object_key,
        ensure_seed_loaded,
        perceptions_to_lens_format,
        resolve_perceptions,
    )

    if not is_umwelt_store_enabled():
        return {"enabled": False, "hint": "ENABLE_UMWELT_STORE=1"}
    await asyncio.to_thread(ensure_seed_loaded)
    obj = object_key or (detect_object_key(query or "") if query else None)
    if not obj:
        return {
            "enabled": True,
            "object_key": None,
            "perceptions": [],
            "hint": "Укажите object_key или query с объектом (дерево, дождь, дом)",
        }
    _, items = await asyncio.to_thread(resolve_perceptions, query or "", object_key=obj)
    return {
        "enabled": True,
        "object_key": obj,
        "total": len(items),
        "perceptions": [p.to_dict() for p in items],
        "lens_format": perceptions_to_lens_format(items),
    }


@app.post("/umwelt/perceptions", tags=["Umwelt"], status_code=201,
          dependencies=[Depends(require_api_key)])
async def umwelt_create_perception_endpoint(req: UmweltPerceptionCreate):
    import uuid

    from core.runtime_flags import is_umwelt_store_enabled
    from core.umwelt_store import UmweltPerception, get_umwelt_store

    if not is_umwelt_store_enabled():
        raise HTTPException(status_code=503, detail="ENABLE_UMWELT_STORE=1")
    pid = req.perception_id or f"perception.{req.object_key}.{uuid.uuid4().hex[:8]}"
    p = UmweltPerception(
        perception_id=pid,
        object_key=req.object_key,
        object_label_ru=req.object_label_ru,
        perceiver_id=req.perceiver_id,
        perceiver=req.perceiver,
        perceiver_category=req.perceiver_category,
        statement=req.statement,
        affordances=req.affordances,
        knowledge_status=req.knowledge_status,
        confidence=req.confidence,
        related_perceptions=req.related_perceptions,
        metadata={"domain": "perception", "layer": 99},
    )
    stored = await asyncio.to_thread(get_umwelt_store().upsert, p)
    return stored.to_dict()


@app.post("/umwelt/seed", tags=["Umwelt"], dependencies=[Depends(require_api_key)])
async def umwelt_load_seed_endpoint(req: UmweltSeedRequest):
    from core.runtime_flags import is_umwelt_store_enabled
    from core.umwelt_store import load_seed_file, sync_perceptions_to_memory

    if not is_umwelt_store_enabled():
        raise HTTPException(status_code=503, detail="ENABLE_UMWELT_STORE=1")
    result = await asyncio.to_thread(load_seed_file)
    if req.sync_to_memory:
        sync = await asyncio.to_thread(
            sync_perceptions_to_memory, req.object_key
        )
        result["memory_sync"] = sync
    return result


@app.post("/telegram/ingest", tags=["Telegram"], status_code=201,
          dependencies=[Depends(require_api_key)])
async def telegram_ingest_endpoint(req: TelegramIngestRequest):
    """
    Ручной ingest как из Telegram (L0 raw → L1 Observed fact).
    Для тестов без webhook.
    """
    from app.telegram_ingest import ingest_telegram_message, is_telegram_enabled

    if not is_telegram_enabled():
        raise HTTPException(
            status_code=503,
            detail="ENABLE_TELEGRAM_INGEST=1",
        )
    try:
        result = await asyncio.to_thread(
            ingest_telegram_message,
            req.text,
            chat_id=req.chat_id,
            user_id=req.user_id,
            message_id=req.message_id,
            username=req.username,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if req.reply:
        from app.telegram_ingest import get_bot_token, send_telegram_reply

        if get_bot_token():
            await send_telegram_reply(
                req.chat_id,
                f"✅ {result['fact_id']}",
            )
    return result


@app.post("/telegram/webhook", tags=["Telegram"])
async def telegram_webhook_endpoint(
    update: dict[str, Any],
    x_telegram_bot_api_secret_token: str | None = Header(None),
):
    """
    Webhook Telegram Bot API → L0/L1.
    Задайте TELEGRAM_WEBHOOK_SECRET и тот же secret в setWebhook.
    Auth API key не требуется — проверяется secret Telegram.
    """
    from app.telegram_ingest import (
        get_bot_token,
        ingest_telegram_message,
        is_telegram_enabled,
        parse_telegram_update,
        send_telegram_reply,
    )

    if not is_telegram_enabled():
        return {"ok": False, "error": "ENABLE_TELEGRAM_INGEST=0"}

    # SECURITY (audit fix): fail-closed — без секрета вебхук НЕ принимает анонимов
    # (раньше при незаданном TELEGRAM_WEBHOOK_SECRET любой мог писать в память).
    import hmac

    expected = (os.getenv("TELEGRAM_WEBHOOK_SECRET") or "").strip()
    if not expected:
        raise HTTPException(status_code=403, detail="TELEGRAM_WEBHOOK_SECRET не задан (fail-closed)")
    if not hmac.compare_digest((x_telegram_bot_api_secret_token or ""), expected):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    parsed = parse_telegram_update(update)
    if not parsed:
        return {"ok": True, "skipped": "no_text_message"}

    try:
        result = await asyncio.to_thread(
            ingest_telegram_message,
            parsed["text"],
            chat_id=parsed["chat_id"],
            user_id=parsed.get("user_id"),
            message_id=parsed.get("message_id"),
            username=parsed.get("username"),
        )
    except ValueError as exc:
        if get_bot_token():
            await send_telegram_reply(parsed["chat_id"], f"❌ {exc}")
        raise HTTPException(status_code=400, detail=str(exc))

    if get_bot_token():
        await send_telegram_reply(
            parsed["chat_id"],
            f"✅ Память: {result['fact_id']}",
        )
    return {"ok": True, **result}


@app.get("/telegram/status", tags=["Telegram"], dependencies=[Depends(require_api_key)])
async def telegram_status_endpoint():
    from app.telegram_ingest import get_bot_token, is_telegram_enabled

    token = get_bot_token()
    return {
        "enabled": is_telegram_enabled(),
        "bot_token_configured": bool(token),
        "webhook_secret_configured": bool(
            (os.getenv("TELEGRAM_WEBHOOK_SECRET") or "").strip()
        ),
        "hint": "polling: python -m app.telegram_bot",
    }


@app.get("/router/modes", tags=["ModeRouter"], dependencies=[Depends(require_api_key)])
async def router_modes_endpoint():
    from core.router.mode_router import is_mode_router_enabled, list_lens_modes

    modes = list_lens_modes()
    return {
        "enabled": is_mode_router_enabled(),
        "modes": modes,
        "hint": "Передайте response_lens в POST /query",
    }


@app.post("/router/route", tags=["ModeRouter"], dependencies=[Depends(require_api_key)])
async def router_dry_run_endpoint(req: RouterRouteRequest):
    """Dry-run линзы без полного pipeline (для UI/отладки)."""
    from core.router.mode_router import apply_lens, is_mode_router_enabled

    if not is_mode_router_enabled():
        return {"enabled": False, "hint": "ENABLE_MODE_ROUTER=1"}
    routed = apply_lens(
        req.query, [], req.response_lens, user_id=req.user_id
    )
    return {
        "enabled": True,
        "lens": routed.lens,
        "system_instructions": routed.system_instructions,
        "lens_meta": routed.lens_meta,
        "cognitive_mode_hint": routed.cognitive_mode_hint,
    }


@app.get("/goals", tags=["Innenwelt"], dependencies=[Depends(require_api_key)])
async def list_goals_endpoint(
    user_id: str = "default",
    status: str | None = "active",
    limit: int = 50,
):
    from core.goal_stack import get_goal_stack
    from core.runtime_flags import is_innenwelt_enabled

    if not is_innenwelt_enabled():
        return {"enabled": False, "hint": "ENABLE_INNENWELT=1"}
    goals = await asyncio.to_thread(
        get_goal_stack().list_goals, user_id, status=status, limit=limit
    )
    return {
        "enabled": True,
        "user_id": user_id,
        "total": len(goals),
        "goals": [g.to_dict() for g in goals],
    }


@app.post("/goals", tags=["Innenwelt"], status_code=201,
          dependencies=[Depends(require_api_key)])
async def create_goal_endpoint(req: GoalCreate):
    from core.goal_stack import get_goal_stack
    from core.runtime_flags import is_innenwelt_enabled

    if not is_innenwelt_enabled():
        raise HTTPException(
            status_code=503,
            detail="Innenwelt отключён. Установите ENABLE_INNENWELT=1",
        )
    goal = await asyncio.to_thread(
        get_goal_stack().create,
        user_id=req.user_id,
        title=req.title,
        description=req.description,
        priority=req.priority,
        keywords=req.keywords,
    )
    return goal.to_dict()


@app.patch("/goals/{goal_id}", tags=["Innenwelt"],
           dependencies=[Depends(require_api_key)])
async def update_goal_status_endpoint(goal_id: str, req: GoalStatusUpdate):
    from core.goal_stack import get_goal_stack
    from core.runtime_flags import is_innenwelt_enabled

    if not is_innenwelt_enabled():
        raise HTTPException(status_code=503, detail="ENABLE_INNENWELT=1")
    try:
        updated = await asyncio.to_thread(
            get_goal_stack().update_status, goal_id, req.status
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Цель '{goal_id}' не найдена")
    return updated.to_dict()


@app.get("/gaps", tags=["Innenwelt"], dependencies=[Depends(require_api_key)])
async def list_gaps_endpoint(user_id: str = "default"):
    from core.gap_detector import detect_gaps
    from core.runtime_flags import is_innenwelt_enabled

    if not is_innenwelt_enabled():
        return {"enabled": False, "hint": "ENABLE_INNENWELT=1"}
    gaps = await asyncio.to_thread(detect_gaps, user_id)
    return {"enabled": True, "user_id": user_id, "total": len(gaps), "gaps": gaps}


@app.get("/innenwelt", tags=["Innenwelt"], dependencies=[Depends(require_api_key)])
async def innenwelt_snapshot_endpoint(user_id: str = "default"):
    """Сводка внутреннего мира: цели, пробелы, welfare."""
    from core.gap_detector import detect_gaps
    from core.goal_stack import get_goal_stack
    from core.runtime_flags import is_innenwelt_enabled, is_l6_welfare_enabled

    if not is_innenwelt_enabled():
        return {"enabled": False, "hint": "ENABLE_INNENWELT=1"}
    goals = await asyncio.to_thread(
        get_goal_stack().list_goals, user_id, status="active", limit=50
    )
    gaps = await asyncio.to_thread(detect_gaps, user_id)
    out: dict[str, Any] = {
        "enabled": True,
        "user_id": user_id,
        "active_goals": [g.to_dict() for g in goals],
        "gaps": gaps,
    }
    if is_l6_welfare_enabled():
        from core.welfare_monitor import get_welfare_monitor

        out["welfare"] = get_welfare_monitor(user_id).snapshot().to_dict()
    return out


@app.get("/welfare", tags=["Layers", "Horizons"], dependencies=[Depends(require_api_key)])
async def welfare_endpoint(user_id: str = "default"):
    from core.runtime_flags import is_l6_welfare_enabled
    from core.welfare_monitor import get_welfare_monitor

    if not is_l6_welfare_enabled():
        return {
            "enabled": False,
            "status": "research",
            "hint": "ENABLE_L6_WELFARE=1 и ENABLE_EVENT_BUS=1",
        }
    snap = get_welfare_monitor(user_id).snapshot()
    return {"enabled": True, "user_id": user_id, "welfare": snap.to_dict()}


@app.post("/memory/volition", tags=["Layers", "Horizons"],
          dependencies=[Depends(require_api_key)])
async def memory_volition_endpoint(body: VolitionBody):
    from core.memory_volition import VolitionRequest, voluntary_write

    result = await voluntary_write(
        VolitionRequest(
            content=body.content,
            user_id=body.user_id,
            confidence=body.confidence,
            reason=body.reason,
            fact_id=body.fact_id,
        )
    )
    if result.get("volition_blocked"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result)
    return result


@app.get("/eventbus/metrics", tags=["Layers"], dependencies=[Depends(require_api_key)])
async def eventbus_metrics():
    from core.event_bus import get_event_bus
    from core.runtime_flags import is_event_bus_enabled

    if not is_event_bus_enabled():
        return {"enabled": False}
    m = get_event_bus().get_metrics()
    return {
        "enabled": True,
        "size": m.size,
        "peak_size": m.peak_size,
        "overflow_count": m.overflow_count,
        "dlq_size": m.dlq_size,
        "published_total": m.published_total,
        "consumed_total": m.consumed_total,
    }


# ── Memory / Stats ────────────────────────────────────────────────────────────

@app.get("/memory/ops/status", tags=["MemoryOps"], dependencies=[Depends(require_api_key)])
async def memory_ops_status_endpoint():
    from core.memory_ops import memory_ops_status

    return await asyncio.to_thread(memory_ops_status)


@app.post("/sources", tags=["MemoryOps"], status_code=201,
          dependencies=[Depends(require_api_key)])
async def register_source_endpoint(req: SourceRegisterRequest):
    from core.memory_ops import get_memory_ops

    try:
        return await asyncio.to_thread(
            get_memory_ops().register_source,
            source_type=req.source_type,
            label=req.label,
            uri=req.uri,
            trust=req.trust,
            metadata=req.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/sources", tags=["MemoryOps"], dependencies=[Depends(require_api_key)])
async def list_sources_endpoint(
    source_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    from core.memory_ops import get_memory_ops

    return await asyncio.to_thread(
        get_memory_ops().list_sources,
        source_type=source_type,
        limit=max(1, min(limit, 500)),
        offset=max(0, offset),
    )


@app.get("/sources/{source_id}", tags=["MemoryOps"], dependencies=[Depends(require_api_key)])
async def get_source_endpoint(source_id: str):
    from core.memory_ops import get_memory_ops

    source = await asyncio.to_thread(get_memory_ops().get_source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Источник '{source_id}' не найден")
    return source


@app.post("/memory/inbox", tags=["MemoryOps"], status_code=201,
          dependencies=[Depends(require_api_key)])
async def enqueue_fact_inbox_endpoint(req: FactInboxCreateRequest):
    from core.memory_ops import get_memory_ops

    try:
        return await asyncio.to_thread(
            get_memory_ops().enqueue_fact,
            claim=req.claim,
            source_id=req.source_id,
            confidence=req.confidence,
            metadata=req.metadata,
            raw_id=req.raw_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/memory/inbox", tags=["MemoryOps"], dependencies=[Depends(require_api_key)])
async def list_fact_inbox_endpoint(
    status: str | None = "pending",
    limit: int = 100,
    offset: int = 0,
):
    from core.memory_ops import get_memory_ops

    try:
        return await asyncio.to_thread(
            get_memory_ops().list_inbox,
            status=status,
            limit=max(1, min(limit, 500)),
            offset=max(0, offset),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/memory/inbox/{inbox_id}/status", tags=["MemoryOps"],
           dependencies=[Depends(require_api_key)])
async def update_fact_inbox_status_endpoint(
    inbox_id: str,
    req: FactInboxStatusRequest,
):
    from core.memory_ops import get_memory_ops

    try:
        item = await asyncio.to_thread(
            get_memory_ops().set_inbox_status,
            inbox_id,
            req.status,
            reason=req.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=404, detail=f"Inbox item '{inbox_id}' не найден")
    return item


@app.post("/memory/inbox/{inbox_id}/promote", tags=["MemoryOps"],
          dependencies=[Depends(require_api_key)])
async def promote_fact_inbox_endpoint(
    inbox_id: str,
    req: FactInboxPromoteRequest,
):
    from core.memory_ops import get_memory_ops

    try:
        return await asyncio.to_thread(
            get_memory_ops().promote_inbox_item,
            inbox_id,
            fact_id=req.fact_id,
        )
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@app.get("/memory/diff", tags=["MemoryOps"], dependencies=[Depends(require_api_key)])
async def memory_diff_endpoint(since: str | None = None, limit: int = 100):
    from core.memory_ops import get_memory_ops

    try:
        return await asyncio.to_thread(
            get_memory_ops().memory_diff,
            since=since,
            limit=max(1, min(limit, 500)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/memory/traces", tags=["MemoryOps"], status_code=201,
          dependencies=[Depends(require_api_key)])
async def create_reasoning_trace_endpoint(req: ReasoningTraceCreateRequest):
    from core.memory_ops import get_memory_ops

    try:
        return await asyncio.to_thread(
            get_memory_ops().save_trace,
            query=req.query,
            answer=req.answer,
            mode=req.mode,
            response_lens=req.response_lens,
            source_fact_ids=req.source_fact_ids,
            rejected_fact_ids=req.rejected_fact_ids,
            notes=req.notes,
            metadata=req.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/memory/traces", tags=["MemoryOps"], dependencies=[Depends(require_api_key)])
async def list_reasoning_traces_endpoint(limit: int = 50, offset: int = 0):
    from core.memory_ops import get_memory_ops

    return await asyncio.to_thread(
        get_memory_ops().list_traces,
        limit=max(1, min(limit, 500)),
        offset=max(0, offset),
    )


@app.get("/memory/traces/{trace_id}", tags=["MemoryOps"], dependencies=[Depends(require_api_key)])
async def get_reasoning_trace_endpoint(trace_id: str):
    from core.memory_ops import get_memory_ops

    trace = await asyncio.to_thread(get_memory_ops().get_trace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' не найден")
    return trace


@app.get("/console/notes", tags=["ConsoleNotes"], dependencies=[Depends(require_api_key)])
async def list_console_notes_endpoint(limit: int = 100):
    from core.console_notes import ConsoleNotesStore

    return {
        "notes": await asyncio.to_thread(
            ConsoleNotesStore().list_notes,
            limit=max(1, min(limit, 500)),
        )
    }


@app.post("/console/notes", tags=["ConsoleNotes"], status_code=201,
          dependencies=[Depends(require_api_key)])
async def create_console_note_endpoint(req: ConsoleNoteCreateRequest):
    from core.console_notes import ConsoleNotesStore

    return await asyncio.to_thread(
        ConsoleNotesStore().create_note,
        req.content,
        title=req.title,
        tags=req.tags,
    )


@app.get("/console/notes/{note_id}", tags=["ConsoleNotes"], dependencies=[Depends(require_api_key)])
async def get_console_note_endpoint(note_id: str):
    from core.console_notes import ConsoleNotesStore

    note = await asyncio.to_thread(ConsoleNotesStore().get_note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' не найдена")
    return note


@app.patch("/console/notes/{note_id}", tags=["ConsoleNotes"],
           dependencies=[Depends(require_api_key)])
async def update_console_note_endpoint(note_id: str, req: ConsoleNoteUpdateRequest):
    from core.console_notes import ConsoleNotesStore

    note = await asyncio.to_thread(
        ConsoleNotesStore().update_note,
        note_id,
        title=req.title,
        content=req.content,
        tags=req.tags,
    )
    if not note:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' не найдена")
    return note


@app.post("/console/notes/{note_id}/edit", tags=["ConsoleNotes"],
          dependencies=[Depends(require_api_key)])
async def edit_console_note_endpoint(note_id: str, req: ConsoleNoteEditRequest):
    from core.console_notes import ConsoleNotesStore, apply_note_instruction

    store = ConsoleNotesStore()
    note = await asyncio.to_thread(store.get_note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' не найдена")
    patch = apply_note_instruction(note, req.instruction)
    return await asyncio.to_thread(
        store.update_note,
        note_id,
        title=patch.get("title"),
        content=patch.get("content"),
    )


@app.delete("/console/notes/{note_id}", tags=["ConsoleNotes"],
            dependencies=[Depends(require_api_key)])
async def delete_console_note_endpoint(note_id: str):
    from core.console_notes import ConsoleNotesStore

    deleted = await asyncio.to_thread(ConsoleNotesStore().delete_note, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' не найдена")
    return {"deleted": True, "note_id": note_id}


@app.get("/memory/stats", tags=["Memory"], dependencies=[Depends(require_api_key)])
async def memory_stats():
    """
    Статистика памяти: факты по состояниям, MHI, NGram.
    """
    all_facts = await asyncio.to_thread(get_all_facts)

    by_state: dict[str, int] = {}
    by_source: dict[str, int] = {}
    total_confidence = 0.0

    for f in all_facts:
        state = f.get("epistemic_state", "unknown")
        source = f.get("source", "unknown")
        by_state[state] = by_state.get(state, 0) + 1
        by_source[source] = by_source.get(source, 0) + 1
        total_confidence += f.get("confidence", 0)

    total = len(all_facts)
    avg_confidence = round(total_confidence / total, 3) if total else 0.0

    # MHI
    try:
        mhi_status = await asyncio.to_thread(check_mhi, _store)
        mhi_value = mhi_status.value
    except Exception:
        mhi_value = "unknown"

    return {
        "total_facts":     total,
        "by_state":        by_state,
        "by_source":       dict(sorted(by_source.items(), key=lambda x: -x[1])[:10]),
        "avg_confidence":  avg_confidence,
        "mhi_status":      mhi_value,
        "ngram_available": bool(_ngram and _ngram.available),
        "ngram_indexed":   _ngram.count() if _ngram and _ngram.available else 0,
        "db_path":         DB_PATH,
    }


@app.post("/memory/consolidate", tags=["Memory"],
          dependencies=[Depends(require_api_key)])
async def memory_consolidate():
    """
    ConsolidationEngine (Спринт 1): Observed с confidence ≥ порога → Validated.
    """
    from core.consolidation_engine import run_consolidation

    report = await asyncio.to_thread(run_consolidation)
    return report.to_dict()


@app.post(
    "/causal/reload-from-graph",
    tags=["Causal"],
    dependencies=[Depends(require_api_key)],
)
async def causal_reload_from_graph_endpoint():
    """
    Graphiti/Neo4j → CausalGraph (Спринт 2.5, опционально).

    Требует STORAGE_BACKEND=neo4j|graphiti и graphiti_core.
    """
    from core.graphiti_adapter import reload_causal_from_graphiti

    return await reload_causal_from_graphiti()


@app.post("/memory/rebuild-index", tags=["Memory"],
          dependencies=[Depends(require_api_key)])
async def rebuild_index(background_tasks: BackgroundTasks):
    """
    Перестроить NGram индекс по всем фактам в памяти.
    Запускается в фоне — не блокирует.
    """
    if not _ngram or not _ngram.available:
        raise HTTPException(status_code=503, detail="NGramIndex недоступен (нет FTS5)")

    async def _rebuild():
        facts = await asyncio.to_thread(get_all_facts)
        count = _ngram.rebuild(facts)
        logger.info("NGramIndex перестроен: %d фактов", count)

    background_tasks.add_task(_rebuild)
    return {"status": "rebuild started", "message": "Проверь /memory/stats через несколько секунд"}


# ── SleepTimeWorker ───────────────────────────────────────────────────────────

@app.get("/agent/notebook", tags=["Agent"], dependencies=[Depends(require_api_key)])
async def get_notebook():
    """
    Блокнот агента: цели, профиль, предложения следующих шагов.
    Доступно только если SleepTimeWorker запущен.
    """
    if not _sleep_worker:
        raise HTTPException(status_code=503,
                            detail="SleepTimeWorker не запущен. "
                                   "Установи SLEEP_WORKER_ENABLED=true.")
    try:
        notebook = await _sleep_worker.get_notebook()
        return notebook
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/agent/suggest", tags=["Agent"], dependencies=[Depends(require_api_key)])
async def suggest_next_step():
    """
    Предложение следующего шага от SleepTimeWorker.
    """
    if not _sleep_worker:
        raise HTTPException(status_code=503, detail="SleepTimeWorker не запущен.")
    try:
        suggestion = await _sleep_worker.suggest_next_step()
        return {"suggestion": suggestion}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/agent/episode", tags=["Agent"], dependencies=[Depends(require_api_key)])
async def update_episode(episode: EpisodeRequest):
    """
    Обновить SleepTimeWorker из нового эпизода взаимодействия.

    AUDIT-FIX v8.4.0: вместо Dict[str, Any] теперь EpisodeRequest с
    Pydantic-валидацией. Content ограничен 10_000 символов — защита
    от prompt injection и DoS на LLM.
    """
    if not _sleep_worker:
        raise HTTPException(status_code=503, detail="SleepTimeWorker не запущен.")
    try:
        await _sleep_worker.update_from_episode(episode.model_dump())
        return {"status": "updated"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Error handlers ────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": str(exc)},
    )


# ─── Запуск ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=LOG_LEVEL.lower(),
        workers=1,  # SQLite не любит multi-process, Sprint 2c → PostgreSQL/Neo4j
    )
