# BATCH 326: Water Service Line Inventory Operations

**KnowledgeUnits:** 44  
**Namespace:** `servicelineops.*`  
**Scope:** materials, customer side records, field verification, lead risk, notices and replacement planning.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| servicelineops.inventory.service_id | service line ID | RECORD | Each service has account, parcel, meter, curb stop, public side and customer side record. | Creates traceable unit for inventory and replacement. |
| servicelineops.inventory.material_status | material status | RECORD | Material is classified as lead, galvanized requiring replacement, copper, plastic, unknown or other. | Drives risk and compliance actions. |
| servicelineops.inventory.public_private | public-private split | CONSTRAINT | Ownership split between utility and customer side is recorded. | Replacement planning needs legal responsibility. |
| servicelineops.inventory.install_year | install year | RECORD | Install year, subdivision age or plumbing permit dates inform material probability. | Helps prioritize unknown services. |
| servicelineops.records.tap_card | tap card | RECORD | Tap cards may show original service material, size, date and location. | Historical records reduce field uncertainty. |
| servicelineops.records.plumbing_permit | plumbing permit review | METHOD | Permits reveal service replacements, meter moves or building plumbing changes. | Updates inventory without excavation. |
| servicelineops.records.meter_record | meter record | RECORD | Meter size, setter, pit, basement location and customer notes support verification. | Field crews know where to look. |
| servicelineops.records.confidence | confidence rating | MODEL | Confidence score reflects record quality, field evidence and consistency. | Separates verified from assumed material. |
| servicelineops.field.scratch_test | scratch test | METHOD | Scratch test checks color and hardness of exposed pipe. | Distinguishes lead, copper and plastic when accessible. |
| servicelineops.field.magnet_test | magnet test | METHOD | Magnet indicates ferrous galvanized or steel pipe. | Supports classification of non-lead but risky materials. |
| servicelineops.field.swab_test | lead swab | QUALITY_CHECK | Lead swab can support field identification but is not sole evidence. | Useful screening with limitations. |
| servicelineops.field.visual_meter | meter-area visual | INSPECTION | Pipe entering meter or wall is inspected where safely accessible. | Low-cost verification for interior services. |
| servicelineops.field.curb_stop | curb stop verification | METHOD | Curb stop excavation or vacuum potholing can reveal public-side material. | Confirms buried segment when records are weak. |
| servicelineops.field.potholing | potholing | METHOD | Vacuum excavation exposes service with less damage than open trench. | Verifies material before replacement design. |
| servicelineops.field.safety | field safety | SAFETY_RULE | Crews manage traffic, excavation, utilities, confined spaces and customer property. | Inventory work still has construction risks. |
| servicelineops.customer.self_report | customer self-report | METHOD | Customers submit photos or forms of visible service material. | Expands inventory coverage quickly. |
| servicelineops.customer.photo_guidance | photo guidance | METHOD | Instructions show where to photograph pipe, scratch area and meter context. | Improves quality of self-reported data. |
| servicelineops.customer.access_appointment | access appointment | METHOD | Appointments coordinate interior inspections, language needs and safety. | Reduces missed visits. |
| servicelineops.customer.privacy | privacy handling | SAFETY_RULE | Customer photos and interior access data are handled with privacy controls. | Maintains trust and legal compliance. |
| servicelineops.leadrisk.lead_gooseneck | lead gooseneck | RECORD | Lead connectors or goosenecks are recorded even when main service is not lead. | Small components can still create lead risk. |
| servicelineops.leadrisk.galvanized_downstream | galvanized downstream | MODEL | Galvanized pipe downstream of lead can accumulate lead scale. | May require replacement classification. |
| servicelineops.leadrisk.unknown_priority | unknown priority | DECISION_RULE | Unknowns are prioritized by age, neighborhood, vulnerable populations and records. | Reduces highest-risk uncertainty first. |
| servicelineops.leadrisk.disturbance | disturbance risk | SAFETY_RULE | Construction or partial replacement can release lead particles. | Requires flushing, filters or notices. |
| servicelineops.notices.initial_notice | initial notice | METHOD | Customers are notified of known or unknown service material and health information. | Supports transparency and compliance. |
| servicelineops.notices.replacement_notice | replacement notice | METHOD | Replacement notices explain schedule, access, cost, ownership and post-work steps. | Helps customers participate. |
| servicelineops.notices.filter | filter notice | METHOD | Filters may be provided or recommended after lead work or disturbance. | Reduces exposure during transition. |
| servicelineops.notices.language_access | language access | METHOD | Notices use plain language and translation where needed. | Improves participation and equity. |
| servicelineops.replacement.full_replacement | full replacement | METHOD | Full replacement removes lead from public and customer side in one coordinated project. | Avoids risks of partial replacement. |
| servicelineops.replacement.partial | partial replacement | FAILURE_MODE | Partial replacement can leave lead and disturb scale. | Often requires extra risk controls. |
| servicelineops.replacement.bundle | bundle projects | METHOD | Replacements are bundled with paving, main replacement or neighborhood projects. | Reduces cost and disruption. |
| servicelineops.replacement.contractor | contractor management | METHOD | Contractors need specs, customer coordination, restoration and data return requirements. | Replacement data must update inventory. |
| servicelineops.replacement.restoration | restoration | QUALITY_CHECK | Pavement, sidewalk, lawn and interior penetrations are restored after work. | Customer acceptance depends on site restoration. |
| servicelineops.funding.grant | grant tracking | RECORD | Grants track eligible costs, match, addresses, procurement and reporting. | Supports affordability of replacements. |
| servicelineops.funding.customer_cost | customer cost policy | DECISION_RULE | Utility policy defines whether customer-side replacement is free, shared or financed. | Impacts participation and equity. |
| servicelineops.funding.priority_equity | equity priority | MODEL | Priority may consider children, schools, income, lead levels and disadvantaged areas. | Targets replacement where benefit is greatest. |
| servicelineops.data.database | inventory database | RECORD | Database stores material, evidence, confidence, dates, photos and replacement status. | Single source of truth for program. |
| servicelineops.data.gis_layer | GIS layer | RECORD | GIS maps service status by parcel, main and project area. | Visualizes unknown clusters and replacement progress. |
| servicelineops.data.qa | data QA | QUALITY_CHECK | QA checks duplicates, impossible materials, missing evidence and public/private mismatch. | Keeps inventory defensible. |
| servicelineops.data.public_map | public map | METHOD | Public-facing map or lookup shares service status with customers. | Builds transparency. |
| servicelineops.sampling.lead_sample | lead sampling link | RECORD | Water lead results are linked to service material and premise plumbing notes. | Helps interpret exposure and corrosion control. |
| servicelineops.sampling.post_replacement | post-replacement sampling | QUALITY_CHECK | Samples after replacement verify lead reduction and detect disturbance. | Confirms project outcome. |
| servicelineops.reporting.compliance | compliance report | RECORD | Report summarizes lead, galvanized, unknown, replaced and notices. | Meets regulatory and management needs. |
| servicelineops.reporting.progress | progress dashboard | RECORD | Dashboard tracks verifications, replacements, funding and customer participation. | Shows whether program is moving. |
| servicelineops.review.lessons | lessons learned | METHOD | Program reviews records quality, customer response, contractor issues and lead results. | Improves next replacement phase. |
