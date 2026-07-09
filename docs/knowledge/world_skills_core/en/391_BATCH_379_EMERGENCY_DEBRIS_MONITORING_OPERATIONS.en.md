# BATCH 379: Emergency Debris Monitoring Operations

**KnowledgeUnits:** 44  
**Namespace:** `debrismonitorops.*`  
**Scope:** load tickets, truck certification, route checks, disposal site monitors, disputes and audit.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| debrismonitorops.activation.monitor_plan | monitor plan | RECORD | Plan defines zones, contractors, monitors, disposal sites and reporting cadence. | Controls debris oversight. |
| debrismonitorops.activation.role_roster | role roster | RECORD | Roster lists field, tower, disposal, QA and supervisor monitors. | Assigns accountability. |
| debrismonitorops.activation.safety_brief | safety briefing | SAFETY_RULE | Brief covers traffic, heavy equipment, dust, heat, unstable piles and PPE. | Protects monitors. |
| debrismonitorops.activation.map_book | map book | RECORD | Map book shows eligible roads, zones, disposal sites and restricted areas. | Prevents ineligible pickup. |
| debrismonitorops.truck.cert_id | truck certification ID | RECORD | Certification links truck, owner, plate, capacity, photos and date. | Establishes legal hauling capacity. |
| debrismonitorops.truck.capacity_measure | capacity measure | MEASUREMENT | Capacity is measured in cubic yards or approved unit. | Supports payment accuracy. |
| debrismonitorops.truck.photo | truck photo | RECORD | Photos document bed, sideboards, plate and markings. | Detects altered capacity. |
| debrismonitorops.truck.decertify | decertification | METHOD | Truck is removed when modified, unsafe, duplicate or unauthorized. | Prevents bad tickets. |
| debrismonitorops.load.ticket_id | load ticket ID | RECORD | Ticket links truck, monitor, origin, debris type, time, destination and volume. | Creates payment evidence. |
| debrismonitorops.load.origin | load origin | RECORD | Origin records street, GPS, zone, parcel or right-of-way location. | Verifies eligibility. |
| debrismonitorops.load.debris_type | debris type | RECORD | Type distinguishes vegetative, construction, white goods, hazardous or mixed debris. | Routes disposal correctly. |
| debrismonitorops.load.fullness | fullness estimate | MEASUREMENT | Monitor estimates percentage of certified capacity loaded. | Determines payable volume. |
| debrismonitorops.route.route_check | route check | QUALITY_CHECK | Route checks compare truck path with eligible collection zones. | Detects ineligible hauling. |
| debrismonitorops.route.detour | detour note | RECORD | Detours record road closure, access issue or safety reason. | Explains route variation. |
| debrismonitorops.route.gps_log | GPS log | RECORD | GPS log supports origin, route and disposal verification where available. | Strengthens audit. |
| debrismonitorops.route.repeat_load | repeat load flag | MODEL | Repeat load patterns can signal duplicate ticketing or short hauling. | Targets review. |
| debrismonitorops.disposal.site_entry | disposal entry | METHOD | Site monitor confirms truck, ticket, debris type and arrival time. | Closes load chain. |
| debrismonitorops.disposal.tower_check | tower check | QUALITY_CHECK | Tower monitor estimates volume and load quality from safe vantage point. | Validates payment. |
| debrismonitorops.disposal.reduction | debris reduction | RECORD | Grinding, burning, chipping or compaction records input and output volumes. | Supports final accounting. |
| debrismonitorops.disposal.rejection | rejected load | RECORD | Rejection records contamination, unsafe material, wrong site or missing ticket. | Prevents improper disposal. |
| debrismonitorops.eligibility.row | right-of-way eligibility | CONSTRAINT | Public reimbursement often requires debris from eligible right-of-way or approved property. | Protects funding. |
| debrismonitorops.eligibility.private_property | private property debris | CONSTRAINT | Private property debris needs authorization and separate tracking. | Avoids claim errors. |
| debrismonitorops.eligibility.preexisting | preexisting debris | FAILURE_MODE | Preexisting debris can be mistaken for disaster debris. | Requires evidence review. |
| debrismonitorops.eligibility.hazardous | hazardous material route | SAFETY_RULE | Hazardous loads use specialist handling and separate documentation. | Protects health and compliance. |
| debrismonitorops.dispute.contractor_dispute | contractor dispute | METHOD | Contractor disputes on volume, rejection or eligibility are logged and reviewed. | Provides fair resolution. |
| debrismonitorops.dispute.monitor_conflict | monitor conflict | METHOD | Conflicting monitor notes trigger supervisor review. | Keeps records consistent. |
| debrismonitorops.dispute.resident_claim | resident claim | RECORD | Resident claims of missed pickup, damage or wrong removal are tracked. | Supports service recovery. |
| debrismonitorops.dispute.adjustment | ticket adjustment | METHOD | Adjustments document reason, approver, original and corrected value. | Preserves audit trail. |
| debrismonitorops.qa.ticket_audit | ticket audit | QUALITY_CHECK | Audit samples tickets for truck, origin, volume, debris and disposal proof. | Detects billing error. |
| debrismonitorops.qa.field_shadow | field shadowing | QUALITY_CHECK | Supervisors shadow monitors to verify consistent estimates. | Improves reliability. |
| debrismonitorops.qa.fraud_flag | fraud flag | MODEL | Red flags include duplicate tickets, inflated volume, altered trucks or off-route loads. | Targets investigation. |
| debrismonitorops.qa.training | monitor training | METHOD | Training covers tickets, eligibility, safety, debris types and ethics. | Builds defensible records. |
| debrismonitorops.records.daily_log | daily log | RECORD | Daily log captures monitors, trucks, zones, weather, issues and ticket counts. | Summarizes work. |
| debrismonitorops.records.photo_log | photo log | RECORD | Photos support truck certification, debris piles, damage and disputes. | Adds evidence. |
| debrismonitorops.records.retention | retention rule | CONSTRAINT | Tickets, logs, photos and GPS data follow disaster grant retention. | Preserves reimbursement evidence. |
| debrismonitorops.records.chain | custody chain | RECORD | Ticket custody tracks issue, completion, review, upload and archive. | Prevents loss. |
| debrismonitorops.reporting.daily_volume | daily volume | MEASUREMENT | Daily volume reports cubic yards by type, zone and site. | Shows progress. |
| debrismonitorops.reporting.cost_support | cost support | RECORD | Monitored quantities support contractor invoices and reimbursement claims. | Links work to payment. |
| debrismonitorops.reporting.dashboard | dashboard | MEASUREMENT | Dashboard tracks loads, volumes, rejects, disputes and remaining zones. | Guides operations. |
| debrismonitorops.reporting.closeout_pack | closeout package | RECORD | Package compiles certifications, tickets, invoices, maps, disputes and approvals. | Supports audit closeout. |
| debrismonitorops.safety.stop_work | stop-work authority | SAFETY_RULE | Monitors or supervisors can stop unsafe loading or hauling. | Prevents harm. |
| debrismonitorops.safety.public_contact | public contact rule | METHOD | Monitors route resident questions to public information or field supervisor. | Keeps role clear. |
| debrismonitorops.demob.final_ticket_review | final ticket review | QUALITY_CHECK | Final review resolves missing, duplicate and disputed tickets. | Closes billing risk. |
| debrismonitorops.review.after_action | after-action review | METHOD | Review captures monitoring staffing, forms, technology and contractor issues. | Improves next debris operation. |
