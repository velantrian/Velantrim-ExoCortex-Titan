# 🔱 VELANTRIM V8.7 — Action Items (по аудиту 2026-06-06)

> Тезисный чек-лист. Полные обоснования (file:line, последствия, верификация) — в [`AUDIT_DEEP_2026-06-06.md`](AUDIT_DEEP_2026-06-06.md).
> Счёт находок: **Critical 1 · High 11 · Medium 17 · Low 19.**

## 🔴 Critical

- [ ] **#1 Починить MetaSupervisor.** `core/meta_supervisor.py:259` — заменить `compute_mhi` → `MHICalculator(store).calculate()`. Разнести сбор MHI/DLQ/budget по отдельным `try`-блокам. Поднять `except` с DEBUG до WARNING. Добавить тест, гоняющий `_collect_mhi()` против заполненного store (не только `_evaluate`).

## 🟠 High

- [ ] **#2 Единый источник истины для ESM.** Python `ESM_TRANSITIONS` (`core/memory.py:38`) ≠ DB-триггеры (`migrations/009_truth_kernel.sql`). Выровнять матрицы + тест на идентичность множеств.
- [ ] **#3 Починить `store_facts_batch`.** Отклонять drift на Supported (как `store_fact`); всегда `record['epistemic_state'] = existing` чтобы L0 не расходился с L1. Заодно фикс pre-existing NameError на `core/memory.py:635`.
- [ ] **#4 Закрыть GDPR-утечку.** В транзакции удаления чистить/редактировать `fact_versions` и raw-текст; `l0_raw_memory` — через trigger-aware путь (DELETE/UPDATE запрещены триггерами 010).
- [ ] **#5 `forget_all` over-deletion.** Убрать substring-`LIKE %user_id%`; матчить структурно; отклонять пустой/«default» user_id без force-флага. Добавить `foreign_keys=ON` в `forget_all`.
- [ ] **#6/#7 Усилить hash-цепи.** Включить `actor`/`reason` (provenance) и `reason`/`confidence` (audit) в `_compute_hash`. Версионировать схему хэша + разовая ре-хэш-миграция.
- [ ] **#10 Устранить rename-дрейф прод-кода.** Прогнать `mypy --strict` как punch-list: `update_fact`, `create_store`, `EssenceLayer`, `get_budget_planner`, `get_living_store` — починить каждый вызов.
- [ ] **#9 Развязать CI-парадокс.** Решить, mypy реально BLOCKING или нет; починить F401/F841; точно запинить ruff/mypy (`==x.y.z`).
- [ ] **#11 Архивация (`memory_archival`).** Исключать уже-архивированные (`AND fact_id NOT IN (...)`); `INSERT OR IGNORE`; хранить полный claim (не `[:500]`); bump `fact_version` (иначе триггер 009 ABORT'ит).

## 🟡 Medium

- [ ] **#12** `link_by_tags` должен эмитить `inference_source` (иначе дубли рёбер при пересборке KB).
- [ ] **#13** `modality_guard` (`truth_policy.py:177`) — проверять через `fact_evidence_ref(...)`, а не bare list-truthiness.
- [ ] **#14** `truth_maintenance.supersede()` — прогонять new_fact через TruthGate перед `transition_esm("Validated")` (обход I68).
- [ ] **#16** `store_facts_batch` — писать `claim_type`/`origin_type` (сейчас всё падает в `UNKNOWN`).
- [ ] **#17** Поднять `NAMESPACE_BRIDGE_CONFIDENCE` ≥ 0.5 (иначе multi-hop reasoning не пересекает подразделы на дефолтном пороге).
- [ ] **#18** `HybridRetriever` — кэшировать по версии store; не ре-энкодить корпус на каждой ветке запроса.
- [ ] **#19** CAS-guard в `transition_esm`/`update_state`: `WHERE fact_id=? AND epistemic_state=?` (check-then-act гонка).
- [ ] **#20** `server.py` catch-all — возвращать `{"error":"internal_server_error"}`, детали только в server-side лог.
- [ ] **#21** RAR-парсер (`archive_parser.py:240`) — добавить `MAX_EXTRACTED_SIZE` guard (как в zip/tar).
- [ ] **#8/#22** `CausalGraph.import_snapshots()` и `provenance.append()` из `forgetting` — ловить конкретные исключения, логировать; прокинуть внешний `conn` в `append()`.
- [ ] **#23/#24** `truth_maintenance` и `BranchManager` — сузить `except`, логировать на WARNING, не рапортовать успех при дропнутой записи; пробросить degraded-флаг.
- [ ] **#25** Мёртвый `RawMemoryStore`/`raw_derivation_chain` — удалить либо консолидировать с `l0_fact_provenance`; добавить self-DDL guard.
- [ ] **#26** `situation.py:91` — добавить `get_living_store()` в `living_context.py` (сейчас Living-Context enrichment мёртв).
- [ ] **#27** Вынести `--cov`/`fail_under` из дефолтного `addopts` в выделенный full-suite CI-шаг (частичные раны ложно RED).
- [ ] **#28** `test_confidence_boundary_values` — убрать `except: pass`, использовать `pytest.raises(ValueError)` точечно.

## 🟢 Low (быстрые)

- [ ] Append-only DB-триггеры на `provenance_chains` + проверка непрерывности seq в `verify()`.
- [ ] Удалить дубли: `_ESM_RANK` (`semantic_dedup.py:51`), orphaned `core/text_utils.py`, unused `DEFAULT_TRIAD` (`branch_manager.py:33`), неиспользуемые пресеты в `__all__` `perspectives.py`.
- [ ] `storage_info.cache_clear()` в `reset_graph_store()`.
- [ ] `adaptive_truth._apply_satisfaction` — не ослаблять порог в RED-зоне (medicine/law/finance).
- [ ] `decide()` ALLOW-shortcut (`truth_policy.py:297`) — гейтить на `SUBJECTIVE_TYPES`.
- [ ] `contradiction_resolver` — строить subject-key из `re.sub(_NEG_RE,' ',claim)` (учёт negations).
- [ ] `SleepTimeWorker` Phase 3 — `await asyncio.to_thread(...)` (не блокировать event loop, I28).
- [ ] `forgetting._find_dependents` fails-open to [] → логировать WARNING + флаг `dependents_unknown`.
- [ ] `causal_chain` — single-pass reachability с global visited + cap (комбинаторный рост на hub/diamond графах).
- [ ] `IndexCoordinator` (`:43,58,71`) — `index_fact/remove_fact` → `index()/remove()`.
- [ ] `meta_supervisor` — реализовать throttle через `last_mhi`/`mhi_check_sec` и `if old_mode != self._mode:` transition-hook (или удалить F841).
- [ ] Backend-дивергенция: дропнуть unused reverse-edge `weight*0.9` (`memory_graph`/`sqlite_graph` vs `cypher`).
- [ ] `_next_seq` (`provenance_chain.py:266`) — не проглатывать DB-ошибку в sentinel `seq=0`.
- [ ] `web_console` self-probe — строить base из loopback (Host-header SSRF).
- [ ] Rate limiter — за доверенным прокси брать rightmost untrusted hop из XFF (не `request.client.host`).
- [ ] Gemini model id — валидировать против `^[A-Za-z0-9.\-]+$` (`llm_router.py:260`, `gemini_models.py:205`).
- [ ] Console — рендерить через `textContent`/DOMPurify + CSP-header (XSS через `/telegram/webhook`).
- [ ] `build_kb_graph` — scope ESM-лестницу к genuinely-Observed fact_ids (или фильтр `claim_type='WORLD_FACT'`).

---

## Рекомендованный порядок

`#1 → #10 → #2 → #4/#5 → #3/#16 → #6/#7 → #9/#27 → остальное (silent-swallow #8/#22/#23/#24, RAR #21, утечка #20)`

**Старт:** `#1` — самая маленькая правка с наибольшим эффектом (восстанавливает единственный механизм самозащиты хранилища).
