"""
🏛️ core/essence_facade/__init__.py — Essence Engine Facade (V8.7 Titan)

Фасад-слой понимания. Агрегирует существующие модули без переноса файлов.
Ни один файл не перемещён — только импорты-обёртки.

Правила фасада (канон):
    1. НЕ пишет FACT. Только предлагает гипотезы через TruthGate.
    2. Все выводы сопровождаются WhyTrace.
    3. Без LLM в детерминированном контуре. Креативный синтез — отдельный слой.
    4. Essence Engine НЕ заменяет TruthGate. Он работает ПОСЛЕ верификации.

"""

from core.essence_facade.gist import (
    Gist,
    GistSynthesizer,
    extract_gist,
    get_gist_synthesizer,
)

from core.essence_facade.situation import (
    SituationModel,
    build_situation,
    get_situation_model,
)

from core.essence_facade.goal_frame import (
    get_goal_frame_bridge,
)

from core.essence_facade.mirror import (
    get_mirror_bridge,
)

from core.essence_facade.causal import (
    get_causal_bridge,
)

from core.essence_facade.observer_bridge import (
    get_observer_bridge,
)

# V8.7: реэкспорт из core/essence.py (плоский файл, чтобы тесты не ломались)
from core.essence import (  # type: ignore[attr-defined]
    Essence,
    MeaningRole,
    WhyTrace,
    compose_essence,
    is_essence_enabled,
)

__all__ = [
    "Gist",
    "GistSynthesizer",
    "SituationModel",
    "build_situation",
    "extract_gist",
    "get_causal_bridge",
    "get_gist_synthesizer",
    "get_goal_frame_bridge",
    "get_mirror_bridge",
    "get_observer_bridge",
    "get_situation_model",
]
