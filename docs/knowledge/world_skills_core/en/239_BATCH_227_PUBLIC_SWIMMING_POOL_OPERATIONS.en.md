# BATCH_227 — Public Swimming Pool Operations Detail
# world_skills_core · source: world_skills_core:batch_227:public_swimming_pool_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| poolops.admit.admission_check | Pool admission check | invariant | Check verifies ticket, pass, age rule, capacity, waiver and facility status before entry. | control access |
| poolops.admit.wristband | Pool wristband | variant | Wristband shows paid entry, swim level, session, group or age category. | visible entitlement |
| poolops.admit.capacity_count | Pool capacity count | invariant | Count tracks bathers, spectators, staff and occupancy limits. | avoid overcrowding |
| poolops.admit.swim_test | Swim test workflow | variant | Workflow evaluates swimmer ability for deep water, slide or program access under local rules. | match risk |
| poolops.admit.rule_briefing | Pool rule briefing | invariant | Briefing communicates running, diving, food, supervision, toys, hygiene and emergency rules. | set behavior |
| poolops.lifeguard.zone_assignment | Lifeguard zone assignment | invariant | Assignment maps guard to water zone, blind spots, equipment and rotation time. | active surveillance |
| poolops.lifeguard.scanning_pattern | Lifeguard scanning pattern | invariant | Pattern keeps eyes moving over surface, bottom, edges and high-risk users. | detect trouble |
| poolops.lifeguard.rotation | Lifeguard rotation | invariant | Rotation changes positions and breaks to maintain attention and coverage. | reduce fatigue |
| poolops.lifeguard.whistle_signal | Pool whistle signal | invariant | Signal communicates rule correction, attention, emergency or all-clear by code. | fast communication |
| poolops.lifeguard.rescue_equipment | Rescue equipment check | invariant | Check covers tube, backboard, reaching pole, ring, first aid and communication device. | ready response |
| poolops.water.chemical_test | Pool chemical test | invariant | Test records disinfectant, pH and other required water readings by schedule. | water safety evidence |
| poolops.water.test_log | Pool water test log | invariant | Log captures time, result, staff, corrective action and reopening decision. | audit trail |
| poolops.water.fecal_incident | Pool contamination incident | invariant | Incident triggers closure, treatment, cleaning, documentation and communication per protocol. | protect swimmers |
| poolops.water.turbidity_check | Pool clarity check | invariant | Check confirms bottom visibility and safe observation conditions. | see swimmers |
| poolops.water.mechanical_room | Pool mechanical room check | invariant | Check observes pumps, filters, valves, feeders, alarms, leaks and access restrictions. | keep system running |
| poolops.program.swim_lesson_roster | Swim lesson roster | invariant | Roster lists participants, level, instructor, guardian contact, attendance and skill notes. | organize lessons |
| poolops.program.lane_assignment | Pool lane assignment | variant | Assignment allocates lanes for lap swim, lessons, teams, therapy or public use. | share water |
| poolops.program.pool_party | Pool party booking | variant | Booking coordinates capacity, room, lifeguards, food rules, timing and cleanup. | event control |
| poolops.program.aquatics_class | Aquatics class setup | variant | Setup prepares instructor, equipment, lane, music, attendance and safety plan. | run class |
| poolops.program.weather_program_change | Weather program change | variant | Change cancels, delays or relocates outdoor pool activity due to lightning, heat or air quality. | environment response |
| poolops.facility.deck_inspection | Pool deck inspection | invariant | Inspection checks wet surfaces, drains, ladders, rails, furniture and trip hazards. | prevent injury |
| poolops.facility.locker_room_check | Pool locker room check | invariant | Check covers cleanliness, showers, toilets, floors, lockers, privacy and supplies. | user hygiene |
| poolops.facility.gate_fence | Pool gate and fence check | invariant | Check confirms barriers, latches, signs and unauthorized access controls. | prevent unsupervised entry |
| poolops.facility.slide_check | Pool slide check | variant | Check covers height rule, water flow, landing zone, stairs and attendant position. | attraction safety |
| poolops.facility.diving_board_check | Diving board check | variant | Check covers surface, fulcrum, rails, depth, rules and restricted use. | high-risk feature |
| poolops.safety.incident_report | Pool incident report | invariant | Report documents rescue, injury, rule violation, contamination, missing child or conflict. | formal record |
| poolops.safety.first_aid_response | Pool first aid response | invariant | Response records assessment, care within role, EMS call, guardian notice and follow-up. | emergency evidence |
| poolops.safety.missing_child | Missing child protocol | invariant | Protocol locks down exits, alerts staff, searches water first and documents timeline. | seconds matter |
| poolops.safety.thunder_closure | Thunder or lightning closure | invariant | Closure clears water and deck according to weather policy before reopening. | avoid strike risk |
| poolops.safety.guard_debrief | Lifeguard incident debrief | variant | Debrief reviews rescue, communication, equipment, documentation and improvement actions. | learn quickly |
| poolops.cleaning.deck_cleaning | Pool deck cleaning | invariant | Cleaning removes water, debris, sunscreen residue, food, glass hazards and algae. | safe surface |
| poolops.cleaning.restroom_sanitation | Pool restroom sanitation | invariant | Sanitation follows schedule for wet, high-traffic bathrooms and changing areas. | hygiene |
| poolops.cleaning.trash_round | Pool trash round | invariant | Round removes waste from deck, concessions, locker rooms and entrances. | cleanliness |
| poolops.cleaning.lost_found | Pool lost and found | invariant | Process tags, stores, claims and disposes towels, goggles, phones or clothing. | return property |
| poolops.cleaning.blood_cleanup | Pool blood cleanup | invariant | Cleanup isolates area, uses PPE, disinfects and documents exposure risk. | biohazard control |
| poolops.staff.opening_round | Pool opening round | invariant | Round checks water, guards, equipment, gates, deck, locker rooms and admissions. | open safely |
| poolops.staff.closing_round | Pool closing round | invariant | Round clears patrons, secures chemicals, locks gates, checks water and records issues. | end safely |
| poolops.staff.certification_record | Lifeguard certification record | invariant | Record tracks lifeguard credentials, expiry, in-service training and skills checks. | qualified coverage |
| poolops.staff.inservice_training | Pool in-service training | invariant | Training practices scanning, rescue, CPR/AED, spinal response, communication and scenarios. | readiness |
| poolops.staff.staffing_shortage | Pool staffing shortage | invariant | Shortage reduces capacity, closes feature, cancels session or triggers replacement staff. | no guard, no swim |
| poolops.billing.pass_sale | Pool pass sale | variant | Sale records day pass, season pass, resident rate, discount or refund rule. | revenue control |
| poolops.metrics.pool_kpi | Pool operations KPI | variant | KPI tracks attendance, incidents, water closures, guard coverage, complaints and maintenance issues. | manage pool |
| poolops.continuity.pump_failure | Pool pump failure response | invariant | Response closes affected water, notifies maintenance, protects equipment and documents reopening criteria. | system outage |
| poolops.continuity.chemical_alarm | Pool chemical alarm response | invariant | Response isolates chemical area, protects staff, escalates and records corrective action. | hazardous materials |
