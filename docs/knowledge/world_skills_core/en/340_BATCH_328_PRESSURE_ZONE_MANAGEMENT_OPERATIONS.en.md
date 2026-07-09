# BATCH 328: Pressure Zone Management Operations

**KnowledgeUnits:** 44  
**Namespace:** `pressurezoneops.*`  
**Scope:** boundaries, PRVs, tanks, pumps, alarms, low-pressure calls, fire flow and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| pressurezoneops.inventory.zone_id | pressure zone ID | RECORD | Zone record includes ID, elevation range, sources, tanks, PRVs, pumps and boundaries. | Defines hydraulic operating unit. |
| pressurezoneops.inventory.boundary_valves | boundary valves | RECORD | Boundary valves are mapped with normal position and isolation role. | Wrong boundary status can merge zones or starve customers. |
| pressurezoneops.inventory.critical_customers | critical customers | RECORD | Hospitals, high-rise buildings, industry and fire-risk sites are flagged in each zone. | Helps prioritize pressure events. |
| pressurezoneops.boundary.closed_valve | normally closed valve | CONSTRAINT | Normally closed valves separate pressure zones and must be protected from accidental opening. | Prevents overpressure or low pressure. |
| pressurezoneops.boundary.zone_transfer | temporary zone transfer | METHOD | Temporary transfers use planned valves, pressure monitoring and customer impact review. | Maintains service during outages without destabilizing system. |
| pressurezoneops.boundary.map_qa | boundary map QA | QUALITY_CHECK | GIS boundaries are checked against SCADA, field valves and pressure observations. | Keeps maps aligned with reality. |
| pressurezoneops.prv.prv_setpoint | PRV setpoint | RECORD | PRV setpoints and downstream targets are recorded by location. | Supports troubleshooting and audits. |
| pressurezoneops.prv.pilot_check | pilot check | INSPECTION | PRV pilots, strainers and sensing lines are checked for blockage and drift. | Small parts control large pressure effects. |
| pressurezoneops.prv.bypass | PRV bypass | SAFETY_RULE | Bypass valves are controlled and logged during maintenance. | Accidental bypass can overpressurize customers. |
| pressurezoneops.prv.failure_open | PRV fail-open | FAILURE_MODE | Fail-open condition can raise downstream pressure beyond design. | Risks leaks, breaks and customer damage. |
| pressurezoneops.prv.failure_closed | PRV fail-closed | FAILURE_MODE | Fail-closed condition can cause low pressure or outage downstream. | Requires rapid response. |
| pressurezoneops.tank.hgl | hydraulic grade line | MODEL | Tank level sets pressure through elevation head in its zone. | Explains why levels and pressure move together. |
| pressurezoneops.tank.operating_band | operating band | DECISION_RULE | Tanks operate between high and low levels that preserve pressure and storage. | Prevents overflow, low pressure and stale water. |
| pressurezoneops.tank.level_alarm | tank level alarm | RECORD | High, low and communication alarms are set with escalation contacts. | Early warning for zone imbalance. |
| pressurezoneops.pumps.booster_pump | booster pump | METHOD | Booster pumps raise pressure into higher zones according to demand and tank controls. | Critical for elevated customers. |
| pressurezoneops.pumps.pump_sequence | pump sequence | DECISION_RULE | Pump sequencing balances pressure, energy, redundancy and tank turnover. | Avoids short cycling and unstable pressure. |
| pressurezoneops.pumps.vfd | variable speed control | METHOD | VFDs modulate pump output to maintain pressure setpoint. | Smooths demand changes but needs tuning. |
| pressurezoneops.alarms.high_pressure | high pressure alarm | DECISION_RULE | High pressure triggers PRV check, pump control review and boundary valve investigation. | Prevents main breaks and customer damage. |
| pressurezoneops.alarms.low_pressure | low pressure alarm | DECISION_RULE | Low pressure triggers tank/pump/source checks and possible advisory review. | Low pressure can threaten water quality. |
| pressurezoneops.alarms.sensor_drift | sensor drift | FAILURE_MODE | Pressure sensors can drift or plug, causing false alarms or missed events. | Requires calibration and field comparison. |
| pressurezoneops.calls.low_pressure_intake | low-pressure call intake | RECORD | Intake records address, fixture scope, time, neighbors, recent work and pressure symptoms. | Separates premise issue from zone event. |
| pressurezoneops.calls.field_gauge | field gauge check | MEASUREMENT | Crews measure hydrant or service pressure with calibrated gauge. | Confirms SCADA or customer report. |
| pressurezoneops.calls.premise_regulator | premise regulator | INSPECTION | Customer pressure-reducing valves can fail or restrict flow. | Not every low-pressure call is utility-side. |
| pressurezoneops.fire.fire_flow | fire flow model | MODEL | Fire flow depends on zone pressure, pipe capacity, pumps, tanks and hydrant spacing. | Pressure management affects firefighting. |
| pressurezoneops.fire.fire_event | fire event coordination | METHOD | Large fire draws are monitored for tank levels, pump status and residual pressure. | Maintains service during emergency demand. |
| pressurezoneops.fire.flow_test_review | flow test review | QUALITY_CHECK | Hydrant flow tests are reviewed for zone pressure and valve conditions. | Tests can reveal hydraulic restrictions. |
| pressurezoneops.operations.daily_review | daily pressure review | METHOD | Operators review zone trends, tank levels, alarms, pump status and unusual demand. | Finds early abnormal behavior. |
| pressurezoneops.operations.demand_peak | demand peak | MODEL | Morning, irrigation and heat peaks can depress pressure. | Helps distinguish normal peak from failure. |
| pressurezoneops.operations.leak_effect | leak effect | FAILURE_MODE | Large leaks or breaks can pull zone pressure down rapidly. | Pressure trend can detect hidden breaks. |
| pressurezoneops.operations.water_age | water age balance | MODEL | Pressure operations also affect storage turnover and water age. | Hydraulic stability and quality must be balanced. |
| pressurezoneops.maintenance.prv_pm | PRV PM | METHOD | PM includes strainer cleaning, setpoint test, valve exercise and vault condition. | Keeps pressure control reliable. |
| pressurezoneops.maintenance.vault_safety | PRV vault safety | SAFETY_RULE | Vault entry requires atmospheric checks, traffic control and fall protection where relevant. | Pressure assets can be confined-space hazards. |
| pressurezoneops.maintenance.boundary_check | boundary valve check | METHOD | Boundary valves are periodically verified for correct status. | Prevents silent zone misconfiguration. |
| pressurezoneops.records.zone_schematic | zone schematic | RECORD | Schematic shows sources, tanks, pumps, PRVs, boundaries and sensors. | Gives operators quick mental model. |
| pressurezoneops.records.setpoint_history | setpoint history | RECORD | Setpoint changes are logged with reason, approver, date and expected effect. | Prevents mystery operating changes. |
| pressurezoneops.records.event_log | pressure event log | RECORD | Events include alarms, calls, field readings, actions and resolution. | Supports after-action review. |
| pressurezoneops.qa.model_calibration | hydraulic model calibration | QUALITY_CHECK | Model pressures are compared with field gauges and SCADA trends. | Improves planning reliability. |
| pressurezoneops.qa.sensor_calibration | sensor calibration | QUALITY_CHECK | Pressure transmitters and gauges are checked on schedule. | Bad sensors create bad operations. |
| pressurezoneops.qa.minimum_pressure | minimum pressure compliance | CONSTRAINT | Utilities monitor minimum pressure requirements under normal and emergency conditions. | Supports public health and fire protection. |
| pressurezoneops.reporting.zone_dashboard | zone dashboard | RECORD | Dashboard shows pressures, levels, alarms, pumps, calls and maintenance status. | Gives system view by zone. |
| pressurezoneops.reporting.capital_need | capital need | MODEL | Repeated low pressure may indicate need for mains, tanks, pumps or PRV upgrades. | Converts operations data into infrastructure planning. |
| pressurezoneops.reporting.emergency_mode | emergency mode record | RECORD | Emergency mode documents temporary boundaries, pumps, setpoints, notices and return criteria. | Keeps abnormal pressure operations traceable. |
| pressurezoneops.review.incident_review | incident review | METHOD | Pressure incidents are reviewed for cause, response, communication and prevention. | Improves operating rules. |
| pressurezoneops.review.seasonal_tuning | seasonal tuning | METHOD | Setpoints and pump schedules may be adjusted for summer demand or winter low flow. | Keeps pressure stable across seasons. |
