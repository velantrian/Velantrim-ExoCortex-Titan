# BATCH_113 — Common Diseases & Conditions Reference (Educational)
# world_skills_core · source: world_skills_core:batch_113:disease_reference
# KnowledgeUnits: 44
# ВНИМАНИЕ: общеобразовательная справка, НЕ диагностика и НЕ лечение. При симптомах — к врачу.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| disease.concept.acute_chronic | Острые и хронические болезни | invariant | внезапные краткие vs длительные | разные подходы |
| disease.concept.infectious | Инфекционные болезни | invariant | вызваны патогенами, передаются | профилактика, изоляция |
| disease.concept.noncommunicable | Неинфекционные болезни (НИЗ) | invariant | ССЗ, рак, диабет, ХОБЛ — ведущая причина смерти | образ жизни |
| disease.cardio.hypertension | Гипертония | variant | стойко повышенное давление; «тихий убийца» | контроль давления |
| disease.cardio.heart_attack | Инфаркт миокарда | invariant | гибель участка сердца из-за закупорки | срочная помощь, FAST не для сердца |
| disease.cardio.stroke | Инсульт | invariant | нарушение кровотока мозга; признаки FAST | время = мозг |
| disease.cardio.atherosclerosis | Атеросклероз | variant | бляшки сужают артерии | основа ССЗ |
| disease.metab.diabetes1 | Диабет 1 типа | variant | аутоиммунный, нужен инсулин | пожизненный контроль |
| disease.metab.diabetes2 | Диабет 2 типа | variant | инсулинорезистентность; связан с образом жизни | питание, активность |
| disease.metab.obesity | Ожирение | variant | избыток жира; фактор риска многих болезней | образ жизни |
| disease.resp.asthma | Астма | variant | хроническое воспаление дыхательных путей | ингаляторы, триггеры |
| disease.resp.copd | ХОБЛ | variant | хроническая обструкция; курение — главная причина | отказ от курения |
| disease.resp.pneumonia | Пневмония | variant | воспаление лёгких (бактерии/вирусы) | лечение по причине |
| disease.resp.flu | Грипп | invariant | вирусная инфекция; вакцинация ежегодно | профилактика |
| disease.resp.cold | Простуда (ОРВИ) | invariant | вирусная; проходит сама, симптоматика | гигиена |
| disease.infect.covid | COVID-19 | variant | вирус SARS-CoV-2; вакцины, маски, гигиена | пандемия 2020+ |
| disease.infect.tuberculosis | Туберкулёз | variant | бактерия, поражает лёгкие; лечится антибиотиками | курс лечения важен |
| disease.infect.hiv | ВИЧ/СПИД | variant | поражает иммунитет; терапия превращает в хроническое | профилактика, АРТ |
| disease.infect.hepatitis | Гепатиты A/B/C | variant | воспаление печени; вакцины от A и B | профилактика |
| disease.infect.malaria | Малярия | variant | паразит, переносится комарами | защита от укусов |
| disease.infect.foodborne | Кишечные инфекции | invariant | сальмонелла, кишечная палочка; гигиена пищи | безопасность еды |
| disease.cancer.concept | Рак | invariant | Рак: неконтролируемое деление клеток | ранняя диагностика |
| disease.cancer.common | Распространённые виды | variant | лёгкие, грудь, простата, толстая кишка, кожа | скрининг |
| disease.cancer.risk | Факторы риска рака | variant | курение, UV, инфекции, наследственность | профилактика |
| disease.cancer.screening | Скрининг рака | variant | маммография, колоноскопия, мазок | раннее выявление спасает |
| disease.mental.depression | Депрессия | variant | стойкое сниженное настроение; излечима | помощь, не слабость |
| disease.mental.anxiety | Тревожные расстройства | variant | чрезмерная тревога; распространены | терапия, поддержка |
| disease.neuro.alzheimer | Болезнь Альцгеймера | variant | прогрессирующая деменция | уход, поддержка |
| disease.neuro.parkinson | Болезнь Паркинсона | variant | дрожь, скованность; дофамин | лечение симптомов |
| disease.neuro.epilepsy | Эпилепсия | variant | повторяющиеся судороги | первая помощь при приступе |
| disease.neuro.migraine | Мигрень | variant | сильная головная боль, триггеры | управление |
| disease.musculo.arthritis | Артрит | variant | воспаление суставов (остео-, ревматоидный) | подвижность, лечение |
| disease.musculo.osteoporosis | Остеопороз | variant | хрупкость костей; кальций, активность | профилактика переломов |
| disease.digest.ulcer | Язва желудка | variant | часто из-за H. pylori; лечится | диагностика |
| disease.digest.ibs | Синдром раздражённого кишечника | variant | функциональное расстройство | диета, стресс |
| disease.allergy.concept | Аллергия | invariant | иммунная реакция на безвредное | избегание, антигистамины |
| disease.allergy.anaphylaxis | Анафилаксия | invariant | тяжёлая аллергическая реакция, угроза жизни | адреналин, срочная помощь |
| disease.autoimmune.concept | Аутоиммунные болезни | variant | Аутоиммунность: иммунитет атакует собственные ткани | хроническое управление |
| disease.skin.common | Кожные болезни | variant | экзема, псориаз, акне, дерматит | дерматолог |
| disease.eye.common | Болезни глаз | variant | катаракта, глаукома, близорукость | офтальмолог |
| disease.prevention.vaccination | Вакцинация | invariant | предотвращает инфекции, коллективный иммунитет | профилактика |
| disease.prevention.lifestyle | Профилактика образом жизни | invariant | питание, движение, сон, без курения | большинство НИЗ предотвратимы |
| disease.prevention.hygiene | Гигиена | invariant | мытьё рук, чистая вода, санитария | снижение инфекций |
| disease.warning.see_doctor | Когда срочно к врачу | invariant | боль в груди, одышка, признаки инсульта, высокая температура | спасение жизни |
