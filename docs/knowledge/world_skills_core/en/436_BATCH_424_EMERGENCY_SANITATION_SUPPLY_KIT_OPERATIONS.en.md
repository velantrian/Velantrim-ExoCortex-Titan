# BATCH 424: Emergency Sanitation Supply Kit Operations

**KnowledgeUnits:** 44  
**Namespace:** `sanitationkitops.*`  
**Scope:** contents, assembly, eligibility, storage, distribution, safety messages and inventory.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| sanitationkitops.activation.trigger | activation trigger | MODEL | Trigger includes displacement, sewage disruption, cleanup work, sheltering or hygiene shortage. | Starts kit operation. |
| sanitationkitops.activation.service_area | service area | RECORD | Area defines neighborhoods, shelters, cleanup zones and partner distribution routes. | Focuses supply. |
| sanitationkitops.activation.partner | partner roster | RECORD | Roster lists public health, warehouses, nonprofits, shelters and cleanup teams. | Coordinates capacity. |
| sanitationkitops.activation.command_link | command link | RECORD | Operation reports to logistics, public health, sheltering and public information. | Maintains oversight. |
| sanitationkitops.contents.item_master | item master | RECORD | Master lists soap, sanitizer, gloves, masks, bags, wipes, bleach, towels and instructions. | Standardizes kits. |
| sanitationkitops.contents.required_items | required items | CONSTRAINT | Required items define minimum kit contents by use case. | Preserves quality. |
| sanitationkitops.contents.optional_items | optional items | RECORD | Optional items include diapers, menstrual supplies, cleanup tools or water treatment where appropriate. | Adapts kits. |
| sanitationkitops.contents.restriction | restricted item | SAFETY_RULE | Chemicals and sharp tools require handling warnings or may be excluded. | Reduces harm. |
| sanitationkitops.assembly.workstation | assembly workstation | METHOD | Workstation sets tables, bins, labels, counts and quality check point. | Speeds packing. |
| sanitationkitops.assembly.pick_list | pick list | RECORD | Pick list defines items, quantity, language inserts and kit type. | Guides volunteers. |
| sanitationkitops.assembly.batch_record | batch record | RECORD | Batch records date, kit type, quantity, staff and lot/source where needed. | Supports traceability. |
| sanitationkitops.assembly.quality_check | kit quality check | QUALITY_CHECK | Check verifies contents, sealed items, expiration and instruction sheet. | Prevents incomplete kits. |
| sanitationkitops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria define household impact, cleanup role, shelter status or partner referral. | Preserves fairness. |
| sanitationkitops.eligibility.frequency | frequency limit | CONSTRAINT | Limit defines kits per household or team per period. | Extends stock. |
| sanitationkitops.eligibility.exception | exception record | RECORD | Exception records medical, infant, large household or heavy cleanup need. | Allows flexibility. |
| sanitationkitops.eligibility.duplicate_check | duplicate check | QUALITY_CHECK | Check links prior issues, household and route delivery. | Prevents overissue. |
| sanitationkitops.storage.clean_storage | clean storage | SAFETY_RULE | Kits stay dry, pest-free, temperature-appropriate and separated from waste. | Preserves usability. |
| sanitationkitops.storage.chemical_separation | chemical separation | SAFETY_RULE | Chemicals are separated from food, medical items and incompatible products. | Prevents contamination. |
| sanitationkitops.storage.expiry_rotation | expiry rotation | METHOD | Short-dated items are issued first and expired items removed. | Reduces waste. |
| sanitationkitops.storage.security | stock security | SAFETY_RULE | High-demand items use supervised storage and counts. | Reduces loss. |
| sanitationkitops.distribution.pickup_flow | pickup flow | METHOD | Flow handles eligibility, queue, kit issue, safety message and receipt. | Serves residents. |
| sanitationkitops.distribution.delivery_request | delivery request | RECORD | Request captures address, kit type, access, contact and mobility barrier. | Enables delivery. |
| sanitationkitops.distribution.route_plan | route plan | METHOD | Route groups deliveries by geography, urgency and kit type. | Saves time. |
| sanitationkitops.distribution.issue_receipt | issue receipt | RECORD | Receipt records household/team, kit type, quantity, date and staff. | Supports inventory. |
| sanitationkitops.safety.instruction_sheet | instruction sheet | RECORD | Sheet explains safe use, hand hygiene, chemical dilution warnings and disposal. | Prevents misuse. |
| sanitationkitops.safety.bleach_warning | bleach warning | SAFETY_RULE | Warning says not to mix bleach with ammonia, acids or unknown cleaners. | Prevents toxic gas. |
| sanitationkitops.safety.ppe_message | PPE message | METHOD | Message explains gloves, mask limits, eye protection and handwashing. | Improves safety. |
| sanitationkitops.safety.waste_message | waste message | METHOD | Message explains bagging, debris separation, sharps and local disposal route. | Supports sanitation. |
| sanitationkitops.inventory.receiving | receiving check | QUALITY_CHECK | Receiving checks quantity, condition, expiration, labels and source. | Protects stock. |
| sanitationkitops.inventory.stock_count | stock count | MEASUREMENT | Count reconciles received, assembled, issued, damaged and remaining items. | Shows inventory. |
| sanitationkitops.inventory.shortage | shortage record | RECORD | Shortage records item, kit impact, substitute and procurement need. | Guides resupply. |
| sanitationkitops.inventory.reconciliation | reconciliation | QUALITY_CHECK | Reconciliation compares component stock with completed kits and issue records. | Detects errors. |
| sanitationkitops.communication.public_notice | public notice | METHOD | Notice states kit contents, eligibility, locations, limits and safety cautions. | Guides residents. |
| sanitationkitops.communication.partner_update | partner update | METHOD | Partners receive kit stock, shortages, pickup rules and delivery routes. | Aligns referrals. |
| sanitationkitops.communication.language | language support | METHOD | Inserts and signs use common local languages and pictograms. | Improves access. |
| sanitationkitops.communication.feedback | feedback process | METHOD | Feedback captures missing items, unclear instructions or access barriers. | Improves kits. |
| sanitationkitops.records.daily_log | daily log | RECORD | Log stores assembly count, distribution, deliveries, shortages and incidents. | Creates audit trail. |
| sanitationkitops.records.cost | cost record | RECORD | Cost tracks components, packing, transport, storage and labor. | Supports finance. |
| sanitationkitops.records.retention | retention rule | CONSTRAINT | Records follow emergency, grant, finance and public health schedules. | Preserves audit. |
| sanitationkitops.metrics.kits_issued | kits issued | MEASUREMENT | Count tracks kits issued by type, area and channel. | Shows output. |
| sanitationkitops.metrics.component_loss | component loss | MEASUREMENT | Loss tracks damaged, expired, missing or unusable components. | Improves control. |
| sanitationkitops.qa.sample_audit | sample audit | QUALITY_CHECK | Audit opens sample kits to verify contents and inserts. | Maintains quality. |
| sanitationkitops.demob.closeout | closeout | METHOD | Closeout transfers stock, reconciles inventory, archives logs and retires expired items. | Ends cleanly. |
| sanitationkitops.review.after_action | after-action review | METHOD | Review captures contents, safety messages, distribution, shortages and inventory lessons. | Improves future kits. |
