# BATCH_146 — Fleet Maintenance & Dispatch Operations
# world_skills_core · source: world_skills_core:batch_146:fleet_maintenance_dispatch_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| fleetops.asset.vehicle_register | Vehicle register | invariant | Реестр транспорта хранит единицы флота, владельцев, характеристики, статус, документы и назначение. | знать, чем управляешь |
| fleetops.asset.vin_plate | VIN and asset plate | invariant | VIN или asset plate связывает физическое транспортное средство с учетной системой, документами и историей обслуживания. | не перепутать актив |
| fleetops.asset.odometer_record | Odometer record | invariant | Запись пробега используется для обслуживания, расхода топлива, амортизации, гарантий и анализа использования. | пробег как trigger |
| fleetops.asset.service_history | Service history | invariant | История сервиса показывает ремонты, inspections, parts, failures, costs и повторяющиеся проблемы. | видеть паттерны |
| fleetops.asset.warranty_tracking | Warranty tracking | variant | Warranty tracking помогает не оплачивать за свой счет ремонт, который покрывается гарантией или сервисным контрактом. | деньги и сроки |
| fleetops.maintenance.pm_schedule | Preventive maintenance schedule | invariant | PM schedule задает обслуживание по пробегу, времени, часам работы, условиям эксплуатации или regulatory requirement. | меньше аварийных простоев |
| fleetops.maintenance.inspection_checklist | Fleet inspection checklist | invariant | Inspection checklist стандартизирует проверку состояния перед выпуском, после рейса или при приемке из ремонта. | одинаковое качество осмотра |
| fleetops.maintenance.defect_report | Vehicle defect report | invariant | Defect report фиксирует неисправность, симптом, водителя, время, пробег, severity и решение о допуске. | не терять проблемы |
| fleetops.maintenance.work_order | Maintenance work order | invariant | Work order связывает задачу ремонта, детали, труд, разрешение, статус и закрывающую проверку. | ремонт как управляемый процесс |
| fleetops.maintenance.parts_availability | Parts availability | variant | Доступность запчастей влияет на downtime, priority ремонта, складской запас и выбор поставщика. | простой часто из-за parts |
| fleetops.maintenance.tire_management | Tire management | invariant | Управление шинами отслеживает износ, давление, ротацию, повреждения, возраст и соответствие нагрузке. | безопасность и топливо |
| fleetops.maintenance.brake_inspection | Brake inspection | invariant | Проверка тормозов оценивает износ, утечки, регулировку, предупреждения и соответствие safety threshold. | критичный safety control |
| fleetops.maintenance.fluid_analysis | Fluid analysis | variant | Анализ масла или жидкости может выявить износ, загрязнение, перегрев или нарушение интервала обслуживания. | ранняя диагностика |
| fleetops.dispatch.driver_roster | Driver roster | invariant | Driver roster показывает доступность водителей, квалификации, смены, ограничения и назначенные рейсы. | люди тоже capacity |
| fleetops.dispatch.route_assignment | Route assignment | invariant | Назначение маршрута учитывает адреса, окна доставки, пробки, ограничения транспорта, безопасность и рабочее время. | оптимизация без хаоса |
| fleetops.dispatch.load_planning | Load planning | invariant | Планирование загрузки учитывает вес, объем, распределение, совместимость груза, порядок выгрузки и ограничения автомобиля. | рейс должен быть выполним |
| fleetops.dispatch.delivery_window | Delivery window | variant | Delivery window задает допустимый период прибытия и влияет на маршрут, ожидание, SLA и штрафы. | время как ресурс |
| fleetops.dispatch.vehicle_availability | Vehicle availability | invariant | Доступность транспортного средства зависит от статуса ремонта, документов, водителя, топлива, загрузки и назначения. | планировать реальный fleet |
| fleetops.dispatch.substitution_plan | Vehicle substitution plan | variant | План замены транспорта снижает срыв рейса при поломке, задержке ремонта или внезапном пике спроса. | запасной сценарий |
| fleetops.safety.driver_license_check | Driver license check | invariant | Проверка водительских прав и допусков подтверждает, что водитель имеет право управлять конкретным классом транспорта. | compliance before dispatch |
| fleetops.safety.hours_of_service | Hours of service | invariant | Контроль рабочего времени и отдыха снижает риск усталости и нарушения транспортных правил. | безопасность смен |
| fleetops.safety.pretrip_inspection | Pre-trip inspection | invariant | Предрейсовый осмотр выявляет очевидные safety defects до выхода транспортного средства на маршрут. | остановить проблему заранее |
| fleetops.safety.incident_report | Fleet incident report | invariant | Incident report фиксирует ДТП, повреждение, near miss, травму, cargo loss или нарушение для анализа и claims. | факты сразу после события |
| fleetops.safety.fatigue_management | Driver fatigue management | variant | Управление усталостью включает график, перерывы, мониторинг, культуру остановки и разбор опасных паттернов. | человек не машина |
| fleetops.fuel.fuel_card | Fuel card control | variant | Fuel card control связывает покупку топлива с водителем, автомобилем, местом, объемом и отклонениями. | снизить misuse |
| fleetops.fuel.consumption_variance | Fuel consumption variance | invariant | Отклонение расхода топлива может указывать на стиль вождения, маршрут, груз, техническую проблему или ошибку записи. | сигнал для проверки |
| fleetops.fuel.idling_monitor | Idling monitor | variant | Monitoring холостого хода помогает снижать расход, выбросы, износ и необъясненные часы работы двигателя. | управлять привычками |
| fleetops.fuel.alternative_fuel | Alternative fuel fleet | variant | Альтернативное топливо требует учета инфраструктуры, дальности, веса, стоимости, обслуживания и operational fit. | не только цена топлива |
| fleetops.fuel.emissions_compliance | Emissions compliance | invariant | Соответствие требованиям по выбросам зависит от класса двигателя, обслуживания, документации и режима эксплуатации. | регуляторный риск |
| fleetops.telematics.gps_trace | GPS trace | invariant | GPS trace показывает фактический маршрут, остановки, время, отклонения и возможные спорные точки доставки. | доказательство движения |
| fleetops.telematics.geofence_alert | Geofence alert | variant | Geofence alert срабатывает при входе или выходе транспорта из заданной зоны. | контроль depot и customers |
| fleetops.telematics.harsh_braking | Harsh braking event | variant | Harsh braking event может указывать на рискованный стиль, дорожную ситуацию, грузовую проблему или ложный датчик. | повод для coaching |
| fleetops.telematics.diagnostic_code | Diagnostic trouble code | invariant | Diagnostic trouble code помогает связать сигнал автомобиля с системой, severity и решением о сервисе. | телематика в maintenance |
| fleetops.telematics.temperature_monitor | Cargo temperature monitor | variant | Temperature monitor нужен для груза с cold chain или heat sensitivity и должен быть связан с alarm response. | качество груза в пути |
| fleetops.compliance.registration_renewal | Vehicle registration renewal | invariant | Продление регистрации требует отслеживания сроков, документов, сборов и вывода транспорта из рейса при просрочке. | не выпускать нелегально |
| fleetops.compliance.insurance_certificate | Insurance certificate | invariant | Insurance certificate подтверждает покрытие, срок, транспорт, риски и требования клиента или регулятора. | доказательство защиты |
| fleetops.compliance.permits | Transport permits | variant | Permits могут требоваться для веса, опасного груза, территории, маршрута, международной перевозки или спецтехники. | правила зависят от груза |
| fleetops.compliance.inspection_due | Regulatory inspection due | invariant | Срок обязательной inspection должен попадать в planning, чтобы транспорт не работал с просроченным допуском. | compliance calendar |
| fleetops.compliance.audit_file | Fleet audit file | invariant | Audit file хранит лицензии, inspections, maintenance, incident records, training и proof of compliance. | доказательная папка |
| fleetops.cost.total_cost_of_ownership | Total cost of ownership | invariant | TCO транспорта включает покупку, финансирование, топливо, обслуживание, downtime, insurance, налоги и resale. | видеть полную цену |
| fleetops.cost.cost_per_km | Cost per kilometer | invariant | Cost per kilometer связывает расходы флота с пробегом и помогает сравнивать vehicles, routes и utilization. | operational unit economics |
| fleetops.cost.downtime_cost | Downtime cost | variant | Стоимость простоя включает потерянные рейсы, замену транспорта, штрафы, overtime и недовольство клиента. | downtime не бесплатен |
| fleetops.cost.replacement_cycle | Replacement cycle | variant | Цикл замены транспорта учитывает возраст, пробег, repairs, fuel efficiency, compliance, resale и reliability. | менять до точки убытка |
| fleetops.cost.residual_value | Residual value | variant | Residual value влияет на решение купить, арендовать, продать или продлить срок использования транспорта. | остаточная стоимость важна |
