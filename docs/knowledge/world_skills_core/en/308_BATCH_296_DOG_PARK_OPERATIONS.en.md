# BATCH_296 — Dog Park Operations Detail
# world_skills_core · source: world_skills_core:batch_296:dog_park_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| dogparkops.inventory.dog_park_record | Dog park record | invariant | Record stores location, size, zones, gates, surfacing, water, amenities and maintenance history. | manage facility |
| dogparkops.inventory.small_dog_area | Small dog area | variant | Area separates smaller dogs by weight, size, age or behavior policy. | reduce conflict |
| dogparkops.inventory.double_gate | Dog park double-gate entry | invariant | Entry uses two gates to reduce escape risk during arrivals and exits. | control access |
| dogparkops.inventory.waste_station | Dog park waste station | invariant | Station includes bag dispenser, bin, signage, service frequency and stock status. | manage waste |
| dogparkops.gates.gate_latch_check | Dog park gate latch check | invariant | Check ensures gate closes, latches, aligns, swings safely and resists dog escape. | prevent escapes |
| dogparkops.gates.fence_condition | Dog park fence condition | invariant | Condition checks height, gaps, holes, leaning posts, sharp edges and undermining. | secure perimeter |
| dogparkops.gates.accessibility_gate | Dog park accessible gate | variant | Gate supports usable width, hardware reach, surface and maneuvering clearance. | inclusive access |
| dogparkops.surfacing.turf_condition | Dog park turf condition | variant | Condition includes bare spots, mud, compaction, urine burn, drainage and overuse. | maintain surface |
| dogparkops.surfacing.gravel_surface | Dog park gravel surface | variant | Surface needs grading, replenishment, dust control, drainage and debris removal. | keep usable |
| dogparkops.surfacing.mud_control | Dog park mud control | invariant | Control uses drainage, rest periods, surface repair, mulch, gravel or temporary closure. | reduce mess |
| dogparkops.surfacing.hole_repair | Dog park hole repair | invariant | Repair fills dog-dug holes and settles surface to prevent trips and injury. | remove hazard |
| dogparkops.water.drinking_fountain | Dog park drinking fountain | invariant | Fountain serves dogs and handlers and requires cleaning, drainage, leaks and seasonal control. | provide water |
| dogparkops.water.bowl_station | Dog park bowl station | variant | Station manages shared bowls, cleaning, storage, contamination and theft risk. | support hydration |
| dogparkops.water.winter_shutoff | Dog park water winter shutoff | variant | Shutoff prevents freeze damage and requires public notice or alternate water plan. | protect plumbing |
| dogparkops.cleaning.waste_pickup | Dog park waste pickup | invariant | Pickup removes feces, bagged waste, litter and overflowing bins from park areas. | hygiene |
| dogparkops.cleaning.disinfection_need | Dog park disinfection need | variant | Need arises after disease concern, contamination, high use, vomit, blood or outbreak notice. | protect health |
| dogparkops.cleaning.odor_control | Dog park odor control | invariant | Control manages urine concentration, waste bins, drainage, ventilation and cleaning frequency. | improve comfort |
| dogparkops.rules.rule_signage | Dog park rule signage | invariant | Signage states leash, vaccination, waste, supervision, aggressive dog and hours rules. | set behavior |
| dogparkops.rules.license_requirement | Dog park license requirement | variant | Requirement may link access to dog license, registration, permit or proof of vaccination. | manage eligibility |
| dogparkops.rules.closure_rule | Dog park closure rule | invariant | Rule defines closure for maintenance, weather, disease, unsafe conditions or overcrowding. | manage risk |
| dogparkops.incidents.dog_bite_incident | Dog bite incident | invariant | Incident records parties, dog details, injury, location, witnesses, animal control referral and follow-up. | respond safely |
| dogparkops.incidents.aggressive_dog_report | Aggressive dog report | variant | Report captures behavior, repeat concerns, owner response, witness and enforcement path. | reduce conflict |
| dogparkops.incidents.escape_incident | Dog escape incident | invariant | Incident records gate, fence, handler, direction, outcome and corrective action. | improve containment |
| dogparkops.incidents.user_conflict | Dog park user conflict | variant | Conflict involves disputes about behavior, rules, waste, gates, children or park etiquette. | manage community |
| dogparkops.repairs.fence_repair | Dog park fence repair | invariant | Repair fixes holes, loose fabric, posts, rails, gates, hinges or sharp edges. | restore containment |
| dogparkops.repairs.bench_shade_repair | Dog park bench and shade repair | variant | Repair addresses seating, shade structures, umbrellas, anchors, splinters and stability. | restore amenities |
| dogparkops.repairs.irrigation_repair | Dog park irrigation repair | variant | Repair handles broken heads, leaks, overspray, timers and turf watering needs. | support surface |
| dogparkops.safety.heat_risk | Dog park heat risk | invariant | Risk includes hot surfacing, limited shade, dehydration, high temperature and vulnerable dogs. | prevent harm |
| dogparkops.safety.surface_hazard | Dog park surface hazard | invariant | Hazard includes holes, glass, sharp objects, exposed roots, ice, mud or broken edging. | prevent injury |
| dogparkops.safety.disease_notice | Dog park disease notice | variant | Notice communicates outbreak concern, cleaning action, closure or animal health guidance. | inform users |
| dogparkops.complaints.waste_complaint | Dog park waste complaint | invariant | Complaint reports uncollected feces, overflowing bins, missing bags or odor. | dispatch cleaning |
| dogparkops.complaints.noise_complaint | Dog park noise complaint | variant | Complaint concerns barking, early use, crowd behavior or nearby residential impact. | manage nuisance |
| dogparkops.complaints.maintenance_complaint | Dog park maintenance complaint | invariant | Complaint reports broken gate, fence gap, water issue, surface hazard or damaged amenity. | start work |
| dogparkops.records.daily_check_log | Dog park daily check log | invariant | Log records gates, surfacing, waste, water, incidents, cleaning, repairs and closures. | trace service |
| dogparkops.records.incident_record | Dog park incident record | invariant | Record stores injury, bite, escape, conflict, witness, referral and corrective action. | manage liability |
| dogparkops.records.closure_record | Dog park closure record | variant | Record explains closure reason, duration, notices, barriers, repairs and reopening check. | document outage |
| dogparkops.reporting.condition_report | Dog park condition report | invariant | Report summarizes gates, fencing, surfacing, waste, water, amenities, incidents and backlog. | manage park |
| dogparkops.reporting.use_pattern_report | Dog park use pattern report | variant | Report tracks peak times, crowding, zone use, complaints and maintenance demand. | plan capacity |
| dogparkops.metrics.waste_station_uptime | Dog park waste station uptime KPI | invariant | KPI measures stations stocked, usable and serviced on schedule. | monitor hygiene |
| dogparkops.metrics.incident_rate | Dog park incident rate KPI | variant | KPI tracks bites, escapes, conflicts and injuries by period and location. | target controls |
| dogparkops.coordination.animal_control | Dog park animal control coordination | invariant | Coordination handles bite reports, dangerous behavior, licensing, enforcement and public education. | manage incidents |
| dogparkops.coordination.volunteer_group | Dog park volunteer group coordination | variant | Coordination aligns cleanup, feedback, events, minor stewardship and reporting. | support park |
| dogparkops.continuity.emergency_closure | Dog park emergency closure | invariant | Closure handles unsafe fence, bite cluster, contamination, storm damage or severe surface hazard. | protect users |
| dogparkops.close.work_closeout | Dog park work closeout | invariant | Closeout confirms repair or cleaning, photos, signs, records and complaint response. | finish work |
