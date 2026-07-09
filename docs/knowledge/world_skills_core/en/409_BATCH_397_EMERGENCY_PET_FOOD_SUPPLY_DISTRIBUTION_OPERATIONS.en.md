# BATCH 397: Emergency Pet Food and Supply Distribution Operations

**KnowledgeUnits:** 44  
**Namespace:** `petfooddistops.*`  
**Scope:** intake, stock, eligibility, pickup, delivery, safety and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| petfooddistops.activation.trigger | distribution trigger | MODEL | Trigger includes evacuation, sheltering, supply disruption, income shock or animal welfare requests. | Starts pet support. |
| petfooddistops.activation.partner | partner roster | RECORD | Roster lists animal shelter, food bank, veterinary, rescue and logistics partners. | Coordinates capacity. |
| petfooddistops.activation.service_area | service area | CONSTRAINT | Service area defines eligible jurisdictions, shelters, neighborhoods or outreach routes. | Focuses resources. |
| petfooddistops.activation.command_link | command link | RECORD | Operation reports to animal services, logistics, donations and public information. | Maintains oversight. |
| petfooddistops.intake.owner_info | owner intake | RECORD | Intake captures household, contact, pet count, species, size and urgent constraints. | Defines need. |
| petfooddistops.intake.pet_profile | pet profile | RECORD | Profile notes species, weight band, food type, medical diet and behavior warnings. | Selects supplies. |
| petfooddistops.intake.need_type | need type | RECORD | Need type distinguishes food, litter, crates, leashes, bowls, medication support or transport. | Routes items. |
| petfooddistops.intake.privacy | privacy handling | SAFETY_RULE | Personal data is collected only for distribution, delivery and referral purposes. | Protects residents. |
| petfooddistops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria may use disaster impact, location, shelter status, income or referral. | Preserves fairness. |
| petfooddistops.eligibility.exception | exception review | RECORD | Exceptions document urgent welfare risk, large animal count or special diet need. | Allows humane flexibility. |
| petfooddistops.eligibility.frequency | frequency limit | CONSTRAINT | Frequency limit defines how often a household can receive standard support. | Extends stock. |
| petfooddistops.eligibility.verification | verification method | METHOD | Verification may use self-attestation, shelter roster, address, referral or caseworker confirmation. | Keeps access workable. |
| petfooddistops.inventory.item_master | item master | RECORD | Item master lists food type, species, size, unit, brand constraints and handling notes. | Standardizes stock. |
| petfooddistops.inventory.receiving | receiving check | QUALITY_CHECK | Receiving checks quantity, packaging, expiration, recalls, pests and donation source. | Protects animals. |
| petfooddistops.inventory.special_diet | special diet stock | RECORD | Special diet stock is tracked separately from general food. | Supports medical needs. |
| petfooddistops.inventory.litter_supply | litter supply | MEASUREMENT | Litter stock tracks bags, scoops, trays and waste-related supplies. | Supports cats. |
| petfooddistops.storage.pest_control | pest control | SAFETY_RULE | Storage protects pet food from pests, moisture, heat and contamination. | Maintains usability. |
| petfooddistops.storage.separation | supply separation | METHOD | Food, cleaning chemicals, medicines and used crates are separated. | Prevents contamination. |
| petfooddistops.storage.expiry_rotation | expiry rotation | METHOD | Rotation issues short-dated stock first and removes expired or recalled items. | Avoids unsafe issue. |
| petfooddistops.storage.security | stock security | SAFETY_RULE | High-demand supplies are controlled with access logs and supervised loading. | Reduces loss. |
| petfooddistops.issue.standard_kit | standard kit | METHOD | Standard kit bundles food amount, litter or small supplies by species and period. | Speeds handoff. |
| petfooddistops.issue.pickup_flow | pickup flow | METHOD | Pickup flow manages queue, verification, item selection, loading and receipt. | Serves households. |
| petfooddistops.issue.delivery_request | delivery request | RECORD | Delivery request records address, access, pet needs, mobility barriers and contact window. | Enables outreach. |
| petfooddistops.issue.receipt | issue receipt | RECORD | Receipt logs household, items, quantities, date, staff and exception notes. | Supports inventory. |
| petfooddistops.delivery.route_plan | delivery route | METHOD | Route plan groups deliveries by geography, priority, access and supply type. | Saves time. |
| petfooddistops.delivery.contact_attempt | contact attempt | RECORD | Attempt records call, text, door contact, failed access or reschedule. | Tracks delivery effort. |
| petfooddistops.delivery.no_contact | no-contact handling | METHOD | No-contact policy defines whether supplies can be left, held or returned. | Controls risk. |
| petfooddistops.delivery.field_safety | field safety | SAFETY_RULE | Delivery teams use animal behavior caution, PPE, visibility and route communication. | Protects staff. |
| petfooddistops.safety.bite_risk | bite risk | SAFETY_RULE | Bite risk procedures include distance, owner handling, muzzling advice and escalation. | Prevents injury. |
| petfooddistops.safety.food_recall | food recall check | QUALITY_CHECK | Recall check screens donated or purchased food against current recall notices. | Prevents harm. |
| petfooddistops.safety.allergen_note | allergen note | METHOD | Allergen or diet warnings are communicated when substitute food is issued. | Reduces health issues. |
| petfooddistops.safety.waste | waste handling | METHOD | Damaged food, used litter and contaminated supplies are disposed safely. | Keeps site sanitary. |
| petfooddistops.communication.public_notice | public notice | METHOD | Notice states items, eligibility, hours, limits, pickup access and delivery options. | Guides residents. |
| petfooddistops.communication.partner_update | partner update | METHOD | Partners receive stock needs, distribution counts, shortages and referral pathways. | Aligns response. |
| petfooddistops.communication.multilingual | multilingual script | METHOD | Scripts cover common local languages and plain species/food terms. | Improves access. |
| petfooddistops.communication.shortage_message | shortage message | METHOD | Shortage message explains substitutions, limits, next delivery and referral options. | Reduces conflict. |
| petfooddistops.records.daily_log | daily log | RECORD | Log stores stock received, issued, deliveries, incidents, shortages and unmet needs. | Summarizes operation. |
| petfooddistops.records.cost | cost record | RECORD | Costs track purchased food, transport, storage, labor and equipment. | Supports finance. |
| petfooddistops.records.donation | donation record | RECORD | Donation record captures donor, item, condition, restrictions and disposition. | Maintains accountability. |
| petfooddistops.records.retention | retention rule | CONSTRAINT | Records follow animal services, emergency, grant and privacy schedules. | Preserves audit. |
| petfooddistops.metrics.households_served | households served | MEASUREMENT | Metric counts households and animals supported by species and area. | Shows reach. |
| petfooddistops.metrics.stockout | stockout rate | MEASUREMENT | Stockout rate tracks unavailable food or supplies by category. | Guides procurement. |
| petfooddistops.metrics.delivery_completion | delivery completion | MEASUREMENT | Completion tracks requested, attempted, completed and failed deliveries. | Measures outreach. |
| petfooddistops.review.after_action | after-action review | METHOD | Review captures eligibility, donations, storage, delivery safety and shortage lessons. | Improves future support. |
