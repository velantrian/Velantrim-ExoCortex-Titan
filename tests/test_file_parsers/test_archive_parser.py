"""
tests/test_file_parsers/test_archive_parser.py
================================================
H4 regression (Claude audit 2026-07-28): ArchiveParser._extract_rar() must
cap real streamed bytes, not the archive's own (attacker-controlled)
declared header size.

Before the fix, the size guard only summed `RarInfo.file_size` from the RAR
header and then called `rf.extract()` unbounded — a crafted archive that
under-reports its size in the header bypassed the guard entirely and could
decompress far past MAX_EXTRACTED_SIZE, the same zip-bomb class this module
already disables .7z support for.

No `unrar`/`bsdtar`/`7z` backend capable of reading real .rar archives is
assumed to be installed, so these tests fake `rarfile.RarFile` itself at the
interface boundary (`namelist`/`getinfo`/`open`) rather than depend on a real
archive binary. This tests the guard logic in `_extract_rar` directly and
deterministically. All tests skip cleanly if `rarfile` isn't installed
(RARFILE_AVAILABLE is optional at runtime, same as py7zr).
"""
from __future__ import annotations

import io
import os
import tempfile

import pytest

rarfile = pytest.importorskip("rarfile")

from core.file_parsers.archive_parser import ArchiveParser  # noqa: E402
from core.file_parsers.base import ParseResult  # noqa: E402


class _FakeRarInfo:
    def __init__(self, filename: str, file_size: int, is_directory: bool = False):
        self.filename = filename
        self.file_size = file_size
        self._is_directory = is_directory

    def isdir(self) -> bool:
        return self._is_directory


def _fake_rar_file_cls(members: dict):
    """members: {name: (declared_file_size, real_bytes)}.

    Returns a class mimicking rarfile.RarFile's read interface so
    _extract_rar's guard logic can be tested without a real .rar archive
    or an installed unrar-compatible backend.
    """

    class _FakeRarFile:
        def __init__(self, path: str):
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def namelist(self) -> list:
            return list(members.keys())

        def getinfo(self, name: str) -> _FakeRarInfo:
            declared_size, _ = members[name]
            return _FakeRarInfo(name, declared_size)

        def open(self, name: str, mode: str = "r"):
            _, real_bytes = members[name]
            return io.BytesIO(real_bytes)

    return _FakeRarFile


@pytest.fixture
def dummy_rar(tmp_path):
    """A placeholder .rar path — its bytes are never actually read, since
    rarfile.RarFile itself is faked; _check_file() only needs it to exist.
    """
    p = tmp_path / "archive.rar"
    p.write_bytes(b"placeholder - never actually parsed as RAR")
    return str(p)


class TestExtractRarSizeGuard:
    def test_declared_size_lies_real_bytes_are_capped(self, dummy_rar, monkeypatch):
        """The core H4 regression: a member whose header declares a tiny
        size but streams far more real bytes must still be capped."""
        parser = ArchiveParser()
        parser.MAX_EXTRACTED_SIZE = 1024  # 1 KB cap for the test

        real_payload = b"X" * (10 * 1024)  # 10 KB — 10x past the cap
        members = {"payload.bin": (10, real_payload)}  # header lies: declares 10 bytes
        monkeypatch.setattr(rarfile, "RarFile", _fake_rar_file_cls(members))

        result = ParseResult(file_path=dummy_rar, file_type="archive")
        with tempfile.TemporaryDirectory() as tmpdir:
            files = parser._extract_rar(dummy_rar, tmpdir, result)
            # Capped mid-stream: nothing survives, partial file removed.
            assert files == []
            assert not os.path.exists(os.path.join(tmpdir, "payload.bin"))

        assert "max_extracted_size_reached" in result.warnings

    def test_declared_size_alone_still_rejects_early(self, dummy_rar, monkeypatch):
        """Cheap early-reject path (declared size already over cap) must
        still work without needing to stream anything."""
        parser = ArchiveParser()
        parser.MAX_EXTRACTED_SIZE = 1024

        content = b"Y" * 2048
        members = {"big.bin": (2048, content)}  # declared size alone > cap
        monkeypatch.setattr(rarfile, "RarFile", _fake_rar_file_cls(members))

        result = ParseResult(file_path=dummy_rar, file_type="archive")
        with tempfile.TemporaryDirectory() as tmpdir:
            files = parser._extract_rar(dummy_rar, tmpdir, result)
            assert files == []

        assert "rar_max_extracted_size_reached" in result.warnings

    def test_normal_extraction_still_succeeds(self, dummy_rar, monkeypatch):
        """The fix must not break legitimate small archives."""
        parser = ArchiveParser()
        content = b"hello from inside the rar"
        members = {"note.txt": (len(content), content)}
        monkeypatch.setattr(rarfile, "RarFile", _fake_rar_file_cls(members))

        result = ParseResult(file_path=dummy_rar, file_type="archive")
        with tempfile.TemporaryDirectory() as tmpdir:
            files = parser._extract_rar(dummy_rar, tmpdir, result)
            assert len(files) == 1
            with open(files[0], "rb") as f:
                assert f.read() == content

        assert "max_extracted_size_reached" not in result.warnings
        assert "rar_max_extracted_size_reached" not in result.warnings

    def test_directory_entries_are_skipped(self, dummy_rar, monkeypatch):
        parser = ArchiveParser()
        members = {
            "docs/": (0, b""),
            "docs/readme.txt": (5, b"hello"),
        }
        fake_cls = _fake_rar_file_cls(members)

        # Mark the directory entry as such (real rarfile.RarInfo.isdir()
        # reflects the archive's own directory flag).
        orig_getinfo = fake_cls.getinfo

        def getinfo(self, name):
            info = orig_getinfo(self, name)
            if name.endswith("/"):
                info._is_directory = True
            return info

        fake_cls.getinfo = getinfo
        monkeypatch.setattr(rarfile, "RarFile", fake_cls)

        result = ParseResult(file_path=dummy_rar, file_type="archive")
        with tempfile.TemporaryDirectory() as tmpdir:
            files = parser._extract_rar(dummy_rar, tmpdir, result)
            assert len(files) == 1
            assert files[0].endswith("readme.txt")


class TestExtractRarPathTraversal:
    def test_dotdot_member_is_blocked(self, dummy_rar, monkeypatch):
        parser = ArchiveParser()
        members = {"../../etc/evil.txt": (5, b"pwned")}
        monkeypatch.setattr(rarfile, "RarFile", _fake_rar_file_cls(members))

        result = ParseResult(file_path=dummy_rar, file_type="archive")
        with tempfile.TemporaryDirectory() as tmpdir:
            files = parser._extract_rar(dummy_rar, tmpdir, result)
            # A literal ".." segment is rejected by the normpath check before
            # the realpath-based guard even runs, so this is a silent skip
            # (no rar_path_traversal_blocked warning) — not extracted either way.
            assert files == []

    def test_absolute_path_member_is_blocked(self, dummy_rar, monkeypatch):
        parser = ArchiveParser()
        members = {"/etc/passwd": (5, b"pwned")}
        monkeypatch.setattr(rarfile, "RarFile", _fake_rar_file_cls(members))

        result = ParseResult(file_path=dummy_rar, file_type="archive")
        with tempfile.TemporaryDirectory() as tmpdir:
            files = parser._extract_rar(dummy_rar, tmpdir, result)
            assert files == []


class TestArchiveParserRarWiring:
    def test_parse_dispatches_rar_extension_to_rarfile(self, dummy_rar, monkeypatch):
        """End-to-end: .rar dispatches through the real parse() entry point,
        not just the unit-tested _extract_rar() directly."""
        content = b"integration test content"
        members = {"note.txt": (len(content), content)}
        monkeypatch.setattr(rarfile, "RarFile", _fake_rar_file_cls(members))

        parser = ArchiveParser()
        result = parser.parse(dummy_rar)

        assert result.error is None
        assert result.extraction_method == "rarfile"
        assert result.structured_data["file_count"] == 1
