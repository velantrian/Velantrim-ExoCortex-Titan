# BATCH 322: Public Water Main Flushing Operations

**KnowledgeUnits:** 44  
**Namespace:** `mainflushops.*`  
**Scope:** zones, valves, hydrants, discoloration, residuals, notices, traffic control and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| mainflushops.program.flush_zone | flushing zone | RECORD | System is divided into zones by pressure, pipe network, valves and water age. | Prevents random flushing that stirs problems elsewhere. |
| mainflushops.program.unidirectional | unidirectional flushing | METHOD | UDF closes valves to force high velocity in one pipe segment at a time. | Better removes sediment than ordinary hydrant opening. |
| mainflushops.program.velocity_target | velocity target | MEASUREMENT | Flushing aims for enough velocity to mobilize sediment without damaging system. | Too little does nothing; too much can create problems. |
| mainflushops.program.dead_end | dead-end main | MODEL | Dead-end mains have low turnover and need scheduled flushing. | Reduces water age, odor and discoloration complaints. |
| mainflushops.program.season | seasonal planning | DECISION_RULE | Flushing is scheduled around demand, freezing risk, drought restrictions and construction. | Timing affects safety and water availability. |
| mainflushops.mapping.pipe_material | pipe material map | RECORD | Pipe material, age and diameter are reviewed before flushing. | Old iron mains may release more discoloration. |
| mainflushops.mapping.valve_sequence | valve sequence | RECORD | Sequence lists which valves to close/open and in what order. | Prevents pressure loss and unintended outages. |
| mainflushops.mapping.hydrant_list | hydrant list | RECORD | Hydrant ID, location, nozzle size, drainage and condition are documented. | Crews need reliable discharge points. |
| mainflushops.mapping.sensitive_customers | sensitive customers | RECORD | Hospitals, dialysis, food plants and large users are flagged. | Reduces impact on critical customers. |
| mainflushops.valves.exercise | valve exercise | METHOD | Valves are exercised carefully and recorded during flushing setup. | Stuck or broken valves change zone plan. |
| mainflushops.valves.status_tag | valve status tag | RECORD | Field crews track temporary closed/open status. | Prevents leaving a valve wrong after flushing. |
| mainflushops.valves.broken_valve | broken valve | FAILURE_MODE | Broken or lost valves are reported for repair and map update. | Improves future isolation capability. |
| mainflushops.hydrants.flow_setup | hydrant flow setup | METHOD | Hydrant is opened slowly, flowed, monitored and closed slowly. | Reduces water hammer and main disturbance. |
| mainflushops.hydrants.diffuser | diffuser use | SAFETY_RULE | Diffuser or hose controls discharge direction and erosion. | Protects traffic, property and streams. |
| mainflushops.hydrants.dechlorination | dechlorination | CONSTRAINT | Discharge may require dechlorination before entering storm drains or waterways. | Prevents chlorine harm to aquatic life. |
| mainflushops.hydrants.hydrant_defect | hydrant defect | RECORD | Leaks, poor drainage, bad caps, stiff stems or traffic damage are logged. | Flushing doubles as hydrant condition check. |
| mainflushops.waterquality.discoloration | discoloration | OBSERVATION | Brown or red water often indicates iron or manganese sediment mobilized. | Explains customer calls during flushing. |
| mainflushops.waterquality.residual | chlorine residual | MEASUREMENT | Residual is checked before, during or after flushing where required. | Confirms disinfectant remains adequate. |
| mainflushops.waterquality.turbidity | turbidity check | MEASUREMENT | Turbidity or visual clarity helps decide when to stop flushing. | Avoids wasting water after pipe clears. |
| mainflushops.waterquality.water_age | water age | MODEL | Low demand areas can lose residual and develop taste/odor issues. | Flushing manages stagnant zones. |
| mainflushops.waterquality.sample_after | post-flush sample | QUALITY_CHECK | Samples may verify residual, clarity or bacteriological status after unusual work. | Confirms safe return to normal. |
| mainflushops.customer.notice | customer notice | METHOD | Notice explains dates, areas, possible discoloration and what customers should do. | Reduces surprise and complaint volume. |
| mainflushops.customer.laundry_warning | laundry warning | METHOD | Customers are warned to avoid laundry during discoloration windows. | Prevents stained clothes and claims. |
| mainflushops.customer.complaint_log | complaint log | RECORD | Complaints record address, time, color, pressure, odor and action. | Helps correlate impacts with flushing sequence. |
| mainflushops.customer.followup | customer follow-up | METHOD | Persistent issues trigger service line flush, sample or field visit. | Shows whether problem is system or premise plumbing. |
| mainflushops.pressure.low_pressure | low pressure risk | FAILURE_MODE | Excessive flushing can drop pressure in nearby areas. | Pressure monitoring protects service and fire flow. |
| mainflushops.pressure.water_hammer | water hammer | FAILURE_MODE | Rapid valve or hydrant changes can create surge. | Slow operation protects mains and services. |
| mainflushops.pressure.fire_flow | fire flow coordination | METHOD | Fire department and dispatch may be informed of active zones and hydrant use. | Avoids conflict during emergencies. |
| mainflushops.traffic.work_zone | work zone | SAFETY_RULE | Crews use cones, signs, vests and safe hydrant positioning. | Hydrants often sit near traffic. |
| mainflushops.traffic.night_work | night work | DECISION_RULE | Night flushing may reduce customer impact but increases traffic and visibility hazards. | Schedule choice balances disruption and crew safety. |
| mainflushops.environment.erosion | erosion control | METHOD | Discharge is directed to avoid soil erosion, flooding yards or icing roads. | Prevents maintenance from creating damage. |
| mainflushops.environment.discharge_permit | discharge permit | CONSTRAINT | Some areas require permits or best practices for chlorinated discharge. | Keeps flushing compliant. |
| mainflushops.operations.crew_brief | crew brief | METHOD | Crew reviews map, sequence, hazards, customer notes, sample needs and contacts. | Reduces mistakes in field sequence. |
| mainflushops.operations.flow_duration | flow duration | RECORD | Start time, stop time, estimated flow and clarity endpoint are logged. | Supports water loss accounting and future planning. |
| mainflushops.operations.abort_criteria | abort criteria | DECISION_RULE | Work stops for main break, pressure drop, unsafe traffic, flooding or major customer impact. | Protects system and public. |
| mainflushops.operations.restoration | restoration check | QUALITY_CHECK | Valves are returned, hydrants closed, caps replaced, pavement clear and records completed. | Prevents after-work failures. |
| mainflushops.records.water_loss | water loss estimate | MEASUREMENT | Volume is estimated from hydrant flow and duration. | Supports non-revenue water accounting. |
| mainflushops.records.gis_update | GIS update | RECORD | New valve status, hydrant defects and pipe notes update maps. | Field work improves asset data. |
| mainflushops.records.sequence_revision | sequence revision | METHOD | Field discoveries revise future flushing sequence. | Program improves with each cycle. |
| mainflushops.records.annual_history | annual history | RECORD | Yearly history tracks zones completed, complaints, water quality and repairs found. | Shows program effect over time. |
| mainflushops.qa.field_audit | field audit | QUALITY_CHECK | Supervisor audits sequence, safety, records and water quality checks. | Keeps crews consistent. |
| mainflushops.qa.data_review | data review | QUALITY_CHECK | Logs are reviewed for missing times, impossible flows and unresolved complaints. | Prevents bad operational records. |
| mainflushops.reporting.program_summary | program summary | RECORD | Summary reports miles flushed, water used, complaints, hydrant defects and water-quality results. | Communicates value of flushing program. |
| mainflushops.reporting.next_cycle | next cycle plan | METHOD | Next plan adjusts zones by complaints, residual trends, construction and valve issues. | Keeps flushing targeted rather than ritual. |

