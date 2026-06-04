"""
tests/test_file_parsers/test_basic.py
========================================
Базовые тесты для file_parsers v2.0:
- Базовые компоненты (ParseResult, ParserRegistry, _ModelSingleton)
- Text/JSON/CSV parsers (без зависимостей)
- FileIngester orchestrator
- ENV configuration
- Regression тесты для audit-фиксов
"""

import json
import os

import pytest

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def text_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello Velantrim\nЭто тестовый файл.", encoding="utf-8")
    return str(f)


@pytest.fixture
def json_file(tmp_path):
    f = tmp_path / "test.json"
    f.write_text(
        json.dumps({"key": "value", "list": [1, 2, 3]}, ensure_ascii=False),
        encoding="utf-8",
    )
    return str(f)


@pytest.fixture
def jsonl_file(tmp_path):
    f = tmp_path / "test.jsonl"
    lines = [
        json.dumps({"id": 1, "name": "первый"}),
        json.dumps({"id": 2, "name": "второй"}),
        json.dumps({"id": 3, "name": "третий"}),
    ]
    f.write_text("\n".join(lines), encoding="utf-8")
    return str(f)


@pytest.fixture
def csv_file(tmp_path):
    f = tmp_path / "test.csv"
    f.write_text(
        "name,age,city\nAlice,30,Moscow\nBob,25,London\n",
        encoding="utf-8",
    )
    return str(f)


@pytest.fixture
def markdown_file(tmp_path):
    f = tmp_path / "test.md"
    f.write_text(
        "---\ntitle: Test\nauthor: Velantrim\n---\n\n"
        "# Заголовок\n\nЭто параграф.\n\n## Подзаголовок\n",
        encoding="utf-8",
    )
    return str(f)


@pytest.fixture
def yaml_file(tmp_path):
    f = tmp_path / "test.yaml"
    f.write_text(
        "key: value\nlist:\n  - item1\n  - item2\nnested:\n  inner: data\n",
        encoding="utf-8",
    )
    return str(f)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Базовые компоненты (base.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestBase:

    def test_parse_result_to_fact_dict(self):
        """ParseResult.to_fact_dict() возвращает правильный формат."""
        from core.file_parsers.base import ParseResult

        result = ParseResult(
            file_path="/tmp/test.pdf",
            file_type="pdf",
            extracted_text="Some content",
        )
        fact = result.to_fact_dict()

        assert "fact_id" in fact
        assert fact["fact_id"].startswith("pdf_")
        assert "claim" in fact
        assert "confidence" in fact
        assert fact["source"] == "file_parser:test.pdf"
        assert fact["epistemic_state"] == "Observed"
        assert "metadata" in fact

    def test_parse_result_sha256_not_blake3(self):
        """v2.0 fix: используется SHA256 (есть в stdlib), а не BLAKE3."""
        from core.file_parsers.base import ParseResult

        result = ParseResult(
            file_path="/tmp/test.pdf",
            file_type="pdf",
            extracted_text="content",
        )
        # Не должно быть ImportError на blake3
        fact = result.to_fact_dict()
        # fact_id должен иметь хеш в нужной длине
        assert len(fact["fact_id"]) > 10

    def test_confidence_calibration(self):
        """v2.0: confidence учитывает наличие essence и warnings."""
        from core.file_parsers.base import ParseResult

        # Чистый success
        r1 = ParseResult(
            file_path="x", file_type="pdf",
            extracted_text="text",
            essence={"Суть": "test"},
        )
        # С warnings
        r2 = ParseResult(
            file_path="x", file_type="pdf",
            extracted_text="text",
            essence={"Суть": "test"},
            warnings=["partial_failure"],
        )
        # Без essence
        r3 = ParseResult(file_path="x", file_type="pdf", extracted_text="text")

        # С ошибкой
        r4 = ParseResult(file_path="x", file_type="pdf", error="failed")

        f1 = r1.to_fact_dict()
        f2 = r2.to_fact_dict()
        f3 = r3.to_fact_dict()
        f4 = r4.to_fact_dict()

        assert f1["confidence"] > f2["confidence"], "Warnings должны снижать confidence"
        assert f2["confidence"] > f3["confidence"], "Essence повышает confidence"
        assert f4["confidence"] == 0.0, "Error → confidence 0"

    def test_parser_registry_singleton(self):
        """ParserRegistry — синглтон."""
        from core.file_parsers.base import ParserRegistry
        r1 = ParserRegistry()
        r2 = ParserRegistry()
        assert r1 is r2

    def test_model_singleton(self):
        """_ModelSingleton lazy-loaded, грузит модель один раз."""
        from core.file_parsers.base import _ModelSingleton

        call_count = {"n": 0}
        def loader():
            call_count["n"] += 1
            return "loaded_model"

        # Первый вызов — загрузка
        m1 = _ModelSingleton.get("test_key", loader)
        assert m1 == "loaded_model"
        assert call_count["n"] == 1

        # Второй вызов — из кеша
        m2 = _ModelSingleton.get("test_key", loader)
        assert m2 == "loaded_model"
        assert call_count["n"] == 1, "Loader не должен вызываться повторно"

        # Очистка
        _ModelSingleton.clear("test_key")
        _ModelSingleton.get("test_key", loader)
        assert call_count["n"] == 2

    def test_max_file_size_protection(self, tmp_path):
        """v2.0 audit fix: файлы > MAX_FILE_SIZE → ошибка вместо OOM."""
        from core.file_parsers.text_parser import TextParser

        # Создаём parser с маленьким лимитом для теста
        parser = TextParser()
        parser.max_file_size_bytes = 100   # 100 bytes only

        big_file = tmp_path / "big.txt"
        big_file.write_text("x" * 1000)   # 1000 bytes

        result = parser.parse(str(big_file))
        assert result.error is not None
        assert "слишком большой" in result.error.lower() or "too large" in result.error.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TextParser
# ═══════════════════════════════════════════════════════════════════════════════

class TestTextParser:

    def test_plain_text(self, text_file):
        from core.file_parsers.text_parser import TextParser
        parser = TextParser()
        result = parser.parse(text_file)

        assert result.error is None
        assert "Hello Velantrim" in result.extracted_text
        assert "тестовый" in result.extracted_text
        assert result.file_type == "text"
        assert result.word_count > 0

    def test_json(self, json_file):
        from core.file_parsers.text_parser import TextParser
        parser = TextParser()
        result = parser.parse(json_file)

        assert result.error is None
        assert "value" in result.extracted_text
        assert result.structured_data.get("format") == "json"
        assert result.structured_data.get("data", {}).get("key") == "value"

    def test_jsonl(self, jsonl_file):
        from core.file_parsers.text_parser import TextParser
        parser = TextParser()
        result = parser.parse(jsonl_file)

        assert result.error is None
        assert result.structured_data.get("format") == "jsonl"
        assert result.structured_data.get("row_count") == 3

    def test_markdown_with_frontmatter(self, markdown_file):
        from core.file_parsers.text_parser import TextParser
        parser = TextParser()
        result = parser.parse(markdown_file)

        assert result.error is None
        # Frontmatter должен быть extracted (если PyYAML установлен)
        if result.structured_data.get("frontmatter"):
            fm = result.structured_data["frontmatter"]
            assert isinstance(fm, dict)
        # Headers должны быть найдены
        headers = result.structured_data.get("headers", [])
        assert len(headers) >= 1

    def test_yaml_safe_load(self, yaml_file):
        """v2.0 security fix: yaml.safe_load (не unsafe load)."""
        pytest.importorskip("yaml")
        from core.file_parsers.text_parser import TextParser
        parser = TextParser()
        result = parser.parse(yaml_file)

        assert result.error is None
        # Safe-loaded YAML — это dict
        data = result.structured_data.get("data")
        if data is not None:
            assert isinstance(data, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CSVParser
# ═══════════════════════════════════════════════════════════════════════════════

class TestCSVParser:

    def test_csv_basic(self, csv_file):
        from core.file_parsers.csv_parser import CSVParser
        parser = CSVParser()
        result = parser.parse(csv_file)

        assert result.error is None
        assert "Alice" in result.extracted_text or "Alice" in str(result.structured_data)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FileIngester orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

class TestFileIngester:

    def test_ingest_text(self, text_file):
        from core.file_parsers import FileIngester
        ingester = FileIngester()
        result = ingester.ingest(text_file)

        assert result.error is None
        assert result.file_type == "text"
        assert "Hello Velantrim" in result.extracted_text

    def test_ingest_unknown_extension(self, tmp_path):
        from core.file_parsers import FileIngester
        f = tmp_path / "test.xyz"
        f.write_text("content", encoding="utf-8")
        ingester = FileIngester()
        result = ingester.ingest(str(f))
        # Должен fallback на text parser ИЛИ дать ошибку
        # (зависит от реализации)
        assert result.error is None or "xyz" in result.error

    def test_ingest_non_existent(self):
        from core.file_parsers import FileIngester
        result = FileIngester().ingest("/tmp/does_not_exist_xyzzy.txt")
        assert result.error is not None
        assert "не найден" in result.error.lower() or "not found" in result.error.lower()

    def test_ingest_directory(self, tmp_path):
        """ingest_directory находит все поддерживаемые файлы."""
        # Создаём несколько файлов
        (tmp_path / "a.txt").write_text("file A", encoding="utf-8")
        (tmp_path / "b.md").write_text("# file B", encoding="utf-8")
        (tmp_path / "c.json").write_text('{"k": "v"}', encoding="utf-8")
        # И один неподдерживаемый (но он попадёт в text fallback)
        (tmp_path / "d.unknown_ext").write_text("ignored", encoding="utf-8")

        from core.file_parsers import FileIngester
        results = FileIngester().ingest_directory(str(tmp_path), recursive=False)

        # Минимум 3 поддерживаемых
        successful = [r for r in results if not r.error]
        assert len(successful) >= 3

    def test_ingest_directory_parallel(self, tmp_path):
        """Parallel processing работает."""
        for i in range(5):
            (tmp_path / f"file_{i}.txt").write_text(f"content {i}", encoding="utf-8")

        from core.file_parsers import FileIngester
        results = FileIngester().ingest_directory(
            str(tmp_path), workers=2,
        )
        assert len(results) >= 5
        # Все должны иметь file_path
        for r in results:
            assert r.file_path

    def test_to_fact_conversion(self, text_file):
        """ParseResult → store_fact compatible dict."""
        from core.file_parsers import FileIngester
        ingester = FileIngester()
        result = ingester.ingest(text_file)
        fact = ingester.to_fact(result)

        # Проверяем формат под core.memory.store_fact
        assert "fact_id" in fact
        assert "claim" in fact
        assert "source" in fact
        assert "confidence" in fact
        assert "epistemic_state" in fact
        assert isinstance(fact["confidence"], float)
        assert 0 <= fact["confidence"] <= 1

    def test_stats_tracking(self, text_file, csv_file):
        """Статистика обновляется."""
        from core.file_parsers import FileIngester
        ingester = FileIngester()
        ingester.ingest(text_file)
        ingester.ingest(csv_file)

        stats = ingester.get_stats()
        assert stats["processed"] == 2
        assert stats["total_bytes"] > 0
        assert stats["total_time_ms"] >= 0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ENV конфигурация
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnvConfig:

    def test_disable_parsers(self, monkeypatch):
        """VELANTRIM_DISABLE_PARSERS работает."""
        monkeypatch.setenv("VELANTRIM_DISABLE_PARSERS", "video,audio")

        # Перезагружаем модуль чтобы env подхватился
        import importlib

        import core.file_parsers.base as base_mod
        import core.file_parsers.file_ingester as ing_mod
        # Сбрасываем singleton
        base_mod.ParserRegistry._instance = None
        base_mod.ParserRegistry._parsers = {}
        base_mod.ParserRegistry._extension_map = {}
        base_mod.ParserRegistry._initialized = {}

        importlib.reload(ing_mod)
        ingester = ing_mod.FileIngester()

        # video и audio расширения не должны быть зарегистрированы
        exts = ingester.registry.supported_extensions()
        assert ".mp4" not in exts
        assert ".mp3" not in exts
        # А text — должен
        assert ".txt" in exts


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Round-trip: parse → store → export (интеграция с file_generators)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRoundTrip:
    """
    Главная фишка Этапа 1+2: parser и generator зеркальные.
    Файл → факт → файл должен сохранить главное содержание.
    """

    def test_text_parse_to_html_export(self, text_file, tmp_path):
        """TXT → fact → HTML report — пайплайн закрывается."""
        from core.file_generators import FileExporter
        from core.file_parsers import FileIngester

        # 1. Парсим
        ingester = FileIngester()
        parse_result = ingester.ingest(text_file)
        fact = ingester.to_fact(parse_result)

        # 2. Экспортируем
        exporter = FileExporter()
        output = str(tmp_path / "report.html")
        gen_result = exporter.export_facts(
            [fact], output, title="Round-trip test",
        )

        assert gen_result.error is None
        assert os.path.exists(output)

        # 3. Содержимое должно содержать claim
        with open(output, encoding="utf-8") as f:
            content = f.read()
        # Часть оригинала должна сохраниться
        assert fact["claim"][:30] in content or "Velantrim" in content
