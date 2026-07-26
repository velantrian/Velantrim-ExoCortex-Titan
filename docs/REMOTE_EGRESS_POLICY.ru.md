# 🔒 Remote Egress & Epistemic Boundary

## Статус

Начиная с `titan-policy-v2`, серверные вызовы внешних LLM, STT и TTS
**запрещены по умолчанию** и должны получить capability lease от
`core.policy_kernel.PolicyKernel`.

Это относится к серверному runtime. Браузерный GitHub Pages PWA выполняет
прямые browser-to-provider запросы и требует отдельной browser security
модели.

## Конфигурация

```env
# Полностью local-first — defaults
VELANTRIM_NETWORK_MODE=deny
VELANTRIM_REMOTE_DATA_MODE=never
```

Для явного разрешения внешнего LLM/STT/TTS:

```env
VELANTRIM_NETWORK_MODE=allow
VELANTRIM_REMOTE_DATA_MODE=allowed
```

### Network mode

| Значение | Поведение |
|---|---|
| `deny` | Любой remote network capability блокируется |
| `ask` | Блокируется до появления consent broker |
| `allow` | Сеть разрешена, но отдельно проверяется remote-data policy |

### Remote-data mode

| Значение | Поведение |
|---|---|
| `never` | Пользовательские и memory payload запрещены |
| `redacted` | Разрешён только вызов с `data_mode=redacted` |
| `allowed` | Разрешён raw payload |

Неверные значения ENV не приводят к fallback-разрешению: snapshot получает
`policy_dependency_unavailable`, а egress блокируется.

## Execution boundary

```text
LLM / STT / TTS request
        │
        ▼
ensure_remote_egress_allowed()
        │
        ▼
PolicyKernel.lease_capability(
  locality="remote",
  requires_network=True,
  data_mode=none|redacted|raw
)
        │
   ┌────┴────┐
   │         │
 DENY      ALLOW
   │         │
 no HTTP   provider call
```

## Epistemic compatibility guard

Старый console prompt называл весь список memory rows «верифицированными
фактами». При console fallback туда могли попадать `Observed` записи.

До завершения структурного `EvidenceBundle` remote boundary:

1. удаляет ложные формулировки `verified memory / Верифицированные факты`;
2. добавляет обязательную инструкцию не повышать epistemic state;
3. требует квалифицировать Observed, Hypothesized и fallback memory как
   неподтверждённые.

Это safety shim, а не конечная модель. Целевая архитектура должна передавать
провайдеру структурированные секции:

```text
VERIFIED_EVIDENCE
REPORTED_MEMORY
HYPOTHESES
```

## Инварианты

- Ни один серверный provider call не открывает HTTP connection до lease.
- `network=allow` не отменяет `remote_data=never`.
- Provider connectivity test использует `data_mode=none`.
- STT/TTS и обычный чат используют `data_mode=raw`.
- `redacted` не считается реализованной очисткой автоматически: caller обязан
  явно передать `data_mode=redacted`.
- Policy parsing fail-closed.
