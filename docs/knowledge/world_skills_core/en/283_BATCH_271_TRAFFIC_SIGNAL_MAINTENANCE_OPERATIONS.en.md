# BATCH_271 — Traffic Signal Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_271:traffic_signal_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| signalops.inventory.signal_asset_record | Traffic signal asset record | invariant | Record stores controller, cabinet, poles, heads, detectors, power feed, communications and location. | know asset |
| signalops.inventory.intersection_inventory | Signalized intersection inventory | invariant | Inventory groups approaches, phases, pedestrian equipment, detection zones, preemption and timing plans. | manage node |
| signalops.inventory.cabinet_labeling | Signal cabinet labeling | invariant | Labels identify breakers, load switches, detector racks, terminals, network gear and spare circuits. | speed diagnosis |
| signalops.inventory.firmware_record | Controller firmware record | variant | Record captures controller model, firmware, conflict monitor version and approved configuration baseline. | control change |
| signalops.inspection.visual_check | Signal visual inspection | invariant | Inspection checks heads, lenses, visors, mounts, poles, cabinet condition, wiring and visibility. | find defects |
| signalops.inspection.night_visibility | Signal night visibility review | variant | Review checks lens brightness, alignment, glare, obstruction and driver recognition after dark. | protect users |
| signalops.inspection.pedestrian_equipment_check | Pedestrian signal equipment check | invariant | Check reviews push buttons, locator tones, countdown displays, accessible features and crossings. | pedestrian safety |
| signalops.inspection.conflict_monitor_test | Conflict monitor test | invariant | Test verifies monitor detects conflicting greens, red failure, voltage faults and cabinet safety logic. | prevent crashes |
| signalops.fault.dark_signal | Dark traffic signal fault | invariant | Fault means all indications are off because of power, cabinet, breaker, wiring or controller failure. | emergency response |
| signalops.fault.flash_mode | Unplanned flash mode | invariant | Flash mode indicates controller, monitor, detector, power or cabinet fault requiring diagnosis. | restore control |
| signalops.fault.stuck_phase | Stuck signal phase | invariant | Phase remains active because of detector call, controller fault, wiring issue or timing configuration. | reduce delay |
| signalops.fault.lamp_out | Signal lamp outage | invariant | Outage records failed LED module, wiring problem, load switch fault or head damage. | replace promptly |
| signalops.detectors.loop_failure | Inductive loop detector failure | invariant | Failure includes open loop, shorted loop, sensitivity problem, water intrusion or pavement damage. | restore detection |
| signalops.detectors.video_detection_fault | Video detection fault | variant | Fault may come from camera aim, lens dirt, occlusion, weather, lighting or zone configuration. | maintain calls |
| signalops.detectors.radar_detection_fault | Radar detection fault | variant | Fault may involve mounting angle, range settings, interference, firmware or blocked field of view. | reliable detection |
| signalops.detectors.ped_button_fault | Pedestrian push button fault | invariant | Fault includes dead button, stuck call, wiring break, missing sign or accessibility feature failure. | crossing access |
| signalops.timing.timing_plan_record | Signal timing plan record | invariant | Record stores cycle length, splits, offsets, coordination pattern, phase sequence and effective period. | control timing |
| signalops.timing.split_adjustment | Signal split adjustment | variant | Adjustment reallocates green time among phases based on queues, volumes, safety and policy. | improve flow |
| signalops.timing.offset_adjustment | Signal offset adjustment | variant | Offset aligns progression along corridor while considering speed, spacing, stops and side-street delay. | coordinate corridor |
| signalops.timing.flash_schedule | Signal flash schedule | variant | Schedule defines authorized flashing operation by time, location, safety review and activation rules. | controlled operation |
| signalops.repairs.led_module_replacement | LED signal module replacement | invariant | Replacement verifies correct color, size, orientation, gasket, wiring, load and final indication. | restore display |
| signalops.repairs.load_switch_replacement | Load switch replacement | invariant | Replacement corrects channel output faults and requires phase verification before return to service. | fix output |
| signalops.repairs.cabinet_power_repair | Cabinet power repair | invariant | Repair checks utility feed, breakers, surge protection, UPS, grounding and internal distribution. | restore power |
| signalops.repairs.pole_head_alignment | Signal head alignment repair | variant | Repair re-aims heads, tightens brackets, corrects visor orientation and checks driver visibility. | improve recognition |
| signalops.communication.remote_monitoring | Signal remote monitoring | invariant | Monitoring reports alarms, communication loss, flash events, detector status and cabinet door openings. | detect faults |
| signalops.communication.network_outage | Signal network outage | invariant | Outage affects remote access, coordination, clocks, alarms and data retrieval across intersections. | restore communications |
| signalops.communication.clock_sync | Signal controller clock sync | variant | Sync aligns controller time for schedules, coordination, logs and daylight saving changes. | keep patterns |
| signalops.priority.emergency_preemption | Emergency vehicle preemption | invariant | Preemption gives authorized vehicles priority through detector, confirmation, transition and recovery logic. | emergency access |
| signalops.priority.transit_priority | Transit signal priority | variant | Priority adjusts phases for buses or trams using detection, thresholds, schedule adherence and recovery. | improve transit |
| signalops.priority.railroad_preemption | Railroad preemption interface | invariant | Interface coordinates nearby signals with rail crossing activation, clearance intervals and fail-safe logic. | avoid queues |
| signalops.safety.work_zone_signal_control | Signal work zone control | invariant | Control protects crews with cones, vehicles, lane closures, lockout steps and traffic management. | worker safety |
| signalops.safety.mast_arm_damage_response | Mast arm damage response | variant | Response evaluates crash damage, head stability, electrical safety, temporary control and structural repair. | manage hazard |
| signalops.safety.cabinet_lock_control | Signal cabinet lock control | invariant | Lock control prevents unauthorized access to controller, power circuits, timing and network equipment. | protect system |
| signalops.records.trouble_ticket | Signal trouble ticket | invariant | Ticket records complaint, location, symptom, priority, crew action, parts, photos and closure. | trace work |
| signalops.records.controller_event_log | Controller event log review | invariant | Review interprets faults, detector calls, coordination changes, flash entries and communication events. | diagnose cause |
| signalops.records.as_built_update | Signal as-built update | variant | Update revises plans after equipment, wiring, detection, cabinet or timing changes. | keep records |
| signalops.reporting.monthly_fault_report | Signal monthly fault report | invariant | Report summarizes outages, flash events, detector failures, response times, repairs and repeat locations. | manage backlog |
| signalops.reporting.timing_change_report | Signal timing change report | variant | Report records reason, parameters, approval, implementation date, observed effect and rollback option. | govern changes |
| signalops.metrics.signal_uptime | Traffic signal uptime KPI | invariant | KPI tracks proportion of time signals operate normally without dark, flash or communication alarms. | reliability |
| signalops.metrics.detector_health_rate | Detector health rate KPI | variant | KPI tracks working detection channels by corridor, type, age and fault recurrence. | plan renewal |
| signalops.stock.spare_parts_control | Signal spare parts control | invariant | Control tracks LEDs, load switches, detector cards, push buttons, fuses, batteries and cabinets. | material readiness |
| signalops.stock.ups_battery_replacement | Signal UPS battery replacement | variant | Replacement follows age, test result, outage history and critical intersection priority. | backup power |
| signalops.continuity.storm_signal_response | Storm signal response | variant | Response triages dark signals, damaged heads, flooded cabinets, power loss and temporary control. | restore safety |
| signalops.close.repair_closeout | Signal repair closeout | invariant | Closeout confirms normal operation, records parts, updates ticket, logs photos and notes follow-up. | finish repair |
