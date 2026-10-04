from __future__ import annotations

import builtins
from hashlib import sha256
from io import BytesIO
from importlib import metadata
import json
from pathlib import Path
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
    Pilot0EvaluationInputError,
    evaluate_q1_q15_frozen,
    parse_blind_questions,
    validate_frozen_evaluator_input_bytes,
)
from core.pilot0.pdf_input import (
    PARSER_NAME,
    PINNED_PARSER_VERSION,
    Pilot0PdfError,
    _pinned_pdf_reader,
    parse_local_pdf,
)
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
    lines = [
        "# Reader questions v0.3 candidate — только вопросы",
        "",
        "**Статус:** CANDIDATE; локальный оценочный комплект, не канонический и не для публичного распространения.",
        "",
        "Этот файл содержит только вопросы; ответы, локаторы и критерии оценки вынесены в отдельный файл.",
        "",
        "## I. Прямые факты",
        "",
    ]
    lines.extend(f"**{i}.** Synthetic markdown question {i}?" for i in range(1, 16))
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
        installed = metadata.version(PARSER_NAME)
        self.assertEqual(installed, PINNED_PARSER_VERSION)
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
        # Full-suite tests evict core.*; reuse classes captured by this builder.
        artifact_contracts = freeze_reader_output.__globals__
        result_type = artifact_contracts["ReaderResult"]
        capsule_type = (
            result_type.success.__func__.__globals__["KnowledgeCapsule"]
        )
        capsule_contracts = capsule_type.create.__func__.__globals__
        source_type = artifact_contracts["RawSource"]
        mode_type = artifact_contracts["ReaderMode"]
        budget_type = artifact_contracts["ReaderBudget"]
        artifact_error_type = artifact_contracts["Pilot0ArtifactError"]
        text = "Bearer abcdefghijklmnopqrstuv"
        source = source_type("synthetic-secret", text, "sha256:" + "b" * 64)
        span = capsule_contracts["SourceSpan"].from_text(
            document_id=source.document_id,
            raw_text=text,
            start_offset=0,
            end_offset=len(text),
            source_revision=source.source_revision,
        )
        claim = capsule_contracts["CapsuleClaim"].create(
            text=text,
            modality=capsule_contracts["ClaimModality"].OBSERVATION,
            source_spans=(span,),
            extraction_confidence=1.0,
        )
        capsule = capsule_type.create(
            source_document_id=source.document_id,
            essence=text,
            claims=(claim,),
            reader_id=FakeSemanticReader.reader_id,
            reader_version=FakeSemanticReader.reader_version,
            coverage_score=1.0,
            compression_ratio=1.0,
        )
        with self.assertRaises(artifact_error_type):
            freeze_reader_output(
                FakeSemanticReader(),
                source,
                mode=mode_type.FAST,
                budget=budget_type(),
                result=result_type.success(capsule),
            )

    def test_evaluator_requires_trusted_digest_and_blocks_in_process_callback(self):
        frozen = frozen_bytes()
        called = []

        def fake_evaluator(reader_view, question_id, question):
            called.append((reader_view, question_id, question))
            return "Synthetic answer"

        with self.assertRaisesRegex(Pilot0EvaluationInputError, "restricted runtime"):
            evaluate_q1_q15_frozen(
                frozen.json_bytes,
                questions_json(),
                evaluator=fake_evaluator,
                expected_reader_artifact_sha256=frozen.sha256,
            )
        self.assertEqual(called, [])
        with self.assertRaisesRegex(
            Pilot0EvaluationInputError, "trusted expected_reader_artifact_sha256"
        ):
            evaluate_q1_q15_frozen(
                frozen.json_bytes,
                questions_json(),
                evaluator=fake_evaluator,
            )

    def test_stale_trusted_digest_rejects_rehashed_claim_before_parse_or_callback(self):
        frozen = frozen_bytes()
        envelope = json.loads(frozen.json_bytes)
        claim = envelope["payload"]["claims"][0]
        claim["text"] = "Bearer abcdefghijklmnopqrstuv"
        claim["source_spans"][0]["end_offset"] = len(claim["text"])
        envelope["payload_sha256"] = sha256(
            canonical_json_bytes(envelope["payload"])
        ).hexdigest()
        tampered = canonical_json_bytes(envelope)
        called = []

        with self.assertRaisesRegex(Pilot0EvaluationInputError, "trusted digest"):
            evaluate_q1_q15_frozen(
                tampered,
                questions_json(),
                evaluator=lambda *_args: called.append(True),
                expected_reader_artifact_sha256=frozen.sha256,
            )
        self.assertEqual(called, [])

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
                    evaluate_q1_q15_frozen(
                        value,
                        questions,
                        evaluator=fake,
                        expected_reader_artifact_sha256=sha256(value).hexdigest(),
                    )
        with self.assertRaisesRegex(Pilot0EvaluationInputError, "trusted digest"):
            evaluate_q1_q15_frozen(
                frozen.json_bytes,
                questions,
                evaluator=fake,
                expected_reader_artifact_sha256="0" * 64,
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
                expected_reader_artifact_sha256=frozen.sha256,
            )
        short = {"questions": [{"id": "Q1", "question": "Q?"}]}
        with self.assertRaises(Pilot0EvaluationInputError):
            evaluate_q1_q15_frozen(
                frozen.json_bytes,
                json.dumps(short).encode(),
                evaluator=fake,
                expected_reader_artifact_sha256=frozen.sha256,
            )

    def test_bold_numbered_markdown_q1_q15_is_accepted_and_answer_section_rejected(self):
        parsed = parse_blind_questions(questions_markdown())
        self.assertEqual([item[0] for item in parsed], [f"Q{i}" for i in range(1, 16)])
        contaminated = questions_markdown() + b"\n## Answers\nPrior response.\n"
        with self.assertRaises(Pilot0EvaluationInputError):
            parse_blind_questions(contaminated)

    def test_frozen_preamble_and_exact_trusted_digest_are_accepted_without_answers(self):
        frozen = frozen_bytes()
        with patch("core.pilot0.evaluator.parse_blind_questions") as parse_questions:
            with self.assertRaisesRegex(Pilot0EvaluationInputError, "trusted digest"):
                validate_frozen_evaluator_input_bytes(
                    frozen.json_bytes,
                    questions_markdown(),
                    expected_reader_artifact_sha256="0" * 64,
                )
            parse_questions.assert_not_called()

        _reader_view, parsed = validate_frozen_evaluator_input_bytes(
            frozen.json_bytes,
            questions_markdown(),
            expected_reader_artifact_sha256=frozen.sha256,
        )
        self.assertEqual([question_id for question_id, _question in parsed], [f"Q{i}" for i in range(1, 16)])
        self.assertTrue(all(len(item) == 2 for item in parsed))

    def test_markdown_parser_rejects_unknown_preamble_and_answer_like_fields(self):
        unknown_preamble = questions_markdown().replace(
            b"**1.**", b"Unapproved pre-Q1 annotation.\n\n**1.**", 1
        )
        with self.assertRaises(Pilot0EvaluationInputError):
            parse_blind_questions(unknown_preamble)

        for field in (
            b"Answer: synthetic",
            b"A1: synthetic",
            b"Answers",
            b"Prior answers: synthetic",
            b"sealed key: synthetic",
            b"score: 1",
            b"scoring: synthetic",
            b"Key",
            b"Score",
            b"Rubric",
            b"rubric: synthetic",
            b"source_map: {}",
            b"locator: synthetic",
        ):
            with self.subTest(field=field):
                contaminated = questions_markdown().replace(
                    b"Synthetic markdown question 1?",
                    b"Synthetic markdown question 1?\n" + field,
                    1,
                )
                with self.assertRaises(Pilot0EvaluationInputError):
                    parse_blind_questions(contaminated)

    def test_markdown_parser_rejects_inserted_answer_scoring_and_key_sections(self):
        for section in (b"## ANSWERS", b"## SCORING", b"## SEALED KEY"):
            with self.subTest(section=section):
                contaminated = questions_markdown().replace(
                    b"Synthetic markdown question 1?\n",
                    b"Synthetic markdown question 1?\n" + section + b"\n\n",
                    1,
                )
                with self.assertRaises(Pilot0EvaluationInputError):
                    parse_blind_questions(contaminated)

    def test_evaluator_rejects_traversal_symlink_and_alias_paths_before_reading(self):
        import os

        frozen = frozen_bytes()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reader_path = root / "frozen_reader.json"
            reader_path.write_bytes(frozen.json_bytes)
            traversal = root / ".." / "outside" / "frozen_reader.json"
            symlink = root / "reader-link.json"
            symlink.symlink_to(reader_path)
            parent_alias = root / "directory-alias"
            parent_alias.symlink_to(root, target_is_directory=True)
            hardlink_alias = root / "reader-alias.json"
            os.link(reader_path, hardlink_alias)
            candidates = (reader_path, traversal, symlink, parent_alias / reader_path.name, hardlink_alias)
            for candidate in candidates:
                with self.subTest(path_kind=str(candidate)):
                    with self.assertRaisesRegex(Pilot0EvaluationInputError, "already-loaded bytes"):
                        validate_frozen_evaluator_input_bytes(
                            candidate,
                            questions_markdown(),
                            expected_reader_artifact_sha256=frozen.sha256,
                        )

    def test_thinking_mode_strict_allowlist_and_existing_high_payload_mapping(self):
        for invalid in ("enabled", "HIGH", " high", "xhigh", None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    Pilot0ReaderConfig(deepseek_thinking=invalid)  # type: ignore[arg-type]
        config = Pilot0ReaderConfig(deepseek_thinking="high")
        self.assertEqual(config.to_safe_dict()["model_selection"], "OWNER_SELECTED")
        for mode in ("off", "high", "max"):
            cfg = LlmCallConfig(
                provider="deepseek",
                api_key="",
                model="OWNER_SELECTED",
                deepseek_thinking=mode,
            )
            body = _deepseek_request_body(
                cfg,
                [{"role": "user", "content": "offline synthetic"}],
                quick_ping=False,
            )
            if mode == "off":
                self.assertEqual(body["thinking"], {"type": "disabled"})
            else:
                self.assertEqual(body["thinking"], {"type": "enabled"})
                self.assertEqual(body["reasoning_effort"], mode)

    def test_thinking_mapping_has_no_network_call_and_rejects_non_deepseek_mode(self):
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
            invalid = LlmCallConfig(
                provider="deepseek",
                api_key="",
                model="synthetic-model",
                deepseek_thinking="enabled",
            )
            with self.assertRaises(ValueError):
                _deepseek_request_body(
                    invalid,
                    [{"role": "user", "content": "offline synthetic"}],
                    quick_ping=False,
                )


if __name__ == "__main__":
    unittest.main()
