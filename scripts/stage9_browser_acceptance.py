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


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_http(url: str, timeout_s: float = 45.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
        time.sleep(0.25)
    raise RuntimeError(f"Titan did not become ready: {last_error}")


def _request_json(method: str, url: str, payload: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
        return int(response.status), body


def _post_json(url: str, payload: dict) -> tuple[int, dict]:
    return _request_json("POST", url, payload)


def _patch_json(url: str, payload: dict) -> tuple[int, dict]:
    return _request_json("PATCH", url, payload)


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        print("Stage 9 requires Playwright: pip install playwright", file=sys.stderr)
        print("Then install Chromium: python -m playwright install chromium", file=sys.stderr)
        raise SystemExit(2) from exc

    root = Path(__file__).resolve().parents[1]
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    with tempfile.TemporaryDirectory(prefix="titan-stage9-") as tmp:
        tmp_path = Path(tmp)
        env = os.environ.copy()
        env.update(
            {
                "VELANTRIM_API_KEY": "",
                "VELANTRIM_ALLOW_OPEN": "true",
                "VELANTRIM_NETWORK_MODE": "deny",
                "VELANTRIM_REMOTE_DATA_MODE": "never",
                "VELANTRIM_DB_PATH": str(tmp_path / "stage9.db"),
                "VELANTRIM_NGRAM_DB": str(tmp_path / "stage9-ngram.db"),
                "VELANTRIM_NOTES_DB": str(tmp_path / "stage9-notes.db"),
                "CORE_BLOCKS_DB": str(tmp_path / "stage9-blocks.db"),
                "NOTEBOOK_DB": str(tmp_path / "stage9-notebook.db"),
                "LLM_PROVIDER": "none",
                "SLEEP_WORKER_ENABLED": "false",
                "ENABLE_CAUSAL_GRAPH": "0",
                "ENABLE_VELUM": "0",
                "PORT": str(port),
            }
        )

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
            env=env,
        )

        try:
            _wait_http(f"{base_url}/health")

            fact_id = "stage9_browser_fact"
            status, _ = _post_json(
                f"{base_url}/facts",
                {
                    "fact_id": fact_id,
                    "claim": "my name is Stage Nine User",
                    "source": "stage9-browser-acceptance",
                    "confidence": 0.9,
                    "metadata": {
                        "memory_category": "personal",
                        "evidence_refs": ["stage9-source-1", "stage9-source-2"],
                    },
                },
            )
            if status not in (200, 201):
                raise RuntimeError(f"Could not seed Stage 9 fact: HTTP {status}")

            # Use Titan's existing public ESM + TruthGate path. The acceptance
            # seed must satisfy the same BALANCED policy as ordinary memory;
            # the browser test must not weaken recall rules merely to pass.
            for target in ("Hypothesized", "Supported", "Validated"):
                status, body = _patch_json(
                    f"{base_url}/facts/{fact_id}/transition",
                    {"new_state": target, "by": "stage9-browser-acceptance"},
                )
                if status != 200:
                    raise RuntimeError(
                        f"Could not transition Stage 9 fact to {target}: HTTP {status} {body}"
                    )
            if body.get("epistemic_state") != "Validated":
                raise RuntimeError("Stage 9 fact did not reach Validated through TruthGate")

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context(locale="en-US")
                page = context.new_page()
                page.goto(f"{base_url}/console/", wait_until="networkidle")

                page.locator("#messages").wait_for(state="visible", timeout=15_000)

                toggle = page.locator("#llmToggleBtn")
                if toggle.count() and "on" in (toggle.get_attribute("class") or "").split():
                    toggle.click()

                composer = page.locator(".composer textarea").first
                composer.wait_for(state="visible", timeout=10_000)
                composer.fill("what is my name?")
                page.locator(".composer-send-btn").click()

                bot_messages = page.locator("#messages .msg.bot")
                bot_messages.last.wait_for(state="visible", timeout=20_000)
                page.wait_for_function(
                    "() => document.querySelector('#messages')?.innerText.includes('Stage Nine User')",
                    timeout=20_000,
                )

                text = page.locator("#messages").inner_text()
                if "Stage Nine User" not in text:
                    raise RuntimeError("Console did not surface the validated memory fact")

                print("STAGE9_BROWSER_ACCEPTANCE=PASS")
                print(f"CONSOLE_URL={base_url}/console/")
                print("FLOW=real Chromium -> Console composer -> /chat -> validated memory -> DOM reply")
                print("LLM=disabled; external network/provider not required")
                browser.close()
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
