# 🌍 World Skills Core — структура языков и папок

**Язык:** русский  
**Статус:** рабочий канон v0.1  
**Runtime:** не активирован  
**Назначение:** отдельная папка для компактной базы "умения": инвариантная наука, вариантная практика, технологии, логика, человек, общество и повседневные процессы.

---

## 🧭 Как не терять фокус сборки

Главный машинный файл состояния:

```text
WORLD_SKILLS_CORE_STATE.ru.json
```

Его нужно читать перед продолжением сбора. Он хранит:

- текущий счётчик KnowledgeUnit;
- последний batch;
- цель `50 000+`;
- правила против дублей;
- уже покрытые macro-areas;
- список следующих пробелов;
- контракт формата для новых batch-файлов.

То есть продолжение не должно идти только из памяти чата. Правильный порядок:

```text
1. Прочитать WORLD_SKILLS_CORE_STATE.ru.json
2. Проверить ru/00_WORLD_SKILLS_CORE_MAP.ru.md
3. Посмотреть последние batch-файлы
4. Добавить новый тематический batch
5. Пересчитать ID и дубли
6. Обновить README, карту и JSON-state
```

JSON нужен потому, что его легче читать машине: по нему проще продолжать в новом окне, строить валидатор, проверять дубли, видеть gaps и не терять смысл сборки.

---

## 🎯 Решение по структуре

Да, этот слой лучше держать **отдельно**, но не отдельно от проекта вообще, а внутри существующей папки знаний:

```text
docs/knowledge/world_skills_core/
```

Так он:

- не смешивается с кодом ExoCortex;
- не ломает stable V8.6;
- связан с уже существующими `KNOWLEDGE_*.md`;
- готов к будущему переводу на английский;
- может позже стать источником JSON/JSONL seed-базы.

---

## 🌐 Языковая политика

Сейчас основной рабочий язык — **русский**.

Английскую структуру создаём сразу, но пока не заполняем полностью:

```text
world_skills_core/
├── README.ru.md                    ← русский индекс и правила
├── ru/                             ← рабочий русский канон
│   └── 00_WORLD_SKILLS_CORE_MAP.ru.md
└── en/                             ← место для будущего перевода
    └── README.en.md
```

Правило:

> Сначала делаем смысл и структуру на русском.  
> Потом переводим на английский, не меняя архитектурный смысл.

---

## 🧠 Что такое World Skills Core

Это не учебник и не Wikipedia.

Это компактная машинная база:

```text
что устойчиво верно
что меняется по условиям
как люди реально делают вещи
какие есть формулы и правила
какие есть ограничения и риски
как вывести следствие
где знание вероятностное, а где строгое
```

Цель:

> дать Velantrim не просто факты, а основу для понимания мира и практических действий.

---

## 🧩 Связь с уже существующими файлами

Эта папка не заменяет старую базу знаний. Она собирает её в более понятную доменную карту.

| Уже есть | Как используется |
|---|---|
| `KNOWLEDGE_0_OVERVIEW.md` | базовая философия: только суть, без педагогики |
| `KNOWLEDGE_BASE_LAWS.md` | фундаментальные законы |
| `KNOWLEDGE_1_INVARIANT.md` | устойчивые факты |
| `KNOWLEDGE_2_VARIANT.md` | меняющиеся факты, география, история, геология |
| `KNOWLEDGE_3_PRACTICAL.md` | процессы, технологии, производство |
| `KNOWLEDGE_4_PERCEPTION.md` | восприятие организмами |
| `KNOWLEDGE_5_LOGIC.md` | логика и правила вывода |
| `KNOWLEDGE_6_ABSTRACT.md` | воображение, история, интуиция, абстрактные модели |
| `WORLD_KNOWLEDGE_CORE_v1_0.ru.md` | future-work канон качества, времени, противоречий |

`World Skills Core` — это слой над ними:

```text
KNOWLEDGE_*.md
  → World Skills Core map
    → домены
      → KnowledgeUnit
        → future JSON/JSONL seed
```

---

## 🛡️ Важное правило

Этот слой пока **не должен автоматически писать в L3 Canonical Memory**.

Путь должен быть таким:

```text
World Skills Core draft
  → source / confidence / limits
  → review
  → Truth Gate
  → L3 Canonical Graph
```

Нельзя:

- писать гипотезы как факты;
- смешивать философские позиции с физическими законами;
- считать психологические модели абсолютными;
- считать практические инструкции безопасными без safety-поля;
- обещать, что база уже "умнее всех", пока нет тестов.

---

## ✅ Что делаем сейчас

1. Создаём отдельную структуру.
2. Фиксируем русский как source-of-truth.
3. Подготавливаем английскую папку.
4. Описываем доменную карту.
5. Потом постепенно наполняем русские домены.
6. Потом переводим на английский.

---

## 📦 Stage 01 — первый P0 seed pack

Первый сбор знаний лежит здесь:

| Файл | Что внутри |
|---|---|
| `ru/01_P0_FORMAL_LOGIC_MATH.ru.md` | математика, логика, статистика, вычисления |
| `ru/02_P0_NATURAL_EARTH_CORE.ru.md` | физика, химия, биология, география, геология |
| `ru/03_P0_ENGINEERING_PRACTICAL_CORE.ru.md` | инженерия, технологии, дороги, электроника, быт |
| `ru/04_P0_HUMAN_SOCIAL_MEANING_CORE.ru.md` | психология, общество, философия, смысл |
| `ru/99_SOURCE_RULES_AND_COLLECTION_PLAN.ru.md` | правила источников и план расширения |

Все записи пока являются **seed-знанием**, а не автоматически утверждённым L3 Canon.

---

## 📦 Stage 02 — массовое расширение P1

После первичного seed-пакета добавлен второй слой расширения:

| Файл | Что внутри |
|---|---|
| `ru/05_P1_MATH_LOGIC_EXPANSION.ru.md` | алгебра, геометрия, тригонометрия, анализ, вероятность, дискретная математика |
| `ru/06_P1_PHYSICS_CHEMISTRY_EXPANSION.ru.md` | механика, жидкости, тепло, электричество, квант/ядро, химия |
| `ru/07_P1_BIO_EARTH_EXPANSION.ru.md` | клетка, генетика, физиология, экология, география, грунты, климат |
| `ru/08_P1_ENGINEERING_TECH_EXPANSION.ru.md` | материалы, дороги, строительство, электроника, микрочипы, производство, software/ops |
| `ru/09_P1_HUMAN_SOCIAL_EXPANSION.ru.md` | восприятие, обучение, коммуникация, экономика, право, этика, философия |

Цель по объёму для настоящего MVP — не меньше **1500-3000 компактных units**.

---

## 🏭 Полный practical scope

Чтобы не потерять практическую суть, добавлена отдельная карта полного покрытия:

| Файл | Назначение |
|---|---|
| `ru/10_PRACTICAL_FULL_SCOPE_MAP.ru.md` | полный состав practical civilization core: еда, одежда, жильё, материалы, медицина, инструменты, искусство, ремонт, услуги, безопасность |
| `ru/11_AGRO_TEXTILE_INDUSTRY_ECONOMY_SCOPE.ru.md` | растения, культуры, лекарственные травы, красители, текстиль, заводы, финансы, экономика, международная торговля и право |

Целевая карта рассчитана на **20 000+ practical/science units** и задаёт квоты по доменам.

---

## 🧭 50K Collection Protocol

Для большого сбора добавлен протокол:

| Файл | Назначение |
|---|---|
| `ru/12_50K_COLLECTION_PROTOCOL.ru.md` | как собрать 50 000+ units без дублей и потери смысла |
| `ru/13_BATCH_001_AGRO_FOOD_TEXTILE.ru.md` | первый batch: растения, еда, лекарственные/красильные/волокнистые культуры, текстиль |
| `ru/14_BATCH_002_CONSTRUCTION_HOME_MATERIALS.ru.md` | второй batch: жильё, стройматериалы, крыши, фундаменты, вода, отопление, safety |
| `ru/15_BATCH_003_MATERIALS_MANUFACTURING.ru.md` | третий batch: руды, металлы, керамика, цемент, стекло, бумага, пластики, краски |
| `ru/16_BATCH_004_MACHINES_MOTORS_TOOLS.ru.md` | четвёртый batch: машины, двигатели, насосы, инструменты, сварка, транспорт |
| `ru/17_BATCH_005_ELECTRICITY_ELECTRONICS_POWER.ru.md` | пятый batch: электричество, электроника, батареи, сети, CPU, software/security |
| `ru/18_BATCH_006_HEALTH_PHARMA_HYGIENE.ru.md` | шестой batch: гигиена, фарма, медизделия, лаборатории, care safety |
| `ru/19_BATCH_007_ECONOMY_FINANCE_TRADE_LAW.ru.md` | седьмой batch: экономика, финансы, международная торговля, право, IP |
| `ru/20_BATCH_008_ARTS_WOOD_CRAFTS_CREATIVE_TOOLS.ru.md` | восьмой batch: карандаши, ручки, бумага, краски, дерево, ремёсла |
| `ru/21_BATCH_009_TRANSPORT_LOGISTICS_INFRASTRUCTURE.ru.md` | девятый batch: дороги, rail, maritime, aviation, склады, городская инфраструктура |
| `ru/22_BATCH_010_WATER_WASTE_ENVIRONMENT_HOME_UTILITIES.ru.md` | десятый batch: вода, канализация, отходы, среда, бытовые инженерные системы |
| `ru/23_BATCH_011_FOOD_COOKING_PRESERVATION_KITCHENS.ru.md` | одиннадцатый batch: готовка, сохранение пищи, пищевая химия, кухни, HACCP |
| `ru/24_BATCH_012_MINING_ENERGY_INDUSTRIAL_SYSTEMS.ru.md` | двенадцатый batch: добыча, энергия, grid, промышленная безопасность |
| `ru/25_BATCH_013_AGRICULTURE_LIVESTOCK_FORESTRY_FISHERIES.ru.md` | тринадцатый batch: почвы, фермы, животные, лес, рыба, сельхоз safety |
| `ru/26_BATCH_014_APPAREL_TEXTILES_FOOTWEAR_PERSONAL_GOODS.ru.md` | четырнадцатый batch: одежда, ткани, обувь, фабрики, качество, уход |
| `ru/27_BATCH_015_EDUCATION_KNOWLEDGE_WORK_COMMUNICATION.ru.md` | пятнадцатый batch: обучение, документация, argumentation, переговоры, коммуникация |
| `ru/28_BATCH_016_MEASUREMENT_TOOLS_REPAIR_MAINTENANCE.ru.md` | шестнадцатый batch: измерения, инструменты, ремонт, troubleshooting, maintenance |
| `ru/29_BATCH_017_COMPUTING_DATA_AI_COMMUNICATIONS.ru.md` | семнадцатый batch: компьютеры, data, сети, cybersecurity, AI, traceability |
| `ru/30_BATCH_018_HOME_FURNITURE_APPLIANCES_DOMESTIC_LIFE.ru.md` | восемнадцатый batch: дом, мебель, бытовая техника, уборка, безопасность |
| `ru/31_BATCH_019_CIVIC_GOVERNANCE_PUBLIC_SERVICES_EMERGENCY.ru.md` | девятнадцатый batch: государство, службы, emergency systems, городское управление |
| `ru/32_BATCH_020_BODY_SPORTS_ERGONOMICS_DAILY_CARE.ru.md` | двадцатый batch: тело, спорт, эргономика, повседневный уход, safety |
| `ru/33_BATCH_021_RESEARCH_LAB_STANDARDS_EVIDENCE.ru.md` | двадцать первый batch: научный метод, лаборатории, evidence, стандарты, trace |
| `ru/34_BATCH_022_BUSINESS_OPERATIONS_MARKETING_HR.ru.md` | двадцать второй batch: business, marketing, sales, HR, operations, compliance |
| `ru/35_BATCH_023_CULTURE_MEDIA_LANGUAGE_HISTORY.ru.md` | двадцать третий batch: культура, язык, медиа, история, искусство, архивы |
| `ru/36_BATCH_024_GEOGRAPHY_GIS_NAVIGATION_CLIMATE_REGIONS.ru.md` | двадцать четвёртый batch: география, GIS, навигация, климат, регионы |
| `ru/37_BATCH_025_CHEMICAL_PRODUCTS_COSMETICS_DETERGENTS.ru.md` | двадцать пятый batch: бытовая химия, косметика, клеи, краски, detergents |
| `ru/38_BATCH_026_ARCHITECTURE_URBAN_HOUSING_INTERIOR.ru.md` | двадцать шестой batch: архитектура, жильё, фасады, интерьер, городская среда |
| `ru/39_BATCH_027_PSYCHOLOGY_COGNITION_SOCIAL_BEHAVIOR.ru.md` | двадцать седьмой batch: психология, внимание, память, bias, группы, поведение |
| `ru/40_BATCH_028_LAW_RIGHTS_CONTRACTS_CONSUMER_DATA.ru.md` | двадцать восьмой batch: права, договоры, потребители, data protection, liability |
| `ru/41_BATCH_029_SYSTEMS_MODELS_CAUSAL_THINKING.ru.md` | двадцать девятый batch: systems thinking, причинность, модели, risk, decisions |
| `ru/42_BATCH_030_METALWORK_MACHINING_FABRICATION.ru.md` | тридцатый batch: металлы, станки, ЧПУ, сварка, литьё, fabrication safety |
| `ru/43_BATCH_031_ELECTRONICS_DEVICES_MICROCHIPS_ROBOTICS.ru.md` | тридцать первый batch: электроника, embedded, PCB, микрочипы, робототехника |
| `ru/44_BATCH_032_MEDICINE_CLINICAL_SYSTEMS_PUBLIC_HEALTH.ru.md` | тридцать второй batch: клинические системы, patient safety, public health |
| `ru/45_BATCH_033_PHILOSOPHY_ETHICS_MEANING_REASONING.ru.md` | тридцать третий batch: философия, этика, meaning, reasoning, AI ethics |
| `ru/46_BATCH_034_FINANCE_ACCOUNTING_INSURANCE_TAXES.ru.md` | тридцать четвёртый batch: финансы, учёт, налоги, страхование, investing |
| `ru/47_BATCH_035_SECURITY_DEFENSE_RISK_SAFETY_SYSTEMS.ru.md` | тридцать пятый batch: security, defense, risk, continuity, safety systems |
| `ru/48_BATCH_036_AUTOMOTIVE_VEHICLES_MAINTENANCE.ru.md` | тридцать шестой batch: автомобили, ДВС, EV, диагностика, обслуживание |
| `ru/49_BATCH_037_RAIL_MARINE_AEROSPACE_HEAVY_EQUIPMENT.ru.md` | тридцать седьмой batch: rail, marine, aerospace, heavy equipment |
| `ru/50_BATCH_038_PACKAGING_PRINTING_CONSUMER_GOODS.ru.md` | тридцать восьмой batch: упаковка, печать, маркировка, consumer goods |
| `ru/51_BATCH_039_RETAIL_HOSPITALITY_TOURISM_SERVICE_OPERATIONS.ru.md` | тридцать девятый batch: retail, hospitality, tourism, service operations |
| `ru/52_BATCH_040_APPLIED_MATH_DECISION_QUANTITATIVE_LIFE.ru.md` | сороковой batch: прикладная математика, решения, вероятности, таблицы |
| `ru/53_BATCH_041_AUDIO_MUSIC_STAGE_EVENTS_PRODUCTION.ru.md` | сорок первый batch: аудио, музыка, сцена, свет, events, hearing safety |
| `ru/54_BATCH_042_SPACE_ASTRONOMY_TIME_SATELLITES.ru.md` | сорок второй batch: астрономия, время, орбиты, спутники, GNSS |
| `ru/55_BATCH_043_GEOLOGY_MINERALS_SOIL_GEOTECH.ru.md` | сорок третий batch: геология, минералы, почвы, грунты, geotech |
| `ru/56_BATCH_044_CONSTRUCTION_TRADES_PLUMBING_ELECTRICAL_HVAC.ru.md` | сорок четвёртый batch: стройпрофессии, plumbing, electrical, HVAC |
| `ru/57_BATCH_045_FOOD_AGRO_INDUSTRIAL_PROCESSING_SUPPLY.ru.md` | сорок пятый batch: пищевая промышленность, переработка, HACCP, traceability |
| `ru/58_BATCH_046_TEXTILES_ADVANCED_DYES_FASHION_SUPPLY.ru.md` | сорок шестой batch: текстиль, волокна, крашение, fashion supply, quality |
| `ru/59_BATCH_047_WOOD_PAPER_FOREST_PRODUCTS_FURNITURE.ru.md` | сорок седьмой batch: дерево, бумага, мебель, лесные продукты, safety |
| `ru/60_BATCH_048_PHARMA_MEDICINES_HERBAL_BOTANICAL_HEALTH_PRODUCTS.ru.md` | сорок восьмой batch: фарма, лекарства, GMP, фармаконадзор, фитосырье |
| `ru/61_BATCH_049_CROPS_HERBS_HORTICULTURE_PLANT_USES.ru.md` | сорок девятый batch: культуры, травы, волокна, красители, horticulture |
| `ru/62_BATCH_050_CERAMICS_GLASS_CEMENT_LIME_BUILDING_MATERIALS.ru.md` | пятидесятый batch: керамика, стекло, цемент, известь, стройматериалы |
| `ru/63_BATCH_051_POWER_GRID_ELECTRIFICATION_UTILITIES_FIELD_OPS.ru.md` | пятьдесят первый batch: электросети, подстанции, SCADA, utility operations |
| `ru/64_BATCH_052_MANUFACTURING_FACTORY_DESIGN_LEAN_QUALITY_MAINTENANCE.ru.md` | пятьдесят второй batch: фабрики, lean, качество, maintenance, запуск производства |
| `ru/65_BATCH_053_INTERNATIONAL_TRADE_CUSTOMS_LOGISTICS_LAW.ru.md` | пятьдесят третий batch: международная торговля, таможня, Incoterms, trade law |
| `ru/66_BATCH_054_PERSONAL_KNOWLEDGE_MEMORY_NOTES_LEARNING_SYSTEMS.ru.md` | пятьдесят четвёртый batch: личная память, заметки, обучение, traceable knowledge |
| `ru/67_BATCH_055_OFFICE_ADMIN_PROJECT_MANAGEMENT_DOCUMENT_WORKFLOWS.ru.md` | пятьдесят пятый batch: офис, проекты, документы, закупки, workflow |
| `ru/68_BATCH_056_PUBLIC_INFRASTRUCTURE_ROADS_BRIDGES_TUNNELS_DRAINAGE.ru.md` | пятьдесят шестой batch: дороги, мосты, тоннели, ливневка, asset management |
| `ru/69_BATCH_057_WASTE_RECYCLING_CIRCULAR_ECONOMY_SANITATION.ru.md` | пятьдесят седьмой batch: отходы, переработка, sanitation, circular economy |
| `ru/70_BATCH_058_WATER_TREATMENT_IRRIGATION_HYDROLOGY_FLOOD_CONTROL.ru.md` | пятьдесят восьмой batch: вода, очистка, орошение, гидрология, паводки |
| `ru/71_BATCH_059_CLOTHING_FOOTWEAR_LEATHER_LAUNDRY_REPAIR.ru.md` | пятьдесят девятый batch: одежда, обувь, кожа, стирка, ремонт |

Перед началом 50K-сбора проверка показала:

```text
existing IDs: 582
duplicate IDs: 0
```

Текущая контрольная точка после Batch 059:

```text
current IDs: 4010
duplicate IDs: 0
remaining to 50000: 45990
last batch: 71_BATCH_059_CLOTHING_FOOTWEAR_LEATHER_LAUNDRY_REPAIR.ru.md
```

Текущая контрольная точка после старта Layer 5:

```text
current IDs: 21173
duplicate IDs: 0
remaining to 50000: 28827
last batch: 462_BATCH_450_CRISIS_VITAL_RECORDS_FEE_WAIVER_SUPPORT.ru.md
coverage added: contract clause details; engineering calculation limits; language grammar details; metrology/tolerance/QC detail; material degradation; condition monitoring; civic systems; evidence/records procedure; material selection; industrial utilities; service operations; educational assessment; climate adaptation; building envelope/moisture; warehouse logistics; data governance; agriculture operations; textile defects and QA; food plant sanitation and allergen control; treasury cash and liquidity; public procurement and grants; cybersecurity incident response; laboratory quality/calibration; fleet maintenance and dispatch; building commissioning and handover; insurance claims/underwriting; HR workforce/payroll controls; environmental permitting and compliance monitoring; nonprofit/public program monitoring; airport ground operations; retail cash/loss prevention controls; utilities outage restoration; seaport terminal/yard operations; hotel housekeeping/facility operations; construction site logistics/safety; manufacturing changeover/line clearance; cold-chain distribution; library/archive operations; public transit control; wastewater treatment plant operations; postal/parcel operations; elevator/escalator service operations; broadcast/media playout operations; parking/curb management; veterinary clinic operations; pharmacy operations; call center quality operations; event venue operations; dental clinic operations; cleaning/janitorial services; print shop operations; laboratory animal facility operations; museum exhibition operations; court clerk operations; fire prevention inspection operations; mortgage/loan servicing operations; property management/leasing; corporate travel operations; procurement card controls; facilities energy management; subscription billing operations; identity and access management operations; records management operations; industrial laundry operations; mailroom/document scanning operations; laboratory sample logistics operations; field service installation operations; food retail fresh department operations; outpatient front desk operations; school administration operations; rental equipment fleet operations; restaurant front-of-house operations; home care agency operations; municipal permit counter operations; equipment calibration service operations; catering event production operations; security guard operations; funeral home operations; landscaping service operations; ophthalmology clinic operations; radiology imaging center operations; physical therapy clinic operations; pest control service operations; self-storage facility operations; urgent care clinic operations; veterinary boarding operations; car wash operations; appliance repair service operations; dialysis center operations; auto body repair shop operations; locksmith service operations; moving company operations; courier messenger operations; commercial kitchen equipment service operations; coworking space operations; marina operations; laundromat operations; pet grooming operations; boatyard repair operations; crematory operations; appliance retail delivery operations; mobile phone repair operations; community recreation center operations; blood donation center operations; public swimming pool operations; fitness club operations; theater box office and usher operations; farmers market operations; public library programming operations; vehicle inspection station operations; campground operations; funeral cemetery operations; public park maintenance operations; public housing maintenance operations; animal shelter operations; food bank warehouse operations; street maintenance operations; solid waste collection operations; recycling center operations; community health outreach operations; public records request operations; water meter utility operations; unemployment benefits office operations; disaster relief distribution operations; election polling place operations; voter registration office operations; public defender intake operations; probation office operations; courthouse security operations; jail booking operations; legal aid clinic operations; juvenile services intake operations; court interpreter scheduling operations; victim services office operations; civil process service operations; mediation center operations; public health inspection operations; restaurant inspection operations; building code inspection operations; occupational safety inspection operations; environmental health sampling operations; housing habitability inspection operations; fire code inspection operations; elevator inspection program operations; public works asset management operations; stormwater inspection operations; bridge inspection operations; traffic sign inventory operations; traffic signal maintenance operations; pavement management operations; sidewalk inspection operations; road closure permit operations; transit stop maintenance operations; bike lane maintenance operations; streetlight maintenance operations; snow and ice control operations; street sweeping operations; catch basin maintenance operations; urban forestry work order operations; pavement marking operations; municipal drainage complaint operations; public playground inspection operations; road shoulder maintenance operations; traffic calming operations; school crossing guard operations; public restroom maintenance operations; municipal sign shop operations; roadway guardrail maintenance operations; street furniture maintenance operations; municipal fountain maintenance operations; public plaza operations; pedestrian wayfinding operations; public art maintenance operations; dog park operations; trail maintenance operations; outdoor market sanitation operations; community garden operations; urban farm operations; compost site operations; tree nursery operations; seed library operations; native plant restoration operations; invasive plant management operations; irrigation district field operations
latest added: disaster temporary ID appointment support operations; emergency communication board distribution operations; recovery tutoring intake coordination operations; crisis vital records fee waiver support operations
```
