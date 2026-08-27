# 🗿 Velantrim Titan V1 — Closure Record

Дата: 2026-08-22

Статус этого документа: **closure candidate** до merge соответствующего Stage 11 PR. Если этот документ присутствует в `main` после успешных exact-head CI / CodeQL / aggregate gates, Stage 11 считается закрытым и статус продукта становится **TITAN V1 — DONE**.

## 🎯 Что именно считается завершённым

Завершён bounded Titan V1 как ordinary-user local-first продуктовый путь: человек может установить Titan, выполнить первый запуск, настроить провайдера при необходимости, работать через Console, использовать локальную память, файлы и существующие tools, остановить и запустить систему снова, восстановиться после типовых ошибок и безопасно обновить Git-checkout без понимания внутренней архитектуры.

Это **не** production authorization и не разрешение на расширение authority.

## ✅ Фиксированные этапы V1

| Stage | Название | Итог |
|---|---|---|
| 1 | Current Product Reality Audit | DONE |
| 2 | Installation + First Run | DONE |
| 3 | Model / Provider Setup | DONE |
| 4 | Core User Experience | DONE |
| 5 | Files / Data / Tools E2E | DONE |
| 6 | Continuity / State / Restart | DONE |
| 7 | Failure / Recovery | DONE |
| 8 | Packaging / Update / Operations | DONE |
| 9 | End-to-End Acceptance | DONE |
| 10 | Bounded Pilot | DONE |
| 11 | Titan V1 Closure | DONE when this closure candidate is merged to `main` with all required gates green |

После Stage 11 **не существует обязательного Stage 12**. Research и P2/P3 backlog не открываются автоматически.

## 🧱 P0 / P1

На входе productization были зафиксированы пять V1 P1:

- `P1-01` — fragmented installation / first run;
- `P1-02` — provider onboarding conflict with fail-closed egress;
- `P1-03` — files capability not ordinary-user E2E wired;
- `P1-04` — отсутствовал current release/update lifecycle;
- `P1-05` — duplicate evidence tokens могли раздувать legacy TruthGate cardinality.

Итог closure candidate:

- **P0 = 0**;
- **P1 = 0**;
- все пять перечисленных P1 закрыты в своих заранее определённых этапах.

## 🧪 Ключевые доказательства

### Stage 2 — установка и первый запуск

PR #360. Cross-platform bootstrap создаёт/reuses `.venv`, безопасно создаёт `.env`, запускает loopback server и ждёт health. Fail-closed defaults сохраняются.

### Stage 3 — provider onboarding

PR #364. Explicit remote-data opt-in, provider/model/key configuration и существующие egress controls без новой authority.

### Stage 5 — files/data/tools

PR #366. Local file parser → canonical `/ingest/text`; existing MCP tools через bounded CLI; exact-string D1 deduplication без EvidenceAdmission architecture.

### Stage 6 — continuity

PR #367. Reopen regressions доказывают сохранение фактов и Console notes через новый store instance на том же SQLite path; repeat bootstrap сохраняет user configuration.

### Stage 7 — failure / recovery

PR #368. Startup early-exit, readiness timeout, dependency-install failure и busy-port recovery закреплены product regressions. Existing LLM failure can degrade to local/offline answer where material exists.

### Stage 8 — packaging / update / operations

PR #369. Bounded updater по умолчанию check-only; apply требует clean `main`, fast-forward ancestry и использует только `git merge --ff-only`. Нет reset/rebase/force/auto-update daemon.

### Stage 9 — настоящий browser E2E

PR #370. Mocked DOM smoke не был принят как достаточное доказательство. Добавлен реальный headless Chromium acceptance:

`real Chromium → real Console composer → /chat → Validated memory → DOM reply`.

Acceptance seed проходит существующий ESM + TruthGate путь до `Validated`; policy не ослабляется. External LLM не требуется.

### Stage 10 — bounded pilot

PR #371. Pilot #2 прошёл **5 / 5** сценариев:

1. authenticated local startup + health — PASS;
2. Validated memory → useful local chat — PASS;
3. local `.txt` → FileIngester → `/ingest/text` — PASS;
4. MCP reader tools — PASS, visible tools: 9;
5. stop/restart на тех же SQLite paths → validated recall снова работает — PASS.

Pilot record явно фиксирует:

- `production_authorized = false`;
- `remote_canon = false`;
- `external_llm_required = false`.

## 📊 Bounded V1 readiness dimensions

Это инженерные оценки **только относительно зафиксированного V1 scope**, не authorization metrics и не обещание абсолютного качества:

| Dimension | Closure assessment |
|---|---:|
| Architecture fitness for bounded V1 | 90% |
| Core capabilities required by V1 | 92% |
| Installation / first run | 95% |
| User E2E | 93% |
| Integration | 92% |
| Failure / recovery | 90% |
| UX / operations | 88% |

Таким образом, заранее заданные finish targets выполнены: architecture/core/install/user-E2E/integration достигли V1 target band; failure/recovery ≥85%; UX/operations ≥85%.

Оставшиеся несовершенства не становятся обязательной V1 работой без нового текущего P0/P1.

## 🔒 Границы, которые closure НЕ меняет

После Titan V1 closure остаются истинными:

- `runtime_authority = false`;
- `operator_go = false`;
- production runtime **не авторизован**;
- remote Canon **FORBIDDEN**;
- CI green ≠ production authorization;
- merge ≠ runtime activation;
- pilot ≠ production evidence;
- retrieval ≠ evidence;
- validation ≠ admission;
- receipt ≠ truth;
- identity ≠ authority;
- model output ≠ Canon.

## 🧭 Что остаётся после V1

Можно существовать future/research backlog: GraphRAG/Louvain, typed evidence architecture, trusted registry, дополнительные providers, deeper telemetry, research cognition и другие идеи. Они не являются незавершённостью Titan V1.

Новый обязательный workstream может быть открыт только отдельным решением или новым доказанным P0/P1, а не потому, что систему можно сделать ещё сложнее.

## 🏁 Closure rule

Если Stage 11 closure PR с этим документом:

1. относится к актуальному `main` после Stage 10;
2. имеет `P0 = 0`, `P1 = 0`;
3. проходит full CI, CodeQL и aggregate merge evidence на exact head;
4. не содержит runtime/authority expansion;
5. успешно merged в protected `main`;

то итоговый продуктовый статус:

# **TITAN V1 — DONE**
