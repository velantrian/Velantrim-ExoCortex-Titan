"""An installed package is not an implemented adapter capability."""
import pytest


def test_unimplemented_mineru_does_not_read_pdf(monkeypatch):
    from core.file_parsers.pdf_parser import PDFParser, MINERU_AVAILABLE
    assert MINERU_AVAILABLE is False
    monkeypatch.setattr("builtins.open", lambda *a, **k: pytest.fail("placeholder read the whole PDF"))
    with pytest.raises(NotImplementedError, match="not implemented"):
        PDFParser()._parse_mineru("never-read.pdf")
