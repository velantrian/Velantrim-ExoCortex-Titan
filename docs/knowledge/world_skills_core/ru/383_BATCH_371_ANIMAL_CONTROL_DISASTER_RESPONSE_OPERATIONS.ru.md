# BATCH 371: Animal Control Disaster Response Operations

**KnowledgeUnits:** 44  
**Namespace:** `animaldisasterops.*`  
**Scope:** pet sheltering, rescue requests, owner reunification, bite incidents, supplies and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| animaldisasterops.activation.trigger | activation trigger | MODEL | Animal response activates when disaster affects pets, livestock, strays or bite risk. | Opens animal-specific operations. |
| animaldisasterops.activation.authority | authority record | RECORD | Authority records lead agency, incident link, site and operating period. | Clarifies responsibility. |
| animaldisasterops.activation.partner_roles | partner roles | RECORD | Partners include animal control, shelters, vets, rescue groups and agriculture agencies. | Aligns response network. |
| animaldisasterops.activation.field_boundary | field boundary | CONSTRAINT | Response scope separates owned pets, strays, livestock, wildlife and dangerous animals. | Routes cases correctly. |
| animaldisasterops.intake.request_id | rescue request ID | RECORD | Request ID links caller, animal, location, hazard, owner and status. | Tracks animal rescue demand. |
| animaldisasterops.intake.location | location capture | METHOD | Location captures address, GPS, access route, flood/fire zone and owner contact. | Helps field teams find animals. |
| animaldisasterops.intake.animal_description | animal description | RECORD | Description records species, breed, color, size, microchip, collar and behavior. | Supports identification. |
| animaldisasterops.intake.priority | priority level | MODEL | Priority uses life risk, trapped status, weather, aggression, owner evacuation and public hazard. | Sends teams to urgent cases. |
| animaldisasterops.field.team_safety | team safety | SAFETY_RULE | Field teams assess access, utilities, flood, fire, bites and PPE before approach. | Protects responders. |
| animaldisasterops.field.capture_plan | capture plan | METHOD | Capture plan chooses traps, leads, crates, nets or specialist support. | Reduces injury. |
| animaldisasterops.field.owner_permission | owner permission | CONSTRAINT | Entry or animal removal requires permission or emergency authority. | Protects property rights. |
| animaldisasterops.field.transport | animal transport | METHOD | Transport separates species, aggression, illness and temperature needs. | Moves animals safely. |
| animaldisasterops.shelter.intake | animal shelter intake | METHOD | Intake records animal, source, condition, owner, location and belongings. | Starts custody trail. |
| animaldisasterops.shelter.cage_card | cage card | RECORD | Cage card shows ID, species, warnings, feeding, meds and owner status. | Keeps care visible. |
| animaldisasterops.shelter.separation | species separation | SAFETY_RULE | Species, size, aggression and disease risk are separated. | Prevents conflict and spread. |
| animaldisasterops.shelter.capacity | shelter capacity | MEASUREMENT | Capacity tracks kennels, crates, staff, food and veterinary limits. | Prevents overcrowding. |
| animaldisasterops.medical.triage | veterinary triage | METHOD | Triage identifies injury, dehydration, heat/cold exposure, pregnancy or infectious signs. | Routes urgent care. |
| animaldisasterops.medical.medication | medication record | RECORD | Medication from owner or vet is logged without improvising treatment. | Maintains continuity. |
| animaldisasterops.medical.quarantine | quarantine area | SAFETY_RULE | Bite, rabies risk or infectious animals use quarantine protocol. | Protects animals and people. |
| animaldisasterops.medical.vet_referral | vet referral | METHOD | Animals needing care route to veterinarian or emergency clinic. | Avoids unsafe shelter care. |
| animaldisasterops.reunification.owner_claim | owner claim | METHOD | Owner claim verifies identity, animal match and custody right. | Prevents wrong release. |
| animaldisasterops.reunification.microchip | microchip scan | METHOD | Microchip scan links animal to registered owner when data is current. | Speeds reunification. |
| animaldisasterops.reunification.photo_board | photo board | METHOD | Public photo lists show found animals while limiting sensitive location data. | Helps owners search. |
| animaldisasterops.reunification.release | release record | RECORD | Release records owner, proof, animal condition, time and instructions. | Closes custody. |
| animaldisasterops.bite.incident | bite incident | RECORD | Bite record captures victim, animal, circumstances, wound report and owner. | Starts required follow-up. |
| animaldisasterops.bite.quarantine_order | quarantine order | CONSTRAINT | Bite cases follow rabies and animal control quarantine rules. | Protects public health. |
| animaldisasterops.bite.exposure_referral | exposure referral | SAFETY_RULE | Human exposure routes to medical or public health guidance. | Reduces health risk. |
| animaldisasterops.bite.investigation | bite investigation | METHOD | Investigation reviews animal history, vaccination, behavior and legal status. | Supports decisions. |
| animaldisasterops.supplies.food | animal food supply | RECORD | Food inventory tracks species, special diets, quantity and burn rate. | Prevents shortages. |
| animaldisasterops.supplies.crates | crates and cages | RECORD | Crates are tracked by size, condition, owner and location. | Keeps containment available. |
| animaldisasterops.supplies.sanitation | sanitation supplies | SAFETY_RULE | Cleaning, waste, litter and disinfectant supplies support disease control. | Keeps shelter safe. |
| animaldisasterops.supplies.donation | animal donation control | METHOD | Donations are accepted by need, safety, packaging and storage capacity. | Avoids unusable piles. |
| animaldisasterops.records.custody | custody log | RECORD | Custody log tracks rescue, transport, shelter, care and release. | Supports legal accountability. |
| animaldisasterops.records.photo | photo record | RECORD | Photos document animal condition and identification at intake/release. | Reduces disputes. |
| animaldisasterops.records.privacy | owner privacy | SAFETY_RULE | Owner addresses and contacts are not publicly exposed unnecessarily. | Protects evacuees. |
| animaldisasterops.records.retention | retention rule | CONSTRAINT | Records follow animal control, emergency and legal schedules. | Preserves evidence. |
| animaldisasterops.communication.public_notice | public notice | METHOD | Notices explain pet sheltering, found animals, claims, supplies and deadlines. | Guides owners. |
| animaldisasterops.communication.owner_update | owner update | METHOD | Owners receive animal status, location, care needs and pickup rules. | Reduces anxiety. |
| animaldisasterops.communication.partner_update | partner update | METHOD | Partners receive capacity, supply needs, hazards and transport requests. | Coordinates support. |
| animaldisasterops.metrics.animals_served | animals served | MEASUREMENT | Counts track rescued, sheltered, reunited, transferred and deceased animals. | Shows workload. |
| animaldisasterops.metrics.reunification_rate | reunification rate | MEASUREMENT | Rate measures animals returned to owners from shelter population. | Shows outcome quality. |
| animaldisasterops.qa.case_audit | case audit | QUALITY_CHECK | Audit checks custody, owner proof, medical notes and release records. | Improves control. |
| animaldisasterops.demob.transfer | transfer process | METHOD | Remaining animals transfer to shelters, fosters or owners under records. | Prevents abandonment. |
| animaldisasterops.demob.after_action | after-action review | METHOD | Review captures rescue gaps, shelter capacity, bite issues and supply needs. | Improves next response. |
