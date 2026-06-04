"""Короткий WAV для проверки STT (Gemini / OpenAI Whisper)."""

from __future__ import annotations

import base64
import io
import math
import struct
import wave


def make_test_wav_base64(duration_ms: int = 800, sample_rate: int = 16000) -> str:
    """Синус 440 Гц — достаточно для теста API распознавания."""
    n_frames = max(1, int(sample_rate * duration_ms / 1000))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_frames):
            val = int(8000 * math.sin(2 * math.pi * 440.0 * i / sample_rate))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return base64.b64encode(buf.getvalue()).decode("ascii")


TEST_WAV_B64 = make_test_wav_base64()

__all__ = ["TEST_WAV_B64", "make_test_wav_base64"]
