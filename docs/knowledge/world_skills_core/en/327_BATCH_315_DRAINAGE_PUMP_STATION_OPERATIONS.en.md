# BATCH 315: Drainage Pump Station Operations

**KnowledgeUnits:** 44  
**Namespace:** `drainpumpops.*`  
**Scope:** wet wells, pumps, controls, power, alarms, maintenance, storm staffing and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| drainpumpops.inventory.station_id | station ID | RECORD | Pump station получает ID, basin, outfall, owner, pump count, capacity и control mode. | Связывает alarms, work orders и storm performance. |
| drainpumpops.inventory.service_area | service area map | RECORD | Карта показывает streets, drains, pipes, low points и properties served. | Объясняет, что затопит при отказе станции. |
| drainpumpops.inventory.pump_curve | pump curve file | RECORD | Для каждого pump хранят curve, motor rating, impeller, speed и design point. | Помогает отличать hydraulic limit от mechanical failure. |
| drainpumpops.inventory.outfall_condition | outfall condition | INSPECTION | Outfall проверяют на flap gate, tailwater, debris, erosion и access. | Pumping useless, если discharge blocked или submerged. |
| drainpumpops.wetwell.level_setpoints | wet well setpoints | DECISION_RULE | Start, stop, lead-lag и high-high levels задают по storage, pump capacity и inflow behavior. | Неверные setpoints вызывают short cycling или flooding. |
| drainpumpops.wetwell.sediment | wet well sediment | INSPECTION | Sediment, grit и debris уменьшают storage and clog pumps. | Regular cleaning keeps controls and hydraulics reliable. |
| drainpumpops.wetwell.float_check | float check | QUALITY_CHECK | Floats or level sensors test for free movement, accuracy and fouling. | Sensor failure can stop pumps even if hardware is good. |
| drainpumpops.wetwell.confined_space | confined space rule | SAFETY_RULE | Entry requires permit, gas monitoring, ventilation, rescue plan and trained crew. | Wet wells combine drowning, toxic gas and engulfment risks. |
| drainpumpops.wetwell.inflow_screen | inflow screen | INSPECTION | Screens and trash racks are checked for blockage before storms. | Blockage can starve or flood the station. |
| drainpumpops.pumps.lead_lag | lead-lag rotation | METHOD | Pumps rotate lead position to balance run hours and wear. | Prevents one unit from aging faster than standby pumps. |
| drainpumpops.pumps.test_run | test run | METHOD | Pumps are run under observed conditions with amps, vibration, flow and discharge check. | Finds failures before storm demand. |
| drainpumpops.pumps.clog_response | clog response | METHOD | Clogs are suspected from rising level, low flow, high amps or abnormal noise. | Fast diagnosis avoids overflow and motor damage. |
| drainpumpops.pumps.seal_leak | seal leak | FAILURE_MODE | Seal leaks allow water into motor or oil out of housing. | Early repair prevents catastrophic pump loss. |
| drainpumpops.pumps.bearing_noise | bearing noise | FAILURE_MODE | Growling, heat or vibration suggests bearing wear or misalignment. | Maintenance can be scheduled before pump seizure. |
| drainpumpops.pumps.check_valve | check valve inspection | INSPECTION | Check valves are checked for slam, stuck open, leakage and debris. | Prevents backflow and repeated pump cycling. |
| drainpumpops.controls.scada_status | SCADA status | RECORD | SCADA shows levels, run status, faults, power, communications and trends. | Operators see station health without visiting every site. |
| drainpumpops.controls.manual_override | manual override | SAFETY_RULE | Manual mode is logged and returned to automatic when conditions allow. | Prevents accidental disablement of flood protection. |
| drainpumpops.controls.panel_inspection | panel inspection | INSPECTION | Panels are checked for moisture, corrosion, breakers, starters, VFDs and labeling. | Electrical faults often appear before storm events. |
| drainpumpops.controls.alarm_test | alarm test | QUALITY_CHECK | High level, power fail, pump fail and communication alarms are tested. | Alarm chains must work before operators rely on them. |
| drainpumpops.controls.trend_review | trend review | QUALITY_CHECK | Runtime, starts, levels and rainfall are trended for abnormal behavior. | Trends reveal capacity loss and sensor drift. |
| drainpumpops.power.utility_feed | utility feed | INSPECTION | Utility service, transformer, disconnects and surge protection are checked. | Pump station reliability begins at incoming power. |
| drainpumpops.power.generator | backup generator | METHOD | Generator test includes fuel, battery, transfer switch, load and exhaust. | Backup power must run under real pump load. |
| drainpumpops.power.fuel_stock | fuel stock | RECORD | Fuel level, supplier, delivery access and consumption rate are tracked. | Long storms require endurance planning. |
| drainpumpops.power.transfer_switch | transfer switch | QUALITY_CHECK | ATS is tested for automatic start, load transfer and retransfer. | Generator without transfer is not useful protection. |
| drainpumpops.alarms.callout_roster | callout roster | RECORD | Roster lists primary, backup, escalation and contractor contacts. | Alarms need humans who can respond. |
| drainpumpops.alarms.ack_time | alarm acknowledgment time | MEASUREMENT | Response metrics track notification, acknowledgment, arrival and resolution times. | Shows whether staffing matches flood risk. |
| drainpumpops.alarms.nuisance_alarm | nuisance alarm | FAILURE_MODE | Repeated false alarms cause fatigue and delayed response. | Bad alarm tuning reduces real emergency readiness. |
| drainpumpops.maintenance.pm_schedule | PM schedule | METHOD | Preventive maintenance covers pumps, valves, sensors, panels, generator, structure and site. | Shared schedule prevents hidden single-point failures. |
| drainpumpops.maintenance.cleaning | wet well cleaning | METHOD | Cleaning removes sediment, trash, grease and vegetation with bypass or shutdown plan. | Restores storage and protects impellers. |
| drainpumpops.maintenance.lubrication | lubrication task | METHOD | Motors, bearings, couplings and gates are lubricated per manufacturer intervals. | Prevents wear from neglect in rarely used equipment. |
| drainpumpops.maintenance.spare_parts | critical spares | RECORD | Spare floats, starters, fuses, belts, seals, sensors and pump parts are stocked. | Storm repair cannot wait for routine procurement. |
| drainpumpops.storm.prestorm_check | pre-storm checklist | METHOD | Before storms crews check levels, debris, pumps, generator, alarms, fuel and access. | Converts forecast into readiness. |
| drainpumpops.storm.staffing | storm staffing | DECISION_RULE | Staffing increases when rainfall forecast, tide/tailwater, basin saturation or prior failures raise risk. | Keeps response aligned with event severity. |
| drainpumpops.storm.site_access | flooded access plan | METHOD | Alternate routes, high-clearance vehicles and safe parking are planned. | Operators must reach the station when roads flood. |
| drainpumpops.storm.debris_patrol | debris patrol | METHOD | Crews patrol inlets, trash racks and outfalls during intense rainfall. | Many station failures are blockage, not pump failure. |
| drainpumpops.storm.after_action | storm after-action | METHOD | After event compare rainfall, levels, runtimes, failures, complaints and repairs. | Improves capacity planning and procedures. |
| drainpumpops.records.run_hours | run hour record | RECORD | Run hours per pump are logged and compared across units. | Supports maintenance and replacement decisions. |
| drainpumpops.records.work_order | station work order | RECORD | Work orders include fault, diagnosis, parts, labor, photos and return-to-service status. | Creates traceable reliability history. |
| drainpumpops.records.bypass_plan | bypass plan | RECORD | Bypass plan lists portable pumps, hoses, power, permits and discharge location. | Provides continuity during major repair. |
| drainpumpops.records.capacity_review | capacity review | MODEL | Capacity is reviewed against changed impervious area, rainfall intensity and tailwater. | Stations can become undersized as watersheds urbanize. |
| drainpumpops.security.site_security | site security | INSPECTION | Fences, locks, cameras, lighting and vandalism signs are checked. | Protects critical flood-control assets. |
| drainpumpops.safety.electrical_loto | electrical LOTO | SAFETY_RULE | Electrical work uses lockout/tagout, verification and qualified personnel. | Prevents shock and unexpected pump start. |
| drainpumpops.reporting.monthly_summary | monthly summary | RECORD | Summary reports availability, failures, PM completion, alarms and storm events. | Lets managers see system readiness. |
| drainpumpops.reporting.capital_priority | capital priority | DECISION_RULE | Replacement priority uses age, failure rate, capacity gap, criticality and parts availability. | Guides capital budget to highest flood-risk stations. |

