# 🌍 World Knowledge Core v1.0

**Статус:** future work / архитектурный канон  
**Runtime:** не активирован  
**Правило:** не менять stable `/query`, stable DB и Truth Gate без отдельного RFC, тестов и флагов.

---

## Главный смысл

Velantrim не должен становиться “копией человека” или театром личности.
Правильная цель:

> Velantrim = проверяемая модель знания, времени, причинности и выводов.

Wikipedia хранит тексты. LLM генерирует язык. World Knowledge Core должен
хранить структурированное знание: что известно, насколько этому можно доверять,
когда это было верно, чем это опровергалось, какие есть противоречия и какой
TRACE ведёт к выводу.

---

## Что это даст

| Слой | Что даёт |
|------|----------|
| `KnowledgeUnit` | факты становятся атомарными и типизированными, а не просто текстом |
| `KnowledgeQuality` | у каждого знания появляется профиль доверия |
| `TemporalEpistemology` | система понимает историю знания и смену моделей |
| `NegativeKnowledge` | система помнит тупики, опровержения и неудачные пути |
| `InconsistencyHunter` | противоречия становятся объектами review, а не скрытым мусором |
| `CrossDomainBridge` | система связывает домены по структуре, механизму и ограничениям |
| `EssenceLayer` | система выделяет главное, строит смысловую цепочку и отвечает коротко |
| `ReasoningModes` | выводы различаются: deductive, causal, analogical, bayesian и т.д. |
| `MetaReasoning` | TRACE можно спросить: почему выбран этот путь и что изменило бы вывод |

---

## Базовые объекты

### KnowledgeUnit

Типизированная единица знания.

```json
{
  "id": "ku_photosynthesis_mechanism_001",
  "type": "MECHANISM",
  "claim": "Фотосинтез преобразует световую энергию в химическую энергию.",
  "domain": "biology",
  "inputs": ["light", "CO2", "H2O"],
  "outputs": ["glucose", "O2"],
  "source_refs": ["src_textbook_biology_001"],
  "truth_status": "SUPPORTED",
  "quality_score": 0.86,
  "trace_id": "trace_..."
}
```

Разрешённые типы для v1:

`TERM`, `FACT`, `LAW`, `MODEL`, `METHOD`, `CONSTRAINT`, `MECHANISM`,
`CAUSE`, `EVIDENCE`, `COUNTEREVIDENCE`, `HYPOTHESIS`, `NEGATIVE_RESULT`.

### KnowledgeQualityScore

```json
{
  "source_tier": "reference",
  "evidence_count": 4,
  "replication_count": 2,
  "contradiction_count": 1,
  "consensus_strength": 0.72,
  "recency_score": 0.81,
  "domain_risk": "science_medium_risk",
  "overall_quality": 0.68
}
```

Важно: `confidence`, `truth_status` и `quality_score` не заменяют друг друга.
Это разные оси.

### SourceTier

Минимальная шкала источников:

| Tier | Значение |
|------|----------|
| `reference` | NIST, CODATA, IUPAC, стандарты, справочные данные |
| `textbook` | учебники, open courseware, фундаментальные курсы |
| `peer_reviewed` | принятая journal/conference paper |
| `systematic_review` | systematic review / meta-analysis |
| `preprint` | arXiv, bioRxiv и аналогичные источники |
| `index_metadata` | Semantic Scholar, OpenAlex, PubMed как индекс |
| `user_note` | пользовательская заметка |
| `unknown` | источник не классифицирован |

Правило: `arXiv != peer_reviewed`, `PubMed != truth`.

### TemporalStatus

Знание существует во времени и в парадигмах.

```json
{
  "epistemic_status": "superseded",
  "valid_period": ["1803-01-01", "1911-01-01"],
  "paradigm_context": "Dalton atomic theory",
  "superseded_by": "Rutherford nuclear model"
}
```

Статусы v1:

`current`, `historical_misconception`, `superseded`, `working_model`,
`emerging_evidence`, `contested_frontier`, `retracted`.

### NegativeKnowledgeRecord

Система должна хранить не только то, что работает, но и то, что уже не сработало.

```json
{
  "hypothesis": "Перпетуум-мобиле возможно.",
  "status": "rejected",
  "why_failed": "Нарушает законы термодинамики.",
  "lessons_learned": "Нельзя получать работу без источника энергии.",
  "related_dead_ends": ["free energy", "overunity devices"]
}
```

---

## Слои World Knowledge Core

| Уровень | Название | Задача |
|---------|----------|--------|
| L1 | Knowledge Units | атомарные типизированные claims |
| L2 | Quality Layer | профиль доверия и риска |
| L3 | Temporal Epistemology | время, парадигмы, supersession |
| L4 | Negative Knowledge | тупики, опровержения, failed hypotheses |
| L5 | Inconsistency Hunter | поиск конфликтов и отправка в Pending/Review |
| L6 | Cross-Domain Bridges | структурные мосты между доменами |
| L7 | Essence Layer | суть, meaning chain, короткий ответ, WhyTrace |
| L8 | Reasoning Modes | deductive / abductive / analogical / causal / bayesian |
| L9 | Meta-Reasoning | анализ собственного TRACE |

---

## Интеграция с текущей архитектурой

World Knowledge Core не заменяет существующие слои.

| Уже есть | Как использовать |
|----------|------------------|
| Graph Truth Store | хранит проверенные canonical facts |
| Truth Gate | не даёт автоматически повышать claims до истины |
| ESM states | управляют жизненным циклом facts |
| Fractal Memory L0-L3 | даёт уровни raw → working → episodic → canonical |
| TRACE | становится основой Meta-Reasoning |
| CrossDomain | база для будущих bridge rules |
| Understanding Layer | база для Essence Layer: суть, causal roles, living context |
| Research App | безопасное место для экспериментов |

Главное ограничение:

```text
World Knowledge Core может начинаться как документация и Research sandbox.
Stable core нельзя менять без отдельного RFC, миграций и тестов.
```

---

## Приоритеты

### P0 — фундамент, не ломает архитектуру

1. `KnowledgeUnit` schema.
2. `SourceTier` registry.
3. `KnowledgeQualityScore`.
4. `TemporalStatus`.
5. `NegativeKnowledgeRecord`.
6. `InconsistencyHunter lite` только как отчёт, без auto-fix.

### P1 — делает систему умнее

1. `CrossDomainBridge lite`.
2. `ReasoningModes` registry.
3. `DerivedFact` + `ProofTrace`.
4. `AdversarialCheck` только для high-risk / science / architecture answers.

### P2 — исследовательский слой

1. `ScientificCore lite`.
2. `FalsificationCriteria`.
3. `HypothesisLab`.
4. `MetaReasoning` поверх TRACE.

### P3 — дальняя перспектива

1. Full `AnalogicalReasoner`.
2. `ConceptAlgebra`.
3. `ThoughtExperimentsEngine`.
4. Counterfactual / World Simulator modules.

---

## Что не делать сейчас

- Не делать полный arXiv ingestion.
- Не повышать scientific claims в `FACT` автоматически.
- Не строить большой symbolic reasoner на всё.
- Не обещать “сознание”, “сверхчеловека” или “личность”.
- Не включать World Simulator как MVP.
- Не менять stable `/query` ради future-work идей.

---

## Каноническая формула

```text
Velantrim =
  Graph Truth Store
  + Fractal Memory
  + Knowledge Quality
  + Temporal Epistemology
  + Negative Knowledge
  + Inconsistency Review
  + Cross-Domain Reasoning
  + Essence Layer
  + TRACE / Meta-Reasoning
```

И коротко:

> Velantrim должен видеть то, что человеческий ум не удерживает одновременно:
> историю знания, противоречия, источники, причинные цепочки, аналогии,
> ошибочные пути и условия фальсификации.

---

## Статус для NLnet / внешнего описания

В текущую заявку это стоит включать только одной строкой:

> Future work: World Knowledge Core — typed knowledge units with quality,
> temporal epistemology, negative knowledge, contradiction review and traceable
> reasoning.

Реализация — после основных стабильных задач, через Research sandbox.
