from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ingest_file import ingest_file
from scripts.titan_tools import list_tools


PILOT_API_KEY = "stage10-pilot-local-key"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _request_json(
    method: str,
    url: str,
    *,
    api_key: str = PILOT_API_KEY,
    payload: dict | None = None,
    timeout: float = 15.0,
) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"X-Api-Key": api_key}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            body = json.loads(raw or "{}")
            return int(response.status), body
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw or "{}")
        except json.JSONDecodeError:
            body = {"raw": raw[:500]}
        return int(exc.code), body


def _wait_ready(base_url: str, timeout_s: float = 45.0) -> None:
    deadline = time.monotonic() + timeout_s
    last: object = None
    while time.monotonic() < deadline:
        try:
            status, body = _request_json("GET", f"{base_url}/health", timeout=3)
            last = (status, body)
            if status == 200:
                return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
        time.sleep(0.25)
    raise RuntimeError(f"Pilot server did not become healthy: {last}")


def _start_server(root: Path, env: dict[str, str]) -> tuple[subprocess.Popen, str]:
    port = _free_port()
    child_env = env.copy()
    child_env["PORT"] = str(port)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=root,
        env=child_env,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_ready(base_url)
    except Exception:
        _stop_server(process)
        raise
    return process, base_url


def _stop_server(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _seed_validated_fact(base_url: str) -> dict:
    fact_id = "stage10_pilot_fact"
    status, body = _request_json(
        "POST",
        f"{base_url}/facts",
        payload={
            "fact_id": fact_id,
            "claim": "my pilot codename is Cedar",
            "source": "stage10-bounded-pilot",
            "confidence": 0.9,
            "metadata": {
                "memory_category": "personal",
                "evidence_refs": ["pilot-evidence-a", "pilot-evidence-b"],
            },
        },
    )
    if status not in (200, 201):
        raise RuntimeError(f"Pilot fact create failed: HTTP {status} {body}")

    for target in ("Hypothesized", "Supported", "Validated"):
        status, body = _request_json(
            "PATCH",
            f"{base_url}/facts/{fact_id}/transition",
            payload={"new_state": target, "by": "stage10-bounded-pilot"},
        )
        if status != 200:
            raise RuntimeError(f"Pilot transition to {target} failed: HTTP {status} {body}")

    if body.get("epistemic_state") != "Validated":
        raise RuntimeError("Pilot fact did not reach Validated through TruthGate")
    return body


def _offline_chat(base_url: str) -> dict:
    status, body = _request_json(
        "POST",
        f"{base_url}/chat",
        payload={
            "message": "what is my pilot codename?",
            "profile": "citizen",
            "use_memory": True,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": False,
            "block_memory": [],
            "chat_history": [],
        },
    )
    if status != 200:
        raise RuntimeError(f"Pilot chat failed: HTTP {status} {body}")
    reply = str(body.get("reply") or "")
    if "Cedar" not in reply:
        raise RuntimeError(f"Pilot chat did not recall validated memory: {reply!r}")
    return body


def main() -> int:
    root = ROOT
    results: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="titan-v1-pilot-") as tmp:
        tmp_path = Path(tmp)
        env = os.environ.copy()
        env.update(
            {
                "VELANTRIM_API_KEY": PILOT_API_KEY,
                "VELANTRIM_ALLOW_OPEN": "false",
                "VELANTRIM_NETWORK_MODE": "deny",
                "VELANTRIM_REMOTE_DATA_MODE": "never",
                "VELANTRIM_DB_PATH": str(tmp_path / "pilot.db"),
                "VELANTRIM_NGRAM_DB": str(tmp_path / "pilot-ngram.db"),
                "VELANTRIM_NOTES_DB": str(tmp_path / "pilot-notes.db"),
                "CORE_BLOCKS_DB": str(tmp_path / "pilot-blocks.db"),
                "NOTEBOOK_DB": str(tmp_path / "pilot-notebook.db"),
                "LLM_PROVIDER": "none",
                "SLEEP_WORKER_ENABLED": "false",
                "ENABLE_CAUSAL_GRAPH": "0",
                "ENABLE_VELUM": "0",
                "VELANTRIM_MCP_MAX_CAPABILITY": "reader",
            }
        )

        process: subprocess.Popen | None = None
        try:
            process, base_url = _start_server(root, env)
            status, health = _request_json("GET", f"{base_url}/health")
            if status != 200:
                raise RuntimeError(f"Pilot health failed: HTTP {status} {health}")
            results.append({"scenario": "startup_health", "status": "PASS"})

            fact = _seed_validated_fact(base_url)
            chat = _offline_chat(base_url)
            results.append(
                {
                    "scenario": "validated_memory_chat",
                    "status": "PASS",
                    "epistemic_state": fact.get("epistemic_state"),
                    "facts_count": chat.get("facts_count"),
                }
            )

            pilot_file = tmp_path / "pilot-note.txt"
            pilot_file.write_text(
                "Titan bounded pilot document. The local launch color is amber.\n",
                encoding="utf-8",
            )
            ingested = ingest_file(
                pilot_file,
                base_url=base_url,
                api_key=PILOT_API_KEY,
            )
            if int(ingested.get("characters") or 0) <= 0 or int(ingested.get("requests") or 0) <= 0:
                raise RuntimeError(f"Pilot file ingestion produced no usable result: {ingested}")
            results.append(
                {
                    "scenario": "file_ingest",
                    "status": "PASS",
                    "file_type": ingested.get("file_type"),
                    "requests": ingested.get("requests"),
                }
            )

            tools = list_tools(
                base_url=base_url,
                api_key=PILOT_API_KEY,
                capability="reader",
            )
            names = {str(tool.get("name") or "") for tool in tools}
            if "search_facts" not in names:
                raise RuntimeError(f"Pilot MCP reader surface missing search_facts: {sorted(names)}")
            results.append(
                {
                    "scenario": "mcp_reader_tools",
                    "status": "PASS",
                    "visible_tools": len(tools),
                }
            )

            _stop_server(process)
            process = None
            process, restarted_url = _start_server(root, env)
            status, restored = _request_json(
                "GET",
                f"{restarted_url}/facts/stage10_pilot_fact",
            )
            if status != 200 or restored.get("epistemic_state") != "Validated":
                raise RuntimeError(f"Pilot restart did not restore validated fact: {status} {restored}")
            _offline_chat(restarted_url)
            results.append({"scenario": "restart_continuity", "status": "PASS"})
        finally:
            if process is not None:
                _stop_server(process)

    print("STAGE10_BOUNDED_PILOT=PASS")
    print(
        json.dumps(
            {
                "pilot": "Titan V1 bounded local-first pilot",
                "production_authorized": False,
                "remote_canon": False,
                "external_llm_required": False,
                "scenarios": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
