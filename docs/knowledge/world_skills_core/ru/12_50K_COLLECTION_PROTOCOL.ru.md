# 🧭 50K Collection Protocol — как собрать 50 000 units и не потерять смысл

**Язык:** русский  
**Статус:** рабочий протокол v0.1  
**Цель:** собрать 50 000+ compact KnowledgeUnit без дублей, без смешивания фактов с гипотезами и без потери practical-смысла.

---

## 🎯 Главная цель

Нужно собрать не энциклопедию текста, а базу умения:

```text
инвариантная наука
+ вариантная наука
+ практическая технология
+ растения / сырьё / материалы
+ еда / одежда / жильё / медицина / инструменты
+ экономика / финансы / торговля / право
+ safety / failure modes / контроль качества
+ логика и условия применимости
```

---

## 🧱 Единица сбора

Каждая запись должна быть компактной:

```text
ID | Тип | Суть | Условия / границы | Связи
```

Для практических процессов дополнительно нужны:

```text
сырьё
этапы
оборудование
условия
дефекты
контроль качества
безопасность
```

---

## 🆔 Правило ID

ID должен быть:

- уникальный;
- стабильный;
- машинно читаемый;
- без пробелов;
- с доменным namespace.

Примеры:

```text
agro.crop.wheat.soil_requirements
food.process.bread.fermentation
textile.process.cotton.ginning
factory.cement.kiln.energy
finance.manufacturing.working_capital
trade.incoterms.fob
law.international.arbitration_clause
```

---

## 🚫 Anti-duplicate protocol

Перед каждым batch:

1. считать все ID из `world_skills_core/ru/*.ru.md`;
2. проверить exact duplicates;
3. новые ID добавлять только в свободном namespace;
4. если понятие уже есть, не повторять, а добавлять:
   - `process`;
   - `failure_mode`;
   - `quality_check`;
   - `safety_rule`;
   - `economic_unit`;
   - `supply_chain_unit`.

Правило:

> Не создавать второй `chem.corrosion`, если уже есть.  
> Создавать `eng.pipeline.corrosion_under_insulation` или `maintenance.corrosion.inspection` — это другой слой.

---

## 📊 Целевые квоты 50K

| Слой | Цель units |
|---|---:|
| 🌾 Agriculture / plants / raw resources | 4 000 |
| 🍞 Food / cooking / preservation | 4 000 |
| 🧵 Textile / clothing / leather | 3 500 |
| 🏠 Shelter / construction / home systems | 4 500 |
| 🧱 Materials / chemistry / manufacturing materials | 5 000 |
| 🔥 Industrial processes / factories | 5 000 |
| ⚙️ Machines / tools / engines | 4 000 |
| ⚡ Electrical / electronics / computing | 4 500 |
| 💊 Health / medicine / care | 3 000 |
| 🎨 Arts / writing / creative tools | 2 000 |
| 🧰 Repair / maintenance / everyday skills | 2 500 |
| 💰 Economy / finance / trade / law | 4 000 |
| 🛡️ Safety / risk / failure modes | 4 000 |
| 🧮 Formal / science support | 3 000 |
| **Итого** | **53 000** |

---

## 📦 Batch strategy

Собирать не одним гигантским файлом, а пачками:

```text
Batch 001  agro + food + textile foundation
Batch 002  construction + home + natural materials
Batch 003  metals + ceramics + glass + plastics
Batch 004  machines + engines + tools
Batch 005  electricity + electronics + chips
Batch 006  medicine + hygiene + pharma safety
Batch 007  factories + industrial operations
Batch 008  finance + economy + trade + law
Batch 009  repair + maintenance + everyday skills
Batch 010  arts + writing + creative materials
...
```

Каждый batch должен иметь:

- свою тему;
- 100-500 новых units;
- отсутствие дублей;
- минимум 5 типов units: `MATERIAL`, `PROCESS`, `MECHANISM`, `FAILURE_MODE`, `QUALITY_CHECK`, `SAFETY_RULE`.

---

## ✅ Текущий статус

Перед началом 50K-сбора:

```text
existing IDs: 582
duplicates: 0
```

Stage 50K начинается с:

```text
13_BATCH_001_AGRO_FOOD_TEXTILE.ru.md
```
