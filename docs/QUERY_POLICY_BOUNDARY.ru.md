# 🛡️ Titan Query / Policy Boundary

**Статус:** исполнимый P0-контракт
**Связано:** GitHub issues #50 и #53
**Дата:** 2026-07-25

## 1. Зачем существует эта граница

До этого среза обычный запрос был одновременно чтением и скрытым ingestion:

1. retrieval возвращал строку;
2. `build_facts_pack()` повторно вызывал `store_fact()`;
3. NGram обновлялся из query-path;
4. успешный legacy confidence-floor продвигал факт в `Validated`;
5. causal extractor сохранял `hypothetical` relation;
6. cross-domain bridge мог сохранить `analogous_to`;
7. fire-and-forget reconsolidation снова вызывал `store_fact()`.

В результате операция «ответить на вопрос» могла менять факты, ESM, метаданные
и граф отношений ещё до отдельного review/ingestion решения.

## 2. Новый основной контракт

```text
QueryPipeline
  retrieval
  → canonical resolve
  → policy-filtered FactsPack
  → provenance/Guardian
  → evidence sufficiency
  → read-only contradiction lookup
  → bounded answer or AnalysisProposal

Ingestion / maintenance
  candidate
  → schema + provenance
  → PolicyKernel
  → WriteProtocolGate
  → TruthGate / ESM
  → canonical SQLite transaction
  → VersionStore + AuditChain
```

### QueryPipeline не имеет права:

- создавать отсутствующий canonical fact;
- обновлять существующий fact во время recall;
- менять `epistemic_state`;
- маркировать trace как будто promotion произошёл;
- индексировать неизвестную retrieval-строку;
- создавать causal или cross-domain relation;
- запускать reconsolidation или adaptive-state mutation;
- использовать произвольный `Observed` как fallback evidence;
- ослаблять policy при недоступности компонента.

### QueryPipeline имеет право:

- читать Canon и проекции;
- заменять stale projection payload текущим canonical payload;
- фильтровать по состоянию и режиму;
- показывать существующие contradictions;
- возвращать causal candidate как `proposal_only`;
- выдавать честный bounded answer;
- показывать canonical user report как **неподтверждённое сообщение
  пользователя**, не как мировой факт.

## 3. Разрешённый user-report recall

Полный запрет всех `Observed` ломает базовую персональную память: только что
сохранённое «my name is Ruslan» исчезает до фоновой валидации. Поэтому введено
узкое правило, не смешивающее личный отчёт и истину о мире.

`Observed` можно отобразить, только если одновременно:

```text
canonical_record = true
origin_type = USER_REPORTED
claim_type != WORLD_FACT
source is present and source != unknown
```

Такой элемент получает:

```text
truth_status = UNVERIFIED
reported_only = true
```

Он не продвигается, не становится `VERIFIED` и в offline UI получает подпись
«not validated yet». External `Observed WORLD_FACT` этим исключением не
пользуется.

## 4. Bounded answer

Если нет policy-eligible подтверждённых локальных данных:

```json
{
  "answer": "Недостаточно подтверждённых локальных данных.",
  "error": null,
  "facts": [],
  "insufficient_evidence": true,
  "reason_code": "..."
}
```

Стабильные причины текущего среза:

| Reason code | Значение |
|---|---|
| `no_local_retrieval_results` | локальный retrieval ничего не нашёл |
| `no_policy_eligible_local_evidence` | кандидаты найдены, но исключены policy/ESM |
| `truth_gate_rejected` | реальный TruthGate отклонил candidate pack |
| `insufficient_validated_local_evidence` | renderer не получил Validated/Supported или безопасный user report |
| `real_truth_gate_unavailable` | production gate недоступен; MVP fallback не используется |
| `unknown_cognitive_mode:*` | неизвестный режим не откатывается к слабому гейту |

`error=null` здесь принципиален: нехватка доказательств — нормальное
ограниченное состояние, а не сбой сервера.

## 5. Causal proposals

Causal regex больше не вызывает `CausalGraph.add_relation()` на recall.
Он формирует детерминированный:

```json
{
  "proposal_id": "causal-proposal:<stable hash>",
  "relation_id": null,
  "type": "implies",
  "status": "hypothetical",
  "review": "pending",
  "disposition": "proposal_only"
}
```

Одинаковая пара фактов и тип дают один `proposal_id`. Реальный `relation_id`
может появиться только после отдельного review/ingestion действия.

## 6. PolicyKernel

`core/policy_kernel.py` отделяет полномочия от оптимизации.

### Типы

| Тип | Назначение |
|---|---|
| `EffectivePolicy` | итоговые hard restrictions |
| `PolicySnapshot` | неизменяемый снимок policy + health |
| `PolicyDecision` | allow/deny с reason code и snapshot id |
| `CapabilityLease` | ограниченное разрешение конкретной capability |

### Текущие P0-инварианты

```yaml
network: deny
remote_data: never
canonical_write_provider: local
remote_canonical_write_allowed: false
write_gate_required: true
fail_closed: true
```

`ENABLE_WRITE_GATE=0` больше не отключает безопасность. Поле оставлено для
совместимости и диагностики; ложное значение логируется и игнорируется.

### Fail-closed

Если local config или MetaSupervisor недоступен:

```text
PolicySnapshot.source =
  last_verified_fail_closed | safe_default_fail_closed

writes_allowed = false
reason_code = policy_dependency_unavailable
```

Последняя проверенная политика сохраняет ограничения, но не даёт разрешение
на canonical write при неизвестном runtime health.

## 7. HTTP / structured write outcomes

Добавлен `WriteStatus.REJECTED_POLICY`. Он отделён от:

- `REJECTED_SAFE_MODE`;
- `REJECTED_WRITE_GATE`;
- `REJECTED_VALIDATION`;
- storage/internal failures.

`WritesBlockedError` переносит безопасный `reason_code` и `snapshot_id`.
HTTP `/facts` возвращает controlled `503` для `REJECTED_POLICY` и
`REJECTED_SAFE_MODE`, а не ложный `200/201`.

## 8. Доказательства и residual scope

Регрессионные тесты проверяют:

- `build_facts_pack()` не пишет новый retrieval row;
- существующий canonical row не меняется;
- non-canonical projection не может сам объявить себя `Validated`;
- `Observed` не продвигается на query;
- causal hints не создают relation rows;
- неизвестный cognitive mode блокируется;
- недоступный real TruthGate не откатывается к MVP;
- policy dependency failure отклоняет durable write;
- remote canonical write не получает lease;
- user-reported personal recall остаётся доступным и честно маркированным.

Не входят в этот срез:

- durable `ProjectionOutbox/ProjectionCoordinator`;
- отдельный публичный `IngestionPipeline` API;
- relation/erasure/archive closure issue #50;
- persisted policy snapshots и replay store;
- ADAO shadow planner;
- consent/redaction gateway для remote capabilities.

Эти части должны развиваться отдельными PR с собственными транзакционными
контрактами и тестовыми доказательствами.
