from __future__ import annotations

import argparse
import asyncio
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable

from core.document_structure import DocumentStructureFormat
from core.reader_core_contracts import CoverageAxis
from core.reader_parse_bridge import resolve_reader_document_format
from core.reader_product_pipeline import (
    ReaderProductConfig,
    ReaderProductPipeline,
    ReaderProductPipelineError,
)
from core.readers.llm_adapter import LlmReaderAdapter
from core.semantic_reader import RawSource, ReaderMode


_PROVIDER_ENV = {
    "openai": ("OPENAI_API_KEY", "OPENAI_MODEL", "chat-latest"),
    "deepseek": ("DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "deepseek-v4-flash"),
    "gemini": ("GEMINI_API_KEY", "GEMINI_MODEL", "gemini-2.5-flash"),
    "openrouter": ("OPENROUTER_API_KEY", "OPENROUTER_MODEL", "openai/chat-latest"),
    "anthropic": ("ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
}


class ReadDocumentError(RuntimeError):
    """A user-actionable document-reading failure."""


def project_root(script_file: str | Path = __file__) -> Path:
    return Path(script_file).resolve().parents[1]


def venv_python(root: Path) -> Path:
    if os.name == "nt":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def maybe_reexec_in_venv(root: Path, argv: list[str] | None = None) -> int | None:
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
    args = [
        str(target),
        str(Path(__file__).resolve()),
        *(argv if argv is not None else sys.argv[1:]),
    ]
    return subprocess.call(args, cwd=root)


def load_env_file(path: Path) -> None:
    """Load local Titan config without overwriting explicit process environment."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def parse_local_file(path: Path):
    if not path.is_file():
        raise ReadDocumentError(f"File not found: {path}")
    try:
        from core.file_parsers import FileIngester
    except ImportError as exc:
        raise ReadDocumentError(
            "File parser dependencies are missing. Re-run scripts/bootstrap_titan.py."
        ) from exc

    parsed = FileIngester().ingest(str(path))
    if parsed.error:
        raise ReadDocumentError(parsed.error)
    if not parsed.extracted_text or not parsed.extracted_text.strip():
        raise ReadDocumentError("The parser returned no readable text from this file.")
    return parsed


def resolve_reader_from_env() -> LlmReaderAdapter:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider not in _PROVIDER_ENV:
        raise ReadDocumentError(
            "No supported LLM provider is configured. Run scripts/configure_provider.py first."
        )
    key_name, model_name, default_model = _PROVIDER_ENV[provider]
    api_key = os.getenv(key_name, "").strip()
    model = os.getenv(model_name, "").strip() or default_model
    if not api_key:
        raise ReadDocumentError(
            f"{key_name} is missing. Run scripts/configure_provider.py again."
        )
    return LlmReaderAdapter(provider=provider, model=model, api_key=api_key)


def document_format_for(path: Path, parsed=None) -> DocumentStructureFormat:
    structured_data = getattr(parsed, "structured_data", None)
    return resolve_reader_document_format(
        path_suffix=path.suffix,
        structured_data=structured_data,
    ).document_format


def raw_source_for(path: Path, text: str) -> RawSource:
    digest = sha256(text.encode("utf-8")).hexdigest()
    return RawSource(
        document_id=f"reader-document:{digest}",
        text=text,
        source_revision=f"sha256:{digest}",
    )


def _coverage_payload(result) -> dict[str, float | None]:
    return {
        axis.value: result.coverage_map.axis(axis).ratio
        for axis in CoverageAxis
    }


def _product_status(result) -> str:
    if not result.complete:
        return "degraded"
    if result.remaining_reread_plan.tasks or result.remaining_reread_plan.deferred_items:
        return "complete_with_open_work"
    return "complete"


def result_payload(result, *, file_name: str, file_type: str) -> dict[str, object]:
    exceptions = [
        {
            "category": candidate.category.value,
            "statement": candidate.statement_text,
            "start_offset": candidate.statement_span.start_offset,
            "end_offset": candidate.statement_span.end_offset,
        }
        for scan in result.exception_scans
        for candidate in scan.candidates
    ]
    return {
        "file": file_name,
        "file_type": file_type,
        "status": _product_status(result),
        "complete": result.complete,
        "document_id": result.source.document_id,
        "source_revision": result.source.source_revision,
        "session_id": result.session.session_id,
        "session_state": result.session.state.value,
        "total_units": result.total_units,
        "completed_units": result.completed_units,
        "reader_attempts": result.reader_attempts,
        "reread_attempts": result.reread_attempts,
        "remaining_reread_tasks": len(result.remaining_reread_plan.tasks),
        "deferred_reread_items": len(result.remaining_reread_plan.deferred_items),
        "coverage": _coverage_payload(result),
        "source_grounded_digest": result.source_grounded_digest,
        "synthesis_id": result.synthesis.synthesis_id if result.synthesis else None,
        "exceptions": exceptions,
        "warnings": list(result.warnings),
    }


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read a local PDF/DOCX/EPUB/text document through Titan Reader Core "
            "without writing the result to memory or Canon."
        )
    )
    parser.add_argument("file", type=Path)
    parser.add_argument(
        "--mode",
        choices=[item.value for item in ReaderMode],
        default=ReaderMode.STANDARD.value,
        help="Initial Reader depth. Selective reread may deepen weak units once.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable summary instead of the human report.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


async def read_document(path: Path, *, mode: ReaderMode):
    parsed = parse_local_file(path)
    reader = resolve_reader_from_env()
    source = raw_source_for(path, parsed.extracted_text)
    structure_resolution = resolve_reader_document_format(
        path_suffix=path.suffix,
        structured_data=parsed.structured_data,
    )
    config = ReaderProductConfig(initial_mode=mode)
    result = await ReaderProductPipeline(reader, config=config).read(
        source,
        document_format=structure_resolution.document_format,
    )
    if structure_resolution.reason_code == "parser_declared_markdown":
        result = replace(
            result,
            warnings=tuple(
                dict.fromkeys(
                    (*result.warnings, "reader_structure:parser_declared_markdown")
                )
            ),
        )
    return parsed, result


def _print_human(payload: dict[str, object]) -> None:
    status = str(payload["status"]).upper()
    print(f"[Titan Reader] {status}: {payload['file']} ({payload['file_type']})")
    print(
        "[Titan Reader] Units: "
        f"{payload['completed_units']}/{payload['total_units']}; "
        f"reader attempts: {payload['reader_attempts']}; "
        f"rereads: {payload['reread_attempts']}"
    )
    print("\nSOURCE-GROUNDED DIGEST")
    print(payload["source_grounded_digest"] or "(no grounded digest available)")

    exceptions = payload["exceptions"]
    if isinstance(exceptions, list) and exceptions:
        print("\nCRITICAL EXCEPTION CANDIDATES")
        for item in exceptions[:20]:
            if isinstance(item, dict):
                print(f"- [{item['category']}] {item['statement']}")

    remaining = payload["remaining_reread_tasks"]
    deferred = payload["deferred_reread_items"]
    if remaining:
        print(f"\n[Titan Reader] Remaining bounded reread tasks: {remaining}")
    if deferred:
        print(f"[Titan Reader] Deferred reread items: {deferred}")
    if payload["status"] == "complete_with_open_work":
        print(
            "[Titan Reader] All reading units were processed, but explicit "
            "follow-up work remains open; do not treat this as fully resolved."
        )

    warnings = payload["warnings"]
    if isinstance(warnings, list) and warnings:
        print("\nBOUNDARY / WARNINGS")
        for warning in warnings:
            print(f"- {warning}")
    print("\n[Titan Reader] Read-side result only: no memory/Canon write was performed.")


def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = project_root()
    load_env_file(root / ".env")
    parsed, result = asyncio.run(
        read_document(
            args.file.expanduser().resolve(),
            mode=ReaderMode(args.mode),
        )
    )
    payload = result_payload(
        result,
        file_name=args.file.name,
        file_type=parsed.file_type,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_human(payload)
    return 0 if result.complete else 3


def main() -> int:
    root = project_root()
    delegated = maybe_reexec_in_venv(root)
    if delegated is not None:
        return delegated
    try:
        return run()
    except (ReadDocumentError, ReaderProductPipelineError) as exc:
        print(f"[Titan Reader] Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\n[Titan Reader] Cancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
