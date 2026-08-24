"""Bounded Reader Product -> RDR-14 benchmark adapter.

This module connects an already-selected ``SemanticReader`` and the existing
``ReaderProductPipeline`` to the existing RDR-14 ``ReaderLocalPipeline``
protocol. It does not select providers, load secrets, upload documents, wire
``/query``, write memory/Canon/graph state, call TruthGate/Write Gate, schedule
background work, or authorize promotion/live use.

The corpus document is re-verified against its content-addressed RDR-11
descriptor before every replay. The adapter then runs the existing foreground
Reader Product path and normalizes its artifacts through the existing RDR-12
``ReaderDocumentPrediction.from_artifacts`` contract.
"""

from __future__ import annotations

import asyncio
from hashlib import sha256
import json
from pathlib import Path
import time

from core.critical_exceptions import CriticalExceptionCandidate
from core.document_structure import DocumentStructureFormat
from core.reader_benchmark_executor import (
    ReaderLocalBenchmarkCase,
    ReaderLocalPipelineResult,
)
from core.reader_benchmark_scoring import (
    ReaderDocumentPrediction,
    ReaderExecutionMeasurement,
)
from core.reader_corpus_adjudication import CorpusDocumentDescriptor
from core.reader_product_pipeline import ReaderProductConfig, ReaderProductPipeline
from core.semantic_reader import RawSource, SemanticReader


class ReaderProductBenchmarkAdapterError(RuntimeError):
    """Raised when the bounded benchmark bridge cannot execute safely."""


class ReaderProductBenchmarkAdapter:
    """Explicit RDR-14 adapter for the existing Reader Product pipeline."""

    adapter_version = "reader-product-benchmark-adapter.v1"

    def __init__(
        self,
        *,
        corpus_root: str | Path,
        reader: SemanticReader,
        config: ReaderProductConfig | None = None,
    ) -> None:
        root = Path(corpus_root).resolve()
        if not root.is_dir():
            raise ReaderProductBenchmarkAdapterError(
                "corpus_root must be an existing directory"
            )
        if not isinstance(reader, SemanticReader):
            raise ReaderProductBenchmarkAdapterError(
                "reader must implement SemanticReader"
            )
        if config is not None and not isinstance(config, ReaderProductConfig):
            raise ReaderProductBenchmarkAdapterError(
                "config must be a ReaderProductConfig or None"
            )
        self._root = root
        self._reader = reader
        self._config = config

    def run_case(
        self,
        case: ReaderLocalBenchmarkCase,
        *,
        replay_index: int,
    ) -> ReaderLocalPipelineResult:
        if not isinstance(case, ReaderLocalBenchmarkCase):
            raise ReaderProductBenchmarkAdapterError(
                "case must be a ReaderLocalBenchmarkCase"
            )
        if replay_index not in (1, 2):
            raise ReaderProductBenchmarkAdapterError(
                "replay_index must be 1 or 2"
            )

        text = self._verified_text(case.descriptor)
        source = RawSource(
            document_id=case.descriptor.document_id,
            text=text,
            source_revision=case.descriptor.source_revision,
        )

        started = time.perf_counter_ns()
        try:
            result = asyncio.run(
                ReaderProductPipeline(
                    self._reader,
                    config=self._config,
                ).read(
                    source,
                    document_format=DocumentStructureFormat.PLAIN_TEXT,
                    session_key=(
                        f"benchmark:{case.case_id}:replay:{replay_index}:"
                        f"{case.descriptor.source_revision}"
                    ),
                )
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as exc:
            raise ReaderProductBenchmarkAdapterError(
                f"Reader Product execution failed: {type(exc).__name__}"
            ) from exc
        elapsed_ms = max(0, (time.perf_counter_ns() - started) // 1_000_000)

        exceptions = tuple(
            candidate
            for scan in result.exception_scans
            for candidate in scan.candidates
            if isinstance(candidate, CriticalExceptionCandidate)
        )
        prediction = ReaderDocumentPrediction.from_artifacts(
            document_descriptor_id=case.descriptor.descriptor_id,
            cards=result.cards,
            exception_candidates=exceptions,
            relation_set=result.relations,
            synthesis=result.synthesis,
            warnings=result.warnings,
        )

        projection_bytes = len(
            json.dumps(
                prediction.identity_payload(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        )
        warnings = [
            "model_tokens_unavailable_from_reader_product_v1",
            "section_latencies_unavailable_from_reader_product_v1",
            "rebuild_time_unavailable_from_reader_product_v1",
            "resume_metrics_unavailable_from_reader_product_v1",
            "query_path_not_invoked_by_benchmark_adapter",
            *result.warnings,
        ]
        measurement = ReaderExecutionMeasurement(
            section_latencies_ms=(),
            session_wall_time_ms=elapsed_ms,
            model_tokens=0,
            projection_bytes=projection_bytes,
            rebuild_time_ms=0,
            query_path_latency_delta_ms=0,
            resume_reused_units=0,
            resume_eligible_units=0,
            truth_gate_bypass_count=0,
            query_path_write_count=0,
            direct_canon_write_count=0,
            untrusted_instruction_execution_count=0,
            warnings=tuple(sorted(dict.fromkeys(warnings))),
        )
        artifact_ids = tuple(
            sorted(
                {
                    result.session.session_id,
                    result.coverage_map.coverage_map_id,
                    result.initial_reread_plan.reread_plan_id,
                    result.remaining_reread_plan.reread_plan_id,
                    *(
                        (result.relations.relation_set_id,)
                        if result.relations is not None
                        else ()
                    ),
                    *(
                        (result.synthesis.synthesis_id,)
                        if result.synthesis is not None
                        else ()
                    ),
                }
            )
        )
        return ReaderLocalPipelineResult(
            prediction=prediction,
            measurement=measurement,
            run_artifact_ids=artifact_ids,
        )

    def _verified_text(self, descriptor: CorpusDocumentDescriptor) -> str:
        if not isinstance(descriptor, CorpusDocumentDescriptor):
            raise ReaderProductBenchmarkAdapterError(
                "descriptor must be a CorpusDocumentDescriptor"
            )

        rebuilt = CorpusDocumentDescriptor.from_file(
            root=self._root,
            relative_path=descriptor.relative_path,
            document_id=descriptor.document_id,
            media_type=descriptor.media_type,
            usage_basis=descriptor.usage_basis,
            rights_reference=descriptor.rights_reference,
            privacy_class=descriptor.privacy_class,
            redistribution_allowed=descriptor.redistribution_allowed,
        )
        if rebuilt.descriptor_id != descriptor.descriptor_id:
            raise ReaderProductBenchmarkAdapterError(
                "corpus document no longer matches benchmark descriptor"
            )

        path = (self._root / descriptor.relative_path).resolve()
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != descriptor.content_sha256:
            raise ReaderProductBenchmarkAdapterError(
                "corpus bytes changed after descriptor verification"
            )
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReaderProductBenchmarkAdapterError(
                "corpus document is not valid UTF-8"
            ) from exc
        if len(text) != descriptor.char_count:
            raise ReaderProductBenchmarkAdapterError(
                "corpus character count changed after descriptor verification"
            )
        return text
