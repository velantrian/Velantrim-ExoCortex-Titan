# BATCH_110 — Automotive: How Cars Work & Maintenance
# world_skills_core · source: world_skills_core:batch_110:automotive_basics
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| carmnt.engine.ice | Двигатель внутреннего сгорания | invariant | топливо+воздух сгорают, толкают поршни | источник движения |
| carmnt.engine.four_stroke | Четыре такта | invariant | впуск, сжатие, рабочий ход, выпуск | принцип ДВС |
| carmnt.engine.cylinders | Цилиндры и поршни | invariant | возвратно-поступательное движение → вращение | мощность |
| carmnt.engine.diesel_petrol | Бензин vs дизель | variant | искра vs сжатие воспламеняют топливо | разные двигатели |
| carmnt.engine.electric | Электромобиль | variant | батарея + электромотор, без ДВС | без топлива и выхлопа |
| carmnt.engine.hybrid | Гибрид | variant | ДВС + электромотор | экономия топлива |
| carmnt.engine.cooling | Система охлаждения | invariant | антифриз отводит тепло двигателя | защита от перегрева |
| carmnt.engine.oil | Моторное масло | invariant | смазка, охлаждение, защита деталей | критично менять вовремя |
| carmnt.engine.oil_change | Замена масла | invariant | по пробегу/времени; старое масло теряет свойства | здоровье двигателя |
| carmnt.engine.air_filter | Воздушный фильтр | variant | чистый воздух в двигатель | мощность, расход |
| carmnt.engine.fuel_filter | Топливный фильтр | variant | защита от грязи в топливе | стабильная работа |
| carmnt.engine.spark_plugs | Свечи зажигания | variant | искра для воспламенения (бензин) | ровная работа |
| carmnt.engine.timing_belt | Ремень/цепь ГРМ | invariant | синхронизирует клапаны и поршни | обрыв → дорогой ремонт |
| carmnt.drive.transmission | Коробка передач | invariant | согласует обороты двигателя и колёс | тяга и скорость |
| carmnt.drive.manual_auto | Механика vs автомат | variant | ручное vs авто переключение | управление |
| carmnt.drive.clutch | Сцепление | variant | соединяет/разъединяет двигатель и КПП | переключение передач |
| carmnt.drive.differential | Дифференциал | variant | колёса вращаются с разной скоростью в повороте | управляемость |
| carmnt.drive.fwd_rwd_awd | Привод (передний/задний/полный) | variant | какие колёса ведущие | сцепление, поведение |
| carmnt.brake.system | Тормозная система | invariant | гидравлика прижимает колодки к диску | остановка авто |
| carmnt.brake.pads | Тормозные колодки | invariant | изнашиваются, требуют замены | безопасность |
| carmnt.brake.abs | ABS | invariant | предотвращает блокировку колёс при торможении | управляемость на торможении |
| carmnt.brake.fluid | Тормозная жидкость | variant | передаёт усилие; гигроскопична, меняется | надёжность тормозов |
| carmnt.tire.function | Шины | invariant | сцепление с дорогой, амортизация | безопасность |
| carmnt.tire.pressure | Давление в шинах | invariant | правильное → износ, расход, управляемость | регулярно проверять |
| carmnt.tire.tread | Протектор и износ | invariant | глубина рисунка отводит воду; лысая шина опасна | замена вовремя |
| carmnt.tire.seasonal | Сезонные шины | variant | зимние/летние по температуре | сцепление по погоде |
| carmnt.tire.rotation | Ротация шин | variant | равномерный износ | продление срока |
| carmnt.elec.battery | Аккумулятор | invariant | пуск двигателя, питание электроники | разряд → не заводится |
| carmnt.elec.alternator | Генератор | invariant | заряжает АКБ при работе двигателя | питание в движении |
| carmnt.elec.starter | Стартер | variant | прокручивает двигатель при пуске | запуск |
| carmnt.elec.lights | Световые приборы | invariant | фары, поворотники, стоп-сигналы | безопасность, ПДД |
| carmnt.fluid.coolant | Охлаждающая жидкость | variant | уровень и состояние | защита от перегрева/замерзания |
| carmnt.fluid.checks | Проверка жидкостей | invariant | масло, антифриз, тормозная, омыватель | регулярное ТО |
| carmnt.maint.schedule | Регламент ТО | invariant | плановое обслуживание по пробегу | предотвращение поломок |
| carmnt.maint.warning_lights | Лампы на панели | invariant | значки предупреждают о неисправностях | не игнорировать |
| carmnt.maint.dashboard | Приборная панель | variant | спидометр, тахометр, топливо, температура | контроль состояния |
| carmnt.safety.seatbelt | Ремень безопасности | invariant | главное средство защиты при ДТП | спасает жизни |
| carmnt.safety.airbag | Подушки безопасности | variant | дополняют ремень при ударе | защита |
| carmnt.safety.distance | Дистанция и тормозной путь | invariant | растёт с квадратом скорости | безопасное вождение |
| carmnt.safety.aquaplaning | Аквапланирование | variant | плёнка воды → потеря сцепления | снизить скорость в дождь |
| carmnt.eco.fuel_economy | Экономия топлива | variant | плавная езда, давление шин, ТО | расход и затраты |
| carmnt.eco.emissions | Выхлоп и катализатор | variant | снижение вредных газов | экология, нормы |
| carmnt.problem.wont_start | Не заводится | invariant | АКБ, стартер, топливо, зажигание — диагностика | поиск причины |
| carmnt.problem.overheating | Перегрев двигателя | invariant | остановиться, не открывать горячую крышку | предотвращение поломки |
