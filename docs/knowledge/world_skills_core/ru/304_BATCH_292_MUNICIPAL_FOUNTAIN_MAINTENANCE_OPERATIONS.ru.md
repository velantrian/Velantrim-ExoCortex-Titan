# BATCH_292 — Municipal Fountain Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_292:municipal_fountain_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| fountainops.inventory.fountain_record | Municipal fountain record | invariant | Record stores location, basin, pumps, filters, lights, controls, water source and season. | manage asset |
| fountainops.inventory.pump_record | Fountain pump record | invariant | Record captures pump model, flow, power, service date, condition and spare status. | maintain pumps |
| fountainops.inventory.nozzle_record | Fountain nozzle record | variant | Record stores nozzle type, pattern, alignment, clog history and replacement parts. | control display |
| fountainops.inventory.control_panel | Fountain control panel record | invariant | Panel controls pumps, lights, timers, sensors, breakers and automation. | diagnose system |
| fountainops.water.quality_check | Fountain water quality check | invariant | Check measures clarity, odor, algae, debris, sanitizer if used, pH and contamination signs. | protect public |
| fountainops.water.algae_control | Fountain algae control | variant | Control manages sunlight, nutrients, circulation, cleaning and approved treatment. | keep clean |
| fountainops.water.makeup_water | Fountain makeup water | invariant | Makeup replaces evaporation, splash loss, leakage and maintenance drawdown. | maintain level |
| fountainops.water.cross_connection_control | Fountain cross-connection control | invariant | Control prevents fountain water from contaminating potable supply through backflow prevention. | protect water |
| fountainops.pumps.pump_startup | Fountain pump startup | invariant | Startup checks priming, valves, strainers, electrical supply, flow and abnormal noise. | start safely |
| fountainops.pumps.pump_failure | Fountain pump failure | invariant | Failure includes no flow, low flow, overheating, vibration, tripped breaker or seal leak. | restore operation |
| fountainops.pumps.strainer_cleaning | Fountain strainer cleaning | invariant | Cleaning removes leaves, trash, sediment and debris restricting pump flow. | protect pump |
| fountainops.pumps.variable_speed_drive | Fountain variable speed drive | variant | Drive controls pump speed for flow pattern, energy savings and programmed effects. | tune operation |
| fountainops.filters.filter_cleaning | Fountain filter cleaning | invariant | Cleaning removes sediment, biofilm and debris from cartridge, sand or screen filters. | maintain clarity |
| fountainops.filters.filter_pressure | Fountain filter pressure | variant | Pressure readings indicate clogging, bypass, pump issue or cleaning need. | diagnose flow |
| fountainops.nozzles.nozzle_clog | Fountain nozzle clog | invariant | Clog distorts spray pattern because of sediment, leaves, scale, algae or foreign objects. | restore display |
| fountainops.nozzles.nozzle_alignment | Fountain nozzle alignment | invariant | Alignment controls spray height, direction, splash, wind drift and public exposure. | reduce waste |
| fountainops.lighting.underwater_light_check | Fountain underwater light check | invariant | Check reviews fixture sealing, brightness, lens, wiring, grounding and control timing. | safe lighting |
| fountainops.lighting.led_driver_fault | Fountain LED driver fault | variant | Fault causes dark, flickering, wrong-color or unstable lighting circuits. | repair lights |
| fountainops.lighting.night_scene_review | Fountain night scene review | variant | Review checks lighting visibility, glare, color program, public safety and display quality. | improve amenity |
| fountainops.leaks.basin_leak | Fountain basin leak | invariant | Leak may occur through cracks, joints, waterproofing, drains, fittings or settlement. | conserve water |
| fountainops.leaks.pipe_leak | Fountain piping leak | invariant | Leak affects underground or equipment-room pipes, valves, unions and fittings. | prevent damage |
| fountainops.leaks.splash_loss | Fountain splash loss | variant | Loss occurs when spray height, wind, nozzle aim or basin edge causes water escape. | adjust display |
| fountainops.cleaning.basin_cleaning | Fountain basin cleaning | invariant | Cleaning removes sediment, coins, leaves, algae, trash, stains and slippery deposits. | keep safe |
| fountainops.cleaning.surface_descaling | Fountain surface descaling | variant | Descaling removes mineral deposits from stone, tile, metal, nozzles and fixtures. | preserve finish |
| fountainops.cleaning.coin_removal | Fountain coin removal | variant | Removal handles coins, trash and found items with custody, safety and donation rules if applicable. | clean basin |
| fountainops.winter.winterization | Fountain winterization | invariant | Winterization drains water, protects pumps, blows lines, covers features and shuts controls. | avoid freeze |
| fountainops.winter.spring_startup | Fountain spring startup | invariant | Startup cleans basin, installs components, tests pumps, fills system and verifies display. | reopen season |
| fountainops.winter.freeze_damage | Fountain freeze damage | variant | Damage includes cracked basin, broken pipe, failed valve, damaged pump or lifted finish. | repair after winter |
| fountainops.safety.electrical_safety | Fountain electrical safety | invariant | Safety covers GFCI, grounding, wet locations, lockout, underwater lights and panels. | protect workers |
| fountainops.safety.slip_hazard | Fountain slip hazard | invariant | Hazard arises from overspray, algae, wet paving, leaks, ice or cleaning residue. | prevent falls |
| fountainops.safety.public_contact | Fountain public contact risk | variant | Risk includes climbing, wading, drinking, pets, children, coins and unsafe access. | manage behavior |
| fountainops.complaints.no_flow_complaint | Fountain no-flow complaint | invariant | Complaint reports fountain off, weak spray, broken pattern or unexpected shutdown. | dispatch repair |
| fountainops.complaints.noise_complaint | Fountain noise complaint | variant | Complaint concerns pump noise, water impact, vibration, night operation or mechanical hum. | adjust system |
| fountainops.complaints.water_quality_complaint | Fountain water quality complaint | invariant | Complaint reports odor, algae, foam, discoloration, trash, dead animals or contamination. | inspect water |
| fountainops.records.maintenance_log | Fountain maintenance log | invariant | Log records checks, cleaning, water tests, repairs, parts, shutdowns and observations. | trace service |
| fountainops.records.chemical_record | Fountain treatment chemical record | variant | Record tracks approved chemical use, amount, reason, date, staff and storage. | control treatment |
| fountainops.records.shutdown_record | Fountain shutdown record | invariant | Record explains shutdown reason, duration, public notice, safety action and restart condition. | manage outage |
| fountainops.reporting.season_report | Fountain season report | variant | Report summarizes operating days, failures, water use, complaints, costs and winterization. | plan season |
| fountainops.metrics.uptime | Fountain uptime KPI | invariant | KPI measures share of scheduled operating time fountain runs as intended. | monitor reliability |
| fountainops.metrics.water_use | Fountain water use KPI | variant | KPI tracks makeup water, leaks, splash loss, evaporation and conservation actions. | manage resource |
| fountainops.coordination.events | Fountain event coordination | variant | Coordination handles temporary shutdown, display changes, crowd protection or plaza event conflicts. | support events |
| fountainops.coordination.landscape_link | Fountain landscape coordination | variant | Coordination aligns cleaning, planting, irrigation, paving and nearby drainage work. | avoid conflicts |
| fountainops.continuity.emergency_shutdown | Fountain emergency shutdown | invariant | Shutdown stops pumps or power for electrical fault, contamination, leak, injury or structural hazard. | protect public |
| fountainops.close.work_closeout | Fountain maintenance closeout | invariant | Closeout confirms repair, water quality, safe operation, records, photos and public status. | finish work |
