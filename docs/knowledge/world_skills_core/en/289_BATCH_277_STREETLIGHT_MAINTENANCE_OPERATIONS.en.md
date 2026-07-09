# BATCH_277 — Streetlight Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_277:streetlight_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| streetlightops.inventory.light_asset_record | Streetlight asset record | invariant | Record stores pole ID, fixture, lamp type, wattage, circuit, location, owner and status. | manage asset |
| streetlightops.inventory.pole_record | Streetlight pole record | invariant | Record captures pole material, height, foundation, arm, attachments, condition and ownership. | maintain pole |
| streetlightops.inventory.circuit_map | Streetlight circuit map | invariant | Map links lights to feeds, panels, breakers, photocells, cabinets and service points. | diagnose outages |
| streetlightops.inventory.led_conversion_status | LED conversion status | variant | Status records legacy fixture, LED retrofit, color temperature, driver, date and warranty. | track upgrades |
| streetlightops.inspection.night_patrol | Streetlight night patrol | invariant | Patrol identifies dark lights, cycling lamps, dim output, glare, blocked fixtures and unsafe areas. | find outages |
| streetlightops.inspection.daytime_visual_check | Daytime streetlight visual check | variant | Check reviews pole damage, open handholes, leaning poles, broken lenses and wiring exposure. | spot hazards |
| streetlightops.inspection.post_storm_patrol | Post-storm light patrol | variant | Patrol checks knocked-down poles, wires, flooded bases, dark circuits and damaged fixtures. | restore safety |
| streetlightops.outage.single_light_outage | Single streetlight outage | invariant | Outage affects one fixture because of lamp, driver, fuse, photocell, wiring or fixture failure. | repair light |
| streetlightops.outage.multiple_light_outage | Multiple streetlight outage | invariant | Outage affects several lights because of circuit, breaker, cable, control or utility supply problem. | find feeder |
| streetlightops.outage.intermittent_outage | Intermittent streetlight outage | variant | Outage appears cycling, flickering or weather-dependent due to failing component or connection. | diagnose pattern |
| streetlightops.outage.dayburner | Streetlight dayburner | invariant | Dayburner remains on during daylight because of photocell, control, wiring or communication fault. | reduce waste |
| streetlightops.outage.dim_light | Dim streetlight condition | variant | Condition includes lumen depreciation, dirty lens, wrong driver, voltage drop or obstruction. | improve visibility |
| streetlightops.electrical.photocell_fault | Streetlight photocell fault | invariant | Fault causes dayburner, night outage, cycling or wrong switching time. | fix control |
| streetlightops.electrical.driver_failure | LED driver failure | invariant | Failure interrupts LED fixture power regulation and may cause outage, flicker or dimming. | replace driver |
| streetlightops.electrical.cable_fault | Streetlight cable fault | invariant | Fault includes open conductor, short, ground fault, water intrusion or damaged underground cable. | restore circuit |
| streetlightops.electrical.breaker_trip | Streetlight breaker trip | invariant | Trip indicates overload, short, ground fault, moisture, damaged equipment or coordination issue. | protect circuit |
| streetlightops.repairs.fixture_replacement | Streetlight fixture replacement | invariant | Replacement matches fixture type, mounting, optical distribution, wattage, controls and documentation. | restore lighting |
| streetlightops.repairs.fuse_replacement | Streetlight fuse replacement | variant | Replacement corrects localized protection failure after checking for fault cause. | restore feed |
| streetlightops.repairs.pole_straightening | Streetlight pole straightening | variant | Repair corrects leaning pole if foundation, structure and attachments are acceptable. | remove hazard |
| streetlightops.repairs.knockdown_repair | Streetlight knockdown repair | invariant | Repair handles crash-damaged pole, exposed wiring, temporary safety, replacement and billing evidence. | emergency repair |
| streetlightops.controls.smart_node | Streetlight smart node | variant | Node provides remote switching, dimming, outage reporting, metering or sensor communication. | manage remotely |
| streetlightops.controls.dimming_schedule | Streetlight dimming schedule | variant | Schedule sets output by time, location, safety need, energy policy and special events. | save energy |
| streetlightops.controls.group_control_fault | Group control fault | invariant | Fault affects multiple lights because controller, relay, communication or schedule fails. | restore group |
| streetlightops.reporting.public_outage_report | Public streetlight outage report | invariant | Report records caller, pole number, location, symptom, safety issue and photos if available. | citizen input |
| streetlightops.reporting.outage_ticket | Streetlight outage ticket | invariant | Ticket tracks diagnosis, crew assignment, parts, owner, completion, repeat status and closure. | trace repair |
| streetlightops.reporting.night_patrol_report | Night patrol report | variant | Report lists observed outages, inaccessible assets, hazards, route covered and follow-up work. | plan crews |
| streetlightops.safety.electrical_safety | Streetlight electrical safety | invariant | Safety covers de-energizing, testing, PPE, grounding, exposed conductors and wet conditions. | protect crew |
| streetlightops.safety.aerial_lift_safety | Streetlight aerial lift safety | invariant | Safety covers lift setup, traffic control, overhead wires, fall protection and weather limits. | safe access |
| streetlightops.safety.open_handhole | Open streetlight handhole hazard | invariant | Hazard exposes wiring or creates pedestrian risk at pole base and requires immediate control. | prevent injury |
| streetlightops.coordination.utility_owner | Streetlight utility owner coordination | invariant | Coordination handles utility-owned poles, service feeds, metering, outages and repair responsibility. | clarify handoff |
| streetlightops.coordination.police_safety_priority | Police safety priority lighting | variant | Priority flags outages affecting crash sites, crime concerns, crossings or emergency response routes. | rank work |
| streetlightops.coordination.tree_obstruction | Tree obstruction coordination | variant | Coordination removes branches blocking light while considering tree health, clearance and permits. | restore illumination |
| streetlightops.led.color_temperature_record | Streetlight color temperature record | variant | Record documents LED color, glare concerns, neighborhood standard and fixture specification. | manage comfort |
| streetlightops.led.glare_complaint | Streetlight glare complaint | variant | Complaint records excessive brightness, spill light, window impact or shielding need. | adjust fixture |
| streetlightops.led.warranty_claim | Streetlight LED warranty claim | invariant | Claim records fixture model, failure mode, install date, serial number and replacement request. | recover cost |
| streetlightops.stock.parts_inventory | Streetlight parts inventory | invariant | Inventory tracks fixtures, drivers, photocells, fuses, handhole covers, wire and poles. | repair readiness |
| streetlightops.stock.standard_fixture | Standard streetlight fixture | variant | Standard defines approved models, optics, wattage, color, controls and mounting hardware. | consistency |
| streetlightops.metrics.outage_response_time | Streetlight outage response time KPI | invariant | KPI measures time from report or patrol finding to repair completion. | improve service |
| streetlightops.metrics.dayburner_rate | Streetlight dayburner rate KPI | variant | KPI tracks lights incorrectly on during day by area, fixture type and cause. | energy savings |
| streetlightops.metrics.led_conversion_progress | LED conversion progress KPI | variant | KPI tracks converted assets, energy reduction, remaining legacy lights and warranty issues. | manage program |
| streetlightops.data.asset_update | Streetlight asset update | invariant | Update records repaired component, new fixture, circuit change, pole status and photos. | keep data current |
| streetlightops.data.location_correction | Streetlight location correction | variant | Correction fixes pole coordinates, address reference, circuit link or map placement after field verification. | improve map |
| streetlightops.continuity.temporary_lighting | Temporary street lighting | variant | Temporary lighting supports outages, construction, events or safety zones until permanent repair. | maintain visibility |
| streetlightops.close.repair_closeout | Streetlight repair closeout | invariant | Closeout confirms light operation at night or test mode, ticket update and material use. | finish repair |
