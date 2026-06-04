"""
core/core3_adapter.py — Dual Core Router bridge to the Truth Engine (Core-3).

Per docs/TRUTH_AND_RINGZERO_CANON.ru.md §5.5 and VELANTRIM_Dual_Core_Router/README.ru.md:
this is the SUBPROCESS adapter — the safest first step. ExoCortex (Big Core) asks
Core-3 (the small truth/recovery core) "can this answer be trusted?" by sending
`query + facts + relations` and receiving a verdict: allow | gap_notice | reject.

Design rules (Router README §3/§7/§9):
  * The adapter does NOT import Core-3 into this process — it calls it as a command.
  * Core-3 runs in its own folder with an in-memory DB — it never writes Big Core memory.
  * Easy to disable; meant for strict / high-risk queries, not every request.
  * Fail-safe: if the verifier is unavailable/slow/broken, return a CONSERVATIVE
    verdict (default `gap_notice` — "couldn't confirm"), never a false `allow`.

Config (env):
  VELANTRIM_CORE3_PATH    — path to the Core-3 package root (the dir containing `velantrim/`).
                            Default: sibling `../velantrim_core-3/velantrim_core`.
  VELANTRIM_CORE3_PYTHON  — python executable to run Core-3. Default: current interpreter.
  VELANTRIM_CORE3_TIMEOUT — subprocess timeout in seconds. Default: 20.

Usage:
    from core.core3_adapter import verify
    v = verify("why are trees important for soil?",
               facts=[{"fact_id": "f1", "claim": "Roots hold moisture",
                       "confidence": 0.9, "source": "forest_corpus:roots"}])
    if not v.allowed:
        return honest_gap_or_rejection(v)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

# ── verdict vocabulary (canon §5.1) ────────────────────────────────────────
ALLOW = "allow"
GAP_NOTICE = "gap_notice"
REJECT = "reject"


@dataclass
class Core3Verdict:
    """Result of a Core-3 verification. `ok=False` ⇒ adapter/verifier failure
    (the `decision` is then the configured conservative fallback, not a real verdict)."""
    decision: str                                  # allow | gap_notice | reject
    truth_status: str = "unknown"
    evidence_ids: list = field(default_factory=list)
    path: list = field(default_factory=list)
    rejected: list = field(default_factory=list)
    trace_note: str = ""
    blocked_reason: str | None = None
    facts_pack_id: str | None = None
    ok: bool = True
    error: str | None = None

    @property
    def allowed(self) -> bool:
        return self.decision == ALLOW

    @property
    def is_gap(self) -> bool:
        return self.decision == GAP_NOTICE

    @property
    def is_reject(self) -> bool:
        return self.decision == REJECT

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "truth_status": self.truth_status,
            "evidence_ids": self.evidence_ids,
            "path": self.path,
            "rejected": self.rejected,
            "trace_note": self.trace_note,
            "blocked_reason": self.blocked_reason,
            "facts_pack_id": self.facts_pack_id,
            "ok": self.ok,
            "error": self.error,
        }


# ── locating Core-3 ─────────────────────────────────────────────────────────
def _default_core3_path() -> Path:
    # repo_root = .../VELANTRIM_ExoCortex_V8.6 ; the sibling research folder holds core-3
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root.parent / "velantrim_core-3" / "velantrim_core"


def core3_path() -> Path:
    return Path(os.getenv("VELANTRIM_CORE3_PATH", str(_default_core3_path())))


def is_available() -> bool:
    """True iff the Core-3 verify entrypoint is present at the configured path."""
    return (core3_path() / "velantrim" / "verify.py").is_file()


# ── contract building (canon §5.5) ──────────────────────────────────────────
def build_contract(query: str, facts: Iterable[dict],
                   relations: Iterable[dict] | None = None, *,
                   mode: str = "strict", min_conf: float | None = None) -> dict:
    contract: dict = {
        "query": query,
        "facts": list(facts or []),
        "relations": list(relations or []),
        "mode": mode,
    }
    if min_conf is not None:
        contract["min_conf"] = float(min_conf)
    return contract


def _fail(on_error: str, status: str, error: str, note: str) -> Core3Verdict:
    return Core3Verdict(decision=on_error, truth_status=status, ok=False,
                        error=error, trace_note=note)


# ── main entry ───────────────────────────────────────────────────────────────
def verify(query: str, facts: Iterable[dict],
           relations: Iterable[dict] | None = None, *,
           mode: str = "strict", min_conf: float | None = None,
           on_error: str = GAP_NOTICE, timeout: float | None = None) -> Core3Verdict:
    """Ask Core-3 to verify whether an answer over `facts` is trustworthy.

    Returns a Core3Verdict. On any adapter failure (Core-3 missing, timeout,
    crash, unparseable output) returns `on_error` (default gap_notice) with ok=False.
    """
    contract = build_contract(query, facts, relations, mode=mode, min_conf=min_conf)
    path = core3_path()
    if not (path / "velantrim" / "verify.py").is_file():
        return _fail(on_error, "unavailable", f"Core-3 not found at {path}",
                     "core3_adapter: verifier unavailable")

    python = os.getenv("VELANTRIM_CORE3_PYTHON", sys.executable)
    t = timeout if timeout is not None else float(os.getenv("VELANTRIM_CORE3_TIMEOUT", "20"))
    env = dict(os.environ)
    env["PYTHONPATH"] = str(path) + os.pathsep + env.get("PYTHONPATH", "")

    try:
        proc = subprocess.run(
            [python, "-m", "velantrim.verify"], cwd=str(path),
            input=json.dumps(contract, ensure_ascii=False),
            capture_output=True, text=True, encoding="utf-8",
            timeout=t, env=env,
        )
    except subprocess.TimeoutExpired:
        return _fail(on_error, "timeout", f"timed out after {t}s",
                     f"core3_adapter: timeout after {t}s")
    except Exception as exc:                       # noqa: BLE001 — fail-safe boundary
        return _fail(on_error, "error", str(exc), "core3_adapter: spawn failed")

    out = (proc.stdout or "").strip()
    if not out:
        return _fail(on_error, "error", (proc.stderr or "").strip()[:500],
                     "core3_adapter: empty output / non-zero exit")
    try:
        data = json.loads(out.splitlines()[-1])    # last line = verdict JSON
    except (json.JSONDecodeError, IndexError) as exc:
        return _fail(on_error, "error",
                     f"bad verdict json: {exc}; stderr={(proc.stderr or '')[:300]}",
                     "core3_adapter: unparseable verdict")

    return Core3Verdict(
        decision=data.get("decision", on_error),
        truth_status=data.get("truth_status", "unknown"),
        evidence_ids=data.get("evidence_ids", []),
        path=data.get("path", []),
        rejected=data.get("rejected", []),
        trace_note=data.get("trace_note", ""),
        blocked_reason=data.get("blocked_reason"),
        facts_pack_id=data.get("facts_pack_id"),
        ok=True,
    )
