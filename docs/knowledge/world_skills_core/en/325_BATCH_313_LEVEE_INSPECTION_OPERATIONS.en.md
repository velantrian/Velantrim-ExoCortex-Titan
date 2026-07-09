# BATCH 313: Levee Inspection Operations

**KnowledgeUnits:** 44  
**Namespace:** `leveeops.*`  
**Scope:** patrols, seepage, animal burrows, vegetation, erosion, encroachments, flood response and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| leveeops.patrol.routine_route | routine patrol route | METHOD | Patrol route покрывает crown, riverside slope, landside slope, toe, structures и access roads. | Не оставляет blind spots в линейной системе защиты. |
| leveeops.patrol.frequency | inspection frequency | DECISION_RULE | Частота зависит от season, flood stage, past defects, construction nearby и regulatory program. | Риск меняется во времени, schedule должен это отражать. |
| leveeops.patrol.two_person_rule | two-person patrol | SAFETY_RULE | During flood or remote patrols экипажи работают парами и с communication plan. | Снижает риск при ночных и мокрых условиях. |
| leveeops.patrol.stage_trigger | river stage trigger | DECISION_RULE | Flood patrol начинается при заданных river stages или forecasts. | Позволяет заранее увидеть seepage и slope distress. |
| leveeops.patrol.logbook | patrol logbook | RECORD | Logbook фиксирует reach, time, stage, weather, observers, defects и actions. | Создает доказуемую историю состояния levee. |
| leveeops.seepage.clear_seep | clear seep | OBSERVATION | Clear seepage without soil movement может быть monitored, но требует location tracking. | Не всякая вода является piping, но она сигнал риска. |
| leveeops.seepage.sand_boiling | sand boil | FAILURE_MODE | Sand boil with sediment indicates internal erosion or piping risk. | Требует emergency response, not routine note. |
| leveeops.seepage.toe_wetness | toe wetness | OBSERVATION | Wet spots at landside toe могут указывать seepage, drainage issue или rainfall ponding. | Field context отличает flood seepage от поверхностной воды. |
| leveeops.seepage.relief_well | relief well check | INSPECTION | Relief wells проверяют на flow, blockage, damage, settlement и access. | Wells снижают pressure только если работают. |
| leveeops.seepage.seepage_map | seepage map | RECORD | Seepage points наносят на map с stage, flow estimate и turbidity. | Помогает видеть повторяющиеся weak zones. |
| leveeops.animals.burrow_detection | burrow detection | INSPECTION | Burrows ищут на slopes, toe, near structures и vegetated areas. | Animal holes создают seepage paths и local instability. |
| leveeops.animals.burrow_class | burrow classification | RECORD | Классифицируют diameter, depth indication, activity, species clues и location. | Приоритизирует заполнение и control. |
| leveeops.animals.repair_fill | burrow repair fill | METHOD | Burrow repair uses suitable compacted fill and surface restoration per standard. | Просто засыпать loose soil часто недостаточно. |
| leveeops.animals.wildlife_control | wildlife control coordination | METHOD | Persistent burrowing requires coordination with wildlife/control authorities. | Maintenance не решает биологический источник без program control. |
| leveeops.vegetation.mowing_window | mowing window | METHOD | Vegetation mowing поддерживает visibility while respecting weather, nesting and access constraints. | Инспекция невозможна через плотную высокую растительность. |
| leveeops.vegetation.woody_growth | woody growth risk | FAILURE_MODE | Trees and brush can create root paths, windthrow voids and inspection obstruction. | Woody vegetation на levee часто является structural concern. |
| leveeops.vegetation.root_void | root void | FAILURE_MODE | Dead roots may decay and form seepage pathways. | Удаление деревьев требует engineered backfill plan. |
| leveeops.vegetation.herbicide_record | herbicide record | RECORD | Chemical control фиксирует product, applicator, weather, area и restrictions. | Нужен для compliance и повторяемости vegetation program. |
| leveeops.erosion.slope_rill | slope rill erosion | INSPECTION | Rills and gullies на slopes показывают runoff concentration. | Ранний repair защищает geometry levee. |
| leveeops.erosion.wave_wash | wave wash | FAILURE_MODE | Wave wash повреждает riverside slope and armoring during high water/wind. | Требует armor repair или временной защиты до следующего flood. |
| leveeops.erosion.toe_scour | toe scour | INSPECTION | Scour at levee toe or channel edge undermines slope support. | Может ускорить instability при high stage. |
| leveeops.erosion.surface_crack | surface cracking | OBSERVATION | Longitudinal или transverse cracks фиксируют по length, width, offset и moisture. | Cracks могут отражать settlement, desiccation или slope movement. |
| leveeops.erosion.slough_slide | slough or slide | FAILURE_MODE | Sloughing indicates shallow slope failure or saturated soil movement. | Требует geotechnical review, not cosmetic grading only. |
| leveeops.encroachments.utility_crossing | utility crossing | RECORD | Pipes, cables и conduits через levee need permits, seals, inspections и as-builts. | Uncontrolled crossings create seepage and access risk. |
| leveeops.encroachments.fence | fence encroachment | INSPECTION | Fences can block patrol access or penetrate levee section. | Even small encroachments matter in emergency movement. |
| leveeops.encroachments.structure_nearby | nearby structure | CONSTRAINT | Buildings, fill, excavation or ponds near levee can alter load and seepage. | Land-use control protects levee integrity. |
| leveeops.encroachments.unpermitted_work | unpermitted work | FAILURE_MODE | Unauthorized digging, ramps, roads or landscaping can weaken levee. | Needs fast stop-work and documentation. |
| leveeops.structures.closure_structure | closure structure | INSPECTION | Gates, stoplogs and closures are checked for fit, seals, corrosion, storage and deployment access. | Flood protection fails if closures cannot be installed. |
| leveeops.structures.pipe_penetration | pipe penetration | INSPECTION | Pipes through levee are checked for seepage, joints, flap gates, corrosion and animal access. | Penetrations are common weak points. |
| leveeops.structures.pump_station_interface | pump station interface | INSPECTION | Pump station walls, discharge pipes, backup power and levee tie-ins are checked together. | Interface failures can bypass levee protection. |
| leveeops.structures.access_road | access road condition | INSPECTION | Crown or toe roads need passability, drainage and load capacity for emergency crews. | Flood response depends on reliable access. |
| leveeops.floodresponse.watch_level | watch level | DECISION_RULE | Watch level increases patrol staffing, reporting frequency and staging of materials. | Escalation happens before visible distress becomes crisis. |
| leveeops.floodresponse.sandbag_plan | sandbag plan | METHOD | Sandbags, plastic, pumps and lighting are staged by vulnerable reaches and access routes. | Reduces response time under high water. |
| leveeops.floodresponse.boil_ring | sand boil ring | METHOD | Emergency boil rings reduce hydraulic gradient while allowing clear water to flow. | Helps control piping without sealing pressure dangerously. |
| leveeops.floodresponse.incident_command | incident command link | METHOD | Levee patrol reports feed emergency management with location, severity and resource needs. | Field observations become coordinated action. |
| leveeops.floodresponse.night_patrol | night patrol lighting | SAFETY_RULE | Night patrols need lighting, reflective gear, communication and traffic control. | Most flood risk can peak outside daylight. |
| leveeops.qa.defect_codes | defect code list | RECORD | Standard defect codes cover seepage, erosion, vegetation, animal, encroachment and structure issues. | Makes reports comparable across reaches. |
| leveeops.qa.severity_rating | severity rating | MODEL | Severity combines likelihood, consequence, flood stage sensitivity and repair urgency. | Helps rank many defects during limited crew time. |
| leveeops.qa.gps_accuracy | GPS accuracy note | QUALITY_CHECK | Location records include accuracy, offset from levee stationing and photo direction. | Crews can return to the exact defect. |
| leveeops.qa.reinspection | reinspection closeout | QUALITY_CHECK | Repairs are reinspected for compaction, grade, vegetation cover and recurrence. | Closure means defect resolved, not just work performed. |
| leveeops.reporting.daily_flood_report | daily flood report | RECORD | During flood, reports summarize stage, patrols, defects, actions and resource gaps. | Decision-makers see current levee risk. |
| leveeops.reporting.annual_inspection | annual inspection report | RECORD | Annual report includes inventory, condition, deficiencies, repairs, photos and priority plan. | Supports funding, compliance and readiness. |
| leveeops.reporting.deficiency_tracker | deficiency tracker | RECORD | Tracker assigns owner, due date, status, evidence and risk rating to each issue. | Prevents defects from disappearing after inspection. |
| leveeops.reporting.after_action | after-action review | METHOD | After floods, teams review performance, near misses, communications and repair needs. | Turns emergency experience into better operations. |

