"""
tests/test_smoke.py — Smoke Tests v8.5.1
=========================================
Быстрые тесты что система вообще стартует.
Запускать первыми — если они падают, всё остальное смысла нет.

Запуск:
    pytest tests/test_smoke.py -v --tb=short
"""


class TestImports:
    """Всё импортируется без ошибок."""

    def test_import_core_memory(self):
        from core.memory import store_fact
        assert store_fact is not None

    def test_import_core_pipeline(self):
        from core.pipeline import run
        assert run is not None

    def test_import_core_truth_gate(self):
        from core.truth_gate import TruthGate
        assert TruthGate is not None

    def test_import_core_mhi(self):
        from core.mhi import MHICalculator
        assert MHICalculator is not None

    def test_import_causal_graph(self):
        # FIX v8.5.2 (Claude audit): после разделения на FORWARD/BACKWARD
        # VALID_RELATION_TYPES = 21 (15 forward + 6 backward), не 15.
        # Проверяем оба множества отдельно — это часть API-контракта.
        from core.causal_graph import (
            BACKWARD_RELATION_TYPES,
            FORWARD_RELATION_TYPES,
            VALID_RELATION_TYPES,
        )
        assert len(FORWARD_RELATION_TYPES) == 15   # 12 оригинальных + 3 новых из v8.5.1
        assert len(BACKWARD_RELATION_TYPES) == 6   # caused_by, prevented_by, …
        assert len(VALID_RELATION_TYPES) == 21     # объединение для storage

    def test_import_living_context(self):
        from core.living_context import LivingContext
        assert LivingContext is not None

    def test_import_understanding_layer(self):
        from core.understanding_layer import UnderstandingLayer
        assert UnderstandingLayer is not None

    def test_import_audit_chain(self):
        from core.audit_chain import AuditChain
        assert AuditChain is not None

    def test_import_cache_coherence(self):
        from core.cache_coherence import CoherentCache
        assert CoherentCache is not None

    def test_import_confidence(self):
        from core.confidence import compute_confidence
        assert compute_confidence is not None

    def test_import_evidence(self):
        from core.evidence import EvidenceModel
        assert EvidenceModel is not None

    def test_import_facts_pack(self):
        from core.facts_pack import COGNITIVE_MODE_POLICIES
        assert "PRECISION" in COGNITIVE_MODE_POLICIES

    def test_import_validators(self):
        from core.validators import (
            validate_confidence,
        )
        assert validate_confidence is not None

    def test_import_errors(self):
        from core.errors import (
            FactNotFoundError,
            VelantrimError,
        )
        assert issubclass(FactNotFoundError, VelantrimError)

    def test_import_raw_memory(self):
        from core.raw_memory import RawMemoryStore
        assert RawMemoryStore is not None

    def test_import_text_utils(self):
        from utils.text_utils import tokenize
        assert tokenize is not None

    def test_import_file_parsers(self):
        from core.file_parsers import FileIngester
        assert FileIngester is not None

    def test_import_file_generators(self):
        from core.file_generators import FileExporter
        assert FileExporter is not None


class TestValidators:
    """Валидаторы работают корректно после фиксов."""

    def test_nan_confidence_rejected(self):
        """FIX v8.5.1: NaN больше не проходит."""
        import math

        from core.validators import validate_confidence
        ok, err = validate_confidence(math.nan)
        assert ok is False
        assert "NaN" in err

    def test_inf_confidence_rejected(self):
        import math

        from core.validators import validate_confidence
        ok, err = validate_confidence(math.inf)
        assert ok is False

    def test_whitespace_source_rejected(self):
        """FIX v8.5.1: whitespace-only source блокируется."""
        from core.validators import validate_source
        ok, err = validate_source("   ")
        assert ok is False
        assert "whitespace" in err.lower()

    def test_valid_confidence(self):
        from core.validators import validate_confidence
        ok, err = validate_confidence(0.85)
        assert ok is True
        assert err is None

    def test_valid_source(self):
        from core.validators import validate_source
        ok, err = validate_source("physics:textbook")
        assert ok is True


class TestRelationTypes:
    """
    FIX v8.5.1: все 15 forward-типов отношений разрешены.
    FIX v8.5.2 (Claude audit): после починки silent inverse drop система
    различает FORWARD_RELATION_TYPES (15 — что пользователь может передать
    в add_relation) и BACKWARD_RELATION_TYPES (6 — авто-генерируемые
    inverse-рёбра). VALID_RELATION_TYPES — объединение, что может хранить БД.
    """

    def test_forward_relation_types_count(self):
        """API-surface: пользователь может передавать ровно 15 типов."""
        from core.causal_graph import FORWARD_RELATION_TYPES
        assert len(FORWARD_RELATION_TYPES) == 15

    def test_backward_relation_types_count(self):
        """Storage-surface: 6 backward-типов создаются авто-инверсно."""
        from core.causal_graph import BACKWARD_RELATION_TYPES
        assert len(BACKWARD_RELATION_TYPES) == 6

    def test_valid_relation_types_count(self):
        """Storage-уровень: 15 forward + 6 backward = 21 в БД."""
        from core.causal_graph import VALID_RELATION_TYPES
        assert len(VALID_RELATION_TYPES) == 21

    def test_new_types_present(self):
        from core.causal_graph import FORWARD_RELATION_TYPES
        assert "becomes" in FORWARD_RELATION_TYPES
        assert "affords" in FORWARD_RELATION_TYPES
        assert "inhabited_by" in FORWARD_RELATION_TYPES

    def test_original_12_types_present(self):
        from core.causal_graph import FORWARD_RELATION_TYPES
        original = {
            "causes", "prevents", "requires", "enables",
            "implies", "contradicts", "generalizes", "specializes",
            "precedes", "follows", "composes", "analogous_to",
        }
        assert original.issubset(FORWARD_RELATION_TYPES)

    def test_backward_types_not_in_forward(self):
        """Архитектурный инвариант: backward-типы НЕ должны быть в forward."""
        from core.causal_graph import BACKWARD_RELATION_TYPES, FORWARD_RELATION_TYPES
        assert FORWARD_RELATION_TYPES.isdisjoint(BACKWARD_RELATION_TYPES)


class TestSleepWorkerFix:
    """FIX v8.5.1 Gemini: create_task сохраняет ссылку."""

    def test_bg_tasks_set_exists(self):
        """SleepTimeWorker имеет механизм хранения task references."""
        import inspect

        from core.sleep_time_worker import SleepTimeWorker
        src = inspect.getsource(SleepTimeWorker)
        assert "_bg_tasks" in src, "Нет _bg_tasks — GC может убить tasks"
        assert "add_done_callback" in src, "Нет cleanup callback"


class TestArchiveDepthFix:
    """FIX v8.5.1 Gemini Security: zip-bomb защита работает."""

    def test_archive_parser_creates_deeper_instance(self):
        """ArchiveParser создаёт новый инстанс с depth+1 для вложенных архивов."""
        import inspect

        from core.file_parsers.archive_parser import ArchiveParser
        src = inspect.getsource(ArchiveParser.parse)
        assert "_depth + 1" in src or "_depth+1" in src, \
            "Depth не увеличивается при рекурсии — zip-bomb уязвимость!"

    def test_max_depth_constant(self):
        from core.file_parsers.archive_parser import ArchiveParser
        assert ArchiveParser.MAX_DEPTH == 3


class TestModelSingletonFix:
    """FIX v8.5.1 Gemini Critical: _ModelSingleton thread-safe."""

    def test_has_lock(self):
        import inspect

        from core.file_parsers.base import _ModelSingleton
        src = inspect.getsource(_ModelSingleton)
        assert "threading.Lock" in src or "_lock" in src, \
            "_ModelSingleton без Lock — race condition при параллельных запросах!"

    def test_double_checked_locking(self):
        """Паттерн double-checked locking для производительности."""
        import inspect

        from core.file_parsers.base import _ModelSingleton
        src = inspect.getsource(_ModelSingleton.get)
        # Первая проверка без lock (быстрый путь)
        assert "if key in cls._instances" in src or "if key not in cls._instances" in src


class TestRawMemory:
    """L0 Immutable Raw Memory работает."""

    def test_raw_memory_store_basic(self):
        import sqlite3
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript("""
            CREATE TABLE l0_raw_memory (
                raw_id TEXT PRIMARY KEY,
                original_text TEXT NOT NULL,
                content_hash TEXT NOT NULL UNIQUE,
                source TEXT, source_url TEXT,
                source_type TEXT DEFAULT 'unknown',
                language TEXT DEFAULT 'unknown',
                char_count INTEGER DEFAULT 0,
                word_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                metadata TEXT DEFAULT '{}'
            );
            CREATE TABLE facts (
                fact_id TEXT PRIMARY KEY,
                claim TEXT,
                epistemic_state TEXT DEFAULT 'Observed',
                confidence REAL DEFAULT 0.8,
                derived_from TEXT
            );
            CREATE TABLE raw_derivation_chain (
                step_id TEXT PRIMARY KEY,
                raw_id TEXT, derived_fact_id TEXT,
                derivation_type TEXT DEFAULT 'direct',
                step_index INTEGER DEFAULT 0,
                transformation TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        from core.raw_memory import RawMemoryStore
        store = RawMemoryStore(conn)

        # Сохранить оригинал
        raw_id = store.store(
            "Дерево растёт в лесу. Птицы вьют гнёзда.",
            source="test.txt",
        )
        assert raw_id.startswith("raw_")

        # Дедупликация
        raw_id2 = store.store(
            "Дерево растёт в лесу. Птицы вьют гнёзда.",
            source="другой файл",
        )
        assert raw_id == raw_id2, "Дедупликация по SHA256 не работает"

        # Получение
        entry = store.get(raw_id)
        assert entry is not None
        assert "Дерево" in entry.original_text
