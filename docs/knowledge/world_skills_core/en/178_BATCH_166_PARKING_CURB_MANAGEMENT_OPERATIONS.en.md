# BATCH_166 — Parking & Curb Management Operations Detail
# world_skills_core · source: world_skills_core:batch_166:parking_curb_management_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| curbops.inventory.curb_inventory | Curb inventory | invariant | Curb inventory records spaces, zones, signs, meters, loading areas, restrictions and geometry. | know the curb asset |
| curbops.inventory.parking_space | Parking space record | invariant | Space record links location, type, length, restrictions, meter ID and enforcement rules. | one stall, one rule set |
| curbops.inventory.sign_code | Parking sign code | invariant | Sign code translates posted regulation into enforceable time, vehicle, permit, price or loading condition. | sign becomes data |
| curbops.inventory.loading_zone | Loading zone | invariant | Loading zone allocates curb space for goods, service vehicles or short commercial activity. | deliveries need curb |
| curbops.inventory.accessible_space | Accessible parking space | invariant | Accessible space provides regulated access features, location and enforcement protection. | equity in curb design |
| curbops.inventory.fire_lane | Fire lane | invariant | Fire lane restriction protects emergency access and has high-priority enforcement. | safety over convenience |
| curbops.permit.residential_permit | Residential parking permit | variant | Residential permit gives eligible residents parking rights within defined area and conditions. | local access control |
| curbops.permit.commercial_permit | Commercial vehicle permit | variant | Commercial permit authorizes specific business parking, loading or service activity under defined limits. | work vehicles managed |
| curbops.permit.visitor_permit | Visitor permit | variant | Visitor permit provides temporary local parking permission with time, address or quota controls. | guest access |
| curbops.permit.permit_fraud_check | Permit fraud check | invariant | Fraud check looks for copied, expired, misused, sold or ineligible permits. | protect scarce space |
| curbops.permit.digital_permit | Digital parking permit | variant | Digital permit links vehicle plate or account to authorization without physical decal. | enforcement by data |
| curbops.permit.permit_waitlist | Permit waitlist | variant | Waitlist controls demand when permits exceed available curb or garage capacity. | ration scarce permits |
| curbops.pricing.meter_rate | Meter rate | invariant | Meter rate sets price by zone, time, vehicle type or policy objective. | price shapes demand |
| curbops.pricing.dynamic_pricing | Dynamic parking pricing | variant | Dynamic pricing adjusts rates based on occupancy, time, event or demand targets. | manage availability |
| curbops.pricing.occupancy_target | Parking occupancy target | invariant | Occupancy target defines desired use level so drivers can usually find a space. | not always 100 percent full |
| curbops.pricing.payment_session | Parking payment session | invariant | Payment session links plate, zone, start, paid duration, amount and expiration. | proof of payment |
| curbops.pricing.grace_period | Parking grace period | variant | Grace period allows small timing tolerance before or after paid session under policy. | reduce unfair citations |
| curbops.pricing.rate_table_update | Rate table update | invariant | Rate update synchronizes meters, apps, signs, enforcement devices and public information. | avoid conflicting prices |
| curbops.enforcement.plate_scan | License plate scan | invariant | Plate scan checks observed vehicle against payment, permit, stolen, boot or citation data. | enforcement input |
| curbops.enforcement.citation | Parking citation | invariant | Citation records violation, evidence, location, time, officer, plate and legal basis. | formal penalty |
| curbops.enforcement.photo_evidence | Parking photo evidence | invariant | Photo evidence documents vehicle, sign, curb, meter or violation context for review. | dispute-proofing |
| curbops.enforcement.chalk_mark | Tire chalking | variant | Chalking marks or digitally records vehicle presence to enforce time limits where allowed. | time-limit evidence |
| curbops.enforcement.scofflaw | Scofflaw vehicle | variant | Scofflaw status identifies vehicle with repeated unpaid citations that may trigger immobilization or tow. | chronic nonpayment |
| curbops.enforcement.tow_authorization | Tow authorization | invariant | Tow authorization requires qualifying violation, evidence, notification rules and safe vehicle removal. | severe enforcement |
| curbops.appeals.appeal_intake | Citation appeal intake | invariant | Appeal intake records contest reason, evidence, deadlines, citation and appellant identity. | due process path |
| curbops.appeals.hearing_review | Parking hearing review | invariant | Review evaluates citation evidence, ordinance, signage, payment data and appellant claim. | independent judgment |
| curbops.appeals.dismissal_reason | Dismissal reason | invariant | Dismissal reason classifies why citation is cancelled, such as error, unclear sign, valid permit or emergency. | learn from mistakes |
| curbops.appeals.payment_plan | Citation payment plan | variant | Payment plan spreads fines over time for eligible debt while tracking compliance. | collection with flexibility |
| curbops.appeals.refund_process | Parking refund process | variant | Refund process returns overpayment or invalid charge with approval and audit trail. | money correction |
| curbops.occupancy.sensor | Parking occupancy sensor | variant | Sensor estimates space occupancy using in-ground, camera, meter or mobile data. | real-time availability |
| curbops.occupancy.manual_survey | Manual occupancy survey | invariant | Survey counts occupied and available spaces at defined times and locations. | ground truth |
| curbops.occupancy.turnover | Parking turnover | invariant | Turnover measures how many different vehicles use a space over time. | short stay versus storage |
| curbops.occupancy.cruising | Cruising for parking | variant | Cruising occurs when drivers circle searching for parking and adds traffic, emissions and delay. | hidden congestion |
| curbops.occupancy.event_parking | Event parking plan | variant | Event plan adjusts pricing, staffing, signage, transit coordination and enforcement around large demand spikes. | temporary peak |
| curbops.curb.ridehail_pickup | Ridehail pickup zone | variant | Pickup zone organizes curb access for ridehail vehicles to reduce double parking and passenger confusion. | curb for apps |
| curbops.curb.micro_mobility_parking | Micromobility parking area | variant | Micromobility parking area manages scooters or bikes to protect sidewalks and access. | small vehicles need rules |
| curbops.curb.bus_stop_clearance | Bus stop clearance | invariant | Clearance around bus stop ensures transit access, safe boarding and schedule reliability. | curb supports transit |
| curbops.curb.delivery_window | Curb delivery window | variant | Delivery window reserves curb for loading during specific periods and allows other use later. | time-sharing curb |
| curbops.curb.temporary_no_parking | Temporary no-parking order | variant | Temporary order reserves curb for construction, moving, events, utilities or emergency work. | curb can change |
| curbops.operations.meter_fault | Meter fault | invariant | Meter fault affects payment, citation validity, repair dispatch and customer communication. | broken device risk |
| curbops.operations.sign_maintenance | Parking sign maintenance | invariant | Sign maintenance keeps regulations visible, accurate, legally enforceable and aligned with data systems. | sign is law interface |
| curbops.operations.cash_collection | Meter cash collection | variant | Cash collection controls route, canister, count, deposit, variance and staff security. | physical money remains |
| curbops.operations.enforcement_beat | Enforcement beat | invariant | Beat assigns officer area, timing, priority violations and expected coverage. | patrol design |
| curbops.operations.policy_evaluation | Curb policy evaluation | invariant | Evaluation compares occupancy, turnover, citations, revenue, complaints and equity impacts against policy goals. | manage curb deliberately |
