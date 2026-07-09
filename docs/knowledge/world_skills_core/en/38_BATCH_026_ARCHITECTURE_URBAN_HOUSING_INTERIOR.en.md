# 🏙️ Batch 026 — Architecture, Urban Housing & Interior Systems

**Язык:** русский  
**Статус:** 50K batch 026 / seed units / не L3 truth  
**Цель:** добавить практическую архитектуру: жильё, планировки, фасады, городская ткань, доступность, строительная логика и эксплуатация зданий.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `arch.site.context` | METHOD | Архитектура начинается с контекста участка: солнце, ветер, рельеф, доступ, соседи. | Игнорирование места создаёт дорогие ошибки. | planning |
| `arch.site.orientation` | DESIGN_METHOD | Ориентация здания влияет на свет, тепло и комфорт. | Оптимум зависит от климата. | climate |
| `arch.site.setback` | REGULATION | Отступы задают расстояние здания от границ участка или улицы. | Нормы зависят от города. | zoning |
| `arch.site.access` | DESIGN_CONSTRAINT | Доступ включает пешеходов, машины, сервисы, пожарных и людей с инвалидностью. | Конфликты потоков надо решать рано. | urban |
| `arch.site.drainage` | DESIGN_CONSTRAINT | Участок должен отводить воду от здания и соседей. | Плохой уклон разрушает фундамент и подвалы. | water |
| `arch.program` | DOCUMENT | Program описывает функции, площади, связи и пользователей здания. | Без программы дизайн становится догадкой. | requirements |
| `arch.bubble_diagram` | TOOL | Bubble diagram показывает связи помещений до точной геометрии. | Упрощает раннее планирование. | design |
| `arch.adjacency_matrix` | TOOL | Матрица смежности фиксирует, какие помещения должны быть рядом или раздельно. | Полезна для больниц, школ, производств. | planning |
| `arch.floorplan.circulation` | DESIGN_PRINCIPLE | Коридоры и проходы должны связывать зоны без лишних конфликтов. | Перебор коридоров теряет площадь. | interior |
| `arch.floorplan.flexibility` | DESIGN_PRINCIPLE | Гибкая планировка допускает изменение функций со временем. | Требует сетки, инженерных резервов и нейтральных зон. | housing |
| `arch.housing.daylight` | QUALITY | Естественный свет влияет на комфорт, энергию и восприятие пространства. | Блики и перегрев тоже возможны. | lighting |
| `arch.housing.cross_ventilation` | DESIGN_METHOD | Сквозное проветривание использует разность давления между фасадами. | Зависит от ветра, плана, шума, безопасности. | ventilation |
| `arch.housing.privacy_gradient` | DESIGN_PRINCIPLE | Жильё часто организуют от публичных зон к приватным. | Культура и образ жизни меняют границы. | sociology |
| `arch.housing.acoustic_privacy` | QUALITY | Звукоизоляция защищает сон, работу и личную жизнь. | Требует массы, герметичности, развязки конструкций. | acoustics |
| `arch.housing.storage_ratio` | DESIGN_CONSTRAINT | Достаточное хранение снижает беспорядок и перегруз жилой площади. | Нужны разные типы хранения. | home |
| `arch.housing.kitchen_triangle` | HEURISTIC | Kitchen triangle связывает мойку, плиту и холодильник. | Современные кухни не всегда следуют треугольнику. | kitchen |
| `arch.housing.bathroom_wet_zone` | DESIGN_METHOD | Ванная требует контроля воды, вентиляции, уклонов и гидроизоляции. | Малые протечки создают большие повреждения. | plumbing |
| `arch.housing.entry_transition` | DESIGN_PRINCIPLE | Входная зона переводит улицу в дом: обувь, одежда, грязь, безопасность. | Климат сильно влияет. | domestic |
| `arch.housing.balcony` | SPACE_TYPE | Балкон даёт наружное пространство, свет и вентиляцию. | Риски: мостики холода, вода, безопасность. | housing |
| `arch.housing.accessible_unit` | DESIGN_PRINCIPLE | Доступное жильё учитывает ширину, развороты, пороги, санузел и управление. | Лучше проектировать сразу, чем переделывать. | accessibility |
| `arch.structure.load_path` | PRINCIPLE | Load path показывает, как нагрузки идут от крыши/этажей к фундаменту. | Разрыв пути опасен. | structural |
| `arch.structure.grid` | DESIGN_TOOL | Конструктивная сетка упорядочивает колонны, пролёты и планировку. | Слишком жёсткая сетка мешает функциям. | engineering |
| `arch.structure.span` | CONSTRAINT | Пролёт влияет на материал, высоту балки, стоимость и гибкость. | Большие пролёты дороги. | structural |
| `arch.structure.shear_wall` | COMPONENT | Shear walls сопротивляются горизонтальным нагрузкам ветра/землетрясений. | Их нельзя произвольно удалять. | structural |
| `arch.structure.core` | COMPONENT | Ядро здания часто содержит лестницы, лифты и жёсткость. | Определяет план и эвакуацию. | highrise |
| `arch.envelope.wall_assembly` | SYSTEM | Стена как assembly включает несущий слой, тепло, влагу, воздух и отделку. | Ошибка слоя создаёт конденсат или плесень. | building_science |
| `arch.envelope.thermal_bridge` | FAILURE_MODE | Мостик холода проводит тепло через слабый участок оболочки. | Может вызывать конденсат. | energy |
| `arch.envelope.vapor_control` | DESIGN_METHOD | Пароизоляция/пароконтроль управляет миграцией влаги в стене. | Нужна климатическая логика. | building_science |
| `arch.envelope.air_barrier` | COMPONENT | Воздушный барьер снижает неконтролируемые утечки воздуха. | Должен быть непрерывным. | energy |
| `arch.envelope.rain_screen` | SYSTEM | Rainscreen отделяет облицовку от водозащитного слоя и даёт дренаж. | Требует вентиляционного зазора. | facade |
| `arch.facade.window_wall_ratio` | METRIC | Доля остекления влияет на свет, тепло, стоимость и комфорт. | Больше стекла не всегда лучше. | energy |
| `arch.facade.shading_device` | COMPONENT | Солнцезащита снижает перегрев и блики. | Внешняя часто эффективнее внутренней. | climate |
| `arch.facade.double_skin` | SYSTEM | Double-skin facade создаёт дополнительный слой воздуха и управления климатом. | Сложно и дорого в обслуживании. | facade |
| `arch.roof.flat_drainage` | DESIGN_CONSTRAINT | Плоская крыша всё равно требует уклонов и водоотвода. | Застой воды ускоряет повреждения. | roofing |
| `arch.roof.green_roof` | SYSTEM | Зелёная крыша удерживает воду, снижает перегрев и даёт экосистемные функции. | Требует несущей способности и ухода. | ecology |
| `arch.roof.solar_ready` | DESIGN_METHOD | Solar-ready roof учитывает ориентацию, тень, нагрузку и электрические пути. | Дешевле заложить заранее. | energy |
| `arch.fire.compartmentation` | SAFETY_SYSTEM | Противопожарные отсеки ограничивают распространение огня и дыма. | Проёмы и проходки должны быть защищены. | fire_safety |
| `arch.fire.egress` | SAFETY_SYSTEM | Эвакуация требует путей, ширины, расстояний, освещения и дверей. | Нельзя блокировать мебелью и складом. | safety |
| `arch.fire.stair_pressurization` | SAFETY_SYSTEM | Подпор воздуха защищает лестницы от дыма. | Требует обслуживания и питания. | highrise |
| `arch.fire.material_reaction` | PROPERTY | Материалы различаются по горючести, дыму и распространению пламени. | Сертификация зависит от норм. | materials |
| `arch.mep.coordination` | PROCESS | MEP coordination совмещает вентиляцию, трубы, электрику и конструкцию. | Конфликты на стройке дороги. | BIM |
| `arch.mep.service_shafts` | COMPONENT | Шахты проводят вертикальные коммуникации здания. | Их место влияет на планировку. | building |
| `arch.mep.access_panels` | DESIGN_METHOD | Ревизионные люки дают доступ к обслуживанию скрытых систем. | Без доступа ремонт разрушает отделку. | maintenance |
| `arch.elevator.core` | SYSTEM | Лифты задают вертикальную доступность и пропускную способность. | Важны ожидание, пожарный режим, резерв. | building |
| `arch.stairs.geometry` | DESIGN_CONSTRAINT | Удобство лестницы зависит от высоты подступенка и глубины проступи. | Нормы ограничивают безопасность. | ergonomics |
| `arch.interior.material_palette` | DESIGN_TOOL | Палитра материалов задаёт долговечность, акустику, уход и атмосферу. | Красивое, но хрупкое решение быстро стареет. | interior |
| `arch.interior.flooring_selection` | MATERIAL_DECISION | Пол выбирают по износу, влажности, шуму, уходу и безопасности. | Один материал не подходит всем зонам. | materials |
| `arch.interior.wall_finish` | MATERIAL_DECISION | Отделка стен влияет на чистку, свет, акустику и ремонтопригодность. | Материал должен соответствовать нагрузке. | interior |
| `arch.interior.ceiling_acoustics` | DESIGN_METHOD | Потолки могут управлять шумом, светом и инженерным доступом. | Подвесные системы снижают высоту. | acoustics |
| `arch.interior.furniture_clearance` | DESIGN_CONSTRAINT | Мебель требует зон открывания, прохода и использования. | План с мебелью проверяет реальную пригодность. | interior |
| `arch.interior.universal_controls` | ACCESSIBILITY | Выключатели, ручки и органы управления должны быть достижимыми и понятными. | Высоты и усилия важны. | accessibility |
| `arch.bim.model` | TOOL | BIM связывает геометрию, данные, координацию и документацию здания. | Модель не равна реальному зданию без контроля. | digital |
| `arch.bim.clash_detection` | METHOD | Clash detection ищет пересечения систем до стройки. | Не ловит все ошибки монтажа. | coordination |
| `arch.cost.quantity_takeoff` | METHOD | Quantity takeoff считает объёмы материалов из чертежей/модели. | Ошибки измерения портят смету. | construction |
| `arch.cost.value_engineering` | METHOD | Value engineering ищет более ценное решение за меньшую стоимость. | Не должно превращаться в урезание качества. | project |
| `arch.construction.mockup` | METHOD | Mockup проверяет узел, материал или фасад до массового строительства. | Экономит ошибки на серии. | QA |
| `arch.construction.punch_list` | PROCESS | Punch list фиксирует недоделки перед сдачей. | Нужен владелец и сроки исправления. | construction |
| `arch.post_occupancy_evaluation` | METHOD | POE проверяет, как здание работает после заселения. | Даёт обратную связь для будущих проектов. | feedback |
| `arch.adaptive_reuse` | METHOD | Adaptive reuse приспосабливает старое здание под новую функцию. | Балансирует наследие, нормы и стоимость. | sustainability |
| `arch.historic_preservation` | PRINCIPLE | Сохранение исторических зданий удерживает культурную и материальную память. | Требует специальных методов и компромиссов. | heritage |
| `arch.housing.affordable_design` | POLICY_DESIGN | Доступное жильё требует контроля земли, стоимости, стандартов и эксплуатации. | Дешёвое строительство может стать дорогим в жизни. | civic |
| `arch.urban.block_permeability` | URBAN_METRIC | Проницаемость квартала влияет на пешие маршруты и активность улицы. | Слишком много проездов может вредить тишине. | urban |
| `arch.urban.mixed_use` | URBAN_MODEL | Mixed-use совмещает жильё, работу, услуги и торговлю. | Требует управления шумом, логистикой, нормами. | urban |
| `arch.urban.street_edge` | DESIGN_PRINCIPLE | Активный край улицы поддерживает безопасность и жизнь города. | Глухие фасады ослабляют пешеходную среду. | urban |
| `arch.urban.human_scale` | DESIGN_PRINCIPLE | Human scale делает пространство читаемым и комфортным для человека. | Не исключает высокую плотность. | urban_design |

---

## 📊 Batch 026 summary

```text
new units: 65
main layers:
  site, housing and interior design
  structure, envelope, fire and MEP
  BIM, construction quality and urban form
```
