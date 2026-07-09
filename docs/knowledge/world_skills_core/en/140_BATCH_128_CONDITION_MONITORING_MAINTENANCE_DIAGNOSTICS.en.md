# BATCH_128 — Condition Monitoring & Maintenance Diagnostics
# world_skills_core · source: world_skills_core:batch_128:condition_monitoring_diagnostics
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| condmon.vibration.baseline | Vibration baseline | invariant | Базовая вибрационная сигнатура фиксирует нормальное состояние машины и нужна для обнаружения изменений. | сравнение с собой, а не с абстрактной нормой |
| condmon.vibration.imbalance | Rotating imbalance | invariant | Дисбаланс ротора часто проявляется вибрацией на частоте вращения и растёт с массой смещения. | диагностика вращающихся узлов |
| condmon.vibration.misalignment | Shaft misalignment | variant | Несоосность валов может давать повышенную вибрацию, нагрев муфты и ускоренный износ подшипников. | проверка монтажа |
| condmon.vibration.looseness | Mechanical looseness | variant | Механическая слабина часто создает ударные компоненты, нестабильную фазу и рост вибрации при нагрузке. | искать крепеж и посадки |
| condmon.vibration.bearing_outer_race | Bearing outer race defect | invariant | Дефект наружного кольца подшипника обычно вызывает повторяющиеся импульсы на характерной частоте контакта. | раннее обнаружение подшипника |
| condmon.vibration.bearing_inner_race | Bearing inner race defect | invariant | Дефект внутреннего кольца подшипника модулируется вращением вала и может меняться с нагрузкой. | отличать от наружного кольца |
| condmon.vibration.envelope_analysis | Envelope analysis | invariant | Envelope analysis выделяет повторяющиеся ударные импульсы, скрытые в высокочастотной вибрации подшипника. | диагностика ранних дефектов |
| condmon.vibration.resonance_check | Resonance check | variant | Резонанс возникает, когда возбуждение близко к собственной частоте конструкции и резко усиливает отклик. | менять жесткость или скорость |
| condmon.oil.viscosity_trend | Oil viscosity trend | invariant | Тренд вязкости масла показывает загрязнение, окисление, разбавление или неправильный сорт смазки. | здоровье смазки |
| condmon.oil.particle_count | Oil particle count | invariant | Счет частиц в масле показывает уровень загрязнения и риск абразивного износа гидравлики или подшипников. | контроль чистоты |
| condmon.oil.wear_metals | Wear metals analysis | invariant | Анализ металлов износа связывает элементы в масле с возможными источниками деталей и режимами износа. | локализация проблемы |
| condmon.oil.water_contamination | Water in oil | invariant | Вода в масле ухудшает смазку, ускоряет коррозию и может вызывать кавитацию или эмульсию. | контроль герметичности |
| condmon.oil.acid_number | Acid number trend | variant | Рост кислотного числа масла указывает на старение, окисление или химическое загрязнение смазки. | срок замены масла |
| condmon.thermal.hotspot | Thermal hotspot | invariant | Тепловая аномалия показывает место с повышенной температурой относительно сравнимых точек или прежнего состояния. | быстрое обнаружение риска |
| condmon.thermal.electrical_connection | Hot electrical connection | invariant | Плохой электрический контакт нагревается из-за повышенного сопротивления и может быть виден на термограмме под нагрузкой. | профилактика пожара |
| condmon.thermal.insulation_loss | Insulation loss thermal pattern | variant | Потеря теплоизоляции создает локальные зоны повышенного теплопотока и отличимый температурный рисунок. | энергоаудит и ремонт |
| condmon.thermal.steam_trap | Steam trap thermography | variant | Неисправный конденсатоотводчик может проявляться аномальной температурой до и после устройства. | экономия пара |
| condmon.ultrasound.air_leak | Ultrasonic air leak | invariant | Ультразвуковой контроль может находить утечки сжатого воздуха по высокочастотному шуму турбулентной струи. | снижение энергопотерь |
| condmon.ultrasound.electrical_discharge | Ultrasonic electrical discharge | invariant | Частичные разряды, корона и дуговые явления могут создавать ультразвуковые сигналы до видимого отказа. | контроль электрооборудования |
| condmon.ultrasound.bearing_lubrication | Ultrasonic bearing lubrication | variant | Ультразвук подшипника может помогать дозировать смазку, когда уровень шума падает до нормального диапазона. | избегать недо- и пересмазки |
| condmon.motor.current_signature | Motor current signature | invariant | Анализ сигнатуры тока двигателя ищет электрические и механические дефекты через частотные компоненты в токе. | диагностика без доступа к валу |
| condmon.motor.insulation_resistance | Insulation resistance trend | invariant | Тренд сопротивления изоляции показывает влажность, загрязнение или старение изоляции электрической машины. | планировать сушку или ремонт |
| condmon.motor.winding_temperature | Winding temperature | invariant | Температура обмоток влияет на срок службы изоляции и часто важнее температуры корпуса двигателя. | защита двигателя |
| condmon.process.control_limits | Process control limits | invariant | Контрольные границы процесса строятся по статистике нормальной вариации и не равны инженерным спецификациям. | не путать контроль и допуск |
| condmon.process.alarm_rationalization | Alarm rationalization | variant | Rationalization тревог убирает дубли, шум и неясные сигналы, чтобы оператор видел действительно важные отклонения. | снижение alarm fatigue |
| condmon.process.bad_actor_list | Bad actor list | variant | Список bad actors ранжирует оборудование по отказам, простоям, стоимости и риску. | фокус maintenance усилий |
| condmon.maintenance.p_f_curve | P-F curve | invariant | P-F curve показывает интервал между обнаруживаемым потенциальным отказом и функциональным отказом. | выбирать период контроля |
| condmon.maintenance.failure_mode | Failure mode | invariant | Failure mode описывает конкретный способ, которым объект перестает выполнять требуемую функцию. | основа диагностики |
| condmon.maintenance.functional_failure | Functional failure | invariant | Functional failure наступает, когда объект уже не выполняет требуемую функцию на заданном уровне. | отличать дефект от отказа |
| condmon.maintenance.condition_based | Condition-based maintenance | invariant | Condition-based maintenance планирует действие по фактическому состоянию оборудования, а не только по календарю. | меньше лишних ремонтов |
| condmon.maintenance.predictive_model | Predictive maintenance model | variant | Predictive maintenance model прогнозирует риск отказа по данным, но требует проверки на ложные тревоги и пропуски. | модель не заменяет инженера |
| condmon.maintenance.work_order_history | Work order history | invariant | История work orders связывает симптомы, действия, детали, время простоя и повторяемость проблем. | память обслуживания |
| condmon.maintenance.root_cause | Maintenance root cause | invariant | Root cause analysis ищет системную причину повторного отказа, а не только заменяет поврежденную деталь. | предотвращение повторов |
| condmon.maintenance.rca_5why_limit | 5 Why limit | variant | Метод 5 Why полезен для структурирования вопросов, но может упростить сложную многофакторную причину. | не превращать RCA в ритуал |
| condmon.maintenance.fmea_rpn_limit | FMEA RPN limit | variant | RPN в FMEA ранжирует риск через severity, occurrence и detection, но одинаковый RPN может скрывать разные профили риска. | смотреть компоненты оценки |
| condmon.maintenance.criticality_ranking | Asset criticality ranking | invariant | Критичность актива учитывает безопасность, производство, качество, экологию, стоимость и наличие резервирования. | приоритет ресурсов |
| condmon.maintenance.spare_part_lead_time | Spare part lead time | variant | Время поставки запасной части влияет на стратегию склада сильнее, чем цена детали сама по себе. | избежать долгого простоя |
| condmon.maintenance.pm_optimization | PM optimization | variant | Оптимизация профилактики убирает задачи, которые не уменьшают риск отказа или создают лишние вмешательства. | меньше overmaintenance |
| condmon.maintenance.lubrication_route | Lubrication route | invariant | Маршрут смазки задаёт точки, материал, количество, периодичность и способ подтверждения выполненной операции. | стандартизация смазки |
| condmon.maintenance.contamination_control | Contamination control | invariant | Контроль загрязнения предотвращает попадание частиц, воды и неправильных жидкостей в чувствительные системы. | гидравлика и подшипники |
| condmon.maintenance.post_repair_test | Post-repair test | invariant | Проверка после ремонта подтверждает, что причина устранена и оборудование вернулось к рабочим параметрам. | закрытие work order по факту |
| condmon.data.sensor_quality | Sensor data quality | invariant | Данные датчиков требуют проверки пропусков, дрейфа, выбросов, калибровки и изменения условий эксплуатации. | надежная аналитика |
| condmon.data.false_positive | False positive alarm | invariant | Ложноположительная тревога сообщает о проблеме, которой нет, и со временем снижает доверие операторов к системе. | настройка порогов |
| condmon.data.false_negative | False negative alarm | invariant | Ложноотрицательная диагностика пропускает реальную проблему и может быть опаснее шумной тревоги. | оценка чувствительности |
