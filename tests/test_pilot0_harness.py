from __future__ import annotations

import builtins
from hashlib import sha256
from io import BytesIO
from importlib import metadata
import json
from pathlib import Path
import socket
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

# The local test environment intentionally has no httpx installed. The router's
# pure payload helpers are exercised behind a transport stub; no HTTP call can run.
try:
    import httpx  # noqa: F401
except ModuleNotFoundError:
    httpx_stub = types.ModuleType("httpx")

    class _NoNetworkAsyncClient:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("HTTP transport is disabled in Pilot-0 tests")

    class _HttpxResponseStub:
        pass

    httpx_stub.AsyncClient = _NoNetworkAsyncClient  # type: ignore[attr-defined]
    httpx_stub.Response = _HttpxResponseStub  # type: ignore[attr-defined]
    sys.modules["httpx"] = httpx_stub

from core.knowledge_capsule import CapsuleClaim, ClaimModality, KnowledgeCapsule, SourceSpan
from core.llm_router import LlmCallConfig, _deepseek_request_body
from core.pilot0.artifact import (
    Pilot0ArtifactError,
    canonical_json_bytes,
    freeze_reader_output,
    parse_frozen_reader_json,
)
from core.pilot0.config import Pilot0ReaderConfig
from core.pilot0.evaluator import (
    INSUFFICIENT_EVIDENCE,
    Pilot0EvaluationInputError,
    evaluate_q1_q15_frozen,
    load_frozen_evaluator_inputs,
)
from core.pilot0.pdf_input import (
    PARSER_NAME,
    PINNED_PARSER_VERSION,
    Pilot0PdfError,
    _pinned_pdf_reader,
    parse_local_pdf,
)
from core.readers.llm_adapter import LlmReaderAdapter
from core.semantic_reader import (
    RawSource,
    ReaderBudget,
    ReaderMode,
    ReaderResult,
)


class FakeSemanticReader:
    reader_id = "test.synthetic-reader"
    reader_version = "0.1-test"

    async def extract(self, source, *, mode, budget):  # pragma: no cover - must not be called
        raise AssertionError("artifact serialization must not execute Reader extraction")


def synthetic_pdf_bytes() -> bytes:
    """Build a tiny PDF in memory with local pypdf; no corpus fixture is used."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=220, height=100)
    font = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
        }
    )
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 10 50 Td (Synthetic Pilot PDF) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(content)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def synthetic_reader_inputs():
    text = "Synthetic evidence supports a bounded claim."
    source_text = text + " Additional synthetic context stays outside the Reader claim."
    source = RawSource(
        document_id="synthetic-doc-01",
        text=source_text,
        source_revision="sha256:" + "a" * 64,
    )
    span = SourceSpan.from_text(
        document_id=source.document_id,
        raw_text=source.text,
        start_offset=0,
        end_offset=len(text),
        source_revision=source.source_revision,
    )
    claim = CapsuleClaim.create(
        text=text,
        modality=ClaimModality.OBSERVATION,
        source_spans=(span,),
        extraction_confidence=1.0,
    )
    capsule = KnowledgeCapsule.create(
        source_document_id=source.document_id,
        essence=text,
        claims=(claim,),
        reader_id=FakeSemanticReader.reader_id,
        reader_version=FakeSemanticReader.reader_version,
        coverage_score=1.0,
        compression_ratio=1.0,
        prompt_version="synthetic-prompt-v1",
    )
    return FakeSemanticReader(), source, ReaderResult.success(capsule)


def questions_json() -> bytes:
    return json.dumps(
        {"questions": [{"id": f"Q{i}", "question": f"Synthetic question {i}?"} for i in range(1, 16)]},
        separators=(",", ":"),
    ).encode("utf-8")


def questions_markdown() -> bytes:
    lines = ["# Synthetic blind question set", ""]
    lines.extend(f"Q{i}. Synthetic markdown question {i}?" for i in range(1, 16))
    return ("\n".join(lines) + "\n").encode("utf-8")


def frozen_bytes():
    reader, source, result = synthetic_reader_inputs()
    return freeze_reader_output(
        reader,
        source,
        mode=ReaderMode.STANDARD,
        budget=ReaderBudget(max_source_chars=1000, max_claims=8, max_essence_chars=100),
        result=result,
    )


class Pilot0HarnessTests(unittest.TestCase):
    def test_pinned_parser_extracts_only_synthetic_local_pdf(self):
        try:
            installed = metadata.version(PARSER_NAME)
        except metadata.PackageNotFoundError:
            self.skipTest("the exact local Pilot-0 parser is not installed in this environment")
        if installed != PINNED_PARSER_VERSION:
            self.skipTest("the exact local Pilot-0 parser version is not installed in this environment")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "synthetic.pdf"
            path.write_bytes(synthetic_pdf_bytes())
            with patch("socket.socket.connect", side_effect=AssertionError("network denied")):
                parsed = parse_local_pdf(path)
        self.assertEqual(parsed.parser_name, PARSER_NAME)
        self.assertEqual(parsed.parser_version, PINNED_PARSER_VERSION)
        self.assertEqual(parsed.page_count, 1)
        self.assertIn("Synthetic Pilot PDF", parsed.text)
        self.assertTrue(parsed.source_revision.startswith("sha256:"))

    def test_parser_fails_closed_on_version_mismatch_without_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "synthetic.pdf"
            path.write_bytes(b"%PDF-1.4\n")
            with patch("core.pilot0.pdf_input.metadata.version", return_value="99.0"):
                with self.assertRaises(Pilot0PdfError):
                    parse_local_pdf(path)

    def test_missing_parser_does_not_try_fallback_or_download(self):
        imported = []
        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name in {"pypdf", "fitz"}:
                imported.append(name)
                raise ModuleNotFoundError(name)
            return original_import(name, *args, **kwargs)

        with patch("core.pilot0.pdf_input.metadata.version", return_value=PINNED_PARSER_VERSION):
            with patch("builtins.__import__", side_effect=guarded_import):
                with self.assertRaises(Pilot0PdfError):
                    _pinned_pdf_reader()
        self.assertEqual(imported, ["pypdf"])

    def test_parser_refuses_non_pdf_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "raw.txt"
            path.write_text("synthetic", encoding="utf-8")
            with self.assertRaises(Pilot0PdfError):
                parse_local_pdf(path)

    def test_freeze_is_canonical_deterministic_and_excludes_secrets_and_source_text(self):
        first = frozen_bytes()
        second = frozen_bytes()
        self.assertEqual(first.json_bytes, second.json_bytes)
        self.assertEqual(first.sha256, second.sha256)
        self.assertEqual(first.payload_sha256, second.payload_sha256)
        text = first.json_bytes.decode("utf-8")
        self.assertNotIn('"api_key"', text)
        self.assertNotIn('"secret"', text)
        self.assertNotIn('"source_map"', text)
        payload = parse_frozen_reader_json(first.json_bytes, expected_sha256=first.sha256)
        self.assertEqual(payload["source"]["revision"], "sha256:" + "a" * 64)
        self.assertEqual(payload["config"]["reader"]["model_selection"], "OWNER_SELECTED")
        self.assertEqual(payload["cards"], ())
        self.assertEqual(payload["relations"], ())
        self.assertEqual(payload["coverage"]["reader_core_axes"], ())
        self.assertEqual(payload["synthesis"]["essence"], "Synthetic evidence supports a bounded claim.")
        self.assertEqual(payload["execution"]["claim_count"], 1)
        self.assertEqual(payload["execution"]["local_network_calls"], 0)
        self.assertNotIn("Synthetic evidence supports a bounded claim.", text.split('"claims"')[0])
        with self.assertRaises(TypeError):
            payload["reader"]["id"] = "changed"

    def test_frozen_parser_rejects_tampered_thinking_config_even_with_recomputed_hash(self):
        envelope = json.loads(frozen_bytes().json_bytes)
        envelope["payload"]["config"]["reader"]["deepseek_thinking"] = "enabled"
        envelope["payload_sha256"] = sha256(
            canonical_json_bytes(envelope["payload"])
        ).hexdigest()
        tampered = canonical_json_bytes(envelope)
        with self.assertRaises(Pilot0ArtifactError):
            parse_frozen_reader_json(tampered)

    def test_freeze_rejects_source_revision_or_span_mismatch(self):
        reader, source, result = synthetic_reader_inputs()
        wrong_source = RawSource(
            document_id=source.document_id,
            text=source.text,
            source_revision="different-revision",
        )
        with self.assertRaises(Pilot0ArtifactError):
            freeze_reader_output(
                reader,
                wrong_source,
                mode=ReaderMode.STANDARD,
                budget=ReaderBudget(),
                result=result,
            )

    def test_secret_shaped_claim_is_rejected_not_persisted(self):
        text = "Bearer abcdefghijklmnopqrstuv"
        source = RawSource("synthetic-secret", text, "synthetic-r1")
        span = SourceSpan.from_text(
            document_id=source.document_id,
            raw_text=text,
            start_offset=0,
            end_offset=len(text),
            source_revision=source.source_revision,
        )
        claim = CapsuleClaim.create(
            text=text,
            modality=ClaimModality.OBSERVATION,
            source_spans=(span,),
            extraction_confidence=1.0,
        )
        from core.knowledge_capsule import KnowledgeCapsule

        capsule = KnowledgeCapsule.create(
            source_document_id=source.document_id,
            essence=text,
            claims=(claim,),
            reader_id=FakeSemanticReader.reader_id,
            reader_version=FakeSemanticReader.reader_version,
        )
        with self.assertRaises(Pilot0ArtifactError):
            freeze_reader_output(
                FakeSemanticReader(),
                source,
                mode=ReaderMode.FAST,
                budget=ReaderBudget(),
                result=ReaderResult.success(capsule),
            )

    def test_q1_q15_uses_only_frozen_representation_and_abstains_when_fake_does(self):
        frozen = frozen_bytes()
        seen = []

        def fake_evaluator(reader_view, question_id, question):
            seen.append((question_id, question, reader_view["schema"]))
            return "Synthetic answer" if question_id == "Q1" else None

        with patch("socket.socket.connect", side_effect=AssertionError("network denied")):
            answers = evaluate_q1_q15_frozen(
                frozen.json_bytes,
                questions_json(),
                evaluator=fake_evaluator,
                expected_sha256=frozen.sha256,
            )
        self.assertEqual(len(answers), 15)
        self.assertEqual(answers[0].answer, "Synthetic answer")
        self.assertTrue(all(item.answer == INSUFFICIENT_EVIDENCE for item in answers[1:]))
        self.assertEqual(len(seen), 15)
        self.assertEqual(seen[0][2], "pilot0.frozen-reader.v1")

    def test_evaluator_rejects_pdf_raw_text_maps_keys_prior_answers_and_wrong_hash(self):
        frozen = frozen_bytes()
        questions = questions_json()
        fake = lambda _reader, _qid, _question: None
        forbidden = (
            b"%PDF-1.7 synthetic",
            b"raw document text",
            b'{"source_map":{}}',
            b'{"sealed_key":"not-used"}',
            b'{"prior_answers":[]}',
        )
        for value in forbidden:
            with self.subTest(value=value[:20]):
                with self.assertRaises(Pilot0EvaluationInputError):
                    evaluate_q1_q15_frozen(value, questions, evaluator=fake)
        with self.assertRaises(Pilot0EvaluationInputError):
            evaluate_q1_q15_frozen(
                frozen.json_bytes,
                questions,
                evaluator=fake,
                expected_sha256="0" * 64,
            )

    def test_question_schema_rejects_prior_answers_and_non_q1_q15(self):
        frozen = frozen_bytes()
        fake = lambda _reader, _qid, _question: None
        contaminated = {"questions": [{"id": "Q1", "question": "Q?", "answer": "prior"}]}
        with self.assertRaises(Pilot0EvaluationInputError):
            evaluate_q1_q15_frozen(
                frozen.json_bytes,
                json.dumps(contaminated).encode(),
                evaluator=fake,
            )
        short = {"questions": [{"id": "Q1", "question": "Q?"}]}
        with self.assertRaises(Pilot0EvaluationInputError):
            evaluate_q1_q15_frozen(
                frozen.json_bytes,
                json.dumps(short).encode(),
                evaluator=fake,
            )

    def test_markdown_q1_q15_is_accepted_and_answer_section_is_rejected(self):
        frozen = frozen_bytes()
        fake = lambda _reader, _qid, _question: None
        answers = evaluate_q1_q15_frozen(
            frozen.json_bytes,
            questions_markdown(),
            evaluator=fake,
        )
        self.assertEqual(len(answers), 15)
        contaminated = questions_markdown() + b"\n## Answers\nPrior response.\n"
        with self.assertRaises(Pilot0EvaluationInputError):
            evaluate_q1_q15_frozen(
                frozen.json_bytes,
                contaminated,
                evaluator=fake,
            )

    def test_file_entry_rejects_original_manuscript_path_and_accepts_only_named_pair(self):
        frozen = frozen_bytes()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reader_path = root / "frozen_reader.json"
            questions_path = root / "Reader_questions_v0.3_candidate.md"
            reader_path.write_bytes(frozen.json_bytes)
            questions_path.write_bytes(questions_markdown())
            self.assertEqual(
                load_frozen_evaluator_inputs(reader_path, questions_path),
                (frozen.json_bytes, questions_markdown()),
            )
            manuscript = root / "original_manuscript.pdf"
            manuscript.write_bytes(b"%PDF-1.7\nsynthetic only")
            with self.assertRaises(Pilot0EvaluationInputError):
                load_frozen_evaluator_inputs(manuscript, questions_path)
            raw = root / "raw_document.txt"
            raw.write_text("synthetic raw text", encoding="utf-8")
            with self.assertRaises(Pilot0EvaluationInputError):
                load_frozen_evaluator_inputs(reader_path, raw)

    def test_thinking_mode_strict_allowlist_and_existing_high_payload_mapping(self):
        for invalid in ("enabled", "HIGH", " high", "xhigh", None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    Pilot0ReaderConfig(deepseek_thinking=invalid)  # type: ignore[arg-type]
        config = Pilot0ReaderConfig(deepseek_thinking="high")
        self.assertEqual(config.to_safe_dict()["model_selection"], "OWNER_SELECTED")
        adapter = LlmReaderAdapter(
            provider="deepseek",
            model="OWNER_SELECTED",
            api_key="",
            deepseek_thinking=config.deepseek_thinking,
        )
        captured = []

        async def fake_chat_complete(call_config, *_args, **_kwargs):
            captured.append(call_config)
            return "synthetic only"

        import asyncio
        import core.llm_router

        with patch.object(core.llm_router, "chat_complete", new=fake_chat_complete):
            asyncio.run(adapter._call_provider("synthetic source text"))
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0].deepseek_thinking, "high")
        body = _deepseek_request_body(
            captured[0],
            [{"role": "user", "content": "synthetic only"}],
            quick_ping=False,
        )
        self.assertEqual(body["thinking"], {"type": "enabled"})
        self.assertEqual(body["reasoning_effort"], "high")

    def test_thinking_mapping_has_no_network_call_and_rejects_non_deepseek_mode(self):
        with self.assertRaises(ValueError):
            LlmReaderAdapter(
                provider="openai",
                model="synthetic-model",
                api_key="",
                deepseek_thinking="high",
            )
        cfg = LlmCallConfig(
            provider="deepseek",
            api_key="",
            model="OWNER_SELECTED",
            deepseek_thinking="max",
        )
        body = _deepseek_request_body(
            cfg,
            [{"role": "user", "content": "offline synthetic"}],
            quick_ping=False,
        )
        self.assertEqual(body["reasoning_effort"], "max")
        with patch("httpx.AsyncClient", side_effect=AssertionError("network denied")):
            self.assertEqual(body["thinking"], {"type": "enabled"})


if __name__ == "__main__":
    unittest.main()
