# 🛠️ Batch 016 — Measurement, Tools, Repair & Maintenance

**Язык:** русский  
**Статус:** 50K batch 016 / seed units / не L3 truth  
**Цель:** добавить практическое знание о том, как измерять, проверять, чинить, обслуживать и поддерживать вещи в рабочем состоянии.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `measurement.accuracy_precision` | DISTINCTION | Accuracy — близость к истинному значению; precision — повторяемость измерений. | Можно быть точным, но смещённым. | metrology |
| `measurement.uncertainty` | MODEL | Неопределённость показывает диапазон доверия к измерению. | Не является ошибкой сама по себе. | statistics |
| `measurement.calibration_traceability` | QUALITY_SYSTEM | Traceability связывает измерение с эталонами через цепочку калибровок. | Требует документов и периодичности. | metrology |
| `measurement.resolution` | PROPERTY | Разрешение — минимальный шаг, который прибор показывает или различает. | Не равно точности. | instruments |
| `measurement.repeatability` | QUALITY | Repeatability — разброс измерений при одинаковых условиях. | Отличается от reproducibility. | quality |
| `measurement.reproducibility` | QUALITY | Reproducibility — согласие результатов при разных условиях/операторах/лабораториях. | Важно для стандартов. | quality |
| `measurement.bias` | ERROR | Bias — систематическое смещение результата. | Повторение не убирает bias. | statistics |
| `measurement.random_error` | ERROR | Случайная ошибка даёт разброс вокруг значения. | Снижается усреднением, если нет bias. | statistics |
| `measurement.significant_figures` | RULE | Значащие цифры отражают разумную точность числа. | Нельзя добавлять ложную точность. | math |
| `measurement.tolerance` | CONSTRAINT | Допуск задаёт допустимое отклонение размера или свойства. | Слишком строгий допуск повышает стоимость. | manufacturing |
| `measurement.gauge_blocks` | TOOL | Концевые меры длины используют как точные физические эталоны. | Требуют чистоты и температуры. | metrology |
| `measurement.vernier_caliper` | TOOL | Штангенциркуль измеряет наружные, внутренние размеры и глубину. | Ошибки от перекоса и давления. | tools |
| `measurement.micrometer` | TOOL | Микрометр измеряет малые размеры винтовым механизмом. | Требует нулевой проверки и чистых поверхностей. | tools |
| `measurement.dial_indicator` | TOOL | Индикатор часового типа показывает малые перемещения и биения. | Нужна жёсткая установка. | machining |
| `measurement.torque_wrench` | TOOL | Динамометрический ключ ограничивает момент затяжки. | Требует калибровки и правильной техники. | mechanics |
| `measurement.multimeter` | TOOL | Мультиметр измеряет напряжение, ток, сопротивление и другие параметры. | Неверный режим может быть опасен. | electronics |
| `measurement.oscilloscope` | TOOL | Осциллограф показывает изменение сигнала во времени. | Полоса и пробник ограничивают результат. | electronics |
| `measurement.thermometer` | TOOL | Термометр измеряет температуру через физическое свойство датчика. | Время отклика и место измерения важны. | instruments |
| `measurement.pressure_gauge` | TOOL | Манометр измеряет давление газа или жидкости. | Нужен диапазон и защита от перегрузки. | fluids |
| `measurement.flow_meter` | TOOL | Расходомер измеряет объёмный или массовый поток. | Тип зависит от среды, вязкости, загрязнений. | process |
| `measurement.scale_balance` | TOOL | Весы измеряют массу через силу или баланс. | Требуют уровня, калибровки, защиты от воздуха. | lab |
| `measurement.moisture_meter` | TOOL | Влагомер оценивает содержание воды в материале. | Метод зависит от дерева, зерна, почвы, бетона. | materials |
| `measurement.ph_meter` | TOOL | pH-метр измеряет кислотность через электродный потенциал. | Нужна калибровка буферами. | chemistry |
| `measurement.lux_meter` | TOOL | Люксметр измеряет освещённость. | Положение и спектр источника влияют на результат. | building |
| `tool.hand.hammer` | TOOL | Молоток передаёт ударную энергию через массу и скорость. | Тип зависит от задачи и материала. | tools |
| `tool.hand.screwdriver` | TOOL | Отвёртка передаёт крутящий момент на шлиц или биту. | Неправильный размер портит крепёж. | repair |
| `tool.hand.wrench` | TOOL | Ключ захватывает гайку/болт для передачи момента. | Нужен подходящий профиль и размер. | mechanics |
| `tool.hand.pliers` | TOOL | Плоскогубцы и клещи удерживают, гнут или режут материалы. | Не заменяют гаечный ключ для момента. | repair |
| `tool.hand.file` | TOOL | Напильник снимает материал множеством зубьев. | Направление и тип насечки важны. | metalwork |
| `tool.hand.clamp` | TOOL | Струбцина удерживает детали под давлением. | Слишком сильное давление может деформировать. | woodworking |
| `tool.power.drill` | TOOL | Дрель вращает сверло для отверстий или крепежа. | Скорость и сверло зависят от материала. | repair |
| `tool.power.grinder` | TOOL | Угловая шлифмашина режет и шлифует абразивным диском. | Высокий риск травм и искр. | safety |
| `tool.power.circular_saw` | TOOL | Циркулярная пила режет вращающимся диском. | Требует защиты от kickback. | wood |
| `tool.power.jigsaw` | TOOL | Лобзик режет возвратно-поступательным полотном. | Подходит для криволинейных резов. | tools |
| `tool.power.soldering_iron` | TOOL | Паяльник нагревает припой и соединяемые поверхности. | Нужны флюс, температура, вентиляция. | electronics |
| `repair.diagnosis.symptom_cause` | METHOD | Симптом — наблюдаемое проявление; причина — механизм отказа. | Один симптом может иметь много причин. | reasoning |
| `repair.diagnosis.isolate_variables` | METHOD | Изоляция переменных меняет по одному фактору, чтобы найти причину. | Требует контрольных условий. | troubleshooting |
| `repair.diagnosis.known_good_swap` | METHOD | Замена на заведомо исправный элемент проверяет подозреваемый узел. | Риск повредить исправную деталь. | repair |
| `repair.diagnosis.visual_inspection` | METHOD | Визуальный осмотр ищет трещины, перегрев, коррозию, утечки, износ. | Не выявляет все скрытые дефекты. | maintenance |
| `repair.diagnosis.listen_smell_touch` | METHOD | Звук, запах и температура могут указывать на отказ. | Использовать безопасно, не касаясь опасных частей. | safety |
| `repair.electrical.power_first` | RULE | При диагностике электроники сначала проверяют питание, землю и соединения. | Высокое напряжение требует специалиста. | electronics |
| `repair.electrical.continuity` | METHOD | Прозвонка проверяет наличие электрического соединения. | Не выполнять на цепи под напряжением. | safety |
| `repair.electrical.connector_corrosion` | FAILURE_MODE | Коррозия контактов повышает сопротивление и вызывает сбои. | Влага и соли ускоряют процесс. | electronics |
| `repair.mechanical.lubrication` | METHOD | Ремонт: Смазка снижает трение, износ и нагрев. | Неверная смазка может навредить. | mechanics |
| `repair.mechanical.alignment` | METHOD | Соосность валов, ремней и деталей снижает вибрацию и износ. | Требует измерения, не только глазом. | machines |
| `repair.mechanical.bearing_noise` | FAILURE_MODE | Шум подшипника может указывать на износ, загрязнение или недостаток смазки. | Нужно учитывать нагрузку и скорость. | machines |
| `repair.plumbing.leak` | FAILURE_MODE | Утечки возникают из-за соединений, трещин, уплотнений, давления или коррозии. | Вода быстро повреждает конструкции. | plumbing |
| `repair.plumbing.trap` | COMPONENT | Сифон удерживает водяной затвор против запахов из канализации. | Испарение воды нарушает защиту. | home |
| `repair.plumbing.valve_shutoff` | SAFETY_RULE | Запорный клапан позволяет остановить воду перед ремонтом или аварией. | Нужно знать расположение заранее. | home |
| `repair.building.crack_monitoring` | METHOD | Наблюдение за трещиной во времени помогает отличить старый дефект от активного движения. | Структурные риски требует инженер. | building |
| `repair.building.caulking` | METHOD | Герметик закрывает щели от воды и воздуха. | Не заменяет структурный ремонт. | home |
| `repair.building.paint_prep` | METHOD | Подготовка поверхности важнее самой краски для долговечности покрытия. | Нужны очистка, шлифовка, грунт. | finishing |
| `repair.appliance.filter_cleaning` | METHOD | Фильтры бытовых приборов нужно чистить для потока воздуха/воды. | Забитый фильтр перегревает или снижает эффективность. | maintenance |
| `repair.appliance.belt_drive` | COMPONENT | Ременная передача передаёт вращение и может проскальзывать/изнашиваться. | Натяжение критично. | machines |
| `maintenance.preventive` | METHOD | Preventive maintenance выполняют по времени/пробегу до отказа. | Может быть лишним без анализа риска. | maintenance |
| `maintenance.condition_based` | METHOD | Condition-based maintenance зависит от состояния оборудования. | Требует датчиков или осмотров. | maintenance |
| `maintenance.corrective` | METHOD | Corrective maintenance чинит после обнаружения отказа. | Подходит не для критичных систем. | operations |
| `maintenance.cmms` | SYSTEM | CMMS хранит заявки, активы, работы, запчасти и историю обслуживания. | Данные должны быть дисциплинированными. | software |
| `maintenance.spare_parts` | SYSTEM | Запасные части балансируют риск простоя и стоимость хранения. | Нужна критичность и lead time. | logistics |
| `maintenance.mtbf_mttr` | METRIC | MTBF оценивает среднее время между отказами, MTTR — время восстановления. | Средние значения скрывают распределение. | reliability |
| `maintenance.rca_failure_code` | TOOL | Коды отказов помогают анализировать повторяющиеся проблемы. | Слишком общие коды бесполезны. | data |
| `maintenance.oee` | METRIC | OEE объединяет availability, performance и quality оборудования. | Не должен стимулировать скрывать простои. | manufacturing |
| `maintenance.vibration_analysis` | METHOD | Анализ вибрации выявляет дисбаланс, несоосность, подшипники и резонанс. | Требует базы и опыта. | predictive |
| `maintenance.thermal_imaging` | METHOD | Тепловизор выявляет перегрев, потери тепла и электрические проблемы. | Эмиссивность и отражения искажают картинку. | inspection |
| `maintenance.ultrasound_leak` | METHOD | Ультразвук помогает находить утечки сжатого воздуха и вакуума. | Нужны тихие условия и навык. | energy |
| `safety.tool.ppe_eye` | SAFETY_RULE | Защита глаз нужна при резке, шлифовке, химии, пыли и давлении. | Очки должны соответствовать риску. | PPE |
| `safety.tool.hearing` | SAFETY_RULE | Длительный шум повреждает слух, даже если не кажется болезненным. | Нужны замеры и защита. | PPE |
| `safety.tool.dust_control` | SAFETY_RULE | Пыль может быть токсичной, взрывоопасной или вредной для лёгких. | Нужны вытяжка, фильтрация, маски. | workshop |

---

## 📊 Batch 016 summary

```text
new units: 68
main layers:
  measurement and metrology
  hand/power tools
  troubleshooting and repair
  maintenance systems and workshop safety
```
