"""Single-parser local PDF input for the experimental Pilot-0 path.

The parser is deliberately pinned to the version already present in the local
implementation environment. There is no parser cascade, fallback, installer,
download, or remote input path.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib import metadata
from io import BytesIO
from pathlib import Path

PARSER_NAME = "pypdf"
PINNED_PARSER_VERSION = "6.18.1"
MAX_PDF_BYTES = 32_000_000
MAX_PDF_PAGES = 500
MAX_EXTRACTED_CHARS = 2_000_000


class Pilot0PdfError(ValueError):
    """Local PDF input could not be accepted under the pinned parser contract."""


@dataclass(frozen=True, slots=True)
class ParsedLocalPdf:
    """Transient local parse result; source text is never part of a frozen artifact."""

    text: str
    source_revision: str
    parser_name: str
    parser_version: str
    page_count: int


def _pinned_pdf_reader():
    """Load exactly pypdf at the pinned version; missing or mismatched fails closed."""

    try:
        installed_version = metadata.version(PARSER_NAME)
    except metadata.PackageNotFoundError as exc:
        raise Pilot0PdfError("Pinned local PDF parser is unavailable") from exc
    if installed_version != PINNED_PARSER_VERSION:
        raise Pilot0PdfError(
            f"Pinned local PDF parser version mismatch: expected {PINNED_PARSER_VERSION}"
        )
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise Pilot0PdfError("Pinned local PDF parser is unavailable") from exc
    return PdfReader


def parse_local_pdf(path: str | Path) -> ParsedLocalPdf:
    """Parse a bounded, regular local PDF using only the pinned pypdf version."""

    pdf_path = Path(path)
    if pdf_path.suffix.lower() != ".pdf":
        raise Pilot0PdfError("Pilot-0 parser accepts only a local .pdf path")
    if pdf_path.is_symlink():
        raise Pilot0PdfError("Symlink PDF inputs are not accepted")
    try:
        stat_result = pdf_path.stat()
    except OSError as exc:
        raise Pilot0PdfError("Local PDF input is unavailable") from exc
    if not pdf_path.is_file():
        raise Pilot0PdfError("Local PDF input must be a regular file")
    if stat_result.st_size <= 0 or stat_result.st_size > MAX_PDF_BYTES:
        raise Pilot0PdfError("Local PDF size is outside the configured bound")
    try:
        data = pdf_path.read_bytes()
    except OSError as exc:
        raise Pilot0PdfError("Local PDF input could not be read") from exc
    if len(data) != stat_result.st_size or not data.startswith(b"%PDF-"):
        raise Pilot0PdfError("Local input is not a stable PDF byte stream")

    PdfReader = _pinned_pdf_reader()
    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise Pilot0PdfError("Encrypted PDFs are not accepted")
        page_count = len(reader.pages)
        if page_count <= 0 or page_count > MAX_PDF_PAGES:
            raise Pilot0PdfError("PDF page count is outside the configured bound")
        extracted: list[str] = []
        total_chars = 0
        for page in reader.pages:
            page_text = page.extract_text() or ""
            total_chars += len(page_text)
            if total_chars > MAX_EXTRACTED_CHARS:
                raise Pilot0PdfError("Extracted text exceeds the configured bound")
            extracted.append(page_text)
    except Pilot0PdfError:
        raise
    except Exception as exc:
        raise Pilot0PdfError("Pinned parser rejected the local PDF") from exc

    return ParsedLocalPdf(
        text="\n\n".join(extracted),
        source_revision=f"sha256:{sha256(data).hexdigest()}",
        parser_name=PARSER_NAME,
        parser_version=PINNED_PARSER_VERSION,
        page_count=page_count,
    )


__all__ = [
    "MAX_EXTRACTED_CHARS",
    "MAX_PDF_BYTES",
    "MAX_PDF_PAGES",
    "PARSER_NAME",
    "PINNED_PARSER_VERSION",
    "ParsedLocalPdf",
    "Pilot0PdfError",
    "parse_local_pdf",
]
