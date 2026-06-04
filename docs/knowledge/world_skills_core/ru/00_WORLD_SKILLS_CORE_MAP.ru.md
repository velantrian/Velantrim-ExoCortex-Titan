# 🌍 World Skills Core v0.1 — карта доменов

**Язык:** русский  
**Статус:** рабочая карта / не runtime  
**Цель:** сделать Velantrim более понятливым и практичным через компактное ядро науки, техники, логики, человека и общества.

---

## 🧠 Главная идея

Velantrim не нужно хранить весь интернет.

Ему нужна экономичная база:

```text
инварианты мира
+ варианты по условиям
+ практические технологии
+ логика и вывод
+ человек и общество
+ качество источников
+ ограничения применимости
```

Такая база делает систему не просто "знающей", а **умеющей связывать знания в цепочки**.

---

## 🗺️ Общая карта

```text
🌍 WORLD SKILLS CORE
│
├── 🧮 01 Formal Core
│   ├── математика
│   ├── логика
│   ├── статистика
│   ├── теория информации
│   └── вычисления
│
├── ⚛️ 02 Natural Science Core
│   ├── физика
│   ├── химия
│   ├── биология
│   ├── материаловедение
│   └── астрономия
│
├── 🌍 03 Earth & Space Core
│   ├── география
│   ├── геология
│   ├── климатология
│   ├── гидрология
│   ├── почвоведение
│   └── GIS / карты / координаты
│
├── 🛠️ 04 Engineering & Technology Core
│   ├── строительство
│   ├── дороги и инфраструктура
│   ├── машины и механизмы
│   ├── электроника и микропроцессоры
│   ├── энергетика
│   ├── производство
│   ├── бытовая химия
│   └── безопасность
│
├── 🧬 05 Life & Health Core
│   ├── физиология
│   ├── медицина как риск-домен
│   ├── питание
│   ├── микробиология
│   └── экология
│
├── 🧠 06 Human Core
│   ├── психология
│   ├── когнитивистика
│   ├── память и внимание
│   ├── обучение
│   ├── коммуникация
│   └── поведение
│
├── 🏛️ 07 Society Core
│   ├── экономика
│   ├── право
│   ├── управление
│   ├── логистика
│   ├── города
│   └── социальные системы
│
├── 📜 08 Philosophy & Meaning Core
│   ├── эпистемология
│   ├── этика
│   ├── философия науки
│   ├── аргументация
│   └── границы знания
│
└── 🔧 09 Practical Everyday Core
    ├── дом и быт
    ├── ремонт
    ├── материалы
    ├── инструменты
    ├── бытовые риски
    └── повседневные процессы
```

---

## 🧩 Что собирать в каждом домене

Не статьи. Не длинные объяснения. Только суть.

| Тип знания | Что хранить | Пример |
|---|---|---|
| `LAW` | устойчивый закон | `F = m·a` |
| `THEOREM` | доказанная математическая связь | теорема Пифагора |
| `MODEL` | модель с условиями | модель идеального газа |
| `MECHANISM` | как работает процесс | вода в трещине замерзает и расширяется |
| `METHOD` | как делают люди | пайка, цементация, фотолитография |
| `CONSTRAINT` | что ограничивает | температура плавления, токсичность, прочность |
| `FAILURE_MODE` | как ломается | коррозия, усталость металла, перегрев |
| `SAFETY_RULE` | риск и запрет | не смешивать отбеливатель с кислотами |
| `FORMULA` | расчёт | площадь, объём, давление, сопротивление |
| `HEURISTIC` | практическое правило | сначала проверить питание, потом плату |
| `ARGUMENT` | позиция/довод | философский аргумент |
| `COUNTEREVIDENCE` | что против | эксперимент, опровержение |

---

## ⚖️ Разная строгость для разных областей

Не все знания одинаковые.

| Область | Как хранить |
|---|---|
| 🧮 Математика | строго: аксиомы, определения, теоремы, доказательства |
| ⚖️ Логика | правила вывода, тип логики, условия применимости |
| ⚛️ Физика | законы + границы: классика, квант, релятивизм |
| 🧪 Химия | реакции, вещества, условия, безопасность |
| 🧬 Биология | механизмы + вариативность живых систем |
| 🌍 География | данные, координаты, климат, меняющиеся факты |
| 🪨 Геология | модели, слои, материалы, региональные условия |
| 🛠️ Инженерия | процессы, ограничения, failure modes, safety |
| 🧠 Психология | вероятностные модели, не абсолютные истины |
| 📜 Философия | школы, аргументы, позиции, контраргументы |

---

## 🧠 Почему это сделает систему умнее

Обычная LLM часто знает фразы.

Velantrim с World Skills Core сможет строить цепочки:

```text
геология → какой грунт
физика → что происходит с водой и нагрузкой
химия → как ведёт себя материал
математика → как посчитать уклон/давление/объём
инженерия → как построить и обслужить
экономика → что реально возможно по бюджету
психология → как люди будут этим пользоваться
этика → какие риски для людей
```

Пример:

```text
Почему дорога разрушается зимой?

география: регион с циклами freeze/thaw
геология: слабый грунт или плохой дренаж
физика: вода расширяется при замерзании
химия: свойства асфальтобетона и соли
инженерия: недостаточная толщина слоя
математика: нагрузка транспорта и напряжение
практика: обслуживание и ремонт
```

Ответ становится не "дорога плохая", а:

> Дорога разрушается из-за цепочки: вода попадает в микротрещины, замерзает, расширяется, ослабляет материал; затем нагрузка транспорта ускоряет разрушение. Если грунт слабый, дренаж плохой, а смесь не подходит к климату, повреждения растут быстрее.

---

## 📦 Базовый формат записи

```json
{
  "id": "mechanism.road.freeze_thaw_damage",
  "domain": "engineering.roads",
  "type": "MECHANISM",
  "statement": "Freeze-thaw cycles damage road surfaces when water enters cracks, freezes, expands, and increases internal stress.",
  "conditions": [
    "temperature crosses 0°C",
    "water can enter pores or cracks",
    "material has insufficient resistance or drainage"
  ],
  "limits": [
    "Does not explain all road damage",
    "Traffic load, asphalt mix, base layer and drainage must also be considered"
  ],
  "prereq": [
    "concept.water_expansion_freezing",
    "concept.material_stress",
    "concept.drainage"
  ],
  "links": [
    "physics.phase_change",
    "geology.soil_stability",
    "chemistry.asphalt_binder",
    "engineering.road_maintenance"
  ],
  "truth_status": "SUPPORTED",
  "confidence": 0.9,
  "safety_critical": false
}
```

---

## 🚦 Приоритет наполнения

### P0 — фундамент

1. 🧮 логика и типы вывода;
2. 🧮 базовая математика;
3. ⚛️ физика повседневного мира;
4. 🧪 химия материалов и бытовой безопасности;
5. 🛠️ инженерные failure modes;
6. 🌍 география + геология для инфраструктуры;
7. 🧠 психология внимания, памяти, ошибок.

Первый P0 seed pack уже выделен в файлы:

```text
01_P0_FORMAL_LOGIC_MATH.ru.md
02_P0_NATURAL_EARTH_CORE.ru.md
03_P0_ENGINEERING_PRACTICAL_CORE.ru.md
04_P0_HUMAN_SOCIAL_MEANING_CORE.ru.md
99_SOURCE_RULES_AND_COLLECTION_PLAN.ru.md
```

Stage 02 расширяет P0 до P1:

```text
05_P1_MATH_LOGIC_EXPANSION.ru.md
06_P1_PHYSICS_CHEMISTRY_EXPANSION.ru.md
07_P1_BIO_EARTH_EXPANSION.ru.md
08_P1_ENGINEERING_TECH_EXPANSION.ru.md
09_P1_HUMAN_SOCIAL_EXPANSION.ru.md
```

Полный practical scope для 20 000+ units:

```text
10_PRACTICAL_FULL_SCOPE_MAP.ru.md
11_AGRO_TEXTILE_INDUSTRY_ECONOMY_SCOPE.ru.md
```

50K protocol и первый batch:

```text
12_50K_COLLECTION_PROTOCOL.ru.md
13_BATCH_001_AGRO_FOOD_TEXTILE.ru.md
14_BATCH_002_CONSTRUCTION_HOME_MATERIALS.ru.md
15_BATCH_003_MATERIALS_MANUFACTURING.ru.md
16_BATCH_004_MACHINES_MOTORS_TOOLS.ru.md
17_BATCH_005_ELECTRICITY_ELECTRONICS_POWER.ru.md
18_BATCH_006_HEALTH_PHARMA_HYGIENE.ru.md
19_BATCH_007_ECONOMY_FINANCE_TRADE_LAW.ru.md
20_BATCH_008_ARTS_WOOD_CRAFTS_CREATIVE_TOOLS.ru.md
21_BATCH_009_TRANSPORT_LOGISTICS_INFRASTRUCTURE.ru.md
22_BATCH_010_WATER_WASTE_ENVIRONMENT_HOME_UTILITIES.ru.md
23_BATCH_011_FOOD_COOKING_PRESERVATION_KITCHENS.ru.md
24_BATCH_012_MINING_ENERGY_INDUSTRIAL_SYSTEMS.ru.md
25_BATCH_013_AGRICULTURE_LIVESTOCK_FORESTRY_FISHERIES.ru.md
26_BATCH_014_APPAREL_TEXTILES_FOOTWEAR_PERSONAL_GOODS.ru.md
27_BATCH_015_EDUCATION_KNOWLEDGE_WORK_COMMUNICATION.ru.md
28_BATCH_016_MEASUREMENT_TOOLS_REPAIR_MAINTENANCE.ru.md
29_BATCH_017_COMPUTING_DATA_AI_COMMUNICATIONS.ru.md
30_BATCH_018_HOME_FURNITURE_APPLIANCES_DOMESTIC_LIFE.ru.md
31_BATCH_019_CIVIC_GOVERNANCE_PUBLIC_SERVICES_EMERGENCY.ru.md
32_BATCH_020_BODY_SPORTS_ERGONOMICS_DAILY_CARE.ru.md
33_BATCH_021_RESEARCH_LAB_STANDARDS_EVIDENCE.ru.md
34_BATCH_022_BUSINESS_OPERATIONS_MARKETING_HR.ru.md
35_BATCH_023_CULTURE_MEDIA_LANGUAGE_HISTORY.ru.md
36_BATCH_024_GEOGRAPHY_GIS_NAVIGATION_CLIMATE_REGIONS.ru.md
37_BATCH_025_CHEMICAL_PRODUCTS_COSMETICS_DETERGENTS.ru.md
38_BATCH_026_ARCHITECTURE_URBAN_HOUSING_INTERIOR.ru.md
39_BATCH_027_PSYCHOLOGY_COGNITION_SOCIAL_BEHAVIOR.ru.md
40_BATCH_028_LAW_RIGHTS_CONTRACTS_CONSUMER_DATA.ru.md
41_BATCH_029_SYSTEMS_MODELS_CAUSAL_THINKING.ru.md
42_BATCH_030_METALWORK_MACHINING_FABRICATION.ru.md
43_BATCH_031_ELECTRONICS_DEVICES_MICROCHIPS_ROBOTICS.ru.md
44_BATCH_032_MEDICINE_CLINICAL_SYSTEMS_PUBLIC_HEALTH.ru.md
45_BATCH_033_PHILOSOPHY_ETHICS_MEANING_REASONING.ru.md
46_BATCH_034_FINANCE_ACCOUNTING_INSURANCE_TAXES.ru.md
47_BATCH_035_SECURITY_DEFENSE_RISK_SAFETY_SYSTEMS.ru.md
48_BATCH_036_AUTOMOTIVE_VEHICLES_MAINTENANCE.ru.md
49_BATCH_037_RAIL_MARINE_AEROSPACE_HEAVY_EQUIPMENT.ru.md
50_BATCH_038_PACKAGING_PRINTING_CONSUMER_GOODS.ru.md
51_BATCH_039_RETAIL_HOSPITALITY_TOURISM_SERVICE_OPERATIONS.ru.md
52_BATCH_040_APPLIED_MATH_DECISION_QUANTITATIVE_LIFE.ru.md
53_BATCH_041_AUDIO_MUSIC_STAGE_EVENTS_PRODUCTION.ru.md
54_BATCH_042_SPACE_ASTRONOMY_TIME_SATELLITES.ru.md
55_BATCH_043_GEOLOGY_MINERALS_SOIL_GEOTECH.ru.md
56_BATCH_044_CONSTRUCTION_TRADES_PLUMBING_ELECTRICAL_HVAC.ru.md
57_BATCH_045_FOOD_AGRO_INDUSTRIAL_PROCESSING_SUPPLY.ru.md
58_BATCH_046_TEXTILES_ADVANCED_DYES_FASHION_SUPPLY.ru.md
59_BATCH_047_WOOD_PAPER_FOREST_PRODUCTS_FURNITURE.ru.md
60_BATCH_048_PHARMA_MEDICINES_HERBAL_BOTANICAL_HEALTH_PRODUCTS.ru.md
61_BATCH_049_CROPS_HERBS_HORTICULTURE_PLANT_USES.ru.md
62_BATCH_050_CERAMICS_GLASS_CEMENT_LIME_BUILDING_MATERIALS.ru.md
63_BATCH_051_POWER_GRID_ELECTRIFICATION_UTILITIES_FIELD_OPS.ru.md
64_BATCH_052_MANUFACTURING_FACTORY_DESIGN_LEAN_QUALITY_MAINTENANCE.ru.md
65_BATCH_053_INTERNATIONAL_TRADE_CUSTOMS_LOGISTICS_LAW.ru.md
66_BATCH_054_PERSONAL_KNOWLEDGE_MEMORY_NOTES_LEARNING_SYSTEMS.ru.md
67_BATCH_055_OFFICE_ADMIN_PROJECT_MANAGEMENT_DOCUMENT_WORKFLOWS.ru.md
68_BATCH_056_PUBLIC_INFRASTRUCTURE_ROADS_BRIDGES_TUNNELS_DRAINAGE.ru.md
69_BATCH_057_WASTE_RECYCLING_CIRCULAR_ECONOMY_SANITATION.ru.md
70_BATCH_058_WATER_TREATMENT_IRRIGATION_HYDROLOGY_FLOOD_CONTROL.ru.md
71_BATCH_059_CLOTHING_FOOTWEAR_LEATHER_LAUNDRY_REPAIR.ru.md
```

Текущая контрольная точка:

```text
current IDs: 21173
duplicate IDs: 0
remaining to 50000: 28827
last batch: 462_BATCH_450_CRISIS_VITAL_RECORDS_FEE_WAIVER_SUPPORT.ru.md
coverage state: MVP seed exceeded, 50K collection in Layer 5 detail expansion
new Layer 5 coverage: contract clause details; engineering calculation limits; language grammar details; metrology/tolerance/QC detail; material degradation; condition monitoring; civic systems; evidence/records procedure; material selection; industrial utilities; service operations; educational assessment; climate adaptation; building envelope/moisture; warehouse logistics; data governance; agriculture operations; textile defects and QA; food plant sanitation and allergen control; treasury cash and liquidity; public procurement and grants; cybersecurity incident response; laboratory quality/calibration; fleet maintenance and dispatch; building commissioning and handover; insurance claims/underwriting; HR workforce/payroll controls; environmental permitting and compliance monitoring; nonprofit/public program monitoring; airport ground operations; retail cash/loss prevention controls; utilities outage restoration; seaport terminal/yard operations; hotel housekeeping/facility operations; construction site logistics/safety; manufacturing changeover/line clearance; cold-chain distribution; library/archive operations; public transit control; wastewater treatment plant operations; postal/parcel operations; elevator/escalator service operations; broadcast/media playout operations; parking/curb management; veterinary clinic operations; pharmacy operations; call center quality operations; event venue operations; dental clinic operations; cleaning/janitorial services; print shop operations; laboratory animal facility operations; museum exhibition operations; court clerk operations; fire prevention inspection operations; mortgage/loan servicing operations; property management/leasing; corporate travel operations; procurement card controls; facilities energy management; subscription billing operations; identity and access management operations; records management operations; industrial laundry operations; mailroom/document scanning operations; laboratory sample logistics operations; field service installation operations; food retail fresh department operations; outpatient front desk operations; school administration operations; rental equipment fleet operations; restaurant front-of-house operations; home care agency operations; municipal permit counter operations; equipment calibration service operations; catering event production operations; security guard operations; funeral home operations; landscaping service operations; ophthalmology clinic operations; radiology imaging center operations; physical therapy clinic operations; pest control service operations; self-storage facility operations; urgent care clinic operations; veterinary boarding operations; car wash operations; appliance repair service operations; dialysis center operations; auto body repair shop operations; locksmith service operations; moving company operations; courier messenger operations; commercial kitchen equipment service operations; coworking space operations; marina operations; laundromat operations; pet grooming operations; boatyard repair operations; crematory operations; appliance retail delivery operations; mobile phone repair operations; community recreation center operations; blood donation center operations; public swimming pool operations; fitness club operations; theater box office and usher operations; farmers market operations; public library programming operations; vehicle inspection station operations; campground operations; funeral cemetery operations; public park maintenance operations; public housing maintenance operations; animal shelter operations; food bank warehouse operations; street maintenance operations; solid waste collection operations; recycling center operations; community health outreach operations; public records request operations; water meter utility operations; unemployment benefits office operations; disaster relief distribution operations; election polling place operations; voter registration office operations; public defender intake operations; probation office operations; courthouse security operations; jail booking operations; legal aid clinic operations; juvenile services intake operations; court interpreter scheduling operations; victim services office operations; civil process service operations; mediation center operations; public health inspection operations; restaurant inspection operations; building code inspection operations; occupational safety inspection operations; environmental health sampling operations; housing habitability inspection operations; fire code inspection operations; elevator inspection program operations; public works asset management operations; stormwater inspection operations; bridge inspection operations; traffic sign inventory operations; traffic signal maintenance operations; pavement management operations; sidewalk inspection operations; road closure permit operations; transit stop maintenance operations; bike lane maintenance operations; streetlight maintenance operations; snow and ice control operations; street sweeping operations; catch basin maintenance operations; urban forestry work order operations; pavement marking operations; municipal drainage complaint operations; public playground inspection operations; road shoulder maintenance operations; traffic calming operations; school crossing guard operations; public restroom maintenance operations; municipal sign shop operations; roadway guardrail maintenance operations; street furniture maintenance operations; municipal fountain maintenance operations; public plaza operations; pedestrian wayfinding operations; public art maintenance operations; dog park operations; trail maintenance operations; outdoor market sanitation operations; community garden operations; urban farm operations; compost site operations; tree nursery operations; seed library operations; native plant restoration operations; invasive plant management operations; irrigation district field operations; emergency shelter supply inventory operations; disaster field kitchen sanitation inspection operations; emergency commodity point-of-distribution operations; disaster household cleanup kit distribution operations; emergency shelter registration data quality operations; disaster welfare check operations; emergency pet food and supply distribution operations; post-disaster mold remediation referral operations; emergency shelter accessibility accommodation tracking operations; disaster lost document replacement support operations; crisis transportation assistance operations; emergency clothing distribution operations; emergency prescription refill support operations; disaster benefits navigation desk operations; emergency childcare support operations; disaster repair volunteer work order coordination operations; disaster home cleanup volunteer safety briefing operations; emergency appliance replacement assistance operations; crisis rent and utility assistance intake operations; disaster legal clinic appointment operations; disaster tenant habitability documentation support operations; emergency school enrollment assistance operations; recovery grant application document review operations; disaster small business recovery intake operations; farm disaster assistance intake operations; livestock emergency feed support operations; community tool lending library operations; disaster volunteer interpreter scheduling operations; disaster community information kiosk operations; emergency public charging station operations; disaster cooling supply distribution operations; recovery peer support group coordination operations; disaster laundry voucher operations; emergency sanitation supply kit operations; crisis document translation request handling operations; disaster senior outreach visit scheduling operations; disaster mobile shower voucher operations; emergency baby supply distribution operations; recovery job placement intake operations; crisis fuel voucher controls operations; disaster temporary mail pickup operations; emergency public Wi-Fi access support operations; recovery household budget counseling intake operations; crisis disability equipment repair coordination operations; disaster prescription delivery route coordination operations; emergency pet shelter volunteer shift operations; disaster food truck/mobile meal route operations; crisis replacement eyewear assistance operations; disaster home accessibility modification requests; crisis pet medication support operations; recovery volunteer mentor matching operations; emergency replacement hearing aid assistance operations; disaster durable medical equipment lending operations; emergency replacement phone access assistance operations; recovery school supply kit distribution operations; crisis legal document notarization support operations; disaster temporary ID appointment support operations; emergency communication board distribution operations; recovery tutoring intake coordination operations; crisis vital records fee waiver support operations
latest added: disaster temporary ID appointment support operations; emergency communication board distribution operations; recovery tutoring intake coordination operations; crisis vital records fee waiver support operations
```

### P1 — практическое умение

1. дороги и строительство;
2. электроника и микропроцессоры;
3. машины и механизмы;
4. энергетика;
5. бытовая химия;
6. ремонт и материалы;
7. сельское хозяйство и питание.

### P2 — расширение мышления

1. философия науки;
2. этика;
3. экономика и право;
4. история технологий;
5. cross-domain bridges;
6. negative knowledge;
7. temporal knowledge.

---

## 🛡️ Правило истины

Каждая запись должна отвечать на вопросы:

```text
Что утверждается?
Где это верно?
Где это не верно?
Какой тип знания?
Насколько уверены?
Есть ли риск?
С чем связано?
Может ли это стать L3-фактом?
```

Если ответов нет — это не канон, а черновик.

---

## ✅ Итог

World Skills Core — это не замена LLM.

Это опора для LLM:

```text
Knowledge Core = что известно
Logic = как выводить
Noetic / Essence = что главное
LLM = как объяснить человеку
Truth Gate = что можно утверждать
```

Так система становится не просто разговорной, а **понимающей связи между наукой, техникой, человеком и реальной жизнью**.
