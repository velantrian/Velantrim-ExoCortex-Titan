# 🧠 HMA — Hybrid Memory Architecture (исследовательская концепция)

> **Тип:** архитектура нейросети, не софт. Не реализуемо в текущем стеке.
> **Источник:** HMA_Architecture.md + Neural Memory Architectures for LLMs PDF
> **Статус:** исследовательский интерес. V8.7 имеет архитектурные аналоги на софтовом уровне.

---

## 🎯 Суть

HMA предлагает **встроить память внутрь LLM** — не как внешнюю систему (RAG), а как нейросетевые слои. 5 изолированных регистров, внутренний маршрутизатор, гибридное внимание.

```
Современный подход:   LLM ← внешняя память (RAG, SQLite, векторные БД)
Подход HMA:            LLM = Transformer + SSM + Router + 5 регистров (внутри)
```

Это требует обучения модели с нуля. V8.7 не может это реализовать — мы используем уже обученные LLM. Но архитектурные аналогии ценны.

---

## 🏗️ 5 регистров HMA vs V8.7

| Регистр HMA | Что это в нейросети | Архитектурный аналог в V8.7 |
|-------------|--------------------|---------------------------|
| 📜 **INST REG** | Frozen KV-cache (до 32K токенов). Системный промпт НИКОГДА не вытесняется | `CoreMemoryBlocks` — ~500 токенов всегда в контексте |
| 🧠 **WM** | Sliding window attention + SSM (2M+ токенов). Рабочая память | `WorkingNotebook` + L0/L1 + `fractal_memory.py` |
| 🗄️ **EXT GRAPH** | KuzuDB + Qdrant с Cross-Register Attention | `LadybugDB` + `hybrid_retriever.py` + `causal_graph.py` |
| 🕐 **EPISODIC** | SSM state, персистентный между сессиями | L1 Episodic Buffer + `bi-temporal I96` |
| 🔍 **GRAPH INDEX** | Bloom filter + ANN (1-3ms) для быстрого факт-чекинга | `NGramIndex` FTS5 trigram |

---

## 🧭 Internal Router

```
В HMA:      <10M-параметров классификатор внутри модели.
            Классифицирует КАЖДЫЙ токен по типу:
            INSTRUCTION / FACT / WORKING / QUERY / CODE / CREATIVE

В V8.7:     question_formula.py — 29 rule-based формул вопроса.
            ModeRouter — 3 линзы тона (PERSONAL/VELANTRIM/UMWELT).
```

**Разница:** HMA делает это на уровне токенов (внутри forward pass). V8.7 — на уровне запроса (до pipeline).

---

## ⚡ Hybrid Attention

```
HMA_Attn = α·LocalAttn + β·SSM_State + γ·CrossAttn(регистры)
           α, β, γ — learnable веса, сумма = 1

В V8.7:    HybridRetriever = RRF(BM25, Dense) — фиксированный k=60.
           Нет learnable весов. Нет Cross-Attention к регистрам.
```

---

## 🔐 Memory Write Gate

```
HMA:       importance > 0.7 → EPISODIC всегда
           confidence > 0.85 AND verified → EXT_GRAPH через Truth Gate
           instruction_pattern → INST REG только при подтверждении

В V8.7:    write_gate.py — WORLD_FACT без источника → REJECT
           truth_gate.py — 4 CognitiveModes
           consolidation_engine.py — Observed → Validated
```

---

## 📊 Три адаптируемые идеи

Три концепта из HMA/PDF, которые можно адаптировать в софтовой архитектуре V8.7:

| # | Идея | Статус |
|---|------|--------|
| 1 | **Embedding-based routing** — замена 29 if/elif на product-key lookup. O(1) вместо O(n) | Задокументировано в FUTURE_COMPONENTS.md |
| 2 | **Learnable retrieval weights** — адаптивные α/β/γ для BM25/Dense/Causal. Обновление через Prediction Error | Задокументировано в FUTURE_COMPONENTS.md |
| 3 | **Three-tier session persistence** — LSM state сохраняется между сессиями | Задокументировано в FUTURE_COMPONENTS.md |

---

## 🔬 Ключевые исследовательские работы (из PDF)

| Работа | Год | Суть |
|--------|-----|------|
| **Titans** (Google DeepMind) | 2024 | Три уровня памяти: Core (sliding window) + Long-term (MLP) + Persistent. >2M контекст |
| **PEER** (Google DeepMind) | 2024 | Product-key routing: >1M микро-экспертов через sparse lookup O(√N) |
| **MEMORYLLM** | 2024 | 7680 latent слотов внутри модели. M+ преемник: +150K долгосрочных слотов |
| **Mamba-3** | 2026 | Complex-valued SSM с половиной размера состояния Mamba-2 |
| **RWKV-7 "Goose"** | 2025 | Generalized delta rule. 3B SoTA multilingual. RWKV-8 ROSA — символическая адресация |
| **Graphiti** (Zep) | 2025 | Bi-temporal граф. Sub-200ms retrieval. 94.8% точность |
| **Gated DeltaNet** (NVIDIA) | 2025 | Delta-rule обновления памяти → Qwen3-Next, Qwen3.5, Kimi Linear |
| **Letta (MemGPT v2)** | 2025 | Единственная система с явно именованными слотами памяти (#1 Terminal-Bench) |
| **Infini-Attention** (Google) | 2024 | Фиксированная compressive memory матрица. 114× сжатие vs полный KV cache |

---

## 🏁 Вывод

HMA — следующий эволюционный шаг после софтовых систем памяти. Когда LLM получат нативную память внутри архитектуры — внешние системы станут не нужны. V8.7 — мост к этому будущему: все концепты HMA реализованы как софтовые аналоги, готовые к интеграции когда железо догонит.

**Когда возвращаться:** при появлении open-source моделей с SSM-регистрами и нативной маршрутизацией (RWKV-8, Mamba-4, Qwen4). Тогда портировать логику V8.7 внутрь модели.
