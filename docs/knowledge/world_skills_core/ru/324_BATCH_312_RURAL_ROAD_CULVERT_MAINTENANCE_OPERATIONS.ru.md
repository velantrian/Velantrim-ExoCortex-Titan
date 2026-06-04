# BATCH 312: Rural Road Culvert Maintenance Operations

**KnowledgeUnits:** 44  
**Namespace:** `culvertops.*`  
**Scope:** inventory, inspections, sediment, inlet/outlet condition, repairs, flooding complaints and replacement priority.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| culvertops.inventory.asset_id | culvert asset ID | RECORD | Каждый culvert получает ID, road name, milepost, coordinates, owner и drainage crossing. | Без asset ID жалобы, inspections и repairs не связываются. |
| culvertops.inventory.pipe_type | pipe type record | RECORD | Указывают material, shape, diameter, length, slope, headwalls и installation year. | Материал и геометрия определяют failure modes. |
| culvertops.inventory.upstream_area | upstream drainage area | MEASUREMENT | Drainage area оценивают по maps, LiDAR, field flow paths и land use. | Показывает, насколько culvert подходит к runoff нагрузке. |
| culvertops.inventory.criticality | criticality rating | MODEL | Criticality учитывает road class, detour length, homes, emergency access и flood history. | Помогает сначала обслуживать наиболее важные crossings. |
| culvertops.inventory.photo_baseline | photo baseline | RECORD | Initial photos фиксируют inlet, outlet, road surface, ditch и downstream channel. | Дает сравнение при будущей деградации. |
| culvertops.inspection.cycle | inspection cycle | METHOD | Rural culverts проверяют routine cycle и дополнительно после крупных storms. | Малые дефекты дешевле исправлять до washout. |
| culvertops.inspection.inlet_blockage | inlet blockage | INSPECTION | На inlet ищут debris, trash, sediment, vegetation, ice и collapsed ditch banks. | Blockage повышает риск overtopping и road erosion. |
| culvertops.inspection.outlet_scour | outlet scour | INSPECTION | На outlet проверяют scour hole, undermining, displaced riprap и bank erosion. | Scour может разрушить pipe bedding и road embankment. |
| culvertops.inspection.pipe_barrel | pipe barrel condition | INSPECTION | Внутри pipe смотрят corrosion, deformation, joint separation, cracks и sediment. | Barrel defects показывают structural и hydraulic capacity loss. |
| culvertops.inspection.road_surface | road surface symptom | OBSERVATION | Sinkholes, depressions, cracks и wet spots над pipe указывают на voids или leakage. | Дорожное покрытие часто первым показывает hidden failure. |
| culvertops.inspection.safety_access | safe inspection access | SAFETY_RULE | Inspection не входит в confined space без permit, gas check и rescue plan. | Простая culvert check не должна превращаться в high-risk entry. |
| culvertops.sediment.sediment_depth | sediment depth | MEASUREMENT | Sediment depth сравнивают с pipe diameter и hydraulic opening. | Показывает потерю capacity в процентах. |
| culvertops.sediment.upstream_source | sediment source tracing | METHOD | Источник sediment ищут в ditch erosion, unpaved roads, fields, banks или construction. | Чистка без source control быстро повторяется. |
| culvertops.sediment.cleanout_trigger | cleanout trigger | DECISION_RULE | Cleanout назначают при capacity loss, flooding complaints или blocked fish passage. | Приоритизирует work crews по impact. |
| culvertops.sediment.disposal | sediment disposal | METHOD | Removed sediment размещают так, чтобы он не вернулся в ditch or stream. | Иначе maintenance создает повторное загрязнение. |
| culvertops.inlet.headwall | headwall condition | INSPECTION | Headwall проверяют на cracks, rotation, undermining, loose stones и settlement. | Headwall стабилизирует pipe entrance и embankment. |
| culvertops.inlet.apron | inlet apron | INSPECTION | Apron и riprap защищают от erosion и направляют flow в pipe. | Поврежденный apron увеличивает blockage и scour. |
| culvertops.inlet.alignment | inlet alignment | QUALITY_CHECK | Flow должен входить без sharp bend, perched lip или ditch offset. | Плохая alignment снижает capacity даже у большого pipe. |
| culvertops.inlet.beaver_screen | beaver screen management | METHOD | Screens требуют inspection frequency и debris removal plan. | Защита от beaver может сама стать blockage. |
| culvertops.outlet.tailwater | tailwater condition | OBSERVATION | Высокий tailwater снижает discharge и может затопить upstream. | Нужен при анализе flooding complaints. |
| culvertops.outlet.perching | perched outlet | FAILURE_MODE | Outlet висит над downstream bed и создает barrier or erosion drop. | Важно для aquatic passage и channel stability. |
| culvertops.outlet.energy_dissipation | energy dissipation | METHOD | Riprap, pools или grade control уменьшают скорость на выходе. | Предотвращает downstream incision. |
| culvertops.outlet.vegetation | outlet vegetation | METHOD | Vegetation управляют так, чтобы не блокировать flow и стабилизировать banks. | Полная зачистка может усилить erosion. |
| culvertops.repair.patch | localized patch | METHOD | Малые holes или joint leaks могут требовать patch, band или grout по material. | Продлевает срок службы без полной замены. |
| culvertops.repair.reline | culvert lining | METHOD | Lining устанавливают при достаточном diameter и допустимой capacity loss. | Быстрый repair, но hydraulic opening уменьшается. |
| culvertops.repair.end_section | end section repair | METHOD | Damaged flared end sections и aprons заменяют для smooth entrance/exit. | Улучшает hydraulics и снижает edge failures. |
| culvertops.repair.ditch_regrade | ditch regrade | METHOD | Ditch grade корректируют для steady approach flow and drainage. | Culvert работает лучше, когда upstream ditch не заилен. |
| culvertops.repair.temporary_bypass | temporary bypass | METHOD | During repair water bypass or pump-around protects work zone and stream. | Позволяет чинить без uncontrolled muddy flow. |
| culvertops.complaint.intake | flooding complaint intake | RECORD | Жалоба фиксирует location, time, rain, water depth, property impact и photos. | Помогает отличить hydraulic problem от isolated storm severity. |
| culvertops.complaint.field_response | complaint field response | METHOD | Crew проверяет blockage, upstream ponding, outlet flow, road damage и safety closure need. | Быстро переводит жалобу в action. |
| culvertops.complaint.history | complaint history | RECORD | Повторные complaints связывают с rainfall, maintenance dates и inspection scores. | Pattern показывает undercapacity или chronic blockage. |
| culvertops.complaint.public_update | public update | METHOD | Жителю сообщают received, inspected, planned action и timeline. | Снижает повторные звонки и улучшает доверие. |
| culvertops.priority.condition_score | condition score | MODEL | Score объединяет structural condition, blockage, scour, road risk и maintenance history. | Дает сравнимый repair backlog. |
| culvertops.priority.hydraulic_capacity | hydraulic capacity screen | MODEL | Capacity screen сравнивает pipe size с watershed, storm level, slope и tailwater. | Выявляет culverts, где cleanout не решит flooding. |
| culvertops.priority.replacement_trigger | replacement trigger | DECISION_RULE | Replacement нужен при collapse risk, repeated flooding, severe corrosion, undercapacity или aquatic barrier goals. | Удерживает crew от бесконечного patching. |
| culvertops.priority.bundle_projects | bundle projects | METHOD | Nearby culverts группируют по route, watershed или contractor mobilization. | Экономит mobilization cost и сокращает closures. |
| culvertops.permit.stream_work | stream work permit | CONSTRAINT | Culvert repair in stream may require permits, timing windows и erosion controls. | Road crew должна учитывать environmental compliance. |
| culvertops.permit.fish_passage | fish passage requirement | CONSTRAINT | Replacement может требовать embedment, natural bed, low-flow channel или wider span. | Совмещает road drainage и ecology. |
| culvertops.traffic.work_zone | rural work zone | SAFETY_RULE | Work zone includes signs, flaggers, cones, detour и night visibility where needed. | Защищает crew на narrow rural roads. |
| culvertops.traffic.emergency_closure | emergency closure | DECISION_RULE | Road закрывают при overtopping, embankment loss, sinkhole или exposed pipe hazard. | Предотвращает vehicle collapse or washout injury. |
| culvertops.records.asbuilt | as-built update | RECORD | После repair обновляют size, material, invert, photos, permits и costs. | Следующий inspection работает с актуальной информацией. |
| culvertops.records.cost_history | cost history | RECORD | Costs по cleanout, repair и replacement связывают с asset ID. | Показывает, где replacement дешевле постоянного maintenance. |
| culvertops.reporting.program_summary | program summary | RECORD | Summary показывает inspected, cleaned, repaired, replaced, complaints и backlog risk. | Помогает бюджетировать rural drainage program. |
| culvertops.reporting.storm_review | storm review | METHOD | После крупного storm сравнивают failures с inventory scores и rainfall. | Улучшает future priority model. |

