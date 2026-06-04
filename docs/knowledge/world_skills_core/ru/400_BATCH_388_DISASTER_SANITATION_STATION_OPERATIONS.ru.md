# BATCH 388: Disaster Sanitation Station Operations

**KnowledgeUnits:** 44  
**Namespace:** `sanitationstationops.*`  
**Scope:** portable toilets, handwashing, waste servicing, placement, accessibility, complaints and demobilization.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| sanitationstationops.activation.trigger | activation trigger | MODEL | Trigger includes sheltering, water outage, outdoor queues, debris crews or damaged restrooms. | Starts sanitation support. |
| sanitationstationops.activation.site_list | site list | RECORD | Site list stores locations, users, expected volume, owner and service level. | Organizes deployment. |
| sanitationstationops.activation.health_review | health review | SAFETY_RULE | Public health reviews placement, waste handling and handwashing needs. | Reduces disease risk. |
| sanitationstationops.activation.vendor | vendor assignment | RECORD | Vendor record links units, service frequency, contacts and contract terms. | Controls outsourced service. |
| sanitationstationops.placement.location | placement location | METHOD | Placement considers access, distance, lighting, drainage, traffic and privacy. | Makes units usable. |
| sanitationstationops.placement.setback | setback rule | CONSTRAINT | Units avoid wells, food areas, waterways and blocked exits. | Protects health and safety. |
| sanitationstationops.placement.accessibility | accessible unit | METHOD | Accessible units are placed on firm route near services. | Supports disabled users. |
| sanitationstationops.placement.security | security lighting | METHOD | Lighting, patrol or fencing may protect users and units. | Reduces misuse. |
| sanitationstationops.inventory.unit_id | toilet unit ID | RECORD | Unit ID links vendor, type, location, status and service history. | Tracks assets. |
| sanitationstationops.inventory.handwash_id | handwash station ID | RECORD | Station ID links water, soap, towels, sanitizer and location. | Controls hygiene support. |
| sanitationstationops.inventory.supplies | supply inventory | MEASUREMENT | Supplies track toilet paper, soap, sanitizer, towels, water and chemicals. | Prevents depletion. |
| sanitationstationops.inventory.status | unit status | RECORD | Status records clean, full, damaged, tipped, inaccessible or removed. | Guides service. |
| sanitationstationops.service.frequency | service frequency | MODEL | Frequency uses expected users, heat, event length and waste capacity. | Prevents overflow. |
| sanitationstationops.service.pumping | pumping service | METHOD | Pumping removes waste and refreshes chemicals under safe handling rules. | Keeps toilets operational. |
| sanitationstationops.service.cleaning | cleaning service | METHOD | Cleaning addresses surfaces, odors, paper, handwash and visible soil. | Maintains dignity. |
| sanitationstationops.service.water_refill | handwash refill | METHOD | Water, soap and towels are refilled on schedule or demand. | Maintains hygiene. |
| sanitationstationops.waste.disposal_site | disposal site | RECORD | Waste disposal site is approved and documented. | Protects environment. |
| sanitationstationops.waste.manifest | waste manifest | RECORD | Manifest records volume, unit, truck, time and disposal location. | Supports compliance. |
| sanitationstationops.waste.spill | toilet waste spill response | SAFETY_RULE | Toilet waste spills trigger cordon, vendor pumpout, disinfection, health notification and cleanup record. | Prevents contamination. |
| sanitationstationops.waste.hazard | hazardous conflict | CONSTRAINT | Toilets near chemical, flood or structural hazards may need relocation. | Protects users. |
| sanitationstationops.complaint.complaint_id | complaint ID | RECORD | Complaint ID links site, issue, reporter, time and resolution. | Tracks service problems. |
| sanitationstationops.complaint.odor | odor complaint | METHOD | Odor complaints trigger cleaning, pumping, relocation or ventilation review. | Improves usability. |
| sanitationstationops.complaint.access | access complaint | METHOD | Access complaints address blocked path, lighting, distance or disability barriers. | Supports equity. |
| sanitationstationops.complaint.vandalism | vandalism complaint | RECORD | Vandalism records damage, safety issue, photo and repair/removal. | Maintains function. |
| sanitationstationops.public.signage | signage | METHOD | Signs direct users to toilets and handwashing without blocking traffic. | Helps people find facilities. |
| sanitationstationops.public.instructions | user instructions | METHOD | Instructions explain handwashing, waste, hours and complaint contact. | Encourages proper use. |
| sanitationstationops.public.language | language support | METHOD | Core sanitation signs use local languages and symbols where possible. | Improves access. |
| sanitationstationops.public.privacy | privacy screen | METHOD | Screens or placement protect dignity where queues or open areas exist. | Improves acceptance. |
| sanitationstationops.safety.staff_ppe | staff PPE | SAFETY_RULE | Service staff use PPE for waste, chemicals, lifting and traffic. | Protects workers. |
| sanitationstationops.safety.traffic | traffic protection | SAFETY_RULE | Service trucks and users are protected from vehicle conflicts. | Reduces accidents. |
| sanitationstationops.safety.weather | weather anchoring | SAFETY_RULE | Units are anchored or moved for wind, flood, snow or heat exposure. | Prevents tipping and hazards. |
| sanitationstationops.safety.night | night safety | METHOD | Night sites need lighting, visibility and security review. | Protects users. |
| sanitationstationops.records.service_log | service log | RECORD | Log records cleaning, pumping, refill, repair, removal and technician. | Provides evidence. |
| sanitationstationops.records.photo | photo record | RECORD | Photos document placement, damage, access and closeout condition. | Supports disputes. |
| sanitationstationops.records.cost | cost record | RECORD | Costs track rental, service, damage, supplies and emergency fees. | Supports finance. |
| sanitationstationops.records.retention | retention rule | CONSTRAINT | Records follow health, procurement, finance and emergency retention rules. | Preserves audit. |
| sanitationstationops.metrics.unit_ratio | unit ratio | MEASUREMENT | Ratio compares toilets/handwash stations to user population. | Shows adequacy. |
| sanitationstationops.metrics.service_miss | missed service | MEASUREMENT | Missed service records vendor, site, cause and corrective action. | Improves reliability. |
| sanitationstationops.qa.site_inspection | site inspection | QUALITY_CHECK | Inspection checks cleanliness, supplies, access, safety and placement. | Keeps service acceptable. |
| sanitationstationops.demob.removal | unit removal | METHOD | Removal pumps, cleans, documents condition and restores site. | Ends service cleanly. |
| sanitationstationops.demob.final_reconcile | final reconciliation | QUALITY_CHECK | Final reconciliation matches units, service logs, invoices and damage. | Prevents billing gaps. |
| sanitationstationops.review.after_action | after-action review | METHOD | Review captures placement, servicing, complaints, accessibility and vendor lessons. | Improves next deployment. |
| sanitationstationops.governance.health_liaison | health liaison | RECORD | Public health liaison reviews sanitation adequacy, complaints and disease risk. | Keeps health accountability visible. |
| sanitationstationops.governance.owner | program owner | RECORD | Owner coordinates public health, logistics, vendor and site managers. | Keeps accountability clear. |
