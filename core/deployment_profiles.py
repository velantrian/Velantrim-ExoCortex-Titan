"""
Профили развёртывания — «витрина» Velantrim для разных аудиторий.

Пользователь выбирает профиль (личный / компания / наука / …):
  • при старте сервера: VELANTRIM_PROFILE=personal + config/profiles/personal.env
  • в запросе: POST /query { "profile": "citizen", "query": "..." }
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = ROOT / "config" / "profiles"

# Заводские значения QueryRequest — для «явного» переопределения полей
_QUERY_DEFAULTS = {
    "mode": "BALANCED",
    "response_lens": "VELANTRIM",
    "top_k": 3,
    "use_llm": True,
    "domain": None,
}


@dataclass(frozen=True)
class DeploymentProfile:
    id: str
    emoji: str
    title: str
    tagline: str
    difficulty: str  # easy | medium | hard
    audience: str
    env_file: str
    query_mode: str
    query_lens: str
    query_domain: str | None
    query_top_k: int
    query_use_llm: bool
    landmark_steps: list[str] = field(default_factory=list)
    recommended_api: list[str] = field(default_factory=list)
    features_human: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "emoji": self.emoji,
            "title": self.title,
            "tagline": self.tagline,
            "difficulty": self.difficulty,
            "difficulty_stars": _difficulty_stars(self.difficulty),
            "audience": self.audience,
            "env_file": self.env_file,
            "startup": {
                "env_var": "VELANTRIM_PROFILE",
                "example": f"VELANTRIM_PROFILE={self.id}",
                "powershell": f"$env:VELANTRIM_PROFILE='{self.id}'; uvicorn server:app --port 8755",
            },
            "query_defaults": {
                "mode": self.query_mode,
                "response_lens": self.query_lens,
                "domain": self.query_domain,
                "top_k": self.query_top_k,
                "use_llm": self.query_use_llm,
            },
            "landmark_steps": self.landmark_steps,
            "recommended_api": self.recommended_api,
            "features": self.features_human,
        }


def _difficulty_stars(level: str) -> str:
    return {"easy": "⭐", "medium": "⭐⭐", "hard": "⭐⭐⭐"}.get(level, "⭐⭐")


_PROFILES: dict[str, DeploymentProfile] = {
    "citizen": DeploymentProfile(
        id="citizen",
        emoji="🏠",
        title="Для всех",
        tagline="Простой личный помощник: спросил — получил ответ из памяти",
        difficulty="easy",
        audience="Обычные люди без технического бэкграунда",
        env_file="config/profiles/citizen.env",
        query_mode="BALANCED",
        query_lens="PERSONAL",
        query_domain="personal",
        query_top_k=3,
        query_use_llm=True,
        landmark_steps=[
            "1️⃣ Запусти сервер с профилем citizen",
            "2️⃣ POST /query с полем profile: citizen",
            "3️⃣ Сохрани важное: POST /facts одной фразой",
        ],
        recommended_api=["POST /query", "POST /facts", "GET /health"],
        features_human=[
            "Простые ответы, без жаргона",
            "Личная линза (PERSONAL)",
            "Минимум фоновых процессов",
        ],
    ),
    "personal": DeploymentProfile(
        id="personal",
        emoji="🧑",
        title="Личный бот",
        tagline="Цели, привычки, заметки — память только для тебя",
        difficulty="easy",
        audience="Персональный AI-ассистент",
        env_file="config/profiles/personal.env",
        query_mode="BALANCED",
        query_lens="PERSONAL",
        query_domain="personal",
        query_top_k=5,
        query_use_llm=True,
        landmark_steps=[
            "1️⃣ POST /goals — задай 1–3 цели",
            "2️⃣ POST /facts — сохрани факты о себе",
            "3️⃣ POST /query profile=personal — спроси с учётом целей",
            "4️⃣ GET /innenwelt — что система «чувствует»",
        ],
        recommended_api=[
            "POST /query",
            "POST /facts",
            "GET|POST /goals",
            "GET /gaps",
            "GET /innenwelt",
        ],
        features_human=[
            "Innenwelt: цели и пробелы",
            "ModeRouter PERSONAL",
            "Telegram (опционально)",
        ],
    ),
    "company": DeploymentProfile(
        id="company",
        emoji="🏢",
        title="Компания",
        tagline="Корпоративная память: факты, аудит, лимиты, благополучие системы",
        difficulty="medium",
        audience="Команды, поддержка, внутренние агенты",
        env_file="config/profiles/company.env",
        query_mode="PRECISION",
        query_lens="VELANTRIM",
        query_domain="system",
        query_top_k=5,
        query_use_llm=True,
        landmark_steps=[
            "1️⃣ Обязательный VELANTRIM_API_KEY",
            "2️⃣ POST /facts source=wiki/HR/…",
            "3️⃣ POST /query profile=company mode=PRECISION",
            "4️⃣ GET /welfare и GET /titan/status — здоровье",
            "5️⃣ GET /audit/recent — что отвечала система",
        ],
        recommended_api=[
            "POST /query",
            "POST /facts",
            "GET /welfare",
            "GET /titan/status",
            "GET /audit/recent",
            "POST /memory/volition",
        ],
        features_human=[
            "Строгий Truth Gate (PRECISION)",
            "Welfare + Memory Budget",
            "Аудит ответов",
        ],
    ),
    "science": DeploymentProfile(
        id="science",
        emoji="🔬",
        title="Наука",
        tagline="Факты, источники, причинность — для исследовательской работы",
        difficulty="medium",
        audience="Учёные, лаборатории, R&D",
        env_file="config/profiles/science.env",
        query_mode="PRECISION",
        query_lens="UMWELT",
        query_domain="science",
        query_top_k=8,
        query_use_llm=True,
        landmark_steps=[
            "1️⃣ POST /ingest/text или /facts с source=doi/…",
            "2️⃣ POST /query profile=science domain=science",
            "3️⃣ GET /facts/{id}/relations — связи",
            "4️⃣ POST /cross-domain/plan — мосты доменов",
        ],
        recommended_api=[
            "POST /facts",
            "POST /ingest/text",
            "POST /query",
            "GET /facts/{id}/relations",
            "POST /cross-domain/plan",
        ],
        features_human=[
            "Каузальный граф",
            "Домен science",
            "Umwelt: инженер + учёный + наблюдатель",
        ],
    ),
    "education": DeploymentProfile(
        id="education",
        emoji="🎒",
        title="Обучение",
        tagline="Курсы, конспекты, экзамены — память ученика или преподавателя",
        difficulty="easy",
        audience="Школа, вуз, самообучение",
        env_file="config/profiles/education.env",
        query_mode="BALANCED",
        query_lens="PERSONAL",
        query_domain="personal",
        query_top_k=6,
        query_use_llm=True,
        landmark_steps=[
            "1️⃣ POST /facts — сохрани определение или правило",
            "2️⃣ POST /ingest/text — вставь конспект",
            "3️⃣ POST /query profile=education — спроси «объясни» или «проверь меня»",
            "4️⃣ POST /goals — цель: «сдать экзамен по …»",
        ],
        recommended_api=[
            "POST /query",
            "POST /facts",
            "POST /ingest/text",
            "GET|POST /goals",
        ],
        features_human=[
            "Понятные ответы (BALANCED + PERSONAL)",
            "Innenwelt для целей обучения",
            "Ingest текста для лекций",
        ],
    ),
    "research": DeploymentProfile(
        id="research",
        emoji="🧪",
        title="Исследования",
        tagline="Максимум связей, cross-domain, cognitive runtime",
        difficulty="hard",
        audience="Advanced R&D, прототипы, Horizons",
        env_file="config/profiles/research.env",
        query_mode="EXPLORATION",
        query_lens="UMWELT",
        query_domain="science",
        query_top_k=10,
        query_use_llm=True,
        landmark_steps=[
            "1️⃣ Профиль research + exocortex слои",
            "2️⃣ POST /query — смотри cross_domain в ответе",
            "3️⃣ GET /runtime/status",
            "4️⃣ GET /horizons — что в roadmap",
        ],
        recommended_api=[
            "POST /query",
            "GET /runtime/status",
            "GET /cross-domain/bridges",
            "GET /horizons",
            "GET /cognitive/facts",
        ],
        features_human=[
            "CrossDomain V3",
            "CognitiveFact + Runtime",
            "PolyWelt 6 агентов",
        ],
    ),
    "developer": DeploymentProfile(
        id="developer",
        emoji="⚙️",
        title="Разработчик",
        tagline="Все слои ExoCortex — как в dev-профиле",
        difficulty="hard",
        audience="Инженеры Velantrim",
        env_file="config/exocortex-dev.env",
        query_mode="BALANCED",
        query_lens="VELANTRIM",
        query_domain=None,
        query_top_k=10,
        query_use_llm=True,
        landmark_steps=[
            "1️⃣ config/exocortex-dev.env → .env",
            "2️⃣ GET /layers/status",
            "3️⃣ GET /titan/status",
            "4️⃣ pytest tests/",
        ],
        recommended_api=[
            "GET /layers/status",
            "GET /titan/status",
            "GET /runtime/status",
            "POST /query",
        ],
        features_human=["Все ENABLE_* из exocortex-dev", "Для отладки и демо"],
    ),
}


def list_profiles() -> list[dict[str, Any]]:
    return [p.to_dict() for p in _PROFILES.values()]


def get_profile(profile_id: str) -> DeploymentProfile:
    key = (profile_id or "").strip().lower()
    if key not in _PROFILES:
        allowed = ", ".join(sorted(_PROFILES))
        raise ValueError(f"Неизвестный profile '{profile_id}'. Доступны: {allowed}")
    return _PROFILES[key]


def get_current_profile_id() -> str | None:
    raw = (os.getenv("VELANTRIM_PROFILE") or "").strip().lower()
    return raw if raw in _PROFILES else None


def get_current_profile() -> dict[str, Any] | None:
    pid = get_current_profile_id()
    if not pid:
        return None
    out = get_profile(pid).to_dict()
    out["active_on_server"] = True
    return out


def resolve_query_params(
    *,
    profile: str | None,
    mode: str,
    response_lens: str,
    domain: str | None,
    top_k: int,
    use_llm: bool | None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """
    Слить профиль с полями запроса.
    Явно переданные значения (≠ заводских) имеют приоритет над профилем.
    use_llm=None — взять из профиля или True по умолчанию.
    """
    default_use_llm = True if use_llm is None else use_llm

    if not profile:
        return {
            "mode": mode,
            "response_lens": response_lens,
            "domain": domain,
            "top_k": top_k,
            "use_llm": default_use_llm,
        }, None

    p = get_profile(profile)
    eff_use_llm = p.query_use_llm if use_llm is None else use_llm
    effective = {
        "mode": mode if mode != _QUERY_DEFAULTS["mode"] else p.query_mode,
        "response_lens": (
            response_lens
            if response_lens != _QUERY_DEFAULTS["response_lens"]
            else p.query_lens
        ),
        "domain": domain if domain is not None else p.query_domain,
        "top_k": top_k if top_k != _QUERY_DEFAULTS["top_k"] else p.query_top_k,
        "use_llm": eff_use_llm,
    }
    landmark = {
        "profile": p.id,
        "emoji": p.emoji,
        "title": p.title,
        "difficulty": p.difficulty,
        "difficulty_stars": _difficulty_stars(p.difficulty),
        "tagline": p.tagline,
        "landmark_steps": p.landmark_steps,
    }
    return effective, landmark


def load_profile_env(profile_id: str, *, override: bool = True) -> Path:
    """Подгрузить config/profiles/<id>.env (или путь из профиля)."""
    from dotenv import load_dotenv

    from core.feature_config import clear_config_cache

    p = get_profile(profile_id)
    path = ROOT / p.env_file
    if not path.is_file():
        raise FileNotFoundError(f"Файл профиля не найден: {path}")
    load_dotenv(path, override=override)
    os.environ["VELANTRIM_PROFILE"] = p.id
    clear_config_cache()
    return path


__all__ = [
    "DeploymentProfile",
    "get_current_profile",
    "get_current_profile_id",
    "get_profile",
    "list_profiles",
    "load_profile_env",
    "resolve_query_params",
]
