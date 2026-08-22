from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

DEFAULT_PORT = 8755
REQUEST_CHUNK_CHARS = 20_000


class FileIngestError(RuntimeError):
    """A user-actionable file-ingestion failure."""


def project_root(script_file: str | Path = __file__) -> Path:
    return Path(script_file).resolve().parents[1]


def venv_python(root: Path) -> Path:
    if os.name == "nt":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def maybe_reexec_in_venv(root: Path, argv: list[str] | None = None) -> int | None:
    """Use the Stage-2 managed runtime automatically when invoked with system Python."""
    py = venv_python(root)
    if not py.exists():
        return None
    try:
        current = Path(sys.executable).resolve()
        target = py.resolve()
    except OSError:
        return None
    if current == target:
        return None
    args = [str(target), str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])]
    return subprocess.call(args, cwd=root)


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def safe_source_name(path: Path) -> str:
    name = re.sub(r"[^\w.\-]", "_", path.name, flags=re.UNICODE)
    return ("file:" + name)[:180]


def split_text(text: str, limit: int = REQUEST_CHUNK_CHARS) -> list[str]:
    value = (text or "").strip()
    if not value:
        return []
    return [value[i : i + limit] for i in range(0, len(value), limit)]


def post_ingest(
    *,
    base_url: str,
    api_key: str,
    text: str,
    source: str,
    opener=urllib.request.urlopen,
) -> dict:
    payload = json.dumps(
        {"text": text, "source": source, "confidence": 0.65},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/ingest/text",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
        },
        method="POST",
    )
    try:
        with opener(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise FileIngestError(f"Titan rejected file ingestion (HTTP {exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise FileIngestError(
            f"Titan is not reachable at {base_url}. Start it with scripts/bootstrap_titan.py first."
        ) from exc


def parse_file(path: Path):
    try:
        from core.file_parsers import FileIngester
    except ImportError as exc:
        raise FileIngestError(
            "File parser dependencies are missing. Re-run scripts/bootstrap_titan.py to prepare the V1 runtime."
        ) from exc

    result = FileIngester().ingest(str(path))
    if result.error:
        raise FileIngestError(result.error)
    if not result.extracted_text or not result.extracted_text.strip():
        raise FileIngestError("The parser returned no usable text from this file.")
    return result


def ingest_file(path: Path, *, base_url: str, api_key: str, opener=urllib.request.urlopen) -> dict:
    if not path.is_file():
        raise FileIngestError(f"File not found: {path}")
    if not api_key:
        raise FileIngestError("VELANTRIM_API_KEY is missing from .env.")

    parsed = parse_file(path)
    pieces = split_text(parsed.extracted_text)
    if not pieces:
        raise FileIngestError("The file contains no ingestible text.")

    source = safe_source_name(path)
    responses = []
    for index, piece in enumerate(pieces, start=1):
        part_source = source if len(pieces) == 1 else f"{source}:part-{index}-of-{len(pieces)}"
        responses.append(
            post_ingest(
                base_url=base_url,
                api_key=api_key,
                text=piece,
                source=part_source,
                opener=opener,
            )
        )

    return {
        "file": path.name,
        "file_type": parsed.file_type,
        "extraction_method": parsed.extraction_method,
        "characters": len(parsed.extracted_text),
        "requests": len(responses),
        "responses": responses,
    }


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse a local file with Titan's existing FileIngester and ingest its text through the canonical local /ingest/text API."
    )
    parser.add_argument("file", type=Path)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser.parse_args(list(argv) if argv is not None else None)


def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = project_root()
    env = read_env(root / ".env")
    api_key = env.get("VELANTRIM_API_KEY", "")
    result = ingest_file(
        args.file.expanduser().resolve(),
        base_url=f"http://127.0.0.1:{args.port}",
        api_key=api_key,
    )
    print(f"[Titan] File ingested: {result['file']} ({result['file_type']})")
    print(f"[Titan] Extracted characters: {result['characters']}; API requests: {result['requests']}")
    print("[Titan] The content is now available to the normal Console/memory path.")
    return 0


def main() -> int:
    root = project_root()
    delegated = maybe_reexec_in_venv(root)
    if delegated is not None:
        return delegated
    try:
        return run()
    except FileIngestError as exc:
        print(f"[Titan] File ingest error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
