# BATCH_268 — Stormwater Inspection Operations Detail
# world_skills_core · source: world_skills_core:batch_268:stormwater_inspection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| storminsp.inventory.outfall_record | Stormwater outfall record | invariant | Record stores outfall ID, location, receiving water, pipe size, material and status. | know discharge points |
| storminsp.inventory.pond_record | Stormwater pond record | invariant | Record captures pond type, owner, drainage area, outlet, access and maintenance history. | manage BMP |
| storminsp.inventory.bmp_type | Stormwater BMP type | invariant | Type identifies basin, swale, filter, inlet protection, separator or green infrastructure. | inspect correctly |
| storminsp.schedule.inspection_cycle | Stormwater inspection cycle | invariant | Cycle sets frequency by permit, season, rain event, risk and asset type. | plan compliance |
| storminsp.schedule.rain_event | Stormwater rain event trigger | variant | Trigger schedules inspection after defined rainfall, runoff, complaint or construction activity. | catch issues |
| storminsp.outfall.dry_weather_screen | Dry-weather outfall screen | invariant | Screen checks flow, odor, color, turbidity, floatables, staining and biological indicators. | detect illicit discharge |
| storminsp.outfall.flow_observation | Stormwater outfall flow observation | invariant | Observation records flow presence, rate estimate, weather, tide or upstream condition. | interpret discharge |
| storminsp.outfall.field_test | Stormwater outfall field test | variant | Test records pH, chlorine, ammonia, conductivity, temperature or detergent indicator. | screen pollutants |
| storminsp.illicit.idde_case | Illicit discharge detection case | invariant | Case links report, outfall, observations, tracing, source, enforcement and closure. | track IDDE |
| storminsp.illicit.source_tracing | Illicit discharge source tracing | variant | Tracing uses maps, manholes, dye, CCTV, sampling or business checks. | find source |
| storminsp.illicit.spill_response | Stormwater spill response | invariant | Response contains spill, protects inlets, notifies agencies, documents cleanup and samples. | reduce pollution |
| storminsp.illicit.enforcement_notice | Stormwater illicit discharge notice | invariant | Notice states discharge, evidence, required correction, deadline and penalty path. | compel fix |
| storminsp.pond.embankment_check | Stormwater pond embankment check | invariant | Check reviews erosion, settlement, animal burrows, trees, seepage and slope stability. | prevent failure |
| storminsp.pond.outlet_structure | Stormwater outlet structure check | invariant | Check reviews trash racks, weirs, orifices, valves, debris and damage. | preserve function |
| storminsp.pond.sediment_level | Stormwater pond sediment level | variant | Level estimates sediment accumulation, storage loss and dredging need. | maintain capacity |
| storminsp.pond.vegetation_condition | Stormwater pond vegetation condition | variant | Condition records invasive plants, bare areas, clogged filter media or overgrowth. | manage performance |
| storminsp.construction.site_entry | Construction stormwater site entry | invariant | Entry records permit, operator, weather, phase, disturbed area and inspector. | start inspection |
| storminsp.construction.erosion_control | Erosion control check | invariant | Check reviews silt fence, wattles, blankets, stabilization and perimeter controls. | keep sediment onsite |
| storminsp.construction.sediment_basin | Sediment basin check | variant | Check reviews capacity, outlet, skimmer, sediment depth, embankment and discharge. | manage runoff |
| storminsp.construction.inlet_protection | Storm inlet protection check | invariant | Check verifies inlet barriers, sediment removal, bypass, placement and maintenance. | protect drains |
| storminsp.construction.trackout | Construction trackout check | invariant | Check records sediment on streets, stabilized entrance, sweeping and vehicle controls. | prevent pollution |
| storminsp.maintenance.work_order | Stormwater maintenance work order | invariant | Work order records asset, defect, priority, crew, equipment, due date and result. | fix issues |
| storminsp.maintenance.debris_removal | Stormwater debris removal | invariant | Removal clears trash, leaves, sediment, branches or blockages from storm asset. | restore flow |
| storminsp.maintenance.mowing_access | Stormwater mowing and access | variant | Maintenance keeps access roads, slopes, easements and structures reachable. | enable service |
| storminsp.maintenance.repair_referral | Stormwater repair referral | variant | Referral sends structural defect, sinkhole, pipe collapse or outlet damage to repair crew. | escalate defects |
| storminsp.violation.violation_code | Stormwater violation code | invariant | Code links finding to permit, ordinance, plan requirement or maintenance duty. | consistent enforcement |
| storminsp.violation.repeat_violation | Stormwater repeat violation | variant | Violation repeats previous missed maintenance, discharge, erosion or documentation issue. | escalate |
| storminsp.followup.corrective_action | Stormwater corrective action | invariant | Action defines repair, cleanup, stabilization, maintenance or source removal. | resolve finding |
| storminsp.followup.reinspection | Stormwater reinspection | invariant | Reinspection verifies corrective action, site stabilization, discharge stop or maintenance. | close loop |
| storminsp.sampling.sample_decision | Stormwater sampling decision | variant | Decision selects sample when screening, complaint, spill or permit requires lab evidence. | evidence |
| storminsp.sampling.sample_chain | Stormwater sample custody | invariant | Custody tracks sample ID, location, time, collector, preservation and lab handoff. | defensible data |
| storminsp.records.inspection_report | Stormwater inspection report | invariant | Report documents site, weather, assets, findings, photos, violations and actions. | official record |
| storminsp.records.photo_log | Stormwater inspection photo log | invariant | Log links photos to asset, location, finding, date and inspector. | visual evidence |
| storminsp.records.map_update | Stormwater map update | variant | Update corrects asset location, connectivity, ownership, access or status. | better GIS |
| storminsp.records.case_file | Stormwater inspection case file | invariant | File stores complaints, inspections, samples, notices, orders, photos and closure. | history |
| storminsp.communication.owner_notice | Stormwater owner notice | invariant | Notice tells owner/operator finding, requirement, deadline, evidence and contact. | clear action |
| storminsp.communication.public_report | Stormwater public report response | variant | Response updates resident on complaint receipt, action, referral or closure. | transparency |
| storminsp.quality.supervisor_review | Stormwater inspection supervisor review | invariant | Review checks evidence, permit basis, violation coding, deadlines and closure. | quality |
| storminsp.safety.field_safety | Stormwater inspector field safety | invariant | Safety covers traffic, water, steep slopes, confined spaces, wildlife and weather. | protect inspector |
| storminsp.reporting.permit_report | Stormwater permit report | invariant | Report summarizes inspections, illicit discharges, maintenance, violations and public education. | permit compliance |
| storminsp.metrics.stormwater_kpi | Stormwater inspection KPI | variant | KPI tracks inspections completed, IDDE cases, maintenance backlog, violations and closure time. | manage program |
| storminsp.continuity.flood_response | Stormwater flood response inspection | variant | Inspection documents blocked assets, damage, high-water marks, repairs and public hazards. | recovery |
| storminsp.close.case_closure | Stormwater case closure | invariant | Closure records corrected, referred, unfounded, monitored, enforcement or long-term project. | end case |
| storminsp.audit.audit_trail | Stormwater inspection audit trail | invariant | Trail records inspection edits, notices, work orders, samples, approvals and closure. | accountability |
