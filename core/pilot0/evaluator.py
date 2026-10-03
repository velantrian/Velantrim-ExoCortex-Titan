"""Offline-only Q1–Q15 evaluation interface for frozen Reader JSON.

No model client, HTTP client, document parser, Reader, source path, or answer
store is implemented here. Tests may inject a fake local evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Protocol

from core.pilot0.artifact import Pilot0ArtifactError, parse_frozen_reader_json

INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
MAX_READER_JSON_BYTES = 10_000_000
MAX_QUESTIONS_JSON_BYTES = 1_000_000
MAX_QUESTION_CHARS = 2_000


class Pilot0EvaluationInputError(ValueError):
    """Evaluator input is not exactly a frozen Reader JSON and blind question set."""


class OfflineEvaluator(Protocol):
    """Injected local evaluator; receives no filesystem paths or source document."""

    def __call__(
        self,
        frozen_reader: Mapping[str, Any],
        question_id: str,
        question: str,
    ) -> str | None:
        """Return an evidence-grounded answer or None when evidence is insufficient."""


@dataclass(frozen=True, slots=True)
class EvaluationAnswer:
    question_id: str
    answer: str


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Pilot0EvaluationInputError("Duplicate JSON key in blind questions")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise Pilot0EvaluationInputError(f"Invalid JSON constant in blind questions: {value}")


def _validate_question_items(items: Any) -> tuple[tuple[str, str], ...]:
    if not isinstance(items, list) or len(items) != 15:
        raise Pilot0EvaluationInputError("Blind question file must contain exactly Q1–Q15")
    parsed: list[tuple[str, str]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or set(item) != {"id", "question"}:
            raise Pilot0EvaluationInputError("Each blind question must contain only id and question")
        expected_id = f"Q{index}"
        question = item["question"]
        if item["id"] != expected_id:
            raise Pilot0EvaluationInputError("Blind question IDs must be ordered Q1 through Q15")
        if (
            not isinstance(question, str)
            or not question.strip()
            or len(question) > MAX_QUESTION_CHARS
            or "\x00" in question
        ):
            raise Pilot0EvaluationInputError(f"{expected_id} is not a valid bounded question")
        parsed.append((expected_id, question.strip()))
    return tuple(parsed)


def _parse_markdown_questions(markdown: str) -> tuple[tuple[str, str], ...]:
    marker = re.compile(
        r"^\s*(?:#{1,6}\s*)?(?:[-*+]\s*)?(?:\*\*)?Q(?P<number>1[0-5]|[1-9])"
        r"(?:\*\*)?(?:[.:)\s—-]+)(?P<body>.*)$",
        re.IGNORECASE,
    )
    forbidden_answer_heading = re.compile(
        r"^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:A\d{1,2}|answers?|responses?|prior answers?)\b",
        re.IGNORECASE,
    )
    items: list[dict[str, str]] = []
    current_id: str | None = None
    current_lines: list[str] = []

    def finish_current() -> None:
        nonlocal current_id, current_lines
        if current_id is not None:
            body = " ".join(line.strip() for line in current_lines if line.strip()).strip()
            items.append({"id": current_id, "question": body})
        current_id = None
        current_lines = []

    for line in markdown.lstrip("\ufeff").splitlines():
        if not line.strip():
            continue
        match = marker.match(line)
        if match:
            finish_current()
            current_id = f"Q{int(match.group('number'))}"
            current_lines = [match.group("body").strip()]
            continue
        if forbidden_answer_heading.match(line):
            raise Pilot0EvaluationInputError("Answer/prior-answer sections are forbidden")
        if current_id is None:
            if line.lstrip().startswith("#"):
                continue
            raise Pilot0EvaluationInputError("Unexpected content outside Q1–Q15 in blind questions")
        current_lines.append(line)
    finish_current()
    return _validate_question_items(items)


def parse_blind_questions(blind_questions_json: bytes) -> tuple[tuple[str, str], ...]:
    """Accept strict JSON or Markdown Q1–Q15 only; reject answer/source fields."""

    if not isinstance(blind_questions_json, bytes):
        raise Pilot0EvaluationInputError("Blind questions must be supplied as UTF-8 bytes")
    if len(blind_questions_json) > MAX_QUESTIONS_JSON_BYTES:
        raise Pilot0EvaluationInputError("Blind questions exceed the size bound")
    try:
        decoded = blind_questions_json.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Pilot0EvaluationInputError("Blind questions are not valid UTF-8") from exc
    if decoded.lstrip("\ufeff \t\r\n").startswith("{"):
        try:
            value = json.loads(
                decoded,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_constant,
            )
        except json.JSONDecodeError as exc:
            raise Pilot0EvaluationInputError("Blind questions JSON is invalid") from exc
        if not isinstance(value, dict) or set(value) != {"questions"}:
            raise Pilot0EvaluationInputError("Blind question file has unknown or missing fields")
        return _validate_question_items(value["questions"])
    return _parse_markdown_questions(decoded)


def _validate_input_path(path: str | Path, *, role: str) -> Path:
    candidate = Path(path)
    allowed_suffixes = {".json"} if role == "reader" else {".json", ".md"}
    if candidate.suffix.lower() not in allowed_suffixes:
        raise Pilot0EvaluationInputError("Evaluator accepts frozen Reader JSON and blind questions only")
    if candidate.is_symlink():
        raise Pilot0EvaluationInputError("Symlink evaluator inputs are refused")
    name = candidate.as_posix().lower().replace("_", "-")
    forbidden_markers = (
        "manuscript",
        "source-map",
        "sourcemap",
        "sealed-key",
        "sealedkey",
        "prior-answer",
        "previous-answer",
        "raw-document",
        "raw-source",
    )
    if any(marker in name for marker in forbidden_markers):
        raise Pilot0EvaluationInputError("Forbidden source, key, map, or prior-answer path")
    if role == "reader" and not ("frozen" in name and "reader" in name):
        raise Pilot0EvaluationInputError("Reader input must be named as a frozen Reader JSON artifact")
    if role == "questions" and "question" not in name:
        raise Pilot0EvaluationInputError("Question input must be named as a questions file")
    try:
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file():
            raise Pilot0EvaluationInputError("Evaluator input must be a regular local file")
        limit = MAX_READER_JSON_BYTES if role == "reader" else MAX_QUESTIONS_JSON_BYTES
        if resolved.stat().st_size <= 0 or resolved.stat().st_size > limit:
            raise Pilot0EvaluationInputError("Evaluator input is outside the configured size bound")
    except OSError as exc:
        raise Pilot0EvaluationInputError("Evaluator input is unavailable") from exc
    return resolved


def load_frozen_evaluator_inputs(
    frozen_reader_path: str | Path,
    blind_questions_path: str | Path,
) -> tuple[bytes, bytes]:
    """Read the two permitted local files; reject source, PDF, map, key, and answers."""

    reader_path = _validate_input_path(frozen_reader_path, role="reader")
    questions_path = _validate_input_path(blind_questions_path, role="questions")
    if reader_path == questions_path:
        raise Pilot0EvaluationInputError("Reader and blind questions must be separate files")
    reader_bytes = reader_path.read_bytes()
    questions_bytes = questions_path.read_bytes()
    try:
        parse_frozen_reader_json(reader_bytes)
    except Pilot0ArtifactError as exc:
        raise Pilot0EvaluationInputError("Reader file is not a verified frozen Reader artifact") from exc
    parse_blind_questions(questions_bytes)
    return reader_bytes, questions_bytes


def evaluate_q1_q15_frozen(
    frozen_reader_json: bytes,
    blind_questions_json: bytes,
    *,
    evaluator: OfflineEvaluator | Callable[[Mapping[str, Any], str, str], str | None],
    expected_sha256: str | None = None,
) -> tuple[EvaluationAnswer, ...]:
    """Run an injected local evaluator with only frozen Reader data and Q1–Q15.

    A ``None`` or blank result is rendered as ``INSUFFICIENT_EVIDENCE``. This
    function does not select or provide an evaluator implementation.
    """

    if not callable(evaluator):
        raise Pilot0EvaluationInputError("An explicit local evaluator implementation is required")
    if not isinstance(frozen_reader_json, bytes):
        raise Pilot0EvaluationInputError("Evaluator accepts frozen Reader JSON bytes only")
    if len(frozen_reader_json) > MAX_READER_JSON_BYTES:
        raise Pilot0EvaluationInputError("Frozen Reader JSON exceeds the size bound")
    try:
        reader_view = parse_frozen_reader_json(
            frozen_reader_json,
            expected_sha256=expected_sha256,
        )
    except Pilot0ArtifactError as exc:
        raise Pilot0EvaluationInputError("Reader input is not verified frozen JSON") from exc
    questions = parse_blind_questions(blind_questions_json)

    answers: list[EvaluationAnswer] = []
    for question_id, question in questions:
        answer = evaluator(reader_view, question_id, question)
        if answer is not None and not isinstance(answer, str):
            raise Pilot0EvaluationInputError("Evaluator must return text or None")
        normalized = answer.strip() if isinstance(answer, str) else ""
        answers.append(
            EvaluationAnswer(
                question_id=question_id,
                answer=normalized or INSUFFICIENT_EVIDENCE,
            )
        )
    return tuple(answers)


__all__ = [
    "INSUFFICIENT_EVIDENCE",
    "EvaluationAnswer",
    "OfflineEvaluator",
    "Pilot0EvaluationInputError",
    "evaluate_q1_q15_frozen",
    "load_frozen_evaluator_inputs",
    "parse_blind_questions",
]
