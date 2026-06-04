"""
🎬 Video Parser v2.0 — Видео → транскрипт + ключевые кадры
============================================================
Стратегия: extract audio → AudioParser + extract frames → OCR/captions

CHANGELOG v2.0:
- 🆕 Использует AudioParser для саундтрека (DRY — не дублирует Whisper)
- 🆕 Frame extraction через ffmpeg (lighter, чем OpenCV)
- 🆕 Опциональный Vision-LLM для описания ключевых кадров
"""

import logging
import os
import subprocess
import tempfile
import time

from .base import FileParser, ParseResult

logger = logging.getLogger("velantrim.parsers.video")


def _check_available_cmd(cmd: str) -> bool:
    """Проверка доступности CLI команды (ffmpeg, etc)."""
    import shutil
    return shutil.which(cmd) is not None


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


FFMPEG_AVAILABLE = _check_available_cmd("ffmpeg")
OPENCV_AVAILABLE = _check_available("cv2")


class VideoParser(FileParser):
    file_type = "video"

    # Видео может быть очень большим
    max_file_size_bytes = 5 * 1024 * 1024 * 1024  # 5 GB

    def supported_formats(self) -> list:
        return [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".ts", ".mts"]

    def parse(self, file_path: str) -> ParseResult:
        early = self._check_file(file_path)
        if early is not None:
            return early

        result = ParseResult(file_path=file_path, file_type="video")
        result.file_size_bytes = self._get_file_size(file_path)
        start = time.time()

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_text = ""
                segments: list[dict] = []
                frames_info: list[dict] = []
                method_parts: list[str] = []

                # Аудиодорожка → транскрипт через AudioParser
                if FFMPEG_AVAILABLE:
                    audio_path = self._extract_audio(file_path, tmpdir)
                    if audio_path:
                        try:
                            from .audio_parser import AudioParser
                            audio_parser = AudioParser()
                            audio_result = audio_parser.parse(audio_path)
                            if not audio_result.error:
                                audio_text = audio_result.extracted_text
                                segments = audio_result.structured_data.get("segments", [])
                                method_parts.append(
                                    f"audio:{audio_result.extraction_method}"
                                )
                                if audio_result.language:
                                    result.language = audio_result.language
                        except Exception as exc:
                            logger.warning(f"Audio extraction failed: {exc}")
                            result.warnings.append(f"audio_failed: {exc}")
                else:
                    result.warnings.append("ffmpeg_unavailable: no audio transcript")

                # Ключевые кадры
                if FFMPEG_AVAILABLE:
                    try:
                        frames = self._extract_keyframes(file_path, tmpdir, count=5)
                        # Опционально: OCR/Vision на кадрах
                        if frames and os.getenv("VELANTRIM_VIDEO_OCR", "false").lower() == "true":
                            from .image_parser import ImageParser
                            img_parser = ImageParser()
                            for fpath in frames:
                                ir = img_parser.parse(fpath)
                                if ir.extracted_text and not ir.extracted_text.startswith("["):
                                    frames_info.append({
                                        "frame": os.path.basename(fpath),
                                        "text": ir.extracted_text[:200],
                                    })
                            if frames_info:
                                method_parts.append("frames:OCR")
                        else:
                            frames_info = [{"frame": os.path.basename(f)} for f in frames]
                            method_parts.append("frames:extracted")
                    except Exception as exc:
                        logger.warning(f"Frame extraction failed: {exc}")
                        result.warnings.append(f"frames_failed: {exc}")

                # Сборка результата
                text_parts: list[str] = []
                if audio_text:
                    text_parts.append("=== Аудио транскрипт ===\n" + audio_text)
                if frames_info:
                    text_parts.append("\n=== Кадры ===\n" + "\n".join(
                        f.get("text", f.get("frame", "")) for f in frames_info
                    ))

                if not text_parts:
                    result.error = (
                        "Видео не удалось обработать. "
                        "Установите ffmpeg для извлечения аудио/кадров."
                    )
                    return result

                result.extracted_text = "\n".join(text_parts)
                result.word_count = len(result.extracted_text.split())
                result.extraction_method = " + ".join(method_parts) or "partial"
                result.structured_data = {
                    "format": "video",
                    "audio_segments": segments,
                    "frames": frames_info,
                    "total_segments": len(segments),
                }
                result.provenance = self._build_provenance(file_path, result.extraction_method)

                if result.extracted_text.strip():
                    result = self._enrich_with_essence(result)

        except Exception as exc:
            logger.error(f"VideoParser error: {exc}")
            result.error = str(exc)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _extract_audio(self, video_path: str, tmpdir: str) -> str:
        """Извлекает аудиодорожку через ffmpeg → mp3."""
        audio_path = os.path.join(tmpdir, "audio.mp3")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", video_path,
                    "-vn",                # без видео
                    "-acodec", "libmp3lame",
                    "-ab", "192k",
                    "-y",                 # overwrite
                    audio_path,
                ],
                capture_output=True,
                check=True,
                timeout=600,  # 10 min max
            )
            return audio_path if os.path.exists(audio_path) else ""
        except subprocess.CalledProcessError as exc:
            logger.warning(f"ffmpeg audio extract failed: {exc.stderr.decode(errors='replace')[:200]}")
            return ""
        except subprocess.TimeoutExpired:
            logger.warning("ffmpeg audio extract timeout (10 min)")
            return ""

    def _extract_keyframes(self, video_path: str, tmpdir: str, count: int = 5) -> list[str]:
        """Извлекает count ключевых кадров через ffmpeg."""
        frames_dir = os.path.join(tmpdir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        # Извлекаем кадры через select=eq(pict_type,I) — только I-frames
        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", video_path,
                    "-vf", "select='eq(pict_type,I)',scale=640:-1",
                    "-vsync", "vfr",
                    "-frames:v", str(count),
                    "-y",
                    os.path.join(frames_dir, "frame_%03d.jpg"),
                ],
                capture_output=True,
                check=True,
                timeout=300,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []

        return sorted(
            os.path.join(frames_dir, f)
            for f in os.listdir(frames_dir)
            if f.endswith(".jpg")
        )
