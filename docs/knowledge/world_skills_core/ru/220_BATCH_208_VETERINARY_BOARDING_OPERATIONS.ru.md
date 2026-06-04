# BATCH_208 — Veterinary Boarding Operations Detail
# world_skills_core · source: world_skills_core:batch_208:veterinary_boarding_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| vetboard.reserve.boarding_reservation | Veterinary boarding reservation | invariant | Reservation records pet, owner, dates, lodging type, services, feeding and medical notes. | hold kennel space |
| vetboard.reserve.capacity_calendar | Boarding capacity calendar | invariant | Calendar tracks kennels, runs, cat condos, isolation spaces and staffing limits. | avoid overbooking |
| vetboard.reserve.vaccine_requirement | Boarding vaccine requirement | variant | Requirement defines proof needed for facility entry according to species and policy. | reduce disease risk |
| vetboard.reserve.deposit_policy | Boarding deposit policy | variant | Policy controls reservation hold, cancellation and peak-date commitment. | protect capacity |
| vetboard.reserve.special_service | Boarding special service | variant | Service may include playtime, grooming, medication support, photos or extra walks. | customize stay |
| vetboard.intake.pet_checkin | Pet boarding check-in | invariant | Check-in confirms identity, owner contact, belongings, diet, meds, behavior and release terms. | safe admission |
| vetboard.intake.belongings_inventory | Pet belongings inventory | invariant | Inventory lists food, bedding, toys, leash, carrier and medication received. | return everything |
| vetboard.intake.feeding_instruction | Feeding instruction | invariant | Instruction records food type, amount, timing, restrictions and owner-provided supply. | consistent meals |
| vetboard.intake.medication_instruction | Boarding medication instruction | variant | Instruction records medication name, schedule, route, storage and owner authorization for staff handling. | high-attention task |
| vetboard.intake.behavior_note | Boarding behavior note | invariant | Note flags aggression, fear, escape risk, separation anxiety, group limits or handling preference. | protect pets and staff |
| vetboard.housing.kennel_assignment | Kennel assignment | invariant | Assignment places pet by species, size, temperament, health status and service level. | right space |
| vetboard.housing.clean_bedding | Clean bedding cycle | invariant | Cycle replaces soiled bedding and records laundry or disposal needs. | comfort and hygiene |
| vetboard.housing.water_check | Boarding water check | invariant | Check confirms water availability, clean bowl and abnormal drinking notes. | basic welfare |
| vetboard.housing.temperature_comfort | Boarding temperature comfort | variant | Comfort monitoring checks room temperature, ventilation and pet-specific sensitivity. | environmental care |
| vetboard.housing.isolation_space | Boarding isolation space | variant | Space separates pets with illness signs, exposure risk or policy restrictions. | infection control |
| vetboard.care.feeding_round | Boarding feeding round | invariant | Round gives correct diet, amount and time while noting refusal, vomiting or special issue. | daily care evidence |
| vetboard.care.walk_schedule | Boarding walk schedule | variant | Schedule assigns outdoor breaks, leash rules, yard use and cleanup. | routine and welfare |
| vetboard.care.playgroup_screen | Playgroup screening | variant | Screening evaluates compatibility, size, behavior, vaccine status and supervision needs. | social safety |
| vetboard.care.elimination_log | Elimination log | invariant | Log records urination, stool, diarrhea, constipation or accidents. | health signal |
| vetboard.care.enrichment_activity | Boarding enrichment activity | variant | Activity provides safe play, interaction, puzzle, cuddle or exercise according to pet profile. | reduce stress |
| vetboard.health.daily_observation | Daily pet observation | invariant | Observation notes appetite, energy, stool, breathing, skin, behavior and abnormal signs. | early issue detection |
| vetboard.health.weight_check | Boarding weight check | variant | Check monitors weight for long stays, medical boarding or fragile animals. | trend signal |
| vetboard.health.vet_alert | Veterinary alert | invariant | Alert notifies clinician or supervisor about abnormal observation, injury, illness or medication issue. | escalate care |
| vetboard.health.incident_record | Boarding incident record | invariant | Record documents bite, fight, injury, escape, illness, property damage or handling problem. | accountability |
| vetboard.health.owner_notification | Owner notification | invariant | Notification records reason, time, contact method, message and owner decision if needed. | keep owner informed |
| vetboard.meds.medication_log | Boarding medication log | variant | Log records scheduled dose handling, time, staff, refusal, spill or exception without giving medical advice. | trace administration task |
| vetboard.meds.controlled_storage | Boarding medication storage | invariant | Storage separates labeled pet medication, refrigeration needs, access and expired items. | avoid mix-up |
| vetboard.meds.missed_med_exception | Missed medication exception | invariant | Exception records missed, late, refused or vomited medication and escalation. | high-risk variance |
| vetboard.meds.refill_alert | Medication supply alert | variant | Alert warns owner or staff when owner-provided medication may run out during stay. | prevent gap |
| vetboard.meds.medication_return | Medication return | invariant | Return verifies remaining medication, label and owner pickup at checkout. | close custody |
| vetboard.clean.cleaning_schedule | Boarding cleaning schedule | invariant | Schedule covers kennels, bowls, floors, drains, yards, litter and common areas. | hygiene rhythm |
| vetboard.clean.disinfection_protocol | Boarding disinfection protocol | invariant | Protocol defines products, contact time, surfaces, separation and safety precautions. | infection control |
| vetboard.clean.waste_handling | Pet waste handling | invariant | Handling controls bagging, litter, soiled bedding, odor, pests and disposal route. | sanitation |
| vetboard.clean.laundry_flow | Boarding laundry flow | variant | Flow separates soiled, clean, contaminated and owner-owned bedding. | avoid cross-contamination |
| vetboard.clean.pest_prevention | Boarding pest prevention | invariant | Prevention checks food storage, waste, standing water, entry gaps and monitoring. | protect facility |
| vetboard.checkout.pet_checkout | Pet boarding checkout | invariant | Checkout verifies owner identity, pet, belongings, medications, balance and stay notes. | return correctly |
| vetboard.checkout.report_card | Boarding report card | variant | Report card summarizes feeding, behavior, activities, observations and issues. | owner reassurance |
| vetboard.checkout.grooming_handoff | Boarding grooming handoff | variant | Handoff coordinates bath, nail trim or grooming before pickup. | finish service |
| vetboard.checkout.late_pickup | Boarding late pickup | invariant | Process updates care, fees, space, feeding and owner communication for delayed pickup. | handle overstay |
| vetboard.checkout.poststay_followup | Post-stay follow-up | variant | Follow-up checks satisfaction, health concerns, lost items or future booking. | service loop |
| vetboard.admin.staff_assignment | Boarding staff assignment | invariant | Assignment maps staff to feeding, cleaning, walks, meds, observations and front desk tasks. | who does what |
| vetboard.admin.training_record | Boarding staff training record | invariant | Record tracks animal handling, cleaning, bite prevention, medication task policy and emergency procedures. | competent care |
| vetboard.metrics.boarding_kpi | Boarding operations KPI | variant | KPI tracks occupancy, incidents, medication exceptions, complaints, rebooking and labor. | manage facility |
| vetboard.continuity.emergency_evacuation | Boarding emergency evacuation | invariant | Plan covers pet identification, carriers, records, transport, owner contacts and alternate housing. | protect boarded animals |
