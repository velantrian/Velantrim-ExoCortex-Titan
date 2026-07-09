# BATCH_235 — Public Park Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_235:public_park_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| parkops.workorder.request_intake | Park maintenance request intake | invariant | Intake records location, asset, issue, reporter, priority, photos and safety concern. | start work |
| parkops.workorder.priority_triage | Park work order priority triage | invariant | Triage ranks hazards, service disruption, event impact, routine care and backlog. | focus crews |
| parkops.workorder.route_batch | Park maintenance route batch | variant | Batch groups nearby tasks by crew, equipment, season and travel time. | efficient routes |
| parkops.workorder.status_update | Park work order status update | invariant | Update records assigned, in progress, waiting, completed, deferred or cancelled status. | visible progress |
| parkops.workorder.closeout_photo | Park work order closeout photo | variant | Photo documents repair completion, cleanup, hazard removal or condition change. | proof of work |
| parkops.turf.mowing_schedule | Park turf mowing schedule | invariant | Schedule assigns fields, lawns, slopes, frequency, weather limits and crew. | maintain grounds |
| parkops.turf.irrigation_check | Park irrigation check | variant | Check reviews heads, leaks, timers, coverage, pressure and water restrictions. | healthy turf |
| parkops.turf.field_lining | Athletic field lining | variant | Lining marks sport field boundaries, goals, safety buffers and event timing. | playable fields |
| parkops.turf.soil_compaction | Park soil compaction note | variant | Note records hardpan, drainage, aeration need and turf recovery plan. | improve surfaces |
| parkops.turf.pesticide_notice | Park pesticide notice | invariant | Notice records product, area, timing, restrictions, signage and applicator credentials. | public safety |
| parkops.playground.daily_inspection | Playground daily inspection | invariant | Inspection checks surfacing, swings, slides, climbers, hardware, sharp edges and debris. | child safety |
| parkops.playground.surface_depth | Playground surface depth check | invariant | Check verifies loose-fill or impact surface depth in fall zones. | reduce injury |
| parkops.playground.defect_lockout | Playground defect lockout | invariant | Lockout removes unsafe equipment from use with barriers, signs and repair order. | prevent use |
| parkops.playground.repair_log | Playground repair log | invariant | Log tracks parts, labor, inspection result, reopening approval and warranty. | repair evidence |
| parkops.playground.safety_standard_review | Playground safety standard review | variant | Review compares equipment and surfacing against applicable inspection checklist. | risk control |
| parkops.trees.tree_inventory | Park tree inventory | variant | Inventory records species, location, size, condition, risk rating and maintenance history. | urban forest control |
| parkops.trees.limb_hazard | Park limb hazard response | invariant | Response secures area, evaluates branch risk, assigns pruning and documents closure. | prevent injury |
| parkops.trees.storm_damage | Park storm tree damage | invariant | Damage log captures downed limbs, blocked paths, power risk and cleanup priority. | restore access |
| parkops.trees.planting_plan | Park tree planting plan | variant | Plan selects species, site, watering, protection and establishment schedule. | durable planting |
| parkops.trees.invasive_species | Park invasive species control | variant | Control maps invasive plants, treatment method, timing, disposal and follow-up. | protect habitat |
| parkops.litter.litter_route | Park litter collection route | invariant | Route covers bins, picnic areas, trails, parking, fields and problem hotspots. | clean park |
| parkops.litter.bin_overflow | Park bin overflow response | invariant | Response records full bin, extra pickup, cause, event link and capacity adjustment. | reduce complaints |
| parkops.litter.illegal_dumping | Park illegal dumping record | invariant | Record captures dumped items, location, photos, cleanup cost and enforcement referral. | manage abuse |
| parkops.litter.sharps_found | Park sharps found response | invariant | Response uses trained pickup, container, location record and supervisor notice. | protect public |
| parkops.litter.graffiti_removal | Park graffiti removal | variant | Removal records surface, content severity, method, timing and repeat location. | restore assets |
| parkops.restroom.restroom_round | Park restroom round | invariant | Round checks supplies, fixtures, locks, odors, floors, vandalism and accessibility. | public hygiene |
| parkops.restroom.plumbing_issue | Park restroom plumbing issue | invariant | Issue records clog, leak, fixture failure, closure and plumber dispatch. | restore service |
| parkops.restroom.cleaning_supply | Park restroom supply stock | invariant | Stock tracks paper, soap, sanitizer, bags, chemicals and refill frequency. | avoid outages |
| parkops.restroom.seasonal_opening | Park restroom seasonal opening | variant | Opening checks water, drains, heat, ventilation, locks, cleaning and signage. | start season |
| parkops.restroom.winterization | Park restroom winterization | variant | Winterization drains lines, protects fixtures, closes valves and posts closure. | prevent freeze damage |
| parkops.events.event_site_prep | Park event site preparation | variant | Preparation covers turf, power, barricades, waste, restrooms, access and restoration. | ready event |
| parkops.events.permit_condition | Park event permit condition | invariant | Condition records capacity, hours, amplified sound, vendors, cleanup and insurance. | enforce permit |
| parkops.events.post_event_walk | Park post-event walk | invariant | Walk notes trash, turf damage, utilities, fees, deposits and repair needs. | recover site |
| parkops.events.vendor_vehicle_route | Park vendor vehicle route | variant | Route controls load-in, pedestrian areas, turf protection and emergency access. | safe movement |
| parkops.safety.trail_hazard | Park trail hazard report | invariant | Report captures washout, ice, fallen tree, erosion, bridge issue or blocked path. | protect users |
| parkops.safety.lighting_check | Park lighting check | invariant | Check verifies paths, courts, parking, timers, outages and dark spots. | night safety |
| parkops.safety.water_feature_check | Park water feature check | variant | Check reviews fountains, ponds, splash pads, pumps, barriers and water quality notices. | reduce risk |
| parkops.safety.incident_report | Park incident report | invariant | Report records injury, conflict, damage, wildlife, weather or emergency response. | incident evidence |
| parkops.safety.closure_notice | Park closure notice | invariant | Notice explains closed area, cause, duration, alternative route and contact. | clear communication |
| parkops.assets.bench_table_repair | Park bench and table repair | invariant | Repair logs damaged seating, hardware, surface, paint, replacement and reopening. | usable amenities |
| parkops.assets.signage_check | Park signage check | invariant | Check covers rules, maps, wayfinding, hazards, hours and accessibility signs. | orient visitors |
| parkops.assets.irrigation_asset | Park irrigation asset record | variant | Record links valves, controllers, zones, repairs, parts and seasonal settings. | asset memory |
| parkops.reporting.park_maintenance_report | Park maintenance report | invariant | Report summarizes completed work, hazards, closures, costs, backlog and complaints. | accountable care |
| parkops.metrics.park_kpi | Park maintenance KPI | variant | KPI tracks response time, open hazards, restroom scores, litter, turf condition and event recovery. | manage parks |
