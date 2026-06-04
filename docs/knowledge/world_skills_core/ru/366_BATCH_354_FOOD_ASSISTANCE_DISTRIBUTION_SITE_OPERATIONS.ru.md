# BATCH 354: Food Assistance Distribution Site Operations

**KnowledgeUnits:** 44  
**Namespace:** `fooddistops.*`  
**Scope:** registration, eligibility, inventory, queues, accessibility, safety and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| fooddistops.activation.site_plan | site plan | RECORD | Site plan defines location, hours, layout, partners and service model. | Sets distribution structure. |
| fooddistops.activation.partner_role | partner role | RECORD | Partner role identifies food bank, city, nonprofit, volunteers and security responsibilities. | Avoids confusion. |
| fooddistops.activation.capacity | capacity estimate | MODEL | Capacity estimates households, vehicles, walk-ins, staff and food volume. | Prevents overload. |
| fooddistops.activation.weather | weather plan | METHOD | Weather plan covers shade, heat, rain, cold, tents and closure thresholds. | Protects clients and staff. |
| fooddistops.registration.household | household registration | METHOD | Registration records household size, location, program category and visit date. | Supports fair distribution. |
| fooddistops.registration.low_barrier | low-barrier intake | CONSTRAINT | Emergency food sites minimize paperwork where policy allows. | Keeps access humane. |
| fooddistops.registration.privacy | privacy protection | SAFETY_RULE | Client information is minimized, secured and not exposed in queues. | Protects dignity. |
| fooddistops.registration.duplicate_visit | duplicate visit control | QUALITY_CHECK | Duplicate check prevents multiple pickups when program rules require limits. | Preserves scarce food. |
| fooddistops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria may include residency, income, emergency status or self-attestation. | Defines service population. |
| fooddistops.eligibility.self_attest | self-attestation | METHOD | Self-attestation can document need without excessive proof. | Reduces access barriers. |
| fooddistops.eligibility.referral | referral acceptance | METHOD | Referral from school, clinic, agency or outreach may support eligibility. | Connects systems. |
| fooddistops.eligibility.exception | exception approval | METHOD | Exceptions are documented for disaster, disability, family crisis or stock conditions. | Allows humane flexibility. |
| fooddistops.inventory.receiving | food receiving | METHOD | Receiving records source, date, quantity, temperature and condition. | Protects food safety and accountability. |
| fooddistops.inventory.stock_count | stock count | MEASUREMENT | Stock count tracks cases, pallets, perishables, shelf-stable items and special diets. | Supports allocation. |
| fooddistops.inventory.expiration | date rotation | QUALITY_CHECK | Food is rotated by expiration, best-by, lot and condition. | Reduces waste and unsafe food. |
| fooddistops.inventory.allergen | allergen control | SAFETY_RULE | Allergen or diet items are labeled and separated where practical. | Protects clients. |
| fooddistops.pack.standard_box | standard box | METHOD | Standard box defines base package by household size or event rule. | Speeds distribution. |
| fooddistops.pack.choice_model | client choice model | METHOD | Choice model lets clients select allowed items within inventory and dignity goals. | Reduces waste. |
| fooddistops.pack.cold_item | cold item handling | SAFETY_RULE | Cold items require temperature control, limited dwell time and release logs. | Prevents spoilage. |
| fooddistops.pack.special_diet | special diet handling | METHOD | Special diet requests are filled when inventory and program rules allow. | Supports medical/cultural needs. |
| fooddistops.queue.traffic_flow | traffic flow | METHOD | Traffic plan separates entry, registration, loading, exit and pedestrian routes. | Reduces congestion. |
| fooddistops.queue.walk_in | walk-in queue | METHOD | Walk-in queue provides safe waiting, shade/seating and accessibility. | Supports people without cars. |
| fooddistops.queue.appointment | appointment window | METHOD | Appointment windows spread demand across time. | Reduces long waits. |
| fooddistops.queue.priority | priority lane | METHOD | Priority lane may support elders, disability, emergency referrals or families with infants. | Improves equity. |
| fooddistops.accessibility.ada | accessibility check | QUALITY_CHECK | Site checks accessible path, parking, tables, restrooms and communication. | Keeps distribution inclusive. |
| fooddistops.accessibility.language | language support | METHOD | Signage and interpreters cover common local languages. | Helps clients navigate. |
| fooddistops.accessibility.delivery | home delivery route | METHOD | Delivery supports homebound or quarantined clients under eligibility rules. | Reaches high-need households. |
| fooddistops.accessibility.cultural_food | cultural fit | MODEL | Cultural fit considers staple foods, cooking ability and household preferences. | Makes food more usable. |
| fooddistops.safety.food_safety | food safety | SAFETY_RULE | Handling follows temperature, hygiene, pest and contamination controls. | Prevents illness. |
| fooddistops.safety.site_safety | site safety | SAFETY_RULE | Site safety covers traffic, lifting, slips, crowding, weather and conflict. | Protects everyone onsite. |
| fooddistops.safety.volunteer_brief | volunteer briefing | METHOD | Briefing covers roles, lifting, privacy, conduct, food safety and emergency contacts. | Reduces mistakes. |
| fooddistops.safety.incident | incident report | RECORD | Incidents record injury, conflict, spoiled food, near miss or security issue. | Supports corrective action. |
| fooddistops.distribution.proof | distribution proof | RECORD | Proof records household served, package type, date and staff/volunteer station. | Supports reporting. |
| fooddistops.distribution.shortage | shortage handling | METHOD | Shortage plan defines substitutions, rationing, waitlist or referral. | Manages scarcity transparently. |
| fooddistops.distribution.leftover | leftover handling | METHOD | Leftovers are stored, transferred, donated or discarded by safety rule. | Reduces waste. |
| fooddistops.distribution.referral | service referral | METHOD | Clients may receive referrals to benefits, housing, clinics or legal aid. | Connects food need to broader support. |
| fooddistops.records.lot_trace | lot trace | RECORD | Lot trace preserves source and distribution path for recall. | Enables rapid recall response. |
| fooddistops.records.client_file | client file | RECORD | Client records are kept only as needed for program and reporting. | Limits data burden. |
| fooddistops.records.retention | retention rule | CONSTRAINT | Food, client, volunteer and grant records follow retention schedules. | Supports audit. |
| fooddistops.reporting.households | household reporting | MEASUREMENT | Reports count households, people, children, seniors and special categories. | Shows service reach. |
| fooddistops.reporting.pounds | pounds distributed | MEASUREMENT | Pounds or meal equivalents track volume distributed. | Supports food bank metrics. |
| fooddistops.reporting.unmet | unmet need | MEASUREMENT | Unmet need records turnaways, shortages and waiting list. | Guides resource requests. |
| fooddistops.qa.audit | distribution audit | QUALITY_CHECK | Audit checks eligibility, inventory, safety, privacy and reporting accuracy. | Improves program integrity. |
| fooddistops.closeout.site_close | site closeout | METHOD | Closeout cleans site, reconciles inventory, records issues and briefs partners. | Completes event safely. |
