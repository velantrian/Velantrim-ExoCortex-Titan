# BATCH 386: Emergency Generator Deployment Operations

**KnowledgeUnits:** 44  
**Namespace:** `generatordeployops.*`  
**Scope:** requests, sizing, fuel, installation, safety checks, maintenance, return and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| generatordeployops.request.request_id | generator request ID | RECORD | Request ID links site, requester, load, urgency, duration and status. | Tracks generator demand. |
| generatordeployops.request.mission | mission need | RECORD | Mission describes critical function such as shelter, water, medical, traffic or communications. | Justifies deployment. |
| generatordeployops.request.priority | priority level | MODEL | Priority considers life safety, service outage, vulnerable population and alternatives. | Allocates scarce units. |
| generatordeployops.request.site_contact | site contact | RECORD | Site contact provides access, electrical, fuel and security details. | Enables deployment. |
| generatordeployops.sizing.load_list | load list | RECORD | Load list records equipment, watts/kW, startup surge and critical/noncritical status. | Sizes generator correctly. |
| generatordeployops.sizing.capacity_match | capacity match | METHOD | Generator is matched to load, phase, voltage, runtime and connection type. | Prevents overload. |
| generatordeployops.sizing.electrician_review | electrician review | SAFETY_RULE | Qualified electrical review is required for facility connection. | Prevents backfeed and fire. |
| generatordeployops.sizing.substitution | substitution | METHOD | Substitution uses load shedding or different unit when exact size unavailable. | Keeps mission running. |
| generatordeployops.inventory.unit_id | generator unit ID | RECORD | Unit ID links model, capacity, fuel type, hours, owner and status. | Controls assets. |
| generatordeployops.inventory.availability | availability status | RECORD | Status shows available, deployed, maintenance, reserved or out of service. | Supports dispatch. |
| generatordeployops.inventory.accessories | accessory kit | RECORD | Kit includes cables, camlocks, grounding, transfer gear, oil and tools. | Enables installation. |
| generatordeployops.inventory.test_run | test run | QUALITY_CHECK | Units are test-run before deployment where feasible. | Reduces field failure. |
| generatordeployops.dispatch.dispatch_order | dispatch order | RECORD | Order lists unit, destination, driver, route, accessories and ETA. | Moves equipment. |
| generatordeployops.dispatch.transport | transport method | METHOD | Transport uses trailer, flatbed, forklift or tow vehicle by unit size. | Prevents damage. |
| generatordeployops.dispatch.route_check | route check | METHOD | Route checks road closures, weight, access, turning and security. | Improves delivery. |
| generatordeployops.dispatch.handoff | handoff proof | RECORD | Handoff records site contact, condition, time and accessories delivered. | Closes delivery loop. |
| generatordeployops.install.site_assessment | site assessment | SAFETY_RULE | Site checks ventilation, exhaust, carbon monoxide, weather, flood, grounding and clearance. | Prevents fatal hazards. |
| generatordeployops.install.connection | connection process | METHOD | Connection follows transfer switch, manual interlock or approved temporary setup. | Avoids unsafe backfeed. |
| generatordeployops.install.grounding | grounding check | SAFETY_RULE | Grounding/bonding follows electrical code and unit configuration. | Reduces shock risk. |
| generatordeployops.install.load_test | load test | QUALITY_CHECK | Load test verifies voltage, frequency, load balance and equipment startup. | Confirms function. |
| generatordeployops.fuel.fuel_type | fuel type | RECORD | Fuel type records diesel, gasoline, propane or natural gas need. | Coordinates fuel supply. |
| generatordeployops.fuel.burn_rate | burn rate | MEASUREMENT | Burn rate estimates fuel per hour at expected load. | Plans refueling. |
| generatordeployops.fuel.refuel_schedule | refuel schedule | METHOD | Schedule uses tank size, burn rate, access, weather and mission priority. | Prevents shutdown. |
| generatordeployops.fuel.spill_control | spill control | SAFETY_RULE | Fueling uses containment, no ignition, PPE and spill reporting. | Protects site. |
| generatordeployops.operation.operator_brief | operator briefing | METHOD | Site staff learn start/stop, alarms, load limits, refueling and emergency contacts. | Reduces misuse. |
| generatordeployops.operation.run_log | run log | RECORD | Log records hours, load, fuel, alarms and maintenance. | Supports service and cost. |
| generatordeployops.operation.load_shedding | load shedding | METHOD | Noncritical loads are removed when capacity or fuel is limited. | Protects critical function. |
| generatordeployops.operation.noise | noise control | CONSTRAINT | Noise and placement consider residents, shelters and ordinances where possible. | Reduces conflict. |
| generatordeployops.maintenance.daily_check | daily check | QUALITY_CHECK | Check covers fuel, oil, coolant, leaks, cables, exhaust and alarms. | Prevents failure. |
| generatordeployops.maintenance.service_interval | service interval | CONSTRAINT | Service follows run hours, manufacturer guidance and field conditions. | Keeps unit reliable. |
| generatordeployops.maintenance.failure | failure response | METHOD | Failure triggers troubleshooting, replacement, repair or load transfer. | Restores power. |
| generatordeployops.maintenance.parts | spare parts | RECORD | Parts include oil, filters, belts, fuses, cables and connectors. | Supports field maintenance. |
| generatordeployops.safety.co_monitor | carbon monoxide control | SAFETY_RULE | Generators stay outdoors away from intakes, with CO awareness and monitors where needed. | Prevents poisoning. |
| generatordeployops.safety.weather | weather protection | SAFETY_RULE | Placement protects unit from flood, wind, rain and overheating without blocking ventilation. | Maintains safe operation. |
| generatordeployops.safety.security | security | METHOD | Units may need fencing, locks, lighting or patrols. | Prevents theft and tampering. |
| generatordeployops.safety.incident | incident report | RECORD | Incidents record shock, fire, spill, CO alarm, theft or equipment damage. | Supports corrective action. |
| generatordeployops.finance.cost_code | cost code | RECORD | Costs link rental, fuel, transport, maintenance and labor to incident mission. | Supports reimbursement. |
| generatordeployops.finance.rental_terms | rental terms | CONSTRAINT | Rental terms define rates, damage, fuel, service and return condition. | Controls cost. |
| generatordeployops.records.deployment_file | deployment file | RECORD | File stores request, sizing, dispatch, installation, run logs, fuel and return. | Creates audit trail. |
| generatordeployops.records.retention | retention rule | CONSTRAINT | Records follow emergency, asset, finance and safety schedules. | Preserves evidence. |
| generatordeployops.return.demob_request | demob request | METHOD | Return starts when utility restored, mission ends or replacement arrives. | Avoids idle rental cost. |
| generatordeployops.return.inspection | return inspection | QUALITY_CHECK | Inspection checks hours, damage, accessories, fuel and service need. | Restores inventory. |
| generatordeployops.metrics.uptime | uptime | MEASUREMENT | Uptime tracks generator availability during mission. | Shows reliability. |
| generatordeployops.review.after_action | after-action review | METHOD | Review captures sizing errors, fuel gaps, safety issues and maintenance lessons. | Improves future deployments. |
