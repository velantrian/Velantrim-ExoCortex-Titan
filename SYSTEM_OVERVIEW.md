# 🗺️ Velantrim Titan 9.0 — живая карта системы

> **Роль:** архитектурная и навигационная карта для пользователя, инженера,
> оператора, аудитора и AI-агента.
>
> **Версия:** <!-- SYNC:VERSION -->v9.0.0<!-- /SYNC:VERSION -->
> **Проверенная база:** `main@70bc34fecdcf0bae15bc2264445e31b87b79bf08` на 2026-09-08.
> Это датированный checkpoint, а не вечный claim о remote head.
>
> При конфликте приоритет: exact code → tests/CI → selected config/runtime evidence → docs.

[🇬🇧 English](SYSTEM_OVERVIEW.en.md) · [README](README.md) ·
[README русский](README.ru.md) · [Статус](docs/PROJECT_STATUS.md) ·
[Reviewer map](docs/REVIEWER_README.md)

---

<a id="plain"></a>

## 👋 Titan за 30 секунд

Titan — local-first memory/orchestration runtime для AI-агентов. Центральный принцип —
**разделение полномочий**:

```text
source → memory → retrieval → policy/admission → answer/action
```

```text
retrieval ≠ evidence
admission ≠ verification
model output ≠ Canon
TRACE membership ≠ semantic use ≠ answer support
capability ≠ permission
wired ≠ enabled ≠ observed
```

LLM/provider layer заменяем. Canon mutation, policy, provenance и tool permission не
становятся властью модели только потому, что модель сформулировала текст.

---

<a id="evidence"></a>

## 🧾 Как читать статусы

```text
proposed ≠ implemented ≠ tested ≠ wired ≠ enabled ≠ observed
```

Для implementation claims:

1. executable code на exact SHA;
2. tests/current CI;
3. selected config + runtime observation;
4. current-state docs / accepted ADR;
5. PR/work-log history;
6. archive/history.

Green CI, merged PR, feature flag или зарегистрированный route сами по себе не являются
Operator GO или production authorization.

---

<a id="map"></a>

## 🗺️ L1 — карта системы

```text
ЧЕЛОВЕК / АГЕНТ / ФАЙЛ
        │
        ▼
 API · auth · policy
        │
 ┌──────┼───────────────┐
 ▼      ▼               ▼
READ   WRITE          TOOLS/MCP
 │      │               │
 ▼      ▼               ▼
retrieval/ESM       capability + auth
context  + CAS          boundary
 │      │               │
 └──────┴───────┬───────┘
                ▼
       provenance / audit
                │
        ┌───────┴───────┐
        ▼               ▼
 derived projections   replaceable LLM/provider
```

| Область | Основная поверхность | Граница |
|---|---|---|
| Memory/ESM | `core/memory.py` | canonical fact state |
| Standard promotion | `core/promotion_gateway.py` + canonical store primitive | reviewed `Validated` path |
| Read orchestration | `core/pipeline.py` | текущий `run()` mutation-read-only |
| Retrieval | `core/hybrid_retriever.py`, `core/ngram_index.py` | lexical baseline + optional dense/graph signals |
| Policy/write | `core/truth_gate.py`, `core/write_gate.py`, `core/policy_kernel.py` | trust/permission boundaries |
| Provenance/audit | `core/provenance_chain.py`, `core/audit_chain.py` | evidence о системных эффектах, не truth само по себе |
| MCP/tools | `api/mcp_gateway.py`, `core/mcp_transport.py`, `core/tool_registry.py` | authenticated server-wired capability surface |
| Remote LLM | `core/remote_egress.py`, `core/llm_router.py` | fail-closed egress + epistemic guard |
| Synaptic | reader/capsule/context/shadow surfaces | active answer authority не передан |

---

<a id="flows"></a>

## 🔄 L2 — текущие потоки

### Read/query

```text
query
  → API boundary
  → QueryPipeline
  → candidate narrowing / retrieval
  → FactsPackBuilder / Guardian / truth policy
  → structured result + TRACE
  → optional LLM rendering
```

**Current truth:** `core/pipeline.py::run()` read-only относительно canonical fact storage,
ESM promotion и causal-relation mutation. Старое описание, где legacy `POST /query`
выполняет promotion, больше не соответствует executable pipeline.

В legacy `server.py` ещё могут оставаться комментарии/docstrings со старой схемой; это
отдельный documentation-in-code debt, а не authority source над фактическим pipeline.

### Write/admission

```text
candidate/source
  → provenance/metadata
  → applicable write/ESM/policy checks
  → owning mutation service
  → CAS / required durable evidence
  → canonical state
  → derived projections / audit artifacts
```

Standard `Validated` promotion сходится на `PromotionGateway`, но это не означает одного
глобального owner для всех mutation families.

### MCP/tools

```text
HTTP/SSE MCP request
  → FastAPI auth (`require_api_key`)
  → `api.mcp_gateway`
  → capability/session resolution
  → `McpHandler`
  → `ToolRegistry`
```

На проверенной базе это **implemented + server-wired + auth-gated**. Но:

```text
wired
  ≠ enabled/exposed в каждой deployment configuration
  ≠ observed в конкретном runtime
  ≠ production authorization
```

---

## 🔍 Retrieval precision

`HybridRetriever` поддерживает lexical/BM25-style retrieval, dense embeddings, optional
graph signals и ranking fusion. Это capability, зависящая от dependencies/config:

```text
hybrid capability есть
  ≠ все optional dependencies установлены
  ≠ каждый signal выполняется на каждом query
  ≠ ranking score является evidence/truth authority
```

---

## 🧠 Evidence-use precision

```text
R = retrieved / selected
S = serialized into prompt
T = survives provider packing / transmission
U = demonstrably used by model
A = demonstrably supports final answer
```

R/S/T могут быть наблюдаемы bounded fixtures. Они не устанавливают U/A без отдельного
attribution evidence.

---

## 📄 Synaptic profile

```text
Raw evidence
  → SemanticReader
  → KnowledgeCapsule + SourceSpan
  → LLM Reader Adapter (main/tested; standalone caller)
  → Working Memory Gate (shadow-only)
  → ContextPack (shadow-only)
  → shadow evaluation (feature-gated; no answer authority)
```

Active Synaptic answer authority не передан. Shadow wiring не даёт Canon/ESM write
authority и не становится answer authority автоматически.

---

<a id="engineer"></a>

## 🧑‍💻 Инженерные границы

- read/retrieval не должен тихо становиться canonical write;
- derived indexes/vectors/graphs не выше Canon;
- remote/model output не self-admit в Canon;
- PolicyKernel denial не ослабляется routing preference;
- capability name не равен permission;
- TRACE/audit — observable artifacts, не proof hidden model cognition;
- `UNKNOWN` ≠ `FALSE` ≠ `ABSENT`;
- research/shadow implementation не получает runtime authority автоматически.

---

<a id="assurance"></a>

## 🧪 Architecture Assurance

```text
model / invariant
  → bounded implementation
  → deterministic tests / fault injection / load
  → retained metrics/evidence
  → correction
```

Текущая SQLite/concurrency evidence — bounded characterization, а не unlimited
multiprocess/network-filesystem/SLA/production-scale proof.

---

## 🚫 Atlas не утверждает

- zero hallucinations / absolute source truth;
- certified GDPR/compliance;
- independent security audit, которого не было;
- что все optional layers enabled;
- что MCP wiring = observed/deployed/production-authorized;
- что TRACE доказывает semantic use/answer support;
- что bounded V1 closure закрывает production-hardening P0/P1.

Production-hardening status: [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).
