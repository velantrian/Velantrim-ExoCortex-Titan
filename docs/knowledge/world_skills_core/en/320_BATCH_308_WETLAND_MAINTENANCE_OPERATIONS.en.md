# BATCH 308: Wetland Maintenance Operations

**KnowledgeUnits:** 44  
**Namespace:** `wetlandops.*`  
**Scope:** гидрология, растительность, invasive control, доступ, inspections, sediment, wildlife и compliance.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| wetlandops.hydrology.water_budget | водный баланс wetland | MODEL | Водный баланс складывается из precipitation, inflow, groundwater, evapotranspiration и outflow. | Помогает понять, почему участок пересыхает или переувлажняется. |
| wetlandops.hydrology.hydroperiod | hydroperiod | MODEL | Hydroperiod описывает глубину, длительность и сезонность стояния воды. | Определяет, какие растения и животные могут устойчиво жить в wetland. |
| wetlandops.hydrology.staff_gauge | staff gauge | MEASUREMENT | Простая рейка показывает уровень воды относительно фиксированной отметки. | Дает дешевый долгосрочный ряд для maintenance decisions. |
| wetlandops.hydrology.control_structure | water control structure | METHOD | Шлюз, stop logs или weir регулируют глубину и отток. | Позволяет поддерживать habitat goals без постоянной перестройки участка. |
| wetlandops.hydrology.drawdown | seasonal drawdown | METHOD | Временное снижение уровня воды используют для vegetation reset, sediment exposure или ремонта. | Нужен план, чтобы не нарушить nesting, fish passage или permits. |
| wetlandops.hydrology.blocked_outlet | забитый outlet | FAILURE_MODE | Outlet забивается debris, sediment, beaver activity или vegetation mats. | Может вызвать flooding upstream и loss of designed flow. |
| wetlandops.vegetation.native_zone | зона native vegetation | RECORD | Посадки и естественные communities картируют по влажности, глубине и disturbance. | Позволяет отличать целевую растительность от unwanted succession. |
| wetlandops.vegetation.percent_cover | percent cover survey | MEASUREMENT | Покрытие видов оценивают по transects, quadrats или mapped polygons. | Дает численный критерий успеха maintenance и restoration. |
| wetlandops.vegetation.establishment_window | окно укоренения | HEURISTIC | Молодые wetland plants особенно уязвимы к flood, drought, geese, weeds и trampling. | Первые сезоны требуют чаще проверять survival и protection. |
| wetlandops.vegetation.mowing_timing | timing mowing | DECISION_RULE | Кошение планируют вне nesting windows и до seed set unwanted species. | Снижает конфликт между habitat protection и vegetation control. |
| wetlandops.vegetation.buffer_strip | upland buffer strip | METHOD | Буфер вокруг wetland задерживает sediment, nutrients и human disturbance. | Maintenance участка зависит не только от самой воды, но и от edge zone. |
| wetlandops.invasive.early_detection | early detection invasive | METHOD | Новые invasive patches ищут маленькими пятнами по краям, trails, inflows и disturbed soil. | Раннее удаление дешевле, чем борьба с крупной монокультурой. |
| wetlandops.invasive.treatment_log | журнал treatment | RECORD | Для каждого treatment фиксируют species, method, area, date, weather, crew и follow-up. | Показывает, что реально сработало и где нужен повтор. |
| wetlandops.invasive.disposal_control | disposal control | SAFETY_RULE | Removed biomass и seeds утилизируют так, чтобы не распространять propagules. | Иначе maintenance сам разносит invasive species. |
| wetlandops.invasive.followup_interval | follow-up interval | DECISION_RULE | Повторный обход назначают по biology species и сезону прорастания. | Уменьшает regrowth после первого treatment. |
| wetlandops.invasive.access_cleaning | очистка экипировки | METHOD | Boots, tools и machinery очищают между участками. | Предотвращает перенос семян, фрагментов и pathogens. |
| wetlandops.access.boardwalk_check | проверка boardwalk | INSPECTION | Boardwalk проверяют на slippery surfaces, loose boards, railings, rot и trip hazards. | Поддерживает безопасный public access без повреждения wetland soils. |
| wetlandops.access.trail_edge | trail edge control | METHOD | Края trail обозначают, восстанавливают shortcuts и закрывают muddy braids. | Снижает trampling и расширение disturbed corridor. |
| wetlandops.access.service_route | service route | RECORD | Для техники определяют допустимые routes, seasons, load limits и no-go zones. | Предотвращает rutting и compaction hydric soils. |
| wetlandops.access.signage | signage maintenance | METHOD | Signs сообщают правила, sensitive areas, closures, dogs, drones и contact info. | Снижает нарушения через ясные ожидания. |
| wetlandops.inspection.routine_cycle | routine inspection cycle | METHOD | Inspection cycle включает уровень воды, structures, vegetation, access, erosion и wildlife issues. | Делает maintenance предсказуемым, а не только реакцией на жалобы. |
| wetlandops.inspection.after_storm | post-storm inspection | METHOD | После storms проверяют debris, overtopping, erosion, blocked culverts и damaged trails. | Быстро выявляет угрозы flooding и public safety. |
| wetlandops.inspection.photo_log | photo log | RECORD | Фото привязывают к fixed points, issue IDs и dates. | Доказывает изменение состояния и качество repair. |
| wetlandops.inspection.issue_priority | priority issue ranking | DECISION_RULE | Issues ранжируют по safety, hydrologic function, permit risk, habitat impact и cost. | Помогает выбирать работу при ограниченной crew capacity. |
| wetlandops.sediment.forebay | sediment forebay | METHOD | Forebay принимает грубый sediment до входа воды в основную wetland cell. | Упрощает очистку и защищает habitat core. |
| wetlandops.sediment.accumulation_survey | survey накопления sediment | MEASUREMENT | Глубину sediment сравнивают с design grades или baseline probes. | Показывает, когда нужно dredging или upstream erosion control. |
| wetlandops.sediment.dredging_trigger | trigger dredging | DECISION_RULE | Dredging рассматривают при потере storage, blocked flow или ухудшении water quality. | Избегает лишнего вмешательства, но не пропускает functional failure. |
| wetlandops.sediment.turbidity_control | turbidity control | SAFETY_RULE | Работы с sediment требуют silt curtains, timing и downstream monitoring. | Снижает временное загрязнение во время maintenance. |
| wetlandops.wildlife.nesting_window | nesting window | CONSTRAINT | Многие работы ограничивают в breeding и nesting seasons. | Предотвращает нарушение wildlife protection rules. |
| wetlandops.wildlife.beaver_activity | beaver activity management | METHOD | Beaver dams оценивают по flood risk, habitat benefit, infrastructure conflict и legal status. | Не всякая плотина проблема; решение зависит от контекста. |
| wetlandops.wildlife.mosquito_balance | mosquito balance | MODEL | Комары растут при застойной мелкой воде, но predators и flow diversity могут снижать риск. | Maintenance должен избегать простого осушения как единственного решения. |
| wetlandops.wildlife.invasive_fauna | invasive fauna observation | OBSERVATION | Nutria, carp или другие species могут разрушать vegetation, banks и water clarity. | Ранний учет помогает подключить профильные службы. |
| wetlandops.wildlife.habitat_feature | habitat feature inventory | RECORD | Snags, logs, islands, shallow shelves и open water patches учитывают как habitat assets. | Не все "беспорядочные" элементы нужно удалять. |
| wetlandops.compliance.permit_conditions | permit conditions | RECORD | Permit задает water levels, work windows, mitigation ratios, reporting и allowed methods. | Maintenance без учета permit может стать violation. |
| wetlandops.compliance.wetland_boundary | boundary markers | RECORD | Jurisdictional boundary и buffer zones хранят в GIS и field markers. | Предотвращает случайную работу вне разрешенной зоны. |
| wetlandops.compliance.mitigation_success | mitigation success criteria | QUALITY_CHECK | Success criteria задают survival, percent cover, hydrology, invasive thresholds и years. | Позволяет доказать, что mitigation site выполняет обязательства. |
| wetlandops.compliance.incident_notice | notice incident | METHOD | О spills, unauthorized fill, fish kill или structural failure сообщают по установленному protocol. | Уменьшает legal risk и ускоряет response. |
| wetlandops.compliance.record_retention | retention records | RECORD | Inspection logs, photos, permits, treatments и monitoring data хранят заданный срок. | Нужны для audit, funding и передачи объекта новому оператору. |
| wetlandops.maintenance.work_order | wetland work order | RECORD | Work order описывает location, task, constraints, crew, equipment, access и closeout evidence. | Переводит ecological need в управляемую операционную задачу. |
| wetlandops.maintenance.equipment_limits | equipment limits | CONSTRAINT | Heavy equipment ограничивают по season, soil bearing, mats, slope и access route. | Защищает hydric soils и снижает repair damage. |
| wetlandops.maintenance.volunteer_task_fit | volunteer task fit | DECISION_RULE | Волонтерам дают tasks с низким risk: litter, simple planting, photo monitoring, hand pulling. | Сохраняет безопасность и качество без сложных permits. |
| wetlandops.maintenance.closeout_check | closeout check | QUALITY_CHECK | После работ проверяют debris removal, disturbed soil, signage, water flow и photos. | Закрывает задачу только после восстановления function и безопасности. |
| wetlandops.reporting.condition_score | condition score | MODEL | Score объединяет hydrology, vegetation, invasive cover, access condition и compliance issues. | Упрощает сравнение нескольких wetlands в портфеле. |
| wetlandops.reporting.adaptive_management | adaptive management note | METHOD | Management note связывает наблюдения, действия, результаты и следующий adjustment. | Делает wetland maintenance циклом обучения, а не набором разовых работ. |

