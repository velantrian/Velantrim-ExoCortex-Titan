# BATCH_219 — Laundromat Operations Detail
# world_skills_core · source: world_skills_core:batch_219:laundromat_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| laundromat.customer.store_opening | Laundromat store opening | invariant | Opening checks doors, lights, machines, payment systems, change, supplies, cleaning and safety. | start ready |
| laundromat.customer.store_closing | Laundromat store closing | invariant | Closing secures cash, doors, machines, lost items, trash, alarms and end-of-day logs. | reset site |
| laundromat.customer.customer_flow | Laundromat customer flow | invariant | Flow covers arrival, machine selection, payment, wash, dry, folding and exit. | understand journey |
| laundromat.customer.machine_queue | Laundry machine queue | variant | Queue helps customers wait for washers, dryers or folding tables during peak demand. | reduce conflict |
| laundromat.customer.attendant_help | Laundromat attendant help | variant | Help covers machine selection, payment issue, stuck door, refund, stain question or lost item. | service point |
| laundromat.payment.coin_box | Washer coin box | variant | Coin box collects payment and needs security, count, jam handling and audit. | cash control |
| laundromat.payment.card_reader | Laundry card reader | variant | Reader authorizes payment, starts machine and logs transaction status. | cashless operation |
| laundromat.payment.mobile_pay | Laundromat mobile payment | variant | Mobile pay links customer app, machine ID, price and cycle start. | remote payment |
| laundromat.payment.refund_log | Laundromat refund log | invariant | Log records customer, machine, issue, amount, method and approval. | fair correction |
| laundromat.payment.price_table | Laundry price table | invariant | Table defines washer size, dry time, add-ons, discounts and taxes. | transparent pricing |
| laundromat.machine.washer_status | Washer status | invariant | Status shows available, running, out-of-order, door locked, cycle complete or service needed. | visible capacity |
| laundromat.machine.dryer_status | Dryer status | invariant | Status shows available, running, cooling, blocked, out-of-order or lint service needed. | manage dryers |
| laundromat.machine.out_of_order_tag | Out-of-order tag | invariant | Tag removes failed machine from customer use and records symptom and date. | prevent frustration |
| laundromat.machine.cycle_program | Laundry cycle program | invariant | Program sets water, time, spin, temperature and soil options for customer use. | machine behavior |
| laundromat.machine.machine_number | Machine number | invariant | Number uniquely identifies washer or dryer for payment, maintenance, refund and customer support. | locate issue |
| laundromat.maintenance.lint_cleaning | Dryer lint cleaning | invariant | Cleaning removes lint from screens, ducts and accessible areas by schedule. | fire prevention |
| laundromat.maintenance.drain_check | Laundromat drain check | invariant | Check finds slow drains, backups, leaks, odors or foreign objects. | keep water moving |
| laundromat.maintenance.door_gasket | Washer door gasket check | variant | Check finds tears, trapped items, leaks, mold or poor seal. | prevent water loss |
| laundromat.maintenance.belt_motor | Laundry belt and motor check | variant | Check detects noise, slip, heat, vibration or failure signs. | uptime |
| laundromat.maintenance.vendor_service | Laundry equipment vendor service | invariant | Service call records machine, fault, parts, labor, downtime and release. | repair trace |
| laundromat.cleaning.floor_mop | Laundromat floor cleaning | invariant | Cleaning handles water, detergent, lint, spills, trash and slip hazards. | safe floor |
| laundromat.cleaning.folding_table | Folding table cleaning | invariant | Cleaning removes lint, residue, food, spills and debris from folding surfaces. | customer hygiene |
| laundromat.cleaning.soap_dispenser | Soap dispenser upkeep | variant | Upkeep fills, cleans and checks vending or dispenser mechanisms. | supply availability |
| laundromat.cleaning.restroom_check | Laundromat restroom check | invariant | Check covers soap, paper, trash, cleanliness, leaks and damage. | basic facility |
| laundromat.cleaning.lost_item_bin | Lost item bin | invariant | Bin stores found clothing and objects with date, machine and claim process. | return property |
| laundromat.safety.slip_hazard | Laundromat slip hazard | invariant | Hazard arises from wet floors, detergent spills, loose mats or blocked drains. | prevent falls |
| laundromat.safety.fire_risk | Laundromat fire risk | invariant | Risk increases with lint, overheated dryers, blocked vents, electrical faults or flammable items. | watch heat |
| laundromat.safety.child_safety | Laundromat child safety | invariant | Safety prevents children entering machines, climbing carts or playing near hot equipment. | protect families |
| laundromat.safety.chemical_storage | Laundromat chemical storage | invariant | Storage keeps detergents, bleach, cleaners and SDS separated and labeled. | exposure control |
| laundromat.safety.emergency_contact | Laundromat emergency contact | invariant | Contact list includes owner, attendant, police, fire, utility, plumber and equipment vendor. | fast escalation |
| laundromat.utilities.water_meter | Laundromat water meter | variant | Meter tracks water use and helps detect leaks or abnormal consumption. | utilities cost |
| laundromat.utilities.gas_meter | Laundromat gas meter | variant | Meter tracks dryer or water heating fuel use and variance. | energy control |
| laundromat.utilities.hot_water_system | Hot water system | invariant | System supplies washers and needs temperature, capacity, leak and safety checks. | wash quality |
| laundromat.utilities.ventilation | Laundromat ventilation | invariant | Ventilation removes heat, moisture, odors and combustion byproducts where applicable. | comfort and safety |
| laundromat.utilities.utility_outage | Laundromat utility outage | invariant | Outage process stops affected machines, informs customers and coordinates restoration. | avoid stuck loads |
| laundromat.security.camera_review | Laundromat camera review | variant | Review supports incident, damage, theft, refund dispute or safety investigation. | evidence |
| laundromat.security.cash_collection | Laundromat cash collection | variant | Collection removes coins or bills with count, witness, deposit and variance record. | reduce theft |
| laundromat.security.vandalism_report | Laundromat vandalism report | invariant | Report records damage, machine, restroom, door, camera, time and repair action. | site protection |
| laundromat.security.after_hours_access | After-hours access control | variant | Control limits entry, machine starts or attendant support outside staffed hours. | boundary |
| laundromat.security.customer_conflict | Customer conflict response | invariant | Response de-escalates disputes over machines, payment, belongings or conduct. | keep peace |
| laundromat.admin.supply_inventory | Laundromat supply inventory | invariant | Inventory tracks detergent, bags, hangers, paper goods, cleaning supplies and parts. | avoid stockout |
| laundromat.admin.attendant_task_list | Attendant task list | invariant | List schedules cleaning, customer help, machine checks, refunds, supplies and reports. | shift discipline |
| laundromat.metrics.laundromat_kpi | Laundromat KPI | variant | KPI tracks machine uptime, turns per day, refunds, utilities, complaints and revenue. | manage store |
| laundromat.continuity.flood_response | Laundromat flood response | invariant | Response shuts machines, protects power, contains water, documents damage and calls repair. | water emergency |
