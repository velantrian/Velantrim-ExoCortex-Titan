# 🌐 Связанные проекты Velantrim

> **Назначение:** краткая навигационная карта репозиториев и их границ.  
> **Authority:** этот документ не создаёт runtime-интеграцию, общий Canon, право межпроектной записи или наследование capabilities.  
> **Полная двуязычная карта:** [VELANTRIM_ECOSYSTEM.md](./VELANTRIM_ECOSYSTEM.md).

## 🧭 Актуальные репозитории

| Проект | Репозиторий | Основная роль | Текущее отношение к Titan |
|---|---|---|---|
| 🔱 **Titan** | [Velantrim-ExoCortex-Titan](https://github.com/velantrian/Velantrim-ExoCortex-Titan) | Cognition, orchestration, retrieval, инструменты, агенты и task-aware context | Этот репозиторий; широкое Exo-Cortex research/runtime направление |
| 💎 **Crystal** | [velantrim-exocortex-crystal](https://github.com/velantrian/velantrim-exocortex-crystal) | Проверяемая память, evidence, provenance, TruthGate, TRACE и аудит | Независимое грантовое направление; общего Canon или автоматической записи нет |
| 🧬 **Native Kernel** | [velantrim-native-kernel](https://github.com/velantrian/velantrim-native-kernel) | Substrate-neutral исследование event-, memory- и projection-контрактов | Независимое исследование; возможный будущий Offline Shadow target |
| ⭐️ **Mentaury Soul** | [velantrim-mentaury-soul](https://github.com/velantrian/velantrim-mentaury-soul) | Цифровая индивидуальность, identity continuity, отношения и commitments | Отдельное identity-направление; Titan может предоставлять инструменты, но не identity authority |

## 🗺️ Концептуальная карта

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
```

> Карта показывает **разделение ролей**, а не текущую wiring-схему runtime.

## ⚖️ Куда вносить изменения

| Изменение | Основной репозиторий |
|---|---|
| Titan cognition, orchestration, retrieval, tools, agents, task context | **Titan** |
| Crystal Canon, evidence, provenance, Guardian, TruthGate, TRACE, Receipts | **Crystal** |
| Substrate-neutral event/memory contracts, replay и rebuildable projections | **Native Kernel** |
| Identity continuity, M0–M3, relationships, commitments, Character boundary | **Mentaury Soul** |

Изменение в одном проекте не должно автоматически копироваться в другой. Перенос идеи выполняется через отдельный RFC/ADR, interface contract, тесты и review.

## 🛡️ Обязательные границы

```text
Titan tool output ≠ Crystal Canon
Titan tool output ≠ Mentaury belief or M3
Crystal evidence ≠ automatic Titan Canon
Crystal evidence ≠ automatic Mentaury identity
Native Kernel event ≠ universal Velantrim truth
shared repository family ≠ shared credentials or authority
```

1. Каждый проект сохраняет собственную implementation truth и maturity status.
2. Межпроектная запись запрещена без явного ограниченного адаптера.
3. Credentials, capabilities, consent, relationships и commitments не наследуются автоматически.
4. Open PR, research-документ и Notion-план не равны реализации в GitHub `main`.
5. Интеграция требует threat/privacy review, deterministic tests, rollback, Receipts и одобрения оператора.

## 🔬 Безопасный путь будущей интеграции

```text
идея
→ scoped RFC / ADR
→ bounded interface contract
→ isolated adapter
→ deterministic tests
→ read-only / Offline Shadow evaluation
→ failure and omission analysis
→ security/privacy review
→ explicit approval
→ versioned integration
```

## 🗄️ Исторические локальные папки

Старые имена локальных папок, такие как `VELANTRIM_ExoCortex_V8.6` и
`Graphiti_fractal-main`, могут встречаться в архивной документации. Они не являются
актуальной картой экосистемы и не должны использоваться для определения authority
или места внесения новых межпроектных изменений.
