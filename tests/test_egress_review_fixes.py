"""Регрессии по review-находкам PR #59 (F1, F2, F3 + аудит H5).

Что закрывается:

* **H5** — `model_allowed_for_provider` была написана и экспортирована, но не
  имела ни одного вызова вне тестов, а `model` из тела запроса подставлялся в
  *путь* Gemini-эндпоинта без валидации. Измерено пробником на httpx:
  `../../v1beta/tunedModels` сворачивается в другой путь API,
  `gemini-2.5-flash?key=leak` превращается в инъекцию query, `...#` отбрасывает
  суффикс `:generateContent`. Всё — с ключом сервера в заголовке.
* **F1** — опечатка в egress-переменной не валила загрузку: `PolicyKernel`
  падал closed, но сервер поднимался и молча переставал сохранять факты.
* **F3** — hardened-профиль не закреплял ни одну из двух переменных.
"""
from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


# ── H5: структурная валидация model id ──────────────────────────────────────

ATTACK_PAYLOADS = [
    "../../v1beta/tunedModels",
    "..%2f..%2fv1beta%2ftunedModels",
    "gemini-2.5-flash?key=leak",
    "gemini-2.5-flash#",
    "gemini-2.5-flash:streamGenerateContent",
    "gemini-2.5-flash/../../tunedModels",
    "",
    "   ",
    "not-a-gemini-model",
    "GEMINI-2.5-FLASH",
]


@pytest.mark.parametrize("payload", ATTACK_PAYLOADS)
def test_assert_safe_gemini_model_id_rejects(payload: str):
    from core.gemini_models import assert_safe_gemini_model_id

    with pytest.raises(ValueError):
        assert_safe_gemini_model_id(payload)


def test_assert_safe_gemini_model_id_accepts_every_catalog_id():
    """Подключение ранее неиспользуемого валидатора не должно ломать легитимное.

    Это главный риск такой правки: валидатор мог отклонять реальные модели.
    """
    from core.gemini_models import (
        GEMINI_DEFAULT_MODEL,
        GEMINI_MODEL_SPECS,
        GEMINI_STT_DEFAULT_MODEL,
        GEMINI_STT_FALLBACK_MODELS,
        assert_safe_gemini_model_id,
        ordered_gemini_model_ids,
    )

    ids = (
        set(ordered_gemini_model_ids())
        | set(GEMINI_MODEL_SPECS)
        | {GEMINI_DEFAULT_MODEL, GEMINI_STT_DEFAULT_MODEL}
        | set(GEMINI_STT_FALLBACK_MODELS)
    )
    assert ids, "каталог пуст — тест перестал что-либо проверять"
    for model in sorted(ids):
        assert assert_safe_gemini_model_id(model) == model


def test_assert_safe_gemini_model_id_accepts_gemini_tts_models():
    """TTS-модели живут в tts_router, вне каталога gemini_models."""
    from core.gemini_models import assert_safe_gemini_model_id
    from core.tts_router import DEFAULT_GEMINI_TTS_MODEL, GEMINI_TTS_MODELS

    for model in {DEFAULT_GEMINI_TTS_MODEL, *GEMINI_TTS_MODELS}:
        assert assert_safe_gemini_model_id(model) == model


def test_models_prefix_is_normalized_not_rejected():
    from core.gemini_models import assert_safe_gemini_model_id

    assert assert_safe_gemini_model_id("models/gemini-2.5-flash") == "gemini-2.5-flash"


# ── H5: валидация стоит во ВСЕХ точках сборки URL ───────────────────────────

def test_generate_url_rejects_payloads():
    from core.llm_router import _gemini_generate_url

    assert _gemini_generate_url("v1beta", "gemini-2.5-flash").endswith(
        "/v1beta/models/gemini-2.5-flash:generateContent"
    )
    for payload in ("../../v1beta/tunedModels", "gemini-2.5-flash?x=1"):
        with pytest.raises(ValueError):
            _gemini_generate_url("v1beta", payload)


def test_generate_url_rejects_unknown_api_version():
    """api_version тоже path-сегмент, пусть сейчас и не управляется извне."""
    from core.llm_router import _gemini_generate_url

    with pytest.raises(ValueError):
        _gemini_generate_url("../v1internal", "gemini-2.5-flash")


def test_every_gemini_url_construction_site_validates():
    """Точек сборки Gemini URL три, не одна — и все должны валидировать.

    Фикс только в llm_router пропустил бы streaming (llm_stream) и TTS
    (tts_router): оба собирают путь самостоятельно.
    """
    import core.llm_router as router
    import core.llm_stream as stream
    import core.tts_router as tts

    for module in (router, stream, tts):
        source = inspect.getsource(module)
        sites = [
            line
            for line in source.splitlines()
            if "/models/" in line and "{" in line
        ]
        assert sites, f"{module.__name__}: точка сборки URL не найдена — тест устарел"
        tree = ast.parse(source)
        called = {
            n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
        }
        assert "assert_safe_gemini_model_id" in called, (
            f"{module.__name__} строит Gemini URL, но не валидирует model id"
        )


# ── H5: политика (deprecation/каталог) перестала быть декоративной ──────────

def test_model_allowed_for_provider_has_a_production_caller():
    """Ровно то, что нашёл аудит: 0 вызовов вне тестов."""
    hits: list[str] = []
    for path in (REPO / "core").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "model_allowed_for_provider" not in text:
            continue
        if path.name == "gemini_models.py":
            continue  # определение + __all__
        hits.append(str(path.relative_to(REPO)))
    assert hits, "model_allowed_for_provider снова не вызывается из продакшн-кода"


def test_assert_model_allowed_rejects_deprecated_model():
    from core.gemini_models import _GEMINI_DEPRECATED_IDS
    from core.llm_router import LlmCallConfig, assert_model_allowed

    deprecated = sorted(_GEMINI_DEPRECATED_IDS)
    if not deprecated:
        pytest.skip("список устаревших моделей пуст")
    cfg = LlmCallConfig(provider="gemini", api_key="k", model=deprecated[0])
    with pytest.raises(ValueError):
        assert_model_allowed(cfg)


def test_assert_model_allowed_allows_non_gemini_providers():
    """У openai/anthropic model уходит в JSON-тело, не в путь — не ограничиваем."""
    from core.llm_router import LlmCallConfig, assert_model_allowed

    for provider, model in (
        ("openai", "gpt-4o-mini"),
        ("anthropic", "claude-sonnet-4-20250514"),
        ("deepseek", "deepseek-v4-flash"),
    ):
        assert_model_allowed(LlmCallConfig(provider=provider, api_key="k", model=model))


@pytest.mark.asyncio
async def test_policy_check_runs_before_the_egress_lease(monkeypatch: pytest.MonkeyPatch):
    """Отклонение модели не должно тратить lease."""
    import core.llm_router as router

    leases: list[str] = []
    monkeypatch.setattr(
        router,
        "ensure_remote_egress_allowed",
        lambda *a, **k: leases.append("lease"),
    )
    cfg = router.LlmCallConfig(provider="gemini", api_key="k", model="../../evil")

    with pytest.raises(ValueError):
        await router.chat_complete(cfg, "prompt")

    assert leases == [], "lease был взят для заведомо отклоняемого вызова"


# ── F1: неверная ENV валит загрузку ─────────────────────────────────────────

def test_validate_egress_env_accepts_defaults(monkeypatch: pytest.MonkeyPatch):
    from core.policy_kernel import NetworkMode, RemoteDataMode, validate_egress_env

    monkeypatch.delenv("VELANTRIM_NETWORK_MODE", raising=False)
    monkeypatch.delenv("VELANTRIM_REMOTE_DATA_MODE", raising=False)
    policy = validate_egress_env()
    assert policy.network is NetworkMode.DENY
    assert policy.remote_data is RemoteDataMode.NEVER


@pytest.mark.parametrize(
    "var", ["VELANTRIM_NETWORK_MODE", "VELANTRIM_REMOTE_DATA_MODE"]
)
def test_validate_egress_env_rejects_garbage(var: str, monkeypatch: pytest.MonkeyPatch):
    from core.policy_kernel import validate_egress_env

    monkeypatch.setenv(var, "definitely-not-a-mode")
    with pytest.raises(ValueError) as exc:
        validate_egress_env()
    assert var in str(exc.value)


def test_validate_egress_env_accepts_every_enum_value(monkeypatch: pytest.MonkeyPatch):
    from core.policy_kernel import NetworkMode, RemoteDataMode, validate_egress_env

    for net in NetworkMode:
        for data in RemoteDataMode:
            monkeypatch.setenv("VELANTRIM_NETWORK_MODE", net.value)
            monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", data.value)
            policy = validate_egress_env()
            assert policy.network is net
            assert policy.remote_data is data


def test_server_validates_egress_env_at_import_time():
    """Проверка должна стоять на уровне модуля, а не внутри функции.

    Иначе она не сработает при загрузке и мы вернёмся к тихому read-only.
    """
    source = (REPO / "server.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    module_level_calls = {
        node.func.id
        for stmt in tree.body
        for node in ast.walk(stmt)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "validate_egress_env" in module_level_calls, (
        "validate_egress_env() не вызывается на уровне модуля server.py"
    )


# ── F4: мёртвый необёрнутый egress удалён ───────────────────────────────────

def test_no_ungated_provider_calls_remain_in_server():
    """server.py больше не зовёт провайдеров напрямую.

    Функции были недостижимы, но представляли рабочую копию пути без lease и
    без санитизации промпта. Инвариант «весь egress к провайдеру идёт через
    core.remote_egress» должен быть структурным, а не следствием формы
    control flow — то есть проверяемым grep'ом, а не трассировкой.
    """
    source = (REPO / "server.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "_anthropic_complete" not in defined
    assert "_openai_complete" not in defined

    for host in ("api.anthropic.com", "api.openai.com", "api.deepseek.com"):
        assert host not in source, f"server.py снова обращается к {host} напрямую"


# ── F3: профиль закрепляет обе переменные ───────────────────────────────────

def test_production_profile_pins_both_egress_variables():
    compose = REPO / "docker-compose.prod.yml"
    if not compose.is_file():  # pragma: no cover
        pytest.skip("production profile not present")
    text = compose.read_text(encoding="utf-8")
    assert "VELANTRIM_NETWORK_MODE=deny" in text
    assert "VELANTRIM_REMOTE_DATA_MODE=never" in text


def test_production_profile_no_longer_claims_the_boundary_is_unimplemented():
    """PR #64 писал «#59 не реализован на этом коммите» — теперь реализован."""
    compose = REPO / "docker-compose.prod.yml"
    if not compose.is_file():  # pragma: no cover
        pytest.skip("production profile not present")
    text = compose.read_text(encoding="utf-8")
    assert "not implemented on this commit" not in text


def test_validator_covers_both_egress_variables():
    source = (REPO / "scripts" / "validate_production_profile.py").read_text(
        encoding="utf-8"
    )
    assert "VELANTRIM_NETWORK_MODE" in source
    assert "VELANTRIM_REMOTE_DATA_MODE" in source


# ── F2: доку про data_mode=none ─────────────────────────────────────────────

def test_doc_states_that_data_mode_none_skips_the_remote_data_check():
    doc = REPO / "docs" / "REMOTE_EGRESS_POLICY.ru.md"
    text = doc.read_text(encoding="utf-8")
    assert "data_mode=none" in text
    assert re.search(r"не верифицируется|объявляется\s+вызывающим", text), (
        "доку не сказано, что data_mode объявляется вызывающим и не проверяется"
    )


def test_data_mode_none_really_bypasses_remote_data_but_not_network(
    monkeypatch: pytest.MonkeyPatch,
):
    """Поведение, которое документируется, должно совпадать с кодом."""
    from core.policy_kernel import PolicyKernel

    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "never")
    kernel = PolicyKernel()

    allowed_none = kernel.lease_capability(
        "x", locality="remote", requires_network=True, data_mode="none"
    )
    denied_raw = kernel.lease_capability(
        "x", locality="remote", requires_network=True, data_mode="raw"
    )
    assert allowed_none.allowed is True
    assert denied_raw.allowed is False
    assert denied_raw.reason_code == "remote_data_forbidden"

    # deny перекрывает всё, включая data_mode=none — это и есть способ
    # запретить вообще любой исходящий вызов.
    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "deny")
    kernel = PolicyKernel()
    denied_none = kernel.lease_capability(
        "x", locality="remote", requires_network=True, data_mode="none"
    )
    assert denied_none.allowed is False
    assert denied_none.reason_code == "network_denied"


# ── контракт data_mode="none" ───────────────────────────────────────────────

def test_only_metadata_capabilities_may_declare_data_mode_none():
    """`none` пропускает проверку remote-data — набор должен быть закрытым.

    Иначе любая новая точка вызова могла бы отказаться от remote-data-измерения,
    просто объявив `none`; а поскольку `data_mode` объявляется вызывающим и не
    верифицируется, такой отказ был бы невидим в review.
    """
    from core.remote_egress import (
        _METADATA_ONLY_CAPABILITIES,
        ensure_remote_egress_allowed,
    )

    assert _METADATA_ONLY_CAPABILITIES == {
        "remote_model_discovery",
        "remote_llm_test",
    }

    for capability in ("remote_llm", "remote_stt", "remote_tts", "whatever_new"):
        with pytest.raises(ValueError, match="data_mode='none'"):
            ensure_remote_egress_allowed(
                capability, provider="gemini", data_mode="none"
            )


def test_private_payload_capabilities_declare_raw():
    """STT/TTS несут аудио и пользовательский текст — только `raw`."""
    import core.llm_router as router
    import core.llm_stream as stream
    import core.tts_router as tts

    for module in (router, stream, tts):
        source = inspect.getsource(module)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "id", getattr(node.func, "attr", ""))
            if name != "ensure_remote_egress_allowed":
                continue
            cap = node.args[0] if node.args else None
            mode = next(
                (kw.value for kw in node.keywords if kw.arg == "data_mode"), None
            )
            if not isinstance(cap, ast.Constant) or not isinstance(mode, ast.Constant):
                continue  # передаётся переменной — покрыто рантайм-проверкой выше
            if cap.value in ("remote_stt", "remote_tts"):
                assert mode.value == "raw", (
                    f"{module.__name__}: {cap.value} объявляет "
                    f"data_mode={mode.value!r}, а несёт приватную нагрузку"
                )


def test_connectivity_probe_sends_only_a_repository_owned_prompt():
    """Промпт probe зашит в репозитории, а не приходит от вызывающего."""
    from core.llm_router import test_connection

    source = inspect.getsource(test_connection)
    tree = ast.parse(source.strip())

    # Единственные строковые литералы, уходящие наружу, — фиксированные.
    literals = {
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }
    assert "Ответь одним словом: OK" in literals

    # И у функции нет параметра, через который можно подсунуть текст.
    params = {a.arg for a in tree.body[0].args.args}
    assert params == {"cfg"}, f"test_connection принимает лишнее: {params}"


def test_probe_capability_is_distinct_for_every_provider():
    """Probe должен звать lease как remote_llm_test у всех провайдеров."""
    from core.llm_router import _llm_capability

    assert _llm_capability("none") == "remote_llm_test"
    assert _llm_capability("none", quick_ping=True) == "remote_llm_test"
    assert _llm_capability("raw", quick_ping=True) == "remote_llm_test"
    assert _llm_capability("raw") == "remote_llm"


@pytest.mark.parametrize(
    "smuggled",
    [
        {"prompt": "секретный вопрос пользователя"},
        {"text": "текст из памяти"},
        {"system": "Верифицированные факты: ..."},
        {"memory": ["fact-1", "fact-2"]},
        {"messages": [{"role": "user", "content": "leak"}]},
        {"audio_base64": "AAAA"},
        {"attachment": "secret.pdf"},
    ],
)
def test_public_llm_probe_rejects_user_payload(smuggled: dict):
    """Публичный probe-роут не принимает пользовательский prompt или memory.

    Отклонение, а не молчаливое игнорирование: `data_mode="none"` обходит
    проверку remote-data, поэтому попытка приложить нагрузку должна быть видимой
    ошибкой, а не полем, которое тихо выбросил pydantic.
    """
    from api.llm_routes import LlmTestBody

    with pytest.raises(Exception) as exc:
        LlmTestBody(provider="gemini", api_key="k" * 8, **smuggled)
    assert "extra" in str(exc.value).lower() or "forbidden" in str(exc.value).lower()


@pytest.mark.parametrize(
    "smuggled",
    [{"text": "произнеси это"}, {"prompt": "leak"}, {"memory": "fact"}],
)
def test_public_tts_probe_rejects_user_payload(smuggled: dict):
    from api.llm_routes import TtsTestBody

    with pytest.raises(Exception):
        TtsTestBody(provider="gemini", api_key="k" * 8, **smuggled)


def test_probe_bodies_declare_no_payload_fields():
    """Даже без extra=forbid в схеме не должно быть полей под нагрузку."""
    from api.llm_routes import LlmTestBody, TtsTestBody

    payload_names = {
        "prompt", "text", "system", "memory", "messages", "history",
        "audio", "audio_base64", "attachment", "context", "query",
    }
    for model in (LlmTestBody, TtsTestBody):
        fields = set(model.model_fields)
        assert not (fields & payload_names), (
            f"{model.__name__} объявляет поля под пользовательскую нагрузку: "
            f"{sorted(fields & payload_names)}"
        )


def test_model_discovery_is_metadata_only():
    """Discovery не должен принимать пользовательский текст."""
    from core.gemini_models import fetch_gemini_models_from_api

    params = set(inspect.signature(fetch_gemini_models_from_api).parameters)
    forbidden = {"prompt", "text", "system", "memory", "messages", "query"}
    assert not (params & forbidden), f"discovery принимает нагрузку: {params}"


def test_env_error_names_the_offending_value():
    """Оператор видит в логе только эту строку — в ней должно быть значение."""
    from core.policy_kernel import NetworkMode, _enum_from_env

    import os

    os.environ["VELANTRIM_TEST_MODE_VAR"] = "typo"
    try:
        with pytest.raises(ValueError) as exc:
            _enum_from_env("VELANTRIM_TEST_MODE_VAR", NetworkMode, "deny")
    finally:
        del os.environ["VELANTRIM_TEST_MODE_VAR"]

    message = str(exc.value)
    assert "'typo'" in message, message
    assert "is invalid" in message, message
    assert "expected one of: deny, ask, allow" in message, message


# ── операционная документация не содержит устаревших утверждений ─────────────

OPS_DOC = REPO / "docs" / "operations" / "hardened-production-profile.md"


def test_ops_doc_has_no_stale_boundary_claims():
    text = OPS_DOC.read_text(encoding="utf-8")
    stale = [
        "draft PR #59",
        "not implemented on this commit",
        "Not configured by default — not blocked",
        "the only effective controls",
        "Until it lands",
    ]
    found = [s for s in stale if s in text]
    assert not found, f"устаревшие утверждения остались: {found}"


def test_ops_doc_documents_the_actual_boundary():
    text = OPS_DOC.read_text(encoding="utf-8")
    assert "VELANTRIM_NETWORK_MODE=deny" in text
    assert "VELANTRIM_REMOTE_DATA_MODE=never" in text
    assert "RemoteEgressDeniedError" in text
    # И по-прежнему не переобещает: application-layer ≠ сетевая изоляция.
    lowered = text.lower()
    assert "not network-level isolation" in lowered or (
        "application layer still cannot do" in lowered
    )


def test_ops_doc_still_refuses_to_claim_network_isolation():
    """Честная граница из PR #63/#64 должна сохраниться."""
    text = OPS_DOC.read_text(encoding="utf-8")
    assert "complete network isolation or egress denial" in text, (
        "раздел «не доказывает и не предоставляет» потерял пункт про изоляцию"
    )


def test_ops_doc_marks_the_request_path_gap_resolved():
    text = OPS_DOC.read_text(encoding="utf-8")
    assert "RESOLVED" in text
    assert "data_mode" in text, "остаточное ограничение должно быть названо"
