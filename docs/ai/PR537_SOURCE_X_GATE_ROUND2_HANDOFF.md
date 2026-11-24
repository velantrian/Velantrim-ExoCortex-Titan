# PR #537 — Source-X Gate, hardening round 2 — HANDOFF для независимого аудита

**Статус:** Draft PR, НЕ смержен, НЕ задеплоен. `ENABLE_SOURCE_X_GATE` выключен по умолчанию и во всех профилях (`lite` / `standard` / `heavy`); включается только внутри изолированных тестов. RESEARCH, не Canon. PRODUCTION NOT AUTHORIZED. Operator GO не установлен.

## SHA

| | SHA |
|---|---|
| Base (`main`) | `ad92aa0a709f4334bde048e907bb83295a36b061` |
| Old head (round 1, проаудирован) | `149f4770535b74a85f14ee2f39ef1d917792bd00` |
| New head — код round 2 | `7805f523c62df753e2cb457f54bddaea1f5548b2` |
| New head — этот hand-off | коммит, следующий за `7805f52` на ветке `fix/source-x-gate-audit-hardening-2026-11-23` (только `docs/ai/*`) |

Diff stat `149f477..7805f52`: 12 files changed, 1413 insertions(+), 87 deletions(-)
(`server.py` +422/−, `core/source_x_gate.py` +326/−, `tests/test_source_x_gate_audit_round2.py` +546, ADR amendment +60, PROPOSED ADR +77, `core/event_bridge.py`, `.env.example`, `KNOWN_RISKS.md`, `WORK_LOG.md`, корпус/скрипт/тест корпуса).
Diff stat `ad92aa0..7805f52`: 14 files changed, 3111 insertions(+), 61 deletions(-).

## Что изменено по пунктам

### P0-01 — безопасность логов
- `safe_log_record(verdict, surface)` / `safe_notes_log`: только `event`, `blocked`, `flagged`, `hits[{rule, level, start, end}]`, `official_14_2`, `official_3_1_pct`, `all_l1_in_refusal_sentences`.
- Все вызовы логгера Gate переведены на них; `exc_info=True` удалён везде — при исключении логируется только тип.
- `blocked_attempt_log` (с excerpt) остаётся in-memory, docstring: «NEVER log this».
- Хеши исходного текста НЕ вводились.

### P0-02 — граница вывода (флаг ON)
- `/query/roles`: каждый `lens_context.branches[i].response` проходит `gate_final_text` (surface `query_roles_branch_{i}`), вердикты — в `source_x_gate.branches`.
- `llm_meta.error` → `{"error": <ТипИсключения>, "code"?: str, "error_redacted": "source_x_gate"}`.
- Полный сериализованный ответ `/query`, `/query/roles`, `/chat` проходит `sanitize_outbound`: строгий L1-скан каждого строкового листа, попадание → `[withheld: source-X gate]`, пути — в `source_x_gate.outbound.withheld_paths`; уже прогнанные через Gate поля (answer / llm_answer / reply / branches.response) не сканируются повторно; при внутренней ошибке — fail-closed (все неисключённые листы скрываются), при ошибке обёртки — HTTP 500 `source_x_gate_outbound_error`.
- `/chat/stream`: явный allowlist ключей по типу события (`essence`, `context`, `token`, `done`, `final`, `error`); неизвестные типы отбрасываются; `context.report` — только ключи `ContextReport`; `usage` / `llm_usage` — только числа; затем тот же outbound-скан.
- `facts`, `memory_*`, `dialogue_essence`, `essence.snapshot`, `query` — НЕ изменены (политика доступа к evidence не менялась); попадания в них фиксируются только путём в `source_x_gate.outbound.evidence_exempt_paths_with_hits`. Data-flow map и варианты — `docs/adr/ADR-2026-11-24-source-x-evidence-surfaces-PROPOSED.md` (статус PROPOSED).

### P1-01 — целостность вердикта
- `merge_with_prior_verdict`: повторная проверка не может понизить вердикт pipeline (GATE_ERROR > BLOCKED_ATTEMPT > FLAG_L1_REFUSAL > FLAG_REVIEW > ALLOW > NO_ANSWER).
- Публичная запись: `status`, `reason` (`source_x_figures`, `no_answer_produced`, `gate_exception:<Type>`, `stream_buffer_limit`, `stream_deadline`), `origin` (`pipeline` / `final_check`); `delivered=false` для NO_ANSWER.
- Сводка без текста (status / blocked / reason / origin / rules) пишется в metadata reasoning-trace и в событие `RESPONSE_GENERATED` (`core/event_bridge.on_query_completed(source_x_gate=...)`).

### P1-02 — ресурсы
- Буфер ограничен по UTF-8 байтам (`SOURCE_X_GATE_STREAM_MAX_BYTES`, 262 144); общий дедлайн генерации (`SOURCE_X_GATE_STREAM_DEADLINE_S`, 180 с); keep-alive — SSE-комментарий `: hold` без содержимого (`SOURCE_X_GATE_STREAM_KEEPALIVE_S`, 10 с), отправляется по времени, в том числе пока идут токены — это нужно, чтобы под ASGI 2.4 обнаружить отключение клиента.
- Переполнение / дедлайн → `GATE_ERROR` (`stream_buffer_limit` / `stream_deadline`), удерживаемый текст очищается, провайдер закрывается (`aclose`), офлайн-подстановки нет.
- Чтение провайдера через задачу (`_source_x_guarded_events`), `finally` отменяет ожидание и закрывает генератор; потребление под `contextlib.aclosing`.

## RED / GREEN

| Набор | `149f477` (old) | `7805f52` (new) |
|---|---|---|
| `tests/test_source_x_gate_audit_round2.py` (22 теста, в репо) | **16 failed, 6 passed** | **22 passed** |
| Исходные 10 аудит-тестов без изменений (scratch, вне репо) | **10 failed** | 6 passed, 4 failed — все 4 только из-за evidence-полей (`facts`, `memory_*`, `dialogue_essence`, `essence.snapshot`), которые по ТЗ не меняются |

Шесть тестов, проходящих на old head: адаптированные `test_p0_query_fields` / `test_p0_chat_fields` (evidence-поля разрешены), `test_r2_flag_off_responses_unchanged`, `test_r2_client_disconnect_closes_provider[2.3]`, `test_r2_generation_cancel_closes_provider`, `test_r2_parallel_requests_are_isolated` — это охранные тесты поведения, которое уже было корректным.

## Полный регресс (локально, Python venv, `pytest tests/ --timeout=300`)

| Ветка | Результат |
|---|---|
| main `ad92aa0` | 5023 passed, 17 skipped, 1 xfailed |
| old head `149f477` | 5058 passed (локально и в CI) |
| new head `7805f52` | **5081 passed, 17 skipped, 1 xfailed**, 0 failed |

Также: `ruff check core/` — чисто; `mypy core/` — 357 файлов без ошибок; architecture-freeze (GITHUB_BASE_REF=main), version/branding, tracked-artifacts, project-state, kb-graph — OK. (`ruff check server.py` даёт одну старую ошибку N812 в строке импорта версии, не из этого PR; CI проверяет только `core/`.)

## Пиковая память (tracemalloc, `/chat/stream`, флаг ON, 20 000 уникальных чанков по 1 KiB ≈ 19,5 MiB)

| | Пик | Прочитано чанков | Итог |
|---|---|---|---|
| old `149f477` | **40,38 MiB** | 20 000 | ALLOW, лимита нет |
| new `7805f52` | **0,52 MiB** | 257 | GATE_ERROR / `stream_buffer_limit`, провайдер закрыт, текст не выдан |

## CI

CI зелёный на `149f477` (lint-and-test, CodeQL, coverage ratchet, docker, SBOM, audit, wheel, bounded-pilot, browser-acceptance, evaluate-pull-request — SUCCESS; Titan aggregate merge evidence — PENDING, т.к. Draft). Для коммитов round 2 CI ещё не запускался: см. «Открытые вопросы».

## Documentation impact

`GITHUB_AND_NOTION` (по `docs/ai/DOCUMENTATION_SYNC_PROTOCOL.md`: runtime-wiring, безопасность, новые функции). Notion access: UNAVAILABLE (запись в Notion в этой задаче не разрешена), Notion synchronization: HANDOFF_REQUIRED, `docs/ai/NOTION_HANDOFF.md#handoff-pr-537`; Notion-запись — **PENDING**.

## Корпус

66 текстов — **REGRESSION-набор, НЕ независимый бенчмарк** (тот же автор писал, размечал и подстраивал паттерны). Пометка есть в JSON (`role: REGRESSION`), в выводе `scripts/eval_source_x_gate_corpus.py`, в тесте корпуса, в ADR и в теле PR.

## Открытые вопросы

1. Коммиты round 2 не запушены: push-guard рабочего клона (`pushurl DISABLED`) не обходился. Нужен push владельцем или разрешённым способом; после него — CI и обновление тела PR.
2. Решение по PROPOSED ADR (evidence-поля, включая `query` — эхо собственного ввода пользователя; исключение `query` — решение исполнителя, требует подтверждения).
3. Не-Gate лог `server.py` «LLM генерация упала: %s» может содержать текст исключения провайдера.
4. Выводы вне четырёх эндпоинтов (SleepTimeWorker / notebook, TTS, MCP gateway) Gate не покрывает.
5. Независимый размеченный корпус и второй рецензент.
6. Покрытие (coverage ratchet) локально не измерялось — проверит CI.

## Что явно НЕ сделано

Нет merge, deploy, включения флага в каком-либо профиле, production-активации, вызовов моделей, изменений Canon / ESM, записи в Notion, force push, `--admin`, обхода rulesets или push-guard; политика доступа к evidence не менялась; хеши текста в логи не добавлялись.
