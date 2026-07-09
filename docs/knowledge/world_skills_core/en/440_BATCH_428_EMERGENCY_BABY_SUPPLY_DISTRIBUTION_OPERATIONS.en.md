# BATCH 428: Emergency Baby Supply Distribution Operations

**KnowledgeUnits:** 44  
**Namespace:** `babysupplyops.*`  
**Scope:** diapers, formula, wipes, intake, eligibility, safe messaging, inventory and delivery.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| babysupplyops.activation.trigger | activation trigger | MODEL | Trigger includes displacement, income shock, store closure, formula shortage or sheltering. | Starts baby support. |
| babysupplyops.activation.partner | partner roster | RECORD | Roster lists food banks, clinics, WIC partners, shelters, donors and delivery teams. | Coordinates supply. |
| babysupplyops.activation.service_area | service area | RECORD | Area defines eligible shelters, neighborhoods, routes and jurisdictions. | Focuses resources. |
| babysupplyops.activation.command_link | command link | RECORD | Operation reports to logistics, public health, family services and donations. | Maintains oversight. |
| babysupplyops.intake.caregiver | caregiver intake | RECORD | Intake captures caregiver, infant count, age, contact, language and pickup/delivery need. | Defines request. |
| babysupplyops.intake.child_profile | child profile | RECORD | Profile records age, size, feeding type, allergies and special care notes. | Selects supplies. |
| babysupplyops.intake.urgent_need | urgent need | MODEL | Urgency weighs no formula, no diapers, medical need, transport barrier and infant age. | Prioritizes cases. |
| babysupplyops.intake.privacy | privacy rule | SAFETY_RULE | Family and infant data is collected only for distribution and referral. | Protects household. |
| babysupplyops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria define disaster impact, caregiver status, service area and frequency. | Preserves fairness. |
| babysupplyops.eligibility.verification | verification method | METHOD | Verification can use self-attestation, shelter roster, clinic referral or benefits desk. | Keeps access humane. |
| babysupplyops.eligibility.frequency | frequency limit | CONSTRAINT | Limit defines diapers, wipes or formula amount per period. | Extends stock. |
| babysupplyops.eligibility.exception | exception record | RECORD | Exception records twins, medical need, lost supplies or urgent feeding risk. | Allows flexibility. |
| babysupplyops.inventory.item_master | item master | RECORD | Master lists diaper sizes, wipes, formula types, bottles, hygiene and baby food. | Standardizes stock. |
| babysupplyops.inventory.receiving | receiving check | QUALITY_CHECK | Receiving checks expiration, seal, recall, condition, source and quantity. | Protects infants. |
| babysupplyops.inventory.formula_lot | formula lot | RECORD | Formula lot records brand, type, lot, expiration and recall status. | Enables recall. |
| babysupplyops.inventory.stock_count | stock count | MEASUREMENT | Count tracks received, issued, damaged, expired and remaining supplies. | Shows availability. |
| babysupplyops.storage.clean_storage | clean storage | SAFETY_RULE | Baby supplies stay dry, clean, pest-free and separated from chemicals. | Preserves safety. |
| babysupplyops.storage.temperature | temperature control | SAFETY_RULE | Formula and baby food follow storage temperature and expiration guidance. | Prevents spoilage. |
| babysupplyops.storage.recall_hold | recall hold | METHOD | Recalled or suspect products are held and not issued. | Prevents harm. |
| babysupplyops.storage.security | stock security | SAFETY_RULE | High-demand formula and diapers use supervised storage and counts. | Reduces loss. |
| babysupplyops.issue.standard_bundle | standard bundle | METHOD | Bundle combines diapers, wipes and feeding/hygiene items by child age and need. | Speeds handoff. |
| babysupplyops.issue.formula_match | formula match | SAFETY_RULE | Formula type matches caregiver report; substitutions include safe messaging and referral. | Reduces feeding risk. |
| babysupplyops.issue.receipt | issue receipt | RECORD | Receipt records caregiver, child age/size, items, quantity, date and staff. | Supports inventory. |
| babysupplyops.issue.referral | referral path | METHOD | Feeding, medical or benefits concerns route to clinic, WIC or public health. | Adds expertise. |
| babysupplyops.delivery.delivery_request | delivery request | RECORD | Request captures address, contact, infant needs, access and time window. | Enables outreach. |
| babysupplyops.delivery.route_plan | route plan | METHOD | Route groups deliveries by urgency, area, formula type and vehicle capacity. | Saves time. |
| babysupplyops.delivery.no_contact | no-contact handling | METHOD | Policy defines retry, hold, partner handoff or safe drop-off restrictions. | Controls loss. |
| babysupplyops.delivery.confirmation | delivery confirmation | RECORD | Confirmation records recipient, items, time and unresolved needs. | Closes handoff. |
| babysupplyops.safety.safe_prep | safe preparation message | METHOD | Message covers clean water, hand hygiene, formula preparation and storage basics. | Protects infants. |
| babysupplyops.safety.breastfeeding_support | breastfeeding support | METHOD | Families needing lactation support are referred without pressure or stigma. | Supports choice. |
| babysupplyops.safety.recall_message | recall message | SAFETY_RULE | Recall instructions explain product check, hold and replacement pathway. | Prevents unsafe use. |
| babysupplyops.safety.water_warning | water warning | SAFETY_RULE | Unsafe water conditions trigger public health guidance for feeding preparation. | Reduces illness. |
| babysupplyops.communication.public_notice | public notice | METHOD | Notice states items, eligibility, pickup/delivery, limits and safety guidance. | Guides caregivers. |
| babysupplyops.communication.partner_update | partner update | METHOD | Partners receive stock levels, urgent needs, recalls, shortages and referral rules. | Aligns support. |
| babysupplyops.communication.language | language support | METHOD | Scripts and inserts use common local languages and pictograms. | Improves access. |
| babysupplyops.records.daily_log | daily log | RECORD | Log stores requests, stock, issues, deliveries, recalls and unmet needs. | Creates audit trail. |
| babysupplyops.records.cost | cost record | RECORD | Costs track purchased supplies, transport, storage and labor. | Supports finance. |
| babysupplyops.records.retention | retention rule | CONSTRAINT | Distribution, recall, finance and privacy records follow retention schedules. | Preserves audit. |
| babysupplyops.metrics.children_served | children served | MEASUREMENT | Count tracks children served by age, item type and area. | Shows reach. |
| babysupplyops.metrics.stockout | stockout rate | MEASUREMENT | Rate tracks diaper size, formula type or wipe shortages. | Guides procurement. |
| babysupplyops.metrics.delivery_time | delivery time | MEASUREMENT | Time measures request to pickup or delivery completion. | Reveals delay. |
| babysupplyops.qa.sample_review | sample review | QUALITY_CHECK | Review checks eligibility, formula lot, issue receipt and referral notes. | Improves reliability. |
| babysupplyops.demob.closeout | closeout | METHOD | Closeout transfers stock, archives logs, resolves recalls and closes deliveries. | Ends operation. |
| babysupplyops.review.after_action | after-action review | METHOD | Review captures formula safety, diaper sizes, delivery gaps, referrals and inventory lessons. | Improves future support. |
