# BATCH 392: Disaster Field Kitchen Sanitation Inspection Operations

**KnowledgeUnits:** 44  
**Namespace:** `fieldkitcheninspectops.*`  
**Scope:** inspections, temperatures, handwashing, waste, corrective actions and closure.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| fieldkitcheninspectops.activation.trigger | inspection trigger | MODEL | Trigger includes mass feeding, mobile kitchen setup, complaints, illness signal or new site. | Starts food safety oversight. |
| fieldkitcheninspectops.activation.inspector | inspector assignment | RECORD | Assignment names inspector, site, shift, authority and contact. | Clarifies responsibility. |
| fieldkitcheninspectops.activation.risk_level | risk level | MODEL | Risk level considers meal volume, vulnerable diners, menu, temperature and water. | Sets inspection frequency. |
| fieldkitcheninspectops.activation.checklist | checklist | RECORD | Checklist covers receiving, storage, prep, cooking, holding, service and waste. | Standardizes inspection. |
| fieldkitcheninspectops.site.water | water supply | SAFETY_RULE | Kitchen uses approved potable water or safe alternate method. | Prevents contamination. |
| fieldkitcheninspectops.site.wastewater | wastewater disposal | CONSTRAINT | Wastewater drains to approved sewer, tank or disposal route. | Protects environment. |
| fieldkitcheninspectops.site.pest_control | pest control | QUALITY_CHECK | Food, waste and openings are checked for pest attraction. | Protects food. |
| fieldkitcheninspectops.site.layout | layout check | METHOD | Layout separates raw, cooked, waste, handwash and service flows. | Reduces cross-contamination. |
| fieldkitcheninspectops.receiving.source | approved source | SAFETY_RULE | Food must come from approved supplier, donation pathway or inspected source. | Reduces unsafe food entry. |
| fieldkitcheninspectops.receiving.condition | receiving condition | QUALITY_CHECK | Inspector checks temperature, packaging, spoilage, labels and dates. | Blocks unsafe supplies. |
| fieldkitcheninspectops.receiving.lot_trace | lot trace | RECORD | Lot/source data is kept for high-risk foods. | Enables recall. |
| fieldkitcheninspectops.receiving.rejection | rejection record | RECORD | Rejected food records item, reason, quantity and disposal/return. | Supports accountability. |
| fieldkitcheninspectops.temperature.cooking | cooking temperature | SAFETY_RULE | Critical foods must reach required internal temperature. | Prevents foodborne illness. |
| fieldkitcheninspectops.temperature.hot_hold | hot holding | SAFETY_RULE | Hot held foods remain above required threshold or are discarded. | Keeps meals safe. |
| fieldkitcheninspectops.temperature.cold_hold | cold holding | SAFETY_RULE | Cold foods remain below required threshold or corrective action begins. | Prevents bacterial growth. |
| fieldkitcheninspectops.temperature.cooling | cooling control | SAFETY_RULE | Cooling follows time/temperature limits when leftovers are retained. | Prevents unsafe reuse. |
| fieldkitcheninspectops.temperature.temp_log | temperature log | RECORD | Logs record food, time, reading, staff and corrective action. | Provides evidence. |
| fieldkitcheninspectops.temperature.thermometer | thermometer check | QUALITY_CHECK | Thermometers are available, clean and checked for accuracy. | Ensures valid readings. |
| fieldkitcheninspectops.hygiene.handwash | handwashing station | SAFETY_RULE | Handwashing has water, soap, towels and waste container. | Enables hygiene. |
| fieldkitcheninspectops.hygiene.glove_use | glove use | METHOD | Gloves are used with handwashing and changed between tasks. | Reduces contamination. |
| fieldkitcheninspectops.hygiene.ill_worker | ill worker exclusion | SAFETY_RULE | Ill or symptomatic food workers are excluded or reassigned. | Prevents outbreaks. |
| fieldkitcheninspectops.hygiene.personal_items | personal item control | METHOD | Personal items are kept away from food prep and service. | Maintains sanitation. |
| fieldkitcheninspectops.crosscontam.raw_separation | raw separation | SAFETY_RULE | Raw animal foods are separated from ready-to-eat foods. | Prevents cross-contamination. |
| fieldkitcheninspectops.crosscontam.utensil | utensil control | METHOD | Utensils, boards and pans are separated, cleaned or sanitized by task. | Reduces transfer. |
| fieldkitcheninspectops.crosscontam.allergen | allergen check | SAFETY_RULE | Allergen foods are labeled and handled to limit cross-contact where feasible. | Protects diners. |
| fieldkitcheninspectops.crosscontam.chemical | chemical storage | SAFETY_RULE | Chemicals are labeled and stored away from food and utensils. | Prevents poisoning. |
| fieldkitcheninspectops.waste.trash | trash handling | METHOD | Trash is covered, removed and kept away from prep areas. | Reduces pests. |
| fieldkitcheninspectops.waste.grease | grease handling | CONSTRAINT | Grease is collected and disposed through approved route. | Prevents spills and sewer issues. |
| fieldkitcheninspectops.waste.spoiled_food | spoiled food disposal | SAFETY_RULE | Spoiled or temperature-abused food is discarded and recorded. | Prevents service. |
| fieldkitcheninspectops.waste.waste_log | waste log | RECORD | Waste log records discarded food, reason and quantity. | Shows loss and safety action. |
| fieldkitcheninspectops.corrective.violation | violation record | RECORD | Violation records finding, rule, severity, corrective action and deadline. | Creates follow-up. |
| fieldkitcheninspectops.corrective.immediate | immediate correction | METHOD | Critical violations are corrected during inspection or service stops. | Protects diners. |
| fieldkitcheninspectops.corrective.reinspection | reinspection | QUALITY_CHECK | Reinspection verifies correction of major issues. | Confirms safety. |
| fieldkitcheninspectops.corrective.closure | closure authority | SAFETY_RULE | Unsafe kitchen can be closed or restricted under authority. | Prevents harm. |
| fieldkitcheninspectops.communication.manager_brief | manager briefing | METHOD | Inspector explains findings, corrections and documentation to kitchen lead. | Improves compliance. |
| fieldkitcheninspectops.communication.command_update | command update | METHOD | Command receives critical violations, closures, illness signals and resource needs. | Maintains situational awareness. |
| fieldkitcheninspectops.communication.public_risk | public risk message | METHOD | Public notice may be needed for recall, illness or service change. | Protects consumers. |
| fieldkitcheninspectops.records.inspection_form | inspection form | RECORD | Form stores site, findings, temperatures, photos, actions and signatures. | Preserves evidence. |
| fieldkitcheninspectops.records.photo | photo record | RECORD | Photos document violations, corrections, layout and equipment issues. | Supports review. |
| fieldkitcheninspectops.records.retention | retention rule | CONSTRAINT | Inspection records follow health, emergency and legal schedules. | Keeps audit trail. |
| fieldkitcheninspectops.metrics.violation_rate | violation rate | MEASUREMENT | Rate tracks violations by site, severity and category. | Targets training. |
| fieldkitcheninspectops.metrics.inspection_coverage | inspection coverage | MEASUREMENT | Coverage shows inspected kitchens versus active feeding sites. | Finds oversight gaps. |
| fieldkitcheninspectops.demob.final_inspection | final inspection | QUALITY_CHECK | Final inspection checks food disposition, cleaning, waste and equipment. | Closes site safely. |
| fieldkitcheninspectops.review.after_action | after-action review | METHOD | Review captures water, temperature, staffing, donations and correction lessons. | Improves future feeding. |
