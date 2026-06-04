"""
Тесты для file_parsers — интеграция с Velantrim.

Covers:
  - ParseResult.to_fact_dict(): blake3 fallback, source_override, bi-temporal hint
  - FileIngester: ingest несуществующего файла, to_fact с source_override, get_stats
  - ParseResult конвертация в fact формат совместимый с store_fact()

Примечание (v8.6 cleanup): классы тестов на KnowledgeIngesterV5
(_detect_trusted_source / _write_fact_to_esm / sleep-worker notify) удалены —
модуль был убран при ARCH MIGRATION v8.5.1, эта логика переехала в pipeline/server.
История доступна в git (версия файла до cleanup), если потребуется восстановить.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── Фикстуры ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_parse_result():
    """Простой ParseResult для тестов."""
    from core.file_parsers.base import ParseResult
    return ParseResult(
        file_path="/data/docs/research.pdf",
        file_type="pdf",
        extracted_text="Velantrim использует ESM для управления фактами.",
        extraction_method="PyPDF2 (fallback)",
        provenance={
            "prov:wasGeneratedBy": "PDFParser",
            "prov:generatedAtTime": "2026-05-11T10:00:00+00:00",
        },
    )


@pytest.fixture
def sample_parse_result_with_essence():
    """ParseResult с Essence."""
    from core.file_parsers.base import ParseResult
    return ParseResult(
        file_path="/data/seed/axioms.md",
        file_type="text",
        extracted_text="Graph = Truth. ESM управляет всеми фактами.",
        extraction_method="Markdown parser",
        essence={
            "Суть": "Граф является единственным источником истины в Velantrim",
            "Тип знания": "ESTABLISHED",
            "Уверенность": 0.95,
        },
    )


@pytest.fixture
def ingester():
    """Чистый FileIngester."""
    from core.file_parsers.file_ingester import FileIngester
    return FileIngester()


# ─── ParseResult.to_fact_dict() ───────────────────────────────────────────────

class TestParseResultToFactDict:

    def test_fact_id_generated_without_error(self, sample_parse_result):
        """to_fact_dict() работает даже если blake3 не установлен (fallback sha256)."""
        fact = sample_parse_result.to_fact_dict()
        assert "fact_id" in fact
        assert fact["fact_id"].startswith("pdf_")
        assert len(fact["fact_id"]) > 4

    def test_epistemic_state_is_observed(self, sample_parse_result):
        """I50: начальное состояние всегда Observed."""
        fact = sample_parse_result.to_fact_dict()
        assert fact["epistemic_state"] == "Observed"

    def test_source_default_includes_file_path(self, sample_parse_result):
        """Без override source содержит путь к файлу."""
        fact = sample_parse_result.to_fact_dict()
        assert "file_parser:" in fact["source"]
        assert "research.pdf" in fact["source"]

    def test_source_override_domain_seed(self, sample_parse_result):
        """source_override='domain_seed' передаётся в факт."""
        fact = sample_parse_result.to_fact_dict(source_override="domain_seed")
        assert fact["source"] == "domain_seed"

    def test_source_override_ring_zero(self, sample_parse_result):
        """source_override='ring_zero' передаётся в факт."""
        fact = sample_parse_result.to_fact_dict(source_override="ring_zero")
        assert fact["source"] == "ring_zero"

    def test_claim_from_extracted_text(self, sample_parse_result):
        """Без Essence claim берётся из extracted_text."""
        fact = sample_parse_result.to_fact_dict()
        assert "ESM" in fact["claim"] or "Velantrim" in fact["claim"]
        assert fact["confidence"] < 0.85  # без Essence — ниже

    def test_claim_from_essence(self, sample_parse_result_with_essence):
        """С Essence claim берётся из essence['Суть']."""
        fact = sample_parse_result_with_essence.to_fact_dict()
        assert "источник" in fact["claim"].lower() or "граф" in fact["claim"].lower()
        assert fact["confidence"] == 0.85

    def test_no_bitemporal_fields_in_fact_dict(self, sample_parse_result):
        """Bi-temporal поля НЕ выставляются в to_fact_dict — это задача store_fact()."""
        fact = sample_parse_result.to_fact_dict()
        assert "t_event_valid_start" not in fact
        assert "t_ingestion_start"   not in fact

    def test_metadata_contains_file_info(self, sample_parse_result):
        """metadata содержит file_path, file_type, extraction_method."""
        fact = sample_parse_result.to_fact_dict()
        meta = fact["metadata"]
        assert meta["file_path"]         == "/data/docs/research.pdf"
        assert meta["file_type"]         == "pdf"
        assert meta["extraction_method"] == "PyPDF2 (fallback)"

    def test_empty_file_gets_placeholder_claim(self):
        """Пустой файл без текста и Essence → placeholder claim."""
        from core.file_parsers.base import ParseResult
        result = ParseResult(
            file_path="/tmp/empty.pdf",
            file_type="pdf",
            extracted_text="",
        )
        fact = result.to_fact_dict()
        assert "empty.pdf" in fact["claim"] or fact["claim"].startswith("[")
        assert fact["confidence"] < 0.65


# ─── FileIngester ─────────────────────────────────────────────────────────────

class TestFileIngester:

    def test_ingest_nonexistent_returns_error(self, ingester):
        """Несуществующий файл → ParseResult с error, не исключение."""
        result = ingester.ingest("/nonexistent/file.pdf")
        assert result.error is not None
        assert result.file_type == "unknown"

    def test_supported_formats_not_empty(self, ingester):
        """get_supported_formats() возвращает непустой словарь."""
        formats = ingester.get_supported_formats()
        assert len(formats) > 0
        assert "pdf"   in formats
        assert "audio" in formats
        assert "image" in formats

    def test_to_fact_with_source_override(self, ingester, sample_parse_result):
        """FileIngester.to_fact() передаёт source_override в ParseResult."""
        fact = ingester.to_fact(sample_parse_result, source_override="domain_seed")
        assert fact["source"] == "domain_seed"

    def test_to_facts_batch(self, ingester, sample_parse_result):
        """to_facts() конвертирует список."""
        facts = ingester.to_facts(
            [sample_parse_result, sample_parse_result],
            source_override="domain_seed",
        )
        assert len(facts) == 2
        assert all(f["source"] == "domain_seed" for f in facts)

    def test_get_stats_initial(self, ingester):
        """Начальная статистика — нули."""
        stats = ingester.get_stats()
        assert stats["processed"] == 0
        assert stats["errors"]    == 0


# ─── Совместимость с core.memory ─────────────────────────────────────────────

class TestCoreMemoryCompatibility:

    def test_fact_dict_compatible_with_store_fact_signature(
        self, sample_parse_result
    ):
        """
        Факт из to_fact_dict() совместим с сигнатурой store_fact().
        Проверяем что все обязательные поля присутствуют.
        """
        fact = sample_parse_result.to_fact_dict()

        required_fields = ["fact_id", "claim", "source", "confidence", "epistemic_state"]
        for field in required_fields:
            assert field in fact, f"Обязательное поле '{field}' отсутствует"

        # Типы полей
        assert isinstance(fact["fact_id"],         str)
        assert isinstance(fact["claim"],            str)
        assert isinstance(fact["source"],           str)
        assert isinstance(fact["confidence"],       float)
        assert isinstance(fact["epistemic_state"],  str)
        assert fact["epistemic_state"] == "Observed"
        assert 0.0 <= fact["confidence"] <= 1.0

    def test_domain_seed_source_protected_by_i98(self, sample_parse_result):
        """
        Факт с source='domain_seed' будет защищён I98 TRUSTED_SOURCES.
        Здесь проверяем что источник правильно выставляется.
        """
        fact = sample_parse_result.to_fact_dict(source_override="domain_seed")
        assert fact["source"] == "domain_seed"
        # При передаче в real store_fact() → transition_esm("Contradicted") → TrustedSourceError
        # Это нормальное поведение системы (I98)
