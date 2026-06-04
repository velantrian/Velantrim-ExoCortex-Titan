# 📋 Схема сбора фактов под TruthGate (50K → 1M)

> **Дата:** 2026-05-31 · **Канон:** [TRUTH_AND_RINGZERO_CANON.ru.md](TRUTH_AND_RINGZERO_CANON.ru.md)
>
> Правило из канона §4.1: **нет source → нет ответа** (gap_notice, не выдумка).
> Каждый факт обязан нести источник. Это не ограничение — это то, что даёт
> точность оффлайн без интернета.

---

## 1. Минимальный формат одного факта (JSON)

```json
{
  "fact_id":    "f_phys_light_speed_001",
  "claim":      "Скорость света в вакууме равна 299 792 458 м/с",
  "source":     "CODATA:2018:c",
  "confidence": 0.99,
  "domain":     "physics",
  "metadata": {
    "evidence_ref": {
      "source_id": "CODATA:2018",
      "chunk_id":  "fundamental-constants/c",
      "quote":     "speed of light in vacuum 299 792 458 m/s"
    },
    "language": "ru",
    "tags": ["physics", "constants", "light"]
  }
}
```

### Обязательные поля

| Поле | Тип | Правило | На что влияет |
|------|-----|---------|---------------|
| `fact_id` | str | уникальный, stable (не UUID4!) | дедуп, обновления, трейс |
| `claim` | str | краткое утверждение, ≤ 300 символов | то, что система вернёт как ответ |
| `source` | str | непустой идентификатор источника | **обязателен для TruthGate** — без него verdict = gap_notice |
| `confidence` | float 0–1 | ≥ 0.5 для допуска в ответ; ≥ 0.75 для Validated | какой вес у факта при retrieval |

### Желательные поля (повышают качество)

| Поле | Правило |
|------|---------|
| `domain` | одно слово: `physics`, `biology`, `history`, `math`, … — помогает профилю и поиску |
| `metadata.evidence_ref` | структурный объект — поднимает до строгого EvidenceRef (source_id + локатор) |
| `metadata.tags` | список тегов, помогает кластеризации и аффордансам |
| `metadata.language` | `ru` / `en` (для NLP-операций) |

---

## 2. Правила `fact_id` — почему это важно

🔑 **fact_id — это не UUID4, а осмысленный ключ.** На 50K фактов это даёт:
- **Дедуп:** повторный ингест того же факта = upsert, не дубль.
- **Обновление:** когда CODATA выпускает новое значение — обновляешь конкретный факт, а не плодишь копии.
- **Трейс:** в TraceRecord ты видишь `f_phys_light_speed_001`, а не `3f7a2b1c`.

**Схема именования:**
```
{домен}_{категория}_{суть}_{порядковый}
Примеры:
  f_phys_light_speed_001          # физика / скорость света
  f_bio_dna_structure_001         # биология / структура ДНК
  f_hist_ww2_end_year_001         # история / год конца ВМВ
  f_math_pi_value_001             # математика / значение π
  f_chem_water_formula_001        # химия / формула воды
  wsk_agro_001_soil_nitrogen      # world_skills_core batch 001 / азот в почве
```

---

## 3. Правила `source` — ключ к точности оффлайн

Источник — это **не название статьи**, а **устойчивый идентификатор**:

```
Хорошо:   "CODATA:2018:c"                # стандарт + год + константа
           "IUPAC:2005:periodic-table"    # организация + год + раздел
           "Watson-Crick:Nature:1953"     # автор + журнал + год
           "IAU:2006:resolution-B5"       # орган + год + резолюция
           "world_skills_core:batch_001"  # твой собственный сборник
           "encyclopedia_britannica:2024:photosynthesis"

Плохо:    ""              # пустой → gap_notice (факт не пройдёт TruthGate)
          "интернет"      # неверифицируемо
          "GPT"           # LLM — не источник (именно это система отвергает)
          "неизвестно"    # честно, но бесполезно
```

> **Ключевое правило:** твои практические знания (`world_skills_core`) — тоже источник!
> `"source": "world_skills_core:batch_001:agro"` — валидный источник, если ты его составлял
> из реальных материалов. Система будет на него опираться оффлайн.

---

## 4. Структурный `evidence_ref` (для строгих/научных фактов)

Это поле поднимает факт от «есть source» до «есть доказательство»
(Core-3 канон §4.2). Используй для фактов, требующих полного доверия:

```json
"evidence_ref": {
  "source_id": "CODATA:2018",           // обязательно
  "chunk_id":  "fundamental-constants/c",  // где именно в источнике
  "span":      [120, 145],              // символы в документе (если есть)
  "quote":     "speed of light in vacuum 299 792 458 m/s"  // цитата
}
```

Минимально достаточно: `source_id` + одно из (`chunk_id` | `span` | `quote`).

---

## 5. Схема по типам знаний

### 5.1 Научные константы и факты
```json
{ "fact_id": "f_phys_planck_h_001",
  "claim":   "Постоянная Планка h = 6,626 × 10⁻³⁴ Дж·с",
  "source":  "CODATA:2018:h", "confidence": 0.99, "domain": "physics",
  "metadata": {"evidence_ref": {"source_id":"CODATA:2018","chunk_id":"h","quote":"6.626 070 15e-34 J Hz-1"}} }
```

### 5.2 Биология и медицина (высокий риск → строгое evidence)
```json
{ "fact_id": "f_bio_heart_rate_rest_001",
  "claim":   "Нормальная частота пульса в покое у взрослого: 60–100 уд/мин",
  "source":  "AHA:2023:normal-heart-rate", "confidence": 0.95, "domain": "biology",
  "metadata": {"tags": ["cardiology","health","norms"],
               "evidence_ref": {"source_id":"AHA:2023","chunk_id":"resting-hr","quote":"60 to 100 beats per minute"}} }
```

### 5.3 Практические навыки (`world_skills_core`)
```json
{ "fact_id": "wsk_agro_001_nitrogen_soil",
  "claim":   "Азот необходим для синтеза белков в растениях",
  "source":  "world_skills_core:batch_001:agro", "confidence": 0.90, "domain": "agronomy",
  "metadata": {"tags": ["agronomy","soil","nutrients","plants"]} }
```

### 5.4 История и даты
```json
{ "fact_id": "f_hist_ww2_end_1945_001",
  "claim":   "Вторая мировая война завершилась в 1945 году",
  "source":  "encyclopedia_britannica:2024:world-war-ii", "confidence": 0.99, "domain": "history" }
```

### 5.5 Логические и математические истины
```json
{ "fact_id": "f_math_pythagoras_001",
  "claim":   "В прямоугольном треугольнике a² + b² = c², где c — гипотенуза",
  "source":  "euclidean_geometry:elements:I.47", "confidence": 1.0, "domain": "mathematics" }
```

---

## 6. Причинные связи (relations) — как соединять факты

Связи делают базу **умной** (не просто хранилищем). Добавляй через API:

```json
{
  "from_fact_id": "f_bio_nitrogen_fixation_001",
  "to_fact_id":   "wsk_agro_001_nitrogen_soil",
  "relation_type": "enables",
  "confidence":   0.88,
  "source":       "biochemistry:nitrogen-cycle"
}
```

Канонические типы (из Core-3 `FORWARD_TYPES`):
`causes` · `prevents` · `requires` · `enables` · `implies` · `contradicts`
`generalizes` · `specializes` · `precedes` · `follows` · `composes` · `analogous_to` · `becomes`

> 💡 **Автоинференс** (через LLM) → пишется `truth_status="pending"` (не validated).
> Вручную добавленные связи → `truth_status="validated"`. Никогда не смешивать.

---

## 7. Как батч-ингест запустить (`store_facts_batch`)

```python
from core.memory import SQLiteGraphStore

store = SQLiteGraphStore("data/velantrim.db")
facts = [...]   # список dict по схеме выше

stats = store.store_facts_batch(facts)
# → {"stored": N, "updated": M, "drift": 0, "errors": 0}
```

**Требования к батчу:**
- ✅ Каждый факт должен иметь `fact_id` (без него пропускается с предупреждением).
- ✅ `source` непустой — иначе пройдёт в базу, но не пройдёт TruthGate при ответе.
- ✅ Рекомендуемый размер батча: **200–500 фактов** (баланс скорости/atomicity).
- ⚠️ Весь батч в одной транзакции: или все, или никто (после фикса C2 это гарантировано).

---

## 8. 🔑 Правило самодостаточного claim (data-quality, 2026-05-31)

**`claim` обязан быть САМОДОСТАТОЧНЫМ** — содержать сам факт целиком, а не опираться
на соседние колонки/контекст. Различающая информация должна быть В САМОМ claim.

```
Плохо (generic, неразличимо):
  | georef.fr.capital | Франция — Париж | invariant | столица, евро (EUR) | … |
  | georef.it.capital | Италия — Рим     | invariant | столица, евро (EUR) | … |
  → claim'ы Франции и Италии ИДЕНТИЧНЫ → (1) ложно сливаются дедупом как дубли,
    (2) бесполезны для ответа «столица Франции?» (claim — это то, что хранится и возвращается).

Хорошо (самодостаточно, различимо):
  | georef.fr.capital | Франция — Париж | invariant | Столица Франции — Париж; валюта евро (EUR) | … |
  | georef.it.capital | Италия — Рим     | invariant | Столица Италии — Рим; валюта евро (EUR)    | … |
```

> ⚠️ **Почему это важно:** в системе хранится и ищется именно `claim`. Колонки
> `KnowledgeUnit` / «Практический смысл» — для людей, не для движка. Если различие
> только в них — для памяти факты неотличимы.
>
> 🤖 **Машинная проверка:** `scripts/verify_world_skills.py` флажит **duplicate claims**
> (одна нормализованная «Суть» у ≥2 ID) и **short claims** (<12 симв.). Запуск с
> `--strict-claims` делает их ошибкой (exit 1) для CI.

## 9. Чек-лист факта перед ингестом

```
☐ fact_id осмысленный и уникальный (не UUID4)
☐ claim САМОДОСТАТОЧЕН — различающая инфо в самом claim, не в соседних колонках
☐ claim ≤ 300 симв., конкретное утверждение, без «возможно» / «наверное»
☐ claim НЕ дублирует другой (verify_world_skills.py: 0 duplicate claims)
☐ source непустой, верифицируемый идентификатор
☐ confidence ≥ 0.5 (иначе только Observed, не пройдёт в ответ)
☐ domain указан (physics / biology / history / math / …)
☐ evidence_ref структурный — для строгих/медицинских/научных фактов
☐ Противоречие с существующими фактами проверено (или принять как contradicts)
```

---

*На что влияет этот стандарт:*
🎯 *каждый факт, собранный по этой схеме, проходит TruthGate и становится основой
точного оффлайн-ответа. Факты без source хранятся (не теряются), но получают
gap_notice — система честно говорит «нет доказательств» вместо выдумки.
На 50K фактов это разница между «знающей системой» и «уверенным болтуном».*
