# BATCH_225 — Community Recreation Center Operations Detail
# world_skills_core · source: world_skills_core:batch_225:community_recreation_center_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| recctr.member.membership_registration | Recreation membership registration | invariant | Registration records member identity, household, plan, waivers, payment and access credential. | start membership |
| recctr.member.household_account | Recreation household account | invariant | Account links guardians, dependents, emergency contacts, programs and billing. | family management |
| recctr.member.waiver_status | Recreation waiver status | invariant | Status confirms required risk, photo, code-of-conduct or medical disclosure forms. | permission evidence |
| recctr.member.access_card | Recreation access card | variant | Card controls entry, check-in, membership status and facility permissions. | controlled access |
| recctr.member.offboarding | Recreation member offboarding | invariant | Offboarding cancels access, closes billing, refunds deposits and records reason. | clean exit |
| recctr.booking.facility_booking | Facility booking | invariant | Booking reserves room, court, field, pool lane, gym or studio with time and rules. | shared space |
| recctr.booking.permit_requirements | Recreation booking permit | variant | Permit sets insurance, capacity, alcohol, music, food or security conditions. | event control |
| recctr.booking.setup_layout | Recreation room setup | invariant | Setup defines tables, chairs, AV, sports gear, mats, signage and cleanup needs. | ready space |
| recctr.booking.no_show_release | Booking no-show release | variant | Release returns unused facility to inventory after grace period. | reduce wasted capacity |
| recctr.booking.cancellation_policy | Booking cancellation policy | invariant | Policy defines deadlines, refunds, weather, staffing and rescheduling. | manage expectations |
| recctr.program.program_registration | Program registration | invariant | Registration enrolls participant in class, camp, league, lesson or activity. | reserve seat |
| recctr.program.capacity_waitlist | Program capacity waitlist | variant | Waitlist tracks people seeking entry when program is full. | demand management |
| recctr.program.instructor_assignment | Instructor assignment | invariant | Assignment links instructor, credential, room, roster, supplies and schedule. | staff class |
| recctr.program.attendance_roster | Program attendance roster | invariant | Roster tracks participant attendance, late pickup, absence and emergency contacts. | safety and billing |
| recctr.program.program_evaluation | Program evaluation | variant | Evaluation captures satisfaction, outcomes, attendance, incidents and improvement ideas. | improve offering |
| recctr.aquatics.lifeguard_rotation | Lifeguard rotation | variant | Rotation assigns zones, breaks, scanning positions and relief timing. | maintain vigilance |
| recctr.aquatics.pool_test_log | Pool test log | variant | Log records water checks, time, staff, readings, corrective actions and closure status. | pool safety |
| recctr.aquatics.pool_capacity | Pool capacity control | invariant | Control limits swimmers by occupancy, staff, program and safety rules. | avoid overload |
| recctr.aquatics.swim_lesson_flow | Swim lesson flow | variant | Flow manages rosters, lane assignments, skill levels, instructor notes and guardian pickup. | orderly lessons |
| recctr.aquatics.pool_closure | Pool closure process | invariant | Closure handles contamination, weather, chemical issue, staffing gap or emergency. | stop unsafe use |
| recctr.fitness.equipment_check | Fitness equipment check | invariant | Check covers treadmills, weights, cables, mats, machines, cleanliness and damage. | safe workout |
| recctr.fitness.orientation | Fitness orientation | variant | Orientation teaches facility rules, equipment basics, cleaning and assistance path. | reduce misuse |
| recctr.fitness.group_class_checkin | Group class check-in | invariant | Check-in verifies booking, capacity, instructor, room and waiver. | class control |
| recctr.fitness.personal_training | Personal training session | variant | Session booking records trainer, client, time, goals, package and notes. | paid service |
| recctr.fitness.equipment_outage | Fitness equipment outage | invariant | Outage tags equipment, logs fault, informs users and schedules repair. | avoid injury |
| recctr.frontdesk.checkin | Recreation front desk check-in | invariant | Check-in verifies member, guest, booking, program or day pass. | entry gate |
| recctr.frontdesk.guest_pass | Recreation guest pass | variant | Pass records visitor, sponsor, payment, waiver and access limit. | controlled guest |
| recctr.frontdesk.lost_found | Recreation lost and found | invariant | Process tags, stores, claims and disposes found items by policy. | return property |
| recctr.frontdesk.customer_question | Recreation customer question | invariant | Question routes to membership, program, facility, refund, safety or management answer. | service desk |
| recctr.frontdesk.refund_request | Recreation refund request | variant | Request records program, booking, reason, policy, approval and payment route. | financial control |
| recctr.safety.incident_report | Recreation incident report | invariant | Report documents injury, conflict, theft, property damage, pool event or rule violation. | formal record |
| recctr.safety.first_aid_station | Recreation first aid station | invariant | Station holds supplies, AED if present, logs, contacts and inspection records. | emergency readiness |
| recctr.safety.child_pickup | Child pickup authorization | invariant | Authorization controls who may collect child from program or camp. | safeguard |
| recctr.safety.weather_protocol | Recreation weather protocol | variant | Protocol handles lightning, heat, air quality, snow, field closure or outdoor cancellation. | environment risk |
| recctr.safety.security_walk | Facility security walk | invariant | Walk checks doors, bathrooms, locker rooms, lots, lights and unauthorized presence. | site awareness |
| recctr.facility.opening_round | Recreation center opening round | invariant | Round checks access, rooms, pool, gym, HVAC, cleaning, schedules and staff. | start day |
| recctr.facility.closing_round | Recreation center closing round | invariant | Round clears users, locks rooms, secures cash, checks equipment and logs issues. | end day |
| recctr.facility.maintenance_ticket | Recreation maintenance ticket | invariant | Ticket records facility, equipment, plumbing, HVAC, lighting, field or safety issue. | repair flow |
| recctr.facility.cleaning_schedule | Recreation cleaning schedule | invariant | Schedule covers locker rooms, courts, equipment, floors, bathrooms and high-touch surfaces. | hygiene |
| recctr.facility.vendor_access | Recreation vendor access | variant | Access controls contractors, cleaners, instructors, repair techs and deliveries. | site control |
| recctr.billing.membership_billing | Recreation membership billing | invariant | Billing handles dues, passes, program fees, rentals, discounts and taxes. | revenue |
| recctr.billing.scholarship_discount | Scholarship or discount | variant | Discount applies approved financial aid, resident rate, age category or promotion. | access equity |
| recctr.metrics.rec_center_kpi | Recreation center KPI | variant | KPI tracks attendance, utilization, incidents, program fill, revenue, churn and maintenance backlog. | manage center |
| recctr.continuity.facility_closure | Recreation facility closure | invariant | Closure process informs members, refunds or credits bookings and secures building. | disruption control |
