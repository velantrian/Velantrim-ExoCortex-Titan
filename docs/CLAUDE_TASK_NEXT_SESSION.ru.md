# 🧭 ТЗ для Claude — следующая сессия (architecture/correctness)

> **Репозиторий (канон, под git):** `C:\Users\VELAN\Documents\Research Velantrim\VELANTRIM_ExoCortex_V8.6`
> **Запуск новой сессии:** «Прочитай docs/CLAUDE_TASK_NEXT_SESSION.ru.md и начни с приоритета 1»
> (или назови нужный приоритет). Этот файл — чтобы НЕ переаудитить всё заново и сэкономить токены.

## 0. Что это и где контекст (прочитай эти файлы — и хватит)
Velantrim V8.6 — оффлайн-память для AI с дисциплиной истины. Чтобы войти в курс дёшево, прочитай ТОЛЬКО:
1. `CANONICAL.md` — какая копия канон.
2. `docs/TRUTH_AND_RINGZERO_CANON.ru.md` — единый закон (движок истины + Ring Zero). Главный документ.
3. `docs/MIGRATION_V8.6_TO_CANON.ru.md` — план C1–C12 (что мигрировать).
4. `docs/DEDUP_AND_SCALE_1M.ru.md` — дизайн масштаба (D1–D6, статус ниже).
5. Память сессии: `~/.claude/projects/.../memory/` (velantrim-deep-audit-findings, core3-etalon, product-vision).
Не читай весь `server.py`/`core/` подряд — дорого. Используй Grep/Explore точечно.

## 1. Что УЖЕ сделано (НЕ переделывать)
- ✅ Глубокий аудит (memory: velantrim-deep-audit-findings) — критичные C1/C2/M1–M5/H2 идентифицированы.
- ✅ Канон истины + Ring Zero, план миграции, дизайн дедупа — в `docs/`.
- ✅ Мост Core-3: `core/core3_adapter.py` + `velantrim/verify.py` (в `velantrim_core-3/`), тесты зелёные.
- ✅ **D1** индекс `claim_dedup_key` (фикс M5), **D2** стабильный ORDER BY, **D3** retrieval FTS5 напрямую,
  **D4** детерминированный семантический дедуп + RU-калибровка (порог 0.90, многоязычная модель, guard),
  **D5** trust-aware резолвер противоречий + contradiction-before-promotion (фикс M4/H2). Все с тестами.
- ✅ Профиль `config/profiles/cognitive.env` включает органы (дедуп/резолвер/sleep) с калиброванными настройками.
- ✅ Сбор базы знаний (`docs/knowledge/world_skills_core/`) **делегирован ChatGPT Codex** —
  см. `docs/CODEX_TASK_KNOWLEDGE_COLLECTION.ru.md`. ⛔ ЭТУ ПАПКУ НЕ ТРОГАЙ (зона Codex).

## 2. Что делать (приоритеты — бери сверху)

### 🔴 Приоритет 1 — Безопасность (P0, реальные открытые дыры из аудита)
- `api/llm_routes.py`: **20 роутов БЕЗ авторизации** (нет `require_api_key`) — оракул проверки чужих
  ключей + жжёт квоты. Фикс: `app.include_router(router, dependencies=[Depends(require_api_key)])`.
- `api/web_console.py:~412` `/console/bootstrap`: **отдаёт настоящий `VELANTRIM_API_KEY`** при «локальности»
  по `request.client.host` — за reverse-proxy при `--host 0.0.0.0` утекает всем. Фикс: не отдавать ключ по HTTP.
- (доп.) `web_console.py:~67` auth-оракул `key == expected` не constant-time → `hmac.compare_digest`.
- Добавить тесты (роуты требуют 401 без ключа; bootstrap не отдаёт ключ). Модель: **Opus 4.8 · high**.

### 🧠 Приоритет 2 — Фаза 1: единая truth_policy в V8.6 (C1–C4)
Сейчас в V8.6 read-путь отвечает по голому confidence (см. аудит). Портировать из Core-3:
единый `core/truth_policy.py` (запись И чтение), структурный `EvidenceRef`, вердикт
`allow|gap_notice|reject` в `/query` (`server.py`) + `core/pipeline.py`/`core/trace.py`/`core/facts_pack.py`.
Это ядро «точности оффлайн». Карта правок — в `docs/MIGRATION_V8.6_TO_CANON.ru.md` (T1.1–T1.6). Модель: **Opus 4.8 · high**.

### 🔌 Приоритет 3 — MCP-сервер (вернуть из эталона v8_17_9)
Эталон `velantrim_v8_17_9/velantrim_v8_8/mcp_server.py` (FastMCP, 12 тулов) утрачен в V8.6.
Написать `mcp_server.py` поверх существующих сервисов V8.6 (store/search/transition/relations/audit/
consolidate как FastMCP-тулы) → интеграция с Claude Desktop/Cursor/IDE. Модель: **Opus 4.8 · high**.

### ✅ Чекпойнт — полный pytest
До/после крупных правок: `.\scripts\run_tests.ps1` (или `.venv\Scripts\python.exe -m pytest`, ~20 мин).
Базлайн: 760+ passed; покрытие ~58% (порог 80 не достигнут — известно). Модель: **Sonnet 4.6 · medium**.

## 3. Конвенции
- Канон под git: работай на ветке (не в `master`), коммить осмысленно, в конце
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- Среда: Windows, Python в `.venv\Scripts\python.exe`. Тесты: `-o addopts=""` чтобы снять порог покрытия.
- Правило пользователя: **в конце каждого ответа** — рекомендация модели Claude + режим мышления
  (Sonnet 4.6 для исполнения; Opus 4.8 + high для тонкой корректности). И эмодзи по смыслу.
- ⛔ Не трогай `docs/knowledge/world_skills_core/` (Codex) и `data/*.db`.

## 4. Статус масштаба
`D1 ✅ D2 ✅ D3 ✅ D4 ✅ D5 ✅ D6 ⬜ (int8/HNSW — только при >100K фактов, сейчас преждевременно)`
База знаний: ~6 700 / 50 000 (ведёт Codex).
