# 🏠 Batch 018 — Home, Furniture, Appliances & Domestic Life

**Язык:** русский  
**Статус:** 50K batch 018 / seed units / не L3 truth  
**Цель:** добавить практическое знание о доме как системе: мебель, бытовая техника, хранение, уборка, освещение, безопасность, уход и повседневная организация.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `home.layout.circulation` | DESIGN_PRINCIPLE | Планировка должна оставлять понятные пути движения между зонами. | Мебель не должна блокировать эвакуацию и доступ. | interior |
| `home.layout.zoning` | DESIGN_METHOD | Зонирование разделяет сон, работу, еду, хранение и отдых. | Малые квартиры требуют комбинированных зон. | interior |
| `home.storage.vertical` | METHOD | Вертикальное хранение использует стены и высоту помещения. | Нужны крепления под нагрузку и доступность. | furniture |
| `home.storage.modular` | METHOD | Модульное хранение адаптируется к изменению вещей и комнаты. | Слишком много модулей создаёт визуальный шум. | organization |
| `home.organization.inventory` | METHOD | Учёт вещей снижает дубли, потери и хаос хранения. | Работает только при обновлении. | domestic |
| `home.organization.declutter` | METHOD | Удаление лишних предметов снижает когнитивную нагрузку и время уборки. | Не должно уничтожать важные документы/память. | wellbeing |
| `home.lighting.task` | DESIGN_PRINCIPLE | Рабочее освещение направлено на конкретную задачу. | Требует контроля бликов и теней. | lighting |
| `home.lighting.ambient` | DESIGN_PRINCIPLE | Общее освещение задаёт базовую видимость комнаты. | Не заменяет точечный свет для работы. | lighting |
| `home.lighting.color_temperature` | PROPERTY | Цветовая температура влияет на восприятие уюта, бодрости и цвета предметов. | Предпочтения и задачи различаются. | perception |
| `home.lighting.cri` | METRIC | CRI показывает, насколько естественно источник передаёт цвета. | Важен для кухни, одежды, искусства. | lighting |
| `home.furniture.table_stability` | DESIGN_CONSTRAINT | Стол должен иметь устойчивость против опрокидывания и качания. | Важны центр массы, ноги, крепления, пол. | furniture |
| `home.furniture.chair_ergonomics` | DESIGN_CONSTRAINT | Стул должен поддерживать позу, высоту и движение тела. | Один стул не подходит всем задачам. | ergonomics |
| `home.furniture.shelf_load` | CONSTRAINT | Полки имеют допустимую нагрузку и прогиб. | Длинные пролёты требуют усиления. | furniture |
| `home.furniture.wall_anchor` | SAFETY_RULE | Высокую мебель крепят к стене против опрокидывания. | Особенно важно для детей и сейсмических зон. | child_safety |
| `home.furniture.drawer_slide` | COMPONENT | Направляющие ящиков определяют плавность, нагрузку и долговечность. | Пыль и перегрузка ухудшают ход. | furniture |
| `home.furniture.hinge_adjustment` | METHOD | Петли дверок регулируют зазоры, высоту и прилегание. | Тип петли задаёт доступные регулировки. | repair |
| `home.furniture.flatpack_camlock` | COMPONENT | Эксцентриковые стяжки соединяют детали плоской мебели. | Повторная сборка может ослаблять ДСП. | furniture |
| `home.furniture.upholstery` | PROCESS | Обивка сочетает каркас, наполнитель, ткань и крепление. | Износ зависит от ткани, швов, нагрузки. | textiles |
| `home.furniture.foam_density` | PROPERTY | Плотность и упругость пены влияют на комфорт и срок службы. | Высокая плотность не всегда мягче. | materials |
| `home.furniture.mattress_support` | DESIGN_CONSTRAINT | Матрас и основание должны совместно поддерживать тело. | Медицинские проблемы требуют специалиста. | sleep |
| `home.appliance.refrigerator_cycle` | MECHANISM | Холодильник переносит тепло из камеры наружу через холодильный цикл. | Эффективность падает при грязном конденсаторе и плохой вентиляции. | thermodynamics |
| `home.appliance.refrigerator_seal` | FAILURE_MODE | Изношенный уплотнитель двери пропускает тёплый влажный воздух. | Вызывает лёд, расход энергии и порчу продуктов. | maintenance |
| `home.appliance.washing_machine_drum` | COMPONENT | Барабан стиральной машины перемешивает ткань с водой и моющим средством. | Перегрузка ухудшает стирку и изнашивает подшипники. | appliance |
| `home.appliance.washing_machine_balance` | FAILURE_MODE | Дисбаланс белья вызывает вибрации и нагрузку на узлы. | Особенно заметен при отжиме. | maintenance |
| `home.appliance.dishwasher_spray_arm` | COMPONENT | Разбрызгиватели подают воду на посуду под давлением. | Засоры снижают мойку. | appliance |
| `home.appliance.vacuum_suction` | MECHANISM | Пылесос создаёт разность давления, перенося пыль в фильтр/контейнер. | Забитый фильтр резко снижает поток. | cleaning |
| `home.appliance.air_purifier_cadr` | METRIC | CADR оценивает скорость очистки воздуха от частиц. | Не охватывает все газы и запахи. | air_quality |
| `home.appliance.induction_cooktop` | MECHANISM | Индукционная плита нагревает посуду переменным магнитным полем. | Нужна совместимая посуда. | cooking |
| `home.appliance.microwave_heating` | MECHANISM | Микроволны нагревают полярные молекулы, особенно воду. | Нагрев может быть неравномерным. | cooking |
| `home.appliance.range_hood` | SAFETY_SYSTEM | Вытяжка удаляет дым, жир, влагу и часть загрязнений кухни. | Рециркуляция и вывод наружу различаются. | ventilation |
| `home.cleaning.surface_match` | RULE | Средство уборки выбирают под материал поверхности и тип загрязнения. | Неподходящее средство портит камень, дерево, металл. | chemistry |
| `home.cleaning.contact_time` | METHOD | Дезинфицирующим средствам часто нужно время контакта. | Стирание раньше снижает эффект. | hygiene |
| `home.cleaning.microfiber` | MATERIAL | Микрофибра удерживает пыль и влагу тонкими волокнами. | Может повреждаться высокой температурой и кондиционерами. | textiles |
| `home.cleaning.limescale_acid` | MECHANISM | Кислоты растворяют известковый налёт карбонатов. | Не применять на кислоточувствительных камнях. | chemistry |
| `home.cleaning.grease_alkaline` | MECHANISM | Щёлочные средства лучше разрушают жирные загрязнения. | Могут раздражать кожу и портить материалы. | chemistry_safety |
| `home.cleaning.bleach_safety` | SAFETY_RULE | Хлорные отбеливатели нельзя смешивать с кислотами или аммиаком. | Может выделяться токсичный газ. | safety |
| `home.laundry.sorting` | METHOD | Сортировка белья по цвету, ткани и загрязнению снижает повреждения. | Символы ухода важнее привычки. | apparel |
| `home.laundry.detergent_dose` | METHOD | Доза средства зависит от воды, загрузки и загрязнения. | Избыток может оставлять остатки и вредить машине. | cleaning |
| `home.laundry.fabric_softener` | MATERIAL | Кондиционеры меняют ощущение ткани и снижают статическое электричество. | Могут ухудшать впитываемость полотенец и спорттканей. | textile |
| `home.laundry.drying_airflow` | MECHANISM | Сушка требует тепла, площади испарения и движения воздуха. | Плохая вентиляция создаёт плесень. | household |
| `home.kitchen.storage_dry_goods` | METHOD | Сухие продукты хранят закрыто, сухо, прохладно и защищённо от вредителей. | Масла и орехи прогоркают от кислорода/света. | food |
| `home.kitchen.pantry_rotation` | METHOD | FIFO в кладовой снижает просрочку и потери. | Нужны видимые даты и порядок. | food |
| `home.kitchen.pest_proofing` | METHOD | Плотные контейнеры, уборка крошек и закрытые щели снижают вредителей. | Яды не решают источник пищи и входы. | pest |
| `home.documents.critical_folder` | METHOD | Важные документы лучше хранить вместе, защищённо и с копиями. | Нужен контроль доступа и актуальность. | household |
| `home.documents.digital_backup` | SAFETY_SYSTEM | Цифровые копии документов помогают при потере оригиналов. | Не все копии юридически заменяют оригинал. | data |
| `home.budget.expense_categories` | METHOD | Бытовой бюджет группирует расходы по категориям. | Категории должны отражать реальную жизнь, а не красивую схему. | finance |
| `home.budget.emergency_fund` | RISK_TOOL | Резерв снижает стресс от неожиданных расходов. | Размер зависит от ситуации и дохода. | finance |
| `home.childproofing.outlets` | SAFETY_RULE | Защита розеток и кабелей снижает риск для детей. | Не заменяет наблюдение и исправную электрику. | child_safety |
| `home.childproofing.cabinets` | SAFETY_RULE | Замки шкафов ограничивают доступ к химии, лекарствам и острым предметам. | Опасное лучше хранить высоко и закрыто. | home_safety |
| `home.elder.accessibility` | DESIGN_PRINCIPLE | Дом для пожилых учитывает поручни, свет, нескользкие полы и отсутствие порогов. | Потребности индивидуальны. | care |
| `home.accessibility.universal_design` | PRINCIPLE | Universal design делает пространство удобнее для людей с разными возможностями. | Часто помогает всем пользователям. | design |
| `home.safety.fire_extinguisher` | SAFETY_TOOL | Огнетушитель должен соответствовать типу пожара и быть доступным. | Нужны обучение и срок годности. | fire_safety |
| `home.safety.escape_plan` | SAFETY_PLAN | План эвакуации заранее определяет выходы и место встречи. | Нужно учитывать детей, пожилых, животных. | emergency |
| `home.safety.carbon_monoxide_detector` | SAFETY_SYSTEM | Датчик CO предупреждает о невидимом токсичном газе. | Требует правильного размещения и батарей. | safety |
| `home.safety.gas_shutoff` | SAFETY_SYSTEM | Знание газового крана помогает быстро остановить утечку. | При запахе газа не включать электрические устройства. | emergency |
| `home.safety.water_shutoff` | SAFETY_SYSTEM | Главный водяной вентиль ограничивает ущерб от протечки. | Его нужно проверить заранее. | plumbing |
| `home.safety.electrical_panel_labeling` | METHOD | Подписанный щиток помогает быстро отключить нужную цепь. | Ошибочная подпись опасна. | electricity |
| `home.energy.standby_power` | ENERGY_LOSS | Standby power — потребление устройств в режиме ожидания. | Малое по устройству, но заметное суммарно. | energy |
| `home.energy.thermostat_setback` | METHOD | Снижение/повышение уставки термостата в нужное время экономит энергию. | Комфорт и влажность нужно учитывать. | HVAC |
| `home.energy.window_shading` | METHOD | Шторы, жалюзи и внешнее затенение управляют теплом и светом. | Внешнее затенение лучше против летнего перегрева. | building |
| `home.energy.appliance_label` | INFORMATION | Энергетическая маркировка помогает сравнить расход устройств. | Реальный расход зависит от поведения. | consumer |
| `home.pet.care_space` | DESIGN_CONSTRAINT | Дом с животными требует зон еды, отдыха, туалета и безопасности. | Виды и характеры отличаются. | animal_care |
| `home.pet.toxic_plants` | SAFETY_RISK | Некоторые комнатные растения токсичны для животных или детей. | Требует точной идентификации вида. | health |
| `home.indoor_plants.light_water` | METHOD | Комнатные растения зависят от света, воды, почвы и дренажа. | Перелив часто вреднее недолива. | botany |
| `home.noise.control` | METHOD | Ковры, шторы, уплотнения и планировка снижают бытовой шум. | Структурный шум требует строительных решений. | acoustics |
| `home.smell.source_control` | METHOD | Запахи лучше устранять через источник, вентиляцию и чистку, а не маскировку. | Ароматизаторы могут раздражать. | air_quality |
| `home.seasonal.maintenance` | METHOD | Сезонный чек дома проверяет отопление, водостоки, окна, фильтры, безопасность. | Список зависит от климата и здания. | maintenance |
| `home.move.inventory_labeling` | METHOD | При переезде маркировка коробок по комнате и содержимому снижает потери. | Ценные вещи требуют отдельного контроля. | logistics |
| `home.disaster.kit` | SAFETY_PLAN | Домашний emergency kit покрывает воду, связь, свет, документы и лекарства. | Состав зависит от региона и рисков. | resilience |

---

## 📊 Batch 018 summary

```text
new units: 69
main layers:
  home organization and furniture
  appliances, cleaning, laundry
  domestic safety and accessibility
  household energy and resilience
```
