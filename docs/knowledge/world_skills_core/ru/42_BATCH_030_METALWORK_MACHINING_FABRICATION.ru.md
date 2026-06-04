# 🏭 Batch 030 — Metalwork, Machining & Fabrication

**Язык:** русский  
**Статус:** 50K batch 030 / seed units / не L3 truth  
**Цель:** добавить практический слой металлообработки: резание, станки, сварка, термообработка, контроль, сборка и safety.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `metalwork.material.mild_steel` | MATERIAL | Низкоуглеродистая сталь легко сваривается и формуется. | Прочность ниже легированных сталей. | materials |
| `metalwork.material.stainless_steel` | MATERIAL | Нержавеющая сталь сопротивляется коррозии благодаря хрому. | Неправильная обработка разрушает passive layer. | corrosion |
| `metalwork.material.cast_iron` | MATERIAL | Чугун хорошо льётся и гасит вибрации, но часто хрупок. | Сварка и ударные нагрузки сложны. | casting |
| `metalwork.material.aluminum` | MATERIAL | Алюминий лёгкий, коррозионно устойчивый и теплопроводный. | Сварка и резание требуют учёта тепла и оксидной плёнки. | fabrication |
| `metalwork.material.brass` | MATERIAL | Латунь — медно-цинковый сплав с хорошей обрабатываемостью. | Состав влияет на цвет, прочность и безопасность пыли. | alloys |
| `metalwork.material.titanium` | MATERIAL | Титан лёгкий, прочный и коррозионно устойчивый. | Дорогой и сложный в обработке, стружка пожароопасна. | aerospace |
| `metalwork.property.hardness` | PROPERTY | Твёрдость показывает сопротивление вдавливанию или царапанию. | Не равна toughness. | testing |
| `metalwork.property.toughness` | PROPERTY | Вязкость разрушения показывает способность поглощать энергию до разрушения. | Важна при ударе и холоде. | materials |
| `metalwork.property.machinability` | PROPERTY | Обрабатываемость описывает, насколько материал хорошо режется инструментом. | Зависит от сплава, состояния и инструмента. | machining |
| `metalwork.property.work_hardening` | MECHANISM | Некоторые металлы упрочняются при пластической деформации. | Может усложнять последующую обработку. | metallurgy |
| `metalwork.cutting.speed_feed_depth` | PARAMETERS | Скорость, подача и глубина резания определяют тепло, износ и качество. | Оптимум зависит от материала и инструмента. | machining |
| `metalwork.cutting.chip_formation` | MECHANISM | Стружка формируется сдвигом материала перед режущей кромкой. | Тип стружки влияет на безопасность и качество. | machining |
| `metalwork.cutting.coolant` | METHOD | СОЖ охлаждает, смазывает и уносит стружку. | Требует контроля концентрации и биологии. | maintenance |
| `metalwork.cutting.tool_wear` | FAILURE_MODE | Инструмент изнашивается от трения, тепла, диффузии и сколов. | Износ меняет размеры и поверхность. | quality |
| `metalwork.lathe.turning` | PROCESS | Токарная обработка вращает заготовку и режет неподвижным/движущимся инструментом. | Подходит для цилиндрических деталей. | machining |
| `metalwork.lathe.facing` | PROCESS | Торцевание выравнивает торец вращающейся детали. | Требует правильной установки и центра. | machining |
| `metalwork.lathe.threading` | PROCESS | Нарезание резьбы создаёт винтовой профиль на детали. | Шаг, профиль и глубина критичны. | fasteners |
| `metalwork.mill.face_milling` | PROCESS | Фрезерование плоскости снимает слой вращающейся фрезой. | Жёсткость станка влияет на вибрации. | machining |
| `metalwork.mill.slot_milling` | PROCESS | Пазовое фрезерование создаёт канавки и гнёзда. | Стружкоудаление и прогиб инструмента важны. | machining |
| `metalwork.drilling.twist_drill` | TOOL | Спиральное сверло режет отверстие и выводит стружку канавками. | Нужны скорость, подача и охлаждение. | tools |
| `metalwork.drilling.reaming` | PROCESS | Развёртывание улучшает размер и поверхность уже просверленного отверстия. | Не предназначено для большого снятия материала. | precision |
| `metalwork.boring` | PROCESS | Растачивание точно увеличивает или выравнивает отверстие. | Требует жёсткости и контроля биения. | machining |
| `metalwork.grinding.surface` | PROCESS | Шлифование абразивом даёт точность и чистую поверхность. | Риск перегрева и ожогов металла. | finishing |
| `metalwork.grinding.wheel_dressing` | METHOD | Правка круга восстанавливает геометрию и режущую способность. | Неправильный круг опасен. | safety |
| `metalwork.cnc.gcode` | LANGUAGE | G-code задаёт движения и операции станка с ЧПУ. | Ошибка координат может разбить станок. | CNC |
| `metalwork.cnc.work_offset` | SETUP | Work offset задаёт ноль детали относительно станка. | Неверный offset — частая причина аварии. | CNC |
| `metalwork.cnc.tool_length_offset` | SETUP | Tool length offset учитывает длину инструмента. | Нужно измерять при смене инструмента. | CNC |
| `metalwork.cnc.fixture` | TOOLING | Оснастка удерживает заготовку в правильном положении. | Слабое крепление опасно. | machining |
| `metalwork.metrology.surface_finish` | METRIC | Шероховатость поверхности влияет на трение, уплотнение и усталость. | Измеряется разными параметрами, например Ra. | quality |
| `metalwork.metrology.runout` | METRIC | Биение показывает отклонение вращающейся детали или инструмента. | Влияет на точность и вибрацию. | machining |
| `metalwork.metrology.gdandt` | STANDARD | GD&T задаёт геометрические допуски формы, ориентации и положения. | Требует знания datum и функций детали. | engineering |
| `metalwork.heat_treat.annealing` | PROCESS | Отжиг снижает твёрдость, внутренние напряжения и улучшает обработку. | Режим зависит от сплава. | metallurgy |
| `metalwork.heat_treat.quenching` | PROCESS | Металлообработка: Закалка быстро охлаждает металл для изменения структуры. | Может вызвать трещины и деформации. | metallurgy |
| `metalwork.heat_treat.tempering` | PROCESS | Отпуск после закалки снижает хрупкость и настраивает свойства. | Температура управляет компромиссом твёрдость/вязкость. | metallurgy |
| `metalwork.heat_treat.case_hardening` | PROCESS | Поверхностное упрочнение даёт твёрдый слой и вязкую сердцевину. | Используется для шестерён и валов. | machinery |
| `metalwork.welding.smaw` | PROCESS | Ручная дуговая сварка использует покрытый электрод. | Универсальна, но зависит от навыка. | welding |
| `metalwork.welding.mig_mag` | PROCESS | MIG/MAG подаёт проволоку и защитный газ. | Быстро для производства, чувствительно к ветру. | welding |
| `metalwork.welding.tig` | PROCESS | Металлообработка: TIG использует неплавящийся вольфрамовый электрод и защитный газ. | Даёт чистый шов, но медленнее. | welding |
| `metalwork.welding.spot` | PROCESS | Точечная сварка соединяет листы через сопротивление и давление. | Распространена в кузовах. | manufacturing |
| `metalwork.welding.heat_affected_zone` | ZONE | HAZ — зона металла, изменённая теплом сварки. | Может стать слабым местом. | metallurgy |
| `metalwork.welding.distortion` | FAILURE_MODE | Сварка вызывает деформации из-за локального нагрева и усадки. | Нужны прихватки, последовательность, fixture. | fabrication |
| `metalwork.welding.porosity` | DEFECT | Поры в шве возникают от газа, загрязнения или плохой защиты. | Снижают прочность и герметичность. | QA |
| `metalwork.sheetmetal.bending` | PROCESS | Гибка листа формирует угол через пластическую деформацию. | Нужно учитывать springback. | fabrication |
| `metalwork.sheetmetal.springback` | MECHANISM | После гибки лист частично возвращается назад. | Зависит от материала, толщины, радиуса. | sheetmetal |
| `metalwork.sheetmetal.punching` | PROCESS | Пробивка вырубает отверстия или формы штампом. | Имеет burr и износ инструмента. | manufacturing |
| `metalwork.sheetmetal.laser_cutting` | PROCESS | Лазерная резка использует сфокусированный луч для контуров. | Тепловая зона и газ влияют на край. | fabrication |
| `metalwork.sheetmetal.plasma_cutting` | PROCESS | Плазменная резка режет проводящие металлы струёй плазмы. | Быстрее на толстых листах, грубее лазера. | fabrication |
| `metalwork.casting.sand_casting` | PROCESS | Песчаное литьё формирует металл в песчаной форме. | Поверхность и точность ограничены. | casting |
| `metalwork.casting.die_casting` | PROCESS | Литьё под давлением быстро делает точные детали из сплавов. | Дорогое tooling, выгодно на серии. | manufacturing |
| `metalwork.forging` | PROCESS | Металлообработка: Ковка деформирует металл давлением для формы и структуры. | Улучшает grain flow при правильном процессе. | metallurgy |
| `metalwork.extrusion` | PROCESS | Экструзия продавливает металл через матрицу для постоянного профиля. | Часто для алюминия. | manufacturing |
| `metalwork.surface.galvanizing` | PROCESS | Цинкование защищает сталь жертвенным слоем цинка. | Повреждения цинка ещё могут защищать рядом. | corrosion |
| `metalwork.surface.anodizing` | PROCESS | Анодирование утолщает оксидный слой алюминия. | Улучшает коррозию и окраску. | surface |
| `metalwork.surface.powdercoat` | PROCESS | Порошковая окраска создаёт прочное покрытие после запекания. | Требует подготовки поверхности. | coating |
| `metalwork.corrosion.galvanic` | FAILURE_MODE | Гальваническая коррозия возникает между разными металлами в электролите. | Изоляция и выбор пары важны. | corrosion |
| `metalwork.corrosion.crevice` | FAILURE_MODE | Щелевая коррозия развивается в узких влажных зазорах. | Особенно у нержавейки в хлоридах. | corrosion |
| `metalwork.fastening.rivet` | FASTENER | Заклёпка создаёт постоянное механическое соединение листов. | Хороша при доступе с одной/двух сторон по типу. | assembly |
| `metalwork.fastening.threadlocker` | MATERIAL | Фиксатор резьбы снижает самоотвинчивание. | Тип подбирают по разборности и температуре. | maintenance |
| `metalwork.assembly.press_fit` | METHOD | Прессовая посадка держит детали за счёт натяга. | Требует допусков и контроля напряжений. | assembly |
| `metalwork.assembly.shrink_fit` | METHOD | Тепловая посадка использует расширение/сжатие деталей. | Нужна температура и safety. | assembly |
| `metalwork.qa.nondestructive_testing` | QUALITY_CHECK | NDT проверяет дефекты без разрушения детали. | Метод выбирают по дефекту и материалу. | QA |
| `metalwork.qa.dye_penetrant` | QUALITY_CHECK | Капиллярный контроль выявляет поверхностные трещины. | Требует чистой поверхности. | NDT |
| `metalwork.qa.ultrasonic` | QUALITY_CHECK | УЗК ищет внутренние дефекты звуковыми волнами. | Нужен оператор и калибровка. | NDT |
| `metalwork.safety.hot_work_permit` | SAFETY_RULE | Горячие работы требуют разрешения, очистки зоны и fire watch. | Искры могут зажечь скрытые материалы. | safety |
| `metalwork.safety.machine_guard` | SAFETY_RULE | Ограждения станков защищают от вращения, стружки и зажатия. | Не снимать ради удобства. | safety |
| `metalwork.safety.chip_handling` | SAFETY_RULE | Металлическую стружку убирают инструментом, не руками. | Стружка острая и горячая. | safety |

---

## 📊 Batch 030 summary

```text
new units: 66
main layers:
  metals and machining
  CNC, metrology and tolerances
  welding, casting, forming and finishing
  fabrication safety and QA
```
