# Velantrim ExoCortex Titan — реестр исправлений аудита

Дата: 17 ноября 2026. Исходный `main`: `485c4b0906ec35829ff7231c6276bf7d817f096f`.

Исправления подготовлены в отдельных ветках и draft PR. Слияний в `main`, включения
экспериментальных возможностей и развёртывания не выполнялось. «Исправлено в PR» означает
проверенное предложение кода, а не устранение дефекта в основной ветке.

## Новые PR и порядок рассмотрения

| PR | Содержание | Зависимость |
|---|---|---|
| [#523](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/523) | Admission, BM25, обязательная FactsPack policy, confidence, promotion mode | main |
| [#524](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/524) | MCP: потоковые лимиты, thread pool, TTL/LRU, освобождение mutex | main |
| [#525](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/525) | Сохранность данных, lifecycle, интерфейсы, scope, bounded retrieval | #523 |
| [#526](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/526) | Frozen Stage 9/10, современный Ruff, HTTP typing, fallback CI, лицензии | #523 |
| [#527](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/527) | Retrieval scores, Dense model cache, Gemini TTL/recovery | #523 |
| [#528](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/528) | Telegram: durable receipt, atomic first writer, идемпотентность | #523 |
| [#529](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/529) | Подтверждённый private dead code, одинаковые алгоритмы, API/help | #525 |

Приоритет: #523, #514, #528 и #509; затем #524/#525 и оставшиеся дочерние исправления.
Observer рассматривается последовательно: **#509 → #521 → #522**. Каждый родитель должен
пройти собственные проверки. После будущего разрешённого слияния родителя потребуется
переназначить base дочерних PR и проверить итоговый diff относительно нового main.

## Реестр 42 находок

Местоположения и воспроизведения исходного состояния приведены в
[исходном объединённом аудите](2026-11-16-code-audit.md). Ссылки на строки в нём относятся
к исходному SHA; после исправлений номера строк меняются.

| ID | Уровень | Результат исправления | PR / остаток |
|---|---|---|---|
| A01 | High | Совпавшие BM25-документы не теряются при score ≤ 0; nonmatch не вытесняет отрицательный match | #523 |
| A02 | High | Dev Compose слушает loopback; публичный dev-key не публикуется по сети по умолчанию | #525; для production нужен отдельный профиль/ключ |
| A03 | High | Telegram не подтверждает отклонённую или неподтверждённую canonical-запись | #528 |
| A04 | Medium | Стабильный delivery ID, атомарный first writer, нет дублей facts/raw/events при retry; conflicting edit отклоняется | #528 |
| A05 | Medium | CORS разрешает PATCH и Idempotency-Key | #525 |
| A06 | Medium | SQLite/Cypher edge upsert не стирает label/props существующих узлов | #525 |
| A07 | Medium | У EventBus есть один lifecycle consumer; без него dispatch=False доставляет inline; сбои видны | #525; volatile/process-local, не durable exactly-once |
| A08 | Medium | Worker start идемпотентен; episode tasks ограничены; stop отменяет и ожидает все owned tasks | #525 |
| A09 | Medium | CoreMemoryBlocks читает committed snapshots вместо конкурирующего кеша | #525 |
| A10 | Medium | Глубина архивов хранится в ContextVar, общий registry не подменяется | #525 |
| A11 | Medium | Полный извлечённый child text и предупреждения доходят до enclosing archive | #525; действуют прежние ограничения распаковки/глубины |
| A12 | Medium | MHI consumer использует реальные mhi/freshness_score/validated_facts | #525 |
| A13 | Medium | GraphLab получает owned read-only connection, правильные поля и max_cycle_len | #525; domain bridge filter явно NOT_SUPPORTED, не реализован |
| A14 | Medium | DI constructor/setter и causal factory используют выбранный store; owned connection закрывается | #525; injected stores принадлежат caller |
| A15 | Medium | SQLite connections закрываются при ошибках; failed commit возвращает 0 durable batch progress | #525 |
| A16 | Medium | SQL seed/row/node budgets, ограниченный cycle DFS, API bounds и budget-exhausted status | #525; bounded empty result не доказывает отсутствие пути/цикла |
| A17 | Medium | Role domain/mode проходят через policy owner; неизвестные explicit значения отклоняются, effective params нормализованы | #525 |
| A18 | Medium | Sync MCP tool исполняется в существующем bounded thread pool и не блокирует HTTP event loop | #524 |
| A19 | Medium | Session TTL/LRU и удаление idle mutex после последнего holder/waiter | #524; межпроцессная координация не добавлена |
| A20 | Medium | Расширены Ruff/mypy, добавлен frozen fallback CI без BM25/dense и негативные регрессии | #526; полное condition coverage не заявляется |
| A21 | Low | Morphology dependency согласована с pymorphy3 | #525 |
| A22 | Low | Facade возвращает существующие Observer callable и notebook выбранной сессии | #525 |
| A23 | Low | Удалены private SSE parser/Prometheus probe, unused private arg; MinerU не читает файл впустую, Vision/MinerU явно unfinished | #527/#529; public compatibility APIs сохранены и документированы |
| A24 | Low | Три AST-идентичных graph traversal объединены без изменения алгоритма; RRF лишняя нормализация убрана | #529/#527; большие transaction/orchestration методы требуют отдельной декомпозиции |
| A25 | Low | Описаны node/edge/traversal semantics и реальные границы публичных/резервных API | #525/#529 |
| A26 | Low | Ruff 0.4.10 заменён на locked 0.17.5; semantic F-проверки сохранены | #526 |
| A27 | Low | Добавлен inventory реальных установленных license metadata, unknown помечен; описаны PyMuPDF AGPL/commercial условия | #526; юридическая совместимость всех extras/models не заверена |
| A28 | Low | Уточнены protected LLM test, bootstrap, Graph-as-projection, Docker/API docs и исторический статус #515 | #525/#529 |
| C01 | High | Безопасные LLM error codes/event IDs вместо текста исключения, redaction regressions | существующий #514, конфликт с #515 устранён |
| C02 | High | Дедупликация только тождественных записей, а не словесно похожих утверждений | существующий #509 |
| C03 | Medium | Lexical overlap больше не представлен как semantic support; проверка ограничена фактически отправленными records | #521/#522; смысловая поддержка остаётся UNVERIFIED, verifier не реализован |
| C04 | Medium | Неисполненная проверка Observer даёт check_unavailable, а не clean | #509, согласовано с #521/#522 |
| C05 | High | Удалён confidence boost за повторение/лексическое сходство перед promotion | #523; независимая corroboration не выдумывается |
| C06 | High | Основной query требует FactsPack policy; отказ даёт bounded insufficiency | #523 |
| C07 | High | Оба типа определяются до gate; classifier failure/invalid explicit types отклоняются в single и batch writes | #523 |
| C08 | Medium | MCP считает реальные streamed bytes, ограничивает batch/depth до dispatch; malformed JSON/UTF-8 возвращает 400 | #524; превышение — 413 |
| C09 | Medium | Неизвестный explicit promotion mode отклоняется до чтения/изменения факта | #523 |
| C10 | Medium | Stage 9/10 используют frozen lock, Playwright locked; изменение lock/installer запускает acceptance | #526 |
| C11 | Medium | Five-stage final_score согласован с ranking; graph candidates имеют реальную rank eligibility | #527 |
| C12 | Medium | Branch и реально подключённый multilingual path используют bounded candidate/policy owner, сохраняют domain и показывают деградацию | #525 |
| C13 | Medium | Dense availability — на instance; модель создаётся под общей блокировкой; vector cache locking сохранён | #527 |
| C14 | Medium | Gemini handle TTL/LRU и одна uncached retry при missing handle; полный system сохранён | #527; retry ограничен 404, provider quotas/single-flight отдельно |

## Проверки и отрицательные контроли

Финальный локальный code snapshot: `9270d78675d9d85502dea489776c53702732eca6`;
последующие изменения этой проверочной ветки касаются отчётной документации.
Полный прогон использовал `pytest tests/ -q -o addopts= --tb=short --timeout=90
--cov=core --cov-report=term --cov-report=json --cov-fail-under=74`.
Явный `addopts=` исключает скрытую deselection; skipped/xfail указаны отдельно.

| Набор | Результат |
|---|---|
| Core integrity: полный suite на code a4c03a2 | 4969 passed, 17 skipped, 1 xfailed; core coverage 78.49%, threshold 74% |
| Те же новые регрессии на неизменённом исходном SHA | 25 failed, 3 passed: тесты обнаруживают исходные дефекты, контрольные сценарии сохраняются |
| MCP | 71 passed, включая настоящий Uvicorn/chunked, no-dispatch, event-loop responsiveness, TTL/LRU и idempotency |
| Runtime code 2282007 | 4988 passed, 17 skipped, 1 xfailed; чистый mypy core; remote exact-code lint/test/coverage passed |
| Telegram | Полный suite 4976 passed, 17 skipped, 1 xfailed; финальные receipt/provenance/event проверки 54 passed |
| Retrieval/LLM | 45 focused и 210 broader affected tests passed |
| Fallback environment без rank_bm25/sentence_transformers | 194 passed; дополнительные API/callback/projection checks 79 passed |
| Cleanup | 83 passed; AST identity проверена до извлечения общих функций |
| Совместные repaired-path + import-order проверки | 452 passed; Ruff полного runtime/HTTP/scripts surface и clean mypy core (357) / HTTP (12) прошли |
| Объединённый кандидат, source 9270d78675d9d85502dea489776c53702732eca6 | **5132 passed, 17 skipped, 1 xfailed**, 13 warnings, 532.24 s; core coverage **79.30% ≥ 74%** |

Это разные наборы/версии, их числа **не суммируются**. Прогоны выполнены локально на
Python 3.12; hosted CI использует свой профиль, включая Python 3.11 и дополнительные
зависимости. Skips/xfail не превращены в успешные проверки. Реальные LLM/Telegram вызовы
для этой работы не выполнялись.

## Существовавшие открытые PR

| PR | Выполненное действие / следующий шаг |
|---|---|
| #500 | Устранён конфликт с main, сохранены missing-partner и partial-ESM guards; 40 native tests passed; добавлена обязательная doc metadata. Не merged |
| #506 | Обновлён base snapshot, проверен immutable CodeQL release commit; обновлён exact-pin policy test и doc metadata. Свежие lint/test/coverage/CodeQL и aggregate gate прошли |
| #509 | Устранены конфликты с #515; 97 focused tests; исправлена изоляция после reload core modules; родитель Observer stack |
| #514 | Сохранены safe errors вместе с merged evidence labels/lifecycle; 113 focused tests; конфликт устранён |
| #517 | Устранён конфликт документации, proposal и отсутствие activation сохранены; это не архитектурное одобрение |
| #521 | Согласован с #509, переназначен base на его ветку; 60 focused и 379 import-order checks; parent independently green перед #522 |
| #522 | Синхронизирован с #521; 106 focused / 450 order checks; optional answer guard исправлен в owning child; свежие lint/test/coverage прошли, Draft gate ожидается |
| #520 | Отдельное обновление runtime dependency group: рассматривать после audit fixes, согласовать lock с #526 и повторить dependency/acceptance checks. Автоматически не влито |
| #518 | Opt-in evidence labels для chat: отдельное расширение, не semantic verifier. Не активировано; согласовать финальный server diff после #514/#522/#525/#526 |
| #508 | Документальное раскрытие hackathon: не исправление runtime. Сохранён draft; содержание не одобрялось этим аудитом |
| #503 | Grant draft: не исправление кода. Публичная doc-sync/merge metadata требует отдельного завершения; автоматически не опубликован/не влит |
| #473 | Frozen Reader harness остаётся draft, конфликтующим предложением NOT_RUN. Не подменяет проверенный runtime и не включён в audit repair candidate; отдельный review/refresh |

Наличие зелёных компонентных workflow не делает draft готовым к merge автоматически.
Агрегатный gate может ожидать снятия Draft, parent lifecycle и синхронизации документации.
Старые упавшие/отменённые evaluator runs отличайте от актуального exact-head результата.

## Оставшиеся границы

1. Семантический verifier не создан: unknown не превращается в supported.
2. Domain-specific GraphLab bridge analysis явно отклоняется как unsupported.
3. Межпроцессное exactly-once для MCP и durable EventBus delivery не добавлены; это
   отдельные operational contracts, а не следствие process-local блокировок.
4. Large-function refactoring не смешан с срочными canonical/security исправлениями.
5. Для фактического deployment нужны inventory выбранных extras/models и проверка их
   лицензий; MIT проекта и vulnerability audit этого не заменяют.
6. Уже сохранённые/продвинутые факты автоматически не переписывались и не удалялись.

MCP envelope budgets настраиваются. Они ограничивают HTTP body/batch/depth, **не размер
документов Reader**. Это не основание добавлять произвольное усечение прочитанного текста.

## Объединённый проверочный кандидат

Ветка `audit/integration-verification-20261117` объединяет перечисленные исправления и
согласованные #500/#506/#509/#514/#517/#521/#522 только для проверки совместимости.
Проверочный [PR #530](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/530) — отдельный draft-кандидат **DO NOT MERGE**: исправления предлагается принимать через
их owning PR, а не обходить review всего стека. Main остаётся неизменённым.

Первый совместный прогон: 5128 passed, 4 failed, 17 skipped, 1 xfailed. Он обнаружил
старый CodeQL pin fixture (#506), два dimension fixtures с удалённым class flag (#527)
и TTS mock/egress isolation (#526). Исправления перенесены в эти owning PR. Отдельно
None guard для нового HTTP type profile внесён в owning #522. После синхронизации
452 проверки repaired-path/import-order и все static gates прошли. Финальный полный
повтор: **5132 passed, 17 skipped, 1 xfailed**, core coverage **79.30%**. Branding,
repo hygiene, architecture freeze, project-state и KB graph guards также прошли.
Удалённая main повторно проверена через git ls-remote: исходный SHA не изменён.

Hosted workflows проверяют собственные exact-head snapshots; актуальные результаты
доступны в [checks PR #530](https://github.com/velantrian/Velantrim-ExoCortex-Titan/pull/530/checks).
Draft aggregate gate остаётся ожидающим по правилам репозитория и не снимается ради
зелёного индикатора. Тестовый результат исходного code snapshot не переносится на
будущие изменения runtime.
