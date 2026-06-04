# BATCH 436: Emergency Pet Shelter Volunteer Shift Operations

**KnowledgeUnits:** 44  
**Namespace:** `petsheltershiftops.*`  
**Scope:** roles, animal handling, cleaning, feeding, safety, records and demobilization.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| petsheltershiftops.intake.volunteer_checkin | volunteer check-in | PROCESS | Check-in records identity, contact, availability, training status, limitations and emergency contact. | Builds shift roster. |
| petsheltershiftops.intake.role_screen | role screen | CONTROL | Screening matches volunteers to animal care, cleaning, logistics, admin, transport or public desk roles. | Reduces mismatch. |
| petsheltershiftops.intake.liability_ack | liability acknowledgment | RECORD | Acknowledgment confirms safety rules, confidentiality, animal handling limits and incident reporting duties. | Sets expectations. |
| petsheltershiftops.roster.shift_block | shift block | RECORD | Shift block captures start, end, break, supervisor, zone and backup volunteer. | Controls coverage. |
| petsheltershiftops.roster.no_show | no-show handling | PROCESS | No-show handling marks absence, calls backup and updates animal care assignments. | Prevents care gaps. |
| petsheltershiftops.roster.fatigue_limit | fatigue limit | CONTROL | Fatigue limit caps long shifts and high-stress animal handling assignments. | Protects volunteers and animals. |
| petsheltershiftops.roles.animal_care | animal care role | ROLE | Animal care handles feeding, watering, observation and basic comfort under supervision. | Supports daily care. |
| petsheltershiftops.roles.cleaning_team | cleaning team role | ROLE | Cleaning team manages kennels, litter, bedding, waste, laundry and disinfection tasks. | Maintains sanitation. |
| petsheltershiftops.roles.public_desk | public desk role | ROLE | Public desk answers owner questions, records inquiries and routes reunification requests. | Organizes communication. |
| petsheltershiftops.roles.supply_runner | supply runner role | ROLE | Supply runner moves food, litter, crates, PPE and laundry between zones. | Keeps work flowing. |
| petsheltershiftops.handling.species_limit | species limit | CONTROL | Species limit restricts handling by animal type, size, temperament and volunteer training. | Reduces bites and escapes. |
| petsheltershiftops.handling.leash_protocol | leash protocol | PROCESS | Leash protocol defines double-leash, crate transfer, gate control and handoff rules. | Prevents escapes. |
| petsheltershiftops.handling.stress_signal | stress signal | MODEL | Stress signals include hiding, panting, freezing, growling, excessive vocalization or refusal to eat. | Guides gentle care. |
| petsheltershiftops.handling.quiet_zone | quiet zone | CONTROL | Quiet zone separates stressed, elderly, medically fragile or reactive animals from public flow. | Reduces harm. |
| petsheltershiftops.feeding.diet_card | diet card | RECORD | Diet card lists food type, amount, restrictions, medication note and feeding time. | Prevents wrong feeding. |
| petsheltershiftops.feeding.water_check | water check | PROCESS | Water check verifies clean bowls, refill times and spills in each housing area. | Maintains basic care. |
| petsheltershiftops.feeding.special_diet | special diet control | CONTROL | Special diet separates allergy, prescription food, species-specific or owner-provided feed. | Prevents mistakes. |
| petsheltershiftops.cleaning.kennel_cycle | kennel cleaning cycle | PROCESS | Cycle covers remove animal, dispose waste, clean, disinfect, dry, replace bedding and document completion. | Keeps shelter sanitary. |
| petsheltershiftops.cleaning.contact_time | disinfectant contact time | CONTROL | Contact time ensures disinfectant remains wet long enough before drying or reusing space. | Improves pathogen control. |
| petsheltershiftops.cleaning.waste_stream | waste stream | MODEL | Waste stream separates bagged waste, sharps, soiled bedding, laundry and hazardous cleanup. | Prevents contamination. |
| petsheltershiftops.cleaning.laundry_rotation | laundry rotation | PROCESS | Rotation tracks dirty pickup, wash, dry, clean storage and shortage alerts. | Keeps bedding available. |
| petsheltershiftops.safety.ppe_station | PPE station | CONTROL | PPE station stocks gloves, masks, aprons, eye protection, sanitizer and bite-report forms. | Supports safe work. |
| petsheltershiftops.safety.bite_scratch_report | bite or scratch report | RECORD | Report captures animal, person, wound, time, first aid, supervisor notification and follow-up. | Enables health response. |
| petsheltershiftops.safety.escape_response | escape response | PROCESS | Response locks doors, alerts zones, avoids chasing, uses calm containment and records incident. | Recovers animals safely. |
| petsheltershiftops.safety.zone_access | zone access control | CONTROL | Access limits volunteers to assigned areas and supervisor-approved animal interactions. | Reduces chaos. |
| petsheltershiftops.records.animal_card | animal card | RECORD | Animal card links intake ID, owner status, location, diet, behavior notes and medical flags. | Keeps care consistent. |
| petsheltershiftops.records.task_board | task board | RECORD | Task board shows feeding, cleaning, walks, laundry, supplies and completed checks by time block. | Coordinates teams. |
| petsheltershiftops.records.shift_log | shift log | RECORD | Shift log captures arrivals, departures, incidents, shortages, completed work and handoff notes. | Preserves continuity. |
| petsheltershiftops.records.confidential_note | confidential note | CONTROL | Confidential note restricts owner contact, investigation, bite quarantine or medical details. | Protects privacy. |
| petsheltershiftops.medical.vet_escalation | vet escalation | PROCESS | Escalation routes injury, illness, dehydration, medication concerns or behavior deterioration to veterinary staff. | Gets expert help. |
| petsheltershiftops.medical.medication_boundary | medication boundary | CONTROL | Boundary prevents untrained volunteers from administering medication without authorized supervision. | Reduces clinical risk. |
| petsheltershiftops.medical.isolation_flag | isolation flag | STATE | Isolation flag marks animals needing separation for disease, injury, aggression or observation. | Protects population. |
| petsheltershiftops.communication.handoff_brief | handoff brief | PROCESS | Brief gives next shift open tasks, animal concerns, supply needs and safety notes. | Avoids missed work. |
| petsheltershiftops.communication.owner_question | owner question routing | PROCESS | Routing sends ownership, pickup, lost pet or medical questions to authorized staff. | Gives accurate answers. |
| petsheltershiftops.communication.volunteer_alert | volunteer alert | PROCESS | Alert announces urgent changes such as quarantine, weather closure, supply shortage or role reassignment. | Keeps teams aligned. |
| petsheltershiftops.supplies.inventory_check | inventory check | PROCESS | Check counts food, crates, litter, bowls, bedding, PPE, cleaning chemicals and forms. | Prevents shortages. |
| petsheltershiftops.supplies.low_stock_trigger | low-stock trigger | CONTROL | Trigger defines minimum quantities and reorder or donation request thresholds. | Keeps operations stable. |
| petsheltershiftops.supplies.donation_sort | donation sorting | PROCESS | Sorting separates usable, expired, open, unsafe, species-specific and surplus supplies. | Protects animals. |
| petsheltershiftops.metrics.care_completion | care completion metric | METRIC | Metric tracks scheduled feeding, watering, cleaning and observation tasks completed on time. | Measures reliability. |
| petsheltershiftops.metrics.incident_rate | incident rate | METRIC | Rate tracks bites, scratches, escapes, illness flags, volunteer injuries and near misses. | Shows safety trend. |
| petsheltershiftops.metrics.shift_fill | shift fill metric | METRIC | Shift fill compares scheduled positions, arrivals, backups used and uncovered roles. | Guides staffing. |
| petsheltershiftops.demobilization.return_process | return process | PROCESS | Return process coordinates owner pickup, documentation, animal release and space cleaning. | Closes cases. |
| petsheltershiftops.demobilization.volunteer_checkout | volunteer checkout | PROCESS | Checkout records departure, badge return, unresolved tasks and debrief needs. | Ends shift cleanly. |
| petsheltershiftops.demobilization.after_action | after-action note | RECORD | Note captures staffing, animal care, sanitation, supply and safety lessons. | Improves next shelter. |
