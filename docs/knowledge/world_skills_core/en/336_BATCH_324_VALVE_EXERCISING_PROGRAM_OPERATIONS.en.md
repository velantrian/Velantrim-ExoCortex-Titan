# BATCH 324: Valve Exercising Program Operations

**KnowledgeUnits:** 44  
**Namespace:** `valveops.*`  
**Scope:** valve inventory, locating, turns, torque, failures, isolation maps, repairs and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| valveops.inventory.valve_id | valve ID | RECORD | Each valve has ID, GIS point, type, size, install year, zone and normal status. | Enables reliable isolation and maintenance history. |
| valveops.inventory.valve_type | valve type | RECORD | Gate, butterfly, plug, check and control valves behave differently. | Exercising method depends on valve design. |
| valveops.inventory.normal_position | normal position | RECORD | Normal open/closed status is recorded and field-verified. | Wrong normal status can cause outages or water-quality issues. |
| valveops.inventory.critical_valve | critical valve | MODEL | Critical valves isolate hospitals, transmission mains, tanks or large shutdown areas. | High-impact valves get higher maintenance priority. |
| valveops.locating.surface_box | surface box locating | METHOD | Crews locate valve boxes through maps, metal detection, probing and pavement clues. | Buried or paved-over valves cannot isolate breaks. |
| valveops.locating.gps_update | GPS update | RECORD | Corrected GPS and offset notes are recorded after field location. | Improves future emergency response. |
| valveops.locating.box_cleanout | valve box cleanout | METHOD | Dirt, gravel and debris are removed before operating the nut. | Prevents tool damage and false failure calls. |
| valveops.locating.missing_box | missing box | FAILURE_MODE | Missing or paved-over boxes are logged for repair or raising. | Asset exists only on paper until accessible. |
| valveops.exercising.turn_count | turn count | MEASUREMENT | Turns from open to closed are counted and compared with expected turns. | Unexpected turns may indicate wrong size, broken stem or map error. |
| valveops.exercising.torque | operating torque | MEASUREMENT | Torque is monitored to avoid breaking stems or gearboxes. | Gentle exercising restores motion without damage. |
| valveops.exercising.partial_cycle | partial cycle | METHOD | Large or old valves may be cycled gradually before full closure. | Reduces risk of disturbing deposits or breaking stuck valves. |
| valveops.exercising.full_cycle | full cycle | METHOD | Full close-open cycle confirms operability where safe. | Confirms valve can isolate during emergency. |
| valveops.exercising.slow_operation | slow operation | SAFETY_RULE | Valves are opened and closed slowly to avoid water hammer. | Protects mains and services from pressure surge. |
| valveops.exercising.direction | open direction | RECORD | Open-left or open-right direction is recorded for each valve. | Avoids forcing valve the wrong way. |
| valveops.failure.stuck_valve | stuck valve | FAILURE_MODE | Stuck valves are tagged with attempted turns, torque and condition. | Repair can be prioritized by isolation need. |
| valveops.failure.broken_stem | broken stem | FAILURE_MODE | Stem failure shows free spinning, no movement or abnormal turns. | Valve cannot be trusted for isolation. |
| valveops.failure.buried_valve | buried valve | FAILURE_MODE | Valve box filled with sediment or asphalt prevents access. | Requires excavation or box repair. |
| valveops.failure.leaking_valve | leaking valve | FAILURE_MODE | Closed valve that passes flow may need repair or replacement. | Isolation plans must account for leakage. |
| valveops.isolation.shutdown_area | shutdown area | MODEL | Isolation map shows customers and assets affected by closing a valve set. | Supports main break response and planned work. |
| valveops.isolation.valve_set | valve set | RECORD | Planned shutdown lists exact valves, sequence, expected pressure impacts and verification. | Prevents accidental broader outage. |
| valveops.isolation.confirmation | isolation confirmation | QUALITY_CHECK | Crews confirm isolation through pressure, hydrant flow, meters or excavation condition. | Ensures pipe is safe to repair. |
| valveops.isolation.critical_customer | critical customer notice | METHOD | Critical customers are identified before planned valve closures. | Reduces harm to medical, industrial and fire systems. |
| valveops.repairs.box_raise | box raise | METHOD | Valve boxes are raised or reset after paving or settlement. | Keeps valves accessible from street surface. |
| valveops.repairs.packing | packing leak repair | METHOD | Stem packing leaks are adjusted or repaired according to valve type. | Prevents water loss and corrosion in box. |
| valveops.repairs.replacement | valve replacement | DECISION_RULE | Replacement is prioritized for criticality, failure, age, leakage and lack of isolation alternatives. | Budget goes to valves that matter operationally. |
| valveops.repairs.work_order | repair work order | RECORD | Work order includes defect, valve ID, photos, parts, crew and closeout status. | Creates traceable maintenance loop. |
| valveops.waterquality.discolored_water | discolored water risk | FAILURE_MODE | Exercising can disturb deposits and cause customer discoloration. | Crews coordinate flushing and notices. |
| valveops.waterquality.dead_zone | dead zone detection | OBSERVATION | Unexpected closed valves can create stagnant dead zones. | Exercising improves water-quality mapping. |
| valveops.safety.traffic | traffic control | SAFETY_RULE | Valve work in roads needs cones, signs, vests and safe vehicle placement. | Protects crews during routine asset work. |
| valveops.safety.tooling | valve key safety | SAFETY_RULE | Long valve keys and powered operators require stance and torque control. | Prevents strain injuries and sudden release. |
| valveops.safety.contamination | box contamination | SAFETY_RULE | Boxes with sewage, chemicals or needles require PPE and special handling. | Street assets can contain unexpected hazards. |
| valveops.program.cycle | exercising cycle | DECISION_RULE | Cycle frequency depends on criticality, age, corrosion risk and past failures. | Resources focus on valves most likely to be needed. |
| valveops.program.route | route planning | METHOD | Routes group valves by neighborhood, pressure zone and traffic constraints. | Increases crew productivity. |
| valveops.program.season | seasonal constraints | DECISION_RULE | Freezing, paving season, road work and high demand affect exercising schedule. | Avoids creating avoidable service issues. |
| valveops.program.contractor | contractor QA | QUALITY_CHECK | Contractor work is audited for location accuracy, turns, torque and records. | Keeps outsourced data reliable. |
| valveops.records.field_form | field form | RECORD | Form captures ID, location, turns, torque, status, defects, photos and notes. | Standardizes observations. |
| valveops.records.gis_sync | GIS sync | METHOD | Field updates are reviewed and synced to GIS and asset management. | Makes maps better after every route. |
| valveops.records.history | exercise history | RECORD | History tracks date, operator, turns, failures and repairs. | Shows deterioration and repeat problems. |
| valveops.records.status_codes | status codes | RECORD | Codes distinguish exercised, inaccessible, failed, repaired, abandoned or not found. | Prevents ambiguous backlog. |
| valveops.reporting.completion_rate | completion rate | MEASUREMENT | Program reports planned versus completed valves by cycle. | Shows progress and backlog. |
| valveops.reporting.failure_rate | failure rate | MEASUREMENT | Failure rate by age, material, area and valve type guides replacement planning. | Turns maintenance data into capital insight. |
| valveops.reporting.emergency_readiness | emergency readiness | MODEL | Readiness combines critical valve operability and isolation map confidence. | Measures ability to respond to main breaks. |
| valveops.reporting.management_summary | management summary | RECORD | Summary includes exercised valves, defects, repairs, map corrections and budget needs. | Keeps leadership aware of buried infrastructure risk. |
| valveops.review.after_break | after-break review | METHOD | After main breaks, crews review whether valves worked and records were accurate. | Emergency experience improves the program. |

