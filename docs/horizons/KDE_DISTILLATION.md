# KDE — Knowledge Distillation Engine (Horizons)

> **Статус: 🔬 research** — в **VELANTRIM V8.6 Complex** нет `core/kde_*`, флага `ENABLE_KDE` нет. Сжатие и дистилляция знаний графа — только в спеке V9 §3.5.

## Зачем KDE

Долгоживущий граф накапливает **шум**: дубли, слабые гипотезы, устаревшие эпизоды. KDE — слой **сжатия без потери истины**:

- выделяет «gist» кластеры из Validated фактов;
- предлагает merge/summary узлы через Truth Gate (не автоматом);
- отдаёт дистиллированный контекст в retrieval (меньше токенов).

## Планируемые компоненты

| Компонент | Назначение |
|-----------|------------|
| **DistillationPlanner** | Что сжимать (по decay, MHI, salience) |
| **GistExtractor** | LLM или детерминированный summary |
| **ProvenancePreserver** | Ссылки на исходные fact_id / L0 raw |
| **PromoteGate** | Только Hypothesized → Validated через Truth Gate |

## Связь с V8.6

| Сейчас | Роль при KDE |
|--------|----------------|
| `sleep_time_worker.py` | Ночная дедупликация (частичный аналог) |
| `concept_emergence.py` | Кластеры L2 (🟡 off) |
| `truth_gate.py` | Граница promote distilled facts |
| [R3_EVO_MEMORY.md](R3_EVO_MEMORY.md) | Refine после дистилляции |

## Этапы

| Этап | Статус |
|------|--------|
| Упоминание V9 §3.5 | ✅ |
| Gist schema + API | 🔬 research |
| HITL promote flow | 🔜 V10+ |

Индекс: [`../HORIZONS.md`](../HORIZONS.md)
