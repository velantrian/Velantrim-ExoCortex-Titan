# 🚢 Batch 037 — Rail, Marine, Aerospace & Heavy Equipment

**Язык:** русский  
**Статус:** 50K batch 037 / seed units / не L3 truth  
**Цель:** добавить техническую базу крупных транспортных и рабочих систем: железная дорога, суда, авиация, спецтехника и их safety/maintenance.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `railtech.bogie` | COMPONENT | Тележка несёт колёсные пары и связывает вагон с рельсами. | Влияет на плавность и устойчивость. | rail |
| `railtech.coupler` | COMPONENT | Сцепка соединяет вагоны и передаёт тяговые/сжимающие силы. | Типы сцепок несовместимы без адаптеров. | rail |
| `railtech.air_brake` | SAFETY_SYSTEM | Пневматический тормоз использует давление воздуха для управления торможением поезда. | Fail-safe логика важна. | safety |
| `railtech.dynamic_braking` | METHOD | Динамическое торможение использует тяговые моторы как генераторы/нагрузку. | Не заменяет полностью friction brakes. | rail |
| `railtech.traction_motor` | COMPONENT | Тяговый мотор преобразует электричество во вращение колёс. | Требует охлаждения и управления. | power |
| `railtech.pantograph_wear` | MAINTENANCE | Пантограф снимает ток с контактной сети и изнашивается. | Неправильный контакт повреждает сеть. | rail |
| `railtech.wheel_flat` | FAILURE_MODE | Ползун колеса возникает от блокировки/скольжения и создаёт удары. | Повреждает путь и подшипники. | maintenance |
| `railtech.hotbox_detector` | SAFETY_SYSTEM | Hotbox detector выявляет перегрев букс/подшипников поезда. | Раннее обнаружение предотвращает аварии. | rail_safety |
| `marine.hull_displacement` | MECHANISM | Водоизмещение связано с массой вытесненной воды. | Основа плавучести судна. | physics |
| `marine.stability_metacenter` | MODEL | Остойчивость судна связана с центром тяжести и метацентром. | Неправильная загрузка опасна. | naval |
| `marine.propeller_cavitation` | FAILURE_MODE | Кавитация винта снижает тягу и повреждает поверхности. | Зависит от скорости, давления, формы. | marine |
| `marine.rudder` | COMPONENT | Руль меняет направление потока и поворачивает судно. | Эффективность зависит от скорости. | navigation |
| `marine.bilge_system` | SAFETY_SYSTEM | Осушительная система удаляет воду из нижних частей судна. | Отказ может привести к затоплению. | safety |
| `marine.fire_suppression_engine_room` | SAFETY_SYSTEM | Машинное отделение требует обнаружения и тушения пожара. | Топливо и масло повышают риск. | safety |
| `marine.navigation.colregs` | RULE_SET | COLREGs задают правила предотвращения столкновений судов. | Требуют обучения и situational awareness. | navigation |
| `marine.ais` | SYSTEM | AIS передаёт данные судна для наблюдения и безопасности. | Не все объекты имеют AIS. | maritime |
| `aero.airframe.fuselage` | COMPONENT | Фюзеляж несёт экипаж, пассажиров, груз и часть нагрузок. | Конструкция зависит от давления и аэродинамики. | aerospace |
| `aero.wing.airfoil` | COMPONENT | Профиль крыла формирует подъёмную силу и сопротивление. | Работает в диапазоне углов атаки. | aerodynamics |
| `aero.control_surface.aileron` | COMPONENT | Элероны управляют креном самолёта. | Связаны с roll control. | flight |
| `aero.control_surface.elevator` | COMPONENT | Руль высоты управляет тангажом. | Trim снижает усилие управления. | flight |
| `aero.control_surface.rudder` | COMPONENT | Руль направления управляет рысканием. | Важен при боковом ветре и отказах. | flight |
| `aero.engine.turbofan` | ENGINE | Турбовентилятор создаёт тягу вентилятором и реактивной струёй. | Bypass ratio влияет на эффективность. | aviation |
| `aero.apu` | COMPONENT | APU даёт электроэнергию и воздух на земле/резервно. | Требует топлива и обслуживания. | aircraft |
| `aero.avionics.flight_management` | SYSTEM | FMS помогает маршрутизации, навигации и расчётам полёта. | Пилот должен проверять ввод. | avionics |
| `aero.maintenance.airworthiness_directive` | REGULATION | AD требует обязательных действий для поддержания лётной годности. | Выпуск зависит от регулятора. | aviation_safety |
| `aero.safety.redundant_systems` | DESIGN_PRINCIPLE | Авиация использует резервирование критичных систем. | Redundancy требует независимости. | safety |
| `heavy.hydraulic_cylinder` | COMPONENT | Гидроцилиндр превращает давление жидкости в линейное усилие. | Утечки и загрязнение опасны. | machinery |
| `heavy.hydraulic_pump` | COMPONENT | Гидронасос создаёт поток жидкости для работы системы. | Cavitation и загрязнение сокращают ресурс. | hydraulics |
| `heavy.excavator.boom_stick_bucket` | SYSTEM | Экскаватор работает стрелой, рукоятью и ковшом через гидравлику. | Устойчивость зависит от вылета и грунта. | construction |
| `heavy.loader.bucket` | COMPONENT | Погрузчик перемещает сыпучие материалы ковшом. | Перегруз и поднятый ковш повышают риск опрокидывания. | safety |
| `heavy.crane.load_chart` | SAFETY_DOCUMENT | Грузовая диаграмма крана задаёт допустимый груз по вылету и конфигурации. | Нарушение может привести к опрокидыванию. | lifting |
| `heavy.crane.outrigger` | SAFETY_COMPONENT | Аутригеры расширяют опору крана. | Требуют прочной площадки и leveling. | safety |
| `heavy.forklift.load_center` | CONSTRAINT | Центр груза влияет на допустимую массу подъёма погрузчика. | Длинный груз снижает capacity. | warehouse |
| `heavy.dozer.track` | COMPONENT | Гусеницы распределяют массу и дают тягу на слабом грунте. | Износ ходовой дорогой. | equipment |
| `heavy.maintenance.grease_points` | METHOD | Точки смазки защищают шарниры и втулки спецтехники. | Пропуск ускоряет износ. | maintenance |
| `heavy.maintenance.hydraulic_filter` | METHOD | Фильтр гидросистемы удаляет частицы из масла. | Загрязнение разрушает клапаны и насосы. | maintenance |
| `heavy.safety.blind_spot` | RISK | У тяжёлой техники большие слепые зоны. | Нужны spotters, cameras, exclusion zones. | safety |
| `heavy.safety.lockout_attachment` | SAFETY_RULE | Навесное оборудование нужно блокировать перед обслуживанием. | Гидравлика может опуститься неожиданно. | safety |
| `heavy.fleet.utilization` | METRIC | Utilization показывает, насколько техника реально используется. | Низкая загрузка повышает стоимость часа. | operations |
| `heavy.fleet.preventive_maintenance` | METHOD | Плановое обслуживание снижает аварийные простои. | Интервалы зависят от часов, нагрузки, пыли. | maintenance |
| `heavy.site.ground_bearing_pressure` | CONSTRAINT | Давление на грунт определяет риск просадки техники. | Важен тип грунта и влажность. | geotechnics |
| `heavy.site.lifting_plan` | SAFETY_PLAN | План подъёма описывает груз, кран, стропы, путь, людей и риски. | Нужен для критичных подъёмов. | safety |
| `heavy.rigging.sling_angle` | CONSTRAINT | Угол строп меняет нагрузку на ветви стропа. | Малый угол резко повышает усилия. | lifting |
| `heavy.rigging.shackle` | COMPONENT | Скоба соединяет стропы, крюки и точки крепления. | Нужна маркировка WLL и правильный pin. | rigging |

---

## 📊 Batch 037 summary

```text
new units: 44
main layers:
  rail systems
  marine systems
  aerospace systems
  heavy equipment and lifting safety
```
