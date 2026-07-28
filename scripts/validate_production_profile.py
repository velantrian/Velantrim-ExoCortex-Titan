#!/usr/bin/env python3
"""Structural validator for the hardened production Compose profile.

Asserts the deny-by-default and container-hardening properties of
``docker-compose.prod.yml`` against the *resolved* Compose configuration, so a
variable indirection or a YAML anchor cannot hide a regression.

Resolution uses ``docker compose config`` when the Docker CLI is available
(daemon not required — resolution is client-side). Without it, the raw YAML is
parsed instead and the checks that depend on interpolation are reported as
SKIPPED rather than silently passing.

Usage:
    python scripts/validate_production_profile.py
    python scripts/validate_production_profile.py --json

Exit code 0 = every applicable check passed.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PROD_COMPOSE = REPO_ROOT / "docker-compose.prod.yml"
PROD_ENV_TEMPLATE = REPO_ROOT / ".env.prod.example"

APP_SERVICE = "velantrim"

# Placeholder used only to satisfy the fail-closed ${VAR:?} interpolation while
# resolving the config. Never a real credential.
_RESOLVE_STUB_KEY = "validator-placeholder-not-a-secret"

# Provider/integration credentials that must never be present in the resolved
# production configuration (server.py:150-176, app/telegram_ingest.py,
# core/graphiti_adapter.py).
FORBIDDEN_CREDENTIAL_VARS = frozenset({
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "OPENROUTER_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET",
    "NEO4J_PASSWORD",
    "GRAPHITI_NEO4J_PASSWORD",
})

# Env vars that must be explicitly falsy in the production profile.
# Value = why it matters, cited to the runtime that reads it.
MUST_BE_DISABLED = {
    # Autonomous background cognition. Code default is "true" (server.py:60).
    "SLEEP_WORKER_ENABLED": "autonomous idle-time cognitive worker",
    "ENABLE_SLEEP_CONSOLIDATION": "background consolidation cycle",
    "CONSOLIDATION_ON_SLEEP": "consolidation inside the sleep cycle",
    "ENABLE_EVENT_BUS_BACKGROUND": "background event-bus dispatch",
    "ENABLE_DECAY_ORCHESTRATOR": "autonomous decay maintenance",
    "CAUSAL_LOAD_ON_STARTUP": "eager causal-graph load at boot",
    # Implicit promotion / autonomous ingestion.
    "ENABLE_GRADUATED_PROMOTION": "implicit epistemic promotion",
    "ENABLE_CONCEPT_PROMOTE": "implicit concept promotion",
    "ENABLE_SEMANTIC_DEDUP": "automatic semantic merge of facts",
    "ENABLE_CONTRADICTION_RESOLVER": "automatic contradiction resolution",
    "ENABLE_TELEGRAM_INGEST": "unauthenticated-webhook ingestion path",
    "ENABLE_UMWELT_AUTO_SEED": "automatic seed admission at startup",
    # LLM-backed paths never auto-enabled by a compute profile.
    "ENABLE_CONCEPT_LLM_NAMING": "outbound LLM naming call",
    "ENABLE_CROSS_DOMAIN_LLM_ROUTING": "outbound LLM routing call",
    "VELANTRIM_VISION_LLM": "outbound vision-LLM parsing",
    "VELANTRIM_PDF_USE_MARKER_LLM": "outbound LLM PDF parsing",
    # Research / experimental modules.
    "ENABLE_CONCEPT_EMERGENCE": "research: concept emergence",
    "ENABLE_WORKING_NOTEBOOK": "research: working notebook",
    "ENABLE_VELUM": "research: Velum L1.5",
    "ENABLE_ETIR": "research: Etir L3.5a",
    "ENABLE_ESSENCE": "research: essence layer",
    "ENABLE_L45": "research: L4.5",
    "ENABLE_L6_WELFARE": "research: L6 welfare",
    "ENABLE_MEMORY_VOLITION": "research: memory volition",
    "ENABLE_FOCUS_ENGINE": "research: focus engine",
    "ENABLE_INNENWELT": "research: innenwelt",
    "ENABLE_COGNITIVE_RUNTIME": "research: cognitive runtime",
    "ENABLE_REASONING_BANK": "research: reasoning bank",
    "ENABLE_PREDICTIVE_FUSION": "research: predictive fusion",
    "ENABLE_ACTR_ACTIVATION": "research: ACT-R activation",
    "ENABLE_GRAPH_LAB": "research: NetworkX graph lab",
    # Development / debug surfaces.
    "ENABLE_API_DOCS": "Swagger/OpenAPI admin surface",
    "VELANTRIM_DEV_MOCK": "development mock pipeline",
}

# Env vars that must be explicitly truthy.
MUST_BE_ENABLED = {
    "ENABLE_WRITE_GATE": "canonical write-protocol gate readout",
    "ENABLE_TRUTH_GATE": "epistemic admission gate",
    "ENABLE_TRUTH_POLICY": "read-path truth verdict",
    "ENABLE_RATE_LIMIT": "per-IP token bucket",
    "ENABLE_RESPONSE_GUARDIAN": "response guardian",
    "ENABLE_OUTPUT_FAITHFULNESS": "answer/fact faithfulness check",
    "ENABLE_RESPONSE_AUDIT": "response audit trail",
    "ENABLE_IMMUTABLE_CORE": "immutable-core snapshots",
    "ENABLE_CIRCUIT_BREAKER": "backpressure circuit breaker",
    "ENABLE_MEMORY_BUDGET": "bounded memory growth",
}

TRUTHY = {"1", "true", "yes", "on"}
FALSY = {"0", "false", "no", "off", ""}


class Result:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def add(self, name: str, ok: bool | None, detail: str = "") -> None:
        status = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
        self.checks.append({"check": name, "status": status, "detail": detail})

    @property
    def failures(self) -> list[dict[str, Any]]:
        return [c for c in self.checks if c["status"] == "FAIL"]

    @property
    def skipped(self) -> list[dict[str, Any]]:
        return [c for c in self.checks if c["status"] == "SKIP"]


def resolve_compose() -> tuple[dict[str, Any], bool]:
    """Return (config, resolved_via_docker)."""
    if shutil.which("docker"):
        proc = subprocess.run(
            ["docker", "compose", "-f", str(PROD_COMPOSE), "config"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={
                "PATH": "/usr/bin:/bin:/usr/local/bin",
                "VELANTRIM_API_KEY": _RESOLVE_STUB_KEY,
                "HOME": str(Path.home()),
            },
            check=False,
        )
        if proc.returncode == 0:
            return yaml.safe_load(proc.stdout), True
    return yaml.safe_load(PROD_COMPOSE.read_text(encoding="utf-8")), False


def env_map(service: dict[str, Any]) -> dict[str, str]:
    raw = service.get("environment") or {}
    if isinstance(raw, dict):
        return {k: ("" if v is None else str(v)) for k, v in raw.items()}
    out: dict[str, str] = {}
    for item in raw:
        key, _, value = str(item).partition("=")
        out[key] = value
    return out


def check_no_dangerous_runtime(res: Result, services: dict[str, Any]) -> None:
    for name, svc in services.items():
        res.add(f"{name}: not privileged", svc.get("privileged") is not True)
        res.add(f"{name}: no host network", svc.get("network_mode") != "host")
        res.add(f"{name}: no host PID", str(svc.get("pid") or "") != "host")
        res.add(f"{name}: no host IPC", str(svc.get("ipc") or "") != "host")
        mounts = [str(v) for v in (svc.get("volumes") or [])]
        sock = [m for m in mounts if "docker.sock" in m]
        res.add(f"{name}: no Docker socket mount", not sock, "; ".join(sock))


def check_hardening(res: Result, svc: dict[str, Any]) -> None:
    user = str(svc.get("user") or "")
    res.add(
        "app: runs as explicit non-root user",
        bool(user) and not user.startswith(("root", "0:")) and user != "0",
        f"user={user!r}",
    )
    caps = [str(c).upper() for c in (svc.get("cap_drop") or [])]
    res.add("app: cap_drop includes ALL", "ALL" in caps, f"cap_drop={caps}")
    res.add("app: cap_add is empty", not svc.get("cap_add"), str(svc.get("cap_add")))
    opts = [str(o) for o in (svc.get("security_opt") or [])]
    res.add(
        "app: no-new-privileges enabled",
        any("no-new-privileges" in o and "true" in o for o in opts),
        f"security_opt={opts}",
    )
    res.add("app: read_only root filesystem", svc.get("read_only") is True)
    tmpfs = [str(t) for t in (svc.get("tmpfs") or [])]
    res.add("app: /tmp is tmpfs", any(t.startswith("/tmp") for t in tmpfs), f"tmpfs={tmpfs}")
    res.add("app: healthcheck defined", bool(svc.get("healthcheck")))
    res.add("app: pids_limit set", svc.get("pids_limit") is not None, str(svc.get("pids_limit")))
    res.add(
        "app: memory limit set",
        svc.get("mem_limit") is not None or bool(svc.get("deploy", {}).get("resources")),
        str(svc.get("mem_limit")),
    )
    log_opts = (svc.get("logging") or {}).get("options") or {}
    res.add(
        "app: log rotation configured",
        "max-size" in log_opts and "max-file" in log_opts,
        str(log_opts),
    )
    res.add("app: restart policy set", bool(svc.get("restart")), str(svc.get("restart")))


def check_no_source_mounts(res: Result, svc: dict[str, Any]) -> None:
    """No writable repository bind mount; no source bind mount at all."""
    offenders: list[str] = []
    for vol in svc.get("volumes") or []:
        if isinstance(vol, dict):
            vtype, src = vol.get("type"), str(vol.get("source") or "")
        else:
            parts = str(vol).split(":")
            src = parts[0]
            vtype = "bind" if src.startswith((".", "/", "~")) else "volume"
        if vtype == "bind":
            offenders.append(src)
    res.add(
        "app: no bind mount from the repository",
        not offenders,
        f"bind sources={offenders}",
    )


def check_ports(res: Result, services: dict[str, Any], resolved: bool) -> None:
    published: list[tuple[str, str, str]] = []
    for name, svc in services.items():
        for port in svc.get("ports") or []:
            if isinstance(port, dict):
                published.append((name, str(port.get("published")), str(port.get("host_ip") or "")))
            else:
                published.append((name, str(port), ""))
    res.add(
        "exactly one published port across the stack",
        len(published) == 1,
        f"published={published}",
    )
    if resolved and len(published) == 1:
        _, _, host_ip = published[0]
        res.add(
            "published port binds loopback by default",
            host_ip == "127.0.0.1",
            f"host_ip={host_ip!r}",
        )
    else:
        res.add("published port binds loopback by default", None, "needs resolved config")

    # No database service, therefore no database port. Assert that stays true.
    db_like = [n for n in services if n != APP_SERVICE]
    res.add(
        "no additional (database) service publishes a port",
        not any(services[n].get("ports") for n in db_like),
        f"other services={db_like}",
    )


def check_durable_volume(res: Result, svc: dict[str, Any], top: dict[str, Any]) -> None:
    named: list[str] = []
    for vol in svc.get("volumes") or []:
        if isinstance(vol, dict):
            if vol.get("type") == "volume":
                named.append(str(vol.get("source")))
        else:
            parts = str(vol).split(":")
            if not parts[0].startswith((".", "/", "~")):
                named.append(parts[0])
    declared = set((top.get("volumes") or {}).keys())
    res.add(
        "app: durable named volume for /app/data",
        bool(named) and set(named).issubset(declared),
        f"named={named}, declared={sorted(declared)}",
    )


def check_feature_policy(res: Result, env: dict[str, str]) -> None:
    for var, why in sorted(MUST_BE_DISABLED.items()):
        value = env.get(var)
        if value is None:
            res.add(f"disabled: {var}", False, f"not pinned in the profile ({why})")
        else:
            res.add(
                f"disabled: {var}",
                value.strip().lower() in FALSY,
                f"={value!r} ({why})",
            )
    for var, why in sorted(MUST_BE_ENABLED.items()):
        value = env.get(var)
        if value is None:
            res.add(f"enabled: {var}", False, f"not pinned in the profile ({why})")
        else:
            res.add(
                f"enabled: {var}",
                value.strip().lower() in TRUTHY,
                f"={value!r} ({why})",
            )


def check_providers_and_secrets(res: Result, env: dict[str, str]) -> None:
    present = sorted(v for v in FORBIDDEN_CREDENTIAL_VARS if v in env)
    res.add(
        "no provider/integration credential in the profile",
        not present,
        f"present={present}",
    )
    res.add(
        "LLM_PROVIDER defaults to none",
        env.get("LLM_PROVIDER", "none").strip().lower() == "none",
        f"={env.get('LLM_PROVIDER')!r}",
    )
    res.add(
        "auth bypass VELANTRIM_ALLOW_OPEN not set",
        "VELANTRIM_ALLOW_OPEN" not in env,
        f"={env.get('VELANTRIM_ALLOW_OPEN')!r}",
    )
    api_key = env.get("VELANTRIM_API_KEY", "")
    res.add("VELANTRIM_API_KEY is declared", "VELANTRIM_API_KEY" in env)
    for weak in ("dev-key-change-me", "admin", "changeme", "password", "test"):
        if api_key and api_key.strip().lower() == weak:
            res.add("VELANTRIM_API_KEY is not a known weak default", False, api_key)
            break
    else:
        res.add("VELANTRIM_API_KEY is not a known weak default", True)
    res.add(
        "COMPUTE_PROFILE pinned to lite",
        env.get("COMPUTE_PROFILE", "lite").strip().lower() == "lite",
        f"={env.get('COMPUTE_PROFILE')!r}",
    )
    res.add(
        "VELANTRIM_PROFILE not pinned to a research profile",
        env.get("VELANTRIM_PROFILE", "").strip().lower() not in {"research", "cognitive"},
        f"={env.get('VELANTRIM_PROFILE')!r}",
    )


def check_template_has_no_secrets(res: Result) -> None:
    if not PROD_ENV_TEMPLATE.exists():
        res.add("env template exists", False, str(PROD_ENV_TEMPLATE))
        return
    res.add("env template exists", True)
    offenders: list[str] = []
    for i, line in enumerate(PROD_ENV_TEMPLATE.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if value.strip():
            offenders.append(f"{PROD_ENV_TEMPLATE.name}:{i} {key}")
    res.add(
        "env template assigns no value to any variable",
        not offenders,
        "; ".join(offenders),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv or sys.argv[1:])

    res = Result()
    if not PROD_COMPOSE.exists():
        print(f"error: {PROD_COMPOSE} not found", file=sys.stderr)
        return 2

    config, resolved = resolve_compose()
    res.add("production Compose file parses", isinstance(config, dict))
    services = config.get("services") or {}
    res.add(f"service {APP_SERVICE!r} present", APP_SERVICE in services)
    if APP_SERVICE not in services:
        _emit(res, resolved, args.json)
        return 1

    svc = services[APP_SERVICE]
    env = env_map(svc)

    check_no_dangerous_runtime(res, services)
    check_hardening(res, svc)
    check_no_source_mounts(res, svc)
    check_ports(res, services, resolved)
    check_durable_volume(res, svc, config)
    check_feature_policy(res, env)
    check_providers_and_secrets(res, env)
    check_template_has_no_secrets(res)

    _emit(res, resolved, args.json)
    return 1 if res.failures else 0


def _emit(res: Result, resolved: bool, as_json: bool) -> None:
    if as_json:
        print(json.dumps(
            {
                "resolved_via_docker": resolved,
                "total": len(res.checks),
                "failed": len(res.failures),
                "skipped": len(res.skipped),
                "checks": res.checks,
            },
            indent=2,
        ))
        return
    source = "docker compose config" if resolved else "raw YAML (docker unavailable)"
    print(f"Production profile validation — resolved via {source}\n")
    for c in res.checks:
        mark = {"PASS": "  ok  ", "FAIL": " FAIL ", "SKIP": " skip "}[c["status"]]
        line = f"[{mark}] {c['check']}"
        if c["detail"] and c["status"] != "PASS":
            line += f"  — {c['detail']}"
        print(line)
    print(
        f"\n{len(res.checks)} checks: "
        f"{len(res.checks) - len(res.failures) - len(res.skipped)} passed, "
        f"{len(res.failures)} failed, {len(res.skipped)} skipped"
    )


if __name__ == "__main__":
    raise SystemExit(main())
