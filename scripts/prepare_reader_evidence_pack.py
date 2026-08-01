#!/usr/bin/env python3
"""Prepare a verified local Reader Core evidence pack and blind packets.

Example:
    python scripts/prepare_reader_evidence_pack.py \
      --root /secure/reader-evidence \
      --spec /secure/reader-evidence/evidence-spec.json \
      --output /secure/reader-evidence/artifacts/operator-pack.json \
      --packet-dir /secure/reader-evidence/artifacts/annotation-packets

The command does not upload files, execute Reader Core, or authorize promotion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.reader_corpus_adjudication import ReaderCorpusError  # noqa: E402
from core.reader_evidence_intake import ReaderEvidenceIntakeError  # noqa: E402
from core.reader_evidence_pack import (  # noqa: E402
    ReaderEvidencePackBuilder,
    ReaderEvidencePackError,
    load_evidence_source_spec,
    write_annotation_packets,
    write_canonical_json,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a content-addressed Reader Core evidence operator pack and "
            "separate blind annotation packet JSON files from local inputs."
        )
    )
    parser.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Local root containing corpus documents and guideline bytes.",
    )
    parser.add_argument(
        "--spec",
        required=True,
        type=Path,
        help="Evidence source specification JSON.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Canonical operator evidence pack JSON output.",
    )
    parser.add_argument(
        "--packet-dir",
        required=True,
        type=Path,
        help="Empty output directory for separate blind annotation packets.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        spec = load_evidence_source_spec(args.spec)
        pack = ReaderEvidencePackBuilder().build(root=args.root, spec=spec)
        packet_paths = write_annotation_packets(
            args.packet_dir,
            pack.annotation_packets,
        )
        write_canonical_json(args.output, pack)
    except (
        ReaderEvidencePackError,
        ReaderEvidenceIntakeError,
        ReaderCorpusError,
        OSError,
        UnicodeError,
    ) as exc:
        print(f"reader evidence pack error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "annotation_packet_count": len(packet_paths),
        "initial_ready_case_count": len(
            pack.initial_readiness.ready_case_ids
        ),
        "operator_output": str(args.output),
        "pack_id": pack.pack_id,
        "package_id": pack.package.package_id,
        "packet_directory": str(args.packet_dir),
        "plan_id": pack.plan.plan_id,
        "production_evidence_complete": False,
        "requires_human_annotation": True,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
