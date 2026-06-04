"""
core/claim_classifier.py — Детерминированный классификатор модальности памяти (v8.7, P0)
==========================================================================================

Классифицирует claim_type и origin_type без LLM — только регексы + эвристики.
Русский язык — первичный. Английский — поддерживается.

Принципы (из канона ТЗ):
  · Не использует LLM для классификации (P0-требование).
  · Не изменяет epistemic_state и не вызывает TruthGate.
  · Возвращает (claim_type, origin_type, confidence_hint) — тройку.
  · При сомнении → UNKNOWN, не угадывает.
  · Только детерминированные сигналы (первые слова, ключевые слова, источник).

Использование:
    from core.claim_classifier import classify_claim
    ct, ot, hint = classify_claim("Мне было тревожно", source="user_message")
    # → ("EMOTION", "USER_REPORTED", 0.9)
"""
from __future__ import annotations

import re

from core.validators import ClaimType, OriginType

# ─── Паттерны: первое лицо + эмоция (ru + en) ────────────────────────────────
_EMOTION_PATTERNS_RU = re.compile(
    r"^(мне\s+(\w+\s+)?(было|стало|казалось|страшно|тревожно|тяжело|больно|хорошо|плохо|одиноко|грустно|радостно|тоскливо|жутко|неловко|стыдно|обидно)|"
    r"я\s+(чувствую|чувствовал[а]?|ощущаю|ощущал[а]?|испытываю|испытывал[а]?|"
    r"боюсь|боялся|боялась|злюсь|злился|злилась|грущу|грустил[а]?|"
    r"рад[а]?|радовался|радовалась|счастлив[а]?|доволен|довольна|"
    r"обижен[а]?|обиделся|обиделась|расстроен[а]?|расстроился|расстроилась|"
    r"переживаю|переживал[а]?|нервничаю|нервничал[а]?|устал[а]?|устаю)|"
    r"у\s+меня\s+(тревога|страх|злость|радость|грусть|обида|стресс|паника))",
    re.IGNORECASE,
)

_EMOTION_PATTERNS_EN = re.compile(
    r"^(i\s+(feel|felt|am feeling|was feeling|sense|sensed|"
    r"fear|feared|hate|hated|love|loved|enjoy|enjoyed|"
    r"am\s+(angry|sad|happy|anxious|scared|worried|excited|depressed|"
    r"frustrated|proud|ashamed|guilty|lonely|confused))|"
    r"(i'm|i am)\s+(feeling|anxious|scared|happy|sad|angry|worried|excited))",
    re.IGNORECASE,
)

# ─── Паттерны: интерпретация / субъективное суждение ─────────────────────────
_INTERPRETATION_PATTERNS_RU = re.compile(
    r"^(мне\s+(кажется|показалось|кажется\s+что|думается)|"
    r"я\s+(думаю|думал[а]?|полагаю|полагал[а]?|считаю|считал[а]?|"
    r"подозреваю|подозревал[а]?|предполагаю|предполагал[а]?|"
    r"интерпретирую|понимаю\s+это|воспринимаю\s+это|"
    r"воспринял[а]?\s+это|решил[а]?\s+что)|"
    r"(наверное|наверно|похоже|возможно|скорее\s+всего|по-моему|по\s+моему|"
    r"по\s+всей\s+видимости|видимо|по\s+всей\s+вероятности)\s)",
    re.IGNORECASE,
)

_INTERPRETATION_PATTERNS_EN = re.compile(
    r"^(i\s+(think|thought|believe|believed|suppose|supposed|guess|"
    r"assume|assumed|suspect|suspected|interpret|perceive[d]?)|"
    r"(it\s+seems|it\s+seemed|seemingly|apparently|probably|"
    r"i\s+get\s+the\s+impression|my\s+impression\s+is))",
    re.IGNORECASE,
)

# ─── Паттерны: мнение / оценочное суждение ───────────────────────────────────
_OPINION_PATTERNS_RU = re.compile(
    r"^(по\s+моему\s+мнению|на\s+мой\s+взгляд|с\s+моей\s+точки\s+зрения|"
    r"я\s+(считаю\s+что|уверен[а]?\s+что|не\s+согласен|не\s+согласна|"
    r"согласен|согласна|одобряю|не\s+одобряю|поддерживаю|против)|"
    r"мне\s+(нравится|не\s+нравится|кажется\s+важным|важно\s+что)|"
    r"(хороший|плохой|отличный|ужасный|прекрасный|отвратительный)\s+)",
    re.IGNORECASE,
)

_OPINION_PATTERNS_EN = re.compile(
    r"^(in\s+my\s+opinion|from\s+my\s+perspective|i\s+believe\s+that|"
    r"i\s+think\s+that|i\s+(agree|disagree|support|oppose)|"
    r"(good|bad|great|terrible|awful|wonderful|horrible)\s+)",
    re.IGNORECASE,
)

# ─── Паттерны: цель / намерение ───────────────────────────────────────────────
_GOAL_PATTERNS_RU = re.compile(
    r"^(я\s+(хочу|хотел[а]?|планирую|планировал[а]?|намерен[а]?|"
    r"собираюсь|собирался|собиралась|буду|стремлюсь|стремился|"
    r"мечтаю|мечтал[а]?|решил[а]?\s+что\s+буду)|"
    r"моя\s+(цель|задача|мечта|план)\s+([\-–:]|\s)|"
    r"хочу\s+чтобы|нужно\s+чтобы\s+я)",
    re.IGNORECASE,
)

_GOAL_PATTERNS_EN = re.compile(
    r"^(i\s+(want\s+to|plan\s+to|intend\s+to|aim\s+to|"
    r"would\s+like\s+to|hope\s+to|need\s+to|must|will\s+try)|"
    r"my\s+(goal|aim|objective|plan|dream)\s+(is|was)|"
    r"(i'm|i\s+am)\s+going\s+to)",
    re.IGNORECASE,
)

# ─── Паттерны: предпочтение ───────────────────────────────────────────────────
_PREFERENCE_PATTERNS_RU = re.compile(
    r"^(я\s+(предпочитаю|предпочитал[а]?|люблю|любил[а]?|"
    r"обожаю|обожал[а]?|не\s+люблю|не\s+любил[а]?|"
    r"избегаю|избегал[а]?|нравится|не\s+нравится)|"
    r"мне\s+(нравится|не\s+нравится|по\s+душе|не\s+по\s+душе|"
    r"нравилось|не\s+нравилось))",
    re.IGNORECASE,
)

_PREFERENCE_PATTERNS_EN = re.compile(
    r"^(i\s+(prefer|love|like|enjoy|hate|avoid|dislike)|"
    r"(i\s+do(n't)?|i\s+don't)\s+(like|enjoy|prefer))",
    re.IGNORECASE,
)

# ─── Паттерны: личный опыт / воспоминание ────────────────────────────────────
_EXPERIENCE_PATTERNS_RU = re.compile(
    r"^(я\s+(помню|помнил[а]?|видел[а]?|слышал[а]?|узнал[а]?|"
    r"заметил[а]?|столкнулся|столкнулась|пережил[а]?|"
    r"испытал[а]?\s+на\s+себе|оказался|оказалась\s+в)|"
    r"однажды\s+я|когда\s+я\s+(был[а]?|ходил[а]?|делал[а]?)|"
    r"со\s+мной\s+(произошло|случилось|было)|"
    r"в\s+моей\s+жизни|из\s+моего\s+опыта)",
    re.IGNORECASE,
)

_EXPERIENCE_PATTERNS_EN = re.compile(
    r"^(i\s+(remember|recall|experienced|witnessed|noticed|"
    r"discovered|learned|found\s+out|realized|encountered|went\s+through)|"
    r"(once|when)\s+i\s+(was|went|did)|in\s+my\s+experience)",
    re.IGNORECASE,
)

# ─── Служебные заметки системы ───────────────────────────────────────────────
_SYSTEM_NOTE_PREFIXES = frozenset({
    "system:", "note:", "memo:", "internal:", "debug:", "log:",
    "система:", "заметка:", "служебно:", "внутреннее:", "примечание:",
})

# ─── Индикаторы внешнего источника (для WORLD_FACT-кандидатов) ───────────────
_EXTERNAL_SOURCE_PATTERNS = re.compile(
    r"^(согласно\s+(источнику|данным|исследованию|отчёту|документу|wikipedia|wiki)|"
    r"по\s+(данным|сообщению|информации|версии)|"
    r"из\s+(источника|документа|отчёта|статьи|книги)|"
    r"согласно\s+[A-ZА-ЯЁ]|  "  # согласно Имярек / согласно Организации
    r"according\s+to|based\s+on|per\s+the\s+report|"
    r"the\s+(study|research|data|report|document)\s+(shows|states|indicates|found))",
    re.IGNORECASE,
)

# ─── SOURCE → OriginType маппинг ────────────────────────────────────────────
_SOURCE_TO_ORIGIN: dict[str, str] = {
    # Ключевые слова в поле source → OriginType
    "user":         OriginType.USER_REPORTED,
    "chat":         OriginType.USER_REPORTED,
    "telegram":     OriginType.USER_REPORTED,
    "message":      OriginType.USER_REPORTED,
    "input":        OriginType.USER_REPORTED,
    "llm":          OriginType.LLM_OUTPUT,
    "gpt":          OriginType.LLM_OUTPUT,
    "gemini":       OriginType.LLM_OUTPUT,
    "claude":       OriginType.LLM_OUTPUT,
    "model":        OriginType.LLM_OUTPUT,
    "infer":        OriginType.DERIVED,
    "derived":      OriginType.DERIVED,
    "causal":       OriginType.DERIVED,
    "wsc":          OriginType.EXTERNAL,     # world_skills_core
    "wiki":         OriginType.EXTERNAL,
    "web":          OriginType.EXTERNAL,
    "file":         OriginType.EXTERNAL,
    "doc":          OriginType.EXTERNAL,
    "pdf":          OriginType.EXTERNAL,
    "api":          OriginType.EXTERNAL,
    "dataset":      OriginType.EXTERNAL,
    "seed":         OriginType.EXTERNAL,     # ring_zero/domain_seed
    "domain_seed":  OriginType.EXTERNAL,
    "ring_zero":    OriginType.EXTERNAL,
    "system":       OriginType.SYSTEM_GENERATED,
    "axiom":        OriginType.EXTERNAL,
    "physics":      OriginType.EXTERNAL,
    "chemistry":    OriginType.EXTERNAL,
    "biology":      OriginType.EXTERNAL,
    "math":         OriginType.EXTERNAL,
}


def _classify_origin_from_source(source: str | None) -> str:
    """Определить origin_type из поля source (без LLM)."""
    if not source:
        return OriginType.UNKNOWN
    s = source.lower().strip()
    for key, origin in _SOURCE_TO_ORIGIN.items():
        if key in s:
            return origin
    return OriginType.UNKNOWN


def _classify_claim_type(text: str, source: str | None = None) -> tuple[str, float]:
    """
    Определить claim_type по тексту (детерминированно, без LLM).
    Возвращает (claim_type, confidence_hint).
    """
    t = (text or "").strip()
    if not t:
        return ClaimType.UNKNOWN, 0.0

    # Служебные заметки системы
    tl = t.lower()
    for prefix in _SYSTEM_NOTE_PREFIXES:
        if tl.startswith(prefix):
            return ClaimType.SYSTEM_NOTE, 0.95

    # Эмоции — высокая специфичность
    if _EMOTION_PATTERNS_RU.search(t) or _EMOTION_PATTERNS_EN.search(t):
        return ClaimType.EMOTION, 0.9

    # Цель/намерение — до интерпретации (потому что «я хочу» однозначнее)
    if _GOAL_PATTERNS_RU.search(t) or _GOAL_PATTERNS_EN.search(t):
        return ClaimType.GOAL, 0.85

    # Предпочтение
    if _PREFERENCE_PATTERNS_RU.search(t) or _PREFERENCE_PATTERNS_EN.search(t):
        return ClaimType.PREFERENCE, 0.85

    # Мнение (до интерпретации — «по моему мнению» специфичнее «мне кажется»)
    if _OPINION_PATTERNS_RU.search(t) or _OPINION_PATTERNS_EN.search(t):
        return ClaimType.OPINION, 0.8

    # Интерпретация
    if _INTERPRETATION_PATTERNS_RU.search(t) or _INTERPRETATION_PATTERNS_EN.search(t):
        return ClaimType.INTERPRETATION, 0.8

    # Личный опыт
    if _EXPERIENCE_PATTERNS_RU.search(t) or _EXPERIENCE_PATTERNS_EN.search(t):
        return ClaimType.USER_EXPERIENCE, 0.8

    # Внешний источник явно указан в тексте → кандидат на WORLD_FACT
    if _EXTERNAL_SOURCE_PATTERNS.search(t):
        return ClaimType.WORLD_FACT, 0.75

    # Источник в поле source указывает на внешний/научный контент → WORLD_FACT
    if source:
        origin = _classify_origin_from_source(source)
        if origin == OriginType.EXTERNAL:
            return ClaimType.WORLD_FACT, 0.7
        if origin == OriginType.LLM_OUTPUT:
            return ClaimType.UNKNOWN, 0.4   # LLM сам не определяет модальность

    # Если утверждение начинается со «знакового» факта без личного местоимения
    # и нет признаков субъективности → осторожно WORLD_FACT
    first_word = t.split()[0].lower().rstrip(",.!?:") if t else ""
    subjective_ru = {"я", "мне", "моя", "мой", "моё", "меня", "мои", "у", "со"}
    subjective_en = {"i", "i'm", "i've", "i'd", "my", "me", "mine"}
    if first_word not in subjective_ru and first_word not in subjective_en:
        return ClaimType.WORLD_FACT, 0.55   # слабая уверенность

    return ClaimType.UNKNOWN, 0.3


def classify_claim(
    text: str,
    source: str | None = None,
    *,
    explicit_claim_type: str | None = None,
    explicit_origin_type: str | None = None,
) -> tuple[str, str, float]:
    """
    Главная функция классификации. Возвращает (claim_type, origin_type, confidence_hint).

    Args:
        text: текст утверждения (claim).
        source: значение поля source (помогает определить origin_type).
        explicit_claim_type: если передан — используется без переопределения.
        explicit_origin_type: если передан — используется без переопределения.

    Returns:
        (claim_type, origin_type, confidence_hint)
        confidence_hint: уверенность классификатора [0.0-1.0] — не confidence факта.

    Примеры:
        classify_claim("Мне было тревожно")
        → ("EMOTION", "UNKNOWN", 0.9)

        classify_claim("Я хочу выучить Python", source="user")
        → ("GOAL", "USER_REPORTED", 0.85)

        classify_claim("Вода кипит при 100°C", source="physics.thermo")
        → ("WORLD_FACT", "EXTERNAL", 0.7)

        classify_claim("Кажется, он меня не уважает", source="user_message")
        → ("INTERPRETATION", "USER_REPORTED", 0.8)
    """
    from core.validators import normalize_claim_type, normalize_origin_type

    # Явно переданные значения — наивысший приоритет
    if explicit_claim_type and explicit_claim_type in ClaimType.ALL:
        ct = explicit_claim_type
        ct_conf = 1.0
    else:
        ct, ct_conf = _classify_claim_type(text, source)

    if explicit_origin_type and explicit_origin_type in OriginType.ALL:
        ot = explicit_origin_type
    else:
        ot = _classify_origin_from_source(source)
        # Уточнение: если тип = USER_EXPERIENCE/EMOTION → почти точно USER_REPORTED
        if ot == OriginType.UNKNOWN and ct in (
            ClaimType.EMOTION, ClaimType.GOAL, ClaimType.PREFERENCE,
            ClaimType.OPINION, ClaimType.INTERPRETATION, ClaimType.USER_EXPERIENCE,
        ):
            ot = OriginType.USER_REPORTED

    return normalize_claim_type(ct), normalize_origin_type(ot), round(ct_conf, 3)


__all__ = [
    "classify_claim",
]
