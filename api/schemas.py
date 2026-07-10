"""Pydantic request/response schemas for server.py HTTP API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


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


class QueryRolesRequest(BaseModel):
    query: str
    roles: str | None = None        # comma-separated: "ENGINEER,CRITIC"
    cognitive_mode: str | None = None
    domain: str | None = None


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