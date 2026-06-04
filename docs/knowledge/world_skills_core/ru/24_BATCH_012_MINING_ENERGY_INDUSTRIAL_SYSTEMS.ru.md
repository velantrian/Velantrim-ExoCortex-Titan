# ⚡ Batch 012 — Mining, Energy & Industrial Systems

**Язык:** русский  
**Статус:** 50K batch 012 / seed units / не L3 truth  
**Цель:** добавить практическое знание о добыче сырья, энергетике, промышленных системах, ресурсах и industrial safety.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `mining.exploration.geological_mapping` | METHOD | Геологическое картирование ищет структуры, породы и признаки полезных ископаемых. | Требует полевых данных и интерпретации. | geology |
| `mining.exploration.geophysical_survey` | METHOD | Геофизика измеряет магнитные, гравитационные, электрические или сейсмические свойства. | Даёт косвенные признаки, не прямое доказательство руды. | geology |
| `mining.exploration.core_drilling` | METHOD | Керновое бурение извлекает цилиндр породы для анализа. | Дорого, но даёт прямую информацию. | mining |
| `mining.ore_grade` | METRIC | Содержание полезного компонента в руде определяет экономическую ценность. | Зависит от цены, технологии и примесей. | economics |
| `mining.cutoff_grade` | DECISION_RULE | Cutoff grade отделяет руду от пустой породы экономически. | Меняется с рынком и технологией. | mining_finance |
| `mining.open_pit` | METHOD | Открытая добыча снимает породу уступами сверху вниз. | Подходит для неглубоких залежей; большой след на ландшафте. | mining |
| `mining.underground_shaft` | METHOD | Подземная добыча использует шахты, штреки и вентиляцию. | Риски: обрушение, газ, вода, пожар. | safety |
| `mining.blasting` | PROCESS | Взрывные работы дробят породу для выемки. | Требуют лицензии, расчёта и зоны безопасности. | high_risk |
| `mining.haul_road` | INFRA | Карьерные дороги рассчитаны на тяжёлую технику и уклон. | Пыль, торможение и водоотвод критичны. | transport |
| `mining.crushing` | PROCESS | Дробление уменьшает размер породы перед измельчением или сортировкой. | Энергозатратно и пылеопасно. | materials |
| `mining.grinding` | PROCESS | Измельчение доводит руду до размера раскрытия минералов. | Один из крупнейших потребителей энергии. | processing |
| `mining.flotation` | PROCESS | Флотация разделяет минералы по свойствам поверхности в пене. | Требует реагентов, воды, контроля pH. | chemistry |
| `mining.leaching` | PROCESS | Выщелачивание растворяет целевой компонент химическим раствором. | Риски загрязнения требуют containment. | chemistry_safety |
| `mining.smelting` | PROCESS | Плавка отделяет металл от руды при высокой температуре. | Требует энергии, флюсов, контроля выбросов. | metallurgy |
| `mining.tailings_dam` | INFRA_RISK | Хвостохранилище удерживает отходы обогащения. | Отказ дамбы может быть катастрофическим. | environment |
| `mining.acid_mine_drainage` | FAILURE_MODE | Кислотный дренаж возникает при окислении сульфидов и выносе металлов. | Может продолжаться десятилетиями. | environment |
| `mining.reclamation` | METHOD | Рекультивация восстанавливает ландшафт и снижает остаточные риски. | Нужна с начала проекта, не только в конце. | ecology |
| `quarry.aggregate` | MATERIAL_SOURCE | Карьеры щебня и песка дают заполнители для бетона и дорог. | Качество зависит от породы, формы, фракции. | construction |
| `quarry.dimension_stone` | MATERIAL_SOURCE | Блочный камень добывают для облицовки, плит и памятников. | Важны трещиноватость, цвет, полировка. | building |
| `oilgas.seismic_survey` | METHOD | Сейсморазведка строит модель подземных структур по отражениям волн. | Вероятностная интерпретация. | geology |
| `oilgas.drilling_mud` | MATERIAL | Буровой раствор охлаждает, выносит шлам и стабилизирует скважину. | Состав зависит от давления и пород. | drilling |
| `oilgas.well_casing` | COMPONENT | Обсадные трубы изолируют пласты и укрепляют скважину. | Цементирование критично. | drilling |
| `oilgas.blowout_preventer` | SAFETY_SYSTEM | BOP помогает предотвратить неконтролируемый выброс из скважины. | Требует тестов и обслуживания. | high_risk |
| `oilgas.refining_distillation` | PROCESS | Перегонка нефти разделяет фракции по температурам кипения. | Не создаёт продукты сама по себе, только разделяет. | refining |
| `oilgas.cracking` | PROCESS | Крекинг разбивает тяжёлые углеводороды на более лёгкие. | Катализ и температура определяют выход. | chemistry |
| `oilgas.pipeline_pigging` | METHOD | Pigging очищает, инспектирует или разделяет продукты в трубопроводе. | Нужны камеры запуска и приёма. | pipeline |
| `energy.coal_boiler` | ENERGY_SYSTEM | Угольный котёл превращает химическую энергию топлива в пар. | Высокие выбросы требуют очистки. | power |
| `energy.gas_turbine` | ENERGY_SYSTEM | Газовая турбина сжигает газ и вращает турбину горячими газами. | Быстрый запуск, чувствительна к температуре воздуха. | power |
| `energy.steam_turbine` | ENERGY_SYSTEM | Паровая турбина превращает энергию пара во вращение. | Используется в ТЭС, АЭС, промышленности. | power |
| `energy.combined_cycle` | ENERGY_SYSTEM | Combined cycle использует газовую и паровую турбины для большей эффективности. | Требует сложной тепловой схемы. | power |
| `energy.nuclear.fission_heat` | MECHANISM | Деление ядер выделяет тепло, которое превращают в пар и электричество. | High-risk domain, строгие регуляции. | nuclear |
| `energy.nuclear.control_rods` | COMPONENT | Управляющие стержни поглощают нейтроны и регулируют реакцию. | Часть многослойной системы безопасности. | nuclear |
| `energy.nuclear.coolant_loop` | SYSTEM | Контур теплоносителя переносит тепло из реактора. | Давление, коррозия и резервирование критичны. | nuclear |
| `energy.nuclear.spent_fuel` | WASTE_STREAM | Отработавшее ядерное топливо остаётся радиоактивным и тепловыделяющим. | Требует охлаждения, защиты и долгого управления. | nuclear_safety |
| `energy.hydro.dam_head` | ENERGY_MECHANISM | Напор воды создаёт потенциальную энергию для турбины. | Зависит от высоты и расхода. | hydrology |
| `energy.hydro.turbine` | EQUIPMENT | Гидротурбина преобразует поток воды во вращение. | Тип зависит от напора и расхода. | power |
| `energy.wind.blade_aerodynamics` | MECHANISM | Лопасти ветровой турбины извлекают энергию из воздушного потока. | Ограничены скоростью ветра, шумом, материалами. | wind |
| `energy.wind.capacity_factor` | METRIC | Capacity factor показывает долю фактической выработки от максимальной. | Зависит от ресурса ветра и простоя. | power |
| `energy.solar.pv_cell` | COMPONENT | PV-ячейка превращает свет в электричество через фотоэлектрический эффект. | Выход зависит от света, температуры, деградации. | electronics |
| `energy.solar.inverter` | COMPONENT | Инвертор превращает DC от панелей в AC для сети/дома. | Требует защиты и синхронизации. | power_electronics |
| `energy.solar.thermal_collector` | COMPONENT | Солнечный коллектор нагревает жидкость или воздух солнечным теплом. | Отличается от PV. | heating |
| `energy.geothermal.heat_exchange` | ENERGY_SYSTEM | Геотермия использует тепло земли напрямую или через тепловые насосы. | Ресурс зависит от геологии. | earth |
| `energy.biomass.combustion` | ENERGY_SYSTEM | Биомасса сжигается для тепла или электроэнергии. | Не всегда climate-neutral; важна цепочка поставок. | forestry |
| `energy.battery.grid_storage` | ENERGY_SYSTEM | Аккумуляторы помогают сглаживать спрос, генерацию и частоту сети. | Ограничены ёмкостью, ресурсом, безопасностью. | storage |
| `energy.demand_response` | GRID_METHOD | Demand response временно меняет потребление для балансировки сети. | Требует стимулов и управления нагрузкой. | grid |
| `grid.frequency_control` | GRID_CONTROL | Частота сети отражает баланс генерации и потребления. | Отклонения опасны для оборудования и стабильности. | power |
| `grid.transformer_substation` | INFRA | Подстанции меняют напряжение и распределяют энергию. | Требуют защиты, охлаждения, обслуживания. | power |
| `grid.protection_relay` | SAFETY_SYSTEM | Релейная защита отключает аварийные участки сети. | Настройки должны быть селективными. | electricity |
| `grid.black_start` | RECOVERY_METHOD | Black start восстанавливает энергосистему после полного отключения. | Нужны специальные источники и процедура. | resilience |
| `grid.microgrid` | ENERGY_SYSTEM | Microgrid может работать локально и иногда изолироваться от основной сети. | Требует управления генерацией и нагрузкой. | resilience |
| `resource.water_energy_nexus` | MODEL | Вода нужна энергии, а энергия нужна воде. | Важно для засух, охлаждения, насосов. | systems |
| `resource.material_criticality` | RISK_MODEL | Criticality оценивает важность материала и риск поставок. | Зависит от географии, заменителей, переработки. | supply_chain |
| `resource.recycling_metals` | PROCESS | Переработка металлов снижает потребность в руде и энергии. | Сортировка сплавов критична. | circular_economy |
| `resource.strategic_reserve` | POLICY_TOOL | Стратегические резервы хранят важные ресурсы на случай кризиса. | Имеют стоимость и политические риски. | economy |
| `industrial.heat_exchanger` | EQUIPMENT | Теплообменник передаёт тепло между средами без их смешивания. | Fouling снижает эффективность. | process |
| `industrial.boiler_safety` | SAFETY_RULE | Котлы работают под давлением и требуют защиты от перегрева/перепрессовки. | High-risk equipment. | safety |
| `industrial.compressed_air_leak` | FAILURE_MODE | Утечки сжатого воздуха часто дорого теряют энергию. | Система требует поиска и ремонта утечек. | maintenance |
| `industrial.process_control` | SYSTEM | Process control удерживает параметры процесса через датчики и регуляторы. | Не заменяет safety interlocks. | automation |
| `industrial.scada` | SYSTEM | SCADA наблюдает и управляет распределёнными промышленными процессами. | Требует cybersecurity. | automation |
| `industrial.instrumentation_loop` | SYSTEM | Измерительный контур связывает датчик, сигнал, контроллер и исполнительный механизм. | Калибровка важна для качества. | control |
| `industrial.maintenance_predictive` | METHOD | Predictive maintenance использует признаки состояния для ремонта до отказа. | Нужны данные и пороги. | operations |
| `industrial.lockout_tagout` | SAFETY_RULE | LOTO изолирует энергию оборудования перед ремонтом. | Требует процедуры, замков, проверки нулевой энергии. | safety |
| `industrial.permit_to_work` | SAFETY_SYSTEM | Permit-to-work формально разрешает опасные работы после оценки риска. | Используется для горячих работ, высоты, confined space. | safety |
| `industrial.confined_space` | HIGH_RISK | Замкнутые пространства опасны кислородом, газами, ловушками и доступом. | Нужна процедура и rescue plan. | safety |
| `industrial.hazardous_area` | SAFETY_ZONE | Hazardous area классифицирует зоны с риском взрывоопасной атмосферы. | Требует специального оборудования. | explosion |
| `industrial.fire_triangle` | MODEL | Пожар требует топлива, кислорода и источника зажигания. | Удаление одного элемента снижает риск. | safety |
| `industrial.explosion_venting` | SAFETY_SYSTEM | Explosion venting направляет давление взрыва в безопасную сторону. | Требует расчёта и обслуживания. | safety |
| `industrial.emergency_shutdown` | SAFETY_SYSTEM | ESD быстро переводит процесс в безопасное состояние. | Не должен зависеть от обычного управления. | safety |
| `industrial.process_hazard_analysis` | METHOD | PHA системно ищет опасности процесса и меры защиты. | Методы: HAZOP, what-if, checklist. | safety |
| `industrial.management_of_change` | SAFETY_SYSTEM | MOC оценивает риски изменений перед внедрением. | Малое изменение может сломать защиту. | safety |

---

## 📊 Batch 012 summary

```text
new units: 70
main layers:
  mining and resource extraction
  oil, gas, power systems
  grid and industrial operations
  process safety
```
