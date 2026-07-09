# 🌾 Batch 001 — Agro, Food, Medicinal Plants & Textile Foundation

**Язык:** русский  
**Статус:** 50K batch 001 / seed units / не L3 truth  
**Цель:** начать массовый практический сбор с растений, еды, текстиля и сырья, потому что это один из корневых слоёв цивилизации: еда, одежда, лекарства, красители, волокна, фабрики, хранение и безопасность.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `agro.crop.wheat.grain_use` | MATERIAL_SOURCE | Пшеница даёт зерно для муки, хлеба, макарон и кормов. | Качество зависит от сорта, белка, климата, хранения. | food.flour |
| `agro.crop.wheat.gluten_quality` | PROPERTY | Клейковина пшеницы влияет на упругость теста и хлебопекарные свойства. | Не вся пшеница одинаково подходит для хлеба. | baking |
| `agro.crop.rice.paddy_system` | PROCESS | Рис часто выращивают на затопляемых полях для контроля воды и сорняков. | Не все сорта требуют постоянного затопления. | irrigation |
| `agro.crop.maize.uses` | MATERIAL_SOURCE | Кукуруза используется как пища, корм, крахмал, масло и сырьё для биоэтанола. | Назначение зависит от сорта и переработки. | food, industry |
| `agro.crop.barley.malting` | PROCESS | Ячмень проращивают и сушат для получения солода. | Важны всхожесть, ферменты, влажность, температура. | brewing |
| `agro.crop.oats.food_feed` | MATERIAL_SOURCE | Овёс используют для круп, хлопьев, кормов и пищевых волокон. | Качество зависит от очистки и обработки. | nutrition |
| `agro.crop.rye.bread` | MATERIAL_SOURCE | Рожь используется для хлеба, особенно в холодных регионах. | Тесто ведёт себя иначе из-за другого белкового состава. | baking |
| `agro.legume.soybean.protein_oil` | MATERIAL_SOURCE | Соя даёт белок, масло, корм и сырьё для пищевой промышленности. | Требует обработки из-за антипитательных факторов. | food, feed |
| `agro.legume.pea.nitrogen_fixation` | MECHANISM | Горох и другие бобовые улучшают азотный баланс через симбиоз с бактериями. | Зависит от почвы, инокуляции и условий. | soil |
| `agro.legume.lentil.food` | MATERIAL_SOURCE | Чечевица — источник растительного белка и крахмала. | Требует очистки, сортировки, варки. | food |
| `agro.oilseed.sunflower.oil` | MATERIAL_SOURCE | Подсолнечник выращивают ради семян и масла. | Масличность зависит от сорта и условий. | oil_processing |
| `agro.oilseed.rapeseed.oil` | MATERIAL_SOURCE | Рапс даёт пищевое и техническое масло. | Нужны сорта с контролем нежелательных соединений. | biodiesel |
| `agro.oilseed.flax.oil_fiber` | MATERIAL_SOURCE | Лён может давать масло из семян и волокно из стеблей. | Масличные и волокнистые сорта различаются. | textile.linen |
| `agro.root.potato.starch` | MATERIAL_SOURCE | Картофель даёт пищу и крахмал для пищевой/технической переработки. | Хранение требует контроля температуры и прорастания. | food |
| `agro.root.sugar_beet.sugar` | MATERIAL_SOURCE | Сахарная свёкла используется для получения сахара. | Сахаристость зависит от сорта, почвы, климата. | sugar_processing |
| `agro.crop.sugarcane.sugar_bagasse` | MATERIAL_SOURCE | Сахарный тростник даёт сахарный сок и багассу как побочный материал/топливо. | Тропическая культура; быстро перерабатывается после срезки. | sugar |
| `agro.crop.cassava.starch` | MATERIAL_SOURCE | Маниок даёт крахмал и пищу в тропиках. | Некоторые сорта требуют обработки для снижения токсичных соединений. | food_safety |
| `agro.crop.cotton.fiber_seed` | MATERIAL_SOURCE | Хлопок даёт волокно для текстиля и семена для масла/корма после обработки. | Волокно требует джинирования; вредители и вода критичны. | textile.cotton |
| `agro.crop.flax.fiber` | MATERIAL_SOURCE | Стебли льна дают прочное волокно для ткани и технических материалов. | Требуются retting, трепание, чесание. | textile.linen |
| `agro.crop.hemp.fiber` | MATERIAL_SOURCE | Конопля даёт прочное волокно, костру и семена. | Правовой статус зависит от содержания THC и юрисдикции. | textile.hemp |
| `agro.crop.jute.fiber` | MATERIAL_SOURCE | Джут даёт грубое волокно для мешков, канатов и упаковки. | Лучше подходит для влажных тропиков. | packaging |
| `agro.crop.sisal.fiber` | MATERIAL_SOURCE | Сизаль даёт жёсткое волокно из листьев. | Используется для канатов, матов, композитов. | fiber |
| `agro.crop.bamboo.material` | MATERIAL_SOURCE | Бамбук даёт быстрорастущий строительный и ремесленный материал. | Требует защиты от влаги, насекомых, растрескивания. | construction |
| `agro.crop.cork.oak` | MATERIAL_SOURCE | Пробковый дуб даёт кору для пробки без полной вырубки дерева. | Сбор требует циклов восстановления коры. | materials |
| `agro.crop.natural_rubber.latex` | MATERIAL_SOURCE | Каучуконосные растения дают латекс для натуральной резины. | Требует коагуляции и обработки. | rubber |
| `agro.crop.indigo.dye` | DYE_SOURCE | Индигоносные растения дают синий краситель после ферментации/окисления. | Процесс зависит от вида растения и технологии vat dye. | textile.dye |
| `agro.crop.madder.red_dye` | DYE_SOURCE | Марена даёт красные красители из корней. | Цвет зависит от mordant и условий. | pigments |
| `agro.crop.woad.blue_dye` | DYE_SOURCE | Вайда исторически использовалась как источник синего красителя. | Замещалась индиго; требует обработки листьев. | dye |
| `agro.crop.turmeric.dye_spice` | DYE_SOURCE | Куркума даёт жёлтый пигмент и специю. | Цвет не всегда светостоек в текстиле. | food, dye |
| `agro.crop.saffron.dye_spice` | MATERIAL_SOURCE | Шафран даёт специю и краситель из рылец цветка. | Очень трудоёмкий сбор; высокая стоимость. | food, dye |
| `plant.medicinal.peppermint` | MATERIAL_SOURCE | Мята перечная используется как ароматическое и традиционно пищеварительное растение. | Возможны противопоказания; medical claims требуют источников. | herbs |
| `plant.medicinal.sage` | MATERIAL_SOURCE | Шалфей используют как ароматическое и традиционное лекарственное растение. | Состав и риски зависят от вида и дозы. | herbs |
| `plant.medicinal.valerian` | MATERIAL_SOURCE | Валериана традиционно используется для седативных целей. | Возможны взаимодействия; evidence и дозы требуют источников. | health_safety |
| `plant.medicinal.st_johns_wort` | MATERIAL_SOURCE | Зверобой содержит соединения, влияющие на лекарственные взаимодействия. | Высокий риск взаимодействий с препаратами; нужна осторожность. | medicine_safety |
| `plant.medicinal.lavender` | MATERIAL_SOURCE | Лаванда даёт эфирное масло и ароматическое сырьё. | Эфирные масла могут раздражать кожу/дыхание. | cosmetics |
| `plant.medicinal.thyme` | MATERIAL_SOURCE | Тимьян содержит ароматические соединения и используется в пище/традиционных средствах. | Концентрированные масла требуют осторожности. | food, herbs |
| `plant.medicinal.aloe_vera` | MATERIAL_SOURCE | Алоэ используют в косметике и традиционных средствах для кожи. | Пероральное применение и extracts требуют осторожности. | cosmetics |
| `plant.medicinal.calendula` | MATERIAL_SOURCE | Календула используется в косметике и традиционных наружных средствах. | Возможны аллергии. | herbs |
| `plant.medicinal.nettle` | MATERIAL_SOURCE | Крапива используется как пищевое, волокнистое и традиционное растение. | Сбор требует защиты от жгучих волосков. | textile, food |
| `plant.medicinal.yarrow` | MATERIAL_SOURCE | Тысячелистник традиционно используют как лекарственное растение. | Evidence и безопасность зависят от применения. | herbs |
| `food.process.milling.grain_to_flour` | PROCESS | Помол превращает зерно в муку, отделяя и измельчая части. | Степень помола влияет на питательность и свойства теста. | wheat |
| `food.process.sieving.flour_fraction` | PROCESS | Просеивание разделяет муку по размеру частиц и удаляет примеси. | Не заменяет санитарный контроль. | milling |
| `food.process.bread.yeast_fermentation` | PROCESS | Дрожжи производят CO₂ и ароматические соединения, разрыхляя тесто. | Зависит от температуры, сахаров, соли, времени. | baking |
| `food.process.bread.gluten_network` | MECHANISM | Замес развивает клейковинную сеть, удерживающую газ. | Рожь и безглютеновые смеси требуют других механизмов. | wheat |
| `food.process.pasta.durum_semolina` | PROCESS | Пасту часто делают из semolina твёрдой пшеницы и воды с сушкой. | Качество зависит от белка, замеса, сушки. | wheat |
| `food.process.rice.milling` | PROCESS | Шлифовка риса удаляет оболочки и отруби. | Белый рис хранится иначе, но теряет часть nutrients. | rice |
| `food.process.oil.pressing` | PROCESS | Масло получают механическим прессованием семян/плодов. | Выход зависит от сырья, температуры, подготовки. | oilseed |
| `food.process.oil.extraction` | PROCESS | Растворительная экстракция повышает выход масла. | Требует контроля растворителя и безопасности. | industry |
| `food.process.oil.refining` | PROCESS | Рафинация удаляет примеси, запахи, свободные кислоты и пигменты. | Может менять состав и свойства масла. | food |
| `food.process.sugar.extraction_beet` | PROCESS | Сахар из свёклы получают диффузией, очисткой сока, выпариванием и кристаллизацией. | Требует энергии, воды и контроля примесей. | sugar |
| `food.process.sugar.cane_crushing` | PROCESS | Тростник измельчают и отжимают для получения сока. | Быстрая переработка снижает потери сахара. | sugarcane |
| `food.process.fermentation.lactic` | PROCESS | Молочнокислое брожение снижает pH и помогает сохранению продуктов. | Не гарантирует безопасность без контроля. | yogurt, vegetables |
| `food.process.fermentation.alcoholic` | PROCESS | Алкогольное брожение превращает сахара в этанол и CO₂. | Требует дрожжей и контроля загрязнений. | brewing |
| `food.process.cheese.coagulation` | PROCESS | Сыр начинается с коагуляции молока кислотой/ферментом. | Тип сыра зависит от культуры, соли, влаги, выдержки. | dairy |
| `food.process.yogurt.culture` | PROCESS | Йогурт получают ферментацией молока выбранными культурами. | Температура и чистота критичны. | dairy |
| `food.process.meat.curing` | PROCESS | Соление/нитритное curing снижает риск порчи и меняет вкус/цвет. | Ошибки дозировки опасны; нужны нормы. | food_safety |
| `food.process.smoking` | PROCESS | Копчение добавляет вкус и может снижать влажность/микробную активность. | Дым содержит потенциально вредные соединения; нужен контроль. | preservation |
| `food.process.canning.heat` | PROCESS | Консервирование уничтожает/инактивирует микроорганизмы теплом и герметизацией. | Низкокислотные продукты требуют строгого режима из-за botulism risk. | food_safety |
| `food.process.drying` | PROCESS | Сушка снижает активность воды, замедляя рост микроорганизмов. | Нужна защита от повторного увлажнения. | preservation |
| `food.process.freezing` | PROCESS | Заморозка замедляет микробный рост и реакции. | Не стерилизует продукт. | preservation |
| `food.process.pasteurization` | PROCESS | Пастеризация снижает микробную нагрузку нагревом. | Не равна стерилизации. | dairy |
| `food.process.sterilization` | PROCESS | Стерилизация направлена на уничтожение жизнеспособных микроорганизмов. | Может ухудшать качество продукта. | food_safety |
| `food.safety.water_activity` | CONSTRAINT | Активность воды влияет на рост микроорганизмов. | Не равна общей влажности. | preservation |
| `food.safety.cold_chain` | SAFETY_RULE | Холодовая цепь удерживает скоропортящиеся продукты в безопасном температурном диапазоне. | Разрыв цепи повышает риск порчи. | logistics |
| `food.quality.haccp` | METHOD | HACCP анализирует опасности и критические контрольные точки в пищевом производстве. | Требует документированного процесса. | safety |
| `textile.process.cotton.ginning` | PROCESS | Джинирование отделяет хлопковое волокно от семян. | Повреждение волокна снижает качество. | cotton |
| `textile.process.cotton.card` | PROCESS | Кардочесание расправляет и частично ориентирует волокна. | Не полностью выравнивает как гребнечесание. | spinning |
| `textile.process.combing` | PROCESS | Гребнечесание удаляет короткие волокна и улучшает ровность пряжи. | Повышает качество, но уменьшает выход. | yarn |
| `textile.process.drawing` | PROCESS | Вытягивание выравнивает ленту и смешивает волокна. | Требует контроля равномерности. | spinning |
| `textile.process.roving` | PROCESS | Ровница подготавливает волокнистую ленту к прядению. | Используется не во всех системах. | yarn |
| `textile.process.spinning.ring` | PROCESS | Кольцевое прядение скручивает волокна в прочную пряжу. | Медленнее некоторых систем, но даёт качество. | yarn |
| `textile.process.spinning.open_end` | PROCESS | Open-end прядение быстрее для некоторых типов пряжи. | Обычно даёт другие свойства, чем ring-spun. | yarn |
| `textile.process.weaving.warp_weft` | PROCESS | Ткачество переплетает основу и уток. | Плотность и переплетение определяют свойства ткани. | fabric |
| `textile.process.knitting.loops` | PROCESS | Текстиль: Вязание создаёт полотно из петель. | Эластичнее многих тканых материалов. | clothing |
| `textile.process.nonwoven.bonding` | PROCESS | Нетканые материалы соединяют волокна без ткачества/вязания. | Методы: механический, термический, химический bonding. | filters |
| `textile.process.retting.flax` | PROCESS | Retting льна разрушает связи между волокном и стеблем. | Переразложение портит волокно. | linen |
| `textile.process.scutching.flax` | PROCESS | Трепание отделяет древесные части стебля от льняного волокна. | После retting. | linen |
| `textile.process.hackling.flax` | PROCESS | Чесание льна выравнивает волокна и удаляет остатки. | Качество влияет на тонкость пряжи. | linen |
| `textile.process.wool.scouring` | PROCESS | Промывка шерсти удаляет жир, грязь и растительные примеси. | Сточные воды требуют контроля. | wool |
| `textile.process.wool.carding` | PROCESS | Шерсть кардочешут для подготовки к прядению. | Система зависит от типа пряжи. | wool |
| `textile.process.silk.reeling` | PROCESS | Шёлковую нить разматывают из коконов после подготовки. | Трудоёмкий процесс; влияет на непрерывность нити. | silk |
| `textile.process.dyeing.mordant` | PROCESS | Протрава помогает красителю закрепиться на волокне. | Mordant может быть токсичным; нужен контроль. | dye |
| `textile.process.vat_dyeing` | PROCESS | Vat dyeing переводит нерастворимый краситель в растворимую форму, затем окисляет на волокне. | Типично для индиго. | indigo |
| `textile.process.printing` | PROCESS | Печать наносит рисунок/краситель локально на ткань. | Требует фиксации и промывки. | fabric |
| `textile.finish.mercerization` | PROCESS | Мерсеризация хлопка улучшает блеск, прочность и окрашиваемость. | Использует щёлочь; требует safety. | cotton |
| `textile.finish.sanforization` | PROCESS | Санфоризация снижает последующую усадку ткани. | Механическая отделка. | clothing |
| `textile.quality.yarn_count` | QUALITY_CHECK | Номер пряжи описывает тонкость/массу на длину. | Системы нумерации различаются. | textile |
| `textile.quality.tensile_strength` | QUALITY_CHECK | Прочность нити/ткани измеряет сопротивление разрыву. | Зависит от влажности и метода испытания. | quality |
| `textile.quality.colorfastness` | QUALITY_CHECK | Стойкость окраски показывает сопротивление стирке, свету, трению. | Разные тесты для разных воздействий. | dye |
| `textile.failure.pilling` | FAILURE_MODE | Пиллинг — образование катышков из-за трения и волокон. | Зависит от волокна, пряжи, отделки. | clothing |
| `textile.failure.shrinkage` | FAILURE_MODE | Усадка происходит при стирке/тепле/влаге из-за структуры волокон и ткани. | Контролируется отделкой и режимом ухода. | clothing |
| `textile.safety.dust` | SAFETY_RULE | Текстильная пыль опасна для дыхания и пожароопасна. | Нужны вентиляция, уборка, контроль источника. | factory_safety |

---

## 📊 Batch 001 summary

```text
new units: 92
main layers:
  agro crops
  medicinal / aromatic plants
  dye and fiber plants
  food processing
  textile processing
  quality checks
  safety rules
```
