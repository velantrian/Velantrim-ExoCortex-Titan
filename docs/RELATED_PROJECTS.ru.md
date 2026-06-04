# Связанные репозитории Velantrim

## Главный проект (канон) — VELANTRIM V8.6 Complex

| | |
|---|---|
| **Папка на диске** | `VELANTRIM_ExoCortex_V8.6` (папка продукта — **V8.6 Complex**) |
| **Сервер** | `server.py` |
| **Ядро** | `core/memory.py`, `core/pipeline.py`, `core/truth_gate.py` |
| **L6 MVP** | `core/welfare_monitor.py`, `ENABLE_L6_WELFARE` |
| **Спека V9** | `docs/Velantrim_V9_Final_Audited.md` |

Все новые фичи **сначала** вносятся сюда.

## Интеграция — Graphiti_fractal-main

| | |
|---|---|
| **Папка** | `../Graphiti_fractal-main` |
| **Сервер** | `app.py` |
| **Роль** | Fractal Memory + Graphiti/Neo4j, Etir, L4.5 Beta, локальный sqlite-ingest |

Дубликат L6 в fractal — **legacy fork** для Graphiti-стека; канон L6 — в **V8.6 Complex**. При расхождении править главный проект, затем при необходимости синхронизировать fractal.

## Куда править

| Задача | Репозиторий |
|--------|-------------|
| Truth Gate, ESM, pipeline, L6 welfare | **VELANTRIM_ExoCortex_V8.6** |
| Graphiti, Neo4j, `/upload` fractal | **Graphiti_fractal-main** |
| RFC / Horizons документация | **VELANTRIM_ExoCortex_V8.6** `docs/HORIZONS.md`, `docs/LAYERS_AND_HORIZONS.ru.md`, `docs/horizons/` |

```
C:\Users\VELAN\Documents\velantrim\
├── VELANTRIM_ExoCortex_V8.6\      ← VELANTRIM V8.6 Complex (главный)
└── Graphiti_fractal-main\       ← Graphiti integration
```
