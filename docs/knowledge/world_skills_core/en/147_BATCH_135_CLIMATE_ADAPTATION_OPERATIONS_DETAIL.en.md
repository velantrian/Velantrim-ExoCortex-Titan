# BATCH_135 — Climate Adaptation Operations Detail
# world_skills_core · source: world_skills_core:batch_135:climate_adaptation_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| climadapt.heat.heat_action_plan | Heat action plan | invariant | План действий при жаре связывает прогноз, предупреждения, охлаждающие места, проверку уязвимых людей и медицинскую готовность. | снижает смертность от жары |
| climadapt.heat.cooling_center | Cooling center | variant | Cooling center предоставляет прохладное безопасное место во время жары, но требует доступности, транспорта, воды и коммуникации. | защита уязвимых групп |
| climadapt.heat.urban_heat_island | Urban heat island mitigation | invariant | Снижение городского теплового острова использует тень, деревья, отражающие поверхности, вентиляцию улиц и уменьшение waste heat. | городская адаптация |
| climadapt.heat.cool_roof | Cool roof | variant | Светлая или отражающая кровля снижает поглощение солнечного тепла и может уменьшить нагрузку на охлаждение здания. | особенно важно летом |
| climadapt.heat.worker_rest_cycle | Heat work-rest cycle | variant | Режим work-rest при жаре адаптирует нагрузку, перерывы, воду и тень к температуре, влажности, одежде и акклиматизации. | безопасность труда |
| climadapt.heat.nighttime_temperature | Nighttime heat risk | invariant | Высокая ночная температура повышает риск, потому что организм и здания не успевают восстановиться после дневной жары. | важен не только дневной максимум |
| climadapt.flood.floodplain_mapping | Floodplain mapping | invariant | Карта пойм и зон затопления показывает вероятность и глубину воды, но должна обновляться при изменении климата и застройки. | не строить вслепую |
| climadapt.flood.freeboard | Flood freeboard | invariant | Freeboard добавляет запас высоты над расчетным уровнем воды, чтобы покрыть неопределенность и волны. | защита здания |
| climadapt.flood.backflow_prevention | Backflow prevention | invariant | Обратный клапан или защита от подпора снижает риск попадания сточных вод в здание при перегрузке сети. | санитарная защита |
| climadapt.flood.permeable_surface | Permeable surface | variant | Водопроницаемые покрытия уменьшают поверхностный сток, если грунт, обслуживание и загрязнение позволяют инфильтрацию. | ливневая нагрузка |
| climadapt.flood.detention_basin | Stormwater detention basin | invariant | Detention basin временно удерживает ливневую воду и выпускает ее медленнее, снижая пик потока. | защита нижележащих сетей |
| climadapt.flood.sump_pump_redundancy | Sump pump redundancy | variant | Резервирование sump pump требует второго насоса, питания или сигнализации, потому что паводки часто совпадают с отключениями энергии. | защита подвалов |
| climadapt.drought.water_restriction_stage | Water restriction stage | variant | Ступени ограничения воды заранее связывают уровень дефицита с допустимым использованием, коммуникацией и enforcement. | управляемая экономия |
| climadapt.drought.leak_detection | Drought leak detection | invariant | При засухе сокращение утечек в сетях может быть дешевле и быстрее, чем поиск нового источника воды. | сохранить ресурс |
| climadapt.drought.reuse_water | Water reuse | variant | Повторное использование воды требует разделения потоков, качества под назначение, контроля рисков и понятной маркировки. | не вся вода должна быть питьевой |
| climadapt.drought.soil_moisture | Soil moisture monitoring | variant | Мониторинг влажности почвы помогает поливать растения по потребности, а не по календарю. | экономия воды |
| climadapt.drought.drought_tolerant_landscape | Drought-tolerant landscape | variant | Засухоустойчивый ландшафт снижает потребность в поливе через выбор растений, мульчу, почву и зонирование воды. | устойчивые дворы и города |
| climadapt.drought.water_loss_audit | Water loss audit | invariant | Аудит потерь воды разделяет физические утечки, коммерческие потери, ошибки учета и несанкционированное потребление. | управлять водоканалом |
| climadapt.wildfire.defensible_space | Defensible space | invariant | Defensible space снижает горючую нагрузку вокруг здания через расстояние, растительность, уборку и доступ пожарных. | защита от ландшафтных пожаров |
| climadapt.wildfire.ember_resistance | Ember resistance | invariant | Устойчивость к тлеющим частицам требует защиты вентиляционных отверстий, кровли, желобов, щелей и горючих материалов. | здания часто загораются от искр |
| climadapt.wildfire.smoke_filtration | Wildfire smoke filtration | variant | Защита от дыма пожара требует фильтрации воздуха, герметизации утечек и режима вентиляции, совместимого с безопасностью помещения. | качество воздуха внутри |
| climadapt.wildfire.evacuation_trigger | Wildfire evacuation trigger | variant | Триггеры эвакуации должны связывать угрозу, маршруты, время, уязвимых людей, животных и коммуникационные каналы. | не ждать последней минуты |
| climadapt.wildfire.fuel_break | Fuel break | variant | Fuel break снижает непрерывность горючего материала, но требует обслуживания и не гарантирует остановку огня при сильном ветре. | элемент, а не магическая защита |
| climadapt.coastal.living_shoreline | Living shoreline | variant | Living shoreline использует растительность, рельеф и природные элементы для снижения эрозии и энергии волн. | альтернатива жестким стенкам |
| climadapt.coastal.seawall_limit | Seawall limit | variant | Морская стенка защищает локальный участок, но может усиливать эрозию у основания или на соседних берегах. | учитывать систему берега |
| climadapt.coastal.saltwater_intrusion | Saltwater intrusion | invariant | Проникновение соленой воды в водоносный горизонт ухудшает пресную воду при повышении уровня моря или чрезмерной откачке. | риск для скважин |
| climadapt.coastal.managed_retreat | Managed retreat | variant | Managed retreat переносит людей или активы из зоны растущего риска, когда защита становится слишком дорогой или ненадежной. | сложное социальное решение |
| climadapt.infrastructure.critical_facility_siting | Critical facility siting | invariant | Критичные объекты нужно размещать с учетом будущей жары, паводков, пожаров, доступа и резервирования. | больницы, центры связи, насосные |
| climadapt.infrastructure.redundant_power | Adaptation redundant power | invariant | Резервное питание критичных систем должно учитывать длительность события, топливо, обслуживание, тесты и безопасное подключение. | отказ сети во время бедствия |
| climadapt.infrastructure.cooling_load_growth | Cooling load growth | variant | Рост потребности в охлаждении может перегружать электросети и требует планирования мощности, эффективности и demand response. | жара влияет на энергосистему |
| climadapt.infrastructure.road_surface_heat | Road surface heat | variant | Высокая температура дорожного покрытия ускоряет колееобразование, размягчение связующего и тепловое расширение материалов. | адаптация дорожных материалов |
| climadapt.infrastructure.bridge_scour | Bridge scour under floods | invariant | Размыв опор мостов усиливается при паводках и может подорвать основание без видимого повреждения пролета. | инспекция после паводка |
| climadapt.publichealth.vector_range | Vector range shift | variant | Потепление и изменение влажности могут сдвигать ареалы переносчиков инфекций, но риск зависит от экологии и систем здравоохранения. | мониторинг, не паника |
| climadapt.publichealth.cooling_equity | Cooling equity | invariant | Доступ к охлаждению зависит от дохода, жилья, возраста, здоровья, языка, транспорта и доверия к службам. | справедливая адаптация |
| climadapt.publichealth.communication_language | Risk communication language | invariant | Предупреждения о климатическом риске должны быть понятны людям с разными языками, грамотностью, каналами связи и доверием. | сообщение должно дойти |
| climadapt.publichealth.check_in_registry | Vulnerable resident check-in | variant | Реестр проверки уязвимых жителей требует согласия, актуальных контактов, защиты данных и ясной роли ответственных. | помощь во время экстремума |
| climadapt.planning.scenario_planning | Climate scenario planning | invariant | Сценарное планирование проверяет решения при нескольких будущих условиях, а не при единственном прогнозе. | устойчивость к неопределенности |
| climadapt.planning.adaptive_pathway | Adaptive pathway | variant | Adaptive pathway задает последовательность решений и триггеров, чтобы менять стратегию по мере роста риска. | не переплачивать сразу |
| climadapt.planning.no_regret_measure | No-regret measure | invariant | No-regret мера полезна при разных сценариях будущего, например снижение утечек воды или тень в городе. | хороший первый шаг |
| climadapt.planning.maladaptation | Maladaptation | invariant | Maladaptation снижает один риск, но увеличивает другой риск, неравенство, выбросы или долгосрочную уязвимость. | проверять побочные эффекты |
| climadapt.finance.resilience_benefit | Resilience benefit | variant | Выгода устойчивости включает предотвращенный ущерб, меньше простоев, здоровье, страхуемость и сохранение услуг. | обосновать инвестиции |
| climadapt.finance.lifecycle_cost | Adaptation lifecycle cost | invariant | Стоимость адаптации нужно считать по жизненному циклу: проект, строительство, обслуживание, обновление и отказ. | не только capex |
| climadapt.governance.multiagency_coordination | Multiagency coordination | invariant | Климатическая адаптация требует координации коммунальных служб, транспорта, здравоохранения, жилья, экстренных служб и финансов. | один департамент не справится |
| climadapt.governance.after_action_review | Climate event after-action review | invariant | After-action review после экстремального события фиксирует, что сработало, что нет, какие данные нужны и кто меняет план. | учиться на событиях |
