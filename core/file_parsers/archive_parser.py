"""
📦 Archive Parser v2.0 — Архивы с рекурсивной обработкой (НОВЫЙ)
=================================================================
Поддерживает: ZIP, TAR, TAR.GZ, TAR.BZ2, 7Z, RAR

Парсер ВНУТРИ распаковывает архив во временную папку и обрабатывает
каждый файл через FileIngester (если он передан). Это даёт цепочечный
парсинг: .zip → внутри .pdf → внутри .png → OCR.

⚠️ ВАЖНО: рекурсия защищена от zip-bombs через:
- max_extracted_size — лимит распакованных данных
- max_files — лимит количества файлов
- max_depth — глубина вложенности архивов
"""

import logging
import os
import tempfile
import time

from .base import FileParser, ParseResult

logger = logging.getLogger("velantrim.parsers.archive")


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


PY7ZR_AVAILABLE = _check_available("py7zr")
RARFILE_AVAILABLE = _check_available("rarfile")


class ArchiveParser(FileParser):
    file_type = "archive"

    # Защита от zip-bomb
    MAX_EXTRACTED_SIZE = 1024 * 1024 * 1024  # 1 GB распакованных данных
    MAX_FILES = 1000                          # Не более 1000 файлов
    MAX_DEPTH = 3                             # Не более 3 уровней вложенности

    def __init__(self, inner_ingester: object | None = None, _depth: int = 0) -> None:
        """
        Args:
            inner_ingester: FileIngester для парсинга вложенных файлов.
                            Если None — только листинг содержимого без парсинга.
            _depth: текущая глубина рекурсии (internal).
        """
        super().__init__()
        self._inner = inner_ingester
        self._depth = _depth

    def supported_formats(self) -> list:
        return [
            ".zip", ".tar", ".gz", ".tar.gz", ".tgz",
            ".tar.bz2", ".tbz2", ".bz2",
            ".7z", ".rar",
        ]

    def parse(self, file_path: str) -> ParseResult:
        early = self._check_file(file_path)
        if early is not None:
            return early

        result = ParseResult(file_path=file_path, file_type="archive")
        result.file_size_bytes = self._get_file_size(file_path)
        start = time.time()

        if self._depth >= self.MAX_DEPTH:
            result.error = f"Превышена максимальная глубина вложенности архивов: {self.MAX_DEPTH}"
            result.parse_time_ms = (time.time() - start) * 1000
            return result

        ext = file_path.lower()

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                if ext.endswith(".zip"):
                    files = self._extract_zip(file_path, tmpdir, result)
                    result.extraction_method = "zipfile"
                elif ext.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2")):
                    files = self._extract_tar(file_path, tmpdir, result)
                    result.extraction_method = "tarfile"
                elif ext.endswith(".7z") and PY7ZR_AVAILABLE:
                    files = self._extract_7z(file_path, tmpdir, result)
                    result.extraction_method = "py7zr"
                elif ext.endswith(".rar") and RARFILE_AVAILABLE:
                    files = self._extract_rar(file_path, tmpdir, result)
                    result.extraction_method = "rarfile"
                else:
                    result.error = (
                        f"Архив {ext} не поддерживается. "
                        "Установите: pip install py7zr rarfile"
                    )
                    return result

                # Рекурсивный парсинг через inner ingester
                # FIX v8.5.1 (Gemini Security): depth передаётся как параметр.
                # Раньше _depth хранился в состоянии синглтона и никогда
                # не увеличивался → zip-bomb защита не работала.
                # Теперь для вложенных архивов создаётся новый ArchiveParser
                # с depth+1 — если встречается вложенный .zip, он проверит
                # self._depth+1 >= MAX_DEPTH и остановится.
                inner_results: list[dict] = []
                if self._inner and files:
                    # Временно заменяем archive-парсер в registry на версию с depth+1
                    _deeper = ArchiveParser(
                        inner_ingester=self._inner,
                        _depth=self._depth + 1,
                    )
                    _orig_archive = None
                    if hasattr(self._inner, "registry"):
                        _orig_archive = self._inner.registry._initialized.get("archive")
                        self._inner.registry._initialized["archive"] = _deeper

                    for fpath in files[: self.MAX_FILES]:
                        try:
                            r = self._inner.ingest(fpath)  # type: ignore[attr-defined]  # _inner — FileIngester (duck-typed)
                            inner_results.append({
                                "file": os.path.basename(fpath),
                                "type": r.file_type,
                                "method": r.extraction_method,
                                "text_length": len(r.extracted_text or ""),
                                "error": r.error,
                            })
                        except Exception as exc:
                            logger.warning(f"Inner parse failed for {fpath}: {exc}")

                    # Восстанавливаем оригинальный archive-парсер
                    if _orig_archive is not None and hasattr(self._inner, "registry"):
                        self._inner.registry._initialized["archive"] = _orig_archive

                # Сборка текста — простой листинг + первые 1000 символов из каждого
                text_parts: list[str] = [
                    f"=== Archive: {os.path.basename(file_path)} ===",
                    f"Files: {len(files)}",
                    "",
                ]
                for f in files[:50]:
                    text_parts.append(f"  - {os.path.relpath(f, tmpdir)}")
                text = "\n".join(text_parts)

                result.extracted_text = text
                result.structured_data = {
                    "format": "archive",
                    "file_count": len(files),
                    "files": [os.path.relpath(f, tmpdir) for f in files[:200]],
                    "inner_results": inner_results,
                    "depth": self._depth,
                }
                result.provenance = self._build_provenance(file_path, result.extraction_method)

        except Exception as exc:
            logger.error(f"ArchiveParser error: {exc}")
            result.error = str(exc)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    # ─── Extract methods (защищены от zip-bomb) ───────────────────────────────

    def _stream_copy_capped(
        self,
        src,
        dest_path: str,
        total_size: int,
        result: ParseResult,
        chunk_size: int = 1024 * 1024,
    ) -> tuple[int, bool]:
        """Copy src→dest counting REAL bytes; abort if cap exceeded.

        Returns (new_total_size, ok). On cap breach the partial dest file
        is removed and result.warnings gets max_extracted_size_reached.
        Declared archive sizes are NOT trusted — only bytes actually read.
        """
        parent = os.path.dirname(dest_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        written_ok = True
        with open(dest_path, "wb") as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > self.MAX_EXTRACTED_SIZE:
                    written_ok = False
                    break
                dst.write(chunk)
        if not written_ok:
            try:
                os.remove(dest_path)
            except OSError:
                pass
            result.warnings.append("max_extracted_size_reached")
            return total_size, False
        return total_size, True

    def _extract_zip(self, file_path: str, tmpdir: str, result: ParseResult) -> list[str]:
        import zipfile
        files: list[str] = []
        total_size = 0
        with zipfile.ZipFile(file_path, "r") as zf:
            for member in zf.namelist():
                if len(files) >= self.MAX_FILES:
                    result.warnings.append(f"max_files_reached: {self.MAX_FILES}")
                    break
                # Early reject on declared size (cheap); real-byte cap below
                # is the authoritative zip-bomb guard.
                info = zf.getinfo(member)
                if total_size + max(info.file_size, 0) > self.MAX_EXTRACTED_SIZE:
                    result.warnings.append("max_extracted_size_reached")
                    break
                # Защита от path traversal
                # FIX v8.5.3 (Gemini finding): простая проверка ".." in member
                # пропускает Windows-стиль (C:\Windows, \\..\\..\\), drive letters,
                # backslash-traversal. Правильная проверка — построить полный
                # путь через abspath и проверить, что он остаётся внутри tmpdir.
                base_target = os.path.abspath(tmpdir)
                target_path = os.path.abspath(os.path.join(base_target, member))
                if not target_path.startswith(base_target + os.sep) and target_path != base_target:
                    result.warnings.append(f"unsafe_path_skipped: {member}")
                    continue
                if member.endswith("/"):  # директория
                    continue
                with zf.open(member) as src:
                    total_size, ok = self._stream_copy_capped(
                        src, target_path, total_size, result
                    )
                if not ok:
                    break
                files.append(target_path)
        return files

    def _extract_tar(self, file_path: str, tmpdir: str, result: ParseResult) -> list[str]:
        import tarfile
        files: list[str] = []
        total_size = 0
        with tarfile.open(file_path, "r:*") as tf:
            for member in tf.getmembers():
                if len(files) >= self.MAX_FILES:
                    result.warnings.append(f"max_files_reached: {self.MAX_FILES}")
                    break
                if total_size + max(member.size, 0) > self.MAX_EXTRACTED_SIZE:
                    result.warnings.append("max_extracted_size_reached")
                    break
                # FIX v8.5.3 (Gemini finding): то же что и в zip — abspath-проверка
                base_target = os.path.abspath(tmpdir)
                target_path = os.path.abspath(os.path.join(base_target, member.name))
                if not target_path.startswith(base_target + os.sep) and target_path != base_target:
                    result.warnings.append(f"unsafe_path_skipped: {member.name}")
                    continue
                if not member.isfile():
                    continue
                src = tf.extractfile(member)
                if src is None:
                    continue
                with src:
                    total_size, ok = self._stream_copy_capped(
                        src, target_path, total_size, result
                    )
                if not ok:
                    break
                files.append(target_path)
        return files

    def _extract_7z(self, file_path: str, tmpdir: str, result: ParseResult) -> list[str]:
        """
        Извлечение .7z архива.

        FIX v8.5.3 (Claude audit + Gemini finding): отключено до реализации
        потоковой проверки размера. Текущий py7zr.extractall() не уважает
        MAX_EXTRACTED_SIZE и позволяет zip-bomb атаку: 5KB файл → 50GB OOM.
        В отличие от .zip и .tar (где у нас есть подсчёт байтов на каждый
        member), py7zr API не даёт удобного hook для проверки до распаковки.

        Альтернативы для будущей реализации (v8.5.4+):
        1. py7zr.read() поштучно с проверкой каждого extracted size.
        2. Внешний процесс 7z с -so и stream-counting.
        3. Лимит размера .7z файла на входе (косвенная защита).
        """
        result.error = (
            "Поддержка .7z временно отключена (v8.5.3) из-за риска zip-bomb DoS. "
            "Используйте .zip или .tar, где у нас есть защита по размеру. "
            "См. archive_parser.py:_extract_7z для деталей."
        )
        result.warnings.append("7z_disabled_security_v8.5.3")
        return []

    def _extract_rar(self, file_path: str, tmpdir: str, result: ParseResult) -> list[str]:
        """Распаковать RAR, считая РЕАЛЬНЫЕ байты (audit H4).

        Прежняя версия несла комментарий «добавить MAX_EXTRACTED_SIZE guard (как
        в _extract_zip/_extract_tar)», но паритета не было:

        * размер брался из `info.file_size` — из заголовка RAR, который
          контролирует атакующий, — и суммировался ДО распаковки;
        * затем вызывался `rf.extract(member, tmpdir)`, который пишет файл
          целиком, без предела. Архив с заниженным заявленным размером и
          огромным реальным содержимым проходил guard и писал на диск сколько
          хотел.

        Теперь так же, как в zip/tar: поток через `rf.open()` и
        `_stream_copy_capped`, который обрывает запись на реальном превышении и
        удаляет частичный файл. Заявленный размер остаётся дешёвым early-reject,
        но авторитетным guard'ом больше не является.

        Заодно проверка path traversal выровнена с `_extract_zip`. Прежняя
        (`".." in member_path.split(os.sep)` + `startswith("/")`) — ровно та,
        которую zip-путь в комментарии описывает как недостаточную: она не ловит
        windows-стиль и drive letters. На Linux она эти случаи всё же удерживала
        (backslash здесь не разделитель), так что эксплуатируемой дыры не было —
        это выравнивание, а не закрытие уязвимости. Дополнительно устранено
        рассогласование «проверяли `full`, а распаковывали по `member`».
        """
        import rarfile
        files: list[str] = []
        total_size = 0
        base_target = os.path.abspath(tmpdir)
        with rarfile.RarFile(file_path) as rf:
            for member in rf.namelist():
                if len(files) >= self.MAX_FILES:
                    result.warnings.append(f"max_files_reached: {self.MAX_FILES}")
                    break

                # Дешёвый early-reject по заявленному размеру. Не guard —
                # авторитетна только проверка реальных байт ниже.
                try:
                    declared = max(int(rf.getinfo(member).file_size), 0)
                except Exception:
                    declared = 0
                if total_size + declared > self.MAX_EXTRACTED_SIZE:
                    result.warnings.append("rar_max_extracted_size_reached")
                    break

                # Path traversal: тот же abspath-подход, что в _extract_zip.
                target_path = os.path.abspath(os.path.join(base_target, member))
                if (
                    not target_path.startswith(base_target + os.sep)
                    and target_path != base_target
                ):
                    result.warnings.append(f"rar_path_traversal_blocked: {member}")
                    continue
                if member.endswith("/"):  # директория
                    continue

                with rf.open(member) as src:
                    total_size, ok = self._stream_copy_capped(
                        src, target_path, total_size, result
                    )
                if not ok:
                    break
                files.append(target_path)
        return files
