"""
🖼️ Image Parser v2.0 — OCR + Vision-LLM
=========================================
Каскад:
    Vision-LLM (опц.) → Tesseract (multilang) → PIL metadata

CHANGELOG v2.0:
- 🆕 Конфигурируемые языки OCR (не хардкод "rus+eng")
- 🆕 EXIF metadata извлечение (камера, дата, GPS)
- 🆕 Опциональный Vision-LLM путь (через VELANTRIM_VISION_LLM)
- 🆕 Auto-detection поворота (Tesseract OSD)
- 🆕 _enrich_with_essence унаследован из base
"""

import logging
import os
import time

from .base import FileParser, ParseResult

logger = logging.getLogger("velantrim.parsers.image")


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


PIL_AVAILABLE = _check_available("PIL")
TESSERACT_AVAILABLE = _check_available("pytesseract") and PIL_AVAILABLE


class ImageParser(FileParser):
    """
    Парсер изображений с OCR.

    Конфигурация через ENV:
        VELANTRIM_OCR_LANG=rus+eng+jpn   — языки Tesseract (default: rus+eng)
        VELANTRIM_OCR_OSD=true            — автоопределение поворота
        VELANTRIM_VISION_LLM=true         — использовать Vision-LLM
    """

    file_type = "image"
    # Изображения обычно небольшие, 100MB разумно
    max_file_size_bytes = 100 * 1024 * 1024

    def supported_formats(self) -> list:
        return [
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
            ".bmp", ".tiff", ".tif", ".heic", ".heif",
        ]

    def parse(self, file_path: str) -> ParseResult:
        early = self._check_file(file_path)
        if early is not None:
            return early

        result = ParseResult(file_path=file_path, file_type="image")
        result.file_size_bytes = self._get_file_size(file_path)
        start = time.time()

        if not PIL_AVAILABLE:
            result.error = "PIL/Pillow не установлен. pip install Pillow"
            result.parse_time_ms = (time.time() - start) * 1000
            return result

        try:
            from PIL import Image
            from PIL.ExifTags import TAGS

            with Image.open(file_path) as img:
                metadata = {
                    "width": img.size[0],
                    "height": img.size[1],
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": result.file_size_bytes,
                }

                # EXIF metadata (v2.0 new)
                exif_data = {}
                try:
                    exif = img._getexif() or {}
                    for tag_id, value in exif.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        # Pickle-safe values only
                        if isinstance(value, (str, int, float, tuple)):
                            exif_data[str(tag_name)] = value
                except Exception:
                    pass
                if exif_data:
                    metadata["exif"] = exif_data

            # Выбор метода извлечения текста
            extracted_text = ""

            # Метод 1: Vision-LLM (опционально)
            if os.getenv("VELANTRIM_VISION_LLM", "false").lower() == "true":
                try:
                    extracted_text = self._parse_vision_llm(file_path)
                    result.extraction_method = "Vision-LLM"
                except Exception as exc:
                    logger.warning(f"Vision-LLM failed: {exc}, fallback to OCR")
                    result.warnings.append("vision_llm_failed")

            # Метод 2: Tesseract OCR с multilang
            if not extracted_text and TESSERACT_AVAILABLE:
                try:
                    extracted_text = self._parse_tesseract(file_path)
                    result.extraction_method = "pytesseract OCR"
                except Exception as exc:
                    logger.warning(f"Tesseract failed: {exc}")
                    result.warnings.append(f"tesseract_failed: {exc}")

            # Метод 3: только метаданные
            if not extracted_text:
                w, h = metadata["width"], metadata["height"]
                extracted_text = (
                    f"[Image {w}x{h} {metadata['format']}]"
                    + (" — установите tesseract для OCR" if not TESSERACT_AVAILABLE else "")
                )
                if not result.extraction_method:
                    result.extraction_method = "PIL metadata only"

            result.extracted_text = extracted_text
            result.metadata = metadata
            result.word_count = len(extracted_text.split()) if extracted_text else 0
            result.structured_data = {"image_info": metadata}
            result.provenance = self._build_provenance(
                file_path, result.extraction_method
            )

            if extracted_text.strip() and not extracted_text.startswith("[Image"):
                result = self._enrich_with_essence(result)

        except Exception as exc:
            logger.error(f"ImageParser error: {exc}")
            result.error = str(exc)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    # ─── Backends ─────────────────────────────────────────────────────────────

    def _parse_tesseract(self, file_path: str) -> str:
        """Tesseract OCR с конфигурируемыми языками и OSD."""
        import pytesseract
        from PIL import Image

        languages = os.getenv("VELANTRIM_OCR_LANG", "rus+eng")
        use_osd = os.getenv("VELANTRIM_OCR_OSD", "true").lower() == "true"

        img = Image.open(file_path)

        # OSD — auto-detect rotation and rotate before OCR
        if use_osd:
            try:
                osd = pytesseract.image_to_osd(img)
                # Parse rotation angle from OSD output
                for line in osd.split("\n"):
                    if "Rotate:" in line:
                        angle = int(line.split(":")[1].strip())
                        if angle != 0:
                            img = img.rotate(-angle, expand=True)
                        break
            except Exception:
                pass  # OSD не работает на маленьких изображениях

        text = pytesseract.image_to_string(img, lang=languages).strip()
        return text

    def _parse_vision_llm(self, file_path: str) -> str:
        """
        Vision-LLM путь — опциональный, требует настроенного LLM провайдера.
        Реализация зависит от конкретного провайдера (Claude/GPT-4V/Pixtral).

        TODO: интеграция с центральной LLM-конфигурацией Velantrim.
        """
        raise NotImplementedError(
            "Vision-LLM backend не реализован. "
            "Интегрировать с core/llm_config.py в Sprint 2c."
        )
