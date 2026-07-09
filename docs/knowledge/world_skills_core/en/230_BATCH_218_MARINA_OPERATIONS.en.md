# BATCH_218 — Marina Operations Detail
# world_skills_core · source: world_skills_core:batch_218:marina_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| marina.slip.slip_assignment | Marina slip assignment | invariant | Assignment links vessel, owner, slip, length, beam, draft, term and services. | dock space control |
| marina.slip.transient_slip | Transient slip booking | variant | Booking reserves short-term berth with arrival, departure, vessel size and contact. | visiting boats |
| marina.slip.waitlist | Marina slip waitlist | variant | Waitlist tracks requested size, services, priority, deposit and offer history. | manage demand |
| marina.slip.vessel_profile | Vessel profile | invariant | Profile stores registration, dimensions, insurance, owner, emergency contact and equipment. | know boat |
| marina.slip.move_request | Slip move request | variant | Request changes berth due to size, draft, service, maintenance or customer preference. | controlled relocation |
| marina.dock.dock_inspection | Dock inspection | invariant | Inspection checks decking, cleats, pilings, ladders, lighting, lines and trip hazards. | dock safety |
| marina.dock.line_check | Mooring line check | invariant | Check observes line condition, chafe, tension, fenders and storm readiness. | protect vessel |
| marina.dock.power_pedestal | Shore power pedestal check | invariant | Check verifies outlet condition, breaker, labeling, damage and safe use. | electrical safety |
| marina.dock.water_pedestal | Dock water pedestal check | variant | Check confirms hose bib, leaks, backflow device, freeze risk and labeling. | service reliability |
| marina.fuel.fuel_dock_queue | Fuel dock queue | invariant | Queue controls vessel approach, tie-up, service order and traffic. | safe fueling flow |
| marina.fuel.fuel_transfer | Marina fuel transfer | invariant | Transfer records fuel type, quantity, vessel, attendant, payment and spill watch. | accountable fuel |
| marina.fuel.spill_kit | Marina spill kit | invariant | Kit includes absorbents, booms, PPE and disposal supplies near fueling area. | spill readiness |
| marina.fuel.nozzle_grounding | Fuel nozzle and bonding check | variant | Check reduces static or unsafe fueling condition according to system design. | ignition risk control |
| marina.fuel.fuel_inventory | Marina fuel inventory | invariant | Inventory tracks tank level, deliveries, sales, water checks and variances. | fuel control |
| marina.pumpout.pumpout_booking | Pump-out booking | variant | Booking schedules waste pump-out by vessel, slip, time and service type. | sanitation service |
| marina.pumpout.hose_sanitation | Pump-out hose sanitation | invariant | Sanitation controls hose storage, rinsing, spills, odor and cross-contact. | hygiene |
| marina.pumpout.waste_log | Pump-out waste log | invariant | Log records vessel, volume estimate, date, staff and disposal route where required. | environmental record |
| marina.pumpout.pump_fault | Pump-out equipment fault | invariant | Fault records suction loss, clog, leak, odor, alarm or service outage. | fix quickly |
| marina.pumpout.no_discharge_notice | No-discharge notice | variant | Notice informs boaters of local discharge restrictions and marina rules. | protect water |
| marina.maintenance.work_order | Marina maintenance work order | invariant | Work order records dock, utility, building, vessel service or yard issue. | organize repairs |
| marina.maintenance.haulout_schedule | Haul-out schedule | variant | Schedule coordinates lift, staff, slings, tide, yard space and owner contact. | move boats safely |
| marina.maintenance.lift_inspection | Boat lift inspection | invariant | Inspection checks travel lift, straps, slings, hydraulics, alarms and rated capacity. | heavy lift safety |
| marina.maintenance.bottom_work | Bottom work coordination | variant | Coordination handles washing, blocking, sanding, painting and environmental controls. | yard workflow |
| marina.maintenance.winterization | Marina winterization | variant | Winterization protects water lines, docks, boats, pumps and buildings from freezing season. | seasonal resilience |
| marina.weather.weather_monitor | Marina weather monitor | invariant | Monitor tracks wind, storm, lightning, tide, current, freeze and flood alerts. | conditions drive safety |
| marina.weather.storm_prep | Marina storm preparation | invariant | Prep secures docks, lines, loose items, fuel, power, lifts and customer notices. | reduce storm damage |
| marina.weather.high_water_response | High water response | variant | Response adjusts ramps, utilities, access, dock lines and safety barriers. | flood readiness |
| marina.weather.lightning_hold | Lightning hold | invariant | Hold stops fueling, dock work, lifts or exposed activity during lightning risk. | immediate safety |
| marina.weather.post_storm_survey | Post-storm survey | invariant | Survey checks vessels, docks, utilities, debris, spills and access before reopening. | recover safely |
| marina.customer.checkin | Marina customer check-in | invariant | Check-in verifies reservation, vessel, payment, rules, access credentials and emergency contacts. | welcome and control |
| marina.customer.access_credential | Marina access credential | invariant | Credential controls gates, docks, showers, parking, laundry or fuel account access. | member access |
| marina.customer.rule_ack | Marina rule acknowledgment | invariant | Acknowledgment covers speed, noise, pets, fueling, waste, guests, liveaboard and safety rules. | shared harbor norms |
| marina.customer.service_request | Marina customer service request | invariant | Request captures slip issue, utility fault, pump-out, dock help, package or complaint. | front desk workflow |
| marina.customer.guest_parking | Marina guest parking | variant | Parking controls guest permits, towing rules, time limits and event overflow. | site management |
| marina.safety.life_ring_check | Life ring check | invariant | Check verifies life rings, ladders, throw lines and emergency equipment are visible and intact. | water rescue readiness |
| marina.safety.fire_extinguisher | Marina fire extinguisher check | invariant | Check confirms location, charge, inspection date and access near docks and fuel. | fire response |
| marina.safety.electrical_hazard | Dock electrical hazard | invariant | Hazard report flags damaged cords, submerged power, tripped breakers or unsafe adapters. | shock prevention |
| marina.safety.slip_fall_hazard | Marina slip and fall hazard | invariant | Hazard includes wet dock, algae, ice, loose boards, hoses or poor lighting. | prevent injuries |
| marina.safety.incident_report | Marina incident report | invariant | Report documents injury, vessel damage, spill, fire, theft, near miss or rule violation. | formal record |
| marina.billing.slip_invoice | Marina slip invoice | invariant | Invoice charges slip, utilities, services, storage, fuel, fees and taxes. | bill marina use |
| marina.billing.utility_meter | Marina utility meter | variant | Meter tracks electricity or water use for slip billing or monitoring. | fair allocation |
| marina.billing.delinquency | Marina delinquency process | invariant | Process sends notices, restricts services, tracks payment plan and legal path. | manage arrears |
| marina.metrics.marina_kpi | Marina operations KPI | variant | KPI tracks occupancy, fuel sales, incidents, maintenance tickets, delinquencies and customer issues. | manage marina |
| marina.continuity.fuel_dock_outage | Fuel dock outage plan | invariant | Plan notifies boaters, secures equipment, reroutes fueling and schedules repair. | maintain service |
