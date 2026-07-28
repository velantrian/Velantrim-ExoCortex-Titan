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

### ⚠️ `data_mode=none` не проверяется по remote-data policy

Проверка remote-data применяется только при `data_mode != "none"`. Практическое
следствие: при `network=allow` **вместе с** `remote_data=never` вызов, который
объявил `data_mode="none"`, всё равно получит lease и уйдёт в сеть.

Так задумано — это metadata-запросы без пользовательской нагрузки (например,
discovery моделей). Но важно понимать границу гарантии: `data_mode` **объявляется
вызывающим и не верифицируется**, поэтому `remote_data=never` означает «ни один
вызывающий не заявил отправку данных», а не «данные технически не могли уйти».

Если нужно, чтобы наружу не уходило вообще ничего, включая metadata, — ставьте
`VELANTRIM_NETWORK_MODE=deny`: проверка сети идёт раньше и не зависит от
`data_mode`.

### Неверные значения ENV

Валидируются на старте: `server.py` вызывает `validate_egress_env()` и
**отказывается загружаться** при недопустимом значении.

Причина, по которой это делается на старте, а не лениво. `PolicyKernel` сам по
себе честно падает closed — но сервер при этом поднимается, `/health` отвечает
200, чтение работает, а `canonical_write_decision()` возвращает `False`, потому
что `lease_capability` при `policy_dependency_unavailable` отклоняет **все**
capability, включая локальные. То есть опечатка в одной переменной молча
переводила систему памяти в read-only: она выглядит здоровой и теряет входящие
факты. Теперь это явный отказ загрузки.

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
- `network=allow` не отменяет `remote_data=never` — но только для вызовов с
  `data_mode != none` (см. врезку выше).
- Provider connectivity test использует `data_mode=none`.
- STT/TTS и обычный чат используют `data_mode=raw`.
- `redacted` не считается реализованной очисткой автоматически: caller обязан
  явно передать `data_mode=redacted`.
- Policy parsing fail-closed; неверная конфигурация валит загрузку сервера.
- Gemini model id, попадающий в **путь** URL, проходит структурную валидацию
  (`assert_safe_gemini_model_id`) во всех трёх точках сборки URL —
  `llm_router`, `llm_stream`, `tts_router`. Без неё `model` из тела запроса
  позволял управлять путём и query credentialed-запроса.
- Устаревшие/некаталожные модели отклоняются `assert_model_allowed()` **до**
  получения lease.
- Hardened production profile закрепляет `VELANTRIM_NETWORK_MODE=deny` и
  `VELANTRIM_REMOTE_DATA_MODE=never` явно; это проверяет
  `scripts/validate_production_profile.py`.
