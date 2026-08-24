# 🧪 Titan V1 — Bounded Pilot

Этот пилот — ограниченная проверка готового V1-сценария, а не production-авторизация.

## Что проверяется

Пилот запускает один изолированный локальный Titan и последовательно проверяет:

1. **Startup / health** — локальный сервер поднимается с API-key и fail-closed network policy.
2. **Validated memory → useful answer** — факт проходит существующий ESM + TruthGate путь и затем реально используется локальным `/chat` без LLM.
3. **File ingestion** — обычный локальный `.txt` проходит существующий `FileIngester` и canonical `/ingest/text` API.
4. **Tools** — MCP reader surface реально доступна и содержит существующий `search_facts`.
5. **Restart continuity** — сервер останавливается, поднимается снова на тех же SQLite paths, validated memory остаётся доступной и снова даёт полезный ответ.

Stage 9 уже отдельно доказал настоящий браузерный путь Chromium → Console → `/chat/stream` → Validated memory → DOM reply. Stage 10 не скачивает Chromium повторно, а использует этот факт как prerequisite и проверяет остальные продуктовые поверхности одной ограниченной пилотной матрицей.

## Запуск

```bash
python scripts/titan_v1_bounded_pilot.py
```

Успешный финал содержит:

```text
STAGE10_BOUNDED_PILOT=PASS
```

и JSON со всеми сценариями `PASS`.

## Безопасные границы

Пилот намеренно:

- использует только loopback;
- требует локальный API-key;
- оставляет `VELANTRIM_NETWORK_MODE=deny`;
- оставляет `VELANTRIM_REMOTE_DATA_MODE=never`;
- не требует внешнего LLM;
- ограничивает MCP до `reader`;
- использует временные SQLite-файлы;
- не пишет remote Canon;
- не включает автономный runtime;
- не меняет authority boundaries.

## Что PASS не означает

`STAGE10_BOUNDED_PILOT=PASS` **не означает**:

- production authorization;
- Operator GO;
- разрешение remote Canon;
- HA / disaster recovery;
- неограниченную автономность;
- доказательство всех research-возможностей Titan.

Пилот отвечает только на V1-вопрос: может ли ограниченный local-first продукт пройти ключевой пользовательский цикл на текущем коде без знания внутренней архитектуры.
