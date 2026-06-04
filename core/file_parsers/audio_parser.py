"""
🎤 Audio Parser v2.0 — Транскрипция аудио в текст
==================================================
Каскад (от лучшего к fallback):
    faster-whisper → whisper.cpp → openai-whisper → easytranscriber

CHANGELOG v2.0:
- 🆕 faster-whisper (CTranslate2 backend) — 4× быстрее openai-whisper, 50% меньше RAM
- 🆕 Lazy singleton модели — раньше Whisper грузился НА КАЖДЫЙ файл (1.5GB × N)
- 🆕 Конфигурируемый размер модели через ENV (tiny/base/small/medium/large)
- 🆕 Auto language detection (раньше был хардкод "ru")
- 🆕 VAD filter (Voice Activity Detection) для пропуска тишины
"""

import logging
import os
import time

from .base import FileParser, ParseResult, _ModelSingleton

logger = logging.getLogger("velantrim.parsers.audio")


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


FASTER_WHISPER_AVAILABLE = _check_available("faster_whisper")
WHISPER_CPP_AVAILABLE    = _check_available("pywhispercpp")
OPENAI_WHISPER_AVAILABLE = _check_available("whisper")
EASYTRANSCRIBER_AVAILABLE = _check_available("easytranscriber")


class AudioParser(FileParser):
    """
    Парсер аудио с lazy-loading и каскадом backend'ов.

    Конфигурация через ENV:
        VELANTRIM_WHISPER_MODEL=base|small|medium|large-v3   (default: small)
        VELANTRIM_WHISPER_LANG=ru|en|auto                     (default: auto)
        VELANTRIM_WHISPER_DEVICE=cpu|cuda                     (default: cpu)
        VELANTRIM_WHISPER_COMPUTE_TYPE=int8|float16|float32   (default: int8)
    """

    file_type = "audio"
    # Аудио файлы обычно меньше видео, но 500MB разумно
    # 1 час аудио MP3 ~ 60 MB, час WAV ~ 600 MB

    def supported_formats(self) -> list:
        return [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma", ".opus", ".aiff"]

    def parse(self, file_path: str) -> ParseResult:
        early = self._check_file(file_path)
        if early is not None:
            return early

        result = ParseResult(file_path=file_path, file_type="audio")
        result.file_size_bytes = self._get_file_size(file_path)
        start = time.time()

        try:
            # Метод 1: faster-whisper — 4× быстрее, лучший выбор 2026
            if FASTER_WHISPER_AVAILABLE:
                text, segments, lang = self._parse_faster_whisper(file_path)
                result.extraction_method = "faster-whisper"
                result.language = lang

            # Метод 2: whisper.cpp — CPU-only, embedded systems
            elif WHISPER_CPP_AVAILABLE:
                text, segments, lang = self._parse_whisper_cpp(file_path)
                result.extraction_method = "whisper.cpp"
                result.language = lang

            # Метод 3: openai-whisper — оригинал, медленнее
            elif OPENAI_WHISPER_AVAILABLE:
                text, segments, lang = self._parse_openai_whisper(file_path)
                result.extraction_method = "openai-whisper"
                result.language = lang

            # Метод 4: easytranscriber
            elif EASYTRANSCRIBER_AVAILABLE:
                text, segments, lang = self._parse_easytranscriber(file_path)
                result.extraction_method = "easytranscriber"
                result.language = lang

            else:
                result.error = (
                    "Ни один аудио-парсер не доступен. Установите: "
                    "pip install faster-whisper  (рекомендуется)"
                )
                return result

            result.extracted_text = text
            result.word_count = len(text.split()) if text else 0
            result.structured_data = {
                "segments": segments,
                "total_segments": len(segments),
                "duration_seconds": (
                    segments[-1].get("end", 0) if segments else 0
                ),
                "has_timestamps": any(
                    s.get("start") is not None for s in segments
                ),
            }
            result.provenance = self._build_provenance(
                file_path, result.extraction_method
            )

            if text.strip():
                result = self._enrich_with_essence(result)

        except Exception as exc:
            logger.error(f"AudioParser error: {exc}")
            result.error = str(exc)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    # ─── Backend implementations ──────────────────────────────────────────────

    def _parse_faster_whisper(
        self, file_path: str
    ) -> tuple[str, list[dict], str]:
        """
        faster-whisper через _ModelSingleton.
        v2.0: модель грузится ОДИН РАЗ за процесс, не на каждый файл.
        """
        from faster_whisper import WhisperModel

        model_size = os.getenv("VELANTRIM_WHISPER_MODEL", "small")
        device = os.getenv("VELANTRIM_WHISPER_DEVICE", "cpu")
        compute_type = os.getenv("VELANTRIM_WHISPER_COMPUTE_TYPE", "int8")
        lang_setting = os.getenv("VELANTRIM_WHISPER_LANG", "auto")

        # Lazy singleton — модель грузится один раз
        model_key = f"faster-whisper:{model_size}:{device}:{compute_type}"
        model = _ModelSingleton.get(
            model_key,
            lambda: WhisperModel(
                model_size, device=device, compute_type=compute_type
            ),
        )

        # auto = автоопределение языка
        language = None if lang_setting == "auto" else lang_setting

        segments_gen, info = model.transcribe(
            file_path,
            language=language,
            vad_filter=True,  # Skip silence
            beam_size=5,
        )

        segments = []
        text_parts = []
        for seg in segments_gen:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            })
            text_parts.append(seg.text)

        text = " ".join(text_parts).strip()
        detected_lang = info.language if info else "unknown"
        return text, segments, detected_lang

    def _parse_whisper_cpp(
        self, file_path: str
    ) -> tuple[str, list[dict], str]:
        """whisper.cpp — pywhispercpp bindings."""
        from pywhispercpp.model import Model

        model_size = os.getenv("VELANTRIM_WHISPER_MODEL", "small")
        model_key = f"whisper.cpp:{model_size}"
        model = _ModelSingleton.get(
            model_key,
            lambda: Model(model_size, n_threads=4),
        )

        segments_raw = model.transcribe(file_path)
        segments = [
            {
                "start": s.t0 / 100.0,
                "end": s.t1 / 100.0,
                "text": s.text.strip(),
            }
            for s in segments_raw
        ]
        text = " ".join(s["text"] for s in segments)
        return text, segments, "auto"

    def _parse_openai_whisper(
        self, file_path: str
    ) -> tuple[str, list[dict], str]:
        """Оригинальный openai-whisper."""
        import whisper

        model_size = os.getenv("VELANTRIM_WHISPER_MODEL", "small")
        lang_setting = os.getenv("VELANTRIM_WHISPER_LANG", "auto")

        model_key = f"openai-whisper:{model_size}"
        model = _ModelSingleton.get(
            model_key, lambda: whisper.load_model(model_size)
        )

        language = None if lang_setting == "auto" else lang_setting
        kwargs = {"language": language} if language else {}
        transcription = model.transcribe(file_path, **kwargs)

        segments = [
            {
                "start": s.get("start"),
                "end": s.get("end"),
                "text": s["text"].strip(),
            }
            for s in transcription.get("segments", [])
        ]
        return (
            transcription["text"].strip(),
            segments,
            transcription.get("language", "unknown"),
        )

    def _parse_easytranscriber(
        self, file_path: str
    ) -> tuple[str, list[dict], str]:
        """easytranscriber — обёртка над whisper."""
        import easytranscriber

        model_size = os.getenv("VELANTRIM_WHISPER_MODEL", "small")
        model_key = f"easytranscriber:{model_size}"
        transcriber = _ModelSingleton.get(
            model_key,
            lambda: easytranscriber.Transcriber(model_size=model_size),
        )
        result = transcriber.transcribe(file_path)
        segments = result.get("segments", [])
        text = " ".join(s.get("text", "") for s in segments)
        return text, segments, result.get("language", "unknown")
