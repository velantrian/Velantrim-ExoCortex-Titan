# 🔱 VELANTRIM Titan — Глубокий аудит (2026-07-28)

> **Проверенный HEAD:** `b14de0201b0009bbbd98a9111972a2413d2730f0` (main, 2026-07-28).
> Все ссылки `file:line` ниже перепроверены против **именно этого** коммита.
>
> **Метод:** multi-agent повторный аудит. 6 параллельных research-агентов (read-only, без единой правки кода):
> (1) ре-верификация всех 28 находок аудита `AUDIT_DEEP_2026-06-06.md` против HEAD;
> (2) security-срез (SSRF/injection/auth/XSS/SAFE_MODE); (3) concurrency/write-integrity срез (canonical write
> protocol, hash-цепи); (4) аудит двух НОВЫХ, ранее не проверявшихся кластеров функциональности
> (crystal-transfer, synaptic-контракты); (5) свежий sweep на rename-drift/silent-except по всему `core/`;
> (6) здоровье CI/тестов + отдельная проверка GDPR-erasure саги.
> Один спорный момент (RAR zip-bomb guard) между агентами разошёлся — перепроверен вручную лично, чтением кода.
>
> **Это НЕ отчёт «применил фиксы».** Это только диагностика. Ни один файл кода в репозитории не менялся.
> Находки — диагностика, а не implementation truth: единственный источник истины о состоянии кода — сам код на
> указанном коммите. Фиксы идут отдельными PR (H1/H2 — в `claude/fix-budget-velum-dead-paths`).
>
> **Ре-верификация 2026-07-28 (после PR #63 и #64).** Первая редакция этого отчёта снималась против `ac62961`.
> Затем main продвинулся на 2 коммита — `731b44d` (PR #63, hardened production profile) и `b14de02`
> (PR #64, коррекция заявлений этого профиля). Отчёт перебазирован на `b14de02` и перепроверен:
> **все пять High-находок H1–H5 воспроизводятся без изменений**; ни один из двух коммитов не тронул runtime-код
> (`core/`, `api/`, `server.py`, `migrations/` — пусто в diff), поэтому ни одна находка не закрыта и не
> регрессировала. Что изменилось — см. врезку «Влияние PR #63/#64» ниже.
>
> ---
>
> ### 📌 Post-merge заметка, 2026-07-28 (после PR #66) — H1/H2
>
> **PR #66 восстановил оба сигнала, но вместе с этим включил небезопасные пути применения.** Post-merge
> review дал 9 нерешённых замечаний (7×P1, 2×P2):
>
> * **H1** — сигнал стал живым, но `_evaluate()` проверял восстановление *раньше* эскалации и не включал
>   бюджет в условие recovery. Итог: стор выше `budget_block` осциллировал HEALTHY↔DEGRADED каждый heartbeat
>   и никогда не доходил до SAFE_MODE. Дополнительно: игнорировался `ENABLE_MEMORY_BUDGET=0` (отключённая
>   фича уводила систему в DEGRADED), а пороговые логи `evaluate_budget()` дублировались 6 раз в минуту.
> * **H2** — применение нарушало AGENTS.md §«Canonical memory boundary» (background read-путь мутирует
>   projection state) сразу по трём осям: cross-loop доступ к singleton Velum из worker-потока; запись
>   `fact_id` в keyspace *имён сущностей*; игнорирование `ENABLE_VELUM=0`. Плюс неограниченное
>   перечисление пар, квадратичное по числу подходящих фактов.
>
> **Corrective PR** (`claude/hotfix-pr66-review-findings`): H1 — семантика переходов доведена до конца
> (эскалация раньше восстановления, бюджет — полноправный член условия recovery, гейт по флагу, тихое
> чтение). H2 — **применение убрано, движок переведён в analysis-only**: анализ read-only, отдаётся
> ограниченный proposal, а отчёт честно сообщает `velum_apply_status` вместо несуществующего подкрепления.
>
> **Статус H2: contained, НЕ resolved.** Полноценное применение Velum-replay остаётся нерешённым и требует
> отдельного PR: маппинг `fact_id` → entity name, исполнение на owning event loop, явный canonical/proposal
> apply-сервис, тесты на конкурентность.
>
> **Итог:** с прошлого аудита (56 коммитов до `b14de02`) закрыта подавляющая часть Critical/High находок — это хороший знак,
> команда реально фиксит то, что находит аудит. Но: **0 Critical на сегодня, 5 High (H1-H5: 2 старых недобитых + 3 новых), 15 Medium, 15 Low.** Ключевой системный паттерн не изменился: несколько защитных
> механизмов снова тихо неработоспособны из-за rename-дрейфа (`get_budget_planner`, `get_velum`), но теперь это
> хотя бы честно задокументировано прямо в коде как известный баг — прогресс в культуре, не в устранении.

---

## 📌 Резюме одной строкой

```
Пред. аудит (06-06): Critical 1 · High 11 · Medium 17 · Low 19  (63 находки)
Статус сейчас:       ФИКСЛИЙ (полностью) — 14   ЧАСТИЧНО — 8   НЕ ФИКСЛИЙ — 12   (из 28 пунктов)
Новый аудит (07-28): Critical 0 · High 5 (H1-H5) · Medium 15 (M1-M15) · Low 15
                     (в первой редакции стояло «High 6 / Medium ~16» — пересчитано по факту
                      перечисленных пунктов: H5 и M5 — одна и та же находка, учтена один раз как High)
CI на b14de02:       GitHub Actions run 30338484625 lint-and-test ✅ success (14/14 шагов)
                     локально на b14de02: pytest 2160 passed / 19 skipped / 1 xfailed (345s)
                     mypy 242 файла · validator production-профиля 75/75 · ruff чист на пиновке
```

---

## 🔄 Влияние PR #63/#64 (hardened production profile)

Два коммита между `ac62961` и `b14de02` добавили deny-by-default production-профиль
(`731b44d`) и затем исправили его заявления по итогам ревью (`b14de02`). Оба —
**конфигурация и документация**: diff по `core/`, `api/`, `app/`, `server.py`, `utils/`,
`migrations/`, `Dockerfile` пуст. 9 файлов, +1840 строк.

Что это значит для находок этого отчёта:

| Находка | Влияние |
|---|---|
| **H1–H5** | Не затронуты. Все пять перепроверены на `b14de02` и воспроизводятся (точные строки — в Части II). |
| **#9 «CI больше не театр»** | Подтверждается заново на `b14de02`: GitHub Actions run `30338484625` (`lint-and-test`) — success, все 14 шагов. Локальный полный прогон: **2160 passed, 19 skipped, 1 xfailed** за 345 с (на `ac62961` было 2023 — рост за счёт 137 новых тестов из #62/#63/#64). |
| **Low: PII/at-rest шифрование выключены по умолчанию** | Частично адресовано **операционно**: появился `docker-compose.prod.yml`, который пинит 33 research/autonomous-флага в `0` и требует `VELANTRIM_API_KEY` fail-closed. Сами `core/pii.py` / `core/crypto.py` по-прежнему opt-in — находка остаётся, но «риск дефолтного деплоя» теперь имеет документированный безопасный профиль. |
| **Low: ruff запинен диапазоном** | Не исправлено и **подтверждено численно**: локальный ruff 0.15.8 даёт ровно **141** `UP045` на `core/` — идентично и на `ac62961`, и на `b14de02` (delta 0). Пин `>=0.4,<0.5` остаётся несущим. |
| **M1 (SAFE_MODE пишет мимо write_gate)** | Не затронуто — runtime. Но production-профиль теперь включает `ENABLE_WRITE_GATE=1` явно, так что расхождение инварианта стало наблюдаемее, а не меньше. |
| **Новое, вне списка находок** | PR #64 добавил `pyyaml` в dev-зависимости (до него `requirements-dev.txt` и extra `dev` ставили только `types-PyYAML`, из-за чего валидатор профиля падал `ModuleNotFoundError`, а его тесты молча скипались). Это тот же класс дефекта, что H1/H2 — «механизм есть, но не исполняется» — просто в верификационном слое. |

Отдельно: PR #63 сам был смержен с 7 неразрешёнными P1/P2-замечаниями ревью, которые
закрыл PR #64 (три «защитных» флага профиля не работали: fail-open TruthPolicy,
недостижимый Response Audit, незапущенный `ImmutableCoreScheduler`). Это независимое
подтверждение центрального паттерна этого отчёта — **включённый флаг ≠ работающий
механизм** — на свежем, только что написанном коде.

---

## Часть I — Статус находок аудита 2026-06-06

Легенда: ✅ FIXED · 🟡 PARTIAL · ❌ NOT FIXED · 🔁 REGRESSED

| # | Находка | Статус | Комментарий |
|---|---|---|---|
| 1 🔴 | MetaSupervisor MHI мёртв (`compute_mhi`) | ✅ FIXED | `meta_supervisor.py:262-266` теперь зовёт `MHICalculator(store).calculate()`, DLQ/budget разнесены по try-блокам, swallow поднят до WARNING. |
| 2 🟠 | ESM-матрица Python vs DB-триггеры | ✅ FIXED | `memory.py:51-60` теперь зеркалит `migrations/009_truth_kernel.sql:88-112`, тест на идентичность есть. |
| 3 🟠 | `store_facts_batch` L0/L1 split-brain | ✅ FIXED | `memory.py:3794-3796` теперь всегда синхронизирует `epistemic_state` при отсутствии drift. |
| 4 🟠 | GDPR: PII в `fact_versions`/`l0_raw_memory` после «удаления» | 🟡 PARTIAL | `fact_versions` реально чистится атомарно (`erase_fact_dependents_atomic`). `l0_raw_memory` НЕ чистится (by design, append-only), но статус теперь честно `residual: "raw_original_present"` вместо ложного COMPLETE. Сырой текст всё ещё восстановим. |
| 5 🟠 | `forget_all` substring-LIKE over-deletion | ✅ FIXED | Точное сравнение `source = ?` / `json_extract(metadata,'$.user_id') = ?`, `force`-флаг для ambiguous/default user_id. |
| 6/7/15 🟠 | Hash-цепи без actor/reason/confidence | ✅ FIXED (см. ⚠️ ниже) | `provenance_chain._compute_hash` и `audit_chain` v2-envelope теперь включают actor/reason(+confidence в audit). Но см. новую находку M4 — нет `hash_version` у provenance_chain. |
| 8 🟠 | `CausalGraph.import_snapshots` тихо роняет рёбра | 🟡 PARTIAL | Теперь логирует WARNING/ERROR на каждое дропнутое ребро — уже не тихо. Но всё ещё ловит bare `Exception` и возвращает только `imported`, без `failed`-счётчика. |
| 9 🟠 | CI-театр (ruff/mypy/pytest все красные) | ✅ FIXED | Эмпирически проверено на закреплённых версиях: ruff 0 ошибок, mypy 0 ошибок (strict), полный pytest зелёный. `--cov`/`fail_under=80` убран из default addopts. |
| 10 🟠 | Rename-дрейф прод-кода | 🟡 PARTIAL | `update_fact→store_fact`, `create_store→make_store`, `EssenceLayer→compose_essence`, `get_living_store` — все почищены. **`get_budget_planner` остаётся сломан** — см. новую H1 ниже. |
| 11 🟠 | Re-archival затирает original_claim | ✅ FIXED | `NOT IN (archived_facts)`, `INSERT OR IGNORE`, bump fact_version, `restore_fact()` теперь берёт полный claim из JSON-архива, а не из усечённой колонки. |
| 12 🟡 | `link_by_tags` без `inference_source` | ✅ FIXED | Эмитится `"inference_source": "autolinker"`. |
| 13 🟡 | `modality_guard` bare list-truthiness | ❌ NOT FIXED | `truth_policy.py:177,191` — без изменений. |
| 14 🟡 | `supersede()` обходит TruthGate | ✅ FIXED | Теперь роутит через `TruthGate.evaluate()` перед промоушеном, атомарная CAS-транзакция. |
| 16 🟡 | `store_facts_batch` → UNKNOWN modality | ✅ FIXED | `classify_claim`/`normalize_claim_type`/`normalize_origin_type` + WriteProtocolGate теперь прогоняются per-record. |
| 17 🟡 | Namespace-bridge confidence ниже порога | 🔁 REGRESSED | `NAMESPACE_BRIDGE_CONFIDENCE` теперь **0.30** (было 0.4) — ещё дальше от дефолтного порога traversal 0.5. Multi-hop через bridge-рёбра по-прежнему не работает на дефолтах. |
| 18 🟡 | HybridRetriever ре-энкодит корпус на каждый запрос | ❌ NOT FIXED | `branch_manager.py:213` — без изменений, кэша по версии store нет. |
| 19 🟡 | `transition_esm`/`update_state` check-then-act гонка | ✅ FIXED | Единый UPDATE с CAS-guard `WHERE epistemic_state=?` + проверка rowcount. |
| 20 🟡 | Catch-all возвращает `str(exc)` клиенту | 🟡 PARTIAL | Глобальный handler добавил стабильный `error`-код, но **всё ещё** прикладывает `detail: str(exc)`; десятки локальных `HTTPException(detail=str(exc))` не тронуты. |
| 21 🟡 | RAR zip-bomb без size-guard | 🟡 PARTIAL (не так исправлено, как кажется) | Guard добавлен, но считает **заявленный** `info.file_size` из заголовка RAR (untrusted metadata), а не реальные потоковые байты как в zip/tar (`_stream_copy_capped`). Подделанный архив с заниженным заявленным размером обходит проверку. См. новую H4. |
| 22 🟡 | forgetting: provenance-append не атомарен | 🟡 PARTIAL | Сбой теперь логируется WARNING, но по-прежнему отдельное соединение, не atomic с DELETE. |
| 23 🟡 | truth_maintenance вторичные записи тихо проглатываются | ❌ NOT FIXED | `contradict()` (`truth_maintenance.py:393-415`) — всё ещё bare `except: pass`, `changed=True` возвращается даже при упавшей записи в causal-graph/contradiction-registry. |
| 24 🟡 | BranchManager глотает все исключения | ❌ NOT FIXED | Более того, в коде честно признаны ещё 2 новых мёртвых пути (см. M10). |
| 25 🟡 | Мёртвый RawMemoryStore/raw_derivation_chain | ❌ NOT FIXED | Оба пути (мёртвый и продовый `l0_fact_provenance`) сосуществуют, self-DDL guard не добавлен. |
| 26 🟡 | `situation.py` мёртвый `get_living_store` | 🟡 PARTIAL | Импорт починен, но окружающий `except Exception: pass` (`:107-108`) остался широким. |
| 27 🟡 | `--cov` в default addopts | ✅ FIXED | Убран полностью (не просто вынесен в отдельный шаг). |
| 28 🟡 | `test_confidence_boundary_values` ничего не проверяет | ❌ NOT FIXED | `tests/test_adversarial.py:270-280` — без изменений, тавтологический `pytest.raises((ValueError, Exception))`. |
| Low-пункты | (дубли `_ESM_RANK`, orphaned `text_utils.py`, `storage_info.cache_clear()`, reverse-edge weight*0.9, `_next_seq` sentinel, append-only триггеры на provenance_chains, adaptive_truth RED-zone, `decide()` ALLOW-shortcut, perspectives.py unused presets, rate-limiter XFF) | Почти все ❌ NOT FIXED | Единственные подтверждённо ✅: Host-header SSRF в `web_console.py` (fixed), unused `DEFAULT_TRIAD` import (removed), contradiction_resolver negation handling (похоже адресовано). Список см. в отчётах агентов — не дублирую построчно здесь. |

`AUDIT_ACTION_ITEMS.md` — ни один чекбокс не отмечен, несмотря на реальный прогресс по ~20 пунктам. Чисто гигиенический момент, не баг.

---

## Часть II — Новые находки (код, добавленный/изменённый после 2026-06-06)

### 🟠 HIGH

**H1. 🧟 MetaSupervisor: budget-pressure сигнал навсегда пришпилен к 0.0 — `get_budget_planner` не существует**
`core/meta_supervisor.py:289-299` (мёртвый импорт — строка **295**, `planner.fill_ratio` — **297**; ветки `budget_warn`/`budget_block` — **:90-91**, чтение снапшота — **:340**). Перепроверено на `b14de02`. `from core.memory_budget import get_budget_planner` — модуль `core/memory_budget.py` экспортирует только `check_before_write`, `evaluate_budget`, `BudgetStatus`, `is_memory_budget_enabled`, `count_facts`. Каждый heartbeat бросает `ImportError`, пойманный `except Exception: self._budget_cache = 0.0`. Уже честно признано комментарием в коде как known unfixed follow-up к находке #1/#10.
**Последствие:** ветки `budget > cfg.budget_warn`/`budget_block` (HEALTHY→DEGRADED→SAFE_MODE) в `_evaluate()` никогда не срабатывают — из трёх сигналов иммунной системы памяти живы только MHI и DLQ.

**H2. 🧟 ExperienceReplay: Velum-подкрепление и decay навсегда no-op — три слоя мёртвого пути**
`core/experience_replay.py:128, 148` (перепроверено на `b14de02` — обе строки на месте). Путь был мёртв **не в одном месте, а в трёх**, и каждый слой маскировал следующий — первая редакция этого отчёта зафиксировала только внешний:

1. **Неверный импорт.** `from core.velum import get_velum`, но `get_velum()` определена в `core/velum_bridge.py:31`. Продублировано в двух блоках, т.е. копии могли расходиться независимо.
2. **Вызываемых методов не существует.** Даже с исправленным импортом код звал `velum.observe_entities()` и `velum._decay_weak_edges()` — ни того, ни другого у `Velum` нет; реальный API — `observe_episode()` / `on_session_end()`. Починка одного импорта оставила бы путь ровно таким же мёртвым.
3. **Оба метода async**, а `run()` синхронный (вызывается через `asyncio.to_thread`).

Все три отказа стекались в `logger.debug` или `except: pass`.
**Последствие:** усиление Velum-рёбер для совместно реактивированных фактов и decay устаревших рёбер никогда не выполняются; `report["velum_edges_boosted"/"velum_edges_decayed"]` всегда 0 — и читается это как «нет подходящих пар», а не «ничего не работает».

**H3. 🧬 GDPR-erasure: crash-recovery (`resume_incomplete_jobs`/`resume_incomplete_batches`) нигде не подключён к продакшену**
`core/erasure_coordinator.py`, `core/erasure_batch_coordinator.py` — эти функции существуют, корректно реализованы и покрыты тестами, но **ни разу не вызываются** нигде за пределами собственных unit-тестов (перепроверено на `b14de02`: вне `tests/` встречаются только определения, обёртки `:2051`/`:1546`, экспорты в `__all__` и комментарии): нет startup-хука, cron/scheduled job, admin/MCP-инструмента, упоминания в докой как runbook-шага.
**Последствие:** если процесс падает посреди многошаговой erasure-саги (после `l1_same_db`, до `embeddings`/`ngram`), job/batch остаётся в `RUNNING` с истёкшей арендой навсегда — ни один повторный вызов `forget_fact`/`forget_all` для того же субъекта не реанимирует его (claim-путь намеренно исключает `RUNNING`). `is_erased()` честно остаётся `False` (ложного COMPLETE не будет), но GDPR Art. 17 запрос **молча зависает бесконечно** без ручного вмешательства оператора — при типичном 30-дневном сроке ответа это реалистичный способ пропустить дедлайн незамеченным.

**H4. 🔒 RAR-парсер: size-guard считает заявленный (untrusted) размер, а не реальные распакованные байты — обходимо**
`core/file_parsers/archive_parser.py:301-310` (перепроверено на `b14de02`: `total_size += info.file_size` из заголовка, затем безусловный `rf.extract`). В отличие от `_extract_zip`/`_extract_tar` (реальный потоковый подсчёт байт через `_stream_copy_capped`, обрыв на середине записи), `_extract_rar` суммирует `info.file_size` из заголовка RAR-записи (данные из самого архива, атакующим контролируемые/подделываемые) и только затем безусловно зовёт `rf.extract(member, tmpdir)`, которая распаковывает файл целиком без предела.
**Последствие:** архив с заниженным заявленным `file_size`, но с реальным огромным распакованным содержимым обходит guard и пишет неограниченный объём на диск — тот же класс атаки, из-за которого `.7z` намеренно отключён (комментарий в коде: «5KB → 50GB OOM»). Реален при установленном `rarfile` (задокументированная опция установки).

**H5. 🔒 Gemini model-id всё ещё интерполируется в URL без валидации — существующий валидатор мёртв**
`core/llm_router.py:260` (`_gemini_generate_url`), `core/gemini_models.py:378` (`model_allowed_for_provider`). Перепроверено на `b14de02`: у валидатора **ноль** вызывающих вне `tests/` — только определение и экспорт в `__all__:404`. `model_allowed_for_provider()` (регэксп `^gemini-[a-z0-9][a-z0-9.-]*$`) определена и экспортирована, но **нигде не вызывается** — ни в `_gemini_generate_url`, ни в `api/llm_routes.py:_run_llm_test` (там прямой комментарий «любой gemini-* ID допустим, проверка на стороне Google»). `normalize_gemini_model_id` делает только strip префикса `models/`, без валидации символов.
**Последствие:** клиент-контролируемая строка `model` с `/`, `..`, `?`/`&` попадает напрямую в путь URL исходящего запроса (несущего API-ключ в заголовке `x-goog-api-key`) к фиксированному хосту Google — не полный SSRF (хост зафиксирован), но path/query-injection на этом хосте. Не тронуто в коммите 2aa3b49 (тот трогал `web_console.py`/`archive_parser.py`/`memory.py`/`write_gate.py`/`server.py`, но не `llm_router.py`/`gemini_models.py`).

---

### 🟡 MEDIUM

**M1. 🔒 SAFE_MODE блокирует запись только в `core/memory.py`, не в соседних путях**
`core/console_notes.py`, `core/goal_stack.py`, `core/memory_ops.py`, `core/umwelt_store.py` — прямые `INSERT/UPDATE/DELETE` без вызова `write_gate.ensure_writes_allowed()`. Инвариант в `meta_supervisor.py:16` формулирует SAFE_MODE как «блокировка ВСЕХ пишущих операций», но проверено это только для `store_fact`/transitions/batch (см. `test_safe_mode_writes_blocked.py`). Роуты `/console/notes`, `/goals`, `/sources`, `/memory/inbox`, `/memory/traces` зовут эти методы напрямую.
**Последствие:** система в SAFE_MODE (MHI<0.30) — режим экстренной остановки записи для стабилизации — но авторизованный клиент продолжает создавать заметки/цели/inbox-записи/трейсы/Umwelt-восприятия, наращивая БД ровно во время инцидента, который lockdown должен сдерживать.

**M2. 🧬 `ForgettingEngine.forget_one()` — мёртвый код, но с оригинальным GDPR-багом целиком**
`core/forgetting.py:292-365`. В отличие от `forget_all()` (делегирует в `forget_all_durable()`), `forget_one()` никогда не мигрирован на durable-путь: своё соединение, `except Exception: pass` вокруг DELETE из `fact_mentions`/`fact_versions`/`l0_fact_provenance`, не трогает `l0_raw_memory`/embeddings/ngram. Ноль продовых вызывающих (проверено grep) — но landmine для любого будущего прямого вызова класса.

**M3. ⚙️ `store_fact`/`store_facts_batch` без CAS-guard в UPSERT (в отличие от `update_state`)**
`core/memory.py:1611-1637, 3757-3941`. Drift-детекция читает состояние заранее (возможно устаревший L0-снимок), затем UPSERT без `WHERE epistemic_state=?`. Триггер `prevent_collapsed_mutation` (migration 009) абортит при реальной гонке (fail-closed, не тихая порча), но `store_fact()`'s legacy bool-API не ловит это — всплывает как необработанное исключение вместо структурированного отказа (`store_fact_result()` это обрабатывает правильно).

**M4. ⚙️ `ProvenanceChain._compute_hash` без `hash_version` — legacy-записи провалят `verify()`**
`core/provenance_chain.py:282-309`. Формула хэша исправлена in-place (добавлены actor/reason), но, в отличие от `audit_chain.py` (там есть колонка `hash_version` и dual-dispatch v1/v2), у `provenance_chains` версии схемы хэша вообще нет. Любая запись, созданная до фикса, при вызове `verify()` даст ложный `hash_mismatch`. Пока не эксплуатируется — `.verify()` в проде никем не вызывается (только `.append()`), но это реальный дефект целостности отчётности, если цепь когда-нибудь будет проверена.

**M5. 🔒 Gemini model-id path-injection** — см. H5 выше (некоторые агенты оценили Medium, некоторые High; беру консервативно как самостоятельный пункт severity Medium из-за фиксированного хоста и обязательной API-key авторизации, но обратите внимание на H5 в общем списке действий).

**M6. ⚙️ EdgeSuggester: гонка дублей suggested-edges → неотловленный `IntegrityError` на 500**
`core/edge_suggester.py:127-244, 342-361`. `_pending_pairs` — снэпшот на начало `scan()`, у таблицы `suggested_edges` нет UNIQUE-constraint на `(from,to,type)` (только PK по `suggestion_id`, см. migration 019). Два конкурентных `/edges/suggestions/scan` создают два `pending`-предложения на одну пару; два последующих `/approve` — второй `add_relation()` падает с `sqlite3.IntegrityError` (у `relations` UNIQUE есть), не пойманным в `approve()` → 500 клиенту вместо чистого conflict-ответа.

**M7. ⚙️ `CausalGraph.import_snapshots` — всё ещё bare `except`, нет счётчика failed** — было High (#8), теперь Medium: дропы теперь логируются, но exception-класс всё ещё широкий, а вызывающий код не узнаёт, сколько рёбер потеряно.

**M8. ⚙️ `truth_maintenance.contradict()` — вторичные записи (causal-graph edge, contradiction-registry) тихо проглатываются, `changed=True` возвращается независимо от их успеха** (`truth_maintenance.py:393-415`, находка #23, не фиксили).

**M9. 🔒 Catch-all в `server.py` всё ещё отдаёт `detail: str(exc)` клиенту** — стабильный `error`-код добавлен, но детали exception по-прежнему утекают в глобальном handler (`:4173-4179`) и в десятках локальных `HTTPException(detail=str(exc))`.

**M10. 🧟 BranchManager: LLM- и essence-генерация ответа — навсегда мёртвые пути (новые, честно признанные в коде баги) + широкие except остались**
`core/branch_manager.py:238-257`. `LlmCallConfig(max_tokens=500)` всегда бросает `TypeError` (нет обязательных `provider`/`api_key`); fallback `compose_essence(query=..., facts=...)` не совпадает с реальной сигнатурой (`compose_essence(facts, relations=None)`, нет `query`-kwarg, возвращает dataclass, не dict). Оба пути дохлые — каждый multi-perspective ответ падает в generic-шаблон с фиксированной confidence=0.3. Не safety-критично (read-only фича), но заявленная «multi-perspective LLM-рассуждение» никогда фактически не выполняется.

**M11. 🧟 GraphLab `analyze_graph` эндпоинт всегда сообщает «недоступно» — drift параметра**
`core/graph_lab_bridge.py:120-124` зовёт `gl_analyze(db_path=db, ...)`, но `core/graph_lab.py:319` определяет `analyze(seed_fact_ids=None, *, top_k=20, max_nodes=..., conn=None)` — параметра `db_path` нет. `TypeError` на каждый вызов, пойман `except Exception: logger.debug`, endpoint всегда возвращает `{"available": False}`. Centrality/communities/cycles/pagerank недостижимы в проде.

**M12. 🟡 Несколько построенных, но никогда не подключённых к продакшену safety/decay-модулей**
`core/compute_controller.py` (`decide_compute_path` — адаптивный риск-роутер для TruthGate/reflection/noetic-эскалации, вызывается только из теста, не из `pipeline.py`/`server.py`), `core/memory_archival.py` (0 ссылок нигде, включая тесты — несмотря на недавние правки внутри модуля), `core/fact_decayer.py` (докстринг утверждает интеграцию с ConsolidationEngine/SleepTimeWorker — на деле 0 ссылок), `core/adaptive_truth.py`, `core/negative_reinforcement.py` — та же картина. Это не «один плохой except», а полностью реализованные, инвариант-документированные механизмы, которые никогда не были подключены — их защита просто никогда не активируется, без единого лога об этом.

**M13. ❌ `modality_guard` bare list-truthiness (находка #13, не фиксили)** — `truth_policy.py:177,191`.

**M14. 🔁 Namespace-bridge confidence регрессировала ниже (находка #17)** — `NAMESPACE_BRIDGE_CONFIDENCE=0.30` теперь ещё дальше от порога traversal 0.5.

**M15. ❌ HybridRetriever всё ещё пересобирается на каждый branch/запрос (находка #18)** — без изменений.

---

### 🟢 LOW

- 🔒 Нет `Content-Security-Policy` заголовка нигде (`api/server_middleware.py`) — есть X-Frame-Options/X-Content-Type-Options/HSTS, но не CSP; ручной markdown-рендер консоли (`escapeHtml`) выглядит корректным в проверенных путях, но без CSP это единственная линия защиты.
- 🔒 PII-редакция (`core/pii.py`) и at-rest шифрование (`core/crypto.py`) — оба opt-in, по умолчанию выключены. Осознанный дизайн, но для GDPR-adjacent системы — риск дефолтного деплоя с открытым PII в SQLite.
- 🧪 ruff запинен диапазоном (`>=0.4,<0.5`), не точной версией — при случайном использовании ambient более новой версии (проверено: ruff 0.15.8 даёт 141 false-positive `UP045` на этом же коде) можно ошибочно решить, что появилось 141 новых проблем.
- 🧟 Дубль `_ESM_RANK` в `semantic_dedup.py:51,53` — не убран.
- 🧟 Orphaned-модули без единого импортёра: `core/text_utils.py` (дубль `utils/text_utils.py`), `core/curiosity_engine.py`, `core/query_expander.py`, `core/query_router.py`, `core/working_memory.py`, `core/multi_index_retriever.py`, `core/evidence_pack.py`, `core/trusted_retrieval.py`.
- 🧟 `storage_info.cache_clear()` не вызывается в `reset_graph_store()` — не фиксили.
- 🧟 Unused reverse-edge `weight*0.9` в `core/backends/memory_graph.py:36` — не убран.
- 🧟 `provenance_chain._next_seq` всё ещё глотает ошибку в sentinel `seq=0` (`:326`).
- ⚙️ Append-only DB-триггеры на `provenance_chains` по-прежнему отсутствуют (в отличие от `memory_events`/`audit_chain`).
- 🧟 `adaptive_truth._apply_satisfaction` всё ещё ослабляет порог в RED-зоне — мёртвый код, не фиксили.
- 🧟 `truth_policy.decide()` ALLOW-shortcut всё ещё на `SELF_VALIDATING` вместо `SUBJECTIVE_TYPES` — off-by-default, не фиксили.
- 🧟 `conversation_consolidation.add_insight` всё ещё сбрасывает `created_at` — модуль не подключён, не фиксили.
- 🧟 `perspectives.py` неиспользуемые пресеты (DEEP/PRACTICAL/CREATIVE_TRIAD, SIMPLE_DUO) — не подключены и не убраны.
- 🔒 Rate limiter по-прежнему ключится на `request.client.host`, без XFF-aware логики — корректно и безопасно для прямого деплоя (не спуфится), но станет проблемой (все клиенты за одним bucket) при деплое за реверс-прокси без доп. настройки.
- 🧟 Мёртвая DI-фабрика в `core/app.py:236` — `_GLOBAL_STORE._conn()` не существует (реальный метод — `_db()`), бросит `AttributeError`, но `VelantrimApp`/`get_app()` нигде не инстанциируется в проде — недостижимо, но подлежит чистке.

---

## Часть III — Аудит новых подсистем (crystal-transfer, synaptic) — впервые проверены

### Synaptic-контракты (`knowledge_capsule.py`, `semantic_reader.py`, `readers/`) — 🟢 в целом solid
Иммутабельность реально enforced (`frozen=True, slots=True`, тесты проверяют `FrozenInstanceError` даже на вложенных records). `capsule_id`/`claim_id` — content-derived SHA-256, tamper fail-closed (проверено тестом на ручную подмену id). `extraction_confidence` и `truth_confidence` — независимые поля с валидацией (`HYPOTHESIS` не может иметь `truth_confidence==1.0`). `SemanticReader`/`ExtractiveReader` подтверждённо не пишут в память/Canon/граф — согласно плану PR-SYN-01/02. Тесты нетривиальны (Unicode-офсеты, идемпотентность, prompt-injection текст корректно классифицируется как `INSTRUCTION`-модальность вместо исполнения). Единственная придирка: `readers/extractive.py:277` — `qualifiers = conditions` (одна и та же переменная переиспользована для двух концептуально разных полей). Косметика.

### Crystal-transfer (`compute_profile.py`, `dual_process.py`, `edge_suggester.py`, `xai_explain.py`)
Помимо M6 (гонка дублей suggested-edges) выше:
- `COMPUTE_PROFILE`→`feature_config.py` wiring корректен, explicit-env-wins-over-profile семантика подтверждена тестами (не тавтологичными).
- `@slow_only` в `dual_process.py:80-89` — sync-only декоратор, `asyncio.iscoroutinefunction()` даст `False` на обёрнутой корутине, если когда-нибудь применят к `async def`. Сейчас применяется только к sync `EdgeSuggester.scan` — не баг сегодня, но ловушка на будущее. 🟢 Low.
- `env_explicitly_set` в `compute_profile.py:74-76` — экспортирована в `__all__`, нигде не вызывается. 🟢 Low, dead code.
- `xai_explain.explain_reasoning_trace(resolve_facts=False)` синтезирует `confidence=0.5`/`"Observed"` без реального состояния — путь недостижим (единственный вызывающий всегда передаёт `resolve_facts=True`), но landmine если когда-нибудь включат. 🟢 Low.
- `EdgeSuggester.scan` корректно гейтится `@slow_only`+`require_slow_path`, пишет только в `suggested_edges`, никогда напрямую в `relations` — подтверждено тестом.

---

## Что сделано хорошо

- **Культура ре-аудита реальна.** Из 28 находок прошлого аудита 14 закрыты полностью, 8 частично, и почти везде, где фикс неполный, это **честно признано прямо в коде** комментарием («FIX #X (Claude audit)», «известный нефикшенный баг»), а не замаскировано. Это заметно отличается от типичной практики.
- **CI больше не театр.** Ruff/mypy(strict)/pytest реально зелёные на закреплённых версиях — редкость для проекта такого масштаба (242 модуля).
- **Canonical write protocol реально атомарен.** Все проверенные commit-claims (atomic evidence, atomic terminal transitions, version-safe updates, temporal consistency, CAS-guard в `update_state`) подтверждены прямым чтением кода, не только тестами.
- **GDPR erasure-саге — серьёзная инженерия.** Durable job/batch модель с CAS, fencing-токенами, generation-счётчиками, конкурентность реально протестирована регрессионными тестами гонок (`test_concurrent_erase_calls_on_superseded_candidate_converge_on_one_generation` и т.п.) — логика верна, единственный пробел операционный (crash-recovery не подключена, H3), не архитектурный.
- **Два новых кластера функциональности (synaptic, crystal-transfer) спроектированы и реализованы аккуратно** — контракты соблюдены, тесты нетривиальны, wiring корректен там, где должен быть, и намеренно отсутствует там, где по плану ещё рано.

---

## Рекомендованный порядок (диагностика — решение о фиксах за вами)

1. **H1/H2** — ~~тривиальные однострочные rename-фиксы~~. **Эта оценка оказалась неверной**, и это стоит зафиксировать как урок о самом отчёте: «мёртвый импорт» выглядел как rename на одну строку, а на деле H2 был мёртв в трёх слоях (импорт → несуществующие методы → async/sync), а восстановление сигнала обнажило ещё 9 review-замечаний. Диагностика верно указала *где* сломано, но систематически недооценила *насколько*. **Сделано:** PR #66 (сигналы восстановлены, merged в `afab774`) → corrective PR `claude/hotfix-pr66-review-findings` (H1 — семантика переходов доведена до конца; H2 — переведён в analysis-only, применение отложено). **H2 остаётся contained, не resolved** — см. post-merge заметку выше.
2. **H3** — подключить `resume_incomplete_jobs()`/`resume_incomplete_batches()` к какому-то периодическому механизму (startup-хук или cron); иначе GDPR-таймер реально может быть пропущен незамеченным.
3. **H4** — либо реализовать реальный потоковый счётчик для RAR (как в zip/tar), либо явно отключить `.rar` по аналогии с `.7z` до тех пор.
4. **H5/M5** — навесить `model_allowed_for_provider()` (уже существует, просто не вызывается) на `_gemini_generate_url`.
5. **M1** — распространить `write_gate.ensure_writes_allowed()` на `console_notes`/`goal_stack`/`memory_ops`/`umwelt_store`, если SAFE_MODE должен блокировать реально «ВСЕ» записи, как заявлено в инварианте.
6. **M2** — либо удалить мёртвый `forget_one()`, либо мигрировать его на durable-путь как `forget_all()`.
7. Остальное — по вкусу; ни один Medium/Low не является тикающей бомбой, все либо read-only, либо gated, либо уже fail-closed.
