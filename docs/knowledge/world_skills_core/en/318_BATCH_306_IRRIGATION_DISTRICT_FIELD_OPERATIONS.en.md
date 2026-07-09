# BATCH_306 — Irrigation District Field Operations Detail
# world_skills_core · source: world_skills_core:batch_306:irrigation_district_field_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| irrigationops.inventory.canal_segment | Irrigation canal segment record | invariant | Record stores canal reach, capacity, lining, structures, ownership, condition and maintenance history. | manage canal |
| irrigationops.inventory.gate_record | Irrigation gate record | invariant | Record captures gate type, location, actuator, condition, setting range and service area. | manage control |
| irrigationops.inventory.delivery_point | Irrigation delivery point | invariant | Point connects district supply to turnout, farm lateral, meter, user or rotation schedule. | deliver water |
| irrigationops.inventory.check_structure | Canal check structure | variant | Structure controls upstream water level, flow division and delivery stability. | regulate canal |
| irrigationops.scheduling.water_order | Irrigation water order | invariant | Order records user, volume or flow, start time, duration, crop area and delivery point. | schedule delivery |
| irrigationops.scheduling.rotation_schedule | Irrigation rotation schedule | invariant | Schedule allocates water turns by user, lateral, flow, time and priority rules. | share water |
| irrigationops.scheduling.delivery_change | Irrigation delivery change | variant | Change modifies order because of weather, crop need, canal condition or user request. | adapt operations |
| irrigationops.flow.flow_measurement | Irrigation flow measurement | invariant | Measurement estimates discharge using meter, weir, flume, gate rating or velocity-area method. | account water |
| irrigationops.flow.staff_gauge_reading | Canal staff gauge reading | invariant | Reading records water level at structure for operations, flow estimation or alarms. | monitor level |
| irrigationops.flow.gate_setting | Irrigation gate setting | invariant | Setting defines opening position used to control flow or water level. | regulate delivery |
| irrigationops.flow.flow_balance | Irrigation flow balance | variant | Balance compares inflow, deliveries, spills, storage change, seepage and losses. | account water |
| irrigationops.canals.patrol | Irrigation canal patrol | invariant | Patrol checks water level, banks, debris, leaks, gates, trespass and vegetation. | detect issues |
| irrigationops.canals.debris_removal | Canal debris removal | invariant | Removal clears branches, trash, weeds, sediment or obstruction from canal and structures. | maintain flow |
| irrigationops.canals.bank_slump | Canal bank slump | invariant | Slump indicates bank instability that can reduce capacity or cause breach. | prevent failure |
| irrigationops.canals.seepage_spot | Canal seepage spot | invariant | Seepage shows leakage through bank, lining, structure joint or animal burrow. | investigate leak |
| irrigationops.gates.gate_operation | Irrigation gate operation | invariant | Operation opens, closes or adjusts gate safely while monitoring level and downstream effects. | control water |
| irrigationops.gates.gate_jam | Irrigation gate jam | variant | Jam occurs from sediment, debris, corrosion, bent stem, failed actuator or misalignment. | restore control |
| irrigationops.gates.actuator_fault | Gate actuator fault | variant | Fault affects motor, gearbox, power, telemetry, limit switch or control signal. | repair automation |
| irrigationops.maintenance.canal_dewatering | Canal dewatering | invariant | Dewatering lowers or diverts water to allow inspection, repair, sediment removal or lining work. | access asset |
| irrigationops.maintenance.sediment_removal | Irrigation canal sediment removal | invariant | Removal restores capacity by excavating or flushing accumulated silt and sand. | improve conveyance |
| irrigationops.maintenance.vegetation_control | Canal vegetation control | invariant | Control manages weeds, roots and brush affecting flow, access, lining or visibility. | maintain capacity |
| irrigationops.maintenance.lining_repair | Canal lining repair | variant | Repair fixes cracks, panels, geomembrane, erosion, uplift or joint failure. | reduce losses |
| irrigationops.leaks.leak_complaint | Irrigation leak complaint | invariant | Complaint records seepage, wet field, bank leak, turnout leak or flooding concern. | dispatch check |
| irrigationops.leaks.emergency_breach | Irrigation canal breach | invariant | Breach releases uncontrolled water and requires shutdown, notifications, containment and repair. | protect property |
| irrigationops.leaks.turnout_leak | Irrigation turnout leak | variant | Leak at delivery structure may involve gate seal, pipe, valve, joint or damage. | fix delivery |
| irrigationops.complaints.low_flow_complaint | Irrigation low-flow complaint | invariant | Complaint reports insufficient delivery due to schedule, obstruction, gate, measurement or supply issue. | resolve service |
| irrigationops.complaints.flooding_complaint | Irrigation flooding complaint | variant | Complaint reports overtopping, spill, operational error, blockage or downstream impact. | reduce damage |
| irrigationops.complaints.water_quality_complaint | Irrigation water quality complaint | variant | Complaint notes sediment, algae, odor, debris or contamination affecting user delivery. | investigate source |
| irrigationops.accounting.delivery_record | Irrigation delivery record | invariant | Record logs delivered flow, duration, volume, user, point and operator. | bill and account |
| irrigationops.accounting.loss_estimate | Irrigation conveyance loss estimate | variant | Estimate covers seepage, evaporation, spills, operational waste and measurement error. | improve efficiency |
| irrigationops.accounting.allocation_balance | Irrigation allocation balance | invariant | Balance tracks user entitlement, ordered water, delivered water and remaining amount. | manage rights |
| irrigationops.safety.canal_public_safety | Irrigation canal public safety | invariant | Safety covers drowning risk, steep banks, fast water, signs, fences and outreach. | protect public |
| irrigationops.safety.field_staff_safety | Irrigation field staff safety | invariant | Safety includes lone work, water hazards, gates, snakes, heat, vehicles and confined spaces. | protect workers |
| irrigationops.safety.lockout_gate | Irrigation gate lockout | variant | Lockout controls energy before gate, actuator, pump or structure maintenance. | prevent injury |
| irrigationops.telemetry.remote_monitoring | Irrigation remote monitoring | variant | Monitoring tracks levels, flows, gates, alarms, power and communication status. | operate efficiently |
| irrigationops.telemetry.sensor_fault | Irrigation sensor fault | invariant | Fault affects level, flow, gate position, rain, pressure or communication readings. | verify data |
| irrigationops.telemetry.manual_override | Irrigation manual override | invariant | Override lets field staff operate structure when automation fails or safety requires. | maintain control |
| irrigationops.records.patrol_log | Irrigation patrol log | invariant | Log records canal conditions, flows, gate settings, issues, photos and actions. | trace fieldwork |
| irrigationops.records.maintenance_ticket | Irrigation maintenance ticket | invariant | Ticket tracks defect, priority, crew, materials, shutdown need, completion and cost. | manage repairs |
| irrigationops.reporting.daily_operations_report | Irrigation daily operations report | invariant | Report summarizes orders, deliveries, flows, outages, spills, complaints and maintenance. | coordinate staff |
| irrigationops.metrics.delivery_reliability | Irrigation delivery reliability KPI | invariant | KPI measures scheduled deliveries completed at requested flow and time. | improve service |
| irrigationops.metrics.unaccounted_water | Irrigation unaccounted water KPI | variant | KPI compares diverted water to measured deliveries, storage and known losses. | find losses |
| irrigationops.coordination.watermaster_link | Irrigation watermaster coordination | variant | Coordination aligns field operations with water rights, river diversions, orders and curtailments. | obey allocation |
| irrigationops.close.work_closeout | Irrigation field work closeout | invariant | Closeout confirms repair, gate setting, delivery status, records, user notice and follow-up. | finish work |
