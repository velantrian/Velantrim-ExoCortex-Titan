# 📚 Source Rules & Collection Plan — правила сбора World Skills Core

**Язык:** русский  
**Статус:** рабочие правила v0.2 · C9 / #52 admission-aligned  
**Назначение:** чтобы сбор знаний не превратился в хаотичную энциклопедию или набор неподтверждённых утверждений.

---

## 🎯 Главный принцип

Собираем не тексты, а компактные единицы знания:

```text
LAW / THEOREM / MODEL / MECHANISM / METHOD / CONSTRAINT / FAILURE_MODE / SAFETY_RULE
```

Для **Canon-admission candidate** каждая запись должна иметь полный C9 contract:

```text
id
domain
type
statement
conditions
links
truth_status
source_refs
confidence
risk_domain
limitations
review_status
reviewer
reviewed_at
```

`source_tier` остаётся полезной классификацией источника, но не заменяет конкретные
`source_refs`. Старые таблицы без полного набора полей остаются допустимым исследовательским
корпусом, однако C9 трактует их как `Draft / unreviewed` и не промоутит в Canon.

---

## 🏷️ Source tiers

| Tier | Источник | Как использовать |
|---|---|---|
| `reference` | NIST, CODATA, IUPAC, стандарты, справочники | высокая опора для констант, терминов, reference data |
| `textbook` | проверенные учебники, MIT OCW, университетские курсы | базовые законы, методы, определения |
| `peer_reviewed` | журнальная/конференционная статья | конкретные научные утверждения |
| `systematic_review` | обзор/мета-анализ | сильнее одной статьи, особенно в медицине |
| `standard` | ISO, IEC, IEEE, строительные нормы | инженерные и технические правила |
| `encyclopedic` | Wikipedia / Britannica | быстрый обзор, не финальная верификация |
| `preprint` | arXiv, bioRxiv | гипотеза/ранняя работа, не peer review |
| `practical_manual` | ASM Handbook, datasheets, manuals | производство, материалы, процессы |
| `user_note` | пользовательская заметка | Observed / Hypothesized до проверки |

---

## ⚖️ Truth status by domain

В authoring/review surface `truth_status` — **pre-Canon status**, а не право самостоятельно
поставить ESM `Validated`. Для C9 admission готовая к проверке запись должна приходить как
`Supported`; финальный `Validated` выдаёт только существующая цепочка TruthGate +
PromotionGateway + canonical CAS.

| Домен | Типичный pre-Canon статус после review |
|---|---|
| математика / классическая логика | `Supported` после проверки формулировки и источников |
| физика базовая | `Supported`, если это учебниковый закон с явными условиями |
| химия бытовой безопасности | `Supported`, источник и safety/limits обязательны |
| медицина / здоровье | `Supported`, не промоутить по одному источнику |
| психология | `Supported`, почти никогда не кандидат в `ImmutableCore` |
| философия | `POSITION` / `ARGUMENT`, не `WORLD_FACT` без отдельной классификации |
| инженерная практика | `Supported`, с safety и условиями |
| география текущая | зависит от даты, источника и review |

Нельзя авторским текстом объявить `truth_status=Validated` и тем самым обойти admission.
C9 принимает к финальной TruthGate-проверке только explicit `Supported` candidate.

---

## 🔐 C9 admission metadata

| Поле | Требование |
|---|---|
| `truth_status` | `Supported` перед admission; legacy/missing = `Draft` |
| `source_refs` | непустой набор конкретных уникальных ссылок/идентификаторов источников |
| `confidence` | конечное число `[0,1]`; не является заменой доказательствам |
| `risk_domain` | явная risk-классификация; critical domains выбирают существующий PRECISION TruthGate |
| `limitations` | непустые условия/ограничения применимости |
| `review_status` | `approved` для admission |
| `reviewer` | явный reviewer id; ingest actor не может review сам себя |
| `reviewed_at` | timezone-aware ISO-8601 timestamp |

Полный runtime contract и fail-closed flow описаны в
`docs/operations/world-skills-admission.md` и ADR
`docs/adr/ADR-2026-08-14-world-skills-admission.md`.

---

## 🧪 P0 сбор — что уже начато

| Файл | Слой |
|---|---|
| `01_P0_FORMAL_LOGIC_MATH.ru.md` | математика, логика, статистика, вычисления |
| `02_P0_NATURAL_EARTH_CORE.ru.md` | физика, химия, биология, земля |
| `03_P0_ENGINEERING_PRACTICAL_CORE.ru.md` | техника, инфраструктура, быт |
| `04_P0_HUMAN_SOCIAL_MEANING_CORE.ru.md` | психология, общество, философия |

---

## 🗺️ Дальнейшие этапы

### Stage 02 — расширение формального ядра

- алгебра;
- геометрия;
- тригонометрия;
- математический анализ;
- вероятность;
- дискретная математика;
- теория графов;
- формальные методы;
- типы логики.

### Stage 03 — природные науки

- механика;
- тепло и энергия;
- электричество;
- волны и оптика;
- химические связи;
- реакции;
- материалы;
- клетка;
- генетика;
- экология.

### Stage 04 — техника и технологии

- дороги;
- строительство;
- электроника;
- микропроцессоры;
- машины;
- энергетика;
- производство;
- безопасность;
- ремонт;
- бытовые процессы.

### Stage 05 — человек и общество

- внимание;
- память;
- обучение;
- мотивация;
- коммуникация;
- экономика;
- право;
- управление;
- этика;
- философия науки.

---

## 🚫 Что нельзя делать

- Нельзя копировать большие куски из сайтов.
- Нельзя писать authoring `Validated` как способ обойти TruthGate/PromotionGateway.
- Нельзя считать наличие строки в curated-файле доказательством provenance/review.
- Нельзя автоматически выдумывать `source_refs`, reviewer или review timestamp.
- Нельзя смешивать fact / inference / prediction / hypothesis.
- Нельзя делать медицинские или химически опасные инструкции без safety и limitations.
- Нельзя считать Wikipedia финальным источником для критичных фактов.
- Нельзя автоматически писать legacy seed в Canon/L3 без полного C9 admission.

---

## 🔗 Первичные рамочные источники

Эти источники нужны не как единственная база фактов, а как рамка классификации и проверяемости:

| Источник | Для чего |
|---|---|
| OECD / UNESCO FORD | крупные области науки и R&D |
| NIST / CODATA constants | физические константы и reference values |
| MSC2020 | карта областей математики |
| Stanford Encyclopedia of Philosophy | логика, модальность, временная/эпистемическая логика |
| Britannica / Wikipedia | быстрый обзор и поиск связей, не финальная верификация |

---

## ✅ Формула сбора

```text
source
  → extract compact unit
  → classify domain/type/risk_domain
  → add conditions + limitations
  → add concrete source_refs
  → assign cautious pre-Canon truth_status
  → domain review + reviewer + reviewed_at
  → TruthGate / PromotionGateway admission
  → only then Validated / local Canon
```

Legacy rows without this evidence remain research/scratch candidates; C9 does not
retroactively certify them.
