# E5 — Scallop / DeepProbLog в L4 (Horizons)

> **Статус: 🧪 experimental** — в **VELANTRIM V8.6 Complex** нет `core/scallop_*` / `deepproblog_*`, флага `ENABLE_DPP_REASONING` нет. Дифференцируемое логическое рассуждение вместо LLM CoT — **в исследовании** (V9 §E5).

## Зачем E5

**Chain-of-Thought** в LLM плохо аудируется: шаги не формальны, ошибки compounding.

**Scallop / DeepProbLog (DPP)**:

- правила и факты как логическая программа;
- вероятностные веса + градиенты (PyTorch bridge);
- вывод **проверяем** post-hoc, не только «похож на правду».

Цель для L4 ReasoningBank: стратегии с **formally verifiable** derivation paths.

## Архитектура (план)

```
FactsPack + graph edges
    ↓
DPP program (rules from ReasoningBank strategy)
    ↓
Scallop engine → proof trace
    ↓
Optional: neural predicate weights update (Slow Path)
    ↓
Answer + exportable proof для audit
```

## Планируемые компоненты

| Компонент | Назначение |
|-----------|------------|
| **DPPProgramStore** | Версионированные программы на стратегию |
| **ScallopRuntime** | FFI / subprocess sandbox |
| **ProofExporter** | JSON trace для response_audit |
| **FallbackCoT** | Graceful degrade к LLM при timeout |
| **E5Bridge** | Hook в `reasoning_bank` selection |

## Связь с V8.6 сегодня

| Сейчас | Роль |
|--------|------|
| `core/reasoning_bank.py` | Хранилище стратегий (🟡 off) |
| `core/causal_graph.py` | Факты для логических предикатов |
| [E4_VIRF_PATTERN.md](E4_VIRF_PATTERN.md) | Verifier consumer |
| `core/pipeline.py` | Optional L4 step перед LLM |

## Чего E5 **не** делает

- Не пишет в граф без Truth Gate.
- Не обязателен для online режима (LLM остаётся default).

## Этапы

| Этап | Статус |
|------|--------|
| V9 §E5 | ✅ |
| Scallop sandbox + 1 strategy | 🔬 research |
| Proof in audit API | 🔬 research |
| PyTorch weight sync | 🔜 V10+ |

## Источники

- V9 §E5 — Scallop / DeepProbLog
- Scallop Datalog engine (CMU)
- DeepProbLog literature

Индекс: [`../HORIZONS.md`](../HORIZONS.md)
