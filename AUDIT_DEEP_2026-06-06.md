# 🔱 VELANTRIM V8.7 «Titan» — Глубокий аудит (2026-06-06)

> Метод: multi-agent аудит. 6 recon-агентов (карта подсистем) → 12 dimension-finder'ов (корректность, конкурентность/целостность, безопасность, обработка ошибок, архитектура, SQL/миграции, тесты/CI, разбор pending-диффа) → состязательная верификация КАЖДОЙ находки независимым агентом → синтез.
> Итог: **91 находка проверена → 63 подтверждено/вероятно, 28 отсеяно как ложные.** Счёт после дедупликации: **Critical: 1 · High: 11 · Medium: 17 · Low: 19.**

## Резюме

Система VELANTRIM V8.7 «Titan» архитектурно зрелая: эпистемическое ядро (ESM-машина, TruthGate, hash-chained provenance/audit, write-gate, contradiction-resolver) спроектировано продуманно, а pending-дифф F-01/F-02/P0 закрывает реальные дыры в обработке ошибок и целостности. Однако фундаментальный системный риск — рассинхрон между задокументированными гарантиями и фактической рантайм-реальностью: ключевые защитные механизмы либо мертвы из-за дрейфа API (MetaSupervisor вызывает несуществующий `compute_mhi`), либо отключены флагами по умолчанию (write_gate, truth_policy), либо обходятся (`transition_esm` минует TruthGate). Самая опасная находка одна и достигает Critical: вся MHI/DLQ/budget-driven машина деградации MetaSupervisor навсегда инертна в продакшене из-за проглоченного ImportError. На втором уровне — расхождение Python-матрицы ESM и DB-триггеров (500 на легитимных переходах), GDPR-эрозия (PII остаётся в `fact_versions`/`l0_raw_memory` после «удаления», over-deletion по substring-LIKE), split-brain L0/L1 в batch-пути и неполная защита от подделки в hash-цепях (actor/reason вне хэша). CI заявлен BLOCKING, но все три гейта (ruff/mypy/pytest-coverage) красные — защитная сеть либо обходится, либо ветка немёржабельна.

---

## Находки по severity

### CRITICAL

**1. MetaSupervisor: вся машина деградации мертва — `_collect_mhi` импортирует несуществующий `compute_mhi`, ImportError проглочен на DEBUG**
`core/meta_supervisor.py:259-260` (вызов), проглатывается на `:282-283`, кэш-дефолт на `:134`.
`_collect_mhi()` делает `from core.mhi import compute_mhi; report = compute_mhi(store)`, но `core.mhi` экспортирует только `MHICalculator`/`MHIReport`/`MHIStatus`/`check_mhi` — `compute_mhi` был переименован (это зафиксировано даже в тест-диффе `tests/test_invariants.py:283`). На каждом heartbeat импорт бросает ImportError, который ловится широким `except Exception as exc: logger.debug(...)`. Поскольку битый импорт стоит ПЕРВОЙ строкой блока `if store is not None`, до сбора DLQ (`:267-272`) и budget (`:274-280`) управление вообще не доходит — все три сигнала замораживаются на самых здоровых значениях (mhi=1.0, dlq=0, budget=0.0). Ветка `store is None` тоже пиннит MHI=1.0/HEALTHY.
**Последствие:** автономная «иммунная система», единственная задача которой — обнаружить коллапс здоровья памяти и перевести хранилище в DEGRADED/SAFE_MODE (read-only, экстренный GC), НИКОГДА не реагирует на реальную деградацию. Защитный механизм для хранимых знаний AI-агента полностью инертен в продакшене, а единственный след — DEBUG-лог, который в проде никто не включает. Тесты I-MS2/I-MS3 проходят только потому, что вручную выставляют `_mhi_cache` и зовут `_evaluate` напрямую, минуя `_collect_mhi`.
**Рекомендация:** заменить на `from core.mhi import MHICalculator; report = MHICalculator(store).calculate(); self._mhi_cache = report.mhi; self._mhi_status_cache = report.status.value` (паттерн уже используется в `server.py` и `tests/test_invariants.py:289`); вынести сбор DLQ/budget в отдельные try-блоки, чтобы один сбой не убивал остальные; поднять проглатывание с DEBUG до WARNING/ERROR; добавить smoke-тест, который зовёт `_collect_mhi()` против заполненного store и проверяет, что `_mhi_cache` ушёл с 1.0. Удалить неиспользуемый `from core.mhi import MHIStatus` на `:247`. (Эта находка НЕ входит в pending-дифф — `git diff` для файла пуст.)

---

### HIGH

**2. Python-матрица ESM permissivнее DB-триггеров — `transition_esm()` проходит свою проверку, затем триггер ABORT'ит с необработанным IntegrityError (500 клиенту)**
`core/memory.py:38-47` (ESM_TRANSITIONS) против `migrations/009_truth_kernel.sql:88-112` (esm_allowed_transitions).
Python разрешает Observed→Supported/Validated/Collapsed, Hypothesized→Validated/Collapsed, Supported→Collapsed, Validated→Collapsed — DB не разрешает НИ ОДИН из этих переходов. `transition_esm()` валидирует по permissivной Python-матрице, проходит, затем `update_state()` делает необёрнутый `UPDATE facts SET epistemic_state=...`.
**Последствие:** на полностью мигрированной БД (единственная конфигурация, где Truth Kernel включён) легитимный вызов `transition_esm(fid,'Validated')` из Observed проходит Python-проверку и затем бросает `sqlite3.IntegrityError('VELANTRIM ESM VIOLATION')` из триггера — необработанное исключение к API-потребителю (500). На немигрированной БД тот же shortcut молча проходит, записывая нелегальный по truth-модели переход — гарантия зависит от окружения. Это и есть причина, по которой `build_kb_graph.py` вынужден вручную карабкаться по 3-шаговой лестнице.
**Рекомендация:** выбрать единственный источник истины — либо ужесточить ESM_TRANSITIONS до точного зеркала esm_allowed_transitions, либо добавить недостающие строки в DB-таблицу. Добавить тест, утверждающий идентичность Python-матрицы и DB-таблицы.

**3. `store_facts_batch` молча переписывает claim у Supported-факта и создаёт L0/L1 split-brain (store_fact тот же случай отклоняет)**
`core/memory.py:1293-1313` (drift-блок batch), против отклоняющего raise в store_fact на `:501-509`.
Drift-ветка в batch срабатывает только при `"Contradicted" in allowed`. Для Supported `ESM_TRANSITIONS['Supported']={'Validated','Collapsed'}` не содержит Contradicted → внутренний `if` ложен, matching `else` отсутствует. Результат: `record['epistemic_state']` остаётся дефолтным 'Observed', изменённый claim пишется в L1 через ON CONFLICT, а l0_record уходит в L0 со state 'Observed'. L1 остаётся 'Supported'.
**Последствие:** (1) Split-brain — `get_fact()` читает L0 первым, поэтому возвращает 'Observed', пока БД говорит 'Supported', что ломает downstream ESM-логику, консолидацию и аудит. (2) Семантический дрейф — у Validated-evidence-track факта в 'Supported' молча переписывается смысл при ингесте через batch-путь.
**Рекомендация:** зеркалить store_fact: при изменённом claim и state в {Validated,Supported}, где Contradicted не в allowed — писать ошибку/скипать вместо проваливания; и в no-drift update-ветке ВСЕГДА выставлять `record['epistemic_state']=existing['epistemic_state']` перед построением l0_record. (Отдельный тикет: pre-existing NameError на `core/memory.py:635` — `claim`/`source` не определены; маскируется, т.к. ловится только `sqlite3.OperationalError`, но падает при наличии FTS5.)

**4. GDPR forget_one/forget_all оставляют полный текст claim в `fact_versions` (и verbatim-источник в `l0_raw_memory`), восстановимый через get_fact_history после «завершённого» стирания**
`core/forgetting.py:193, 238-271`.
`forget_one`/`forget_all` делают только `DELETE FROM facts`. Не трогаются `fact_versions` (по дизайну хранит ВСЕ исторические версии claim с полным текстом, VS-01) и `l0_raw_memory` (исходный сырой текст verbatim). PII полностью восстановима через `VersionStore.get_fact_history`/`get_raw_text_for_fact`.
**Последствие:** GDPR-запрос «право на забвение» возвращает `reason='gdpr_completed'`, пока персданные сохраняются минимум в двух других таблицах. Прямой провал комплаенса.
**Рекомендация:** в той же транзакции чистить/редактировать `fact_versions` и raw-текст. Нюанс: `l0_raw_memory` НЕЛЬЗЯ удалить — триггеры `prevent_raw_delete`/`prevent_raw_update` (migration 010) ABORT'ят DELETE и UPDATE; нужен trigger-aware путь редактирования. Смежные баги: (1) `forget_all` не включает `foreign_keys`, поэтому CASCADE-очистка relations не работает; (2) `l0_fact_provenance` имеет `REFERENCES facts` без `ON DELETE CASCADE` → под `forget_one` (FK ON) удаление может упасть с FK-violation.

**5. forget_all выбирает факты по неякорной substring-LIKE на source/metadata → необратимое cross-user over-deletion в GDPR-пути**
`core/forgetting.py:238-242`, дефолт `user_id="default"` на `:221`.
`WHERE source LIKE '%{user_id}%' OR metadata LIKE '%{user_id}%'` — стирание 'user_4' удаляет и 'user_42'/'user_421'; дефолтный 'default' матчит любой факт с подстрокой 'default'.
**Последствие:** GDPR-запрос на одного пользователя может необратимо удалить данные других; случайный вызов с дефолтом массово удаляет факты.
**Рекомендация:** матчить по структурному полю (`json_extract(metadata,'$.user_id') = ?`) — требует нормализации схемы. Минимум немедленно: отклонять пустой/«default» user_id без явного force-флага.

**6 + 7. Hash-цепи provenance и audit исключают `actor`/`reason` (и `confidence`) из хэша — молчаливая подделка кто/почему проходит verify()**
`core/provenance_chain.py:245-264` (_compute_hash), verify() `:210-241`; и `core/audit_chain.py:68-86`, `:327-340`.
provenance `_compute_hash` хэширует только prev_hash/event_type/fact_id/from_state/to_state/payload_str/created_at — `actor`/`reason` хранятся, но НЕ в хэше. audit_chain опускает `confidence`/`reason` (verify_chain даже не выбирает `reason`). Эмпирически: после `UPDATE provenance_chains SET actor='attacker'` verify вернул `(True,'verified')`.
**Последствие:** атакующий/багованный writer с доступом к БД переписывает КТО заблокировал/верифицировал факт и ПОЧЕМУ (а в audit — `confidence`, ядро truth-сигнала), а verify рапортует «verified». «Blockchain-grade» гарантия ложна для этих полей.
**Рекомендация:** включить `actor`/`reason` (provenance) и `reason`/`confidence` канонизированно в `_compute_hash` обоих модулей; добавить `reason` в SELECT verify_chain. Версионировать схему хэша (hash_version), иначе все существующие цепи провалят verify() — нужна разовая ре-хэш-миграция.

**8. CausalGraph.import_snapshots() молча роняет рёбра при любом сбое add_relation**
`core/causal_graph.py:925-927`.
`except (ValueError, Exception): continue` — проглатывает любую ошибку add_relation (FK-violation, trigger-rejection) и скипает ребро без лога. Возвращается только success-count.
**Последствие:** при ре-импорте каузального графа невставившиеся рёбра исчезают молча, импорт рапортует правдоподобный счёт. Downstream каузальный вывод работает на неполном графе — труднообнаружимая частичная потеря данных.
**Рекомендация:** ловить конкретно `(sqlite3.IntegrityError, ValueError)`, логировать каждое дропнутое ребро на WARNING, возвращать оба счёта (imported и failed) либо abort на integrity-ошибках.

**9. CI заявлен BLOCKING (mypy), ruff+pytest — жёсткие гейты, но все три выходят ненулевым сегодня**
`.github/workflows/ci.yml:34,37,40-41`; coverage-гейт в `pyproject.toml`.
(1) ruff `check core/` exit 1: F-коды (≈52×F401, 4×F841, ранее F822 — починен в working tree). (2) mypy (BLOCKING) exit 1 с десятками ошибок. (3) pytest наследует `--cov=core` + `fail_under=80`. Абсолютные счёты version-зависимы, но направление каждого гейта (exit 1) устойчиво.
**Последствие:** если CI блокирующий — ни один PR не мёржится, пока ruff+mypy не чисты, но репозиторий представлен зелёным. Либо CI обходится (гейт-театр), либо ветка перманентно немёржабельна.
**Рекомендация:** выбрать одну реальность — починить F-коды + mypy, либо снять метку BLOCKING. Пинить ruff/mypy точно (`==x.y.z`).

**10. API rename-дрейф: вызовы удалённых символов (`update_fact`, `create_store`, `EssenceLayer`, `get_budget_planner`, `get_living_store`)**
`core/truth_maintenance.py:44,214`; `core/app.py:137`; `core/essence_facade/situation.py:91`; `core/meta_supervisor.py:276`.
mypy --strict помечает множество вызовов символов, не существующих в рантайме. Сильнейший — `truth_maintenance.py:44` (reinforce) и `:214` (confidence_decay): `from core.memory import ... update_fact` исполняется до любой логики → каждый вызов бросает ImportError, и ни один тест эти функции не трогает. `get_budget_planner` в meta_supervisor сидит внутри try/except: pass — budget-pressure молча остаётся 0.0.
**Последствие:** truth_maintenance write-пути и сбор budget-pressure падают в рантайме; где обёрнуто в except: pass — деградируют молча. Это ровно те баги, которые mypy --strict существует чтобы блокировать.
**Рекомендация:** трактовать mypy attr-defined/call-arg список как punch-list; чинить каждый вызов (`update_fact`→store_fact/transition_esm; `create_store`→make_store; `EssenceLayer`→Essence/compose_essence; `get_budget_planner`→evaluate_budget). Добавить точечные тесты.

**11. Re-archival может затереть original_claim (truncated to 500) на втором проходе** *(latent на БД без триггеров 009)*
`core/memory_archival.py:120-127, 199-226`.
После починки IN-list-синтаксиса: archive_old_facts выбирает `WHERE created_at < cutoff` без исключения уже-архивированных. На втором проходе указатель `[ARCHIVED: ...]` (а не реальный claim) пишется в новый файл, `INSERT OR REPLACE` перезатирает original_claim (truncated [:500]). restore_fact находит только указатель → оригинал невосстановим. **На триггер-БД (009) модуль вообще не работает: `bump_fact_version` ABORT'ит UPDATE на `:219` — архивация всегда падает в report.errors.**
**Рекомендация:** `AND fact_id NOT IN (SELECT fact_id FROM archived_facts)`; `INSERT OR IGNORE`; хранить полный claim; добавить `fact_version = fact_version + 1` в UPDATE для совместимости с триггером.

---

### MEDIUM

**12. Tag-рёбра несут inference_source=NULL, ломая UNIQUE-дедуп → пересборки KB-графа накапливают дубликаты рёбер** — `core/knowledge_linker.py:164-170` vs `:226-234`; потребитель `scripts/build_kb_graph.py:126`. `link_by_tags` не эмитит `inference_source`; constraint `UNIQUE(from,to,type,inference_source)` трактует NULL как различные → дубли при перезапусках. → заставить `link_by_tags` эмитить `inference_source`.

**13. modality_guard использует bare list-truthiness для evidence_refs — пропускает не-dict/фальшивые доказательства** *(latent: нет прод-вызова)* — `core/truth_policy.py:177-182,191-197`. Любой truthy-список (включая `["i said so"]`) проходит, в обход канонического `fact_evidence_ref`. → заменить на `if fact_evidence_ref(fact) is None: return False`.

**14. truth_maintenance.supersede() промоутит Observed→Validated без TruthGate/source/evidence (обход I68)** *(latent: нет живых вызовов)* — `core/truth_maintenance.py:101-113`. → прогонять new_fact через TruthGate.evaluate перед transition_esm("Validated").

**15. Audit hash-цепь опускает `confidence`/`reason`** — `core/audit_chain.py:68-86,327-340`. *(Слита с #6/#7; для audit-only severity medium — нужен прямой DB-доступ.)*

**16. `store_facts_batch` опускает claim_type/origin_type → bulk-факты хранятся как UNKNOWN modality** — `core/memory.py:1172-1186,1236-1253`. Каждый batch-факт получает NOT NULL DEFAULT 'UNKNOWN' → world-skills никогда не заполняют `idx_facts_world_fact_conf`; modality-based retrieval/decay трактуют их как UNKNOWN. → прогонять classify_claim + writeGate per-fact, писать claim_type/origin_type.

**17. Namespace-bridge рёбра (conf 0.4) ниже дефолтного порога 0.5 у causal_chain/implications** — `core/knowledge_linker.py:196,270-277`; `core/causal_graph.py:466,516`. Bridge-рёбра (единственные мосты между подразделами) отбрасываются на дефолтах → multi-hop reasoning молча останавливается у стен подразделов, хотя скрипт печатает высокий «% связано». → поднять NAMESPACE_BRIDGE_CONFIDENCE до ≥0.5 либо понизить дефолт traversal до 0.4.

**18. HybridRetriever пересобирается и весь корпус ре-энкодится на каждой ветке каждого запроса** *(эффект только при установленных sentence-transformers)* — `core/branch_manager.py:212`. Игнорирует dirty-flag IndexCoordinator → на ~19k фактах × 2-3 ветки sub-секундный retrieval → многосекундный. → кэшировать один HybridRetriever по версии store; пересборка только при `is_hybrid_dirty`.

**19. transition_esm: check-then-act гонка — read через get_fact() на отдельном соединении, затем необёрнутый UPDATE (только WHERE fact_id)** — `core/memory.py:982-1000` + `:911-960`. Под конкурентными writer'ами через async_store executor → last-writer-wins + фантомная provenance-история. → CAS-guard `WHERE fact_id=? AND epistemic_state=?` в update_state, rowcount==0 = проигранная гонка.

**20. Catch-all handler возвращает сырой str(exc) клиентам — утечка фрагментов SQL-схемы и тел ошибок upstream-провайдеров** — `server.py:3737-3743` (+ `:1856,1868,3722,3740`, `api/llm_routes.py`). → возвращать `{"error":"internal_server_error"}`, детали логировать server-side; echo за debug-флагом.

**21. RAR-извлечение (_extract_rar) опускает byte-accumulation guard MAX_EXTRACTED_SIZE (есть в zip/tar) — RAR decompression-bomb disk-DoS** *(только при установленном rarfile)* — `core/file_parsers/archive_parser.py:240-253`. → аккумулировать `RarInfo.file_size`, брейкать на MAX_EXTRACTED_SIZE; либо отключить .rar (как .7z в v8.5.3).

**22. Provenance-событие удаления факта пишется на отдельном соединении, сбой проглатывается → tamper-evident цепь развивает пробелы** — `core/forgetting.py:423-434`, вызов `:196-198`. `append()` открывает СВОЁ соединение, при сбое `except: pass`, DELETE всё равно коммитится. Плюс самоконтенция: BEGIN IMMEDIATE против того же файла под WAL. → прокинуть внешний `conn` в `append()` (как optional-conn в `_next_seq`).

**23. truth_maintenance вторичные integrity-записи молча проглатываются; contradict() возвращает changed=True даже при дропнутой записи в registry** — `core/truth_maintenance.py:79-80,142-143,183-194`. → логировать на WARNING; для contradiction-registry трактовать сбой как реальную ошибку.

**24. BranchManager retrieval и LLM/essence-пути проглатывают все исключения и деградируют до пустых/шаблонных ответов без логирования** — `core/branch_manager.py:220-245`, `:173-176`. Опаснейший случай — retrieval вернул [] (повреждённый индекс/DB-lock), кормя confidence-0.8 LLM-ответ. → сузить except'ы, логировать, пробросить degraded-флаг в BranchResult.

**25. Мёртвый, схемно-расходящийся provenance-путь: RawMemoryStore/raw_derivation_chain (migration 010) не используется, прод пишет в l0_fact_provenance; нет self-DDL guard** — `core/raw_memory.py:176-185,228` vs `core/memory.py:218-227,768`. → удалить мёртвый путь ЛИБО консолидировать; добавить self-DDL guard.

**26. situation.py импортирует несуществующий get_living_store — LivingContext-обогащение (7 измерений) навсегда мертво, ImportError проглочен** — `core/essence_facade/situation.py:91-92,102`. → добавить `get_living_store(conn)` в living_context.py либо строить `LivingContextStore(store._conn)`; сузить except. (Дифф трогал living_context.py, но фабрику не добавил.)

**27. Дефолтный addopts --cov + fail_under=80 делает любой частичный/локальный pytest-ран exit 1 несмотря на прохождение всех тестов** — `pyproject.toml:99,110-111`; `ci.yml:40`. → вынести `--cov` из дефолтного addopts в выделенный full-suite CI-шаг.

**28. test_confidence_boundary_values ничего не утверждает: valid-цикл проглатывает все исключения; invalid-цикл `pytest.raises((ValueError, Exception))` схлопывается до bare Exception** — `tests/test_adversarial.py:265-274`. → в valid утверждать сохранение и round-trip; в invalid использовать только `pytest.raises(ValueError)`.

---

### LOW

- **adaptive_truth: RED-zone порог истины ослабляется user satisfaction** `core/adaptive_truth.py:101-104,151-168` *(dead code)* — `_apply_satisfaction` снижает min_confidence на 0.1 для ЛЮБОЙ зоны включая RED (medicine/law/finance). → guard'ить relaxation только для GREEN/personal.
- **decide() ALLOW-shortcut использует SELF_VALIDATING вместо SUBJECTIVE_TYPES** `core/truth_policy.py:297-316` *(off by default)* — GOAL/SYSTEM_NOTE без доказательств → ALLOW вместо GAP_NOTICE. → гейтить на SUBJECTIVE_TYPES.
- **Contradiction resolver пропускает negations (больше не/уже не/no longer/n't)** `core/contradiction_resolver.py:32-56` *(gated OFF)* — противоположно-полярные факты получают разные subject-keys. → строить subject-key из `re.sub(_NEG_RE,' ',claim)`.
- **conversation_consolidation: add_insight сбрасывает created_at; finalize перезаписывает user_goal без fallback** `core/conversation_consolidation.py:130,189` *(не подключён)*. → не трогать created_at; `user_goal or row["user_goal"]`.
- **storage_info() lru_cache не инвалидируется reset_graph_store()** `core/storage_facade.py:38-41,60-74`. → `storage_info.cache_clear()` в reset_graph_store().
- **Reverse-edge weight*0.9 (sqlite/memory) vs single directed edge (cypher) — латентная backend-дивергенция** `core/backends/memory_graph.py:35-36`; sqlite 107-115; cypher 127-145 (вес нигде не используется). → дропнуть unused 0.9 reverse-write.
- **causal_chain перечисляет все пути с per-path visited (нет global dedup) → комбинаторный рост на hub/diamond графах глубины 4** `core/causal_graph.py:462-510,576-598,640-662` (через propagate_change/counterfactual). → single-pass reachability с global visited; cap на total results.
- **import_snapshots() success-shaped imported=0 без логирования при провальном Neo4j-reload** `core/causal_graph.py:892-927` *(тот же except #8)*. → narrow catch, лог row-id.
- **IndexCoordinator зовёт несуществующие NGramIndex.index_fact/remove_fact** `core/index_coordinator.py:43,58,71` *(dead code)* — реальный API: index()/remove(). → сменить вызовы; поднять except до warning.
- **meta_supervisor: unused last_mhi → MHI пересчитывается каждые 10s вместо 30s; unused old_mode → нет единого transition-hook** `core/meta_supervisor.py:203,290` (F841). → реализовать throttle и `if old_mode != self._mode:` emit transition, либо удалить.
- **SleepTimeWorker.think() Phase 3 запускает блокирующие sqlite-upsert'ы прямо на event loop без to_thread** `core/sleep_time_worker.py:467,475` (подрывает Slow/Fast разделение I28). → `await asyncio.to_thread(...)` вне lock.
- **build_kb_graph ESM-лестница scoped только по corpus id-set → pre-existing Hypothesized/Supported reasoning-факты с коллизией id молча промоутятся к Validated** `scripts/build_kb_graph.py`. → снапшотить genuinely-Observed fact_ids; либо фильтр claim_type='WORLD_FACT' AND origin_type='EXTERNAL'.
- **Authenticated Host-header SSRF в /console/auth/verify self-probe** `api/web_console.py:95-101,438-487` *(за валидным API-key)*. → строить self-probe base из loopback.
- **Rate limiter ключится по request.client.host → за nginx-прокси все клиенты делят один bucket (DoS)** `server.py:542-562` *(default-off)*. → при доверенном прокси брать rightmost untrusted hop из XFF.
- **Request-controlled Gemini model id f-string-интерполируется в URL-path без валидации** `core/llm_router.py:260-278`; `core/gemini_models.py:205-210` (host фиксирован — path-injection, не SSRF). → валидировать против `^[A-Za-z0-9.\-]+$`.
- **Console рендерит LLM/memory-контент через innerHTML самописным санитайзером без CSP** `static/console/index.html:5638-5669` *(single-tenant, но контент входит через /telegram/webhook)*. → DOMPurify/textContent; CSP-header; escapeHtml для `it.emoji`.
- **_next_seq проглатывает DB-ошибки до sentinel seq=0** `core/provenance_chain.py:266-282` (PK предотвращает реальную порчу). → не проглатывать в 0.
- **forgetting._find_dependents fails open to []** `core/forgetting.py:513-524` — delete-impact warning может ложно рапортовать ноль зависимостей. → логировать WARNING, сигналить `dependents_unknown`.
- **branch_manager.py:33 импортирует unused DEFAULT_TRIAD (F401)** — role-resolution делегирован resolve_roles. → дропнуть из импорта.
- **provenance_chains без append-only DB-триггеров (в отличие от memory_events) — I89 enforced только verify(), tail-deletion обходит verify()** `core/provenance_chain.py:40-57,89-100`. → добавить prevent_update/prevent_delete триггеры; verify() проверять непрерывность seq.
- **Дубликаты дефиниций/именований**: `_ESM_RANK` определён дважды (`core/semantic_dedup.py:51-53`) → удалить дубль; два модуля `text_utils` (core/ orphaned, ноль импортёров) → удалить/переименовать; `perspectives.py` пресеты DEEP/PRACTICAL/CREATIVE_TRIAD, SIMPLE_DUO в `__all__` но не потребляются → подключить или удалить.

---

## Оценка pending-диффа

Незакоммиченные правки F-01/F-02/P0 в целом **корректны и направлены верно** — закрывают реальные silent-failure и concurrency-дыры с сохранением поведения:

- **F-01/F-02 (affordance_linker.py, living_context.py)**: замена silent `except: pass` на counted+logged failure-путь — корректно, образцовый паттерн, который стоит распространить на #8/#21/#22.
- **causal_graph.is_causal_graph_enabled()**: логирование при сбое чтения конфига — корректно.
- **provenance_chain.append()**: одно соединение для seq+prev-hash+insert с WAL, `_next_seq()` с optional conn — корректно, СНИМАЕТ часть concurrency-риска внутри вызова. **Упущено:** actor/reason всё ещё вне хэша (#6); нет append-only триггеров; self-контенция при вызове из forgetting не устранена (#22).
- **build_kb_graph.py**: строгая ESM-лестница через 3 bulk-UPDATE с temp-table и bump fact_version — улучшение против старого кода (гнавшего всю facts-таблицу прямо в Validated). **Упущено:** scoping только по corpus id-set; обход transition_esm-аудита.
- **tests/**: Windows tempdir cleanup, `asyncio.run`, compute_mhi→MHICalculator rename — корректно. **Критическое упущение:** rename применён к ТЕСТАМ, но НЕ к прод-вызову в `meta_supervisor.py:259` (#1, Critical).

**Главный системный пробел диффа:** он чинит обработку ошибок и атомарность точечно, но не трогает rename-дрейф в прод-коде (#1, #10, #26) и расхождение Python-матрицы ESM с DB-триггерами (#2) — самые высокоимпактные находки лежат ВНЕ диффа.

---

## Что сделано хорошо

- **Глубина эпистемической модели.** ESM-машина, разделение claim_type/origin_type, write-gate, TruthGate как «единственный путь к Validated», hash-chained provenance/audit, contradiction-registry с CRISPR-spacer — продуманная, согласованная truth-архитектура. DB-триггеры truth-kernel (009) реально enforce'ят ESM на уровне БД.
- **Защитное отношение к разрушительным операциям.** GDPR erasure_log tombstone атомарно с DELETE; ImmutableCore/Ring-Zero исключаются из archival/forgetting; dry_run-preview в forget_all; намеренное отключение .7z за zip-bomb-риск — видна threat-modeling-дисциплина.
- **Pending-дифф — образцовый паттерн.** Замена silent `except: pass` на counted+logged failure и консолидация provenance.append в одно соединение с WAL — именно та дисциплина, которой не хватает остальному коду.
- **Качество комментариев и инвариантов.** Инварианты (I68, I89, I28, VS-01, I-AR1) явно задокументированы и привязаны к коду; in-code признания ограничений честны.

---

## План действий

1. **Починить MetaSupervisor (#1, Critical).** Заменить `compute_mhi` на `MHICalculator(store).calculate()`, разнести MHI/DLQ/budget по отдельным try-блокам, поднять swallow до WARNING, добавить smoke-тест на `_collect_mhi()`. Восстанавливает единственный механизм самозащиты хранилища.
2. **Устранить весь rename-дрейф прод-кода (#10, #26), верифицируя через mypy --strict.** Прогнать mypy attr-defined/call-arg как punch-list: `update_fact`/`create_store`/`EssenceLayer`/`get_budget_planner`/`get_living_store`. Добавить тесты на write-пути.
3. **Свести Python-матрицу ESM и DB-триггеры к единому источнику истины (#2).** Выбрать одну сторону, добавить тест на идентичность множеств — убирает 500-е на легитимных переходах.
4. **Закрыть GDPR-дыры (#4, #5).** Чистить/редактировать fact_versions и raw-текст в транзакции удаления (trigger-aware для l0_raw_memory); заменить substring-LIKE на структурный user_id; добавить foreign_keys в forget_all.
5. **Починить batch-путь записи (#3, #16).** Зеркалить контракт store_fact: отклонять drift на Supported, синхронизировать L0=L1 epistemic_state, прогонять classify_claim/write-gate, писать claim_type/origin_type.
6. **Усилить tamper-evidence hash-цепей (#6/#7) с версионированием схемы.** Включить actor/reason/confidence в хэш; разовая ре-хэш-миграция; append-only DB-триггеры на provenance_chains; проверка непрерывности seq в verify().
7. **Разрешить CI-парадокс (#9, #27).** Решить, действительно ли mypy BLOCKING; вынести coverage-гейт из дефолтного addopts; точно запинить ruff/mypy; затем починить F401/F841 и mypy-ошибки.
8. **Распространить logged-failure-паттерн диффа на оставшиеся silent-swallow точки (#8, #22, #23, #24) и закрыть RAR-bomb (#21) + str(exc)-утечку (#20).** Вторичные, но многочисленные integrity/observability/safety-дыры; правки дешёвые и однотипные.
