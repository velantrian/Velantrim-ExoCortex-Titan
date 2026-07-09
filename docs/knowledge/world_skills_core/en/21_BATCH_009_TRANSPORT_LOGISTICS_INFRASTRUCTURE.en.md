# 🚚 Batch 009 — Transport, Logistics & Infrastructure Operations

**Язык:** русский  
**Статус:** 50K batch 009 / seed units / не L3 truth  
**Цель:** добавить практическую карту транспорта, складов, портов, железных дорог, авиации, городской инфраструктуры и логистических процессов.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `transport.road.vehicle_load` | CONSTRAINT | Нагрузка транспорта влияет на дорожное покрытие, мосты и безопасность движения. | Не только масса, но и распределение по осям важно. | roads |
| `transport.road.axle_load` | CONSTRAINT | Осевые нагрузки часто сильнее определяют износ дороги, чем общая масса машины. | Нормы зависят от страны и типа дороги. | pavement |
| `transport.road.pavement_wear` | FAILURE_MODE | Покрытие изнашивается от воды, температуры, нагрузки, соли и старения материала. | Требует диагностики причин, а не только ремонта поверхности. | road_maintenance |
| `transport.road.traffic_flow` | MODEL | Поток транспорта зависит от плотности, скорости, полос и поведения водителей. | Перегрузка создаёт пробки и волны торможения. | urban |
| `transport.road.signal_timing` | METHOD | Настройка светофоров управляет очередями, пропускной способностью и безопасностью. | Оптимум зависит от времени суток и потока. | traffic |
| `transport.road.roundabout` | METHOD | Кольцевое движение снижает конфликтные точки на некоторых перекрёстках. | Не всегда подходит для больших потоков или тяжёлого транспорта. | road_design |
| `transport.road.guardrail` | SAFETY_SYSTEM | Ограждения снижают тяжесть выезда с дороги, но сами требуют правильной установки. | Неправильный конец барьера опасен. | safety |
| `transport.road.winter_maintenance` | METHOD | Зимнее содержание использует уборку, противогололёдные материалы и прогноз. | Соль вредна для коррозии и среды. | infrastructure |
| `transport.road.drainage_maintenance` | METHOD | Дренаж дороги должен отводить воду от покрытия и основания. | Засорение быстро ускоряет разрушение. | roads |
| `transport.road.bridge_inspection` | QUALITY_CHECK | Мосты требуют периодического осмотра несущих элементов, опор, деформаций и коррозии. | Частота зависит от типа, возраста и нагрузки. | civil_engineering |
| `transport.rail.gauge` | CONSTRAINT | Ширина колеи определяет совместимость подвижного состава и инфраструктуры. | Разные стандарты усложняют международные перевозки. | rail |
| `transport.rail.switch` | COMPONENT | Стрелочный перевод направляет поезд с одного пути на другой. | Требует точной геометрии и обслуживания. | rail |
| `transport.rail.signaling` | SAFETY_SYSTEM | Сигнализация управляет разрешением движения поездов. | Ошибки могут привести к столкновениям. | rail_safety |
| `transport.rail.wheel_rail_contact` | MECHANISM | Контакт колеса и рельса передаёт нагрузку и тягу через малую площадь. | Износ и смазка критичны. | mechanics |
| `transport.rail.track_ballast` | COMPONENT | Балласт распределяет нагрузку, удерживает шпалы и обеспечивает дренаж. | Загрязнение балласта ухудшает работу пути. | rail |
| `transport.rail.catenary` | COMPONENT | Контактная сеть подаёт электроэнергию электропоездам. | Требует натяжения, изоляции и безопасных расстояний. | power |
| `transport.rail.timetable_headway` | MODEL | Headway — интервал между поездами, определяющий пропускную способность. | Ограничивается сигнализацией, станциями и безопасностью. | scheduling |
| `transport.rail.freight_terminal` | SYSTEM | Грузовой терминал связывает железную дорогу, склад, автомобильный и морской транспорт. | Эффективность зависит от перегрузки и очередей. | logistics |
| `transport.rail.safety_interlocking` | SAFETY_SYSTEM | Interlocking предотвращает несовместимые маршруты поездов. | Должен быть fail-safe. | rail_safety |
| `transport.rail.maintenance_window` | PLANNING | Окно обслуживания — период, когда путь можно ремонтировать без движения поездов. | Требует согласования с расписанием. | operations |
| `transport.maritime.containerization` | SYSTEM | Контейнеризация стандартизирует перевозку грузов между морем, дорогой и железной дорогой. | Требует портовой инфраструктуры и ISO-совместимости. | trade |
| `transport.maritime.port_crane` | EQUIPMENT | Портовые краны перегружают контейнеры и тяжёлые грузы. | Ограничения: грузоподъёмность, ветер, доступ к судну. | ports |
| `transport.maritime.draft` | CONSTRAINT | Осадка судна определяет минимальную глубину воды для безопасного прохода. | Меняется от загрузки и плотности воды. | navigation |
| `transport.maritime.ballast_water` | SYSTEM | Балластная вода стабилизирует судно, но может переносить инвазивные виды. | Регулируется экологическими правилами. | environment |
| `transport.maritime.cargo_stowage` | METHOD | Укладка груза влияет на устойчивость, доступность и безопасность судна. | Неправильная укладка создаёт риск смещения. | shipping |
| `transport.maritime.cold_chain_reefer` | LOGISTICS | Рефрижераторные контейнеры поддерживают температуру скоропортящихся грузов. | Требуют питания и мониторинга. | food_logistics |
| `transport.maritime.bulk_cargo` | CARGO_TYPE | Навалочные грузы перевозят без упаковки: зерно, руда, уголь, цемент. | Риск пыли, самосогревания, смещения. | trade |
| `transport.maritime.tanker_safety` | SAFETY_SYSTEM | Танкерные грузы требуют контроля пожара, паров, давления и загрязнений. | High-risk domain. | chemical_transport |
| `transport.maritime.pilotage` | METHOD | Лоцман помогает судну проходить сложные портовые и прибрежные воды. | Не отменяет ответственность капитана. | navigation |
| `transport.maritime.port_customs` | PROCESS | Портовая таможня связывает груз, документы, классификацию и контроль. | Ошибки задерживают груз и создают штрафы. | trade_law |
| `transport.aviation.lift` | MECHANISM | Подъёмная сила возникает из взаимодействия крыла, скорости и потока воздуха. | Зависит от угла атаки, плотности воздуха и профиля крыла. | physics |
| `transport.aviation.runway_length` | CONSTRAINT | Длина ВПП зависит от самолёта, массы, температуры, высоты и покрытия. | Жара и высокогорье увеличивают требования. | airport |
| `transport.aviation.air_traffic_control` | SAFETY_SYSTEM | Управление воздушным движением разделяет самолёты по высоте, маршруту и времени. | Требует связи, процедур и радаров/наблюдения. | aviation |
| `transport.aviation.weight_balance` | CONSTRAINT | Масса и центровка самолёта влияют на управляемость и безопасность. | Ошибки критичны. | flight_safety |
| `transport.aviation.maintenance_check` | QUALITY_CHECK | Самолёты проходят плановые проверки по часам, циклам и состоянию. | Стандарты зависят от типа и регулятора. | maintenance |
| `transport.aviation.cargo_unit_load_device` | LOGISTICS | ULD стандартизирует авиационные грузы и багаж. | Ограничения по массе, форме, закреплению. | air_cargo |
| `transport.aviation.deicing` | METHOD | Обледенение меняет аэродинамику, поэтому самолёты обрабатывают антиобледенительными жидкостями. | Время защиты ограничено. | safety |
| `transport.aviation.fuel_planning` | PLANNING | Топливо планируют с учётом маршрута, резервов, погоды и альтернативных аэродромов. | Регулируется авиационными правилами. | aviation |
| `transport.aviation.safety_management` | SYSTEM | Safety management системно выявляет риски, события и корректирующие действия. | Требует culture, reporting, analysis. | safety |
| `transport.aviation.noise_zones` | CONSTRAINT | Аэропорты создают шумовые зоны, влияющие на жильё и планирование. | Зависит от маршрутов, типов самолётов и времени суток. | urban |
| `logistics.supply_chain_node` | MODEL | Цепь поставок состоит из узлов: поставщики, склады, фабрики, порты, магазины. | Слабое звено ограничивает всю систему. | supply_chain |
| `logistics.lead_time` | METRIC | Lead time — время от заказа до получения результата. | Включает производство, ожидание, транспорт, таможню. | planning |
| `logistics.safety_stock` | METHOD | Safety stock покрывает неопределённость спроса и поставок. | Избыточный запас стоит денег. | inventory |
| `logistics.reorder_point` | METHOD | Точка заказа показывает, когда нужно пополнить запас. | Зависит от спроса, lead time и safety stock. | inventory |
| `logistics.bottleneck` | FAILURE_MODE | Bottleneck — стадия, ограничивающая производительность всей системы. | Устранение не того узла не повышает throughput. | operations |
| `logistics.routing` | METHOD | Маршрутизация выбирает путь доставки по стоимости, сроку, риску и ограничениям. | Динамична при пробках, погоде, границах. | transport |
| `logistics.cross_docking` | METHOD | Cross-docking перегружает товар почти без хранения. | Требует синхронизации поставок и спроса. | warehouse |
| `logistics.last_mile` | PROCESS | Last mile — последняя доставка до пользователя или магазина. | Часто дорогая и сложная часть логистики. | delivery |
| `logistics.reverse_logistics` | PROCESS | Reverse logistics управляет возвратами, ремонтом, переработкой и утилизацией. | Важно для e-commerce, техники, упаковки. | circular_economy |
| `logistics.traceability` | SYSTEM | Traceability связывает товар с партиями, местом, временем и документами. | Критично для recall, pharma, food, customs. | audit |
| `warehouse.receiving` | PROCESS | Приёмка проверяет товар, количество, качество и документы. | Ошибки при входе ломают весь складской учёт. | warehouse |
| `warehouse.putaway` | PROCESS | Размещение товара выбирает место хранения по размеру, скорости оборота и условиям. | Влияет на скорость сборки заказов. | warehouse |
| `warehouse.picking` | PROCESS | Picking — отбор товаров под заказ. | Ошибки ведут к возвратам и потерям. | warehouse |
| `warehouse.packing` | PROCESS | Упаковка защищает товар и готовит его к перевозке. | Нужны размер, амортизация, маркировка. | logistics |
| `warehouse.inventory_count` | QUALITY_CHECK | Инвентаризация сверяет фактический запас с учётной системой. | Cycle counting снижает остановки. | finance |
| `warehouse.fifo_fefo` | METHOD | FIFO и FEFO управляют очередностью выдачи по времени или сроку годности. | FEFO критично для еды, лекарств, химии. | storage |
| `warehouse.forklift_safety` | SAFETY_RULE | Погрузчики требуют маршрутов, обучения, обзора и ограничения скорости. | Основной риск — наезд, падение груза, опрокидывание. | safety |
| `warehouse.racking_load` | CONSTRAINT | Стеллажи имеют допустимую нагрузку и требуют правильного крепления. | Перегрузка может вызвать обрушение. | warehouse |
| `warehouse.barcode` | SYSTEM | Штрихкоды связывают физический товар с цифровым учётом. | Требуют стандартов, сканеров, качества печати. | information |
| `warehouse.wms` | SYSTEM | WMS управляет приёмкой, хранением, отбором, отгрузкой и запасами. | Эффективность зависит от данных и дисциплины процессов. | software |
| `infra.urban.water_supply` | INFRA_SYSTEM | Водоснабжение доставляет очищенную воду через сети, насосы и резервуары. | Давление, утечки и качество критичны. | water |
| `infra.urban.sewer_network` | INFRA_SYSTEM | Канализация отводит сточные воды к очистке или безопасному сбросу. | Засоры и инфильтрация создают аварии. | sanitation |
| `infra.urban.power_distribution` | INFRA_SYSTEM | Распределительная сеть доставляет электроэнергию к домам и предприятиям. | Требует защиты, трансформаторов и баланса нагрузки. | power |
| `infra.urban.telecom_backbone` | INFRA_SYSTEM | Телеком-магистраль связывает пользователей, дата-центры и сервисы. | Уязвима к обрывам, питанию и перегрузкам. | communications |
| `infra.urban.public_transport` | INFRA_SYSTEM | Общественный транспорт перемещает людей с меньшей площадью дороги на пассажира. | Требует расписания, пересадок и доступности. | city |
| `infra.urban.street_lighting` | INFRA_SYSTEM | Уличное освещение повышает видимость и безопасность, но требует энергии и обслуживания. | Избыточный свет создаёт световое загрязнение. | urban |
| `infra.urban.waste_collection` | INFRA_SYSTEM | Сбор отходов предотвращает санитарные риски и поддерживает переработку. | Нужны маршруты, контейнеры, сортировка. | waste |
| `infra.urban.emergency_access` | DESIGN_CONSTRAINT | Улицы и здания должны допускать доступ пожарных, скорой и эвакуации. | Часто конфликтует с парковкой и плотностью. | safety |
| `infra.urban.zoning` | REGULATION | Зонирование разделяет или смешивает функции города: жильё, промышленность, торговлю. | Может помогать безопасности, но создавать неравенство. | urban_planning |
| `infra.urban.asset_management` | METHOD | Asset management учитывает состояние, стоимость и приоритет обслуживания инфраструктуры. | Помогает ремонтировать до аварии. | public_management |

---

## 📊 Batch 009 summary

```text
new units: 70
main layers:
  roads / rail / maritime / aviation
  logistics / warehouse / supply chain
  urban infrastructure operations
  maintenance and safety
```
