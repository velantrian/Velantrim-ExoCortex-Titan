# BATCH 394: Disaster Household Cleanup Kit Distribution Operations

**KnowledgeUnits:** 44  
**Namespace:** `cleanupkitops.*`  
**Scope:** kit assembly, eligibility, safety instructions, inventory, delivery and feedback.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| cleanupkitops.activation.trigger | kit trigger | MODEL | Trigger includes flood, smoke, mold, sewage, wind debris or household contamination. | Starts cleanup kit support. |
| cleanupkitops.activation.kit_standard | kit standard | RECORD | Standard defines contents, quantities, safety notes and eligible use. | Keeps kits consistent. |
| cleanupkitops.activation.partner | partner roles | RECORD | Partners include public health, nonprofits, donations, logistics and waste services. | Coordinates support. |
| cleanupkitops.activation.risk_review | risk review | SAFETY_RULE | Public health/safety reviews whether cleanup should be resident-safe or professional-only. | Prevents dangerous self-cleanup. |
| cleanupkitops.contents.gloves | gloves | RECORD | Gloves are sized and chosen for chemical, debris or hygiene risks. | Protects hands. |
| cleanupkitops.contents.masks | respiratory protection | CONSTRAINT | Masks are included with clear limits and escalation for heavy mold/asbestos/smoke. | Avoids false protection. |
| cleanupkitops.contents.cleaner | cleaner | RECORD | Cleaner/disinfectant item includes label, dilution and hazard instructions. | Supports safe use. |
| cleanupkitops.contents.tools | hand tools | RECORD | Tools may include scrub brush, bucket, trash bags, squeegee or shovel. | Enables basic cleanup. |
| cleanupkitops.assembly.work_order | assembly work order | RECORD | Work order lists kit type, quantity, contents, staff and date. | Controls production. |
| cleanupkitops.assembly.line_setup | assembly line | METHOD | Line setup stages items in sequence with count checks. | Speeds packing. |
| cleanupkitops.assembly.quality_check | kit quality check | QUALITY_CHECK | Sample kits are checked for missing, damaged or wrong items. | Prevents bad distribution. |
| cleanupkitops.assembly.label | kit label | METHOD | Label shows kit type, language, safety warnings and contact. | Helps users. |
| cleanupkitops.eligibility.affected_area | affected area | CONSTRAINT | Eligibility may depend on address in impacted zone or damage report. | Targets limited supplies. |
| cleanupkitops.eligibility.household_limit | household limit | CONSTRAINT | Limits define number of kits per household or structure. | Extends stock. |
| cleanupkitops.eligibility.priority | priority | MODEL | Priority considers elderly, disability, low income, flood depth and health risk. | Improves equity. |
| cleanupkitops.eligibility.exception | exception approval | METHOD | Exceptions document special household size, shared housing or severe damage. | Adds flexibility. |
| cleanupkitops.inventory.item_stock | item stock | MEASUREMENT | Stock tracks components, completed kits, damaged goods and reserve. | Shows capacity. |
| cleanupkitops.inventory.lot_trace | lot trace | RECORD | Cleaner/disinfectant lots are tracked for recall or safety alert. | Supports traceability. |
| cleanupkitops.inventory.reorder | reorder trigger | MODEL | Reorder uses demand, assembly rate, supplier lead time and reserve. | Prevents kit gaps. |
| cleanupkitops.inventory.storage | storage condition | SAFETY_RULE | Chemicals and PPE are stored away from heat, children, food and incompatibles. | Prevents accidents. |
| cleanupkitops.distribution.site | distribution site | METHOD | Site uses queue, signage, stock area, safety table and loading path. | Makes pickup orderly. |
| cleanupkitops.distribution.delivery | delivery route | METHOD | Delivery supports homebound, isolated or high-priority households. | Reaches vulnerable residents. |
| cleanupkitops.distribution.proof | issue proof | RECORD | Proof records household/address or count, kit type, date and staff. | Supports accountability. |
| cleanupkitops.distribution.partner_pickup | partner pickup | METHOD | Partners can receive kits for assigned neighborhoods with logs. | Expands reach. |
| cleanupkitops.safety.instructions | safety instructions | SAFETY_RULE | Instructions warn about electricity, gas, structural damage, mold, chemicals and PPE limits. | Prevents injury. |
| cleanupkitops.safety.chemical | chemical mixing warning | SAFETY_RULE | Instructions warn not to mix bleach, ammonia, acids or unknown cleaners. | Prevents toxic gas. |
| cleanupkitops.safety.mold_limit | mold limit | CONSTRAINT | Heavy mold, sewage, asbestos or structural hazard requires professional guidance. | Avoids unsafe DIY. |
| cleanupkitops.safety.child_pet | child and pet warning | SAFETY_RULE | Chemicals, sharp debris and contaminated items are kept from children and animals. | Protects households. |
| cleanupkitops.communication.public_notice | public notice | METHOD | Notice states kit sites, eligibility, contents, limits and safety warnings. | Guides residents. |
| cleanupkitops.communication.language | language support | METHOD | Instructions use translated sheets, icons or hotline support. | Improves safe use. |
| cleanupkitops.communication.hotline | hotline route | METHOD | Questions route to public health, cleanup help or disaster assistance line. | Supports correct use. |
| cleanupkitops.communication.feedback | feedback channel | METHOD | Users report missing items, safety concerns or unmet needs. | Improves kits. |
| cleanupkitops.records.assembly_log | assembly log | RECORD | Log records quantities built, staff, component lots and quality checks. | Creates evidence. |
| cleanupkitops.records.issue_log | issue log | RECORD | Issue log tracks sites, deliveries, partner pickups and remaining stock. | Controls distribution. |
| cleanupkitops.records.cost | cost record | RECORD | Costs track components, labor, transport, donations and storage. | Supports finance. |
| cleanupkitops.records.retention | retention rule | CONSTRAINT | Records follow donation, finance, public health and emergency schedules. | Preserves audit trail. |
| cleanupkitops.qa.safety_review | safety review | QUALITY_CHECK | Public health reviews instructions after incidents or questions. | Improves harm prevention. |
| cleanupkitops.qa.inventory_reconcile | inventory reconciliation | QUALITY_CHECK | Components, completed kits and issued kits reconcile. | Detects loss/error. |
| cleanupkitops.metrics.kits_issued | kits issued | MEASUREMENT | Kits issued by area and household type show reach. | Guides resupply. |
| cleanupkitops.metrics.unmet_need | unmet need | MEASUREMENT | Unmet need records turnaways, delivery requests and missing items. | Reveals gaps. |
| cleanupkitops.demob.remaining_stock | remaining stock | METHOD | Remaining kits transfer to cache, partner, future program or disposal. | Avoids waste. |
| cleanupkitops.demob.site_close | site closeout | METHOD | Site closeout removes materials, cleans area and updates public notice. | Ends distribution responsibly. |
| cleanupkitops.review.after_action | after-action review | METHOD | Review captures kit contents, safety clarity, demand and delivery issues. | Improves future cleanup support. |
| cleanupkitops.governance.kit_owner | kit owner | RECORD | Owner coordinates public health, logistics, donations and finance for cleanup kits. | Keeps accountability clear. |
