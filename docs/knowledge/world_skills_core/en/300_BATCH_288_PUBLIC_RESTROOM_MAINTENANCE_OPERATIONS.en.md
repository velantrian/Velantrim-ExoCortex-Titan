# BATCH_288 — Public Restroom Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_288:public_restroom_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| restroomops.inventory.restroom_facility_record | Public restroom facility record | invariant | Record stores location, fixtures, hours, accessibility, utilities, owner and maintenance history. | manage facility |
| restroomops.inventory.fixture_inventory | Restroom fixture inventory | invariant | Inventory tracks toilets, urinals, sinks, dispensers, dryers, mirrors, partitions and drains. | know assets |
| restroomops.inventory.accessibility_features | Restroom accessibility features | invariant | Features include accessible stall, grab bars, turning space, sink clearance, signs and route. | support access |
| restroomops.inventory.seasonal_status | Public restroom seasonal status | variant | Status records seasonal opening, winterization, water shutoff, portable units or closure period. | plan service |
| restroomops.checks.opening_check | Public restroom opening check | invariant | Check verifies cleanliness, supplies, fixtures, lights, doors, locks, odors and hazards before opening. | ready facility |
| restroomops.checks.midday_check | Restroom midday check | variant | Check restores supplies, removes litter, inspects fixtures and handles emerging complaints. | maintain service |
| restroomops.checks.closing_check | Public restroom closing check | invariant | Check secures facility, cleans, reports damage, removes trash and confirms closure status. | end day |
| restroomops.checks.high_use_event_check | High-use restroom event check | variant | Check increases frequency during events, beach days, markets, festivals or park peaks. | handle demand |
| restroomops.cleaning.toilet_cleaning | Public toilet cleaning | invariant | Cleaning removes soil, disinfects contact surfaces, checks flush and restores sanitary condition. | hygiene |
| restroomops.cleaning.sink_counter_cleaning | Sink and counter cleaning | invariant | Cleaning addresses soap residue, hair, water, stains, clogged drains and touch points. | clean surfaces |
| restroomops.cleaning.floor_cleaning | Restroom floor cleaning | invariant | Cleaning removes litter, liquids, mud, odor sources and slip hazards from floor. | safety |
| restroomops.cleaning.deep_clean | Public restroom deep clean | variant | Deep clean tackles scale, grout, odors, walls, partitions, vents and hard-to-reach areas. | reset condition |
| restroomops.supplies.toilet_paper_stock | Toilet paper stock | invariant | Stock control ensures dispensers and storage meet use rate and service interval. | avoid shortages |
| restroomops.supplies.soap_refill | Soap refill | invariant | Refill ensures handwashing availability and checks dispenser function, leaks and vandalism. | hygiene |
| restroomops.supplies.hand_dryer_paper_towels | Hand drying supply | variant | Supply covers paper towels, dryers, batteries, jams, waste bins and accessibility. | complete wash |
| restroomops.supplies.feminine_hygiene_supply | Hygiene product supply | variant | Supply management covers dispensers, disposal bins, restocking and privacy. | inclusive service |
| restroomops.plumbing.clogged_toilet | Public restroom clogged toilet | invariant | Clog disrupts service and may involve paper, objects, vandalism, sewer backup or fixture fault. | restore function |
| restroomops.plumbing.running_toilet | Running toilet | invariant | Fault wastes water because of flapper, valve, sensor, flushometer or debris issue. | save water |
| restroomops.plumbing.sink_leak | Restroom sink leak | invariant | Leak can come from faucet, supply, drain, trap, sensor or vandalized fixture. | prevent damage |
| restroomops.plumbing.floor_drain_issue | Restroom floor drain issue | variant | Issue includes clog, odor trap drying, backup, missing cover or poor slope. | control water |
| restroomops.electrical.light_fault | Restroom lighting fault | invariant | Fault affects safety and may involve lamps, sensors, breakers, wiring or vandalism. | restore visibility |
| restroomops.electrical.hand_dryer_fault | Hand dryer fault | variant | Fault includes no power, sensor failure, overheating, noise, weak airflow or loose mounting. | repair device |
| restroomops.electrical.security_alarm | Restroom security alarm | variant | Alarm covers intrusion, door forced, smoke, fire, panic or remote monitoring event. | protect facility |
| restroomops.vandalism.graffiti | Restroom graffiti | invariant | Graffiti on walls, mirrors, doors or fixtures requires cleaning, documentation or repainting. | restore appearance |
| restroomops.vandalism.fixture_damage | Restroom fixture damage | invariant | Damage includes broken toilet, smashed sink, torn dispenser, damaged partition or door. | repair asset |
| restroomops.vandalism.arson_risk | Restroom arson risk | variant | Risk includes burned paper, scorch marks, smoke, accelerant, trash fires or repeated incidents. | escalate safety |
| restroomops.vandalism.sharps_discovery | Sharps discovery in restroom | invariant | Discovery of needles or blades requires safe handling, disposal and incident record. | protect staff |
| restroomops.closure.emergency_closure | Public restroom emergency closure | invariant | Closure occurs for sewage backup, violence, severe damage, biohazard, fire or structural risk. | protect public |
| restroomops.closure.planned_closure | Planned restroom closure | variant | Closure supports maintenance, winterization, construction, deep cleaning or event conversion. | manage access |
| restroomops.closure.reopening_check | Restroom reopening check | invariant | Check confirms cleaning, repairs, supplies, utilities, safety and signs before reopening. | restore service |
| restroomops.safety.slip_hazard | Restroom slip hazard | invariant | Hazard includes water, soap, mud, ice, loose mats or leaking fixtures. | prevent falls |
| restroomops.safety.biohazard_cleanup | Restroom biohazard cleanup | invariant | Cleanup handles blood, feces, vomit, needles or bodily fluids using PPE and procedures. | protect workers |
| restroomops.safety.staff_security | Restroom maintenance staff security | variant | Security covers working alone, hostile behavior, hidden occupants, nighttime checks and communications. | reduce risk |
| restroomops.records.cleaning_log | Public restroom cleaning log | invariant | Log records time, staff, supplies, condition, issues, closure and follow-up actions. | prove service |
| restroomops.records.repair_ticket | Restroom repair ticket | invariant | Ticket tracks plumbing, electrical, carpentry, vandalism, parts, priority and closeout. | manage work |
| restroomops.records.damage_photo | Restroom damage photo | variant | Photo documents vandalism, biohazard, fixture damage, leak or unsafe condition. | evidence |
| restroomops.reporting.supply_usage_report | Restroom supply usage report | variant | Report tracks paper, soap, liners, chemicals and abnormal consumption by location. | plan stock |
| restroomops.reporting.closure_report | Public restroom closure report | invariant | Report summarizes closures by reason, duration, location, repair status and public impact. | manage availability |
| restroomops.metrics.cleanliness_score | Restroom cleanliness score KPI | variant | Score rates odor, litter, surfaces, supplies, fixture function and user complaints. | monitor quality |
| restroomops.metrics.fixture_uptime | Restroom fixture uptime KPI | invariant | KPI measures fixture availability by toilet, sink, dryer, dispenser and location. | improve reliability |
| restroomops.coordination.park_operations | Restroom park operations coordination | variant | Coordination aligns restroom service with park events, security, trash, utilities and seasonal staffing. | integrate service |
| restroomops.coordination.contract_cleaning | Contract restroom cleaning coordination | variant | Coordination manages scope, frequency, quality checks, supply ownership and invoice verification. | control vendor |
| restroomops.continuity.portable_unit_deployment | Portable restroom deployment | variant | Deployment adds temporary capacity during closure, event, construction or seasonal demand. | maintain access |
| restroomops.close.work_closeout | Public restroom work closeout | invariant | Closeout confirms cleaning or repair completed, supplies restored, records updated and facility status set. | finish work |
