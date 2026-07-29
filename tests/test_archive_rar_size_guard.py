"""Audit H4: RAR-guard должен считать реальные байты, а не заголовок.

Прежняя реализация несла комментарий «добавить MAX_EXTRACTED_SIZE guard (как в
_extract_zip/_extract_tar)», но паритета не было: она суммировала
`info.file_size` из заголовка RAR — данные, которые контролирует атакующий — и
затем звала `rf.extract()`, пишущий файл целиком без предела. Архив с заниженным
заявленным размером обходил guard.

`rarfile` — опциональная зависимость и в этом окружении не установлена, поэтому
тесты подставляют минимальный стаб в `sys.modules`. Это не обход проверки: цель —
поведение `_extract_rar`, а не рабочий unrar. Стаб намеренно лжёт в
`file_size` — именно так выглядит атака.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from core.file_parsers.archive_parser import ArchiveParser
from core.file_parsers.base import ParseResult


class _FakeStream:
    """Поток, отдающий `real_size` байт независимо от заявленного размера."""

    def __init__(self, real_size: int) -> None:
        self._left = real_size

    def read(self, n: int = -1) -> bytes:
        if self._left <= 0:
            return b""
        take = self._left if n < 0 else min(n, self._left)
        self._left -= take
        return b"X" * take

    def __enter__(self) -> _FakeStream:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


class _FakeInfo:
    def __init__(self, file_size: int) -> None:
        self.file_size = file_size


def _install_fake_rarfile(
    monkeypatch: pytest.MonkeyPatch,
    members: dict[str, tuple[int, int]],
) -> dict[str, list[str]]:
    """Подставить стаб `rarfile`.

    members: имя → (заявленный размер, реальный размер потока).
    Возвращает журнал вызовов, чтобы проверить, что extract() не используется.
    """
    calls: dict[str, list[str]] = {"open": [], "extract": []}

    class _FakeRarFile:
        def __init__(self, path: str) -> None:
            self._path = path

        def __enter__(self) -> _FakeRarFile:
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

        def namelist(self) -> list[str]:
            return list(members)

        def getinfo(self, name: str) -> _FakeInfo:
            return _FakeInfo(members[name][0])

        def open(self, name: str, *a: object, **k: object) -> _FakeStream:
            calls["open"].append(name)
            return _FakeStream(members[name][1])

        def extract(self, name: str, path: str) -> None:  # pragma: no cover
            calls["extract"].append(name)
            raise AssertionError(
                "rf.extract() пишет файл целиком без предела — "
                "распаковка обязана идти потоком через rf.open()"
            )

    module = types.ModuleType("rarfile")
    module.RarFile = _FakeRarFile  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "rarfile", module)
    return calls


def _parser(cap: int) -> ArchiveParser:
    parser = ArchiveParser()
    parser.MAX_EXTRACTED_SIZE = cap
    return parser


# ── ядро H4: заявленный размер лжёт ─────────────────────────────────────────

def test_forged_header_does_not_bypass_the_cap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Заявлено 4 байта, реально 4096 — при потолке 512 обрыв обязателен."""
    calls = _install_fake_rarfile(monkeypatch, {"payload.bin": (4, 4096)})
    parser = _parser(512)
    result = ParseResult(file_path=str(tmp_path / "bomb.rar"), file_type="archive")
    out = tmp_path / "out"
    out.mkdir()

    files = parser._extract_rar(str(tmp_path / "bomb.rar"), str(out), result)

    assert "max_extracted_size_reached" in result.warnings
    assert files == []
    on_disk = [p for p in out.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in on_disk)
    assert total <= parser.MAX_EXTRACTED_SIZE, (
        f"на диск записано {total} байт при потолке {parser.MAX_EXTRACTED_SIZE}"
    )
    # Обрыв должен произойти в потоке, а не после полной распаковки.
    assert calls["open"] == ["payload.bin"]
    assert calls["extract"] == []


def test_partial_file_is_removed_on_cap_breach(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Обрыв не должен оставлять недописанный payload."""
    _install_fake_rarfile(monkeypatch, {"payload.bin": (4, 4096)})
    parser = _parser(512)
    result = ParseResult(file_path="x.rar", file_type="archive")
    out = tmp_path / "out"
    out.mkdir()

    parser._extract_rar("x.rar", str(out), result)

    assert list(out.rglob("*")) == [], "частичный файл остался на диске"


def test_extract_is_never_used(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """rf.extract() пишет целиком — путь обязан идти через rf.open()."""
    calls = _install_fake_rarfile(monkeypatch, {"a.txt": (4, 4)})
    out = tmp_path / "out"
    out.mkdir()
    result = ParseResult(file_path="x.rar", file_type="archive")

    _parser(1024)._extract_rar("x.rar", str(out), result)

    assert calls["open"] == ["a.txt"]
    assert calls["extract"] == []


def test_cumulative_size_across_members_is_capped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Потолок общий на архив, а не на файл.

    Заявленные размеры здесь честные, поэтому третий член отсекается дешёвым
    early-reject (200 + 100 > 250) — до открытия потока. Это и есть ожидаемый
    путь: авторитетная проверка реальных байт нужна там, где заголовок лжёт,
    см. тест ниже.
    """
    _install_fake_rarfile(
        monkeypatch,
        {"a.bin": (100, 100), "b.bin": (100, 100), "c.bin": (100, 100)},
    )
    parser = _parser(250)
    result = ParseResult(file_path="x.rar", file_type="archive")
    out = tmp_path / "out"
    out.mkdir()

    files = parser._extract_rar("x.rar", str(out), result)

    assert len(files) == 2, "третий файл должен был упереться в потолок"
    assert "rar_max_extracted_size_reached" in result.warnings
    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    assert total <= parser.MAX_EXTRACTED_SIZE


def test_cumulative_cap_holds_when_every_header_lies(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Все заголовки занижены — потолок должен держать реальный поток.

    Здесь early-reject бесполезен (заявлено по 1 байту), поэтому сработать
    обязана именно проверка реальных байт, и суммарно на диск не должно попасть
    больше потолка.
    """
    _install_fake_rarfile(
        monkeypatch,
        {"a.bin": (1, 100), "b.bin": (1, 100), "c.bin": (1, 100)},
    )
    parser = _parser(250)
    result = ParseResult(file_path="x.rar", file_type="archive")
    out = tmp_path / "out"
    out.mkdir()

    files = parser._extract_rar("x.rar", str(out), result)

    assert "max_extracted_size_reached" in result.warnings, (
        "сработал не тот guard: заголовки лгут, спасти может только подсчёт байт"
    )
    assert len(files) == 2
    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    assert total <= parser.MAX_EXTRACTED_SIZE, (
        f"записано {total} при потолке {parser.MAX_EXTRACTED_SIZE}"
    )


# ── честная распаковка не сломана ───────────────────────────────────────────

def test_legitimate_archive_still_extracts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    _install_fake_rarfile(monkeypatch, {"doc.txt": (11, 11), "b/inner.txt": (5, 5)})
    parser = _parser(1024 * 1024)
    result = ParseResult(file_path="ok.rar", file_type="archive")
    out = tmp_path / "out"
    out.mkdir()

    files = parser._extract_rar("ok.rar", str(out), result)

    assert len(files) == 2
    assert all(Path(f).is_file() for f in files)
    assert Path(files[0]).read_bytes() == b"X" * 11
    # Вложенный путь создан внутри целевой директории.
    assert (out / "b" / "inner.txt").is_file()
    assert "max_extracted_size_reached" not in result.warnings


def test_declared_size_still_used_as_cheap_early_reject(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Огромный заявленный размер отсекается до чтения потока.

    Обратная сторона H4: доверять заголовку нельзя как guard'у, но использовать
    его для дешёвого отказа полезно — незачем стримить то, что заведомо не влезет.
    """
    calls = _install_fake_rarfile(monkeypatch, {"huge.bin": (10**9, 4)})
    parser = _parser(1024)
    result = ParseResult(file_path="x.rar", file_type="archive")
    out = tmp_path / "out"
    out.mkdir()

    files = parser._extract_rar("x.rar", str(out), result)

    assert files == []
    assert "rar_max_extracted_size_reached" in result.warnings
    assert calls["open"] == [], "поток не должен открываться при early-reject"


def test_missing_getinfo_does_not_abort_extraction(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Сбой getinfo() больше не добавляет фиктивный 1 МБ к счётчику.

    Раньше при исключении в getinfo прибавлялась «консервативная оценка» 1 МБ,
    из-за чего честный маленький архив мог упереться в потолок на пустом месте.
    Теперь неизвестный заявленный размер = 0, а решает реальный поток.
    """
    _install_fake_rarfile(monkeypatch, {"a.bin": (4, 4)})
    module = sys.modules["rarfile"]

    def _boom(self, name):  # noqa: ANN001
        raise RuntimeError("нет заголовка")

    monkeypatch.setattr(module.RarFile, "getinfo", _boom)

    parser = _parser(64)
    result = ParseResult(file_path="x.rar", file_type="archive")
    out = tmp_path / "out"
    out.mkdir()

    files = parser._extract_rar("x.rar", str(out), result)

    assert len(files) == 1
    assert "rar_max_extracted_size_reached" not in result.warnings


# ── path traversal выровнен с zip ───────────────────────────────────────────

@pytest.mark.parametrize(
    "member",
    [
        "../escape.txt",
        "../../etc/passwd",
        "a/../../escape.txt",
        "/absolute.txt",
    ],
)
def test_traversal_members_are_blocked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, member: str
):
    _install_fake_rarfile(monkeypatch, {member: (4, 4)})
    out = tmp_path / "out"
    out.mkdir()
    result = ParseResult(file_path="x.rar", file_type="archive")

    files = _parser(1024)._extract_rar("x.rar", str(out), result)

    assert files == []
    outside = [p for p in tmp_path.rglob("*") if p.is_file() and out not in p.parents]
    assert outside == [], f"файл записан вне целевой директории: {outside}"


def test_rar_uses_the_same_traversal_check_as_zip():
    """Прежняя RAR-проверка была той, которую zip-путь называет недостаточной.

    zip перешёл на abspath-сравнение (комментарий в _extract_zip объясняет, что
    `".." in member` пропускает windows-стиль и drive letters). RAR оставался на
    старом варианте и вдобавок валидировал один путь, а распаковывал по другому.
    """
    import ast
    import inspect

    from core.file_parsers import archive_parser

    src = inspect.getsource(archive_parser.ArchiveParser._extract_rar)
    tree = ast.parse(src.strip())
    calls = {
        getattr(n.func, "attr", getattr(n.func, "id", ""))
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
    }
    assert "abspath" in calls, "RAR не использует abspath-сравнение"
    assert "_stream_copy_capped" in calls, "RAR не считает реальные байты"
    assert "extract" not in calls, "RAR снова зовёт распаковку целиком"
