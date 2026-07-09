# BATCH_233 — Campground Operations Detail
# world_skills_core · source: world_skills_core:batch_233:campground_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| campops.reservation.site_inventory | Campground site inventory | invariant | Inventory tracks tent, RV, cabin, group, accessible and closed sites. | sell capacity |
| campops.reservation.booking_record | Campground booking record | invariant | Record links guest, dates, site, equipment, vehicle, occupants, fees and rules. | reservation source |
| campops.reservation.deposit_policy | Campground deposit policy | invariant | Policy defines deposit, cancellation, refund, no-show and modification terms. | reduce disputes |
| campops.reservation.seasonal_hold | Seasonal campsite hold | variant | Hold reserves recurring sites with contract, payment schedule and occupancy limits. | long-stay control |
| campops.reservation.overbooking_check | Campground overbooking check | invariant | Check prevents duplicate site sale across channels, maps and manual holds. | avoid conflict |
| campops.checkin.arrival_packet | Campground arrival packet | invariant | Packet provides map, rules, permits, tags, emergency contacts and amenities. | orient guest |
| campops.checkin.identity_vehicle | Campground identity and vehicle check | invariant | Check verifies reservation, vehicle plates, extra cars and registered occupants. | access control |
| campops.checkin.site_assignment | Campground site assignment | invariant | Assignment matches equipment length, hookups, accessibility, pets and guest preferences. | right site |
| campops.checkin.late_arrival | Campground late arrival | variant | Process provides gate code, map, quiet setup rule and next-day verification. | after-hours service |
| campops.checkin.walkup_booking | Campground walk-up booking | variant | Booking assigns unsold site, collects payment, records guest and explains rules. | fill capacity |
| campops.utilities.electric_hookup | Campsite electric hookup | variant | Hookup record notes amperage, pedestal status, guest connection and fault reports. | reliable power |
| campops.utilities.water_hookup | Campsite water hookup | variant | Hookup checks spigot, hose rules, backflow protection and leak reporting. | water safety |
| campops.utilities.sewer_connection | Campsite sewer connection | variant | Connection governs hose seal, slope, cap, spill response and closure. | sanitation |
| campops.utilities.dump_station | Campground dump station | invariant | Station operation manages queue, rinse water, signage, spill kit and cleaning. | waste control |
| campops.utilities.utility_outage | Campground utility outage | invariant | Outage record tracks affected sites, cause, guest communication and restoration. | continuity |
| campops.sanitation.restroom_round | Campground restroom round | invariant | Round checks toilets, showers, supplies, drains, odors, lighting and damage. | guest hygiene |
| campops.sanitation.trash_collection | Campground trash collection | invariant | Collection schedules dumpsters, bear-proof bins, litter routes and overflow response. | clean grounds |
| campops.sanitation.potable_water_test | Campground potable water test | invariant | Test records sample point, date, result, notice and corrective action. | safe water |
| campops.sanitation.pest_watch | Campground pest watch | variant | Watch tracks insects, rodents, wildlife attractants, complaints and treatment route. | health and comfort |
| campops.sanitation.graywater_policy | Campground graywater policy | invariant | Policy prohibits unsafe discharge and routes graywater to approved disposal. | site protection |
| campops.quiet.quiet_hours | Campground quiet hours | invariant | Rule defines start, end, noise expectations, warnings and enforcement. | guest rest |
| campops.quiet.generator_hours | Campground generator hours | variant | Rule defines permitted times, distance, exhaust direction and exceptions. | noise and safety |
| campops.quiet.group_noise | Campground group noise response | invariant | Response records complaint, warning, leader contact, escalation and eviction if needed. | fair enforcement |
| campops.quiet.pet_control | Campground pet control | invariant | Control covers leash, waste, barking, restricted areas and incident response. | reduce conflict |
| campops.safety.fire_ring_check | Campground fire ring check | invariant | Check verifies permitted location, ash condition, clearance, bans and extinguishing. | fire safety |
| campops.safety.burn_ban | Campground burn ban | invariant | Ban communication posts rules, notifies guests, restricts fuels and logs enforcement. | prevent wildfire |
| campops.safety.wildlife_encounter | Campground wildlife encounter | variant | Encounter record captures species, attractant, guest action, staff response and notices. | reduce risk |
| campops.safety.first_aid | Campground first aid report | invariant | Report records injury, care, witnesses, EMS if needed and follow-up. | care evidence |
| campops.safety.weather_alert | Campground weather alert | invariant | Alert communicates storm, flood, heat, wind or smoke instructions to guests. | timely warning |
| campops.maintenance.site_turnover | Campsite turnover | invariant | Turnover checks trash, fire pit, picnic table, hookups, hazards and signage. | ready next stay |
| campops.maintenance.road_condition | Campground road condition | variant | Condition log tracks potholes, washouts, dust, snow, drainage and grading needs. | access safety |
| campops.maintenance.tree_hazard | Campground tree hazard | invariant | Hazard record identifies dead limbs, lean, root issues, closure and arborist action. | prevent injury |
| campops.maintenance.facility_workorder | Campground facility work order | invariant | Work order covers restroom, cabin, gate, lighting, dock, trail or utility repair. | maintenance tracking |
| campops.maintenance.signage_check | Campground signage check | invariant | Check verifies site numbers, rules, exits, hazards, maps and emergency signs. | wayfinding |
| campops.incident.rule_violation | Campground rule violation | invariant | Violation records rule, guest, warning, fee, eviction or law enforcement involvement. | enforce rules |
| campops.incident.property_damage | Campground property damage | invariant | Damage record links site, asset, guest, photo, cost and recovery action. | protect assets |
| campops.incident.missing_person | Campground missing person response | invariant | Response assigns search zones, contacts, last seen, authorities and resolution log. | rapid response |
| campops.incident.neighbor_conflict | Campsite neighbor conflict | variant | Conflict record captures noise, boundaries, pets, smoke or behavior and mediation. | restore calm |
| campops.store.camp_store_sale | Camp store sale | variant | Sale records firewood, ice, supplies, rentals, tax and receipt. | guest convenience |
| campops.store.firewood_control | Campground firewood control | invariant | Control tracks source, pest restrictions, bundles, storage and sales. | protect forest |
| campops.checkout.checkout_check | Campground checkout check | invariant | Check confirms departure, site condition, keys, permits, refunds and next turnover. | close stay |
| campops.reporting.occupancy_report | Campground occupancy report | invariant | Report summarizes site nights, revenue, no-shows, extensions, cancellations and closures. | manage capacity |
| campops.metrics.campground_kpi | Campground KPI | variant | KPI tracks occupancy, revenue, incidents, maintenance backlog, complaints and sanitation scores. | manage campground |
| campops.continuity.evacuate_campground | Campground evacuation | invariant | Evacuation coordinates notice, routes, roll call, gates, authorities and reentry. | emergency control |
