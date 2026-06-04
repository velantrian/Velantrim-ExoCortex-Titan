"""
🌱 core/affordance_linker.py — Variant C MVP AffordanceLinker
==============================================================
Автоматически извлекает affordances из текста фактов и привязывает их к фактам.

MVP v2: rule-based + опциональная лемматизация pymorphy2.
Без spaCy, без ML, без Kuzu — только SQLite и Python.

Принцип Variant C: сначала числа, потом усложнение.
Go/No-Go критерии по F1:
  F1 ≥ 0.38 → продолжаем
  F1 < 0.38 → добавить pymorphy2, повторить
  F1 < 0.38 после pymorphy2 → нужен spaCy (Patch 14b)

Спек: VARIANT_C_MVP_LIVING_CONTEXT-1.md
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── Rule-based словари ─────────────────────────────────────────────────────────

# Ключевые слова → affordance категория
AFFORDANCE_KEYWORDS: dict[str, list[str]] = {
    "укрытие":    ["укрыться", "спрятаться", "защититься", "shadow", "shelter"],
    "материал":   ["срубить", "пилить", "строить", "использовать", "сделать", "cut", "build"],
    "еда":        ["есть", "съесть", "питаться", "harvest", "eat", "собрать"],
    "тепло":      ["греться", "согреться", "разжечь", "тепло", "warm"],
    "наблюдение": ["смотреть", "наблюдать", "watch", "observe", "видеть"],
    "отдых":      ["отдыхать", "сидеть", "лечь", "rest", "relax"],
    "ориентир":   ["ориентироваться", "найти", "navigate", "landmark"],
}

# Ключевые слова → продукты (что производит)
PRODUCT_KEYWORDS: dict[str, list[str]] = {
    "кислород":   ["кислород", "oxygen", "воздух"],
    "дрова":      ["дрова", "wood", "firewood", "древесина"],
    "тень":       ["тень", "shade", "shadow"],
    "плоды":      ["плоды", "фрукты", "плод", "fruit", "ягода"],
    "зола":       ["зола", "ash", "пепел"],
    "гумус":      ["гумус", "humus", "перегной"],
    "семена":     ["семена", "семя", "seed", "seeds"],
    "смола":      ["смола", "resin", "сок"],
}

# Ключевые слова → агенты (кто использует)
AGENT_KEYWORDS: dict[str, list[str]] = {
    "птица":   ["птица", "птицы", "bird", "birds", "воробей", "скворец"],
    "белка":   ["белка", "белки", "squirrel"],
    "человек": ["человек", "люди", "человека", "people", "person"],
    "гриб":    ["гриб", "грибы", "mushroom", "fungi"],
    "насекомые": ["насекомые", "жук", "бабочка", "insect", "bug"],
    "животные": ["животные", "звери", "animals"],
}


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class AffordanceResult:
    """Результат извлечения affordances из одного факта."""
    fact_id:     str
    affordances: list[str] = field(default_factory=list)
    products:    list[str] = field(default_factory=list)
    agents:      list[str] = field(default_factory=list)
    confidence:  float = 0.0

    def to_dict(self) -> dict:
        return {
            "fact_id":     self.fact_id,
            "affordances": self.affordances,
            "products":    self.products,
            "agents":      self.agents,
            "confidence":  self.confidence,
        }


@dataclass
class BenchmarkResult:
    """Результаты MVP benchmark по Go/No-Go критериям."""
    true_positives:  int = 0
    false_positives: int = 0
    false_negatives: int = 0
    total_facts:     int = 0
    coverage:        int = 0    # сколько фактов получили хоть что-то

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def coverage_pct(self) -> float:
        return self.coverage / self.total_facts * 100 if self.total_facts > 0 else 0.0

    def go_no_go(self) -> str:
        """Оценка по критериям Variant C MVP."""
        if self.f1 >= 0.65:
            return "🟢 ОТЛИЧНО — переходим к Patch 14b Full"
        if self.f1 >= 0.50:
            return "🟡 ХОРОШО — можно расширять"
        if self.f1 >= 0.38:
            return "🟠 МИНИМУМ — добавить pymorphy2 для улучшения"
        return "🔴 НИЖЕ ПОРОГА — добавить pymorphy2, если не поможет → spaCy"

    def report(self) -> str:
        lines = [
            "═" * 50,
            "📊 Variant C MVP Benchmark Results",
            "═" * 50,
            f"  Precision:  {self.precision:.3f}",
            f"  Recall:     {self.recall:.3f}",
            f"  F1:         {self.f1:.3f}",
            f"  Coverage:   {self.coverage_pct:.1f}%",
            f"  TP: {self.true_positives}  FP: {self.false_positives}  FN: {self.false_negatives}",
            "",
            f"  Go/No-Go: {self.go_no_go()}",
            "═" * 50,
        ]
        return "\n".join(lines)


# ── AffordanceLinker ──────────────────────────────────────────────────────────

class AffordanceLinker:
    """
    Rule-based извлечение affordances из текста фактов.

    v1 (MVP): словари + опциональная лемматизация.
    v2 (Patch 14b): spaCy + ML.
    """

    def __init__(self, use_morphology: bool = True) -> None:
        """
        Args:
            use_morphology: использовать pymorphy2 если доступен.
        """
        self._morph = None
        if use_morphology:
            try:
                import pymorphy2
                self._morph = pymorphy2.MorphAnalyzer()
            except ImportError:
                pass  # pymorphy2 не установлен — работаем без лемматизации

    def extract(self, fact_id: str, text: str) -> AffordanceResult:
        """
        Извлечь affordances из текста одного факта.

        Args:
            fact_id: идентификатор факта
            text: текст клейма (claim)

        Returns:
            AffordanceResult с affordances, products, agents
        """
        if not text:
            return AffordanceResult(fact_id=fact_id)

        tokens = self._tokenize(text)
        token_set = set(tokens)

        affordances: list[str] = []
        products:    list[str] = []
        agents:      list[str] = []

        # Ищем affordances
        for canonical, keywords in AFFORDANCE_KEYWORDS.items():
            for kw in keywords:
                kw_lemma = self._lemmatize(kw)
                if any(kw_lemma == t or kw == t for t in token_set):
                    if canonical not in affordances:
                        affordances.append(canonical)
                    break

        # Ищем products
        for canonical, keywords in PRODUCT_KEYWORDS.items():
            for kw in keywords:
                kw_lemma = self._lemmatize(kw)
                if any(kw_lemma == t or kw == t for t in token_set):
                    if canonical not in products:
                        products.append(canonical)
                    break

        # Ищем agents
        for canonical, keywords in AGENT_KEYWORDS.items():
            for kw in keywords:
                kw_lemma = self._lemmatize(kw)
                if any(kw_lemma == t or kw == t for t in token_set):
                    if canonical not in agents:
                        agents.append(canonical)
                    break

        # Confidence зависит от полноты извлечения
        total_found = len(affordances) + len(products) + len(agents)
        confidence = min(0.9, 0.5 + total_found * 0.1) if total_found > 0 else 0.0

        return AffordanceResult(
            fact_id=fact_id,
            affordances=affordances,
            products=products,
            agents=agents,
            confidence=confidence,
        )

    def extract_batch(
        self,
        facts: list[dict],
        text_field: str = "claim",
    ) -> list[AffordanceResult]:
        """
        Пакетное извлечение для списка фактов.

        Args:
            facts: список dict с ключами fact_id и text_field
            text_field: имя поля с текстом (default: "claim")
        """
        return [
            self.extract(f["fact_id"], f.get(text_field, ""))
            for f in facts
        ]

    def benchmark(
        self,
        gold_set: list[dict],
        text_field: str = "claim",
    ) -> BenchmarkResult:
        """
        Запустить benchmark по gold set.

        Gold set format:
            [
                {
                    "fact_id": "f1",
                    "claim": "Дерево растёт в лесу. Птицы вьют гнёзда.",
                    "expected_affordances": ["укрытие", "материал"],
                    "expected_products": ["кислород", "тень"],
                    "expected_agents": ["птица"],
                },
                ...
            ]

        FIX (Perplexity): F1 метрика, а не простая точность.
        """
        result = BenchmarkResult(total_facts=len(gold_set))

        for item in gold_set:
            extracted = self.extract(item["fact_id"], item.get(text_field, ""))

            expected_all = set(
                item.get("expected_affordances", [])
                + item.get("expected_products", [])
                + item.get("expected_agents", [])
            )
            extracted_all = set(
                extracted.affordances
                + extracted.products
                + extracted.agents
            )

            if extracted_all:
                result.coverage += 1

            result.true_positives  += len(expected_all & extracted_all)
            result.false_positives += len(extracted_all - expected_all)
            result.false_negatives += len(expected_all - extracted_all)

        return result

    # ── Internal ──────────────────────────────────────────────────────────────

    def _tokenize(self, text: str) -> list[str]:
        """Токенизация + нижний регистр."""
        tokens = re.findall(r'\b[а-яёa-z]{2,}\b', text.lower())
        return [self._lemmatize(t) for t in tokens]

    def _lemmatize(self, word: str) -> str:
        """Лемматизация через pymorphy2 (если доступен)."""
        if self._morph:
            try:
                return self._morph.parse(word)[0].normal_form
            except Exception:
                pass
        return word.lower()


# ── Store integration ──────────────────────────────────────────────────────────

def index_fact_affordances(
    db_conn,
    fact_id: str,
    result: AffordanceResult,
) -> None:
    """
    Записать результаты AffordanceLinker в БД.
    Использует fact_affordance_tokens для быстрого поиска.
    FIX: json_each() вместо LIKE по JSON.
    """
    db_conn.execute(
        "DELETE FROM fact_affordance_tokens WHERE fact_id = ?",
        (fact_id,),
    )

    for affordance in result.affordances:
        for token in affordance.lower().split():
            try:
                db_conn.execute(
                    """
                    INSERT OR IGNORE INTO fact_affordance_tokens
                    (fact_id, token, field) VALUES (?, ?, 'affordance')
                    """,
                    (fact_id, token),
                )
            except Exception:
                pass

    for product in result.products:
        for token in product.lower().split():
            try:
                db_conn.execute(
                    """
                    INSERT OR IGNORE INTO fact_affordance_tokens
                    (fact_id, token, field) VALUES (?, ?, 'product')
                    """,
                    (fact_id, token),
                )
            except Exception:
                pass

    for agent in result.agents:
        for token in agent.lower().split():
            try:
                db_conn.execute(
                    """
                    INSERT OR IGNORE INTO fact_affordance_tokens
                    (fact_id, token, field) VALUES (?, ?, 'agent')
                    """,
                    (fact_id, token),
                )
            except Exception:
                pass

    db_conn.commit()
