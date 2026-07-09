# BATCH 384: Disaster Fuel Distribution Operations

**KnowledgeUnits:** 44  
**Namespace:** `fueldistops.*`  
**Scope:** fuel requests, allocation, depot control, delivery, security, reconciliation and audit.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| fueldistops.activation.trigger | fuel activation trigger | MODEL | Trigger includes utility outage, fleet surge, generator deployment or fuel market disruption. | Starts controlled fuel operations. |
| fueldistops.activation.fuel_cell | fuel cell | RECORD | Fuel cell names lead, finance, logistics, safety and supplier contacts. | Centralizes decisions. |
| fueldistops.activation.priority_policy | priority policy | CONSTRAINT | Policy ranks life safety, hospitals, shelters, water, public safety and critical fleets. | Allocates scarce fuel fairly. |
| fueldistops.activation.safety_brief | safety briefing | SAFETY_RULE | Brief covers fire, spills, vapors, traffic, grounding, PPE and no-smoking rules. | Protects people and facilities. |
| fueldistops.request.request_id | fuel request ID | RECORD | Request ID links requester, mission, fuel type, quantity, location and priority. | Tracks demand. |
| fueldistops.request.fuel_type | fuel type | RECORD | Type distinguishes gasoline, diesel, propane, aviation, heating or generator fuel. | Prevents wrong delivery. |
| fueldistops.request.burn_rate | burn rate | MEASUREMENT | Burn rate estimates consumption per hour, vehicle, generator or facility. | Predicts resupply timing. |
| fueldistops.request.validation | request validation | QUALITY_CHECK | Validation checks mission need, tank capacity, current stock and duplicate requests. | Prevents over-ordering. |
| fueldistops.allocation.priority | allocation priority | MODEL | Allocation considers mission criticality, remaining fuel, delivery distance and alternatives. | Sends fuel where needed most. |
| fueldistops.allocation.quantity | allocation quantity | METHOD | Quantity balances requested amount, safe storage and available supply. | Avoids waste and shortage. |
| fueldistops.allocation.reserve | reserve level | CONSTRAINT | Reserve protects critical missions and next operational period. | Prevents empty depots. |
| fueldistops.allocation.approval | allocation approval | RECORD | Approval records amount, approver, mission and restrictions. | Supports audit. |
| fueldistops.depot.depot_id | depot ID | RECORD | Depot ID links location, tanks, capacity, staff, security and fuel types. | Creates controlled storage point. |
| fueldistops.depot.inventory | depot inventory | MEASUREMENT | Inventory tracks starting stock, receipts, issues, losses and ending balance. | Maintains accountability. |
| fueldistops.depot.access | depot access control | SAFETY_RULE | Access is limited to authorized staff, drivers and vehicles. | Protects scarce fuel. |
| fueldistops.depot.spill_control | spill control | SAFETY_RULE | Spill kits, containment and reporting process are staged at depot. | Reduces environmental harm. |
| fueldistops.delivery.dispatch | delivery dispatch | METHOD | Dispatch assigns truck, driver, route, quantity, destination and contact. | Moves fuel safely. |
| fueldistops.delivery.route | route planning | METHOD | Route considers road closures, security, bridge limits, weather and return fuel. | Improves reliability. |
| fueldistops.delivery.meter_ticket | meter ticket | RECORD | Meter ticket records gallons, fuel type, source, destination and operator. | Supports reconciliation. |
| fueldistops.delivery.receipt | delivery receipt | RECORD | Recipient confirms quantity, condition, time and tank/equipment filled. | Closes delivery loop. |
| fueldistops.equipment.generator_link | generator link | RECORD | Fuel issue links to generator ID, size, run hours and site. | Supports refuel planning. |
| fueldistops.equipment.vehicle_link | vehicle link | RECORD | Vehicle fueling records unit, odometer/hour meter, fuel type and mission. | Controls fleet fuel. |
| fueldistops.equipment.tank_capacity | tank capacity | RECORD | Tank capacity prevents unsafe overfill and informs delivery quantity. | Reduces spills. |
| fueldistops.equipment.compatibility | fuel compatibility | SAFETY_RULE | Fuel type must match engine, tank, hose and site rules. | Prevents equipment damage. |
| fueldistops.security.escort | escort need | MODEL | High-risk deliveries may need escort due to scarcity, unrest or route hazard. | Protects supply. |
| fueldistops.security.theft_flag | theft flag | MODEL | Abnormal loss, missing tickets or unauthorized access trigger review. | Detects diversion. |
| fueldistops.security.seal | seal control | RECORD | Tanker or portable tank seals are recorded where used. | Maintains integrity. |
| fueldistops.security.public_queue | public queue control | METHOD | Public fuel distribution, if authorized, uses queue, limits and safety controls. | Prevents disorder. |
| fueldistops.finance.price_record | price record | RECORD | Price records contract, spot price, taxes, fees and emergency premium. | Supports finance. |
| fueldistops.finance.cost_code | cost code | RECORD | Fuel costs link to incident, mission, department and reimbursement category. | Enables recovery. |
| fueldistops.finance.invoice_match | invoice match | QUALITY_CHECK | Invoice matches delivery tickets, receipts and contract terms. | Prevents overpayment. |
| fueldistops.finance.exception | finance exception | RECORD | Exceptions record disputed gallons, price, missing ticket or rejected delivery. | Keeps issues visible. |
| fueldistops.records.daily_reconcile | daily reconciliation | QUALITY_CHECK | Daily reconciliation compares stock, receipts, issues, meter and physical inventory. | Finds losses early. |
| fueldistops.records.environment | environmental record | RECORD | Spills, disposal, contaminated fuel and cleanup are documented. | Supports compliance. |
| fueldistops.records.retention | retention rule | CONSTRAINT | Tickets, logs, invoices and incident records follow finance/grant retention. | Preserves audit trail. |
| fueldistops.communication.status | fuel status update | METHOD | Status updates report stock, shortages, delivery delays and priorities. | Guides command. |
| fueldistops.communication.requester_notice | requester notice | METHOD | Requesters receive approved quantity, ETA, limits or denial reason. | Sets expectations. |
| fueldistops.communication.safety_notice | safety notice | SAFETY_RULE | Fuel safety notices cover generator distance, ventilation, refueling and storage. | Reduces fires and poisoning. |
| fueldistops.metrics.fill_rate | fill rate | MEASUREMENT | Fill rate tracks requested versus delivered fuel by mission. | Shows supply adequacy. |
| fueldistops.metrics.stockout | stockout risk | MEASUREMENT | Stockout risk estimates time until depletion by depot and fuel type. | Drives resupply. |
| fueldistops.qa.audit_sample | audit sample | QUALITY_CHECK | Samples verify tickets, receipts, missions and inventories. | Improves integrity. |
| fueldistops.demob.recovery | demob recovery | METHOD | Demob recovers portable tanks, closes depots, reconciles inventory and returns equipment. | Ends operation cleanly. |
| fueldistops.review.after_action | after-action review | METHOD | Review captures supplier, routing, theft, safety and allocation lessons. | Improves next fuel response. |
| fueldistops.governance.fuel_owner | fuel owner | RECORD | Fuel owner coordinates logistics, finance, safety and supplier contracts. | Keeps accountability clear. |
