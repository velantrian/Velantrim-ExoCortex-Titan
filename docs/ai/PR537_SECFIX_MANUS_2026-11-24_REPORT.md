# PR #537 — Security fix по аудиту Manus (2026-11-24) — отчёт и hand-off для независимого ре-аудита

**Статус:** RESEARCH, не Canon. Draft PR #538 (base — ветка #537), НЕ смержен, НЕ задеплоен. `ENABLE_SOURCE_X_GATE` выключен по умолчанию и во всех профилях; включается только внутри изолированных тестов. Исполнитель (Grok-bot) — не утверждающий аудитор: ниже только факты и команды для воспроизведения; выводы о безопасности делает независимый ревьюер.

## 0. Исходное состояние (проверено 2026-11-24 перед началом)

| | SHA | CI |
|---|---|---|
| PR #537 head | `59c6b0a6329d331534dd3fcfb5a3da48b0fc23cb` (совпал с ожидаемым) | все проверки SUCCESS, `Titan aggregate merge evidence` PENDING (Draft) |
| PR #536 head | `9048bcd5c7a41717a111cb6d1e9e81a74551910d` (совпал) | то же; не используется как база, не объединяется |
| base `main` | `ad92aa0a709f4334bde048e907bb83295a36b061` | — |

Новая ветка `fix/pr537-secfix-manus-2026-11-24` от `59c6b0a`; свежий клон; опубликованная ветка #537 не изменялась.

## A. CHANGELOG

### P0-1 — утечка текста исключений провайдера LLM (`server.py`)
Механизм (а не один пример): все ответы/логи об ошибке LLM на затронутых путях строятся из `_llm_error_info()` — закрытый набор кодов (`llm_provider_error`, `llm_context_limit`, `llm_context_overflow`), тип исключения (regex-валидация), HTTP-статус (int 100–599), имя провайдера (regex). `str(exc)` и произвольный `exc.code` не используются. Не зависит от `ENABLE_SOURCE_X_GATE`.
- `server.py:287–378` — `LLM_PROVIDER_ERROR_CODE`, `_llm_error_info`, `_llm_error_message`, `_log_llm_error`, `_raise_if_context_error` (413-детали пересобираются из валидированных полей, `from None`; `LlmContextConfigError` — без изменений, это текст Titan о настройке).
- `/chat` `server.py:2223–2234` — лог только code/type/status; HTTP **400 сохранён** (совместимость), detail = стабильный текст `llm_provider_error: … (HTTP N)[подсказка Titan]; provider details were withheld.`; offline fallback без изменений.
- `/chat/stream` `server.py:2522` (`_LlmStreamError`), `:2633` (сообщение провайдера из события `error` больше не переносится), `:2655` (лог), `:2740–2745` (событие `error` = `code` + безопасный текст).
- `/query` `server.py:3135–3147` — `llm_answer = "[LLM error: <безопасный текст>]"`, `llm_meta = {error: <code>, error_type, status_code?, error_redacted: true}` при любом состоянии флага; лог без текста.
- `tests/test_source_x_gate_audit_round2.py` — один assert обновлён: он фиксировал старый небезопасный контракт (флаг off → `llm_meta.error = str(exc)`); теперь проверяет безопасный код и отсутствие текста. Это не ослабление: проверка стала строже.

### P0-2 — ложное разрешение Soft L1 (`core/source_x_gate.py`)
- `core/source_x_gate.py:394–549` — `refusal_assessment()` → `refusal | negated_refusal | ambiguous | none`: отрицание отказа («неверно, что…», «неправда», «not true that», «нельзя сказать», «never said», «contrary to»), отрицание исключающего отказа («не исключены», «not excluded»), контраст («напротив», «тем не менее», «instead»), чужая речь («заявил», «said»), оговорки («возможно»), условия («если», «if»), вопросы, неотрицаемое утверждение использования/значения в клаузе не про официальные цифры (с исключением «источник X приводит/cites …»). `text_contradicts_refusal()` проверяет другие предложения (отрицание отказа; контраст/анафора + утверждение использования). `is_explicit_refusal_sentence()` = `refusal_assessment(...) == "refusal"`.
- `core/source_x_gate.py:559, 585` — `classify_l1_hits` пишет `refusal_kind` и `refusal_contradicted_elsewhere`.
- Это эвристика по шаблонам, **не семантическое понимание**. Политика Soft L1 не расширена: изменения только сужают условия, при которых он разрешает выдачу.
- Расширение `_REFUSAL_RE` («исключён», «do not use», «don't use»; `/workspace/tz/refusal-widening-uncommitted.patch`) **НЕ включено**: оно расширяет Soft L1 (больше разрешений), а ТЗ требует не расширять политику шире необходимого; два известных over-block корпуса остаются.

### Тесты и данные
- `tests/test_pr537_secfix_provider_errors.py` — 13 сценариев × флаг (unset/0/1) = 39, через HTTP (`TestClient(server.app)`), маркер `SENSITIVE_PROVIDER_ERROR_218` в теле ошибки провайдера (реальный код `core/llm_router` / `core/llm_stream`) или в исключении/`exc.code`; проверяются HTTP body, `llm_answer`, `llm_meta`, `caplog` (сообщения, args, traceback), 413-тексты, успешный ответ, offline fallback.
- `tests/test_pr537_secfix_soft_l1.py` — 39 сценариев (статус, фактически возвращённый текст, публичная запись), HTTP `/chat` и `/query` с флагом on, flag-off без изменений, probe-набор (6 известных пробелов как `xfail(strict=True)`).
- `tests/fixtures/source_x_soft_l1_contradiction_cases_2026-11-24.json` — 39 новых RU/EN текстов (нет в корпусе 66), роль REGRESSION.
- `tests/fixtures/source_x_soft_l1_probe_2026-11-24.json` — 25 текстов, написаны после первой версии эвристики; первый прогон до правок записан в файле; после него добавлены 3 шаблона, поэтому набор **не held-out**.
- `scripts/eval_source_x_soft_l1_cases.py` — согласие / false allow / false block по трём наборам.

## B. PATCH

`git diff 59c6b0a..5d13b2a`: 8 files, +1243 / −22 (код: `server.py` +148/−, `core/source_x_gate.py` +180/−; остальное — тесты, фикстуры, скрипт). Документы — отдельный коммит после него.

## C. REGRESSION EVIDENCE (Python 3.11.18, venv с зависимостями проекта)

RED: `59c6b0a` + новые тестовые файлы (копия дерева через `git archive`):
```
python -m pytest tests/test_pr537_secfix_provider_errors.py tests/test_pr537_secfix_soft_l1.py -q --timeout=120
→ 49 failed, 55 passed, 5 xfailed
```
- провайдер: 21 failed (все 7 «утечечных» сценариев × 3 состояния флага), 18 passed (контроли: успех, offline fallback ×2, 413 limit/overflow — они были корректны и раньше);
- Soft L1: 20 сценариев (все отрицания/противоречия/неоднозначности), `refusal_assessment` отсутствует, 2 HTTP-проверки, 5 probe (4 атаки + `probe_legit_10`, который на `59c6b0a` проходил, а теперь заблокирован — **новая ложная блокировка**, см. риски).

GREEN: `5d13b2a` — те же файлы: provider 39 passed; Soft L1 64 passed, 6 xfailed.

Метрики Soft L1 (`scripts/eval_source_x_gate_corpus.py`, `scripts/eval_source_x_soft_l1_cases.py`):

| Набор | `59c6b0a` | `5d13b2a` |
|---|---|---|
| корпус 66 (REGRESSION baseline) | 64/66; blocking recall 29/29; precision 29/31 | **без изменений** (вывод идентичен) |
| six-model fixtures (25) | 25/25 | 25/25 |
| contradiction scenarios (39) | 19/39, false allow 20, false block 0 | 39/39 |
| probe (25; не held-out) | false allow 8, false block 1 | false allow **4**, false block **2** |
| probe, первый прогон до 3 добавленных шаблонов | — | false allow 5, false block 2 |

Ложные блокировки показаны отдельно: на probe +1 (`probe_legit_10`: «21.8 and 7.6 are not included; the official numbers above are used instead.» — из-за «instead»).

Полный набор:
```
python -m pytest tests/ -q --timeout=300   # VELANTRIM_API_KEY=ci-test-key
59c6b0a: 5081 passed, 17 skipped, 1 xfailed
5d13b2a: 5184 passed, 17 skipped, 7 xfailed, 0 failed
```
Пропуски (17, как и на base): `ladybug` не установлен (1), `test_adversarial` требует запущенный сервер на :8000 (8), Core-3 рядом нет (3), `reportlab`/`pptx` не установлены (5). xfail: 1 старый + 6 известных пробелов probe.

Ruff (`ruff check core/` + новые файлы) — чисто; `ruff check server.py` — 1 старая ошибка N812 (импорт версии, не из этого PR; CI проверяет `core/`). Mypy `core/` — 357 файлов без ошибок. Architecture-freeze (GITHUB_BASE_REF=main) — OK.

## D. CI EVIDENCE

См. PR #538 (checks на точном head). PR открыт против ветки #537, поэтому workflow с фильтром `branches: [main]` (CodeQL, часть supply-chain) на нём **не запускаются** — для них статус UNKNOWN на этом head. Итоговые статусы — в ответе исполнителя и в комментариях ревью.

## E. RISK REGISTER

**FIXED (исправлено и испытано в пределах тестов):**
- Текст исключения провайдера в `/chat` 400, `/chat/stream` error, `/query` `llm_answer`/`llm_meta`, 413-деталях, логах этих путей — при флаге unset/0/1 (39 HTTP-тестов).
- Произвольный `exc.code` больше не попадает в ответ.
- Отрицание отказа / отказ-затем-использование / оговорки / условия / вопросы / чужая речь в контрольных случаях (39 сценариев) больше не дают `FLAG_L1_REFUSAL`.

**OPEN (подтверждённый риск остаётся):**
- Soft L1 на шаблонах обходится: 4 известные ложные «разрешения» в probe (`probe_attack_03/04/06/10`, напр. «Хотя 21,8 формально не публикуется, расчёт построен на ней.»). Попытка закрыть их правилом для уступительных конструкций дала 10 ложных блокировок на реальных ответах моделей (six-model fixtures) и была откатана. Закрытие требует решения владельца (архитектура/политика): напр. Soft L1 по умолчанию выключен под отдельным флагом, или только жёсткий шаблон отказа. Не сделано.
- Новые ложные блокировки: `probe_legit_09` (было и раньше), `probe_legit_10` (новая).
- `api/llm_routes.py` (`/console/llm/test`, `/llm/test`, STT/TTS) возвращает `str(exc)` провайдера по замыслу (диагностика ключа) — прямой обход общего механизма; вне названных в ТЗ эндпоинтов, не менялось.
- Логи не-провайдерных ошибок с текстом сообщения: `chat pipeline` (`server.py` `logger.exception`), `query/roles failed`, `generic_exception_handler`.
- Из отчёта Manus/предыдущих раундов, не менялись: evidence-поля (`facts`, `memory_*`, `dialogue_essence`, essence, `query`) — PROPOSED ADR; trace/events/audit-данные; SleepTimeWorker / notebook и MCP gateway Gate-ом не защищены (не объявлять защищёнными).
- TEXT MATCH ≠ SOURCE PROVENANCE: совпадение чисел не доказывает происхождение.

**UNKNOWN:**
- Поведение на живом провайдере (реальные форматы ошибок) — только фейк и синтетические исключения.
- CodeQL / supply-chain на этом head (не запускаются для base ≠ main).
- Качество эвристики на независимом корпусе — независимого корпуса нет.

## F. REVIEW HANDOFF (для Manus)

Проверить только изменённые пути и связанные границы доверия:
1. `server.py:287–378`, `:2215–2240`, `:2522–2530`, `:2625–2660`, `:2735–2750`, `:3130–3150` — есть ли путь, где `str(exc)`/`exc.args`/`exc.detail`/`exc.code` провайдера всё ещё попадает в HTTP-ответ, SSE или лог на `/chat`, `/chat/stream`, `/query` (включая `__cause__`/traceback).
2. `core/source_x_gate.py:394–590` — новые обходы Soft L1; ложные блокировки допустимых отказов.
3. Воспроизведение (без доверия к выводам исполнителя):
```
git fetch origin fix/pr537-secfix-manus-2026-11-24 && git checkout 5d13b2a
VELANTRIM_API_KEY=ci-test-key python -m pytest tests/test_pr537_secfix_provider_errors.py tests/test_pr537_secfix_soft_l1.py -q
python scripts/eval_source_x_gate_corpus.py; python scripts/eval_source_x_soft_l1_cases.py
# RED: git archive 59c6b0a | tar -x -C /tmp/base && cp tests/test_pr537_secfix_*.py /tmp/base/tests/ && cp tests/fixtures/source_x_soft_l1_*_2026-11-24.json /tmp/base/tests/fixtures/
```

## Ответы на 6 вопросов самопроверки (§10 ТЗ)

1. **Механизм или пример?** Механизм на затронутых путях: единая функция строит ответ/лог из закрытого набора полей, `str(exc)` не используется ни в одной ветке `/chat`, `/chat/stream`, `/query`, `_raise_if_context_error`; тесты подставляют маркер и через тело ответа провайдера (реальный код роутера), и через исключение, и через `exc.code`. Для Soft L1 — исправлен класс «отрицание/противоречие в шаблонных формах», но не класс «любое утверждение использования»: известные обходы остаются (OPEN).
2. **Прямой обход нового обработчика?** Да, вне scope: `api/llm_routes.py` (тест ключа, STT/TTS) возвращает текст исключения провайдера; generic handler и не-провайдерные логи пишут сообщения. Для Soft L1 — 4 известных обхода в probe.
3. **Ложные блокировки Soft L1?** Да, немного: корпус 66 и 25 реальных ответов моделей — без изменений (0 новых), probe — 1 новая ложная блокировка (`instead`). Правило, которое закрыло бы больше обходов, давало 10 ложных блокировок и откатано.
4. **Скрытая зависимость от флага/порядка?** Обработка ошибок от флага не зависит (тесты unset/0/1). Порядок: `_raise_if_context_error` по-прежнему до offline fallback (контекстный отказ не подменяется). Soft L1 работает только при включённом флаге. Тесты HTTP закрепляют `server.API_KEY`, т.к. другой тестовый модуль переимпортирует `server`.
5. **Изменилась ли внешняя семантика API?** Да, в пределах ТЗ: значение `llm_meta.error` (код вместо текста), новые ключи `error_type`/`status_code`/`error_redacted`, текст `llm_answer` и `detail` для ошибки провайдера, у SSE `error` добавлен `code`. HTTP-статусы не менялись (400/413/500). Рекомендация (не сделано): 502 для ошибок провайдера в `/chat` — отдельное изменение контракта.
6. **Что недоказано?** Безопасность на живом провайдере; полнота механизма вне трёх эндпоинтов; качество Soft L1 на независимом корпусе; CodeQL/supply-chain на этом head; отсутствие утечек через трассировки при уровнях логирования/хендлерах, отличных от тестовых.

## Итоговый статус

**READY FOR INDEPENDENT RE-AUDIT** — с явным OPEN по Soft L1 (эвристика обходима; закрытие требует решения владельца) и по `api/llm_routes.py`. Не заявляется глобальная безопасность.
