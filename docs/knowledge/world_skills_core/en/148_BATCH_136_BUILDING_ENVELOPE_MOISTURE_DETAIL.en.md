# BATCH_136 — Building Envelope & Moisture Detail
# world_skills_core · source: world_skills_core:batch_136:building_envelope_moisture
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| envelope.airbarrier.continuity | Air barrier continuity | invariant | Воздушный барьер должен быть непрерывным вокруг отапливаемого объема, включая стыки, проходки и переходы материалов. | утечки ломают систему |
| envelope.airbarrier.pressure_boundary | Pressure boundary | invariant | Pressure boundary здания определяет, где воздух должен останавливаться при ветре, stack effect и работе вентиляции. | найти реальную оболочку |
| envelope.airbarrier.blower_door | Blower door test | variant | Blower door test создает перепад давления и измеряет воздухообмен, чтобы оценить герметичность здания. | проверка качества монтажа |
| envelope.airbarrier.service_penetration | Service penetration sealing | invariant | Проходки труб, кабелей и воздуховодов должны быть герметизированы совместимым материалом, сохраняющим функцию узла. | частый источник утечек |
| envelope.vapor.vapor_control_layer | Vapor control layer | invariant | Пароограничивающий слой управляет диффузией влаги через конструкцию, но не заменяет воздушную герметичность. | не путать воздух и пар |
| envelope.vapor.perm_rating | Permeance rating | invariant | Паропроницаемость материала показывает, насколько легко водяной пар проходит через него при заданных условиях. | выбор слоя |
| envelope.vapor.smart_membrane | Smart vapor retarder | variant | Smart vapor retarder меняет паропроницаемость с влажностью и может помогать конструкции высыхать в безопасном направлении. | сложные климатические узлы |
| envelope.vapor.double_vapor_barrier | Double vapor barrier risk | invariant | Два непроницаемых слоя могут запереть влагу внутри конструкции и замедлить высыхание. | риск плесени и гнили |
| envelope.moisture.bulk_water | Bulk water control | invariant | Дождевая и талая вода должны отводиться наружными слоями, уклонами, flashings и дренажными путями до попадания внутрь. | главный источник влаги |
| envelope.moisture.capillary_break | Capillary break | invariant | Capillary break прерывает подсос воды через пористые материалы с помощью зазора, мембраны или непористого слоя. | фундаменты и стены |
| envelope.moisture.drainage_plane | Drainage plane | invariant | Drainage plane создает путь для воды, которая прошла за облицовку, чтобы она могла выйти наружу. | rainscreen logic |
| envelope.moisture.rainscreen_gap | Rainscreen gap | variant | Вентилируемый зазор за облицовкой ускоряет дренаж и высыхание, если входы и выходы воздуха не заблокированы. | фасад работает лучше |
| envelope.moisture.flashing | Flashing detail | invariant | Flashing направляет воду поверх следующего наружного слоя, а не за него, особенно вокруг окон, дверей и примыканий. | порядок нахлестов |
| envelope.moisture.weep_hole | Weep holes | variant | Weep holes дают воде выйти из полости стены, но требуют защиты от засорения и насекомых. | кирпичные фасады |
| envelope.roof.vented_attic | Vented attic | variant | Вентилируемый чердак снижает накопление влаги и тепла, если воздушный барьер потолка и вентиляционные пути выполнены правильно. | не лечит утечки воздуха |
| envelope.roof.unvented_roof | Unvented roof assembly | variant | Невентилируемая кровельная сборка требует контроля точки росы и достаточной доли наружной или внутренней изоляции. | риск конденсата |
| envelope.roof.ice_dam | Ice dam | invariant | Ледяная дамба возникает, когда снег тает на теплой кровле и замерзает у холодного карниза. | нужна герметичность и изоляция |
| envelope.roof.parapet_risk | Parapet moisture risk | variant | Парапет имеет много примыканий и горизонтальных поверхностей, поэтому требует надежной гидроизоляции и отвода воды. | частая зона протечек |
| envelope.wall.thermal_bridge | Thermal bridge | invariant | Тепловой мост проводит тепло через или вокруг изоляции, снижая фактическое сопротивление всей стены. | считать не только R утеплителя |
| envelope.wall.continuous_insulation | Continuous insulation | invariant | Непрерывная изоляция снаружи каркаса снижает тепловые мосты и повышает температуру чувствительных слоев. | меньше риск конденсата |
| envelope.wall.cavity_insulation_gap | Insulation gap | invariant | Зазоры, сжатие или неполное заполнение утеплителя создают локальные теплопотери и холодные поверхности. | качество установки |
| envelope.wall.sheathing_temperature | Sheathing temperature | variant | Температура обшивки стены зависит от климата, толщины наружной изоляции, внутренней влажности и герметичности. | оценка точки росы |
| envelope.window.u_factor | Window U-factor | invariant | U-factor окна показывает теплопередачу всей оконной системы, включая стеклопакет, раму и дистанционную рамку. | сравнение окон |
| envelope.window.solar_heat_gain | Solar heat gain coefficient | invariant | SHGC показывает долю солнечного тепла, проходящего через окно внутрь здания. | баланс зимы и лета |
| envelope.window.thermal_break_frame | Thermal break frame | variant | Thermal break в раме снижает теплопроводность металлического профиля и риск внутреннего конденсата. | комфорт у окна |
| envelope.window.installation_tape | Window installation tape | variant | Оконные ленты должны соединять окно с drainage plane, air barrier и water barrier в правильном порядке. | монтаж важнее паспорта окна |
| envelope.foundation.damp_proofing | Damp proofing | invariant | Damp proofing ограничивает капиллярную влагу грунта, но не рассчитан на гидростатическое давление воды. | не путать с waterproofing |
| envelope.foundation.waterproofing | Foundation waterproofing | invariant | Waterproofing фундамента рассчитан на удержание жидкой воды при давлении и требует защиты от повреждения засыпкой. | влажные грунты |
| envelope.foundation.drain_tile | Foundation drain | variant | Дренаж фундамента снижает давление воды у стены, если имеет уклон, фильтрацию и безопасный вывод. | защита подвала |
| envelope.foundation.slab_vapor_barrier | Slab vapor barrier | invariant | Паробарьер под плитой снижает поступление влаги из грунта в бетон и напольные покрытия. | полы и качество воздуха |
| envelope.indoor.relative_humidity | Indoor relative humidity | invariant | Внутренняя относительная влажность влияет на конденсацию, комфорт, плесень и усушку материалов. | управлять влажностью |
| envelope.indoor.dew_point | Dew point | invariant | Точка росы показывает температуру, при которой воздух с данной влажностью начинает конденсировать воду. | понять конденсат |
| envelope.indoor.stack_effect | Stack effect | invariant | Stack effect перемещает воздух через здание из-за разности плотности теплого и холодного воздуха. | зимой усиливает утечки |
| envelope.indoor.negative_pressure | Negative pressure risk | variant | Отрицательное давление в здании может втягивать влажный, загрязненный или дымовой воздух через оболочку. | баланс вентиляции |
| envelope.ventilation.drying_potential | Drying potential | invariant | Drying potential конструкции зависит от способности влаги выходить наружу или внутрь без накопления в чувствительных слоях. | проектировать высыхание |
| envelope.ventilation.bath_exhaust | Bath exhaust | variant | Вытяжка ванной должна удалять влажный воздух наружу, а не в чердак, стену или межпотолочное пространство. | избежать плесени |
| envelope.durability.material_sequence | Material layer sequence | invariant | Последовательность слоев в оболочке должна учитывать воду, воздух, пар, тепло, огонь и механическую защиту одновременно. | узел работает как система |
| envelope.durability.compatible_sealant | Compatible sealant | variant | Герметик должен быть совместим с подложкой, движением шва, UV, температурой и сроком службы. | не любой герметик подходит |
| envelope.durability.movement_joint | Movement joint | invariant | Деформационный шов позволяет материалам двигаться из-за температуры, влажности, усадки или нагрузки без трещин. | фасады и кладка |
| envelope.durability.cladding_clearance | Cladding ground clearance | variant | Облицовке нужен зазор от земли, кровли или горизонтальных поверхностей, чтобы снизить увлажнение и гниение. | низ стены уязвим |
| envelope.diagnostics.moisture_meter_limit | Moisture meter limit | variant | Влагомер помогает найти влажные зоны, но показания зависят от материала, соли, температуры и режима прибора. | подтверждать несколькими методами |
| envelope.diagnostics.infrared_limit | Infrared envelope limit | variant | Инфракрасная съемка показывает температурные аномалии, но требует перепада температур и проверки причин другими методами. | не всё холодное является влагой |
| envelope.diagnostics.smoke_pencil | Smoke pencil | variant | Smoke pencil визуализирует движение воздуха через щели при перепаде давления. | поиск утечек |
| envelope.commissioning.enclosure_commissioning | Enclosure commissioning | invariant | Commissioning оболочки проверяет проектные узлы, макеты, монтаж, испытания и исправление дефектов до скрытия слоев. | качество до отделки |
