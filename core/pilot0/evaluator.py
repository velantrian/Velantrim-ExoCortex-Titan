"""Fail-closed Q1–Q15 input validation for frozen Reader JSON.

This module does not read filesystem paths and does not execute evaluator
callbacks. Inputs must already be loaded bytes; exact Reader-envelope integrity
is checked before either serialized input is parsed. A future execution path
requires a separately verified restricted runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Callable, Mapping, Protocol

from core.pilot0.artifact import Pilot0ArtifactError, parse_frozen_reader_json

INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
MAX_READER_JSON_BYTES = 10_000_000
MAX_QUESTIONS_JSON_BYTES = 1_000_000
MAX_QUESTION_CHARS = 2_000
_FROZEN_MARKDOWN_PREAMBLE = (
    "# Reader questions v0.3 candidate — только вопросы",
    "**Статус:** CANDIDATE; локальный оценочный комплект, не канонический и не для публичного распространения.",
    "Этот файл содержит только вопросы; ответы, локаторы и критерии оценки вынесены в отдельный файл.",
    "## I. Прямые факты",
)
_FORBIDDEN_MARKDOWN_SECTION = re.compile(
    r"^\s*#{1,6}\s*(?:\*\*)?(?:ANSWERS?|PRIOR\s+ANSWERS?|SEALED[\s_-]+KEYS?|"
    r"KEYS?|SCORES?|SCORING|RUBRICS?|RESPONSES?|SOURCE[\s_-]*MAPS?|LOCATORS?)\b",
    re.IGNORECASE,
)
_FORBIDDEN_MARKDOWN_FIELD = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:\*\*)?(?:(?:Q(?:1[0-5]|[1-9])\s+)?"
    r"(?:ANSWERS?|RESPONSES?)|PRIOR[\s_-]+ANSWERS?|A\d{1,2}|"
    r"SEALED[\s_-]+KEYS?|KEYS?|SCORES?|SCORING|RUBRICS?|"
    r"SOURCE[\s_-]*MAPS?|LOCATORS?)(?:\*\*)?\s*[:=]",
    re.IGNORECASE,
)
_FORBIDDEN_MARKDOWN_LABEL = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:\*\*)?(?:ANSWERS?|PRIOR[\s_-]+ANSWERS?|A\d{1,2}|"
    r"SEALED[\s_-]+KEYS?|KEYS?|SCORES?|SCORING|RUBRICS?|"
    r"SOURCE[\s_-]*MAPS?|LOCATORS?)(?:\*\*)?\s*$",
    re.IGNORECASE,
)
_FORBIDDEN_MARKDOWN_PAYLOAD = re.compile(
    r"[\"'`](?:ANSWERS?|RESPONSES?|PRIOR[_ -]+ANSWERS?|SEALED[_ -]+KEYS?|"
    r"KEYS?|SCORES?|SCORING|RUBRICS?|SOURCE[_ -]*MAPS?|LOCATORS?)[\"'`]\s*:",
    re.IGNORECASE,
)
_MARKDOWN_HEADING = re.compile(r"^\s*#{1,6}\s+\S")


class Pilot0EvaluationInputError(ValueError):
    """Evaluator input is not exactly a frozen Reader JSON and blind question set."""


class OfflineEvaluator(Protocol):
    """Callable contract placeholder; in-process callables are not a sandbox.

    The public entry point deliberately does not invoke this protocol until a
    separately verified restricted runtime is available.
    """

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
        r"^\s*(?:#{1,6}\s*)?(?:[-*+]\s*)?"
        r"(?:\*\*(?P<bold_number>1[0-5]|[1-9])\.\*\*|"
        r"(?:\*\*)?Q(?P<q_number>1[0-5]|[1-9])(?:[.:)\s—-]+)(?:\*\*)?)"
        r"\s*(?P<body>.*)$",
        re.IGNORECASE,
    )
    items: list[dict[str, str]] = []
    current_id: str | None = None
    current_lines: list[str] = []
    preamble_index = 0

    def reject_forbidden_line(line: str) -> None:
        if (
            _FORBIDDEN_MARKDOWN_SECTION.match(line)
            or _FORBIDDEN_MARKDOWN_FIELD.match(line)
            or _FORBIDDEN_MARKDOWN_LABEL.match(line)
            or _FORBIDDEN_MARKDOWN_PAYLOAD.search(line)
        ):
            raise Pilot0EvaluationInputError(
                "Answer/key/scoring/rubric/source sections or fields are forbidden"
            )

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
            if current_id is None and not items and preamble_index != len(_FROZEN_MARKDOWN_PREAMBLE):
                raise Pilot0EvaluationInputError("Frozen question preamble is incomplete")
            finish_current()
            number = match.group("bold_number") or match.group("q_number")
            current_id = f"Q{int(number)}"
            body = match.group("body").strip()
            reject_forbidden_line(body)
            current_lines = [body]
            continue
        reject_forbidden_line(line)
        if current_id is None:
            expected = (
                _FROZEN_MARKDOWN_PREAMBLE[preamble_index]
                if preamble_index < len(_FROZEN_MARKDOWN_PREAMBLE)
                else None
            )
            if line.strip() != expected:
                raise Pilot0EvaluationInputError(
                    "Unexpected content outside the frozen question preamble and Q1–Q15"
                )
            preamble_index += 1
            continue
        if _MARKDOWN_HEADING.match(line):
            raise Pilot0EvaluationInputError("Extra Markdown sections are forbidden")
        current_lines.append(line)
    finish_current()
    return _validate_question_items(items)


def parse_blind_questions(blind_questions_bytes: bytes) -> tuple[tuple[str, str], ...]:
    """Accept strict JSON or supported Markdown markers; reject answer/source fields."""

    if not isinstance(blind_questions_bytes, bytes):
        raise Pilot0EvaluationInputError("Blind questions must be supplied as already-loaded UTF-8 bytes")
    if len(blind_questions_bytes) > MAX_QUESTIONS_JSON_BYTES:
        raise Pilot0EvaluationInputError("Blind questions exceed the size bound")
    try:
        decoded = blind_questions_bytes.decode("utf-8")
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


def validate_frozen_evaluator_input_bytes(
    frozen_reader_json: bytes,
    blind_questions_bytes: bytes,
    *,
    expected_reader_artifact_sha256: str | None = None,
) -> tuple[Mapping[str, Any], tuple[tuple[str, str], ...]]:
    """Validate already-loaded bytes; verify the trusted Reader digest before parsing.

    Filesystem paths and path-derived aliases are intentionally unsupported.
    The caller must supply the exact trusted digest for the serialized Reader
    envelope, not merely its internally recomputable payload digest.
    """

    if not isinstance(frozen_reader_json, bytes):
        raise Pilot0EvaluationInputError("Frozen Reader input must be supplied as already-loaded bytes")
    if not isinstance(blind_questions_bytes, bytes):
        raise Pilot0EvaluationInputError("Blind questions must be supplied as already-loaded bytes")
    if len(frozen_reader_json) > MAX_READER_JSON_BYTES:
        raise Pilot0EvaluationInputError("Frozen Reader JSON exceeds the size bound")
    if len(blind_questions_bytes) > MAX_QUESTIONS_JSON_BYTES:
        raise Pilot0EvaluationInputError("Blind questions exceed the size bound")
    if not isinstance(expected_reader_artifact_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", expected_reader_artifact_sha256
    ):
        raise Pilot0EvaluationInputError("A trusted expected_reader_artifact_sha256 is required")
    if sha256(frozen_reader_json).hexdigest() != expected_reader_artifact_sha256:
        raise Pilot0EvaluationInputError("Exact frozen Reader bytes do not match the trusted digest")

    try:
        reader_view = parse_frozen_reader_json(
            frozen_reader_json,
            expected_sha256=expected_reader_artifact_sha256,
        )
    except Pilot0ArtifactError as exc:
        raise Pilot0EvaluationInputError("Reader input is not verified frozen JSON") from exc
    questions = parse_blind_questions(blind_questions_bytes)
    return reader_view, questions


def evaluate_q1_q15_frozen(
    frozen_reader_json: bytes,
    blind_questions_bytes: bytes,
    *,
    evaluator: OfflineEvaluator | Callable[[Mapping[str, Any], str, str], str | None],
    expected_reader_artifact_sha256: str | None = None,
) -> tuple[EvaluationAnswer, ...]:
    """Fail closed: validate exact bytes, then block execution pending restricted runtime.

    An arbitrary Python callback is not a filesystem/network sandbox. This
    function therefore never invokes ``evaluator``; execution remains blocked
    until a separately verified restricted runtime is integrated.
    """

    validate_frozen_evaluator_input_bytes(
        frozen_reader_json,
        blind_questions_bytes,
        expected_reader_artifact_sha256=expected_reader_artifact_sha256,
    )
    if not callable(evaluator):
        raise Pilot0EvaluationInputError("An explicit evaluator interface is required")
    raise Pilot0EvaluationInputError(
        "Evaluator execution is blocked until a separately verified restricted runtime is available"
    )


__all__ = [
    "INSUFFICIENT_EVIDENCE",
    "EvaluationAnswer",
    "OfflineEvaluator",
    "Pilot0EvaluationInputError",
    "evaluate_q1_q15_frozen",
    "parse_blind_questions",
    "validate_frozen_evaluator_input_bytes",
]
