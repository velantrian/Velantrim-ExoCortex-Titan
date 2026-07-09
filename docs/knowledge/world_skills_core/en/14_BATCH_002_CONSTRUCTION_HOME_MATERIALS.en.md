# 🏠 Batch 002 — Construction, Home Systems & Natural Materials

**Язык:** русский  
**Статус:** 50K batch 002 / seed units / не L3 truth  
**Цель:** расширить practical-базу по жилью, строительным материалам, крышам, стенам, фундаментам, воде, отоплению, дереву, натуральным материалам и обслуживанию дома.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `construction.site.selection.access` | METHOD | Площадку для строительства оценивают по доступу к дорогам, воде, энергии и логистике. | Хорошая геология не компенсирует отсутствие инфраструктуры. | factory_site |
| `construction.site.drainage_priority` | PRINCIPLE | Вода должна отводиться от здания и фундамента. | Плохой дренаж ускоряет разрушение конструкций. | hydrology |
| `construction.site.soil_test` | METHOD | Геотехническое обследование определяет несущую способность, воду и риски грунта. | Нельзя надёжно проектировать фундамент "на глаз". | geology |
| `construction.foundation.strip` | COMPONENT | Ленточный фундамент передаёт нагрузку стен на грунт непрерывной полосой. | Подходит не для всех грунтов и нагрузок. | house |
| `construction.foundation.slab` | COMPONENT | Плитный фундамент распределяет нагрузку по большой площади. | Может быть дорогим, но полезен на слабых грунтах. | soil |
| `construction.foundation.pile` | COMPONENT | Сваи передают нагрузку на глубинные слои или через боковое трение. | Требуют расчёта и контроля установки. | geotechnical |
| `construction.foundation.frost_depth` | CONSTRAINT | Фундамент учитывает глубину промерзания, чтобы снизить морозное пучение. | Региональные нормы различаются. | frost_heave |
| `construction.wall.load_bearing` | COMPONENT | Несущая стена передаёт нагрузку от перекрытий/крыши к фундаменту. | Нельзя удалять без расчёта. | structural |
| `construction.wall.partition` | COMPONENT | Перегородка разделяет пространство и обычно не несёт основную нагрузку. | Может содержать проводку/трубы. | house |
| `construction.wall.masonry` | PROCESS | Кладка собирает стену из блоков/кирпича и раствора. | Важны перевязка, уровень, швы, влажность. | brick |
| `construction.brick.clay_selection` | MATERIAL_RULE | Глина для кирпича должна иметь подходящую пластичность и примеси. | Слишком много органики/солей ухудшает качество. | ceramics |
| `construction.brick.drying_failure` | FAILURE_MODE | Слишком быстрая сушка кирпича вызывает трещины и деформации. | Нужен контроль влажности и скорости сушки. | brick_process |
| `construction.brick.underfiring` | FAILURE_MODE | Недообжиг даёт слабый кирпич с высокой водопоглощаемостью. | Температурный профиль критичен. | kiln |
| `construction.brick.overfiring` | FAILURE_MODE | Пережог может деформировать кирпич или изменить свойства. | Зависит от состава глины. | ceramics |
| `construction.mortar.lime` | MATERIAL | Известковый раствор пластичен и паропроницаем. | Медленнее набирает прочность, чем цементный. | masonry |
| `construction.mortar.cement` | MATERIAL | Цементный раствор быстрее и прочнее, но может быть жёстким. | Несовместим с некоторыми историческими материалами. | masonry |
| `construction.concrete.aggregate` | MATERIAL | Заполнитель в бетоне формирует объём и влияет на прочность/усадку. | Гранулометрия и чистота важны. | concrete |
| `construction.concrete.water_cement_ratio` | CONSTRAINT | Водоцементное отношение сильно влияет на прочность и пористость бетона. | Избыток воды ухудшает прочность. | concrete |
| `construction.concrete.curing` | PROCESS | Уход за бетоном сохраняет влагу и температуру для гидратации. | Раннее высыхание снижает качество. | concrete |
| `construction.concrete.rebar_cover` | CONSTRAINT | Защитный слой бетона защищает арматуру от коррозии и огня. | Недостаточный слой повышает риск повреждения. | reinforced_concrete |
| `construction.roof.pitch` | CONSTRAINT | Уклон крыши влияет на отвод воды, снег и выбор покрытия. | Плоские и крутые крыши требуют разных решений. | roofing |
| `construction.roof.truss` | COMPONENT | Стропильная система передаёт нагрузки крыши на стены/опоры. | Требует расчёта снеговой и ветровой нагрузки. | wood |
| `construction.roof.waterproofing` | METHOD | Гидроизоляция крыши предотвращает проникновение воды. | Слабые места: стыки, примыкания, проходки. | home |
| `construction.roof.ventilation` | METHOD | Вентиляция кровельного пирога снижает влагу и перегрев. | Ошибки вызывают конденсат и гниение. | building_physics |
| `construction.roof.gutter` | COMPONENT | Водосток отводит дождевую воду от крыши и фундамента. | Засорение повышает риск протечек. | drainage |
| `construction.window.double_glazing` | COMPONENT | Двойное остекление снижает теплопотери и шум. | Качество зависит от герметичности и профиля. | insulation |
| `construction.window.thermal_bridge` | FAILURE_MODE | Мостик холода создаёт локальные теплопотери и риск конденсата. | Часто у стыков, балконов, перемычек. | building_physics |
| `construction.door.weatherstripping` | METHOD | Уплотнение дверей снижает сквозняки и потери тепла. | Требует сохранения вентиляционного баланса. | home |
| `construction.insulation.mineral_wool` | MATERIAL | Минеральная вата теплоизолирует и негорюча, но требует защиты от влаги/пыли. | Монтаж требует PPE. | insulation |
| `construction.insulation.cellulose` | MATERIAL | Целлюлозная изоляция производится из волокнистого сырья и заполняет полости. | Нужна защита от влаги и огня добавками. | natural_materials |
| `construction.insulation.hemp_flax` | MATERIAL | Конопляные/льняные утеплители используют растительное волокно. | Важны fire treatment и влажность. | agro_fiber |
| `construction.insulation.straw_bale` | MATERIAL | Соломенные блоки могут служить стеновым/изоляционным материалом. | Требуют защиты от влаги, огня, грызунов. | bio_based |
| `construction.material.bamboo_structural` | MATERIAL | Бамбук имеет высокую удельную прочность и используется в строительстве. | Требует обработки от насекомых и влаги. | agro.crop.bamboo.material |
| `construction.material.timber_seasoning` | PROCESS | Сушка древесины снижает влажность и деформации. | Слишком быстрая сушка вызывает трещины. | woodworking |
| `construction.material.timber_grain` | PROPERTY | Направление волокон влияет на прочность и коробление древесины. | Поперёк волокон прочность ниже. | wood |
| `construction.material.plywood` | MATERIAL | Фанера склеивает слои шпона с разным направлением волокон. | Клей и влагостойкость определяют применение. | wood_products |
| `construction.material.osb` | MATERIAL | OSB делают из ориентированной щепы и связующего. | Поведение во влажности зависит от класса. | wood_products |
| `construction.material.gypsum_board` | MATERIAL | Гипсокартон — листовой материал для внутренних стен/потолков. | Боится длительного увлажнения без специальных типов. | interior |
| `construction.material.lime_plaster` | MATERIAL | Известковая штукатурка паропроницаема и подходит для многих стен. | Медленно твердеет; требует навыка. | finish |
| `construction.material.clay_plaster` | MATERIAL | Глиняная штукатурка регулирует влажность и легко ремонтируется. | Не подходит без защиты от воды. | natural_finish |
| `construction.material.paint_binder` | TERM | Краска состоит из пигмента, связующего, растворителя/носителя и добавок. | Свойства зависят от системы. | pigments |
| `construction.finish.primer` | METHOD | Грунтовка улучшает адгезию и выравнивает впитываемость поверхности. | Нужна совместимость с основанием и краской. | painting |
| `construction.finish.sealant` | MATERIAL | Герметик закрывает стыки от воды/воздуха/пыли. | Разные типы имеют разную адгезию и эластичность. | maintenance |
| `construction.plumbing.supply_line` | COMPONENT | Водопровод подаёт воду к точкам потребления. | Давление, материал и защита от замерзания важны. | plumbing |
| `construction.plumbing.drain_slope` | CONSTRAINT | Канализационная труба требует достаточного уклона для самотёка. | Слишком малый/большой уклон может вызвать засоры. | sanitation |
| `construction.plumbing.vent_stack` | COMPONENT | Вентиляция канализации стабилизирует давление и защищает сифоны. | Ошибки вызывают запахи и срыв водяного затвора. | plumbing |
| `construction.plumbing.water_hammer` | FAILURE_MODE | Гидроудар возникает при резком изменении скорости потока. | Может повредить трубы/клапаны. | hydraulics |
| `construction.heating.radiator` | COMPONENT | Радиатор передаёт тепло воздуху конвекцией и излучением. | Требует балансировки системы. | HVAC |
| `construction.heating.underfloor` | SYSTEM | Тёплый пол распределяет тепло по большой площади при низкой температуре носителя. | Инерционность высокая. | energy |
| `construction.ventilation.air_exchange` | PRINCIPLE | Вентиляция удаляет влагу, запахи и загрязнения, подавая свежий воздух. | Недостаток повышает CO₂ и риск плесени. | indoor_air |
| `construction.moisture.condensation` | FAILURE_MODE | Конденсат возникает, когда поверхность холоднее точки росы воздуха. | Риск плесени и повреждений. | building_physics |
| `construction.mold.risk` | FAILURE_MODE | Плесень растёт при влаге, органическом материале и подходящей температуре. | Нужны устранение источника влаги и очистка. | health |
| `construction.electrical.panel` | COMPONENT | Электрощит распределяет питание и содержит защитные устройства. | Работы опасны; нужны нормы и квалификация. | electrical_safety |
| `construction.electrical.gfci_rcd` | SAFETY_RULE | УЗО/RCD отключает цепь при утечке тока, снижая риск поражения. | Не заменяет заземление и автоматы. | safety |
| `construction.electrical.breaker` | SAFETY_RULE | Автоматический выключатель защищает проводку от перегрузки/КЗ. | Номинал должен соответствовать кабелю. | fire_safety |
| `construction.electrical.cable_sizing` | CONSTRAINT | Сечение кабеля выбирают по току, длине, способу прокладки и нагреву. | Ошибка вызывает перегрев и пожарный риск. | electrical |
| `construction.fire.compartmentation` | SAFETY_RULE | Противопожарные отсеки замедляют распространение огня и дыма. | Требуют целостности стен/дверей/проходок. | safety |
| `construction.fire.smoke_detector` | SAFETY_RULE | Дымовой извещатель повышает шанс раннего обнаружения пожара. | Требует питания, размещения, обслуживания. | home_safety |
| `construction.home.maintenance_roof_inspection` | METHOD | Крышу проверяют на повреждения покрытия, примыканий, водостоков. | Лучше после бурь и сезонно. | maintenance |
| `construction.home.maintenance_caulk` | METHOD | Стыки вокруг окон/ванн/кухни периодически проверяют и обновляют. | Неправильный герметик быстро откажет. | maintenance |
| `construction.home.maintenance_filter` | METHOD | Фильтры HVAC меняют/чистят для качества воздуха и эффективности. | Период зависит от пыли и системы. | HVAC |
| `construction.home.maintenance_drain_cleaning` | METHOD | Профилактика засоров снижает риск протечек и обратного потока. | Агрессивная химия может повредить трубы и опасна. | plumbing |
| `construction.home.maintenance_gutter_cleaning` | METHOD | Очистка водостоков предотвращает перелив и увлажнение стен/фундамента. | Требуется безопасность при работе на высоте. | roof |
| `construction.safety.working_at_height` | SAFETY_RULE | Работа на высоте требует защиты от падения и устойчивой опоры. | Одна из главных причин тяжёлых травм. | safety |
| `construction.safety.silica_dust` | SAFETY_RULE | Пыль кварца при резке/шлифовке бетона/камня опасна для лёгких. | Нужны wet cutting, extraction, respirator. | occupational_health |
| `construction.safety.asbestos` | SAFETY_RULE | Асбестовые материалы опасны при нарушении и пылеобразовании. | Требует специализированного обращения и норм. | health |
| `construction.safety.lead_paint` | SAFETY_RULE | Старые свинцовые краски опасны при пыли/шлифовке. | Нужны testing и безопасное удаление. | health |
| `construction.safety.confined_space` | SAFETY_RULE | Замкнутые пространства опасны из-за газов, кислородного дефицита и спасательных рисков. | Требуют процедуры допуска. | industrial_safety |
| `construction.factory.site_layout` | METHOD | Планировка завода должна разделять сырьё, производство, склад, людей, отходы и пожарные пути. | Плохая планировка создаёт потери и риски. | factory |
| `construction.factory.utility_corridor` | COMPONENT | Инженерные коридоры несут воду, пар, воздух, электричество, данные. | Требуют доступа для maintenance. | industrial |
| `construction.factory.floor_load` | CONSTRAINT | Пол фабрики рассчитывают под оборудование, вибрацию и транспорт. | Недооценка нагрузки опасна. | industrial_building |
| `construction.factory.ventilation_dust` | SAFETY_RULE | Производственная вентиляция удаляет пыль, пары и тепло от источника. | Общая вентиляция не всегда достаточна. | occupational_safety |
| `construction.factory.fire_zoning` | SAFETY_RULE | Пожароопасные участки отделяют и оснащают защитой. | Зависит от материалов и процессов. | factory_safety |
| `construction.factory.commissioning` | PROCESS | Ввод в эксплуатацию проверяет системы перед нормальной работой. | Включает тесты, документацию, обучение персонала. | operations |

---

## 📊 Batch 002 summary

```text
new units: 74
main layers:
  site selection
  foundations
  walls / roof / windows
  concrete / brick / natural materials
  plumbing / heating / ventilation
  electrical safety
  factory construction
  maintenance and safety
```
