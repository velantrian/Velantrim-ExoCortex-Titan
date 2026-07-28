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

yaml = pytest.importorskip("yaml", reason="PyYAML is required to inspect Compose files")

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
])
def test_experimental_feature_is_disabled(env: dict[str, str], var: str):
    assert var in env, f"{var} is not pinned in the production profile"
    assert env[var].strip().lower() in FALSY, f"{var}={env[var]!r}"


@pytest.mark.parametrize("var", [
    "ENABLE_WRITE_GATE",
    "ENABLE_TRUTH_GATE",
    "ENABLE_TRUTH_POLICY",
    "ENABLE_RATE_LIMIT",
    "ENABLE_RESPONSE_GUARDIAN",
    "ENABLE_OUTPUT_FAITHFULNESS",
    "ENABLE_RESPONSE_AUDIT",
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
