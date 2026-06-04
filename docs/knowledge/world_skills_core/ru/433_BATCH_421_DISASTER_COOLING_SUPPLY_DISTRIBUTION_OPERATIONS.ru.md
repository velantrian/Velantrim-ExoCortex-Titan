# BATCH 421: Disaster Cooling Supply Distribution Operations

**KnowledgeUnits:** 44  
**Namespace:** `coolingsupplyops.*`  
**Scope:** fans, ice, water, shade kits, eligibility, delivery, safety and reconciliation.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| coolingsupplyops.activation.trigger | activation trigger | MODEL | Trigger includes heat wave, power outage, wildfire smoke, sheltering or medical risk. | Starts cooling support. |
| coolingsupplyops.activation.service_area | service area | RECORD | Area defines neighborhoods, shelters, routes, jurisdictions and priority zones. | Focuses resources. |
| coolingsupplyops.activation.partner | partner roster | RECORD | Roster lists public health, utilities, nonprofits, warehouses and delivery partners. | Coordinates capacity. |
| coolingsupplyops.activation.command_link | command link | RECORD | Operation reports to public health, logistics, sheltering, safety and public information. | Maintains oversight. |
| coolingsupplyops.intake.request_source | request source | RECORD | Source records hotline, outreach, clinic, utility, shelter, caseworker or self-request. | Shows demand. |
| coolingsupplyops.intake.household | household profile | RECORD | Profile captures residents, address, heat risk, power status, mobility and contact. | Defines need. |
| coolingsupplyops.intake.medical_risk | medical risk flag | SAFETY_RULE | Risk flags oxygen, heat-sensitive illness, medications, infants, elders or disability. | Prioritizes support. |
| coolingsupplyops.intake.urgency | urgency model | MODEL | Urgency weighs indoor temperature, outage duration, medical risk, isolation and transport. | Orders work. |
| coolingsupplyops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria define heat risk, disaster impact, location, income or referral requirements. | Preserves fairness. |
| coolingsupplyops.eligibility.frequency | frequency limit | CONSTRAINT | Limit defines how often household can receive ice, water or kits. | Extends supply. |
| coolingsupplyops.eligibility.exception | exception record | RECORD | Exception records urgent medical or access need and supervisor approval. | Allows flexibility. |
| coolingsupplyops.eligibility.duplicate_check | duplicate check | QUALITY_CHECK | Check links repeated requests and prior deliveries. | Prevents double issue. |
| coolingsupplyops.inventory.item_master | item master | RECORD | Master lists fans, ice, water, cooling towels, shade kits and batteries. | Standardizes stock. |
| coolingsupplyops.inventory.receiving | receiving check | QUALITY_CHECK | Receiving checks quantity, condition, temperature where relevant, source and date. | Protects supply. |
| coolingsupplyops.inventory.cold_chain | ice cold chain | METHOD | Ice handling tracks freezer, cooler, melt loss and distribution timing. | Maintains usefulness. |
| coolingsupplyops.inventory.stock_count | stock count | MEASUREMENT | Count reconciles received, issued, delivered, melted, damaged and remaining items. | Shows availability. |
| coolingsupplyops.issue.standard_kit | standard kit | METHOD | Standard kit bundles water, fan, shade or cooling items by household need. | Speeds distribution. |
| coolingsupplyops.issue.fan_safety | fan safety | SAFETY_RULE | Fan issue checks power availability, cord safety and placement warnings. | Prevents harm. |
| coolingsupplyops.issue.ice_handling | ice handling | SAFETY_RULE | Ice is handled to avoid contamination and unsafe storage. | Protects users. |
| coolingsupplyops.issue.receipt | issue receipt | RECORD | Receipt records household, items, quantity, date, staff and exception. | Supports inventory. |
| coolingsupplyops.delivery.route_plan | route plan | METHOD | Route groups deliveries by urgency, geography, cold-chain timing and vehicle capacity. | Saves time. |
| coolingsupplyops.delivery.access_check | access check | METHOD | Check covers stairs, gate, elevator, pets, contact window and safe drop-off. | Prevents failed delivery. |
| coolingsupplyops.delivery.no_contact | no-contact handling | METHOD | Policy defines leave, retry, hold or return based on item type and safety. | Controls loss. |
| coolingsupplyops.delivery.confirmation | delivery confirmation | RECORD | Confirmation records delivered items, time, recipient and unresolved needs. | Closes handoff. |
| coolingsupplyops.safety.heat_message | heat safety message | METHOD | Message covers hydration, cooling center, warning signs and emergency escalation. | Reduces illness. |
| coolingsupplyops.safety.power_warning | power warning | SAFETY_RULE | Residents are warned not to overload outlets or use unsafe generators. | Prevents fire/CO risk. |
| coolingsupplyops.safety.worker_heat | worker heat safety | SAFETY_RULE | Staff follow hydration, shade, rest, buddy checks and symptom reporting. | Protects teams. |
| coolingsupplyops.safety.escalation | medical escalation | SAFETY_RULE | Severe heat symptoms route to emergency medical response. | Prevents death. |
| coolingsupplyops.communication.public_notice | public notice | METHOD | Notice states items, eligibility, pickup/delivery, hours and cooling center links. | Guides residents. |
| coolingsupplyops.communication.partner_update | partner update | METHOD | Partners receive stock levels, urgent cases, route barriers and shortages. | Aligns response. |
| coolingsupplyops.communication.language | language support | METHOD | Heat safety and request scripts use common local languages and icons. | Improves access. |
| coolingsupplyops.communication.shortage | shortage message | METHOD | Shortage message explains limits, substitutions, next delivery and cooling alternatives. | Reduces conflict. |
| coolingsupplyops.records.daily_log | daily log | RECORD | Log stores requests, stock, deliveries, incidents, melt loss and unmet needs. | Creates audit trail. |
| coolingsupplyops.records.cost | cost record | RECORD | Costs track purchased items, transport, storage, labor and equipment. | Supports finance. |
| coolingsupplyops.records.retention | retention rule | CONSTRAINT | Records follow emergency, grant, privacy and finance schedules. | Preserves audit. |
| coolingsupplyops.records.donation | donation record | RECORD | Donation record captures donor, item type, quantity, restriction and disposition. | Maintains accountability. |
| coolingsupplyops.records.incident | incident report | RECORD | Incident records heat illness, injury, conflict, spoiled stock or delivery problem. | Supports review. |
| coolingsupplyops.reconcile.inventory | inventory reconciliation | QUALITY_CHECK | Reconciliation compares receipts, issues, deliveries, losses and remaining stock. | Detects variance. |
| coolingsupplyops.metrics.households_served | households served | MEASUREMENT | Count tracks households and high-risk residents served by area. | Shows reach. |
| coolingsupplyops.metrics.stockout | stockout rate | MEASUREMENT | Rate tracks unavailable fans, ice, water or kits by period. | Guides procurement. |
| coolingsupplyops.metrics.delivery_time | delivery time | MEASUREMENT | Time measures request to delivery for urgent and routine cases. | Reveals delay. |
| coolingsupplyops.qa.case_review | case review | QUALITY_CHECK | Review checks eligibility, urgent flags, issue records and delivery confirmation. | Improves reliability. |
| coolingsupplyops.demob.closeout | closeout | METHOD | Closeout transfers remaining stock, closes routes, archives logs and returns equipment. | Ends operation. |
| coolingsupplyops.review.after_action | after-action review | METHOD | Review captures eligibility, cold-chain, delivery access, heat safety and stock lessons. | Improves future cooling. |
