# BATCH_147 — Building Commissioning & Facility Handover Detail
# world_skills_core · source: world_skills_core:batch_147:building_commissioning_handover_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| bldgcom.planning.cx_plan | Commissioning plan | invariant | Commissioning plan задает системы, роли, проверки, документы, сроки, acceptance criteria и порядок закрытия замечаний. | приемка как управляемый процесс |
| bldgcom.planning.owner_project_requirements | Owner project requirements | invariant | OPR описывает ожидания владельца по функциям здания, комфорту, энергии, безопасности, обслуживанию и эксплуатации. | критерии до проектирования |
| bldgcom.planning.basis_of_design | Basis of design | invariant | Basis of design объясняет, как проектные решения отвечают owner requirements и нормативным ограничениям. | связь цели и инженерии |
| bldgcom.planning.commissioning_scope | Commissioning scope | variant | Scope commissioning определяет, какие системы и этапы будут проверяться, а какие остаются вне процедуры. | не проверять вслепую |
| bldgcom.planning.commissioning_schedule | Commissioning schedule | variant | График commissioning должен учитывать готовность монтажа, доступ к системам, сезонность испытаний и исправление deficiencies. | тесты требуют времени |
| bldgcom.planning.roles_matrix | Commissioning roles matrix | invariant | Матрица ролей распределяет владельца, подрядчика, проектировщика, commissioning agent, facility team и поставщиков. | кто за что отвечает |
| bldgcom.prefunctional.submittal_review | Commissioning submittal review | invariant | Review submittals проверяет, что выбранное оборудование и controls способны выполнить проектные требования. | ошибка до монтажа дешевле |
| bldgcom.prefunctional.equipment_tagging | Equipment tagging | invariant | Маркировка оборудования связывает физический объект с drawings, controls, manuals, asset register и maintenance records. | найти нужный asset |
| bldgcom.prefunctional.installation_checklist | Installation checklist | invariant | Installation checklist подтверждает, что оборудование установлено, подключено, доступно и готово к functional testing. | prefunctional gate |
| bldgcom.prefunctional.sensor_calibration | Building sensor calibration | invariant | Калибровка датчиков температуры, давления, потока или CO2 нужна до настройки автоматики. | controls зависят от sensor truth |
| bldgcom.prefunctional.access_clearance | Maintenance access clearance | invariant | Доступ для обслуживания проверяет, можно ли безопасно добраться до фильтров, клапанов, панелей и service points. | эксплуатация после сдачи |
| bldgcom.prefunctional.deficiency_log | Deficiency log | invariant | Deficiency log фиксирует замечание, систему, владельца, severity, срок и статус закрытия. | punch list с дисциплиной |
| bldgcom.functional.functional_test_script | Functional test script | invariant | Functional test script задает пошаговые условия, ожидаемые реакции, evidence и pass/fail criteria. | проверять одинаково |
| bldgcom.functional.hvac_sequence_test | HVAC sequence test | invariant | Тест sequence of operation проверяет, что HVAC реагирует на режимы, датчики, setpoints и alarms как задумано. | комфорт и энергия |
| bldgcom.functional.electrical_load_test | Electrical load test | variant | Load test проверяет распределение, capacity, protection и поведение системы под заданной нагрузкой. | не только включить питание |
| bldgcom.functional.emergency_power_test | Emergency power test | invariant | Тест аварийного питания проверяет запуск, переключение, нагрузку, alarms и возврат к нормальной сети. | resilience здания |
| bldgcom.functional.fire_alarm_interface | Fire alarm interface test | invariant | Проверка интерфейсов пожарной сигнализации подтверждает связи с HVAC, лифтами, дверями, оповещением и monitoring. | life safety coordination |
| bldgcom.functional.controls_trending | Controls trending | variant | Trending в BMS собирает временные ряды, чтобы увидеть hunting, overshoot, short cycling и неверные setpoints. | диагностика после теста |
| bldgcom.functional.water_system_flush | Water system flush | invariant | Промывка и подготовка водных систем удаляет мусор, остатки и загрязнения перед стабильной эксплуатацией. | защитить оборудование и качество |
| bldgcom.functional.elevator_acceptance | Elevator acceptance test | invariant | Acceptance elevator проверяет безопасность, двери, связь, emergency operation, ride quality и документы допуска. | вертикальный транспорт |
| bldgcom.handover.punch_list | Punch list | invariant | Punch list собирает незавершенные или дефектные позиции до final acceptance. | не забыть мелочи |
| bldgcom.handover.om_manual | O&M manual | invariant | O&M manual содержит инструкции эксплуатации, maintenance, parts, warranties, setpoints и troubleshooting. | facility team не остается вслепую |
| bldgcom.handover.as_built_drawings | As-built drawings | invariant | As-built drawings показывают фактическую реализацию после изменений строительства. | реальное здание, не намерение |
| bldgcom.handover.training_session | Operator training session | variant | Training session передает facility team управление системами, alarms, seasonal modes и routine checks. | знания переходят владельцу |
| bldgcom.handover.warranty_matrix | Warranty matrix | invariant | Warranty matrix связывает системы, сроки, условия, контакты, exclusions и процедуры claims. | не потерять гарантию |
| bldgcom.handover.spare_parts_list | Spare parts list | variant | Список spare parts показывает критичные расходники и запасные части, нужные для первых периодов эксплуатации. | меньше downtime |
| bldgcom.handover.asset_register | Facility asset register | invariant | Asset register переносит оборудование в систему эксплуатации с tag, location, specs, warranty и maintenance requirements. | база FM/CMMS |
| bldgcom.handover.maintenance_plan | Initial maintenance plan | invariant | Начальный план обслуживания задает первые inspections, filters, lubrication, tests, calibrations и regulatory checks. | эксплуатация стартует сразу |
| bldgcom.performance.seasonal_testing | Seasonal testing | variant | Seasonal testing проверяет системы в условиях отопления, охлаждения или переходного сезона, которые не были доступны при сдаче. | не все видно в один месяц |
| bldgcom.performance.energy_baseline | Energy baseline | invariant | Energy baseline фиксирует исходное потребление и условия, чтобы сравнивать фактическую performance здания. | контролировать энергию |
| bldgcom.performance.indoor_air_quality | Indoor air quality check | invariant | IAQ check оценивает вентиляцию, загрязнители, влажность, фильтрацию и complaints в контексте эксплуатации. | здоровье и комфорт |
| bldgcom.performance.balancing_report | Testing and balancing report | invariant | TAB report подтверждает фактические расходы воздуха или воды и отклонения от проектных значений. | balancing не на глаз |
| bldgcom.performance.envelope_leakage | Envelope leakage test | variant | Проверка утечек envelope помогает найти air leakage, moisture risk и energy loss. | оболочка как система |
| bldgcom.performance.occupancy_feedback | Occupancy feedback | variant | Feedback пользователей показывает реальные проблемы комфорта, шума, света, навигации или controls после заселения. | эксплуатационная правда |
| bldgcom.performance.recommissioning_trigger | Recommissioning trigger | invariant | Recommissioning нужен после крупных изменений, жалоб, роста energy use или degradation performance. | здание дрейфует |
| bldgcom.performance.measurement_verification | Measurement and verification | variant | M&V сравнивает measured performance с baseline и adjustments, чтобы оценить фактический эффект. | доказать savings |
| bldgcom.closeout.acceptance_criteria | Commissioning acceptance criteria | invariant | Acceptance criteria заранее определяют, какие evidence нужны для принятия системы или закрытия замечания. | спорить меньше |
| bldgcom.closeout.authority_signoff | Authority signoff | variant | Signoff уполномоченного органа может требоваться для life safety, occupancy, elevators, energy или environmental systems. | legal readiness |
| bldgcom.closeout.closeout_report | Commissioning closeout report | invariant | Closeout report обобщает выполненные тесты, открытые items, deviations, recommendations и evidence. | итоговая память проекта |
| bldgcom.closeout.deferred_work | Deferred work | variant | Deferred work должен иметь владельца, срок, interim risk control и acceptance path. | не прятать незавершенное |
| bldgcom.closeout.document_index | Handover document index | invariant | Индекс handover documents помогает быстро найти manuals, drawings, certificates, warranties и test records. | управляемый архив |
| bldgcom.closeout.lessons_learned | Commissioning lessons learned | variant | Lessons learned фиксируют проектные, монтажные и эксплуатационные проблемы для будущих объектов. | улучшать следующие проекты |
| bldgcom.closeout.digital_twin_update | Digital twin update | variant | Обновление digital twin или BIM/FM модели должно отражать фактические assets, locations, parameters и documents. | данные для эксплуатации |
| bldgcom.closeout.retention_schedule | Facility record retention | invariant | Retention schedule задает, какие commissioning records хранить, где, сколько и кто отвечает за доступ. | evidence не исчезает |
