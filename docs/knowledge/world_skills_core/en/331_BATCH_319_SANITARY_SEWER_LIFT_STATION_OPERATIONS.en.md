# BATCH 319: Sanitary Sewer Lift Station Operations

**KnowledgeUnits:** 44  
**Namespace:** `sewerliftops.*`  
**Scope:** wet wells, pumps, force mains, alarms, generators, fats/roots, overflow response and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| sewerliftops.inventory.station_id | station ID | RECORD | Lift station получает ID, basin, force main, pumps, capacity, owner и criticality. | Связывает alarms, overflows, repairs and capital planning. |
| sewerliftops.inventory.force_main | force main record | RECORD | Force main file хранит route, diameter, material, valves, air release points и discharge manhole. | Позволяет быстро искать слабые места при failure. |
| sewerliftops.inventory.service_area | service area | RECORD | Service area maps upstream pipes, customers, low points and bypass options. | Показывает, кто пострадает при station outage. |
| sewerliftops.inventory.criticality | criticality rating | MODEL | Criticality учитывает flow, overflow consequence, access, redundancy and repair difficulty. | Приоритизирует PM and standby resources. |
| sewerliftops.wetwell.level_controls | level controls | INSPECTION | Floats, pressure sensors or ultrasonic level devices проверяют на fouling and calibration. | Неверный level signal может вызвать overflow. |
| sewerliftops.wetwell.grease_mat | grease mat | FAILURE_MODE | Fats, oils and grease form mats that block floats and pump inlets. | Regular cleaning prevents false alarms and pump damage. |
| sewerliftops.wetwell.ragging | ragging | FAILURE_MODE | Wipes and rags wrap impellers, check valves and guide rails. | Explains many repeated clog calls. |
| sewerliftops.wetwell.confined_space | confined space entry | SAFETY_RULE | Wet well entry requires permit, gas testing, ventilation and rescue plan. | Protects crews from H2S, methane, oxygen deficiency and drowning. |
| sewerliftops.wetwell.cleaning_schedule | cleaning schedule | METHOD | Cleaning frequency follows grease load, ragging history, flow and alarm patterns. | Prevents over-cleaning while controlling chronic stations. |
| sewerliftops.pumps.lead_lag | lead-lag sequence | METHOD | Lead and lag pumps alternate to balance runtime and preserve redundancy. | Reduces uneven wear and standby surprises. |
| sewerliftops.pumps.pump_test | pump test | METHOD | Test run checks amps, flow, vibration, noise, seal status and drawdown rate. | Shows whether pump performance matches need. |
| sewerliftops.pumps.drawdown_test | drawdown test | MEASUREMENT | Drawdown rate estimates pump capacity from wet well volume and level change. | Detects clogged impeller or worn pump without flow meter. |
| sewerliftops.pumps.seal_failure | seal failure | FAILURE_MODE | Seal failure allows sewage into motor chamber or oil into wet well. | Early detection prevents motor loss. |
| sewerliftops.pumps.guide_rail | guide rail condition | INSPECTION | Rails, lifting chains and discharge elbows are checked for corrosion and alignment. | Pumps must be retrievable during emergency. |
| sewerliftops.valves.check_valve | check valve | INSPECTION | Check valves are checked for slam, blockage, leakage and stuck position. | Prevents backflow and short cycling. |
| sewerliftops.valves.plug_valve | isolation valve | INSPECTION | Isolation valves are exercised and recorded for operability. | Repair requires ability to isolate pump or force main. |
| sewerliftops.force.air_release | air release valve | INSPECTION | Air release/vacuum valves are checked for clogging, odor and leakage. | Air pockets reduce capacity and can cause pressure surges. |
| sewerliftops.force.surge | pressure surge | FAILURE_MODE | Sudden pump starts/stops can create water hammer in force mains. | Surge control protects pipe and fittings. |
| sewerliftops.force.leak_response | force main leak response | METHOD | Crews isolate, bypass, contain sewage, notify and repair. | Reduces environmental and public health impact. |
| sewerliftops.force.discharge_manhole | discharge manhole | INSPECTION | Discharge manhole is checked for turbulence, corrosion, odor and surcharge. | Shows downstream capacity or force-main issues. |
| sewerliftops.alarms.high_level | high level alarm | SAFETY_RULE | High-level alarm must reach duty staff and have escalation. | It is the last warning before sanitary overflow. |
| sewerliftops.alarms.pump_fail | pump fail alarm | RECORD | Pump fail alarm logs pump, time, condition and response. | Supports reliability tracking. |
| sewerliftops.alarms.power_fail | power fail alarm | METHOD | Power fail alarm triggers generator check or portable power response. | Keeps station running during outages. |
| sewerliftops.alarms.comm_loss | communication loss | FAILURE_MODE | Loss of SCADA or cellular telemetry requires local inspection or backup alarm route. | Silent station failure is a major risk. |
| sewerliftops.power.generator_test | generator test | METHOD | Generator is tested for fuel, battery, transfer, load and alarm integration. | Backup power must work under real pump load. |
| sewerliftops.power.fuel_plan | fuel plan | RECORD | Fuel supply, delivery access, runtime and emergency vendors are documented. | Long outages need planned endurance. |
| sewerliftops.power.portable_generator | portable generator hookup | METHOD | Manual transfer connection and cable compatibility are verified. | Portable backup fails if connection is improvised. |
| sewerliftops.maintenance.pm_schedule | PM schedule | METHOD | PM covers pumps, valves, controls, wet well, generator, fencing and site drainage. | Prevents failures that create overflows. |
| sewerliftops.maintenance.root_control | root control | METHOD | Roots in upstream gravity lines are managed by cutting, chemical treatment or pipe repair. | Reduces inflow blockage and pump debris. |
| sewerliftops.maintenance.fog_program | FOG coordination | METHOD | Chronic grease stations feed outreach or enforcement for fats/oils/grease sources. | Solves cause rather than endless cleaning. |
| sewerliftops.maintenance.spare_parts | critical spares | RECORD | Spare floats, starters, fuses, seals, check valves and pumps are tracked. | Speeds repair during overflow risk. |
| sewerliftops.overflow.sso_trigger | SSO trigger | DECISION_RULE | Overflow response starts at high level, pump outage, force main break or confirmed discharge. | Establishes immediate action threshold. |
| sewerliftops.overflow.containment | overflow containment | METHOD | Crews contain, bypass, recover sewage, disinfect and protect storm drains. | Limits spread and exposure. |
| sewerliftops.overflow.notification | notification rule | CONSTRAINT | Regulators, health officials and public may need notification by deadline. | Compliance depends on timely reporting. |
| sewerliftops.overflow.volume_estimate | volume estimate | MEASUREMENT | Volume is estimated from flow, duration, area, pump data or recovery records. | Required for reports and corrective action. |
| sewerliftops.overflow.root_cause | root cause | METHOD | Cause is classified as power, pump, blockage, grease, I/I, force main, controls or operator issue. | Guides prevention. |
| sewerliftops.bypass.bypass_pump | bypass pump plan | RECORD | Bypass plan defines pump size, suction, discharge, traffic control and noise limits. | Maintains service during station repair. |
| sewerliftops.bypass.force_main_bypass | force main bypass | METHOD | Temporary discharge routing must handle pressure, odor, permits and containment. | Prevents uncontrolled sewage release. |
| sewerliftops.records.run_hours | run hours | RECORD | Run hours and starts are tracked by pump. | Shows wear, imbalance and inflow changes. |
| sewerliftops.records.work_order | work order | RECORD | Work order records fault, diagnosis, labor, parts, photos and return-to-service. | Creates station reliability history. |
| sewerliftops.records.inspection_log | inspection log | RECORD | Routine logs include levels, odors, noise, wet well condition, alarms and site condition. | Gives baseline for abnormal changes. |
| sewerliftops.records.trend_review | trend review | QUALITY_CHECK | Starts, runtimes, rainfall and levels are compared over time. | Detects inflow/infiltration or capacity loss. |
| sewerliftops.reporting.monthly_summary | monthly summary | RECORD | Summary reports PM completion, alarms, SSOs, downtime, failures and corrective actions. | Lets managers see sanitary risk. |
| sewerliftops.reporting.capital_priority | capital priority | MODEL | Replacement priority uses age, failures, capacity, criticality, parts and SSO history. | Directs budget to stations with highest public health risk. |

