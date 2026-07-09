# 3. 💶 Грантовые deliverables — формат NLnet / NGI Zero Commons

**Дата:** 2026-06-06 · [← назад к индексу](README.md)

## 📋 Рамки фонда (проверено, 2026-06-06)

| Параметр | Значение |
|---|---|
| Размер | €5 000 – €50 000 на первый проект; >€50k только **после** успешно завершённого меньшего |
| Лицензия | **обязательно open source** (признанная OSI/FSF), целиком |
| Цель | R&D как основная цель |
| Гео | чёткое **европейское измерение** (приоритет ЕС/Horizon Europe) |
| Отбор | 2 стадии, независимая валидация, **«value for money» / frugal budgets** |
| Открытость | научные результаты — open access |
| Календарь | 13-й call закрылся **2026-06-01** (дедлайн прошёл); программа идёт до **2027-06-30**, новые call'ы до исчерпания бюджета |

Источники: [Commons Fund](https://nlnet.nl/commonsfund/) · [Guide](https://nlnet.nl/commonsfund/guideforapplicants/) · [Eligibility](https://nlnet.nl/commonsfund/eligibility/) · [44 проекта отобрано, март 2026](https://nlnet.nl/news/2026/20260302-announce-commons-fund.html)

> ⏰ **Практика:** дедлайн 13-го call'а уже прошёл. Если заявка туда подана — ждём результат. Если нет — целимся в **следующий call** (программа до середины 2027). Стратегия лестницы: маленький успешный проект → больший грант.

---

## 🧱 Позиция (повторяет [док 1](01_PRODUCT_READY_VS_RESEARCH.md))

> **Product-ready открытое ядро (Crystal) + честный research-фронтир, де-рискованный прототипами Titan.**

Каждый deliverable ниже: 🟢 уже product-ready (упаковать/задокументировать) или 🟡 рабочий PoC → довести до открытого. Все — frugal, проверяемые, целиком открытые.

---

## 🎯 Пять deliverables

### D1 — Verifiable provenance & replayable receipts 🟢
- **Проблема:** ответы AI нельзя перепроверить постфактум; источник «растворён».
- **Deliverable:** портируемый формат tamper-evident receipt + `verify` (перепроверка по канону, детект erased/restricted/modified/contradicted). Спецификация формата как **open standard**.
- **NGI-fit:** verifiable infrastructure, auditability, interop.
- **De-risk:** ✅ уже работает в Crystal `core/provenance.py` (SHA-256+HMAC). Работа = **спека формата + interop + доки**, не «с нуля».
- **Приёмка:** receipt переживает рестарт; ловит 4 типа дрейфа; стороннее воспроизведение по спеке.
- **Объём:** S (малый). 💎 целиком open.

### D2 — GDPR data-subject operations (reusable library) 🟢
- **Проблема:** локальным AI-системам нужен правовой каркас (право на забвение, ограничение, шифрование, PII).
- **Deliverable:** отдельная переиспользуемая open-библиотека: erasure (Art. 17, cascade + content-free tombstone), restriction + RoPA (Art. 18/30), encryption-at-rest (Art. 32), PII-redaction (Art. 5), tamper-evident audit log.
- **NGI-fit:** **европейское измерение в чистом виде** + privacy-by-design.
- **De-risk:** ✅ уже в Crystal (`erasure/compliance/crypto/pii/audit`). Работа = выделить как самостоятельный пакет + article-by-article доки + тесты.
- **Приёмка:** проходит сценарии субъекта данных; audit-log детектирует любую правку; stdlib-fallback без зависимостей.
- **Объём:** S–M. 💎 целиком open. ⭐ **Самый сильный «европейский» пункт.**

### D3 — RFC-MCP-GATEWAY: capability-based доступ агентов 🟡 → 🆕
- **Проблема:** агенты получают доступ к памяти бесконтрольно; LLM может случайно вызвать опасный инструмент.
- **Deliverable:** открытый MCP-gateway поверх памяти: роли как **наборы инструментов** (reader/researcher/ingester/guardian/admin), принцип «опасный инструмент не зарегистрирован → модель его не видит»; транспорт StreamableHTTP + SSE; каждый mutation → trace; запись только после TruthGate.
- **NGI-fit:** **открытый стандарт MCP = interop/commons**, ролевое разделение = privacy/безопасность, multi-agent.
- **De-risk:** ✅ контракт уже есть в Titan `core/tool_registry.py` (5 ролей, capability-chain, MCP-манифест). Работа = транспорт + реализации + порт в Crystal.
- **Приёмка:** reader физически не видит write-tools; деструктив требует admin + audit; два транспорта работают.
- **Объём:** M. 💎 open. Полная спека — [`05_RFC_MCP_GATEWAY.md`](05_RFC_MCP_GATEWAY.md).

### D4 — Graph observability & integrity (`velantrim integrity`) 🟡
- **Проблема:** в графах знаний копится «грязь» (orphan/dangling/дубли/рассинхрон L1↔L3) — её не видно.
- **Deliverable:** одна команда/инструмент, агрегирующая отчёт: dangling_edges, orphan_nodes, duplicate_claims/edges, wrong_direction_edges, contradictions, L1/L3 mismatch, restricted mismatch, missing evidence_ref.
- **NGI-fit:** auditability, reproducibility, «value for money» (видимое качество).
- **De-risk:** ✅ кубики есть (Titan `fact_integrity.py`, `semantic_dedup.py`, `find_contradictions`; Crystal `observe.py`). Работа = **агрегатор + CLI + доки**.
- **Приёмка:** на «грязном» графе отчёт находит все засеянные дефекты; чистый граф → зелёный отчёт.
- **Объём:** S–M. 💎 open.

### D5 — Hybrid (vector+graph) retrieval + открытый eval-harness 🟡
- **Проблема:** заявления «граф улучшает recall» обычно не воспроизводимы (ср. Habr: 46.7%→68.3%, но на **72 нодах/215 рёбрах** — не строгий бенчмарк).
- **Deliverable:** открытый, воспроизводимый eval-harness (датасет + метрики) для гибридного поиска vector+graph-walk; честный отчёт «когда граф помогает, когда нет».
- **NGI-fit:** open-access наука, reproducibility — прямо в духе фонда.
- **De-risk:** ✅ ретриверы есть (Titan Hybrid BM25+Dense+RRF; Crystal graph-walk). Работа = **harness + датасет + отчёт**.
- **Приёмка:** третья сторона воспроизводит цифры по репозиторию; результаты честные (включая отрицательные).
- **Объём:** M. 💎 open. ⚠️ В заявке цифры Habr подавать только как «motivation», не как доказательство.

---

## 🗺️ Как подавать (пакетирование под €5–50k)

| Сценарий | Состав | Почему |
|---|---|---|
| **Минимальный, сильный** (рек.) | D2 + D3 | европейское измерение + открытый стандарт; обе де-рискованы существующим кодом |
| Если упор на доверие | D1 + D2 + D4 | provenance + GDPR + auditability = «verifiable memory» целиком |
| Полный | D1–D5 | если бюджет/время позволяют; держать frugal |

> 💡 **Frugal-правило NLnet:** не предлагай «весь Titan». Предлагай 2–3 узких, проверяемых, целиком открытых пункта, у которых **уже есть рабочий прототип**. Это максимизирует «value for money» в глазах ревьюера.

**Связки:** граница open/moat — [док 2](02_IP_BOUNDARY_OPEN_VS_MOAT.md); как это же двигает продукт — [док 4](04_TITAN_HARDENING_PLAN.md).
