# 👕 Batch 014 — Apparel, Textiles, Footwear & Personal Goods

**Язык:** русский  
**Статус:** 50K batch 014 / seed units / не L3 truth  
**Цель:** добавить практическую базу одежды, тканей, обуви, фабрик, качества, ухода, безопасности и цепочек поставок.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `apparel.fiber.cotton` | MATERIAL | Хлопок — целлюлозное волокно, мягкое и хорошо впитывающее влагу. | Сминается, садится, требует воды в агроцепочке. | textile |
| `apparel.fiber.wool` | MATERIAL | Шерсть — белковое волокно с теплоизоляцией и упругостью. | Может сваливаться и требовать деликатного ухода. | textile |
| `apparel.fiber.linen` | MATERIAL | Лён даёт прочную ткань с высокой влагопроводностью. | Сильно мнётся, качество зависит от волокна. | textile |
| `apparel.fiber.silk` | MATERIAL | Шёлк — белковое волокно с блеском и прочностью. | Чувствителен к свету, поту, уходу. | textile |
| `apparel.fiber.polyester` | MATERIAL | Полиэстер — синтетическое волокно с прочностью и низкой сминаемостью. | Может удерживать запахи и давать микроволокна. | polymers |
| `apparel.fiber.nylon` | MATERIAL | Нейлон прочен, эластичен и используется в одежде, сумках, технических тканях. | Чувствителен к теплу и UV. | polymers |
| `apparel.fiber.viscose` | MATERIAL | Вискоза — regenerated cellulose, мягкая и хорошо драпируется. | Прочность во влажном состоянии может снижаться. | textile |
| `apparel.yarn.spinning` | PROCESS | Прядение скручивает волокна в нить. | Длина и чистота волокна влияют на прочность. | textile |
| `apparel.yarn.twist` | PARAMETER | Крутка нити влияет на прочность, мягкость и внешний вид. | Слишком высокая крутка меняет драпировку. | textile |
| `apparel.fabric.weaving` | PROCESS | Ткачество переплетает нити основы и утка. | Тип переплетения влияет на прочность и вид. | textile |
| `apparel.fabric.knitting` | PROCESS | Вязание создаёт полотно из петель. | Обычно более эластично, чем тканое полотно. | textile |
| `apparel.fabric.nonwoven` | PROCESS | Нетканые материалы получают без прядения и ткачества, связывая волокна. | Используются в медицине, фильтрах, салфетках. | materials |
| `apparel.fabric.denim` | MATERIAL | Деним — прочная саржевая ткань, обычно хлопковая с окрашенной основой. | Износ и стирка меняют цвет. | apparel |
| `apparel.fabric.fleece` | MATERIAL | Fleece — ворсистый трикотаж, часто полиэстеровый, для утепления. | Может пилинговаться и выделять микроволокна. | apparel |
| `apparel.fabric.finishing` | PROCESS | Отделка ткани задаёт мягкость, усадку, водоотталкивание, огнестойкость. | Химия отделки влияет на экологию и кожу. | textile |
| `apparel.dye.reactive` | PROCESS | Реактивные красители химически связываются с целлюлозным волокном. | Требуют соли/щёлочи и промывки. | dyeing |
| `apparel.dye.disperse` | PROCESS | Дисперсные красители применяют для полиэстера и других синтетик. | Часто нужен нагрев/давление. | dyeing |
| `apparel.dye.vat` | PROCESS | Кубовые красители, включая индиго, восстанавливают и окисляют на волокне. | Технология требует контроля химии. | dyeing |
| `apparel.printing.digital` | PROCESS | Цифровая печать наносит рисунок без отдельного трафарета. | Подготовка ткани и чернила критичны. | textile_print |
| `apparel.printing.screen` | PROCESS | Трафаретная печать продавливает краску через сетку. | Хороша для тиражей и плотных цветов. | textile_print |
| `apparel.pattern.drafting` | METHOD | Построение выкройки переводит форму тела и дизайн в детали изделия. | Размерные прибавки критичны. | garment |
| `apparel.sizing` | SYSTEM | Размерная система связывает мерки тела с размерами одежды. | Отличается по странам, брендам, посадке. | retail |
| `apparel.cutting.marker` | METHOD | Раскладка лекал минимизирует отход ткани при раскрое. | Учитывает направление, рисунок, ворс. | factory |
| `apparel.sewing.stitch_lock` | METHOD | Lockstitch создаёт прочный стежок двумя нитями. | Часто используется в одежде. | sewing |
| `apparel.sewing.stitch_overlock` | METHOD | Overlock обмётывает край и соединяет трикотаж/ткани. | Предотвращает осыпание. | sewing |
| `apparel.seam_strength` | QUALITY_CHECK | Прочность шва зависит от ткани, нитки, стежка и припусков. | Проверяется растяжением и износом. | quality |
| `apparel.interlining` | MATERIAL | Прокладочные материалы стабилизируют воротники, манжеты и детали. | Клей и ткань должны быть совместимы. | garment |
| `apparel.buttons` | COMPONENT | Пуговицы — застёжки и декоративные элементы. | Риск отрыва важен для детской одежды. | apparel |
| `apparel.zipper` | COMPONENT | Молния соединяет две стороны через зубья и бегунок. | Качество зависит от материала, ленты, бегунка. | apparel |
| `apparel.elastic` | COMPONENT | Эластичные материалы возвращаются после растяжения. | Деградируют от тепла, UV, стирки. | garment |
| `apparel.quality.pilling` | FAILURE_MODE | Пиллинг — образование катышков от трения и слабых волокон. | Зависит от волокна, пряжи, отделки. | quality |
| `apparel.quality.shrinkage` | FAILURE_MODE | Усадка меняет размер изделия после стирки/сушки. | Контролируется предварительной обработкой. | quality |
| `apparel.quality.colorfastness` | QUALITY_CHECK | Colorfastness показывает устойчивость цвета к стирке, свету, поту, трению. | Требует тестов по назначению. | dye |
| `apparel.care_label` | INFORMATION | Ярлык ухода сообщает допустимую стирку, сушку, глажку и чистку. | Символы зависят от стандартов. | consumer |
| `apparel.repair.patch` | METHOD | Заплата восстанавливает ткань или усиливает слабое место. | Материал и шов должны подходить. | repair |
| `apparel.repair.darning` | METHOD | Штопка восстанавливает отверстия переплетением нитей. | Особенно полезна для носков и трикотажа. | repair |
| `footwear.last` | TOOL | Колодка задаёт форму обуви и посадку. | Размер, полнота и стиль зависят от неё. | footwear |
| `footwear.upper` | COMPONENT | Верх обуви удерживает стопу и задаёт внешний вид. | Материалы влияют на вентиляцию и износ. | footwear |
| `footwear.sole.rubber` | MATERIAL | Резиновая подошва даёт сцепление, амортизацию и износостойкость. | Состав влияет на холод, масло, мокрую поверхность. | footwear |
| `footwear.sole.leather` | MATERIAL | Кожаная подошва дышит и формуется, но чувствительна к воде. | Требует ухода и ремонта. | footwear |
| `footwear.stitchdown` | CONSTRUCTION | Stitchdown пришивает вывернутый верх к подошве/ранту. | Прочная ремонтопригодная конструкция. | footwear |
| `footwear.cemented_construction` | CONSTRUCTION | Клеевая обувь соединяет верх и подошву клеем. | Дешевле, но ремонтопригодность зависит от конструкции. | footwear |
| `footwear.goodyear_welt` | CONSTRUCTION | Goodyear welt соединяет верх, рант и подошву, облегчая замену подошвы. | Дороже и требует навыка. | footwear |
| `footwear.insole_support` | COMPONENT | Стелька и супинатор распределяют давление и поддерживают стопу. | Не лечит медицинские проблемы без специалиста. | ergonomics |
| `footwear.waterproof_membrane` | MATERIAL | Мембрана может блокировать жидкую воду и выпускать часть пара. | Эффективность зависит от конструкции и ухода. | outdoor |
| `footwear.sizing_fit` | QUALITY_CHECK | Посадка обуви зависит от длины, ширины, подъёма, носка и назначения. | Размерная цифра не гарантирует удобство. | consumer |
| `footwear.quality.flex_test` | QUALITY_CHECK | Испытание на изгиб проверяет долговечность подошвы и верха. | Условия должны соответствовать назначению. | quality |
| `apparel.ppe.high_visibility` | PPE | High-visibility одежда повышает заметность через цвет и отражатели. | Не заменяет безопасную организацию движения. | safety |
| `apparel.ppe.flame_resistant` | PPE | Огнестойкая одежда снижает риск воспламенения или ожогов. | Требует сертификации и правильного ухода. | industrial_safety |
| `apparel.ppe.cut_resistant` | PPE | Cut-resistant материалы снижают риск порезов. | Не защищают от всех острых инструментов. | safety |
| `apparel.outdoor.layering` | METHOD | Система слоёв управляет влагой, теплом и защитой от ветра/осадков. | Слои зависят от активности и климата. | outdoor |
| `apparel.thermal.insulation` | PROPERTY | Теплоизоляция одежды удерживает воздух и снижает теплопотери. | Влажность резко снижает эффективность многих утеплителей. | physics |
| `apparel.rainwear.dwr` | MATERIAL_TREATMENT | DWR помогает каплям скатываться с ткани. | Со временем стирается и требует восстановления. | outdoor |
| `apparel.hats.brim_sun` | SAFETY_DESIGN | Поля шляпы уменьшают воздействие солнца на лицо и глаза. | Не заменяет полный sun protection. | health |
| `apparel.gloves.dexterity` | DESIGN_CONSTRAINT | Перчатки балансируют защиту, тепло и ловкость пальцев. | Толстая защита снижает точность. | ergonomics |
| `apparel.bags.seam_reinforcement` | DESIGN_METHOD | Сумки усиливают швы и точки нагрузки для долговечности. | Слабое место часто ручки и углы. | design |
| `apparel.textile_recycling` | PROCESS | Переработка текстиля отделяет материалы для повторного волокна, ветоши или сырья. | Смесовые ткани сложнее перерабатывать. | circular_economy |
| `apparel.microfiber_shedding` | ENV_RISK | Синтетические ткани могут выделять микроволокна при стирке. | Зависит от ткани, стирки, фильтрации. | environment |
| `apparel.supply_chain.audit` | QUALITY_SYSTEM | Аудит цепочки проверяет фабрики, условия, документы и риски. | Аудит не гарантирует правду без follow-up. | labor |
| `apparel.factory.line_balance` | OPERATIONS | Балансировка линии распределяет операции, чтобы не создавать узкие места. | Зависит от времени операций и навыков. | manufacturing |
| `apparel.factory.needle_control` | SAFETY_SYSTEM | Контроль игл предотвращает попадание сломанных частей в изделие. | Критично для детской одежды и экспорта. | quality |
| `apparel.factory.ergonomics` | SAFETY_RULE | Швейное производство требует управления позой, повторяемостью и освещением. | Риск хронических травм. | labor |
| `apparel.factory.fire_safety` | SAFETY_SYSTEM | Текстильные фабрики имеют высокий риск пожара из-за ткани, пыли и людей. | Нужны выходы, сигнализация, обучение. | safety |
| `apparel.costing.bom` | METHOD | BOM перечисляет материалы изделия и их количество. | Основа себестоимости и закупок. | finance |
| `apparel.costing.cmt` | METHOD | CMT оценивает cut-make-trim стоимость производства одежды. | Не включает все overhead и логистику. | manufacturing |
| `apparel.design.tech_pack` | DOCUMENT | Tech pack описывает изделие для фабрики: мерки, материалы, швы, цвета. | Снижает ошибки между дизайнером и производством. | product |
| `apparel.luxury.craftsmanship` | QUALITY_MODEL | Ремесленное качество часто связано с материалом, ручными операциями и контролем деталей. | Не всегда равно функциональной прочности. | craft |
| `apparel.children.choking_hazard` | SAFETY_RULE | Мелкие детали на детской одежде могут быть choking hazard. | Требуются стандарты и испытания. | child_safety |
| `apparel.medical.compression_garment` | MEDICAL_PRODUCT | Компрессионные изделия создают заданное давление на тело. | Медицинское применение требует специалиста и стандартов. | health |
| `apparel.hygiene.laundering_temperature` | METHOD | Температура стирки влияет на очистку, ткань, энергию и гигиену. | Символы ухода и материал ограничивают режим. | household |

---

## 📊 Batch 014 summary

```text
new units: 70
main layers:
  fibers / yarn / fabric / dyeing
  garment production
  footwear construction
  quality, care, PPE and factory safety
```
