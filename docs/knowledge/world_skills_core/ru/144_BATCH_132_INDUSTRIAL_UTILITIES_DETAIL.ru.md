# BATCH_132 — Industrial Utilities Detail
# world_skills_core · source: world_skills_core:batch_132:industrial_utilities_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| indutil.compressed_air.leak_cost | Compressed air leak cost | invariant | Утечка сжатого воздуха постоянно тратит электрическую энергию компрессора и часто дороже самой детали утечки. | быстрый источник экономии |
| indutil.compressed_air.pressure_drop | Compressed air pressure drop | invariant | Падение давления в сети растет из-за малых диаметров, длинных линий, фильтров, утечек и пикового расхода. | не повышать давление вслепую |
| indutil.compressed_air.dryer_selection | Air dryer selection | variant | Осушитель сжатого воздуха выбирают по требуемой точке росы, расходу, давлению, температуре и критичности влаги. | защита пневматики |
| indutil.compressed_air.receiver_tank | Air receiver tank | invariant | Ресивер сжатого воздуха сглаживает пики потребления и снижает частоту переключений компрессора. | стабильность давления |
| indutil.compressed_air.oil_carryover | Compressor oil carryover | variant | Унос масла из компрессора загрязняет воздух, фильтры, инструмент, продукт или пневматические элементы. | контроль качества воздуха |
| indutil.compressed_air.point_of_use_filter | Point-of-use filter | variant | Фильтр у точки потребления защищает чувствительный инструмент или процесс от локальных загрязнений после магистрали. | критичные потребители |
| indutil.steam.boiler_blowdown | Boiler blowdown | invariant | Продувка котла удаляет растворенные соли и шлам, но чрезмерная продувка теряет тепло и воду. | баланс качества и энергии |
| indutil.steam.condensate_return | Condensate return | invariant | Возврат конденсата сохраняет тепло, воду и химическую обработку, снижая нагрузку на котельную. | экономия энергии |
| indutil.steam.steam_trap_role | Steam trap role | invariant | Конденсатоотводчик выпускает конденсат и неконденсируемые газы, удерживая живой пар в системе. | эффективность паровой сети |
| indutil.steam.flash_steam | Flash steam | invariant | Flash steam образуется, когда горячий конденсат попадает в область с меньшим давлением и часть воды мгновенно испаряется. | возможность рекуперации |
| indutil.steam.water_hammer | Steam water hammer | invariant | Гидроудар в паровой системе возникает при накоплении конденсата и резком переносе жидкости паром. | риск разрушения труб |
| indutil.steam.insulation_value | Steam insulation value | invariant | Теплоизоляция паропровода снижает теплопотери, ожоги персонала и образование лишнего конденсата. | безопасность и энергия |
| indutil.chilledwater.delta_t | Chilled water delta T | invariant | Разница температур подачи и обратки chilled water показывает, сколько тепла реально забирает контур. | диагностика эффективности |
| indutil.chilledwater.low_delta_t | Low delta T syndrome | variant | Low delta T возникает, когда расход воды высок, а тепловой съем мал, перегружая насосы и чиллеры. | балансировка системы |
| indutil.chilledwater.cooling_tower_approach | Cooling tower approach | invariant | Approach градирни показывает разницу между температурой выходящей воды и температурой влажного термометра воздуха. | оценка эффективности градирни |
| indutil.chilledwater.water_treatment | Cooling water treatment | invariant | Водоподготовка охлаждающей воды контролирует накипь, коррозию и биологический рост. | защита теплообмена |
| indutil.chilledwater.strainer_fouling | Strainer fouling | variant | Засорение фильтра-сетки увеличивает перепад давления и снижает расход через теплообменник или насос. | простая причина падения мощности |
| indutil.pumps.pump_curve_match | Pump curve matching | invariant | Насос должен работать около подходящей точки своей кривой, где расход, напор и КПД соответствуют системе. | избежать кавитации и перегрева |
| indutil.pumps.parallel_operation | Parallel pump operation | variant | Параллельные насосы увеличивают расход только если кривая системы позволяет, а не автоматически удваивают производительность. | оценка гидравлики |
| indutil.pumps.deadheading | Pump deadheading | invariant | Работа насоса при закрытом выходе превращает энергию в тепло и может повредить насос. | нужен минимальный расход |
| indutil.pumps.seal_flush | Mechanical seal flush | variant | Промывка уплотнения охлаждает, очищает или стабилизирует среду вокруг торцевого уплотнения насоса. | ресурс seal |
| indutil.pumps.cavitation_noise | Cavitation noise | invariant | Кавитация насоса создает шум, вибрацию и эрозию из-за образования и схлопывания паровых пузырьков. | признак плохого всасывания |
| indutil.heatexchanger.fouling_factor | Heat exchanger fouling | invariant | Загрязнение теплообменника добавляет тепловое сопротивление и увеличивает перепад давления. | потеря мощности |
| indutil.heatexchanger.counterflow | Counterflow exchanger | invariant | Противоточный теплообмен обычно эффективнее прямоточного при тех же площадях и расходах. | проектирование теплообмена |
| indutil.heatexchanger.temperature_cross | Temperature cross | variant | Temperature cross в теплообменнике указывает, что выход одной среды пересекает температурный уровень другой в сложной схеме. | проверка реалистичности расчета |
| indutil.heatexchanger.cleaning_interval | Heat exchanger cleaning interval | variant | Интервал чистки теплообменника выбирают по тренду температуры, перепада давления, энергии и стоимости остановки. | обслуживание по состоянию |
| indutil.boiler.feedwater_treatment | Boiler feedwater treatment | invariant | Питательная вода котла требует контроля жесткости, кислорода, pH и примесей, чтобы снизить накипь и коррозию. | надежность котла |
| indutil.boiler.deaerator | Deaerator role | invariant | Деаэратор удаляет растворенный кислород и газы из питательной воды перед котлом. | снижение кислородной коррозии |
| indutil.boiler.economizer | Boiler economizer | variant | Экономайзер использует тепло дымовых газов для подогрева питательной воды или другой среды. | повышение КПД |
| indutil.boiler.stack_temperature | Stack temperature trend | invariant | Рост температуры дымовых газов может указывать на загрязнение теплообменных поверхностей или ухудшение теплопередачи. | диагностика котла |
| indutil.vacuum.leak_rate | Vacuum leak rate | invariant | Скорость утечки вакуумной системы определяет, насколько быстро давление растет при отключенной откачке. | проверка герметичности |
| indutil.vacuum.pump_oil_condition | Vacuum pump oil condition | variant | Масло вакуумного насоса теряет свойства от влаги, растворителей, частиц и термического старения. | ресурс насоса |
| indutil.nitrogen.blanketing | Nitrogen blanketing | variant | Азотная подушка снижает контакт продукта с кислородом или влагой, но требует контроля давления и безопасности атмосферы. | хранение чувствительных материалов |
| indutil.water.softening | Water softening | invariant | Умягчение воды снижает жесткость, чтобы уменьшить накипь в котлах, теплообменниках и моющих процессах. | защита оборудования |
| indutil.water.reverse_osmosis | Reverse osmosis utility | variant | Обратный осмос удаляет многие растворенные вещества через мембрану, но требует предочистки и контроля загрязнения мембран. | чистая технологическая вода |
| indutil.water.deionization | Deionized water | variant | Деионизированная вода имеет низкое содержание ионов, но может быть агрессивной к некоторым материалам и быстро загрязняться. | лаборатории и процессы |
| indutil.energy.submetering | Utility submetering | invariant | Подсчет ресурсов по участкам показывает, где реально потребляются воздух, пар, вода, газ или электричество. | поиск потерь |
| indutil.energy.peak_demand | Peak demand charge | variant | Пиковая электрическая мощность может влиять на счет за энергию отдельно от общего потребления киловатт-часов. | управление нагрузками |
| indutil.energy.heat_recovery | Utility heat recovery | variant | Рекуперация тепла использует отходящее тепло компрессоров, чиллеров, печей или стоков для полезного нагрева. | снижение затрат |
| indutil.energy.load_profile | Utility load profile | invariant | Профиль нагрузки показывает изменение потребления ресурса во времени и выявляет пики, холостой ход и ночные потери. | управлять не средним, а режимом |
| indutil.operations.utility_map | Utility system map | invariant | Карта инженерных сетей показывает источники, магистрали, клапаны, приборы, потребителей и точки изоляции. | быстрее ремонт и LOTO |
| indutil.operations.isolation_valve | Isolation valve strategy | invariant | Запорная арматура должна позволять изолировать участок для ремонта без остановки всей системы, если это важно для производства. | ремонтопригодность |
| indutil.operations.critical_user | Critical utility user | variant | Критичный потребитель ресурса требует приоритета, резервирования или мониторинга, потому что его потеря останавливает ключевой процесс. | надежность производства |
| indutil.operations.utility_sla | Internal utility SLA | variant | Внутренний SLA инженерных сетей задаёт требуемое давление, температуру, качество, доступность и время реакции. | согласование ожиданий |
