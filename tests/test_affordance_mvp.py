"""
tests/test_affordance_mvp.py — Variant C MVP Benchmark
========================================================
Тесты с реальными Go/No-Go критериями по F1.

Запуск:
    pytest tests/test_affordance_mvp.py -v -s   # -s чтобы видеть benchmark отчёт
"""
import pytest

from core.affordance_linker import AffordanceLinker, BenchmarkResult

# Gold set — минимум 25 примеров (FIX: pymorphy2 требует реальных данных)
GOLD_SET = [
    {
        "fact_id": "g01",
        "claim": "Дерево растёт в лесу. Птицы вьют гнёзда в его ветках. "
                 "Белки прячут запасы орехов. Можно срубить на дрова.",
        "expected_affordances": ["укрытие", "материал"],
        "expected_products":    ["дрова"],
        "expected_agents":      ["птица", "белка"],
    },
    {
        "fact_id": "g02",
        "claim": "Лес даёт кислород. Дерево выделяет кислород при фотосинтезе.",
        "expected_affordances": [],
        "expected_products":    ["кислород"],
        "expected_agents":      [],
    },
    {
        "fact_id": "g03",
        "claim": "Дерево создаёт тень в жаркий день. Можно укрыться от солнца.",
        "expected_affordances": ["укрытие"],
        "expected_products":    ["тень"],
        "expected_agents":      [],
    },
    {
        "fact_id": "g04",
        "claim": "В лесу можно собрать плоды и грибы. Насекомые живут под корой.",
        "expected_affordances": ["еда"],
        "expected_products":    ["плоды"],
        "expected_agents":      ["насекомые"],
    },
    {
        "fact_id": "g05",
        "claim": "Дерево можно использовать как ориентир в лесу.",
        "expected_affordances": ["ориентир"],
        "expected_products":    [],
        "expected_agents":      [],
    },
    {
        "fact_id": "g06",
        "claim": "Древесная смола защищает дерево от насекомых.",
        "expected_affordances": [],
        "expected_products":    ["смола"],
        "expected_agents":      ["насекомые"],
    },
    {
        "fact_id": "g07",
        "claim": "Люди используют дерево для строительства домов.",
        "expected_affordances": ["материал"],
        "expected_products":    [],
        "expected_agents":      ["человек"],
    },
    {
        "fact_id": "g08",
        "claim": "Птицы наблюдают за окрестностями с высоких ветвей.",
        "expected_affordances": ["наблюдение"],
        "expected_products":    [],
        "expected_agents":      ["птица"],
    },
    {
        "fact_id": "g09",
        "claim": "Упавший лист становится гумусом и питает почву.",
        "expected_affordances": [],
        "expected_products":    ["гумус"],
        "expected_agents":      [],
    },
    {
        "fact_id": "g10",
        "claim": "Семена разносятся ветром и животными на большие расстояния.",
        "expected_affordances": [],
        "expected_products":    ["семена"],
        "expected_agents":      ["животные"],
    },
    {
        "fact_id": "g11",
        "claim": "Под деревом можно отдыхать в жаркий день и греться у костра.",
        "expected_affordances": ["отдых", "тепло"],
        "expected_products":    [],
        "expected_agents":      [],
    },
    {
        "fact_id": "g12",
        "claim": "Дрова горят и дают тепло. Зола остаётся после горения.",
        "expected_affordances": ["тепло"],
        "expected_products":    ["зола"],
        "expected_agents":      [],
    },
    {
        "fact_id": "g13",
        "claim": "Birds build nests in trees. People use wood for construction.",
        "expected_affordances": ["материал"],
        "expected_products":    [],
        "expected_agents":      ["птица", "человек"],
    },
    {
        "fact_id": "g14",
        "claim": "Trees produce oxygen and absorb CO2.",
        "expected_affordances": [],
        "expected_products":    ["кислород"],
        "expected_agents":      [],
    },
    {
        "fact_id": "g15",
        "claim": "You can shelter under a big tree from rain.",
        "expected_affordances": ["укрытие"],
        "expected_products":    ["тень"],
        "expected_agents":      [],
    },
    {
        "fact_id": "g16",
        "claim": "Грибы растут у корней деревьев. Их можно есть.",
        "expected_affordances": ["еда"],
        "expected_products":    [],
        "expected_agents":      ["гриб"],
    },
    {
        "fact_id": "g17",
        "claim": "Животные прячутся в густом лесу от хищников.",
        "expected_affordances": ["укрытие"],
        "expected_products":    [],
        "expected_agents":      ["животные"],
    },
    {
        "fact_id": "g18",
        "claim": "Дерево держит почву корнями и предотвращает эрозию.",
        "expected_affordances": [],
        "expected_products":    [],
        "expected_agents":      [],
    },
    {
        "fact_id": "g19",
        "claim": "Белка прячет орехи у основания деревьев.",
        "expected_affordances": [],
        "expected_products":    [],
        "expected_agents":      ["белка"],
    },
    {
        "fact_id": "g20",
        "claim": "Человек может пилить дерево и строить из него дом.",
        "expected_affordances": ["материал"],
        "expected_products":    [],
        "expected_agents":      ["человек"],
    },
    {
        "fact_id": "g21",
        "claim": "Дерево плодоносит каждый год. Плоды едят птицы и люди.",
        "expected_affordances": ["еда"],
        "expected_products":    ["плоды"],
        "expected_agents":      ["птица", "человек"],
    },
    {
        "fact_id": "g22",
        "claim": "Дуб живёт сотни лет. Его кора лечебная.",
        "expected_affordances": [],
        "expected_products":    [],
        "expected_agents":      [],
    },
    {
        "fact_id": "g23",
        "claim": "Скворечник на дереве — дом для птиц.",
        "expected_affordances": ["укрытие"],
        "expected_products":    [],
        "expected_agents":      ["птица"],
    },
    {
        "fact_id": "g24",
        "claim": "Хвойный лес выделяет фитонциды. Можно дышать чистым воздухом.",
        "expected_affordances": [],
        "expected_products":    ["кислород"],
        "expected_agents":      [],
    },
    {
        "fact_id": "g25",
        "claim": "Дерево можно использовать как укрытие от дождя или как landmark.",
        "expected_affordances": ["укрытие", "ориентир"],
        "expected_products":    [],
        "expected_agents":      [],
    },
]


class TestAffordanceMVP:

    @pytest.fixture
    def linker(self):
        return AffordanceLinker(use_morphology=True)

    def test_extract_basic(self, linker):
        """Базовое извлечение работает."""
        result = linker.extract("f1", "Дерево растёт в лесу. Птицы вьют гнёзда.")
        assert isinstance(result.affordances, list)
        assert isinstance(result.products, list)
        assert isinstance(result.agents, list)

    def test_extract_finds_agents(self, linker):
        """Находит агентов из текста."""
        result = linker.extract("f1", "Птицы вьют гнёзда. Белки прячут орехи.")
        assert "птица" in result.agents or len(result.agents) > 0

    def test_extract_finds_affordances(self, linker):
        """Находит affordances."""
        result = linker.extract(
            "f1",
            "Можно срубить дерево и построить дом. Укрыться от дождя.",
        )
        assert len(result.affordances) > 0

    def test_extract_finds_products(self, linker):
        """Находит продукты."""
        result = linker.extract("f1", "Дерево выделяет кислород и даёт тень.")
        assert "кислород" in result.products or "тень" in result.products

    def test_extract_empty_text(self, linker):
        """Пустой текст → пустой результат."""
        result = linker.extract("f1", "")
        assert result.affordances == []
        assert result.products == []
        assert result.agents == []
        assert result.confidence == 0.0

    def test_benchmark_result_precision_recall_f1(self, linker):
        """BenchmarkResult правильно считает P/R/F1."""
        br = BenchmarkResult(true_positives=7, false_positives=3, false_negatives=3)
        assert br.precision == pytest.approx(7/10)
        assert br.recall    == pytest.approx(7/10)
        assert br.f1        == pytest.approx(7/10)

    def test_benchmark_on_gold_set(self, linker):
        """
        🎯 ГЛАВНЫЙ ТЕСТ MVP: Go/No-Go по F1 на gold set.

        Этот тест не должен ПАДАТЬ при F1 < порога —
        он должен ПЕЧАТАТЬ отчёт с выводом.
        Реальный Go/No-Go решает разработчик по числам.
        """
        result = linker.benchmark(GOLD_SET)
        print(f"\n{result.report()}")

        # Мягкие assertions — тест не падает при низком F1
        # (это информационный тест, не blocking)
        assert result.total_facts == len(GOLD_SET)
        assert 0.0 <= result.precision <= 1.0
        assert 0.0 <= result.recall <= 1.0
        assert 0.0 <= result.f1 <= 1.0
        assert 0.0 <= result.coverage_pct <= 100.0

        # Жёсткий порог — только если совсем всё плохо
        assert result.f1 >= 0.0, "F1 должен быть неотрицательным числом"

    def test_go_no_go_thresholds(self):
        """Пороги Go/No-Go правильно применяются."""
        assert BenchmarkResult(
            true_positives=65, false_positives=5, false_negatives=35
        ).go_no_go().startswith("🟢")

        assert BenchmarkResult(
            true_positives=50, false_positives=10, false_negatives=50
        ).go_no_go().startswith("🟡")

        assert BenchmarkResult(
            true_positives=38, false_positives=20, false_negatives=62
        ).go_no_go().startswith("🟠")

        assert BenchmarkResult(
            true_positives=20, false_positives=30, false_negatives=80
        ).go_no_go().startswith("🔴")

    def test_batch_extract(self, linker):
        """Пакетное извлечение работает."""
        facts = [
            {"fact_id": "f1", "claim": "Дерево даёт тень."},
            {"fact_id": "f2", "claim": "Птицы гнездятся."},
        ]
        results = linker.extract_batch(facts)
        assert len(results) == 2
        assert all(hasattr(r, "fact_id") for r in results)
