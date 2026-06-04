# BATCH_193 — Rental Equipment Fleet Operations Detail
# world_skills_core · source: world_skills_core:batch_193:rental_equipment_fleet_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| rentfleet.asset.asset_register | Rental asset register | invariant | Register lists equipment ID, serial, category, status, location, ownership and maintenance history. | know fleet |
| rentfleet.asset.utilization_status | Equipment utilization status | invariant | Status shows available, reserved, on-rent, down, in-service, lost or retired. | sell only what exists |
| rentfleet.asset.hour_meter | Hour meter record | variant | Record captures machine runtime for billing, maintenance and wear tracking. | hours matter |
| rentfleet.asset.attachment_set | Equipment attachment set | variant | Set links buckets, bits, hoses, chargers or accessories to main rental item. | complete package |
| rentfleet.asset.replacement_value | Replacement value | invariant | Value supports deposit, insurance, damage claim and loss decision. | risk pricing |
| rentfleet.reserve.reservation | Rental reservation | invariant | Reservation holds equipment, dates, customer, delivery option, rate and required accessories. | promise capacity |
| rentfleet.reserve.availability_check | Availability check | invariant | Check compares requested dates with fleet status, maintenance, transport and prior bookings. | prevent double booking |
| rentfleet.reserve.rate_card | Rental rate card | invariant | Rate card defines daily, weekly, monthly, overtime, mileage, fuel or usage fees. | consistent pricing |
| rentfleet.reserve.deposit_rule | Rental deposit rule | variant | Rule sets security amount based on customer, equipment, value, risk and payment method. | cover exposure |
| rentfleet.reserve.contract_terms | Rental contract terms | invariant | Terms define responsibility, allowed use, return condition, damage, insurance and late fees. | legal frame |
| rentfleet.dispatch.pre_rental_inspection | Pre-rental inspection | invariant | Inspection documents condition, safety devices, fluids, tires, attachments and cleanliness before dispatch. | baseline condition |
| rentfleet.dispatch.make_ready | Rental make-ready | invariant | Make-ready cleans, fuels, charges, tests and stages equipment for pickup or delivery. | ready to use |
| rentfleet.dispatch.customer_training | Customer use briefing | variant | Briefing covers basic operation, limits, safety warnings and support contact. | reduce misuse |
| rentfleet.dispatch.delivery_ticket | Delivery ticket | invariant | Ticket records equipment, condition, destination, time, driver, recipient and signature. | handoff evidence |
| rentfleet.dispatch.transport_fit | Transport fit check | variant | Check confirms trailer, tie-downs, route, loading capacity and access match equipment. | safe move |
| rentfleet.return.return_checkin | Rental return check-in | invariant | Check-in records return time, meter, fuel, condition, accessories and customer notes. | close rental period |
| rentfleet.return.damage_note | Damage note | invariant | Note records new damage, photos, severity, cause if known and claim route. | evidence before repair |
| rentfleet.return.missing_accessory | Missing accessory | invariant | Missing accessory record triggers search, charge, replacement or customer follow-up. | complete inventory |
| rentfleet.return.fuel_charge | Fuel or recharge charge | variant | Charge applies when equipment returns below agreed fuel or battery level. | recover service cost |
| rentfleet.return.late_return | Late return handling | invariant | Handling updates billing, availability, next reservation risk and customer communication. | schedule impact |
| rentfleet.maintenance.preventive_schedule | Rental preventive schedule | invariant | Schedule uses calendar, hours, cycles or inspections to trigger maintenance. | uptime discipline |
| rentfleet.maintenance.down_tag | Down equipment tag | invariant | Tag removes unsafe or failed item from available fleet until repaired and released. | do not rent broken gear |
| rentfleet.maintenance.repair_order | Rental repair order | invariant | Order records fault, diagnosis, labor, parts, vendor and return-to-service test. | fix trace |
| rentfleet.maintenance.safety_recall | Equipment safety recall | variant | Recall identifies affected assets, rental customers, stop-use instructions and repair evidence. | urgent risk control |
| rentfleet.maintenance.cleaning_standard | Rental cleaning standard | invariant | Standard defines acceptable cleanliness, sanitation, debris removal and appearance before rent. | customer-ready |
| rentfleet.billing.rental_invoice | Rental invoice | invariant | Invoice calculates rate, duration, delivery, fuel, damage, accessories, taxes and credits. | bill accurately |
| rentfleet.billing.partial_day_rule | Partial-day rule | variant | Rule defines how early returns, late pickups or hour limits affect charges. | avoid disputes |
| rentfleet.billing.damage_billing | Damage billing | invariant | Billing links damage evidence, contract responsibility, repair estimate and customer notification. | recover loss |
| rentfleet.billing.loss_charge | Lost equipment charge | invariant | Charge applies when item is not returned after search and escalation. | asset accountability |
| rentfleet.billing.credit_adjustment | Rental credit adjustment | variant | Adjustment corrects outage, wrong equipment, service failure or agreed concession. | fair resolution |
| rentfleet.customer.account_approval | Rental account approval | invariant | Approval checks identity, payment, credit, insurance, tax status and authorized users. | trust before release |
| rentfleet.customer.insurance_certificate | Insurance certificate | variant | Certificate confirms customer coverage required for certain equipment or contracts. | transfer risk |
| rentfleet.customer.authorized_operator | Authorized operator | variant | Operator record identifies who may pick up, sign or use controlled equipment. | prevent misuse |
| rentfleet.customer.jobsite_record | Customer jobsite record | variant | Record captures delivery address, access hours, hazards, contact and site rules. | delivery readiness |
| rentfleet.customer.dispute_case | Rental dispute case | invariant | Case documents billing, damage, delay or service disagreement and resolution. | structured recovery |
| rentfleet.inventory.parts_stock | Rental parts stock | variant | Stock supports common maintenance parts, wear items and consumables. | faster turnaround |
| rentfleet.inventory.consumable_sale | Consumable sale | variant | Sale adds blades, belts, fuel, PPE, chemicals or supplies to rental transaction. | attach needed items |
| rentfleet.inventory.cycle_count | Rental inventory cycle count | invariant | Count verifies physical assets and accessories against system records. | find losses |
| rentfleet.inventory.asset_transfer | Fleet asset transfer | invariant | Transfer moves equipment between branches with condition, transport and system update. | balance demand |
| rentfleet.inventory.retirement | Rental asset retirement | invariant | Retirement removes asset due to age, damage, utilization, safety or economics. | lifecycle close |
| rentfleet.safety.ppe_requirement | Rental PPE requirement | variant | Requirement communicates protective equipment needed for equipment use. | safety context |
| rentfleet.safety.prohibited_use | Prohibited rental use | invariant | Prohibition defines unsafe, illegal, overloaded, untrained or out-of-scope operation. | boundaries |
| rentfleet.metrics.fleet_utilization | Fleet utilization KPI | variant | KPI measures rental days, revenue, downtime, turn time, repair cost and availability. | manage fleet economics |
| rentfleet.continuity.substitution | Equipment substitution | variant | Substitution offers equivalent item when reserved unit is unavailable. | save the job |
