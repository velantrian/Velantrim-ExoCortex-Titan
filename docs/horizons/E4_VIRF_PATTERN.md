# E4 — VIRF Pattern (Horizons / System 1 ↔ System 2)

> **Статус: 🧪 experimental** — в **VELANTRIM V8.6 Complex** нет `core/virf_*`, флага `ENABLE_VIRF` нет. Педагогический цикл LLM ↔ formal verifier — **только в исследовании** (V9 §E4).

## Зачем VIRF

**System 1** (быстрый LLM ответ) и **System 2** (медленная формальная проверка) обычно разведены слабо: либо только LLM, либо только rules.

**VIRF** (Verifier-In-the-Loop Reflective Feedback):

1. LLM генерирует черновик + plan;
2. Formal verifier (Scallop / constraints / Truth Gate) проверяет;
3. При fail — **педагогический** feedback в контекст (не silent retry);
4. Итерация до pass или boundary refuse.

На SafeAgentBench (спека): **0%** опасных действий, **77.3%** целевых.

## Архитектура (план)

```
User query
    ↓
System1: LLM draft (Fast Path)
    ↓
System2: VIRF verifier (claims, tools, ESM rules)
    ↓ pass → respond
    ↓ fail → pedagogical trace → System1 refine (bounded turns)
```

## Планируемые компоненты

| Компонент | Назначение |
|-----------|------------|
| **VIRFOrchestrator** | Лимит раундов, таймауты |
| **ClaimExtractor** | Декомпозиция ответа в проверяемые claims |
| **FormalVerifier** | Truth Gate + optional Scallop (см. E5) |
| **PedagogyFormatter** | Человекочитаемый feedback для LLM |
| **VIRFAudit** | Traces в response_audit / Slow Path |

## Связь с V8.6 сегодня

| Сейчас | Роль |
|--------|------|
| `core/truth_gate.py` | Verifier для фактов и режимов |
| `core/response_audit.py` | Хранение traces (🟡 off) |
| `core/pipeline.py` | Post-retrieve validation hook |
| [E5_SCALLOP_DPP.md](E5_SCALLOP_DPP.md) | Усиление System 2 |

## Чего VIRF **не** делает

- Не заменяет Truth Gate при **записи** в память.
- Не гарантирует truth мира — только согласованность с политикой и ESM.

## Этапы

| Этап | Статус |
|------|--------|
| V9 §E4 | ✅ |
| ClaimExtractor MVP | 🔬 research |
| 2-round VIRF в `/query` | 🔬 research |
| Production guardrails | 🔜 V10+ |

## Источники

- V9 §E4
- arXiv:2602.08373 (SafeAgentBench / VIRF)

Индекс: [`../HORIZONS.md`](../HORIZONS.md)
