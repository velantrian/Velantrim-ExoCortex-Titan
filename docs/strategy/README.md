# 🔱 Velantrim — Strategy Pack (Crystal ⇄ Titan)

**Дата:** 2026-06-06
**Автор сборки:** аудит-сессия (сопоставление Titan ⇄ Crystal + NLnet/NGI Zero Commons)
**Статус:** рабочие стратегические документы. Это НЕ код и НЕ инварианты ядра — это карта решений.

> ⚠️ Эти документы описывают **стратегию двух репозиториев**, а не текущий runtime.
> Канон ядра по-прежнему в `docs/INVARIANTS.md`, `docs/KERNEL_STATE.md`, `Velantrim_Project_Map.md`.

---

## 🎯 Главный тезис

У тебя не «два похожих проекта», а **осознанная двухуровневая стратегия**, которая ложится 1:1 на модель NLnet:

| | 🧠 **Titan** (этот репозиторий) | 💎 **Crystal** ([GitHub](https://github.com/velantrian/velantrim-exocortex-crystal)) |
|---|---|---|
| Роль | Полная **когнитивная система** + продукт + R&D-движок | **Verifiable memory layer** — открытое ядро-commons |
| Состояние | Частично рабочая система + research | Презентабельное, протестированное (99%), упакованное |
| Назначение | Продукт + моат | Грант NLnet + доверие + EU-легитимность |
| Размер `core/` | 54 614 LOC / 170 файлов | 4 491 LOC / 20 файлов |
| Тесты | 85 файлов, зрелость ~6.5/10 (self-report) | 384 теста, 99% покрытие, CI-gate |
| GDPR | ❌ нет (только `audit_chain`) | ✅ полный набор (Art. 5/17/18/30/32) |
| Лицензия | 🔒 приватный канон | ✅ AGPL-3.0 (open core; integrations Apache-2.0) |

**Идея:** грант финансирует мост между ними. Research из Titan дозревает и уходит в открытый Crystal как **грантовые deliverables**; дисциплина Crystal (GDPR, тесты, упаковка, receipts) приходит в Titan и делает его **product-ready**. Один R&D-капитал монетизируется дважды.

---

## 📚 Что внутри (порядок чтения)

| # | Документ | О чём | Для кого |
|---|----------|-------|----------|
| 1 | [`01_PRODUCT_READY_VS_RESEARCH.md`](01_PRODUCT_READY_VS_RESEARCH.md) | Честная разметка: что **product-ready**, что **research / не закрыто (норма для стартапа)**, что **designed-only** — по обоим проектам | Презентация фондам/инвесторам |
| 2 | [`02_IP_BOUNDARY_OPEN_VS_MOAT.md`](02_IP_BOUNDARY_OPEN_VS_MOAT.md) | IP-граница: что отдаём в открытый Crystal (грант), что держим моатом в Titan, что спорно | Защита от случайной отдачи продукта в open source |
| 3 | [`03_GRANT_DELIVERABLES_NLNET.md`](03_GRANT_DELIVERABLES_NLNET.md) | 5 deliverables в формате NLnet milestone (frugal, €5–50k, проверяемые) + MCP-RFC | Грантовая заявка |
| 4 | [`04_TITAN_HARDENING_PLAN.md`](04_TITAN_HARDENING_PLAN.md) | План: что и в каком порядке перенести из Crystal, чтобы Titan стал product-ready | Продуктовая дорожная карта |
| 5 | [`05_RFC_MCP_GATEWAY.md`](05_RFC_MCP_GATEWAY.md) | RFC: capability-based доступ агентов через MCP + graph observability | Сильнейший новый грантовый пункт |

---

## 🏷️ Легенда статусов (используется во всех документах)

| Бейдж | Значение |
|---|---|
| 🟢 **PRODUCT-READY** | Работает, протестировано, упаковано, честные границы задокументированы. Можно показывать как «готовое». |
| 🟡 **WORKING / RESEARCH** | Реальный рабочий код на research-зрелости. Делает что обещает, но не закалён (тесты/конкурентность/observability). **Это норма для стартапа.** |
| 🔵 **DESIGNED** | Спроектировано в спеке/RFC, кода нет или заглушки. Честно помечаем как план. |
| 🔴 **GAP** | Дыра. Отсутствует то, что нужно для product-ready или для гранта. |
| 💎 **OPEN→Crystal** | Кандидат в открытый commons (грантовый deliverable, AGPL-3.0). |
| 🔒 **MOAT→Titan** | Продуктовый моат, остаётся приватным. |
| ⚖️ **CONTESTED** | Требует твоего решения, где провести линию open/moat. |

---

## 🧭 Принцип честности (он же — выигрышная позиция для NLnet)

Фонды NGI Zero **ценят честность и не любят хайп** (двухстадийный отбор, независимая валидация, «value for money»). Поэтому посыл заявки:

> **«Есть product-ready ядро (Crystal, 99% тестов, GDPR, упаковано) + честный research-фронтир, часть которого уже доказана прототипами в приватном движке (Titan).»**

Это сильнее, чем «всё готово». Product-ready ядро даёт вес; открытый research-roadmap даёт причину финансировать; приватные прототипы Titan **снижают риск** того, что обещанное не будет сделано.

---

*Источники по NLnet:* [NGI Zero Commons Fund](https://nlnet.nl/commonsfund/) · [Guide for Applicants](https://nlnet.nl/commonsfund/guideforapplicants/) · [Eligibility](https://nlnet.nl/commonsfund/eligibility/)
