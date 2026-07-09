# BATCH_228 — Fitness Club Operations Detail
# world_skills_core · source: world_skills_core:batch_228:fitness_club_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| fitclub.member.membership_sale | Fitness membership sale | invariant | Sale records plan, term, price, start date, agreement, billing and access rules. | start account |
| fitclub.member.member_profile | Fitness member profile | invariant | Profile stores identity, contact, emergency contact, access level and preferences. | know member |
| fitclub.member.waiver_ack | Fitness waiver acknowledgment | invariant | Acknowledgment records risk, conduct, facility rule and health disclosure acceptance. | permission evidence |
| fitclub.member.freeze_request | Membership freeze request | variant | Request pauses billing or access for approved reason and period. | account flexibility |
| fitclub.member.cancel_request | Fitness cancellation request | invariant | Request records notice date, reason, final billing, access end and confirmation. | clean exit |
| fitclub.access.checkin | Fitness club check-in | invariant | Check-in verifies active membership, day pass, guest, class booking or alert. | entry control |
| fitclub.access.guest_pass | Fitness guest pass | variant | Pass records visitor, sponsor, waiver, fee, access limits and expiration. | controlled trial |
| fitclub.access.door_access | Fitness door access | invariant | Access controls entrance, locker area, after-hours and staff-only spaces. | security |
| fitclub.access.tailgating | Fitness tailgating event | invariant | Event flags unauthorized entry behind another member and needs staff response. | revenue and safety |
| fitclub.access.age_restriction | Fitness age restriction | invariant | Restriction limits equipment, areas, hours or supervision by age policy. | youth safety |
| fitclub.floor.equipment_layout | Fitness floor layout | invariant | Layout places cardio, strength, stretching and circulation for safe use and supervision. | usable space |
| fitclub.floor.equipment_orientation | Equipment orientation | variant | Orientation explains basic safe use, adjustment, cleaning and staff help path. | reduce misuse |
| fitclub.floor.floor_walk | Fitness floor walk | invariant | Walk checks equipment, weights, spills, towels, crowding, behavior and hazards. | active oversight |
| fitclub.floor.weight_restack | Weight restack | invariant | Restack returns plates, dumbbells, bars and accessories to designated locations. | order and safety |
| fitclub.floor.equipment_outage | Fitness equipment outage | invariant | Outage tags broken equipment, logs fault, blocks use and schedules repair. | prevent injury |
| fitclub.class.class_schedule | Fitness class schedule | invariant | Schedule assigns class type, room, instructor, capacity, equipment and booking rule. | organize classes |
| fitclub.class.class_checkin | Fitness class check-in | invariant | Check-in verifies booking, waitlist, capacity and attendance. | room control |
| fitclub.class.waitlist | Fitness class waitlist | variant | Waitlist fills canceled spots and manages demand for popular sessions. | fair access |
| fitclub.class.instructor_sub | Instructor substitution | invariant | Substitution replaces absent instructor, updates class notes and informs members. | continuity |
| fitclub.class.room_turnover | Studio room turnover | invariant | Turnover resets equipment, floor, mirrors, sound and ventilation between classes. | ready room |
| fitclub.training.pt_consult | Personal training consultation | variant | Consult records goals, limitations, package, trainer match and scheduling preference. | start coaching |
| fitclub.training.package_sale | Personal training package sale | variant | Sale tracks sessions, price, expiration, trainer, cancellation and refund rules. | service revenue |
| fitclub.training.session_note | Training session note | invariant | Note records attendance, focus, exercises, response, next plan and incidents. | coaching memory |
| fitclub.training.trainer_credential | Trainer credential record | invariant | Record tracks certification, specialty, insurance if needed, CPR/AED and expiry. | qualified staff |
| fitclub.training.session_no_show | Training session no-show | invariant | No-show record applies package policy, notice, trainer time and follow-up. | protect time |
| fitclub.cleaning.equipment_wipe | Equipment wipe routine | invariant | Routine cleans high-touch surfaces, pads, handles, screens and mats. | hygiene |
| fitclub.cleaning.locker_room_round | Locker room round | invariant | Round checks showers, toilets, lockers, towels, supplies, floors and privacy concerns. | member comfort |
| fitclub.cleaning.towel_service | Fitness towel service | variant | Service manages clean towels, soiled bins, laundry, shortage and misuse. | amenity control |
| fitclub.cleaning.sweat_spill | Sweat or spill response | invariant | Response cleans liquid, marks hazard and prevents slips. | floor safety |
| fitclub.cleaning.sanitation_log | Fitness sanitation log | invariant | Log records cleaning rounds, staff, area, time and exceptions. | proof of care |
| fitclub.safety.incident_report | Fitness incident report | invariant | Report documents injury, illness, conflict, equipment issue, theft or privacy concern. | formal record |
| fitclub.safety.aed_check | Fitness AED check | invariant | Check verifies device, pads, battery, location and inspection date. | emergency readiness |
| fitclub.safety.emergency_action_plan | Fitness emergency action plan | invariant | Plan defines staff roles, EMS call, crowd control, documentation and handoff. | respond fast |
| fitclub.safety.behavior_policy | Fitness behavior policy | invariant | Policy manages harassment, filming, dropping weights, unsafe lifting, intoxication or aggression. | shared norms |
| fitclub.safety.child_area | Child or family area control | variant | Control covers supervised zones, pickup, age limits, toys, ratios and incidents. | family safety |
| fitclub.retail.pro_shop_sale | Fitness pro shop sale | variant | Sale handles supplements, apparel, locks, bottles, accessories and returns. | extra revenue |
| fitclub.retail.locker_rental | Locker rental | variant | Rental controls assigned locker, term, fee, lock, contents and abandoned items. | storage service |
| fitclub.billing.failed_payment | Fitness failed payment | invariant | Failure triggers retry, notice, access review, collections or cancellation path. | revenue control |
| fitclub.billing.refund_request | Fitness refund request | invariant | Request records reason, policy, approval, payment method and credit. | financial control |
| fitclub.billing.corporate_plan | Corporate fitness plan | variant | Plan links employer, eligible members, discounts, invoicing and reporting. | group account |
| fitclub.admin.opening_round | Fitness club opening round | invariant | Round checks access, equipment, locker rooms, cleaning, cash, classes and staffing. | start day |
| fitclub.admin.closing_round | Fitness club closing round | invariant | Round clears members, secures cash, locks areas, logs issues and resets equipment. | end day |
| fitclub.metrics.fitness_kpi | Fitness club KPI | variant | KPI tracks joins, cancels, utilization, class fill, PT sales, incidents and maintenance backlog. | manage club |
| fitclub.continuity.power_outage | Fitness power outage plan | invariant | Plan handles lighting, access, equipment shutdown, member notice and reopening. | safe disruption |
