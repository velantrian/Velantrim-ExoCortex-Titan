# 7. 📋 Готовый блок для Crystal — research-направление «живая KB»

**Дата:** 2026-06-06 · [← назад к индексу](README.md)

Готовый текст для вставки в **публичный Crystal** (он на английском — блок тоже на английском, для единообразия). Формулировка **нейтральна к языку** (язык наполнения не упоминается) и в честном стиле Crystal (это research-направление, а не текущая фича).

> ⚠️ **Не вставлено автоматически:** Crystal — отдельный публичный репозиторий, привязанный к гранту; локального git-клона рядом нет (только zip-копии). Применение/push — за тобой (или скажи мне — склонирую и подготовлю коммит на ревью, без push). См. конец файла.

---

## Вариант A — короткий блок в `README.md`

Вставить в секцию **«Research inspiration»** (после абзаца про биологию) или новой подсекцией **«Research direction»**:

```markdown
## Research direction: a living, local knowledge base

Beyond the shippable memory infrastructure, Velantrim's research line (in the
larger ExoCortex research system) explores a **structured knowledge base stored
as a graph — nodes connected by typed edges**, rather than flat encyclopedic
text. Knowledge is organised by epistemic class:

- **invariant science** — laws that do not change;
- **variant & practical knowledge** — applied, changing knowledge;
- **logic** — rules of inference.

An experimental build of roughly **50,000 graph-connected facts** is used to
evaluate how the system answers. If the approach proves effective, the base can
scale to **200,000–300,000 facts**. The goal is *not* "another Wikipedia" (flat
lookup) but a **living cognitive system**: graph-connected, epistemically typed
knowledge that supports reasoning and is designed to **run locally on modest
hardware** — no large GPU, no cloud.

This is a *research direction*, not a current runtime feature — the shippable
infrastructure described above does not depend on it. What this repository
provides (verifiable provenance, GDPR data-subject operations, capability-based
access) is exactly what makes such a knowledge base **trustworthy, lawful and
auditable** rather than an opaque dump.
```

---

## Вариант B — расширенный блок в `FUTURE.md` (раздел «Research directions»)

```markdown
### Living, local knowledge base (graph-native, epistemically typed)

**Today:** the shippable core stores facts with provenance and ESM state, but
does not ship a large curated knowledge base.

**Research:** a knowledge base where every unit is a **node linked by typed,
weighted edges**, partitioned by epistemic class — **invariant science** (stable
laws), **variant & practical knowledge** (applied, changing), and **logic**
(inference rules). An experimental ~50k-fact graph is used to measure answer
quality; on success it scales to 200k–300k facts. The aim is a system that
*reasons over* connected knowledge and runs **locally on modest hardware**,
rather than a flat encyclopedia.

**Why it depends on this repo:** such a base is only trustworthy if every fact
carries provenance, can be lawfully erased/restricted (GDPR), and is reachable
only through capability-gated, audited access. Those guarantees are precisely the
infrastructure this repository implements.
```

---

## Куда именно вставлять

| Файл в Crystal | Место | Вариант |
|---|---|---|
| `README.md` | секция «Research inspiration» / новая «Research direction» | A |
| `FUTURE.md` | раздел «3. Research directions» | B |
| `HYBRID_VISION.md` | как дополнительный слой к биологическому видению | A или B |

---

## 🤝 Как применить (на выбор)

1. **Сам вставишь** — скопируй блок A или B в каноническую копию Crystal и запушишь.
2. **Я подготовлю коммит** — скажи, и я: склонирую `velantrim-exocortex-crystal` начисто, добавлю блок, сделаю коммит **на твоё ревью без push**. Push — только после твоего «ок» (это публичный грант-репозиторий, действие outward-facing).

> 🧭 По принципу честности ([memory: honesty](../KERNEL_STATE.md) / `docs/strategy/01`): подаём как research-направление, а не готовую фичу — это усиливает, а не ослабляет заявку (NLnet ценит честность и проверяемость).
