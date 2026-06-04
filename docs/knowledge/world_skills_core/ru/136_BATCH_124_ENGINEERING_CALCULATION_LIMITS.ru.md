# BATCH_124 — Engineering Calculation Limits
# world_skills_core · source: world_skills_core:batch_124:engineering_calculation_limits
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| engcalc.struct.load_path | Load path | invariant | Load path описывает непрерывный путь передачи нагрузки от точки приложения через элементы к опорам и основанию. | проверка логики конструкции |
| engcalc.struct.free_body_diagram | Free-body diagram | invariant | Диаграмма свободного тела заменяет часть системы силами, моментами и реакциями для записи уравнений равновесия. | база расчёта усилий |
| engcalc.struct.support_reactions | Support reactions | invariant | Реакции опор вычисляют из равновесия сил и моментов, если число неизвестных совместимо со статической определимостью. | начало расчёта балки |
| engcalc.struct.static_determinacy | Static determinacy | invariant | Статически определимая система решается уравнениями равновесия, а статически неопределимая требует совместимости деформаций. | выбирает метод расчёта |
| engcalc.struct.shear_moment_diagram | Shear and moment diagram | invariant | Эпюры поперечной силы и изгибающего момента показывают внутренние усилия вдоль элемента под заданной нагрузкой. | ищет критические сечения |
| engcalc.struct.section_modulus | Section modulus | invariant | Модуль сечения связывает изгибающий момент с максимальным напряжением в сечении через отношение M/W. | подбор профиля |
| engcalc.struct.second_moment_area | Second moment of area | invariant | Момент инерции сечения относительно оси показывает сопротивление изгибу и влияет на прогиб. | сравнение сечений |
| engcalc.struct.deflection_limit | Deflection limit | variant | Ограничение прогиба задают отдельно от прочности, потому что элемент может быть прочным, но слишком гибким для эксплуатации. | сервисная пригодность |
| engcalc.struct.slenderness_ratio | Slenderness ratio | invariant | Гибкость сжатого элемента связывает длину, закрепление и радиус инерции с риском потери устойчивости. | проверка колонн |
| engcalc.struct.effective_length | Effective length | variant | Расчётная длина колонны зависит от условий закрепления концов и боковой раскрепленности. | влияет на устойчивость |
| engcalc.struct.buckling_load | Euler buckling load | invariant | Критическая сила Эйлера уменьшается с квадратом расчётной длины сжатого элемента. | длинные стойки опаснее |
| engcalc.struct.factor_of_safety | Factor of safety | invariant | Коэффициент запаса сравнивает допускаемую способность с ожидаемой нагрузкой и покрывает неопределенности. | управление риском |
| engcalc.struct.load_combination | Load combination | variant | Комбинации нагрузок проверяют одновременное действие постоянных, временных, ветровых, снеговых и аварийных воздействий. | не считать одну нагрузку отдельно |
| engcalc.struct.serviceability | Serviceability check | variant | Проверка эксплуатационной пригодности оценивает прогиб, вибрации, трещины или комфорт, а не только разрушение. | качество использования |
| engcalc.struct.fatigue_cycle | Fatigue cycle | invariant | Усталость возникает от повторных циклов напряжения, даже если каждое отдельное напряжение ниже предела прочности. | важна для мостов и машин |
| engcalc.struct.stress_concentration | Stress concentration | invariant | Отверстия, резкие углы и надрезы повышают локальное напряжение относительно среднего напряжения в детали. | избегать острых переходов |
| engcalc.elec.ohms_law_limit | Ohm law limit | invariant | Закон Ома применим к омическим элементам в линейном диапазоне, но не описывает все полупроводники и дуги. | не расширять формулу без проверки |
| engcalc.elec.power_dissipation | Power dissipation | invariant | Электрическая мощность, рассеиваемая элементом, превращается в тепло и должна быть ниже теплового рейтинга детали. | предотвращает перегрев |
| engcalc.elec.voltage_drop | Voltage drop | invariant | Падение напряжения на проводе растёт с током, длиной и сопротивлением проводника. | подбор сечения кабеля |
| engcalc.elec.short_circuit_current | Short-circuit current | invariant | Ток короткого замыкания ограничивается импедансом источника, проводов, трансформатора и защитных устройств. | нужна защита по отключению |
| engcalc.elec.protective_device_coordination | Protective coordination | variant | Селективность защиты означает, что ближайшее к неисправности устройство отключается раньше вышестоящего. | уменьшает масштаб аварии |
| engcalc.elec.ground_fault_path | Ground fault path | invariant | Путь замыкания на землю должен иметь достаточно низкий импеданс, чтобы защита сработала вовремя. | основа электробезопасности |
| engcalc.elec.capacitor_energy | Capacitor stored energy | invariant | Энергия конденсатора равна половине произведения ёмкости на квадрат напряжения. | опасность даже после отключения |
| engcalc.elec.inductor_transient | Inductor transient | invariant | Индуктивность сопротивляется быстрому изменению тока и может создавать перенапряжение при разрыве цепи. | нужны диоды и снабберы |
| engcalc.thermal.heat_balance | Heat balance | invariant | Тепловой баланс сравнивает поступающее, уходящее и запасаемое тепло в системе. | основа HVAC и охлаждения |
| engcalc.thermal.conduction_resistance | Conduction resistance | invariant | Тепловое сопротивление слоя растёт с толщиной и падает с теплопроводностью и площадью. | расчет утепления |
| engcalc.thermal.convection_coefficient | Convection coefficient | variant | Коэффициент конвекции зависит от скорости потока, геометрии, свойств жидкости и режима течения. | нельзя брать универсальным |
| engcalc.thermal.radiation_fourth_power | Thermal radiation | invariant | Лучистый теплообмен зависит от четвертой степени абсолютной температуры поверхности. | важен при высоких температурах |
| engcalc.thermal.u_value | U-value | invariant | U-value показывает теплопередачу через ограждение и равен обратной величине суммарного термического сопротивления. | сравнение окон и стен |
| engcalc.thermal.thermal_bridge | Thermal bridge | variant | Тепловой мост возникает там, где локально высокая теплопроводность обходит основной слой изоляции. | вызывает потери и конденсат |
| engcalc.fluid.continuity_equation | Continuity equation | invariant | Уравнение неразрывности связывает расход, площадь сечения и скорость потока для сохраняемой массы. | расчет труб и каналов |
| engcalc.fluid.bernoulli_limit | Bernoulli limit | invariant | Уравнение Бернулли применимо к идеализированному потоку и требует поправок на потери, насосы и турбулентность. | не считать реальные трубы идеальными |
| engcalc.fluid.reynolds_number | Reynolds number | invariant | Число Рейнольдса сравнивает инерционные и вязкие силы и помогает отличать ламинарный режим от турбулентного. | выбор формулы сопротивления |
| engcalc.fluid.head_loss | Head loss | invariant | Потери напора в трубе растут с длиной, шероховатостью, скоростью и местными сопротивлениями. | подбор насосов |
| engcalc.fluid.pump_curve | Pump curve | variant | Кривая насоса показывает связь расхода и напора, а рабочая точка возникает на пересечении с кривой системы. | согласование насоса и сети |
| engcalc.fluid.npsh_margin | NPSH margin | variant | Запас NPSH нужен, чтобы давление на входе насоса не опускалось до кавитационного режима. | защита насоса |
| engcalc.fluid.water_hammer | Water hammer | invariant | Гидроудар возникает при быстром изменении скорости жидкости и создаёт кратковременный скачок давления. | нужны плавные клапаны |
| engcalc.control.stability_margin | Stability margin | invariant | Запас устойчивости показывает, насколько система управления далека от самовозбуждения при изменении усиления или фазы. | избегать колебаний |
| engcalc.control.sampling_rate | Sampling rate | invariant | Частота дискретизации должна быть достаточно выше полезной частоты сигнала, чтобы избежать алиасинга. | корректное измерение |
| engcalc.control.sensor_calibration | Sensor calibration | invariant | Калибровка датчика связывает измеренный сигнал с эталонным значением и документирует погрешность. | делает измерения доверенными |
| engcalc.reliability.mtbf_limit | MTBF limit | variant | MTBF описывает среднее время между отказами в популяции, но не гарантирует срок службы конкретного экземпляра. | не путать статистику с обещанием |
| engcalc.reliability.single_point_failure | Single point failure | invariant | Single point failure — элемент, отказ которого один способен остановить всю систему. | искать резервирование |
| engcalc.reliability.derating | Derating | variant | Derating использует компонент ниже предельных параметров, чтобы уменьшить тепловой и электрический стресс. | повышает надежность |
| engcalc.reliability.maintenance_interval | Maintenance interval | variant | Интервал обслуживания выбирают по риску отказа, условиям эксплуатации, критичности и фактическому состоянию. | не только календарь |
