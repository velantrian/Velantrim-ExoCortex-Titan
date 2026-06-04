# BATCH 307: Watershed Monitoring Operations

**KnowledgeUnits:** 44  
**Namespace:** `watershedops.*`  
**Scope:** участки наблюдений, отбор проб, расход воды, качество воды, habitat checks, QA данных, волонтеры и отчетность.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| watershedops.site.network_design | сеть пунктов наблюдений | METHOD | Пункты выбирают так, чтобы покрыть верховья, притоки, устья, проблемные зоны и контрольные участки. | Дает данные, которые объясняют не только факт загрязнения, но и вероятный источник. |
| watershedops.site.reference_reach | эталонный участок | MODEL | Reference reach показывает состояние потока при минимальном влиянии нарушений в том же регионе. | Помогает отличать природную изменчивость от деградации. |
| watershedops.site.access_notes | записи доступа к участку | RECORD | Для каждого site фиксируют координаты, владельца, ключи, сезонные ограничения, hazards и безопасный маршрут. | Снижает срывы выездов и риск захода на неправильный участок. |
| watershedops.site.photo_points | постоянные фототочки | METHOD | Фотографии делают с одинаковых точек, направления и высоты в повторных обходах. | Делает изменение берегов, растительности и эрозии видимым во времени. |
| watershedops.site.station_id_control | контроль ID станции | CONSTRAINT | Один site не должен иметь несколько нестыкующихся названий в полевых листах, лаборатории и базе. | Предотвращает потерю проб и ложные временные ряды. |
| watershedops.sampling.plan_window | окно отбора проб | METHOD | Даты отбора задают по сезону, погоде, базовому расходу или storm-event режиму. | Позволяет сравнивать похожие гидрологические условия. |
| watershedops.sampling.grab_sample | разовая проба воды | METHOD | Grab sample отражает состояние воды в конкретной точке и моменте. | Подходит для регулярного мониторинга, но не заменяет непрерывные датчики. |
| watershedops.sampling.composite_sample | составная проба | METHOD | Composite sample объединяет несколько подпроб по времени или потоку. | Сглаживает краткие пики и полезна для средних нагрузок. |
| watershedops.sampling.bottle_label | этикетка бутылки | RECORD | На бутылке указывают site ID, дату, время, параметр, консервант, отборщика и уникальный sample ID. | Минимизирует путаницу между полем, транспортом и лабораторией. |
| watershedops.sampling.field_blank | полевой blank | QUALITY_CHECK | Blank проверяет загрязнение от бутылок, воды, воздуха или действий отборщика. | Помогает отличить реальный сигнал от contamination artifact. |
| watershedops.sampling.duplicate_sample | дубликат пробы | QUALITY_CHECK | Duplicate sample отбирают рядом и сравнивают с основной пробой. | Показывает воспроизводимость отбора и лабораторного анализа. |
| watershedops.sampling.chain_custody | цепочка custody | RECORD | Chain of custody фиксирует передачу проб, время, подписи, температуру и состояние контейнеров. | Делает результаты пригодными для официальных решений и enforcement. |
| watershedops.flow.stage_reading | показание уровня воды | MEASUREMENT | Stage reading фиксирует высоту водной поверхности относительно staff gauge или датчика. | Уровень нужен для расхода, flood response и сравнения трендов. |
| watershedops.flow.rating_curve | кривая уровень-расход | MODEL | Rating curve связывает stage с discharge на конкретном сечении. | Позволяет получать расход из частых измерений уровня. |
| watershedops.flow.velocity_area | метод скорость-площадь | METHOD | Расход считают через площадь сечения и среднюю скорость по вертикалям. | Дает field check для калибровки rating curve. |
| watershedops.flow.cross_section | поперечное сечение | RECORD | Сечение описывает форму русла, глубины, берега, контрольные точки и изменения после паводков. | Показывает, когда старые расчеты расхода перестают быть надежными. |
| watershedops.flow.baseflow_note | отметка базового стока | HEURISTIC | Baseflow отмечают после сухого периода, когда поток в основном питается подземными водами. | Помогает отделять хронические источники загрязнения от storm runoff. |
| watershedops.flow.storm_event_sampling | отбор во время ливня | METHOD | Storm-event sampling планируют по прогнозу, rising limb, peak и falling limb гидрографа. | Позволяет увидеть загрязнение, которое не появляется в сухую погоду. |
| watershedops.waterquality.temp_do | температура и DO | MEASUREMENT | Температура воды влияет на растворенный кислород и стресс для водных организмов. | Объясняет сезонные fish kill risks и биологические изменения. |
| watershedops.waterquality.ph_conductivity | pH и conductivity | MEASUREMENT | pH показывает кислотность, а conductivity отражает растворенные ионы. | Быстрый скрининг выявляет mine drainage, солевой runoff или wastewater influence. |
| watershedops.waterquality.turbidity_tss | мутность и TSS | MEASUREMENT | Turbidity показывает оптическую взвесь, TSS измеряет массу твердых частиц. | Связывает erosion, construction runoff и sediment load. |
| watershedops.waterquality.nutrients | nutrients monitoring | MEASUREMENT | Азот и фосфор отслеживают как драйвер eutrophication и algal blooms. | Помогает приоритизировать сельхоз, septic или urban runoff меры. |
| watershedops.waterquality.bacteria | бактериальные показатели | MEASUREMENT | E. coli или enterococci используют как индикаторы фекального загрязнения. | Нужны для bathing advisories, livestock exclusion и sewer investigation. |
| watershedops.waterquality.field_meter_cal | калибровка полевого прибора | QUALITY_CHECK | Приборы калибруют до выезда и проверяют по standards в поле. | Иначе тренд качества воды может быть drift прибора, а не реальным изменением. |
| watershedops.habitat.riparian_buffer | riparian buffer check | OBSERVATION | Оценивают ширину, непрерывность и состав прибрежной растительности. | Буфер снижает sediment, nutrients и нагрев воды. |
| watershedops.habitat.bank_stability | устойчивость берегов | OBSERVATION | Фиксируют подмыв, slumping, exposed roots, erosion scarps и livestock damage. | Указывает участки, где sediment load растет из-за русловых процессов. |
| watershedops.habitat.substrate_mix | состав дна | OBSERVATION | Дно описывают как bedrock, boulder, cobble, gravel, sand, silt или organic matter. | Substrate определяет habitat для macroinvertebrates и нереста. |
| watershedops.habitat.pool_riffle | pool-riffle структура | OBSERVATION | Наличие pools, riffles и runs показывает разнообразие гидравлических условий. | Однообразное русло обычно поддерживает меньше видов. |
| watershedops.habitat.barrier_inventory | inventory барьеров | RECORD | Culverts, small dams, perched outlets и debris jams записывают как barriers для aquatic passage. | Помогает планировать восстановление связности водотока. |
| watershedops.bio.macroinvertebrate_index | индекс макробеспозвоночных | MODEL | Macroinvertebrates используют как биологический интегратор качества воды и habitat. | Показывает долгосрочное состояние, даже если химическая проба была нормальной. |
| watershedops.bio.algae_cover | покрытие водорослями | OBSERVATION | Algae cover фиксируют по extent, thickness, color и location. | Связывает nutrients, свет, температуру и flow regime. |
| watershedops.qa.field_sheet_completeness | полнота field sheet | QUALITY_CHECK | Листы проверяют на site ID, время, погоду, flow condition, приборы, initials и комментарии. | Неполная полевая запись снижает доверие к данным. |
| watershedops.qa.data_flag_codes | коды флагов данных | RECORD | Флаги отмечают estimated, rejected, below detection, equipment issue или holding-time exceedance. | Пользователь базы видит ограничения результата. |
| watershedops.qa.range_check | range check | QUALITY_CHECK | Значения сравнивают с допустимыми физическими и историческими диапазонами site. | Быстро выявляет единицы измерения, опечатки и sensor failures. |
| watershedops.qa.time_series_gap | разрыв временного ряда | FAILURE_MODE | Missing dates возникают из-за паводка, льда, доступа, отказа датчика или лабораторной ошибки. | Gaps нужно явно объяснять, чтобы тренды не интерпретировались неверно. |
| watershedops.qa.metadata_dictionary | словарь metadata | RECORD | Для параметров фиксируют units, method, detection limit, instrument и lab method code. | Делает данные переносимыми между программами и годами. |
| watershedops.volunteer.training_checkoff | checkoff обучения волонтеров | METHOD | Волонтеру подтверждают навыки: site access, safety, sampling, meter care, forms и custody. | Повышает качество citizen science данных. |
| watershedops.volunteer.pairing_rule | правило парной работы | SAFETY_RULE | На удаленных или slippery sites волонтеры работают минимум парами. | Снижает риск травм и потери связи. |
| watershedops.volunteer.equipment_kit | field kit list | RECORD | Kit включает bottles, gloves, labels, cooler, ice packs, meter, standards, forms и PPE. | Предотвращает неполные выезды и rejected samples. |
| watershedops.reporting.station_summary | station summary | RECORD | Summary объединяет site map, период наблюдений, параметры, тренды, flags и основные источники риска. | Дает краткое объяснение состояния участка для жителей и управленцев. |
| watershedops.reporting.load_estimate | оценка pollutant load | MODEL | Load оценивают как концентрацию, умноженную на расход за период. | Позволяет сравнить вклад притоков и эффективность restoration projects. |
| watershedops.reporting.hotspot_map | карта hotspot | METHOD | Hotspots показывают участки с повторяющимися exceedances, erosion или habitat stress. | Помогает направлять field crews и funding туда, где эффект выше. |
| watershedops.reporting.public_advisory | public advisory trigger | DECISION_RULE | Advisory выпускают при превышении thresholds, опасных conditions или подтвержденном загрязнении. | Переводит мониторинг в понятное предупреждение для людей. |
| watershedops.reporting.annual_review | annual watershed review | METHOD | Годовой обзор сравнивает тренды, gaps, completed actions и новые приоритеты. | Закрывает цикл: monitoring → decision → action → monitoring. |
