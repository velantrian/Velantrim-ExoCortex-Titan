"""Structural regression tests for the hardened production Compose profile.

These tests parse ``docker-compose.prod.yml`` directly, so they run in CI
without a Docker daemon. They assert the deny-by-default and hardening
properties that make the profile safe; a future edit that weakens one of them
fails here rather than in production.

Runtime behaviour of the container itself (effective capabilities, read-only
enforcement, database persistence) is verified separately by the Docker
workflow and recorded in docs/operations/hardened-production-profile.md.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# NOT importorskip. PyYAML is a declared verification dependency (requirements-dev
# .txt and the `dev` extra). Skipping here made every structural production-profile
# assertion vanish silently whenever the dependency was missing, which is exactly
# how the original profile shipped unverified (PR #63 review). A missing
# verification dependency must fail the suite, not quietly disable it.
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PROD_COMPOSE = REPO_ROOT / "docker-compose.prod.yml"
DEV_COMPOSE = REPO_ROOT / "docker-compose.dev.yml"
LEGACY_COMPOSE = REPO_ROOT / "docker-compose.yml"
PROD_ENV_TEMPLATE = REPO_ROOT / ".env.prod.example"
VALIDATOR = REPO_ROOT / "scripts" / "validate_production_profile.py"

APP_SERVICE = "velantrim"
FALSY = {"0", "false", "no", "off", ""}
TRUTHY = {"1", "true", "yes", "on"}


@pytest.fixture(scope="module")
def prod() -> dict:
    return yaml.safe_load(PROD_COMPOSE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def app(prod: dict) -> dict:
    return prod["services"][APP_SERVICE]


@pytest.fixture(scope="module")
def env(app: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in app.get("environment") or []:
        key, _, value = str(item).partition("=")
        out[key.strip()] = value
    return out


# ── file presence ────────────────────────────────────────────────────────────

def test_production_artifacts_exist():
    assert PROD_COMPOSE.is_file()
    assert PROD_ENV_TEMPLATE.is_file()
    assert VALIDATOR.is_file()


def test_production_compose_parses(prod: dict):
    assert APP_SERVICE in prod["services"]


# ── no dangerous runtime options (threats F, I, M) ───────────────────────────

@pytest.mark.parametrize("field,forbidden", [
    ("privileged", True),
    ("network_mode", "host"),
    ("pid", "host"),
    ("ipc", "host"),
])
def test_no_dangerous_runtime_option(prod: dict, field: str, forbidden):
    for name, svc in prod["services"].items():
        assert svc.get(field) != forbidden, f"{name} sets {field}={forbidden!r}"


def test_no_docker_socket_mount(prod: dict):
    for name, svc in prod["services"].items():
        for vol in svc.get("volumes") or []:
            assert "docker.sock" not in str(vol), f"{name} mounts the Docker socket"


# ── container hardening (threats F, G, H) ────────────────────────────────────

def test_app_runs_as_non_root(app: dict):
    user = str(app.get("user") or "")
    assert user, "no explicit user pinned"
    assert not user.startswith(("root", "0:")) and user != "0", f"user={user!r}"


def test_all_capabilities_dropped(app: dict):
    assert "ALL" in [str(c).upper() for c in app.get("cap_drop") or []]
    assert not app.get("cap_add"), "cap_add must stay empty"


def test_no_new_privileges(app: dict):
    opts = [str(o) for o in app.get("security_opt") or []]
    assert any("no-new-privileges" in o and "true" in o for o in opts), opts


def test_root_filesystem_is_read_only(app: dict):
    assert app.get("read_only") is True


def test_writable_paths_are_explicit_and_narrow(app: dict):
    """Only /tmp, the HOME cache, and the data volume may be writable."""
    tmpfs = [str(t).split(":")[0] for t in app.get("tmpfs") or []]
    assert "/tmp" in tmpfs, f"tmpfs={tmpfs}"
    assert "/app/.cache" in tmpfs, f"tmpfs={tmpfs}"

    targets = []
    for vol in app.get("volumes") or []:
        parts = str(vol).split(":")
        if len(parts) >= 2:
            targets.append(parts[1])
    assert targets == ["/app/data"], f"unexpected writable volume targets: {targets}"


def test_resource_and_log_bounds(app: dict):
    assert app.get("pids_limit"), "pids_limit missing"
    assert app.get("mem_limit"), "mem_limit missing"
    options = (app.get("logging") or {}).get("options") or {}
    assert "max-size" in options and "max-file" in options, options


def test_healthcheck_and_restart_policy(app: dict):
    assert app.get("healthcheck"), "healthcheck missing"
    assert app.get("restart"), "restart policy missing"
    assert app.get("stop_grace_period"), "stop_grace_period missing"


# ── no development source mounts (threat L) ──────────────────────────────────

def test_no_repository_bind_mount(app: dict):
    for vol in app.get("volumes") or []:
        source = str(vol).split(":")[0]
        assert not source.startswith((".", "/", "~")), f"bind mount from repo: {vol}"


# ── ports (threat D) ─────────────────────────────────────────────────────────

def test_single_published_port_bound_to_loopback_by_default(prod: dict):
    published = [
        (name, str(p))
        for name, svc in prod["services"].items()
        for p in svc.get("ports") or []
    ]
    assert len(published) == 1, f"expected one published port, got {published}"
    _, spec = published[0]
    assert "127.0.0.1" in spec, f"default bind is not loopback: {spec}"


def test_no_debug_or_secondary_port_published(prod: dict):
    for name, svc in prod["services"].items():
        for p in svc.get("ports") or []:
            # Container-side port must be the documented API entrypoint only.
            assert str(p).rstrip('"').endswith(":8000"), f"{name} publishes {p}"


# ── durability (section 9) ───────────────────────────────────────────────────

def test_data_volume_is_named_and_declared(prod: dict, app: dict):
    named = [
        str(v).split(":")[0]
        for v in app.get("volumes") or []
        if not str(v).split(":")[0].startswith((".", "/", "~"))
    ]
    assert named, "no named volume for durable state"
    assert set(named).issubset(set((prod.get("volumes") or {}).keys()))


def test_database_paths_point_into_the_data_volume(env: dict[str, str]):
    for var in ("VELANTRIM_DB_PATH", "VELANTRIM_NGRAM_DB", "SQLITE_GRAPH_PATH"):
        assert env.get(var, "").startswith("/app/data/"), f"{var}={env.get(var)!r}"


# ── feature policy: deny by default (threats A, B, N) ────────────────────────

@pytest.mark.parametrize("var", [
    # autonomous background cognition — SLEEP_WORKER_ENABLED defaults to
    # "true" in server.py:60, so an explicit pin is mandatory here
    "SLEEP_WORKER_ENABLED",
    "ENABLE_SLEEP_CONSOLIDATION",
    "CONSOLIDATION_ON_SLEEP",
    "ENABLE_EVENT_BUS_BACKGROUND",
    "ENABLE_DECAY_ORCHESTRATOR",
    "CAUSAL_LOAD_ON_STARTUP",
    # implicit promotion / autonomous ingestion
    "ENABLE_GRADUATED_PROMOTION",
    "ENABLE_CONCEPT_PROMOTE",
    "ENABLE_SEMANTIC_DEDUP",
    "ENABLE_CONTRADICTION_RESOLVER",
    "ENABLE_TELEGRAM_INGEST",
    "ENABLE_UMWELT_AUTO_SEED",
    # research / experimental modules
    "ENABLE_CONCEPT_EMERGENCE",
    "ENABLE_WORKING_NOTEBOOK",
    "ENABLE_VELUM",
    "ENABLE_ETIR",
    "ENABLE_ESSENCE",
    "ENABLE_L45",
    "ENABLE_L6_WELFARE",
    "ENABLE_MEMORY_VOLITION",
    "ENABLE_FOCUS_ENGINE",
    "ENABLE_INNENWELT",
    "ENABLE_COGNITIVE_RUNTIME",
    "ENABLE_REASONING_BANK",
    "ENABLE_PREDICTIVE_FUSION",
    "ENABLE_ACTR_ACTIVATION",
    "ENABLE_GRAPH_LAB",
    # LLM-backed paths
    "ENABLE_CONCEPT_LLM_NAMING",
    "ENABLE_CROSS_DOMAIN_LLM_ROUTING",
    "VELANTRIM_VISION_LLM",
    "VELANTRIM_PDF_USE_MARKER_LLM",
    # development / debug surfaces
    "ENABLE_API_DOCS",
    "VELANTRIM_DEV_MOCK",
    # inert or fail-open controls, corrected after the PR #63 review
    "ENABLE_TRUTH_POLICY",
    "ENABLE_RESPONSE_AUDIT",
])
def test_experimental_feature_is_disabled(env: dict[str, str], var: str):
    assert var in env, f"{var} is not pinned in the production profile"
    assert env[var].strip().lower() in FALSY, f"{var}={env[var]!r}"


@pytest.mark.parametrize("var", [
    "ENABLE_WRITE_GATE",
    "ENABLE_TRUTH_GATE",
    "ENABLE_RATE_LIMIT",
    "ENABLE_RESPONSE_GUARDIAN",
    "ENABLE_OUTPUT_FAITHFULNESS",
    "ENABLE_IMMUTABLE_CORE",
    "ENABLE_CIRCUIT_BREAKER",
    "ENABLE_MEMORY_BUDGET",
])
def test_safety_control_is_enabled(env: dict[str, str], var: str):
    assert var in env, f"{var} is not pinned in the production profile"
    assert env[var].strip().lower() in TRUTHY, f"{var}={env[var]!r}"


def test_compute_profile_pinned_to_lite(env: dict[str, str]):
    """`lite` adds nothing beyond the Truth Kernel (core/compute_profile.py)."""
    assert env.get("COMPUTE_PROFILE") == "lite"


def test_research_deployment_profile_not_selected(env: dict[str, str]):
    """config/profiles/{research,cognitive}.env re-enable the sleep worker."""
    assert env.get("VELANTRIM_PROFILE", "").lower() not in {"research", "cognitive"}


# ── secrets and providers (threats C, E) ─────────────────────────────────────

FORBIDDEN_CREDENTIALS = [
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY",
    "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENROUTER_API_KEY",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_WEBHOOK_SECRET",
    "NEO4J_PASSWORD", "GRAPHITI_NEO4J_PASSWORD",
]


@pytest.mark.parametrize("var", FORBIDDEN_CREDENTIALS)
def test_no_provider_credential_in_compose(env: dict[str, str], var: str):
    assert var not in env, f"{var} must not appear in the production profile"


def test_llm_provider_defaults_to_none(env: dict[str, str]):
    assert "none" in env.get("LLM_PROVIDER", ""), env.get("LLM_PROVIDER")


def test_auth_bypass_is_absent(env: dict[str, str]):
    """VELANTRIM_ALLOW_OPEN disables API-key enforcement (server.py:69)."""
    assert "VELANTRIM_ALLOW_OPEN" not in env


def test_api_key_is_required_fail_closed(env: dict[str, str]):
    """Missing VELANTRIM_API_KEY must abort interpolation, not default."""
    raw = env.get("VELANTRIM_API_KEY", "")
    assert ":?" in raw, f"expected a required-variable expression, got {raw!r}"
    assert ":-" not in raw, "must not provide a fallback value"


def test_env_template_contains_no_values():
    offenders = []
    for i, line in enumerate(PROD_ENV_TEMPLATE.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if value.strip():
            offenders.append(f"line {i}: {key}")
    assert not offenders, f"template assigns values: {offenders}"


def test_env_prod_is_gitignored():
    """A real .env.prod must never be committable."""
    proc = subprocess.run(
        ["git", "check-ignore", "-q", ".env.prod"],
        cwd=str(REPO_ROOT), capture_output=True, check=False,
    )
    assert proc.returncode == 0, ".env.prod is not covered by .gitignore"


def test_env_templates_remain_trackable():
    for name in (".env.example", ".env.prod.example"):
        proc = subprocess.run(
            ["git", "check-ignore", "-q", name],
            cwd=str(REPO_ROOT), capture_output=True, check=False,
        )
        assert proc.returncode != 0, f"{name} must stay trackable"


# ── the profile must not alter development behaviour ─────────────────────────

def test_development_compose_files_are_untouched_and_valid():
    for path in (LEGACY_COMPOSE, DEV_COMPOSE):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert APP_SERVICE in data["services"], path.name


def test_production_profile_uses_a_distinct_container_and_volume(prod: dict, app: dict):
    """No collision with the dev/legacy stacks' container or volume names."""
    assert app.get("container_name") == "velantrim-titan-prod"
    for path in (LEGACY_COMPOSE, DEV_COMPOSE):
        other = yaml.safe_load(path.read_text(encoding="utf-8"))
        other_vols = set((other.get("volumes") or {}).keys())
        assert not other_vols & set((prod.get("volumes") or {}).keys()), path.name


# ── the validator script itself must pass ────────────────────────────────────

def test_validator_script_reports_success():
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=str(REPO_ROOT), capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ─────────────────────────────────────────────────────────────────────────────
# PR #63 review corrections — regression coverage
#
# Each test below pins one corrected claim. They exist so a future edit cannot
# quietly re-enable a control that does not work, or restore a claim the runtime
# does not support.
# ─────────────────────────────────────────────────────────────────────────────

def _prod_text() -> str:
    return PROD_COMPOSE.read_text(encoding="utf-8")


def _env_template_text() -> str:
    return PROD_ENV_TEMPLATE.read_text(encoding="utf-8")


def test_truth_policy_stays_disabled_until_fail_closed(env: dict[str, str]):
    """F1: the read-path verdict is fail-open in server.py.

    server.py wraps the truth_policy block in `except Exception` that logs at
    DEBUG and leaves truth_rejects_answer False, so a raising policy permits the
    answer. Until a reviewed runtime fix lands, this must not be pinned on.
    """
    assert env.get("ENABLE_TRUTH_POLICY", "").strip().lower() in FALSY


def test_profile_does_not_call_truth_policy_fail_closed():
    """The profile must not describe TruthPolicy as fail-closed."""
    text = _prod_text().lower()
    window_start = text.find("enable_truth_policy")
    assert window_start != -1
    window = text[max(0, window_start - 600):window_start + 600]
    assert "fail-open" in window, "the fail-open nature must be stated at the pin"
    assert "fail-closed" not in window, "TruthPolicy must not be called fail-closed"


def test_response_audit_stays_disabled_while_event_bus_is_off(env: dict[str, str]):
    """F2: audit_response_generated is only reachable through the event bus."""
    assert env.get("ENABLE_RESPONSE_AUDIT", "").strip().lower() in FALSY


def test_event_bus_is_not_enabled_to_reach_the_audit_path(env: dict[str, str]):
    """The fix for F2 must not be 'switch the event bus on'."""
    assert env.get("ENABLE_EVENT_BUS", "").strip().lower() in FALSY
    assert env.get("ENABLE_EVENT_BUS_BACKGROUND", "").strip().lower() in FALSY


def test_immutable_core_does_not_claim_automatic_snapshots():
    """F7: ImmutableCoreScheduler has no non-test caller, so nothing is scheduled."""
    text = _prod_text()
    marker = text.find("ENABLE_IMMUTABLE_CORE=1")
    assert marker != -1
    window = text[max(0, marker - 700):marker]
    assert "MANUALLY" in window or "manual" in window, (
        "the manual-only scope of ENABLE_IMMUTABLE_CORE must be stated"
    )
    assert "SHA-256 delta snapshots of the immutable core." not in text, (
        "the original automatic-snapshot claim must be gone"
    )


def test_blocking_is_attributed_to_the_policy_boundary_not_to_llm_provider():
    """F5, updated: the egress boundary now exists — but LLM_PROVIDER isn't it.

    Originally this asserted the profile called providers "not blocked", because
    at that commit nothing blocked them. The policy boundary
    (core/policy_kernel.py + core/remote_egress.py) is now implemented and
    pinned here, so the profile may legitimately claim gating. What must NOT
    come back is attributing that gating to `LLM_PROVIDER=none`, which never
    blocked anything on its own.
    """
    text = _prod_text()
    lowered = text.lower()

    # The real controls are named.
    assert "VELANTRIM_NETWORK_MODE=deny" in text
    assert "VELANTRIM_REMOTE_DATA_MODE=never" in text

    # LLM_PROVIDER is still described as configuration, not as the boundary.
    assert "no provider is configured from the" in lowered, (
        "the profile must keep explaining that LLM_PROVIDER=none is only "
        "'not configured from the environment'"
    )
    assert "on its own that was never a boundary" in lowered, (
        "the profile must keep stating that LLM_PROVIDER=none is not a boundary"
    )


def test_request_supplied_provider_credentials_are_documented():
    """The request-override path must stay documented, and named as gated."""
    for text, label in ((_prod_text(), "compose"), (_env_template_text(), "env template")):
        lowered = text.lower()
        assert "llm_api_key" in lowered, f"{label} does not mention llm_api_key"
        assert "llm_provider" in lowered, f"{label} does not mention llm_provider"
        # The mechanism that actually gates it must be named, so a reader is not
        # left to infer that holding the API key is still sufficient.
        assert "VELANTRIM_NETWORK_MODE" in text, (
            f"{label} does not name the variable that gates the request path"
        )


def test_profile_does_not_describe_the_boundary_as_unimplemented():
    """The pre-#59 wording must not survive now that the boundary is in place."""
    for text, label in ((_prod_text(), "compose"), (_env_template_text(), "env template")):
        assert "not implemented on this commit" not in text, (
            f"{label} still claims the egress boundary is unimplemented"
        )
        assert "draft PR #59" not in text, (
            f"{label} still describes the boundary as a pending draft"
        )


def test_env_template_does_not_claim_env_file_injects_credentials():
    """F4 (docs): --env-file alone does not pass unreferenced vars into the container."""
    text = _env_template_text()
    assert "add BOTH lines to `.env.prod` and restart" not in text, (
        "the false credential-injection instruction must be gone"
    )
    lowered = text.lower()
    assert "does not reach the container" in lowered or "silently ignored" in lowered


def test_answer_integrity_scope_is_documented():
    """F6: guardian/faithfulness run inside core/pipeline.py, not on llm_answer."""
    lowered = _prod_text().lower()
    assert "llm_answer" in lowered, (
        "the profile must state that the integrity checks do not inspect llm_answer"
    )


# ── validator behaviour (F3, F4) ──────────────────────────────────────────────

def test_validator_requires_pyyaml_rather_than_skipping():
    """F3: PyYAML must be a declared verification dependency."""
    assert "pyyaml" in REPO_ROOT.joinpath("requirements-dev.txt").read_text(
        encoding="utf-8"
    ).lower()
    assert "pyyaml>=6.0" in REPO_ROOT.joinpath("pyproject.toml").read_text(encoding="utf-8")


def test_this_module_does_not_skip_on_missing_yaml():
    """A missing verification dependency must fail the suite, not disable it.

    Asserted over the AST: yaml must be acquired by a module-level ``import``,
    not by a skip-on-missing helper. A source substring check cannot be used
    here — this file names the helper in prose, and the assertion text would
    match itself.
    """
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    module_level_imports = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "yaml" in module_level_imports, (
        "yaml must be a hard module-level import so a missing dependency fails"
    )
    # No module-level call may bind the yaml name (that is the skip pattern).
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            assert "yaml" not in targets, "yaml must not be bound by a call"


def _load_validator():
    import importlib.util

    spec = importlib.util.spec_from_file_location("_prod_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("raw,expected,certain", [
    ("${LLM_PROVIDER:-none}", "none", True),
    ("${VELANTRIM_BIND_ADDR:-127.0.0.1}", "127.0.0.1", True),
    ("${VELANTRIM_API_KEY:?required}", "${VELANTRIM_API_KEY:?required}", False),
    ("${SOME_VAR}", "${SOME_VAR}", False),
    ("lite", "lite", True),
    ("0", "0", True),
])
def test_interpolation_resolution(raw: str, expected: str, certain: bool):
    """F4: `${VAR:-default}` resolves; a required/no-default var stays uncertain."""
    module = _load_validator()
    assert module.resolve_interpolation(raw) == (expected, certain)


def test_raw_yaml_fallback_does_not_produce_false_failures():
    """F4: the documented daemon-free path must not fail an unchanged profile."""
    module = _load_validator()
    raw = yaml.safe_load(PROD_COMPOSE.read_text(encoding="utf-8"))
    env = module.env_map(raw["services"][APP_SERVICE])

    result = module.Result()
    module.check_providers_and_secrets(result, env)
    module.check_feature_policy(result, env)

    assert result.failures == [], f"false failures in the fallback path: {result.failures}"


def test_validator_passes_in_both_resolution_modes():
    """Exit 0 with the real Docker CLI and with the raw-YAML fallback alike."""
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=str(REPO_ROOT), capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ── CI wiring (item 6) ────────────────────────────────────────────────────────

@pytest.mark.parametrize("path", [
    "docker-compose.prod.yml",
    ".env.prod.example",
    "scripts/validate_production_profile.py",
    "tests/test_production_profile.py",
    "docs/operations/hardened-production-profile.md",
])
def test_docker_workflow_watches_production_profile_paths(path: str):
    """The Docker workflow must run when the production profile changes."""
    workflow = REPO_ROOT / ".github" / "workflows" / "docker.yml"
    assert f'"{path}"' in workflow.read_text(encoding="utf-8"), (
        f"{path} is missing from docker.yml path filters"
    )
