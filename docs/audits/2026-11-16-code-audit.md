> Исторический read-only аудит исходного SHA. Его формулировки «код не изменён»,
> статусы PR и локальные artifact paths относятся к 16 ноября, до последующего
> разрешения пользователя на исправления. Актуальный реестр предложений и проверок:
> [remediation register](2026-11-17-remediation-register.md). Native reproductions
> доступны в тестах соответствующих PR; локальные logs/ZIP передаются отдельно.

# Сводный аудит Velantrim ExoCortex Titan и проверка дополнительных отчётов

**Дата:** 16 ноября 2026, UTC.  
**Репозиторий:** https://github.com/velantrian/Velantrim-ExoCortex-Titan  
**Проверенный код:** `main@485c4b0906ec35829ff7231c6276bf7d817f096f`. Новые пробы выполнены на том же commit, что и первоначальный аудит. Ссылки на исходники закреплены на этом SHA.  
**Режим:** только отчёт и локальные доказательства. Исходники, тесты, конфигурация и lockfile не изменены. Коммитов, PR, push, merge и записей в Notion не выполнялось.

## Вывод перепроверки

Дополнительные отчёты указали на реальные пробелы первого аудита. Его 28 находок сохраняют значение, но он недостаточно проверял смысловую сохранность свидетельств, поведение при отказах knowledge-policy и распространение provider exceptions. Эти вопросы теперь проверены отдельно.

После сопоставления A-01…A-28 первого отчёта, T-01…T-19 из сообщения ChatGPT и F1…F9 приложенного файла Manus реестр содержит **42 позиции: 8 высокой, 26 средней и 8 низкой критичности**. Это дефекты, условные риски и технический долг, а не 42 эксплуатируемые security-уязвимости. **14 дополнительных позиций C01–C14** отделены от повторов и комментариев к уже найденному коду.

Ключевые новые результаты:

- **FactsPack действительно может работать fail-open.** При отказе builder обычный `pipeline.run()` пропустил canonical Validated-факт с confidence **0,1** в выдачу с `truth_status=VERIFIED`. Штатный PRECISION-путь исключил его. Нижележащий TruthGate не устранил нарушение: он пропускает повторную оценку уже Validated canonical records.
- **Семантическая дедупликация теряет различающиеся записи.** Удалены варианты с отрицанием, числом, условием, переставленными аргументами и независимым source. Удаление не отражено в `excluded_facts`.
- **Неподтверждённое усиление влияет на durable promotion.** Три похожих утверждения одного источника, включая отрицание, прошли из Observed в Validated при включённом boost. Без него все три остались Observed. **Persisted confidence при этом остался 0,74**, а не стал 0,84; важное последствие — изменение отбора и ESM, а не доказанное сохранение повышенного числа.
- **Текст исключения может распространять credential.** Настоящий h11 сформировал ошибку с синтетическим секретом. Этот exception затем прошёл через HTTP `/query`, лог, completion event и настоящую SQLite trace; также через `/llm/test`, SSE `/chat/stream` и router stream event. Реальный production-ключ не использовался и его компрометация не заявляется.
- **Ошибка классификатора ослабляет mandatory write gate.** При исправном классификаторе тестовая запись отклонена; при исключении — durably создана как UNKNOWN/Observed. Это нарушение первоначального допуска, не автоматическое получение Validated.

Высокую критичность не следует автоматически заменять на P0. Например, для C01 подтверждены реальные пути распространения синтетического секрета при ошибке, но не показан неаутентифицированный доступ к production-key. Observer в C03/C04 пассивен: неверный clean-вердикт подтверждён, блокировка либо изменение доставленного ответа не установлены.

## Новая экспериментальная база

Выполнены **13 групп offline-проб**: одна группа проверяет несколько связанных дефектов, поэтому число групп не равно числу позиций реестра. Внешние model/provider запросы подменены; для persistence и promotion использованы реальные временные SQLite-БД. В fault injection менялись объекты в памяти процесса, исходники не редактировались.

| Проверка | Что наблюдалось | Контроль/граница |
|---|---|---|
| Semantic dedup | 5 пар разных записей → по одной записи; excluded=[] | Проверен настоящий FactsPackBuilder, не fixture его результата |
| Faithfulness | Поддержанный и противоположный ответы получили score=1, grounded_claims=1 | Отрицание «не» теряется в токенах длиной ≥3; Observer противоположного ответа — allow/clean |
| Observer при отказе check | `truth_policy.decide` выбрасывает exception → allow/clean, следа unavailable нет | Остальные проверки исполняются; goal-alignment зафиксирован нейтральным значением |
| Corroboration | В памяти 0,74→0,84 у одинакового источника/отрицания/условия | Реальный engine с boost: 3 Validated; без boost: 3 Observed; DB confidence в обоих случаях 0,74 |
| FactsPack отказ | В PRECISION стало 1 VERIFIED-факт с confidence 0,1 | Без отказа — 0 фактов; с require_policy=True — FactsPackPolicyUnavailableError |
| Классификатор отказал | Rejected write → created UNKNOWN/UNKNOWN/Observed | Одинаковый payload с source=unknown; успешная классификация — rejected_write_gate |
| Promotion mode | `PRECIISION` превратился в BALANCED и разрешил promotion | Правильный PRECISION отклонил тот же уровень confidence/evidence |
| Exceptions / credential | Синтетический маркер найден в HTTP, SSE, logs, event и actual trace DB | Error создан h11; сбой provider-вызова подменён. Никаких настоящих credential/provider calls |
| MCP input | 2000 элементов и body около 1,15 МБ полностью приняты и dispatched | Bounded probe; не нагрузочный тест и не поиск точной границы OOM |
| Пятиэтапный retrieval | Ненулевой rrf_score, final_score=0; graph neighbor не попал в full top_k | Обычный retrieve при тех же детерминированных rankings возвращает final_score 2 и 1 |
| BranchManager | `get_all_facts()` без ограничений, весь результат передан retriever; DB exception→[] | Небольшой spy-корпус; не измерение production-латентности |
| DenseRetriever | Сбой второго instance выключает первый; 2 потока загружают одну model дважды | Детерминированный fake model/barrier. Векторный кеш не объявлен незащищённым |
| Gemini cache | TTL=3600s только у provider; после двух 404-запросов stale cache retained | 1 create, 4 generate POST из-за v1beta/v1 retry; fake responses, без Gemini-сети |

Существующие целевые тесты Observer, consolidation, retriever lifecycle, crypto и MCP: **59 passed, 2 warnings, 4,72 с**. Это совместимо с найденными пробелами: они не покрывают все проверенные негативные случаи. Полный suite повторно не запускался, потому что source commit не изменился. Его прежний наблюдаемый результат остаётся **4915 passed / 5 failed / 17 skipped / 21 deselected / 1 xfailed**, а отдельный BM25 differential control — **5 passed**. Эти результаты не складываются в один «новый общий» счётчик.

## Единый реестр без дублирования

Для A01–A28 сохранены исходные ID и оценки. Ссылки и подробности находятся ниже в этом же файле; первый отчёт также сохранён отдельно. C01–C14 — дополнительные проверенные позиции.

| ID | Критичность | Проблема | Основная точка | Соответствие другим отчётам |
|---|---|---|---|---|
| A01 | Высокая | BM25 отбрасывает релевантные документы с неположительным score | [core/hybrid_retriever.py:171](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L171) | T-03; Manus F5 (уточнение причины) |
| A02 | Высокая | Dev Compose: известный ключ + публикация на всех интерфейсах | [docker-compose.dev.yml:22](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docker-compose.dev.yml#L22) | — |
| A03 | Высокая | Telegram подтверждает отклонённую запись | [app/telegram_ingest.py:109](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/app/telegram_ingest.py#L109) | — |
| A04 | Средняя | Повтор Telegram-сообщения создаёт новый факт | [app/telegram_ingest.py:56](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/app/telegram_ingest.py#L56) | Manus F2 |
| A05 | Средняя | CORS блокирует PATCH и MCP idempotency header | [server.py:736](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L736) | Manus F7 |
| A06 | Средняя | Добавление ребра стирает свойства графовых узлов | [core/backends/sqlite_graph.py:93](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/backends/sqlite_graph.py#L93) | — |
| A07 | Средняя | У фоновой очереди EventBus нет потребителя | [core/event_bus.py:93](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/event_bus.py#L93) | — |
| A08 | Средняя | SleepTimeWorker не останавливает дочерние задачи | [core/sleep_time_worker.py:334](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/sleep_time_worker.py#L334) | — |
| A09 | Средняя | CoreMemoryBlocks публикует устаревший кеш после более новой записи | [core/sleep_time_worker.py:169](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/sleep_time_worker.py#L169) | — |
| A10 | Средняя | Параллельный разбор архивов делит изменяемую глубину рекурсии | [core/file_parsers/archive_parser.py:115](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/archive_parser.py#L115) | — |
| A11 | Средняя | Текст внутренних файлов архива теряется | [core/file_parsers/archive_parser.py:122](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/archive_parser.py#L122) | — |
| A12 | Средняя | MHI-export несовместим с реальным MHIReport | [core/velantrim_reports/mhi_report.py:68](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/velantrim_reports/mhi_report.py#L68) | — |
| A13 | Средняя | GraphLab-мост несовместим с вызываемым API | [core/graph_lab_bridge.py:120](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab_bridge.py#L120) | — |
| A14 | Средняя | DI API: неинициализированный конструктор, неработающий setter, неверная фабрика | [core/app.py:62](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/app.py#L62) | — |
| A15 | Средняя | EmbeddingStore сообщает сохранённые строки после ошибки commit | [core/embedding_store.py:171](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/embedding_store.py#L171) | T-13 |
| A16 | Средняя | Ограничения ресурсов GraphLab не ограничивают фактическую работу | [core/graph_lab.py:105](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab.py#L105) | — |
| A17 | Средняя | `/query/roles` игнорирует domain и cognitive_mode | [server.py:2257](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2257) | — |
| A18 | Средняя | MCP запускает синхронный инструмент в event loop HTTP-сервера | [api/mcp_gateway.py:184](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/mcp_gateway.py#L184) | — |
| A19 | Средняя | MCP-сессии и их lock entries не имеют срока/лимита хранения | [core/mcp_transport.py:207](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/mcp_transport.py#L207) | — |
| A20 | Средняя | CI не контролирует ряд критичных контрактов и режим без dense | [.github/workflows/ci.yml:31](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/.github/workflows/ci.yml#L31) | T-16 |
| A21 | Низкая | Общий токенизатор требует старый pymorphy2 вместо установленного pymorphy3 | [utils/text_utils.py:40](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/utils/text_utils.py#L40) | — |
| A22 | Низкая | Публичные facade-мосты подавляют импорт отсутствующих функций | [core/essence_facade/mirror.py:12](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/essence_facade/mirror.py#L12) | T-08 |
| A23 | Низкая | Мёртвые helpers, неиспользуемые опции и пустой MinerU backend | [core/llm_stream.py:425](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_stream.py#L425) | T-18 (дополнение) |
| A24 | Низкая | Дублирование алгоритмов и высокая сложность функций | [core/memory.py:1638](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L1638) | T-14 (низкий долг) |
| A25 | Низкая | Публичные backend-контракты не описывают существенную семантику | [core/graph_store.py:35](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_store.py#L35) | — |
| A26 | Низкая | Ruff зафиксирован на устаревшей ветке 0.4 | [pyproject.toml:99](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/pyproject.toml#L99) | — |
| A27 | Низкая | Неучтённая лицензия опционального PyMuPDF, неполные license-метаданные SBOM | [core/file_parsers/pdf_parser.py:172](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/pdf_parser.py#L172) | — |
| A28 | Низкая | Документация API и статусов расходится с кодом | [api/llm_routes.py:208](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/llm_routes.py#L208) | T-19; Manus F8/F9 |
| C01 | Высокая | Exception text распространяет credential в responses/logs/events/traces | [server.py:2569](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2569) | T-01 |
| C02 | Высокая | Semantic dedup уничтожает разные свидетельства без excluded record | [core/facts_pack.py:336](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/facts_pack.py#L336) | T-02 |
| C03 | Средняя | Lexical overlap выдаётся как grounding при противоположном утверждении | [core/output_faithfulness.py:92](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/output_faithfulness.py#L92) | T-04 |
| C04 | Средняя | Невыполненная проверка Observer превращается в clean | [core/observer.py:142](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/observer.py#L142) | T-05 |
| C05 | Высокая | Необоснованный corroboration boost меняет durable ESM outcome | [core/consolidation_engine.py:161](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/consolidation_engine.py#L161) | T-06 |
| C06 | Высокая | Отказ FactsPack снимает часть policy-фильтра в основном pipeline | [core/pipeline.py:896](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/pipeline.py#L896) | T-07 |
| C07 | Высокая | Отказ classifier превращается в допустимый UNKNOWN при записи | [core/memory.py:1708](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L1708) | Manus F1 |
| C08 | Средняя | MCP не ограничивает body/batch на входе | [api/mcp_gateway.py:83](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/mcp_gateway.py#L83) | Manus F3 |
| C09 | Средняя | Невалидный explicit promotion mode становится BALANCED | [core/memory.py:3846](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L3846) | Manus F4 |
| C10 | Средняя | Stage 9/10 CI резолвит зависимости вне uv.lock | [.github/workflows/stage9-browser-acceptance.yml:31](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/.github/workflows/stage9-browser-acceptance.yml#L31) | Manus F6 |
| C11 | Средняя | retrieve_5stage не заполняет итоговый score; graph expansion теряется | [core/hybrid_retriever.py:632](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L632) | T-09 |
| C12 | Средняя | BranchManager строит retrieval по всей БД и скрывает отказ | [core/branch_manager.py:243](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/branch_manager.py#L243) | T-10 |
| C13 | Средняя | Global dense availability и несериализованная загрузка model | [core/hybrid_retriever.py:282](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L282) | T-11 |
| C14 | Средняя | Gemini cachedContent остаётся в локальном кеше после expiry/404 | [core/llm_stream.py:193](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_stream.py#L193) | T-12 |

## Подробности дополнительных находок

### C01 — Секретоподобный текст exception выходит за диагностическую границу

**Где:** [core/llm_router.py:159](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_router.py#L159), [server.py:2569](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2569), [server.py:2574](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2574), [server.py:2589](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2589), [server.py:2634](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2634), [server.py:2209](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2209), [core/llm_stream.py:504](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_stream.py#L504), [api/llm_routes.py:162](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/llm_routes.py#L162). **Статус:** воспроизведено, высокая критичность.

`h11.Request` с небезопасным символом внутри Authorization header выбросил LocalProtocolError с полным значением заголовка. Это реальная ошибка установленного h11, не придуманное сообщение. Чтобы проверить дальнейшее распространение без сети, созданное исключение передано вместо результата provider call в настоящий server HTTP-путь. Использован только явно синтетический маркер.

Маркер обнаружен в `llm_answer`, `llm_meta.error`, warning log, аргументе completion event и сохранённой записи `reasoning_traces.answer` реальной SQLite-БД. `/llm/test` вернул его в `detail`; `/chat/stream` — в SSE error; `core.llm_stream` — в error event. `repr(LlmCallConfig(...))` также содержит api_key. Документированное свойство request-key «не сохраняется на сервере» не выполняется для этого failure path.

**Граница:** это подтверждение утечки при exception, содержащем credential, а не факт компрометации production-токена. В пробы не входили настоящие ключи, настоящий provider response либо неаутентифицированный доступ к API. Ошибочный ключ может содержать в себе действующий credential плюс лишний символ; считать его безопасным для logs нельзя.

**Предложено:** на HTTP/SSE/event/trace границах возвращать fixed error_code/correlation_id; не помещать provider exception text в поле ответа. Диагностические сообщения очищать до записи, а не только перед выдачей HTTP. Для api_key — SecretStr либо как минимум `repr=False`, валидация управляющих символов. Regression suite должен проверять все перечисленные sinks. PR #514 остаётся draft/unmerged и не считается исправлением main.

### C02 — Лексическое сходство удаляет разные записи и их provenance

**Где:** [core/facts_pack.py:307](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/facts_pack.py#L307), [core/facts_pack.py:336](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/facts_pack.py#L336), [core/facts_pack.py:436](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/facts_pack.py#L436), [core/pipeline.py:839](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/pipeline.py#L839). **Статус:** воспроизведено, высокая критичность.

Код считает `|A ∩ B| / min(|A|, |B|)`, а не обычный Jaccard `intersection/union`. Это overlap coefficient; у включающихся наборов слов он равен 1. Удаляется запись с меньшим confidence, независимо от отрицания, чисел, условий, порядка аргументов и источника.

Все пять пар в probe потеряли вторую запись: «разрешён / не разрешён», «10 / 100», вариант с «только», A→B/B→A и одинаковый текст из разных sources. Во всех случаях `excluded_facts=[]`, поэтому клиент не видит, что свидетельство было отброшено. В summary уменьшается даже наблюдаемое число найденных записей.

**Предложено:** дедуплицировать только идентичные повторы одной и той же записи по устойчивой идентичности и payload. Сохранять отдельное provenance независимых источников. Более сильная семантическая группировка должна быть явной, объяснимой и не удалять противоречия/условия. PR #509 содержит кандидат исправления, но он open/unmerged; его patch здесь не применялся и не сертифицирован этим аудитом.

### C03 — Grounding-score не отличает поддержку от отрицания

**Где:** [core/output_faithfulness.py:18](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/output_faithfulness.py#L18), [core/output_faithfulness.py:90](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/output_faithfulness.py#L90), [core/output_faithfulness.py:164](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/output_faithfulness.py#L164), [core/observer.py:76](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/observer.py#L76), [server.py:2659](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2659). **Статус:** воспроизведено, средняя критичность, пассивная диагностика.

Источник: «Доступ к локальной памяти **не** разрешён…». Ответ: «Доступ к локальной памяти разрешён…». Оба ответа — поддержанный контроль и противоположный — получили score=1, grounded_claims=1. Русское «не» не попало в токены длиной ≥3. GCR оставил противоположный ответ без unsupported-маркера; Observer вернул allow/clean.

**Граница:** extractor документирован как лексическая эвристика, и его значение действительно нельзя считать semantic verifier. Дефект в том, что поля grounded/clean и их применение не сохраняют это различие. Observer здесь не блокирует и не переписывает ответ. Production profile включает `ENABLE_OBSERVER=1`, поэтому диагностика wired и enabled в этом профиле, но наблюдение live-инцидента не заявляется.

**Предложено:** отдельные статусы lexical_overlap, citation_exists, semantic_support_unknown, contradiction_detected и supported. До появления semantic verifier нельзя объявлять наличие lexical overlap проверкой поддержки утверждения. Должны быть отрицательные controls на полярность, числа, идентификаторы, условия и сроки. PR #521/#522 — mitigations/контрактные изменения, не полноценная semantic support implementation и не закрытие #512.

### C04 — Неисполненная проверка Observer выглядит как успешно пройденная

**Где:** [core/observer.py:139](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/observer.py#L139), [core/observer.py:142](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/observer.py#L142), [core/observer.py:154](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/observer.py#L154), [core/observer.py:162](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/observer.py#L162). **Статус:** воспроизведено, средняя критичность.

Fault injection в `truth_policy.decide` оставил `decision=allow`, `flags=[]`, `reason=clean`, `is_clean=True`, хотя обязательная для составного verdict проверка не завершилась. `details.truth_policy` отсутствует, но явного unavailable-статуса нет. Ошибка optional audit sink также подавляется; best-effort логирование само по себе допустимо, но не является гарантией успешной аудиторской записи.

**Предложено:** каждый check должен иметь статус completed/unavailable/skipped с machine-readable причиной. Unavailable не должен означать clean; для пассивного режима нужен хотя бы warn/check_unavailable. Перед превращением Observer в gate потребуется отдельная политика обязательности. Не решать проблему ещё одним `except: return allow`. Часть этой проблемы адресует незалитый #509.

### C05 — Corroboration меняет promotion без независимого подтверждения

**Где:** [core/consolidation_engine.py:161](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/consolidation_engine.py#L161), [core/consolidation_engine.py:183](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/consolidation_engine.py#L183), [core/consolidation_engine.py:308](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/consolidation_engine.py#L308), [core/consolidation_engine.py:390](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/consolidation_engine.py#L390), [core/consolidation_engine.py:412](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/consolidation_engine.py#L412), [core/memory.py:2416](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L2416). **Статус:** воспроизведено helper-ом и реальным SQLite engine, высокая критичность.

Три похожих записи одного source, включая отрицание и условный вариант, получают +0,1 за размер кластера. Источник, независимость и совместимость утверждений не проверяются. `list(facts)` копирует только список: словари входа действительно меняются.

Уточнение важнее простого счётчика: `get_all_facts()` возвращает deep copies, а финальный TruthGate перечитывает durable record. В probe DB confidence **не увеличился**: остался 0,74. Но local boost дал 0,84 и пропустил все три записи через engine threshold 0,75. Затем обычный gateway/TruthGate BALANCED с confidence 0,74 и двумя legacy evidence refs разрешил все три promotion; на диске они стали Validated. В идентичной контрольной БД при отключении только boost три записи остались Observed.

**Предложено:** не считать количество похожих записей независимым подтверждением. Для corroboration определить доказательную lineage, совместимость полярности/условий и явный effect contract; score ранжирования не должен незаметно ослаблять admission precheck. Сохранять один существующий gateway/TruthGate owner. Этот probe не показывает обход самого TruthGate — он был вызван и разрешил по своему bounded контракту.

### C06 — FactsPack failure ослабляет read-side policy, а нижний gate не эквивалентен

**Где:** [core/pipeline.py:800](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/pipeline.py#L800), [core/pipeline.py:896](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/pipeline.py#L896), [core/pipeline.py:906](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/pipeline.py#L906), [core/pipeline.py:965](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/pipeline.py#L965), [core/pipeline.py:1283](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/pipeline.py#L1283), [core/model_free_core.py:206](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/model_free_core.py#L206). **Статус:** воспроизведено, высокая критичность.

Сначала создан и легально promoted реальный canonical факт. Затем поддерживаемый update понизил его confidence до 0,1, сохранив Validated. В штатном PRECISION pipeline FactsPack исключил его и вернул `no_policy_eligible_local_evidence`. При исключении только `FactsPackBuilder.build` основной путь вернул raw_facts; тот же факт дошёл до ответа с VERIFIED и без причины отказа.

Причина прохождения нижнего gate точная: `pipeline.truth_gate` пропускает повторную evaluation для canonical Validated/ImmutableCore. Это не эквивалентно текущим allowed-state/confidence/relevance policy FactsPack. При `require_policy=True` тот же сбой корректно вызвал `FactsPackPolicyUnavailableError`; основной `run()` этот режим не запрашивает.

**Предложено:** включить required-policy контракт для основного pipeline и преобразовывать его отказ в явную недостаточность/недоступность policy. Не возвращать unfiltered facts. Проверить сохранение telemetry и absence of LLM call при отказе, не удаляя существующие canonical optimizations без отдельного основания.

### C07 — Сбой classifier превращается в разрешённый UNKNOWN

**Где:** [core/memory.py:1697](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L1697), [core/memory.py:1708](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L1708), [core/memory.py:1722](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L1722), [core/memory.py:4311](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L4311), [core/write_gate.py:85](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/write_gate.py#L85). **Статус:** воспроизведено single-write, аналогичный batch catch проверен кодом; высокая критичность.

Одинаковая запись о воде с source=`unknown` при успешной классификации получает WORLD_FACT и rejected_write_gate из-за отсутствия допустимого provenance. При исключении classifier fallback нормализует отсутствующие axes к UNKNOWN, и mandatory write gate разрешает запись. Probe получил `created`, а readback подтвердил canonical UNKNOWN/UNKNOWN/Observed.

**Граница:** допуск явно неизвестной модальности предусмотрен дизайном; проблема — смешивание намеренно UNKNOWN и ошибки обязательного вывода. Это fault-path, а не доказанная удалённая команда вызвать exception; новая запись остаётся Observed. В предыдущем аудите этот failure differential не был выполнен.

**Предложено:** отказ classifier при обязательной auto-classification должен быть отдельным rejection/unavailable outcome, не фактической модальностью. Явное UNKNOWN, если оно допускается контрактом, отделить от operational failure. Проверить single/batch/cognitive adapters и отсутствие durable side effects на отказе.

### C08 — MCP не ограничивает ресурсы входного запроса

**Где:** [api/mcp_gateway.py:83](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/mcp_gateway.py#L83), [api/mcp_gateway.py:139](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/mcp_gateway.py#L139), [api/mcp_gateway.py:170](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/mcp_gateway.py#L170). **Статус:** код и bounded HTTP probe, средняя критичность.

Body читается полностью до декодирования JSON, а число batch items не ограничено. Probe с 2000 items и 1 147 481 байтом получил HTTP 200, все 2000 вызовов dispatched. Это не измерение предела отказа и не утверждение, что 1 МБ сам по себе опасен; показано отсутствие handler-level bounds.

**Предложено:** проверка Content-Length плюс счётчик фактически прочитанных bytes до полной буферизации, максимальное число batch items, общий бюджет обработки и фиксированная ошибка превышения. Auth/rate limit ограничивают доступ и скорость, но не стоимость одного запроса. Внешний proxy limit может уменьшить риск конкретной установки, но такого ограничения внутри gateway нет. Это отдельный дефект от A18 (блокировка event loop).

### C09 — Опечатка в explicit promotion mode снижает строгость

**Где:** [core/memory.py:3841](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L3841), [core/memory.py:3846](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L3846), [core/truth_gate.py:56](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/truth_gate.py#L56), [core/cognitive_store.py:31](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/cognitive_store.py#L31), [core/promotion_gateway.py:66](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/promotion_gateway.py#L66). **Статус:** воспроизведено, средняя критичность прямого API.

Для Supported-факта confidence=0,8 с двумя refs правильный PRECISION вернул low_confidence и оставил Supported. `PRECIISION` молча преобразован в BALANCED и продвинул аналогичный факт в Validated. `mode=None` как documented default не является проблемой; проблема — fallback для явно переданного невалидного значения.

**Предложено:** отклонять неизвестные значения до чтения/gate/write; использовать enum на adapters. Публичный HTTP promotion path не позволяет клиенту выбрать такую произвольную строку через typed gateway, поэтому удалённый policy-bypass этим probe не показан.

### C10 — Два acceptance workflow устанавливают незамороженные зависимости

**Где:** [.github/workflows/stage9-browser-acceptance.yml:31](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/.github/workflows/stage9-browser-acceptance.yml#L31), [.github/workflows/stage9-browser-acceptance.yml:35](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/.github/workflows/stage9-browser-acceptance.yml#L35), [.github/workflows/stage10-bounded-pilot.yml:31](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/.github/workflows/stage10-bounded-pilot.yml#L31). **Статус:** подтверждено конфигурацией, средняя критичность воспроизводимости.

Stage 9/10 выполняют `pip install -e '.[server,parsers]'`, а Stage 9 дополнительно резолвит `playwright>=1.48,<2` и устанавливает browser. Эти графы не ограничены frozen uv.lock, хотя основной CI и Docker имеют locked dependency path. Lock-аудит 121 пакета не является аудитом произвольных версий, выбранных отдельным pip resolution в будущем run.

**Предложено:** перевести runtime extras на общий frozen setup; Playwright/browser version управлять явно и сохранять их exact evidence. Не описывать все workflow как воспроизводимые только по наличию uv.lock. Это уточнение supply-chain охвата первого отчёта, не отрицание существующих SBOM/CodeQL/wheel gates.

### C11 — Пятиэтапный retriever нарушает score-контракт

**Где:** [core/hybrid_retriever.py:575](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L575), [core/hybrid_retriever.py:614](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L614), [core/hybrid_retriever.py:632](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L632), [core/hybrid_retriever.py:637](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L637). **Статус:** воспроизведено с deterministic rankings, средняя критичность.

Реальный `retrieve_5stage()` выставляет `final_score=0.0`, сортирует по rrf_score и не копирует его в final_score, если reranker не сработал. Probe получил rrf_score 2/1 и final_score 0/0. Обычный `retrieve` в том же контроле вернул final_score 2/1.

Добавленные graph-neighbors имеют rrf_score 0; когда исходные top_k кандидатов уже заполнили выдачу с положительными оценками, графовое расширение после сортировки/среза не попадает в итог. Это не доказательство бесполезности graph expansion во всех сценариях — например, неполная исходная выдача отличается.

**Предложено:** единая семантика score между методами; явная оценка/квота graph candidates и тест graph-only полезного соседа. Отдельные тесты optional reranker и без него.

### C12 — BranchManager загружает весь корпус и теряет operational failure

**Где:** [core/branch_manager.py:243](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/branch_manager.py#L243), [core/branch_manager.py:249](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/branch_manager.py#L249), [core/branch_manager.py:257](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/branch_manager.py#L257). **Статус:** код и call-spy probe, средняя критичность.

Role retrieval вызывает `get_all_facts()` без limit/domain, затем строит новый HybridRetriever по всему отфильтрованному набору. Probe подтвердил безаргументный вызов и передачу полного корпуса при retrieval_k=3. При DB exception путь вернул `[]`, не указав unavailable; внешний try/catch уже не узнает, почему данных нет.

**Предложено:** использовать существующий bounded retrieval и его фильтры; возвращать typed degraded/unavailable status. При нескольких ветках оценить суммарный бюджет корпуса/model work. Данный probe не является production load benchmark.

### C13 — Global dense availability и гонка создания модели

**Где:** [core/hybrid_retriever.py:220](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L220), [core/hybrid_retriever.py:282](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L282), [core/hybrid_retriever.py:330](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L330), [core/hybrid_retriever.py:342](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L342), [core/hybrid_retriever.py:347](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L347). **Статус:** воспроизведено, средняя критичность.

У корректно загруженного instance available=True сменилось на False после отказа загрузки другого model instance: `_AVAILABLE` общий для класса. Отдельный barrier-probe заставил два concurrent constructors загрузить одну model дважды — get/create/write `_MODEL_CACHE` не сериализованы. Дорогая инициализация может удвоить память/загрузку на старте.

**Предложено:** доступность хранить у instance либо model-keyed outcome; single-flight/per-model lock для создания. `_VECTOR_CACHE` уже защищён RLock, и данный аудит не объявляет его гонкой. Одновременное вычисление одинакового вектора вне lock также не равно повреждению кеша.

### C14 — Gemini cache не восстанавливается после истечения ресурса

**Где:** [core/llm_stream.py:55](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_stream.py#L55), [core/llm_stream.py:193](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_stream.py#L193), [core/llm_stream.py:207](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_stream.py#L207), [core/llm_stream.py:396](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_stream.py#L396), [core/llm_stream.py:410](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_stream.py#L410), [core/llm_stream.py:633](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_stream.py#L633). **Статус:** воспроизведено fake create/expired responses, средняя критичность.

Provider resource создаётся с TTL 3600s, но local map содержит только имя, без timestamp/expiry/capacity. После двух simulated expired-cache запросов local entry остался. Каждая попытка снова отправила тот же cachedContent и получила 404, с retry на другую API version: 1 create, 4 generate calls, ни одного refresh. Кеш также не ограничен по числу уникальных contexts/accounts.

**Предложено:** bounded TTL/LRU, expiry metadata, удаление stale entry при cache-specific response и один контролируемый rebuild/retry. Не ретраить бесконечно и не считать любой 404 гарантированным истечением кеша: ошибки модели/версии должны различаться. Изменение provider/version/model context должно сохранять нынешнюю whole-text identity.

## Что уточнено или не превращено в новую уязвимость

| Замечание | Решение после проверки |
|---|---|
| T-01 обозначен P0 | C01 подтверждён синтетически на реальном HTTP/SQLite пути; уровень высокий. Компрометация действующего production-key и неаутентифицированная эксплуатация не заявляются |
| T-03 / Manus F5 | Это A01. Повторный контроль показал 5/5 pass при отключении только rank-bm25; объяснение только отсутствием внешней модели неполно. Early empty retrieval не доказывает допуск невалидного факта через TruthGate |
| Manus «1938 passed, 1 failed» | В тексте указана остановка suite на первом failure. Это ранний прогресс до остановки, а не завершённый прогон всех тестов; его нельзя сравнивать как альтернативное полное число с 4915/5 |
| T-06 «confidence повышается» | Local boost и alias mutation подтверждены; DB confidence в probe остался 0,74. Дополнительно установлено влияние на durable ESM, см. C05 |
| T-14 — RRF min/max scaling | Лишняя O(n) работа и неверное объяснение: RRF использует rank, нормализованный score игнорируется. Результат при тех же ranks не меняется. Низкий долг в рамках A24, не отдельная существенная ошибка ранжирования |
| T-15 — собственная crypto | Пользовательский HMAC stream + encrypt-then-MAC и `except BaseException` требуют review/явного backend contract, но криптоатака или нарушение целостности не доказаны. Optional fallback документирован; сам его факт не доказывает downgrade-уязвимость. Предпочтение проверенному AEAD — рекомендация, не подтверждённый exploit |
| T-17 — MCP process-local lock | Подтверждённое и уже документированное ограничение. В one-worker конфигурации это не новая эксплуатационная гонка. Многопроцессную гарантию эти locks не дают; A18/A19/C08 касаются других дефектов |
| T-18 — GCRResult / retrieve_diverse | В текущем tracked-коде callers не найдены; возможные внешние library clients не проверены. Кандидаты расширяют A23; нельзя автоматически удалить публичный метод |
| T-18 — Vision LLM | `_parse_vision_llm` в [core/file_parsers/image_parser.py:175](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/image_parser.py#L175) всегда NotImplementedError; вызывающий путь может перейти к OCR. Отражать как NOT_IMPLEMENTED, дополнение A23 |
| T-19 / Manus F8/F9 | Подтверждены stale examples/documentation. Docker уже устанавливает frozen hash-bound export, вопреки тексту [docs/operations/python-dependency-lock.md:36](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docs/operations/python-dependency-lock.md#L36). Таблица [docs/DEPLOY.md:161](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docs/DEPLOY.md#L161) неполна. Дополнение A28, не новые runtime-дефекты |
| Manus F2/F7 | Полностью покрыты A04/A05; различие оценок серьёзности не делает их двумя разными дефектами |
| T-08/T-13/T-16 | Дубли A22/A15/A20; сохранены исходные доказательства и оценки |

## Состояние Issue/PR: read-only сверка 16 ноября 2026

| Объект | Наблюдаемый статус | Следствие для этого аудита |
|---|---|---|
| Issue #510 | Open | BM25 остаётся A01 в проверенном main |
| Issue #511 | Open | Error/credential propagation — C01 |
| Issue #512 | Open | Semantic support не закрыт labels или Observer warning |
| Issue #513 | Open | Corroboration — C05 |
| PR #509 | Open, не draft, unmerged; head `39a705c6…` | Candidate dedup/Observer changes вне main |
| PR #514 | Open, draft, unmerged; head `5dae84bb…` | Candidate sanitized errors вне main |
| PR #515 | Closed, merged | Opt-in evidence labels для `/query` уже в main; это не semantic support verifier |
| PR #518 | Open, draft, unmerged; head `7d097e49…` | Chat labels вне main |
| PR #521 | Open, draft, unmerged; head `5057904c…` | Conservative semantic-unverified warning вне main |
| PR #522 | Open, draft, unmerged; head `5e2869c4…` | Child на #521: sent-record scope вне main |

Точный readback: [github-state.json](audit-addendum-evidence/github-state.json). PR bodies использованы как навигация, а не как замена собственным пробам. Здесь не проверялось исправленное поведение всех branch-heads, не разрешались merge/deploy и не изменялись статусы задач. Находка на main и достаточность proposed fix — разные вопросы.

## Приоритеты после объединения

1. **Границы доверия/отказа:** C01, C06, C07 — исключить попадание exception text в публичные/persisted sinks и ослабление gate при сбоях. Одновременно A02/A03/A04 — known dev credential exposure и достоверное подтверждение записи.
2. **Сохранность знаний:** A01, C02, C05; исправлять с differential controls для negation/numbers/conditions/provenance. C03/C04 — честно показывать неизвестную semantic support и недоступные checks.
3. **Исполняемые контракты и ресурсы:** A06–A19, C08/C09/C11–C14. Сохранять одного transaction/policy owner, bounded workers и корректную cancellation/idempotency.
4. **Проверки и сопровождение:** A20–A28, C10. Расширить tests по фактическим failure paths; не делать broad refactor одновременно с устранением high-risk дефектов.

Ни одна рекомендация в этом документе не является разрешением автоматически изменить main. Для последующего fix нужны тест желаемого поведения, который проваливается на исходном commit, затем проверка исправленного кода и сохранение контрольных случаев. Текущие probes демонстрируют дефекты и контрольные различия, а не означают, что исправление уже принято.

## Сохранённые подробности первоначальных A01–A28

Ниже включён подробный разбор из первого отчёта. Его оценки сохранены; новые уточнения и сопоставление находятся выше. Таким образом, скачанный Markdown содержит полный реестр и рекомендации, а не только ссылки на предыдущую беседу.

### A01 — Неположительный BM25 score превращается в отсутствие знаний

**Где:** [core/hybrid_retriever.py:148](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L148), [core/hybrid_retriever.py:171](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/hybrid_retriever.py#L171), [core/pipeline.py:700](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/pipeline.py#L700). **Статус:** воспроизведено, активный retrieval при установленном `rank-bm25` и недоступном dense.

`BM25Okapi` допускает нулевые и отрицательные IDF/score. Условие `if s > 0` удаляет соответствующие документы, включая точные совпадения. При кандидате `вода кипит при ста градусах` запрос `вода` дал raw score `-0.2746530721670274` и пустой результат. Fallback без `rank-bm25` вернул этот же факт. `HybridRetriever` с недоступным dense также вернул `[]`; pipeline считает это штатным отсутствием локальных данных и не включает собственный BM25 fallback, поскольку исключения не было.

**Влияние:** установка retrieval-extra или отказ загрузки dense-модели ухудшает работоспособность поиска. Узкое множество кандидатов после FTS особенно подвержено проблеме. Пять упавших тестов проходят в контрольном процессе после отключения только backend `rank-bm25`.

**Предложено:** определять lexical совпадение отдельно от знака оценки; выбрать согласованную формулу/нормализацию BM25. Просто пропустить все `s <= 0` в выдачу тоже нельзя: документы без совпадений часто имеют score 0. Добавить дифференциальные проверки маленького корпуса, частых терминов, отсутствующего термина и отказа dense.

### A02 — Dev-профиль доступен за пределами localhost с публичным ключом

**Где:** [docker-compose.dev.yml:21](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docker-compose.dev.yml#L21), [docker-compose.dev.yml:24](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docker-compose.dev.yml#L24). **Статус:** подтверждено конфигурацией; реальная доступность зависит от host firewall/сети.

Порт `8000:8000` публикуется Docker на всех интерфейсах, а API-ключ по умолчанию равен публичному `dev-key-change-me`. Даже при корректно работающем API-key middleware сосед по доступной сети знает credential для чтения и изменения памяти. Надпись «local development only» не ограничивает bind.

**Предложено:** по умолчанию `127.0.0.1:8000:8000`; для внешней публикации требовать явный bind и непустой пользовательский ключ. Hardened production Compose уже использует loopback по умолчанию — это положительный контроль. Публичный dev-ключ не является обнаруженным production-секретом.

### A03 — Telegram возвращает успех после отклонённой записи

**Где:** [app/telegram_ingest.py:76](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/app/telegram_ingest.py#L76), [app/telegram_ingest.py:109](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/app/telegram_ingest.py#L109), [app/telegram_ingest.py:119](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/app/telegram_ingest.py#L119), [app/telegram_ingest.py:126](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/app/telegram_ingest.py#L126), [server.py:3974](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L3974). **Статус:** воспроизведено fault injection.

Результат `store_fact()` не проверяется; возвращаемое `False` смешивает отсутствие создания и отказ. В cognitive-ветке также игнорируется результат `save_fact_dict`. Затем вызывается provenance-link и формируется `ok=True`, даже если `get_fact()` вернул `None`. Probe с отклонённой записью получил `{"ok": true, "fact": null}`. Webhook может отправить пользователю подтверждение сохранения, после которого Telegram больше не повторит успешно принятый update.

**Предложено:** использовать структурированный `WriteResult` и проверять accepted/durable outcome; не подтверждать сохранение до успешной записи. Разделить retryable storage failure и постоянный отказ policy/validation; сохранить диагностируемый статус provenance, не маскировать его под полный успех.

### A04 — Telegram replay не идемпотентен

**Где:** [app/telegram_ingest.py:56](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/app/telegram_ingest.py#L56), [app/telegram_bot.py:54](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/app/telegram_bot.py#L54). **Статус:** воспроизведено с реальной временной SQLite-БД.

Если `tg_<chat>_<message_id>` уже существует, код генерирует новый UUID вместо возврата прежнего результата. Две доставки одного сообщения создали два разных факта. Проверка существования и запись не атомарны; edited messages также не получают явно определённой семантики новой версии. Polling повышает offset до успешного ingest, что дополнительно затрудняет восстановление после сбоя.

**Предложено:** устойчивый ключ доставки `(channel, chat_id, message_id/update_id)`, уникальный DB constraint и повтор ранее сохранённого результата; отдельно описать обработку edits. В polling подтверждать/продвигать offset после согласованного durable outcome.

### A05 — CORS не соответствует HTTP/MCP-контракту

**Где:** [server.py:736](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L736), [server.py:740](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L740), [server.py:3026](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L3026), [api/mcp_gateway.py:132](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/mcp_gateway.py#L132). **Статус:** воспроизведено HTTP preflight.

Список методов не содержит `PATCH`, хотя API использует его для transitions, invalidation, goals, inbox и notes. Список заголовков не содержит `Idempotency-Key`, который принимает MCP gateway. Для явно разрешённого origin preflight дал соответственно `400 Disallowed CORS method` и `400 Disallowed CORS headers`.

**Предложено:** добавить фактически поддерживаемые method/header в allowlist; проверять preflight для каждого внешнего write-контракта. Ошибка относится к cross-origin браузерным клиентам; same-origin консоль и небраузерные клиенты этим ограничением не затрагиваются.

### A06 — `upsert_edge()` стирает props уже существующего узла

**Где:** [core/backends/sqlite_graph.py:72](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/backends/sqlite_graph.py#L72), [core/backends/sqlite_graph.py:93](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/backends/sqlite_graph.py#L93), [core/backends/cypher_graph_base.py:103](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/backends/cypher_graph_base.py#L103), [core/backends/cypher_graph_base.py:124](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/backends/cypher_graph_base.py#L124). **Статус:** воспроизведено на SQLite; идентичная replace-семантика видна в Cypher.

Добавление ребра вызывает `upsert_node(id)` без props. SQLite UPSERT заменяет `props_json` на `{}` и label на `Entity`; аналогичный Cypher SET делает то же. Probe: узел `label=Immutable, immutable=True, claim=...` после ребра стал `Entity, {}`. Memory backend сохраняет props, поэтому backend неэквивалентны.

**Предложено:** отделить `ensure_node_exists` с insert-only поведением от явного обновления props; зафиксировать merge/replace семантику и общие backend-contract tests. Речь о sidecar `gs_nodes`, а не доказанном обходе Ring Zero в канонической таблице `facts`.

### A07 — Background EventBus накапливает события без доставки

**Где:** [core/event_bridge.py:35](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/event_bridge.py#L35), [core/event_bus.py:93](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/event_bus.py#L93), [core/event_bus.py:102](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/event_bus.py#L102), [config/exocortex-dev.env:33](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/config/exocortex-dev.env#L33). **Статус:** воспроизведено; dev-профиль включает этот режим.

При `ENABLE_EVENT_BUS_BACKGROUND=1` publisher передаёт `dispatch=False`. Событие добавляется в deque, но в EventBus и вызывающем коде нет worker/dequeue пути. Прямой dispatch исполняет handlers, а фоновая ветка только растёт до 10 000 элементов. Probe с очередью размера 1: первая публикация успешна, handler не вызван, вторая истекает по timeout.

**Предложено:** единый lifecycle-managed consumer с bounded batch, shutdown и retry/DLQ, либо явный отказ включения background-флага до его появления. Возврат `True` должен означать ясно описанный статус принятия/доставки.

### A08 — Shutdown SleepTimeWorker оставляет фоновые `think()`

**Где:** [core/sleep_time_worker.py:334](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/sleep_time_worker.py#L334), [core/sleep_time_worker.py:529](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/sleep_time_worker.py#L529), [server.py:658](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L658). **Статус:** воспроизведено.

`update_from_episode()` создаёт задачи в `_bg_tasks`; `stop()` отменяет и ожидает только `_task` основного цикла. После stop в probe оставалась одна активная дочерняя задача. Новые episodes создают новые задачи без ограничения числа ожидающих; повторный `start()` также не защищён от создания второго цикла.

**Влияние:** работа с notebook/LLM может продолжаться после заявленного shutdown; накопленные задачи удерживают память и ссылки на старый worker.

**Предложено:** учитывать все задачи у одного owner, закрывать приём episodes, coalesce/ограничивать очередь think, cancel+await дочерние задачи, сделать start/stop идемпотентными.

### A09 — Порядок публикации кеша расходится с порядком commit

**Где:** [core/sleep_time_worker.py:155](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/sleep_time_worker.py#L155), [core/sleep_time_worker.py:169](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/sleep_time_worker.py#L169), [core/sleep_time_worker.py:186](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/sleep_time_worker.py#L186). **Статус:** воспроизведено; остаточный риск уже описан в `KNOWN_RISKS.md`.

Перенос публикации кеша после commit устранил недолговечную запись в RAM, но не сериализует весь update. В probe A завершил commit и был приостановлен; B завершил commit и публикацию; затем A опубликовал кеш. Итог: **SQLite = B, кеш = A**. Независимые уже созданные instances также не инвалидируют свои snapshots. Изменение словаря во время `get_system_context()` не защищено.

**Предложено:** lock вокруг commit+publication для одного instance, version/CAS для меж-instance свежести, либо читать согласованный persisted snapshot. Не считать успешный retry старого UPSERT безопасным относительно более нового значения.

### A10 — Глубина рекурсии архивов хранится в общем registry

**Где:** [core/file_parsers/archive_parser.py:110](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/archive_parser.py#L110), [core/file_parsers/archive_parser.py:117](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/archive_parser.py#L117), [core/file_parsers/archive_parser.py:133](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/archive_parser.py#L133), [core/file_parsers/file_ingester.py:242](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/file_ingester.py#L242). **Статус:** воспроизведено двумя потоками.

Парсер временно заменяет `registry._initialized['archive']` на instance с большей глубиной. Этот же registry используется параллельными вызовами `FileIngester`. Пока A разбирал внутренний файл, независимый top-level архив B был разобран с depth=1 вместо 0. Возможны ложные отказы по MAX_DEPTH и неверное восстановление registry при другом interleaving. Восстановление не оформлено как гарантированный `finally`.

**Предложено:** передавать depth/budget в контексте одной операции или создавать отдельный registry/ingester для рекурсии; не менять общую регистрацию. Нужен детерминированный concurrent-nested-archive тест.

### A11 — Рекурсивный archive ingest выбрасывает извлечённый текст

**Где:** [core/file_parsers/archive_parser.py:122](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/archive_parser.py#L122), [core/file_parsers/archive_parser.py:136](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/archive_parser.py#L136), [core/file_parsers/file_ingester.py:270](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/file_ingester.py#L270). **Статус:** воспроизведено.

Из результата внутреннего parser сохраняются только имя, тип, длина текста и error. В итоговый текст архива попадает список файлов. Probe извлёк 36 символов из `hold.txt`, но текстовый sentinel отсутствовал во всём возвращённом ParseResult. Временная директория после этого удалена; `to_fact()` получает листинг, а не содержимое документов.

**Предложено:** возвращать bounded дочерние ParseResult/SourceSpan либо явный поток результатов для хранения; отдельно ограничивать суммарный объём. Если архив намеренно является только каталогом, переименовать/документировать этот контракт и предоставить отдельный API извлечения содержимого.

### A12 — Экспорт MHI падает на реальном объекте

**Где:** [core/mhi.py:59](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/mhi.py#L59), [core/velantrim_reports/mhi_report.py:68](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/velantrim_reports/mhi_report.py#L68), [core/velantrim_reports/mhi_report.py:90](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/velantrim_reports/mhi_report.py#L90), [core/velantrim_reports/mhi_report.py:158](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/velantrim_reports/mhi_report.py#L158), [server_patch/export_endpoints.py:226](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server_patch/export_endpoints.py#L226). **Статус:** воспроизведено.

Producer `MHIReport` содержит `mhi` и `freshness_score`; consumer ожидает `score` и `freshness`. Прямой вызов `generate_mhi_report(real_MHIReport)` даёт `AttributeError: 'MHIReport' object has no attribute 'score'`. Исправление только score оставит ошибочное нулевое значение freshness из-за `getattr(..., 0)`. Дополнительная статистика ожидает `validated_count` вместо `validated_facts` и тоже молча пропускает показатель.

**Предложено:** типизировать параметр конкретным MHIReport/Protocol, согласовать оба имени, добавить producer→report→export integration test. Текущее покрытие файла — 16%, что не доказывает выполнение основной генерации.

### A13 — GraphLab bridge деградирует из-за несовместимого контракта

**Где:** [core/graph_lab_bridge.py:120](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab_bridge.py#L120), [core/graph_lab.py:319](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab.py#L319), [core/graph_lab_bridge.py:153](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab_bridge.py#L153), [core/graph_lab.py:144](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab.py#L144). **Статус:** воспроизведено.

`analyze_graph()` передаёт `db_path` в `graph_lab.analyze()`, у которого есть `conn`, а `db_path` нет. Ошибка поймана и превращается в `available=False`, даже при установленном NetworkX. Это уже признано inline-комментарием, но executable-дефект остаётся.

Есть и второй слой drift: bridge читает `betweenness_c`, а centrality возвращает `betweenness`; после исправления вызова концепты-мосты всё ещё будут пусты. `domain_a/domain_b` не используются, `max_cycle_len` также не передаётся.

**Предложено:** явный typed result и connection ownership, согласовать ключи и фильтры; тестировать реальный producer вместо fixtures старой формы. Прямой `/graph/analyze` вызывает `graph_lab` и не является этим сломанным bridge.

### A14 — DI-фасад не выполняет собственный публичный контракт

**Где:** [core/app.py:45](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/app.py#L45), [core/app.py:62](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/app.py#L62), [core/app.py:67](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/app.py#L67), [core/app.py:236](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/app.py#L236). **Статус:** три локальных воспроизведения.

`VelantrimApp()` не вызывает `_init_components`, поэтому задокументированный прямой конструктор даёт `KeyError('store')`. Setter `app.store = x` меняет `_components`, getter читает `_lazy`, поэтому возвращает прежнее хранилище. Фабрика causal graph вызывает отсутствующий `_GLOBAL_STORE._conn()` и падает с AttributeError. Последнее также уже помечено inline как known debt.

**Предложено:** явный единый lifecycle/инициализация DI, согласованный setter через `register_instance`, соединение causal graph от выбранного instance с определённым owner/close. Тестировать фактическую изоляцию данных и замену store, а не только создание объекта/health.

### A15 — Ошибка commit скрыта за положительным результатом batch

**Где:** [core/embedding_store.py:167](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/embedding_store.py#L167), [core/embedding_store.py:171](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/embedding_store.py#L171), [core/embedding_store.py:175](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/embedding_store.py#L175), [core/embedding_store.py:122](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/embedding_store.py#L122). **Статус:** воспроизведено fault injection; derived/опциональное хранилище.

`store_batch()` увеличивает count при INSERT, затем ловит ошибку commit и возвращает уже набранное число. Probe: reported_count=2, durable_count=0. Исключения отдельных INSERT тоже проглатываются без сведений о проблемных ID. `close()`/rollback не защищены `finally`; при сбое commit probe подтвердил, что close не вызван. Аналогичная форма открытия/закрытия встречается в других legacy-методах EmbeddingStore.

**Предложено:** connection context с гарантированными rollback/close; публиковать committed count только после успешного commit. Либо атомарный batch с исключением, либо typed partial-result с committed/failed IDs. Не возвращать успешный прогресс для недолговечной проекции.

### A16 — Заявленные бюджеты GraphLab не ограничивают память и перебор

**Где:** [core/graph_lab.py:105](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab.py#L105), [core/graph_lab.py:117](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab.py#L117), [core/graph_lab.py:169](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab.py#L169), [server.py:3681](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L3681), [server.py:3701](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L3701). **Статус:** подтверждено кодом, bounded probe перебора.

Все relations сначала загружаются `fetchall()`, только затем применяется `max_nodes` и seed-фильтр. Поэтому маленький max_nodes не ограничивает объём чтения/память. `nx.simple_cycles(g)` перечисляет циклы любой длины, и лишь после этого применяется `max_len`; limit ограничивает число подходящих результатов, но не работу. Probe с limit=1 заставил функцию просмотреть все 1000 поданных слишком длинных циклов. HTTP-параметры max_nodes/cutoff/limit не имеют верхних bounds.

**Предложено:** ограничивать запрос/итерацию на входе, применять `length_bound=max_len` поддерживаемой NetworkX, задавать бюджет времени/числа просмотренных элементов и верхние API bounds. Различать truncated/budget_exhausted/empty. Не возвращать пустой успешный анализ при operational failure.

### A17 — `/query/roles` сообщает неприменённые ограничения

**Где:** [server.py:2228](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2228), [server.py:2257](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2257), [server.py:2290](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2290). **Статус:** воспроизведено spy на реальном endpoint-функциональном пути.

Request принимает `domain` и `cognitive_mode`, но в `bm.reason()` передаются только query, roles, llm_config. Ответ всё равно записывает входные domain/mode в `effective_params`. Probe для biology/PRECISION подтвердил отсутствие обоих аргументов на consumer-границе.

**Предложено:** применить ограничения через существующий retrieval/policy owner либо убрать/отклонять неподдерживаемые поля. В `effective_params` возвращать только реально применённые значения. Здесь не доказан обход tenant authorization; domain — фильтр результата, а не установленная граница доступа.

### A18 — MCP блокирует общий HTTP event loop

**Где:** [api/mcp_gateway.py:95](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/mcp_gateway.py#L95), [api/mcp_gateway.py:170](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/mcp_gateway.py#L170), [api/mcp_gateway.py:184](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/mcp_gateway.py#L184), [core/mcp_transport.py:494](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/mcp_transport.py#L494). **Статус:** воспроизведено на gateway с контролируемым медленным handler.

`async def mcp_post()` напрямую вызывает синхронный `_dispatch`/`McpHandler.handle`. DB, граф, erasure и threading-lock внутри инструмента работают в event-loop потоке. При 150-мс dispatch тестовый 10-мс таймер проснулся примерно через 160 мс. Более длительная операция задержит health и другие запросы данного worker.

**Предложено:** выделенный ограниченный executor/`asyncio.to_thread` с продуманной семантикой отмены и side effects. Сохранить существующую session-serialization/idempotency и проверить потокобезопасность используемых соединений; нельзя просто перенести вызов в поток без этих проверок.

### A19 — MCP накапливает сессии без TTL и capacity

**Где:** [core/mcp_transport.py:207](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/mcp_transport.py#L207), [core/mcp_transport.py:210](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/mcp_transport.py#L210), [core/mcp_transport.py:256](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/mcp_transport.py#L256), [core/mcp_transport.py:272](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/mcp_transport.py#L272). **Статус:** подтверждено управлением коллекциями.

Каждый initialize без sid создаёт новую запись в `_sessions`. Удаление возможно только явным DELETE; срок жизни и максимальное число записей отсутствуют. Lock entries остаются после завершения calls до discard при удалении сессии. Для исчезнувших клиентов память удерживается до завершения процесса. Даже rate-limit ограничивает скорость, а не суммарный рост.

**Предложено:** bounded session registry с TTL/idle expiry, лимиты на caller и процесс, уборка неактивных lock entries при users=0. Сохранить уже исправленное правило не заменять lock, пока есть holder/waiters.

### A20 — Критичные контракты и fallback-профиль не защищены CI

**Где:** [.github/workflows/ci.yml:31](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/.github/workflows/ci.yml#L31), [.github/workflows/ci.yml:49](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/.github/workflows/ci.yml#L49), [.github/workflows/ci.yml:52](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/.github/workflows/ci.yml#L52), [pyproject.toml:115](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/pyproject.toml#L115), [tests/test_utils_text_utils.py:24](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/tests/test_utils_text_utils.py#L24). **Статус:** проверено конфигурацией, покрытием и локальным прогоном.

Lint/type gates охватывают только `core/`; coverage source также только `core`, хотя ключевые auth/HTTP/Telegram-контракты находятся снаружи. Основная CI-установка включает embeddings/retrieval; отдельной матрицы dense unavailable / lexical backend нет. A01 показывает, почему это существенно. Ряд smoke-tests проверяет только тип/непадение, пропуская семантическую деградацию, как в тесте morphology.

**Предложено:** сохранить общий blocking ratchet и добавить направленные contract/failure tests: реальный MHIReport→экспорт; denied Telegram write и replay; CORS; одноузловой BM25 без dense; stop дочерних задач; concurrent archive/cache; backend preservation. Расширять scope static analysis постепенно, без механического признания всех 31 mypy-сообщений runtime-багами. Добавить branch/fault coverage критичных отказов; текущие проценты — statement coverage.

### A21 — Две несовместимые реализации русской морфологии

**Где:** [utils/text_utils.py:40](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/utils/text_utils.py#L40), [core/lemmatizer_ru.py:41](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/lemmatizer_ru.py#L41), [core/affordance_linker.py:169](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/affordance_linker.py#L169), [core/living_context.py:381](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/living_context.py#L381), [pyproject.toml:40](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/pyproject.toml#L40). **Статус:** воспроизведено на frozen server-extra.

Установлен `pymorphy3`, используемый основным RU router, а общий utils-токенизатор пытается загрузить только `pymorphy2` и молча отключает морфологию. Probe: utils вернул `птицы/вьют/гнёзда` и available=False, основной модуль — `птица/вить/гнездо`.

**Предложено:** один поддерживаемый morphology adapter, явный статус fallback, семантический тест при установленном server-extra. Добавление старого pymorphy2 вместо исправления интеграции создаст ещё одну dependency-ветку.

### A22 — Неисправные facade API превращаются в нормальное отсутствие данных

**Где:** [core/essence_facade/mirror.py:12](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/essence_facade/mirror.py#L12), [core/essence_facade/observer_bridge.py:12](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/essence_facade/observer_bridge.py#L12), [core/essence_facade/gist.py:96](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/essence_facade/gist.py#L96). **Статус:** импорты/возврат None проверены; legacy/опциональные поверхности.

Запрашиваются отсутствующие `get_working_notebook()` и `get_observer()` вместо существующих `get_notebook(session_id)` и `observe(...)`. Широкие except возвращают None или ничего не делают, поэтому отсутствие constraints/observer неотличимо от исправного пустого состояния. Публичный facade экспортирует эти функции. Активная answer authority этого facade не доказана; поэтому критичность низкая.

**Предложено:** согласовать контракты, включая session scope; отделить feature-disabled от broken-dependency. Для непредназначенных к использованию API — явная deprecation/quarantine вместо бессрочного silent no-op.

### A23 — Мёртвые функции, неиспользуемые аргументы и заглушка backend

**Где и что найдено:**

| Код | Наблюдение | Предложено |
|---|---|---|
| [core/llm_stream.py:425](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/llm_stream.py#L425) `_parse_openai_sse_chunk` | Нет ссылок на функцию в текущем tracked-дереве вне определения | Удалить после проверки совместимости; потоковый путь уже использует другой parser |
| [core/metrics.py:36](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/metrics.py#L36) `_check_prometheus` | Нет callers; `_PROMETHEUS_AVAILABLE` обслуживает только этот неиспользуемый helper | Удалить helper и его отдельное состояние либо подключить к реальному статусу |
| [core/contradiction_registry.py:111](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/contradiction_registry.py#L111) `_set_nli_scorer` | Нет callers; возможный оставленный injection/test hook | Зафиксировать назначение; не удалять автоматически как публичную extension point |
| [core/file_parsers/pdf_parser.py:261](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/pdf_parser.py#L261) `_parse_mineru` | Читает весь PDF в память, неизменно возвращает пустой text, не вызывает MinerU | Убрать из cascade до реализации или явно сообщать unsupported; убрать лишнее чтение |
| [core/file_parsers/file_ingester.py:298](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/file_ingester.py#L298) `parser_name` | Принимается и не используется | Удалить параметр либо использовать для корректной статистики |
| [core/multilingual_router.py:109](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/multilingual_router.py#L109) `use_ngram` | Переключатель принимается, но не влияет на поиск | Реализовать переключение либо убрать неработающую опцию |
| [core/graph_lab_bridge.py:134](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab_bridge.py#L134), [core/graph_lab_bridge.py:189](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_lab_bridge.py#L189) | domain_a/domain_b/max_cycle_len принимаются, но не используются | Применять либо отклонять; см. A13 |
| [core/velantrim_reports/mhi_report.py:38](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/velantrim_reports/mhi_report.py#L38) `include_history` | Документированная опция без реализации | Реализовать или убрать из контракта |
| [core/velantrim_reports/truthgate_report.py:36](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/velantrim_reports/truthgate_report.py#L36) `show_passed` | Не влияет на таблицу, которая всегда включает все verdicts | Фильтровать вывод; тест обеих ветвей |

Неиспользуемые `exc_type`/`traceback` в context-manager signature из Vulture не считаются дефектом. Intentionally unwired research-модули, включая `identity_layer`, не объявлены мёртвым кодом только из-за отсутствия production-callers.

### A24 — Копии алгоритмов и трудные для проверки функции

**Где:** [core/backends/sqlite_graph.py:137](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/backends/sqlite_graph.py#L137), [core/backends/memory_graph.py:51](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/backends/memory_graph.py#L51), [core/backends/cypher_graph_base.py:158](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/backends/cypher_graph_base.py#L158), [server.py:1682](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L1682), [server.py:1952](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L1952). **Статус:** AST/complexity scan, ручная сверка.

`spreading_activation` имеет одинаковый нормализованный AST в трёх backend. Подготовка чата/памяти/LLM дублируется в `chat_endpoint` и `_chat_prepare`, хотя docstring второго говорит об общей подготовке обоих маршрутов. Это увеличивает вероятность повторного drift при исправлении policy/context ошибок.

Наиболее сложные функции по Radon: `_reconcile_group` — CC 57 ([core/continuity/state_reconciler.py:527](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/continuity/state_reconciler.py#L527)), `_store_fact_outcome` — CC 55 и 473 строки ([core/memory.py:1638](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L1638)), `create` — CC 55 ([core/continuity/source_admission_decisions.py:769](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/continuity/source_admission_decisions.py#L769)), `store_facts_batch` — CC 50 ([core/memory.py:4208](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/memory.py#L4208)), `/query` — CC 49 ([server.py:2412](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L2412)).

**Предложено:** сначала characterization/differential tests вокруг транзакционных и policy-границ, затем выделение чистых validation/serialization шагов и общего traversal. Не дробить transaction owner и не вводить второго владельца Canon ради снижения метрики.

### A25 — Публичные backend API не документируют поведение, от которого зависит сохранность

**Где:** [core/graph_store.py:35](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_store.py#L35), [core/graph_store.py:39](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_store.py#L39), [core/graph_store.py:51](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/graph_store.py#L51), [core/tool_handlers.py:37](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/tool_handlers.py#L37). **Статус:** документационный пробел.

Абстрактные методы описывают форму, но не объясняют merge/replace props, направление и роль веса ребра, ownership соединения, поведение для отсутствующего узла, thread-safety и исключения. A06 показывает реальное расхождение реализаций, которое такой контракт не предотвращает. Ряд экспортированных tool handlers имеет только голые dict-аннотации без формата результата и ошибок.

AST-счётчик нашёл 1511 из 2553 не-private function/method definitions без собственного docstring в основном Python-коде. Это индикатор, а не 1511 отдельных дефектов: часть функций документируется на уровне класса/маршрута или является внутренней реализацией.

**Предложено:** документировать поддерживаемые публичные API и outcome/error semantics, ввести typed DTO/Protocol на межмодульных границах и исполняемые contract examples. Не добавлять формальные однофразовые docstrings ради счётчика.

### A26 — Устаревший Ruff нельзя обновить обычным refresh lock

**Где:** [pyproject.toml:99](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/pyproject.toml#L99), [uv.lock:2210](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/uv.lock#L2210). **Статус:** lock/constraint и публичные PyPI-метаданные проверены.

В проекте Ruff 0.4.10, ограничение `>=0.4,<0.5` запрещает переход на современные версии. На дату аудита PyPI публикует Ruff 0.17.5 (12 ноября 2026). Этот finding относится к устаревшему dev-инструменту, а не к подтверждённой уязвимости runtime. OSV-проверка замороженного графа чистая.

**Предложено:** отдельное контролируемое обновление Ruff/конфига без массового автоисправления бизнес-кода; после обновления повторить semantic F-checks. Не считать нижние bounds вроде `fastapi>=0.110` доказательством установленной старой версии: реальный runtime зафиксирован lockfile.

### A27 — Условный лицензионный риск опционального PDF backend

**Где:** [LICENSE:1](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/LICENSE#L1), [core/file_parsers/pdf_parser.py:35](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/pdf_parser.py#L35), [core/file_parsers/pdf_parser.py:172](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/pdf_parser.py#L172), [core/file_parsers/pdf_parser.py:299](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/file_parsers/pdf_parser.py#L299), [scripts/generate_sbom.py:113](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/scripts/generate_sbom.py#L113). **Статус:** риск интеграции/учёта, не доказанное нарушение лицензии.

Репозиторий MIT; PDF parser автоматически использует установленный `fitz` и рекомендует `pip install pymupdf`. Публичная metadata PyMuPDF указывает **AGPL-3.0 либо Artifex Commercial License**. PyMuPDF не входит в проверенный lockfile/default image, поэтому нельзя автоматически объявить стандартную сборку нарушающей лицензию. Но ручная установка рекомендованного backend меняет лицензионный состав и обходит воспроизводимый dependency graph. Аналогично ряд опциональных parser/generator integrations подключается по наличию модуля.

Генератор lock-SBOM включает имена, версии, hashes/properties, но не `licenses`; отсутствие этого поля само по себе допустимо для SBOM, однако такой артефакт не доказывает совместимость лицензий.

**Предложено:** инвентаризация всех optional backends с SPDX/источником/условиями распространения, явные поддерживаемые extras и notices, проверка выбранного release-профиля. Для PyMuPDF — осознанный выбор лицензии или использование уже зафиксированного pypdf.

### A28 — Комментарии и документация API сообщают устаревшее поведение

**Где:** [api/llm_routes.py:208](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/llm_routes.py#L208), [api/web_console.py:414](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/api/web_console.py#L414), [server.py:677](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/server.py#L677), [docs/ai/KNOWN_RISKS.md:3](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docs/ai/KNOWN_RISKS.md#L3), [docs/ai/WORK_LOG.md:3](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docs/ai/WORK_LOG.md#L3). **Статус:** подтверждено сравнением с executable-кодом и merge commit.

Docstring `/llm/test` утверждает «без X-Api-Key», хотя route находится в защищённом router. Bootstrap docstring утверждает выдачу серверного ключа на localhost, тогда как безопасная реализация всегда оставляет его None. OpenAPI description всё ещё содержит `Graph = Truth`, от которого актуальные архитектурные документы явно отказались. Верхние записи evidence-labels называют PR draft/not merged, хотя проверенный head — merge #515.

**Предложено:** согласовать публичный API/help и текущие status headers с этим commit; исторические записи сохранять с явной датой и историческим статусом. Документационные противоречия не являются доказательством, что auth отсутствует или ключ действительно выдаётся.

## Покрытие, безопасность и границы исходного прогона

Измерение сделано на основном прогоне, **до audit probes**; пробы не раздувают проценты. Это statement coverage без branch tracing.

| Поверхность | Покрыто / statements | Покрытие |
|---|---:|---:|
| `core/` | 41 444 / 52 814 | 78,47% |
| `server.py` | 1493 / 2038 | 73,26% |
| `api/` | 494 / 768 | 64,32% |
| `app/` | 54 / 121 | 44,63% |
| `core/hybrid_retriever.py` | 200 / 342 | 58,48% |
| `core/embedding_store.py` | 91 / 187 | 48,66% |
| `core/file_parsers/archive_parser.py` | 89 / 187 | 47,59% |
| `core/graph_lab_bridge.py` | 21 / 57 | 36,84% |
| `core/velantrim_reports/mhi_report.py` | 4 / 25 | 16,00% |
| `core/velantrim_reports/truthgate_report.py` | 4 / 52 | 7,69% |

Текущий порог core ≥74% действительно blocking в CI; утверждать, что coverage gate отсутствует, было бы неверно. Однако средний процент скрывает непроверенные producer→consumer контракты и не охватывает внешние относительно core пути. Итог полного прогона с 5 падениями не объявляется успешным только потому, что измеренный core процент выше порога.

Упавшие тесты:

1. `tests/test_embedding_projection.py::test_pipeline_still_reaches_truth_gate_regardless_of_projection_state`.
2. `tests/test_pipeline.py::test_pipeline_step6_modality_flag_on`.
3. `tests/test_pipeline.py::test_query_causal_hints_are_proposals_not_relation_writes`.
4. `tests/test_retrieval_d3.py::test_d3_ngram_candidate_used_directly_beyond_cap`.
5. `tests/test_retrieval_d3.py::test_d3_empty_ngram_falls_back_bounded`.

Первый тест сообщает bypass-count из-за того, что пустой retrieval не дошёл до gate; это **не доказательство допуска неверифицированного факта**. Причина в данном воспроизведении — A01; контроль без `rank-bm25` дал 5/5.

## Безопасность, ошибки и известные ограничения

### Секреты и инъекции

- Распознанные по формату GitHub/LLM-токены в `tests/test_selective_memory_candidates.py:241`, `tests/test_llm_context_no_silent_truncation.py:42`, `benchmarks/bench_selective_memory_candidates.py:54,87` — синтетические данные. Значения в отчёт не копируются.
- `.env`-examples и dev-конфиги содержат placeholders/публичные dev-credentials. Их сетевой риск описан в A02; доказательств утечки реального production-токена в проверенном head нет.
- В просмотренных SQL-потоках значения передаются параметрами. Основные B608 относятся к placeholders, константным/контролируемым именам таблиц и внутренним fragments. Подтверждённого attacker-controlled SQL identifier не найдено. Полный список эвристик сохранён отдельно; чистый Ruff не заменяет эту проверку.
- В проверенных subprocess-потоках file parsers используются списки аргументов, без `shell=True`. Archive ZIP/TAR extraction проверяет границы destination и фактическое число распакованных bytes; symlink TAR members не распаковываются как обычные файлы. Ошибки общих recursion/resource budgets остаются описанными выше.
- Основной console Markdown renderer экранирует HTML и ограничивает схемы ссылок. Воспроизводимая XSS-цепочка не подтверждена. Хранение ключей в browser localStorage увеличивает последствия будущей same-origin XSS; это не объявлено самостоятельной доказанной инъекцией.
- Prompt injection из документов/модели остаётся моделью угроз, а не решённой гарантией. Наличие sanitize/нейтральных labels не доказывает поддержку каждого утверждения источником.

### Существенные уже известные границы

| Граница | Проверенная точка | Остаточный риск |
|---|---|---|
| Доказательства TruthGate | [core/truth_gate.py:244](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/truth_gate.py#L244), [docs/ai/KNOWN_RISKS.md:153](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docs/ai/KNOWN_RISKS.md#L153) | Считаются уникальные непустые string refs; источник, независимость и содержательная поддержка не верифицируются этим счётчиком. Это явно известное ограничение, не закрыто typed reference prototype |
| PII | [docs/ai/KNOWN_RISKS.md:242](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docs/ai/KNOWN_RISKS.md#L242) | Redaction claim не означает физическое стирание произвольной metadata/raw/backups/внешних копий |
| Архивирование | [docs/ai/KNOWN_RISKS.md:253](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docs/ai/KNOWN_RISKS.md#L253) | Файловая система и SQLite не образуют общей ACID-транзакции; возможен orphan payload при неуспешном cleanup |
| MCP сериализация | [core/mcp_transport.py:242](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/core/mcp_transport.py#L242) | Блокировки process-local; multi-worker сериализация этим механизмом не обеспечивается |
| Production readiness | [docs/ai/KNOWN_RISKS.md:489](https://github.com/velantrian/Velantrim-ExoCortex-Titan/blob/485c4b0906ec35829ff7231c6276bf7d817f096f/docs/ai/KNOWN_RISKS.md#L489) | Реальные многопроцессные нагрузки, hot backup/DR и operational evidence не следуют из локального теста |

### Что нельзя заключить по этому аудиту

История Git не просканирована: checkout shallow на один commit. Удалённые/отозванные секреты в старых commit остаются вне проверки. Не выполнялись живые LLM/STT/TTS/Telegram вызовы, загрузка нейромоделей, тесты Neo4j/Redis, сборка контейнера, penetration test или нагрузочное испытание production. 63-МБ `kb_graph.json` проверен как часть secret scan, но истинность и лицензия каждого содержащегося утверждения не верифицированы. Отсутствие найденного секрета/инъекции не является доказательством их отсутствия во всех возможных конфигурациях.

## Рекомендуемый порядок исправления

1. A01: восстановить lexical retrieval без dense и закрепить матрицу fallback-режимов. A02: loopback-default dev Compose. A03/A04: достоверное подтверждение и идемпотентность Telegram.
2. A05/A06/A12/A13/A14/A17: минимальные исправления межмодульных контрактов с реальными producer→consumer тестами.
3. A07–A11/A15/A18/A19: доставка событий, shutdown, concurrency, commit-result и ограничения памяти/числа задач.
4. A16/A20: исполнимые бюджеты и проверки отказов на HTTP/ingest границах; сохранить существующие transaction/policy owners.
5. A21–A28: конвергенция morphology, явная судьба legacy API, удаление подтверждённого dead code, документация, лицензии и контролируемое обновление Ruff. Широкий рефакторинг выполнять после contract tests.

## Воспроизводимость и артефакты

Локальные доказательства находятся в `/workspace/audit-evidence/`:

| Файл | Содержимое |
|---|---|
| [pytest-verified.log](audit-evidence/pytest-verified.log) | Законченный полный прогон, точные падения и итог |
| [pytest-failures-focused.log](audit-evidence/pytest-failures-focused.log) | Пять повторных падений в свежем процессе |
| [pytest-failures-naive-control.log](audit-evidence/pytest-failures-naive-control.log) | Дифференциальный контроль 5 passed |
| [coverage.json](audit-evidence/coverage.json) | Statement coverage основного прогона |
| [reproduce.py](audit-evidence/reproduce.py), [probes.json](audit-evidence/probes.json) | Offline воспроизведения и результаты; fault injection обозначен в коде |
| [dependency-audit.json](audit-evidence/dependency-audit.json) | OSV-ответ: 121 пакет, 0 vulnerabilities/adverse statuses |
| [pypi-metadata.json](audit-evidence/pypi-metadata.json) | Проверенные версии/лицензии Ruff и PyMuPDF |
| [bandit.json](audit-evidence/bandit.json), [vulture.txt](audit-evidence/vulture.txt), [complexity.json](audit-evidence/complexity.json) | Неотфильтрованные результаты статических инструментов |
| [inventory.json](audit-evidence/inventory.json), [exact-duplicates.json](audit-evidence/exact-duplicates.json), [private-unused-candidates.json](audit-evidence/private-unused-candidates.json) | Инвентаризация, AST-дубликаты и кандидаты без callers |
| [ruff-core.json](audit-evidence/ruff-core.json), [mypy-core.txt](audit-evidence/mypy-core.txt), [mypy-surfaces.txt](audit-evidence/mypy-surfaces.txt) | Точные результаты lint/type проверки |
| [secret-locations-redacted.json](audit-evidence/secret-locations-redacted.json) | Только пути/строки совпадений, без значений токенов |

Команда основного прогона из checkout (имена временных БД можно заменить):

```bash
VELANTRIM_DB_PATH=/tmp/titan-audit-main3.db \
VELANTRIM_NGRAM_DB=/tmp/titan-audit-ngram3.db \
VELANTRIM_API_KEY=audit-local-test-key \
COVERAGE_FILE=/workspace/audit-evidence/.coverage \
.venv/bin/python -m coverage run --source=core,api,server,app,localmind,utils \
  -m pytest tests/ -q -o addopts='' --tb=short --timeout=90 \
  -k 'not test_concurrent_fresh_bootstrap_add_column_no_duplicate_error and not test_concurrent_fresh_bootstrap_on_seeded_db_creates_exactly_one_view'
```

Offline-пробы:

```bash
PYTHONPATH=/workspace/Velantrim-ExoCortex-Titan \
  .venv/bin/python /workspace/audit-evidence/reproduce.py
```

Никакие предложенные исправления не применены. Публичные GitHub/Notion records не изменялись: результат этого задания — локальный Markdown-отчёт.

## Доказательства дополнения и комплект для независимой проверки

| Артефакт | Что содержит |
|---|---|
| [verify_additional.py](audit-addendum-evidence/verify_additional.py) | 13 групп воспроизводимых probes; temporary DB, fakes, fault controls |
| [probes.json](audit-addendum-evidence/probes.json) | Числа, verdicts и boolean leak-проверки |
| [probes.log](audit-addendum-evidence/probes.log) | Полный лог заключительного запуска; только синтетический marker |
| [pytest-focused.log](audit-addendum-evidence/pytest-focused.log) | 59 passed существующих целевых tests |
| [github-state.json](audit-addendum-evidence/github-state.json) | Read-only проверка Issue/PR статусов |
| [manifest.json](audit-addendum-evidence/manifest.json) | SHA, checksums, состав и результаты |

Команда probes из checkout:

```bash
PYTHONPATH=/workspace/Velantrim-ExoCortex-Titan \
  .venv/bin/python /workspace/audit-addendum-evidence/verify_additional.py
```

Для asyncio/threaded HTTP-проверок требуется окружение, разрешающее локальные Unix sockets; в данной песочнице ограничения self-pipe мешали `asyncio.to_thread`. Завершённый запуск выполнен с подходящими разрешениями, без изменений приложения для обхода зависания. Новых зависимостей и внешних моделей в дополнении не устанавливалось.

В ZIP-комплект включены этот объединённый отчёт, исходный отчёт, приложенный Manus-файл, старые/новые журналы и scripts. Репозиторий, venv и временные DB в архив не включены. Значения действующих секретов не собирались. Все рекомендации остаются неприменёнными; `git status --porcelain` чист.
