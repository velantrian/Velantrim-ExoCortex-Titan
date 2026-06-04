# 🚗 Batch 036 — Automotive Vehicles & Maintenance

**Язык:** русский  
**Статус:** 50K batch 036 / seed units / не L3 truth  
**Цель:** добавить практическую базу по автомобилям: двигатель, трансмиссия, тормоза, подвеска, электрика, диагностика, EV, безопасность и обслуживание.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `auto.engine.four_stroke_cycle` | MECHANISM | Четырёхтактный двигатель проходит впуск, сжатие, рабочий ход и выпуск. | Детали зависят от топлива и конструкции. | mechanics |
| `auto.engine.intake_airflow` | MECHANISM | Двигателю нужен контролируемый поток воздуха для сгорания. | Фильтр, дроссель, датчики и турбо влияют. | engine |
| `auto.engine.fuel_injection` | SYSTEM | Впрыск топлива дозирует топливо по нагрузке, температуре и режиму. | Ошибки дают расход, дым, пропуски. | engine |
| `auto.engine.spark_ignition` | MECHANISM | Бензиновый двигатель обычно воспламеняет смесь искрой. | Свечи, катушки и timing критичны. | engine |
| `auto.engine.diesel_compression` | MECHANISM | Дизель воспламеняет топливо от нагретого сжатого воздуха. | Требует высокого давления и точного впрыска. | engine |
| `auto.engine.turbocharger` | COMPONENT | Турбокомпрессор использует энергию выхлопа для сжатия воздуха. | Нужны смазка, охлаждение, контроль boost. | engine |
| `auto.engine.cooling_system` | SYSTEM | Система охлаждения отводит тепло через жидкость, радиатор и вентилятор. | Перегрев быстро повреждает двигатель. | maintenance |
| `auto.engine.lubrication_system` | SYSTEM | Масло снижает трение, охлаждает и выносит загрязнения. | Вязкость и уровень критичны. | maintenance |
| `auto.exhaust.catalytic_converter` | COMPONENT | Катализатор снижает вредные выбросы в выхлопе. | Требует правильной смеси и температуры. | emissions |
| `auto.transmission.manual_clutch` | COMPONENT | Сцепление временно разъединяет двигатель и коробку передач. | Износ зависит от техники и нагрузки. | drivetrain |
| `auto.transmission.torque_converter` | COMPONENT | Гидротрансформатор передаёт момент через жидкость в automatic transmission. | Может иметь lock-up clutch. | drivetrain |
| `auto.drivetrain.cv_joint` | COMPONENT | ШРУС передаёт крутящий момент при изменении угла колеса. | Пыльник защищает смазку от грязи. | suspension |
| `auto.brake.hydraulic` | SYSTEM | Гидравлические тормоза передают усилие жидкостью от педали к колёсам. | Воздух и утечки опасны. | safety |
| `auto.brake.abs` | SAFETY_SYSTEM | ABS снижает блокировку колёс при торможении. | Не сокращает тормозной путь во всех условиях. | safety |
| `auto.suspension.spring_damper` | SYSTEM | Пружины несут массу, амортизаторы гасят колебания. | Износ влияет на сцепление и комфорт. | vehicle |
| `auto.steering.rack_pinion` | COMPONENT | Рулевая рейка преобразует вращение руля в боковое движение тяг. | Люфт и износ опасны. | vehicle |
| `auto.tire.pressure` | PARAMETER | Давление шин влияет на сцепление, износ, расход и безопасность. | Проверяется на холодных шинах. | safety |
| `auto.tire.tread_depth` | SAFETY_METRIC | Глубина протектора влияет на отвод воды и сцепление. | Минимум зависит от закона и условий. | vehicle |
| `auto.wheel.alignment` | METHOD | Развал-схождение задаёт углы колёс для устойчивости и износа шин. | Нарушается после ударов и ремонта подвески. | maintenance |
| `auto.electrical.lead_acid_battery` | COMPONENT | Свинцово-кислотная батарея запускает двигатель и питает системы. | Холод и возраст снижают ёмкость. | electrical |
| `auto.electrical.alternator` | COMPONENT | Генератор заряжает батарею и питает сеть при работающем двигателе. | Ремень и регулятор важны. | electrical |
| `auto.electrical.starter_motor` | COMPONENT | Стартер кратко вращает двигатель для запуска. | Высокий ток требует исправных контактов. | electrical |
| `auto.diagnostics.obd2` | INTERFACE | OBD-II даёт доступ к кодам и параметрам автомобиля. | Код не всегда указывает точную деталь. | diagnostics |
| `auto.diagnostics.trouble_code` | RECORD | DTC фиксирует обнаруженную неисправность системы. | Нужна диагностика причины, не только замена. | diagnostics |
| `auto.maintenance.oil_interval` | METHOD | Интервал масла зависит от двигателя, масла, условий и регламента. | Тяжёлые условия сокращают интервал. | maintenance |
| `auto.maintenance.air_filter` | METHOD | Воздушный фильтр защищает двигатель от пыли. | Забитый фильтр снижает поток. | maintenance |
| `auto.maintenance.brake_fluid` | METHOD | Тормозная жидкость гигроскопична и требует периодической замены. | Влага снижает точку кипения. | safety |
| `auto.maintenance.timing_belt` | COMPONENT_RISK | Ремень ГРМ синхронизирует коленвал и распредвал. | Обрыв может разрушить двигатель. | maintenance |
| `auto.safety.airbag` | SAFETY_SYSTEM | Airbag снижает травмы при аварии при правильных условиях. | Работает вместе с ремнём. | safety |
| `auto.safety.seatbelt_pretensioner` | SAFETY_SYSTEM | Преднатяжитель ремня убирает слабину в момент удара. | Одноразовый после срабатывания. | safety |
| `auto.safety.crumple_zone` | DESIGN_PRINCIPLE | Зоны деформации поглощают энергию столкновения. | Кузов после аварии требует проверки. | safety |
| `auto.safety.child_seat_anchor` | SAFETY_SYSTEM | ISOFIX/LATCH крепления фиксируют детское кресло к кузову. | Кресло должно подходить ребёнку и машине. | child_safety |
| `auto.lighting.headlight_aim` | SAFETY_METHOD | Регулировка фар влияет на видимость и ослепление других. | Нагрузка автомобиля меняет угол. | safety |
| `auto.visibility.wiper_system` | SYSTEM | Дворники и омыватель обеспечивают обзор в дождь и грязь. | Старые щётки оставляют полосы. | safety |
| `auto.hvac.cabin_filter` | COMPONENT | Салонный фильтр очищает воздух HVAC от пыли и части частиц. | Забитый фильтр снижает поток. | comfort |
| `auto.body.corrosion` | FAILURE_MODE | Коррозия кузова возникает от влаги, соли и повреждения покрытия. | Скрытые полости особенно уязвимы. | materials |
| `auto.paint.clearcoat` | COMPONENT | Лаковый слой защищает цвет и даёт блеск. | UV, химия и царапины разрушают. | coating |
| `auto.ev.battery_pack` | COMPONENT | EV battery pack хранит энергию в множестве ячеек и модулей. | Требует охлаждения и защиты. | EV |
| `auto.ev.bms` | SAFETY_SYSTEM | Battery management system контролирует напряжение, температуру и баланс ячеек. | Критично для безопасности и ресурса. | electronics |
| `auto.ev.regenerative_braking` | MECHANISM | Рекуперация возвращает часть кинетической энергии в батарею. | Ограничена зарядом, сцеплением и температурой. | EV |
| `auto.ev.ac_charging` | PROCESS | AC charging использует onboard charger автомобиля. | Мощность ограничена машиной и сетью. | charging |
| `auto.ev.dc_fast_charging` | PROCESS | DC fast charging подаёт постоянный ток напрямую в батарейную систему. | Быстрее, но сильнее нагревает и требует инфраструктуры. | charging |
| `auto.hybrid.power_split` | SYSTEM | Гибрид распределяет тягу между ДВС, электромотором и батареей. | Архитектуры гибридов различаются. | drivetrain |
| `auto.fleet.telematics` | SYSTEM | Телематика собирает данные о маршрутах, стиле вождения, топливе и состоянии. | Риски privacy и data quality. | logistics |
| `auto.inspection.roadworthiness` | QUALITY_CHECK | Техосмотр проверяет безопасность и экологичность автомобиля. | Не гарантирует отсутствие будущих отказов. | regulation |

---

## 📊 Batch 036 summary

```text
new units: 45
main layers:
  engine, drivetrain and vehicle systems
  maintenance and diagnostics
  EV, safety and roadworthiness
```
