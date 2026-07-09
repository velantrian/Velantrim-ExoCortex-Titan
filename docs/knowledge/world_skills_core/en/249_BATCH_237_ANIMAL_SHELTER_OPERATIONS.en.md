# BATCH_237 — Animal Shelter Operations Detail
# world_skills_core · source: world_skills_core:batch_237:animal_shelter_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| shelterops.intake.animal_intake | Animal shelter intake | invariant | Intake records animal, source, date, reason, location, condition and legal status. | start case |
| shelterops.intake.stray_hold | Animal stray hold | invariant | Hold tracks required retention period, finder, notices, identification and release eligibility. | legal control |
| shelterops.intake.owner_surrender | Owner surrender intake | variant | Intake captures owner information, history, behavior, medical notes and consent. | better placement |
| shelterops.intake.microchip_scan | Shelter microchip scan | invariant | Scan records chip number, registry contact, owner outreach and outcome. | reunite animal |
| shelterops.intake.photo_profile | Shelter intake photo profile | variant | Profile captures clear photos, markings, age estimate and descriptive notes. | identification |
| shelterops.kennel.kennel_assignment | Shelter kennel assignment | invariant | Assignment matches species, size, behavior, health status and cleaning zone. | safe housing |
| shelterops.kennel.capacity_count | Shelter capacity count | invariant | Count tracks occupied, available, isolation, foster, surgery and hold spaces. | manage population |
| shelterops.kennel.feeding_card | Shelter feeding card | invariant | Card states diet, amount, schedule, restrictions, appetite notes and staff initials. | consistent care |
| shelterops.kennel.behavior_note | Shelter behavior note | invariant | Note records fear, aggression, sociability, enrichment response and handling cautions. | safer handling |
| shelterops.kennel.animal_movement | Shelter animal movement log | invariant | Log tracks kennel, exam, surgery, foster, adoption, transfer or release movement. | know location |
| shelterops.medical.medical_record | Shelter animal medical record | invariant | Record captures exam, vaccinations, medications, tests, treatments and clinician notes. | health history |
| shelterops.medical.vaccine_schedule | Shelter vaccine schedule | invariant | Schedule records due dates, products, lot, staff and boosters. | disease prevention |
| shelterops.medical.quarantine_status | Shelter quarantine status | invariant | Status separates exposed, symptomatic, bite, legal hold or infectious animals. | infection control |
| shelterops.medical.surgery_queue | Shelter surgery queue | variant | Queue prioritizes spay/neuter, urgent care, dental, injury or transfer clearance. | medical planning |
| shelterops.medical.medication_admin | Shelter medication administration | invariant | Administration records animal, drug name, dose as prescribed, time, route and staff. | treatment evidence |
| shelterops.adoption.adoption_application | Animal adoption application | invariant | Application captures adopter identity, household, animals, landlord, preferences and references. | screen placement |
| shelterops.adoption.matchmaking_note | Shelter adoption matchmaking note | variant | Note matches animal needs with adopter lifestyle, experience, housing and expectations. | better fit |
| shelterops.adoption.meet_greet | Animal meet-and-greet | variant | Session records participants, behavior, handler, concerns and next steps. | informed decision |
| shelterops.adoption.contract | Animal adoption contract | invariant | Contract records adopter, animal, fee, obligations, medical disclosures and return terms. | legal placement |
| shelterops.adoption.post_adoption_followup | Post-adoption follow-up | variant | Follow-up checks adjustment, medical concerns, behavior support and satisfaction. | reduce returns |
| shelterops.foster.foster_application | Shelter foster application | invariant | Application records foster identity, home, species preferences, capacity and approvals. | foster readiness |
| shelterops.foster.foster_placement | Shelter foster placement | invariant | Placement links animal, foster, supplies, medical plan, check-in and return date. | extend capacity |
| shelterops.foster.foster_supply | Foster supply issue | variant | Issue records food, litter, crate, medication, equipment and return expectation. | support foster |
| shelterops.foster.foster_update | Foster animal update | invariant | Update captures health, weight, behavior, photos, concerns and appointment needs. | remote monitoring |
| shelterops.volunteer.volunteer_onboarding | Shelter volunteer onboarding | invariant | Onboarding covers application, training, role, waiver, schedule and supervision. | safe help |
| shelterops.volunteer.dog_walking_role | Shelter dog walking role | variant | Role defines approved dogs, leash rules, route, behavior flags and incident reporting. | safe exercise |
| shelterops.volunteer.cat_socialization | Shelter cat socialization role | variant | Role defines handling, room rules, enrichment, sanitation and stress cues. | animal welfare |
| shelterops.volunteer.shift_roster | Shelter volunteer shift roster | invariant | Roster assigns volunteers, duties, times, zones and supervisor contact. | coverage |
| shelterops.incident.bite_report | Shelter bite report | invariant | Report captures animal, person, wound, circumstances, quarantine, notifications and follow-up. | legal safety |
| shelterops.incident.escape_response | Shelter animal escape response | invariant | Response records last location, search roles, traps, notices, owner contact and outcome. | recover animal |
| shelterops.incident.injury_report | Shelter injury report | invariant | Report documents animal or person injury, care, witnesses, cause and prevention action. | incident learning |
| shelterops.incident.behavior_escalation | Shelter behavior escalation | variant | Escalation routes severe fear, aggression or decline to behavior or medical review. | protect welfare |
| shelterops.sanitation.kennel_cleaning | Shelter kennel cleaning | invariant | Cleaning removes waste, bedding, dishes, disinfects surfaces and records completion. | disease control |
| shelterops.sanitation.isolation_protocol | Shelter isolation protocol | invariant | Protocol separates cleaning tools, PPE, traffic flow and waste for infectious areas. | prevent spread |
| shelterops.sanitation.laundry_cycle | Shelter laundry cycle | variant | Cycle manages bedding, towels, contamination, washer loads, drying and storage. | clean supplies |
| shelterops.sanitation.dish_sanitation | Shelter dish sanitation | invariant | Sanitation cleans bowls, litter pans, toys and feeders by zone and risk. | reduce pathogens |
| shelterops.transfer.rescue_transfer | Animal rescue transfer | variant | Transfer records partner, animal list, medical packet, transport, custody and confirmation. | move animals |
| shelterops.transfer.transport_log | Shelter animal transport log | invariant | Log captures driver, vehicle, crates, route, temperature, stops and handoff. | custody |
| shelterops.release.owner_reclaim | Animal owner reclaim | invariant | Reclaim verifies ownership, fees, vaccines, legal requirements and release paperwork. | lawful return |
| shelterops.release.euthanasia_review | Shelter euthanasia review | variant | Review documents medical, behavioral, legal, capacity, alternatives and authorization. | accountable decision |
| shelterops.reporting.population_report | Shelter population report | invariant | Report summarizes intake, adoption, reclaim, transfer, euthanasia, foster and capacity. | manage shelter |
| shelterops.reporting.disease_watch | Shelter disease watch report | variant | Report tracks symptoms, tests, isolation, affected rooms and trend response. | protect population |
| shelterops.metrics.shelter_kpi | Animal shelter KPI | variant | KPI tracks live release, length of stay, capacity, disease, returns, incidents and foster use. | manage outcomes |
| shelterops.continuity.disaster_sheltering | Animal disaster sheltering | variant | Plan coordinates emergency intake, crates, supplies, owners, records and biosecurity. | crisis capacity |
