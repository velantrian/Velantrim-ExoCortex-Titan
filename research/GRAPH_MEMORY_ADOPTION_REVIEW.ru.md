# Разбор `divyanshailani/graph-memory` для Velantrim Titan

**Статус:** архитектурный decision record  
**Решение:** адаптировать отдельные принципы, не встраивать проект целиком  
**Проверенная upstream-версия на момент разбора:** `1.6.5`  
**Upstream:** https://github.com/divyanshailani/graph-memory  
**Связанный RFC Titan:** [`CODE_STRUCTURAL_MEMORY_ADAPTER.md`](./CODE_STRUCTURAL_MEMORY_ADAPTER.md)

---

## 1. Итоговое решение

`graph-memory` полезен Titan не как новая общая память, а как доказательство практической ценности отдельного слоя:

```text
детерминированная структурная память программного кода
```

Перенимаем как архитектурную идею:

```text
Tree-sitter AST
→ структурный граф
→ ограниченный retrieval
→ позже производные summaries
```

Не переносим:

```text
готовый SQLite engine
готовую trust-модель
прямые MCP-записи
автоматический тихий writeback агентов
готовую схему идентификаторов
возрастное снижение истины
LLM-summary с высоким доверием
```

---

## 2. Что в upstream действительно полезно

### 2.1 Tree-sitter вместо LLM для структуры

Проект извлекает файлы, классы, функции и импорты через Tree-sitter. Это правильный принцип: структура кода должна определяться парсером, а не предположением языковой модели.

**Решение Titan:** принять принцип и сделать чистую Titan-native реализацию.

### 2.2 Structural-first retrieval

Для точного вопроса о функции, файле или импорте сначала нужен граф символов, а не embeddings.

**Решение Titan:** добавить `CodeStructuralRetriever` рядом с существующим `HybridRetriever`, а не заменять его.

### 2.3 Ограниченный подграф

Upstream сериализует ближайшее окружение узла вместо выгрузки всего графа.

**Решение Titan:** использовать bounded graph expansion с явными лимитами глубины, узлов, рёбер и времени.

### 2.4 Разделение skeleton и summary

Идея «сначала детерминированный скелет, потом смысловое описание» архитектурно здравая.

**Решение Titan:** MVP реализует только skeleton. Summary допускается позже отдельным RFC как производный, версионируемый и инвалидируемый объект.

### 2.5 MCP-совместимость

Стандартные имена MCP memory tools полезны как ориентир совместимости.

**Решение Titan:** рассматривать только read-only MCP adapter после стабилизации внутреннего API. MCP write остаётся вне первого этапа.

---

## 3. Что нельзя переносить без переработки

### 3.1 Идентификаторы по basename

В upstream файл идентифицируется приблизительно как:

```text
File_<filename>
```

Это создаёт коллизии:

```text
core/utils.py
api/utils.py
```

**Решение Titan:** ID включает постоянный `repository_id`, относительный путь, тип символа и qualified name.

### 3.2 MOC по последнему имени каталога

Разные каталоги с одинаковым последним сегментом могут объединяться.

**Решение Titan:** архитектурные области строятся по полному пути или позже по сообществам dependency graph.

### 3.3 Упрощённый import parsing

Upstream частично разбирает импорт строковыми операциями и создаёт абстрактные dependency-узлы. Это недостаточно для точного internal impact analysis.

**Решение Titan:** Tree-sitter extraction + отдельный Python import resolver с поддержкой absolute/relative imports, `__init__.py`, `src/` layout и явного unresolved состояния.

### 3.4 Неполный differential sync

Удаление старых import edges не решает исчезновение файлов, классов и функций. Orphan cleanup не гарантирует удаление всех ghost nodes.

**Решение Titan:** scan staging, `last_seen_scan` и атомарная финализация. Stale-решение принимается только после полного успешного scan.

### 3.5 Одномерный `trust_score`

Одно число смешивает происхождение, проверку, актуальность, истинность и полезность.

**Решение Titan:** для AST-структуры используется детерминированная scan provenance. Общая ESM/truth-модель Titan не заменяется.

### 3.6 `MAX(trust_score)`

Если обновление всегда сохраняет максимальное когда-либо достигнутое доверие, ошибочно повышенный trust трудно понизить.

**Решение Titan:** не переносить этот механизм.

### 3.7 Trust decay по возрасту

Старость записи не означает ложность. Код может быть неизменным и корректным долгое время.

**Решение Titan:** актуальность определяется соответствием последнему успешному repository scan, а не возрастом.

### 3.8 Прямые MCP writes

В upstream агент может создавать сущности и отношения напрямую, причём default trust способен оказаться максимальным.

**Решение Titan:** первый MCP-этап только read-only. Любой будущий write требует отдельного admission contract.

### 3.9 Автоматический скрытый writeback

Рекомендация агентам автоматически и незаметно записывать решения создаёт риск дублирования, загрязнения и неконтролируемого роста.

**Решение Titan:** никакого автоматического writeback в MVP.

### 3.10 LLM-summary без строгой provenance

Summary должна знать входной graph hash, модель, prompt version и момент инвалидирования.

**Решение Titan:** summaries отсутствуют в MVP. Позже они хранятся отдельно от детерминированной структуры.

---

## 4. Почему Titan не должен использовать вторую базу

Полное встраивание upstream привело бы к следующему:

```text
Titan SQLite / graph backends
+
graph-memory SQLite
```

Это создаёт:

- два источника истины;
- отдельные правила backup/restore;
- отдельную модель удаления;
- риск рассинхронизации;
- дублирование FTS и graph logic;
- отдельную поверхность безопасности;
- сложную диагностику stale данных.

**Решение:** dedicated code-memory tables внутри Titan-controlled SQLite boundary, но отдельно от канонических `facts`.

---

## 5. Что в Titan уже сильнее upstream

Titan уже имеет:

- ESM-состояния;
- WriteGate;
- RecallPolicy fail-closed;
- provenance chain;
- bi-temporal memory;
- hybrid BM25 + dense retrieval;
- semantic dedup;
- Graph Lab;
- privacy/restriction/erasure contracts;
- метрики и CI;
- storage abstractions.

Поэтому upstream не нужен как общий memory engine. Нужна только отсутствующая специализация: AST code index.

---

## 6. Целевая архитектура Titan

```text
Repository snapshot
        ↓
Tree-sitter Python scanner
        ↓
Stable IDs + import resolver
        ↓
Scan staging
        ↓
Atomic finalizer
        ↓
Dedicated code-memory tables
        ↓
Read-only structural retrieval
```

Логическое разделение:

```text
canonical memory = знания пользователя и мира
code structural memory = индекс конкретного состояния репозитория
```

---

## 7. Лицензионная граница

В upstream `pyproject.toml` указан classifier MIT, однако при разборе отдельный файл `LICENSE` не был обнаружен.

До появления явного файла лицензии или письменного разрешения автора:

- не копировать функции или файлы;
- не переносить README дословно;
- не переносить schema SQL;
- не переносить MCP server code;
- не переносить visualizer code;
- реализовать решение clean-room по собственному RFC;
- сохранить ссылку на upstream как источник архитектурного вдохновения.

Даже после подтверждения MIT предпочтительна Titan-native реализация, поскольку контракты систем существенно различаются.

---

## 8. Матрица решения

| Upstream-компонент | Решение Titan | Причина |
|---|---|---|
| Tree-sitter scanner | **ADAPT / переписать** | высокая практическая ценность |
| AST node taxonomy | **ADAPT** | нужна более строгая идентичность |
| Import graph | **REDESIGN** | upstream resolver слишком упрощён |
| One-hop serialization | **ADAPT** | нужен bounded retrieval |
| MOC concept | **DEFER / redesign** | папки не всегда равны архитектурным областям |
| LLM summaries | **DEFER** | нужна provenance и invalidation |
| MCP read compatibility | **DEFER** | полезно после внутреннего API |
| MCP writes | **REJECT for MVP** | обход admission-контрактов |
| SQLite schema | **REJECT** | Titan использует собственную boundary |
| FTS5 search | **REJECT as duplicate** | Titan уже имеет retrieval |
| `trust_score` | **REJECT** | плоская эпистемическая модель |
| trust decay | **REJECT** | возраст не равен ложности |
| orphan sweeper | **REPLACE** | нужен complete-scan reconciliation |
| HTML/3D viewer | **DEFER** | не требуется для structural MVP |
| quiet agent auto-write | **REJECT** | риск неконтролируемого загрязнения |

---

## 9. Финальный вердикт

`graph-memory` — хороший ранний прототип идеи **структурной памяти кода**, но не готовая подсистема для прямого встраивания в Titan.

Правильная формула:

```text
взять идею
≠ скопировать систему

взять Tree-sitter principle
+ добавить Titan reliability contracts
= Code Structural Memory Adapter
```

После реализации Titan получит точную карту программного проекта, сохранив собственные гарантии провенанса, изоляции, безопасности и контролируемого retrieval.
