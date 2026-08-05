# 🌐 Velantrim Ecosystem / Экосистема Velantrim

> **Document type:** navigation and integration-boundary map.  
> **Authority:** this document does not authorize runtime integration, cross-project writes, shared Canon authority, identity mutation or capability inheritance.  
> **Languages:** English first, followed by Russian. Other translations may be added after the English/Russian contract stabilizes.

## English

### Titan's role

**Velantrim ExoCortex — Titan** is the broader cognitive and operational research environment of the Velantrim ecosystem.

Titan explores memory orchestration, retrieval, reasoning, task context, tools, agents, adaptive computation and auditable action paths. It may evaluate bounded adapters to other Velantrim projects, but it must not silently absorb their authority.

```text
Titan as ecosystem orchestrator
≠ Titan as universal source of truth
≠ automatic access to identity state
≠ permission to write into another project's Canon
```

### Project map

| Project | Primary role | Current relationship to Titan |
|---|---|---|
| [🔱 Titan](https://github.com/velantrian/Velantrim-ExoCortex-Titan) | Cognition, orchestration, retrieval, tools, agents and task-aware context | This repository; broader Exo-Cortex research/runtime track |
| [💎 Crystal](https://github.com/velantrian/velantrim-exocortex-crystal) | Verifiable memory, evidence, provenance, trust and audit boundaries | Independent grant-facing product; no automatic shared Canon |
| [🧬 Native Kernel](https://github.com/velantrian/velantrim-native-kernel) | Long-horizon substrate-neutral event and memory-contract research | Independent research; a possible future Offline Shadow target, not Titan's current source of truth |
| [⭐️ Mentaury Soul](https://github.com/velantrian/velantrim-mentaury-soul) | Digital individuality, identity continuity, relationships, commitments and governed development | Separate identity research; Titan may offer tools, not identity authority |

### Conceptual relationship map

```text
                         🌐 VELANTRIM ECOSYSTEM
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
  ⭐️ Mentaury Soul            🔱 Titan                 💎 Crystal
 identity / continuity     cognition / tools       evidence / trust
 relationships / M3        orchestration           provenance / audit
          │                        │                        │
          └──────── proposed governed contracts ──────────┘
                                   │
                                   ▼
                         🧬 Native Kernel
                 substrate-neutral contract research

Conceptual relationships are not claims of current runtime wiring.
```

### Mandatory boundaries

1. Titan does not become the truth authority for Crystal, Native Kernel or Mentaury.
2. Crystal facts or Receipts do not become Titan Canon automatically; admission remains explicit and policy-gated.
3. Titan tools and model outputs do not become Mentaury beliefs, relationships, commitments or M3 identity state automatically.
4. Native Kernel projections remain research artifacts until separately integrated and validated.
5. Cross-project credentials, consent, capabilities and authority are never inherited implicitly.
6. Every integration requires a scoped RFC/ADR, explicit interface contract, deterministic tests, threat/privacy review, rollback and operator approval.

### Safe future integration pattern

```text
proposal
→ bounded adapter contract
→ isolated implementation
→ deterministic tests
→ read-only / Offline Shadow evaluation
→ receipts, omissions and failure analysis
→ security and privacy review
→ explicit approval
→ separately versioned integration
```

---

## Русский

### Роль Titan

**Velantrim ExoCortex — Titan** — более широкая когнитивная и операционная исследовательская среда экосистемы Velantrim.

Titan исследует orchestration памяти, retrieval, reasoning, task context, инструменты, агентов, адаптивные вычисления и аудируемые пути действий. Он может проверять ограниченные адаптеры к другим проектам Velantrim, но не должен незаметно присваивать их authority.

```text
Titan как оркестратор экосистемы
≠ Titan как универсальный источник истины
≠ автоматический доступ к identity-state
≠ право записи в Canon другого проекта
```

### Карта проектов

| Проект | Основная роль | Текущее отношение к Titan |
|---|---|---|
| [🔱 Titan](https://github.com/velantrian/Velantrim-ExoCortex-Titan) | Cognition, orchestration, retrieval, инструменты, агенты и task-aware context | Этот репозиторий; широкое Exo-Cortex направление |
| [💎 Crystal](https://github.com/velantrian/velantrim-exocortex-crystal) | Проверяемая память, доказательства, provenance, доверие и аудит | Независимое грантовое направление; общего Canon по умолчанию нет |
| [🧬 Native Kernel](https://github.com/velantrian/velantrim-native-kernel) | Долгосрочное substrate-neutral исследование event- и memory-контрактов | Независимое исследование; возможный будущий Offline Shadow target, но не текущий источник истины Titan |
| [⭐️ Mentaury Soul](https://github.com/velantrian/velantrim-mentaury-soul) | Цифровая индивидуальность, continuity, отношения, commitments и управляемое развитие | Отдельное identity-исследование; Titan может предоставлять инструменты, но не identity authority |

### Обязательные границы

1. Titan не становится truth-authority для Crystal, Native Kernel или Mentaury.
2. Факты или Receipts Crystal не становятся Titan Canon автоматически; admission остаётся явным и policy-gated.
3. Инструменты и model outputs Titan не становятся автоматически beliefs, relationships, commitments или M3-state Mentaury.
4. Проекции Native Kernel остаются исследовательскими артефактами до отдельной интеграции и валидации.
5. Credentials, consent, capabilities и authority не наследуются между проектами неявно.
6. Каждая интеграция требует ограниченного RFC/ADR, явного interface contract, детерминированных тестов, threat/privacy review, rollback и одобрения оператора.

### Безопасная последовательность интеграции

```text
предложение
→ ограниченный контракт адаптера
→ изолированная реализация
→ детерминированные тесты
→ read-only / Offline Shadow оценка
→ Receipts, omissions и анализ отказов
→ security и privacy review
→ явное одобрение
→ отдельно версионируемая интеграция
```
