# BATCH 360: Disaster Debris Assistance Intake Operations

**KnowledgeUnits:** 44  
**Namespace:** `debrisassistops.*`  
**Scope:** property reports, eligibility, right-of-entry, prioritization, contractor handoff and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| debrisassistops.intake.case_id | debris case ID | RECORD | Case ID links property, owner, damage, hazard, date, channel and status. | Creates controlled intake. |
| debrisassistops.intake.property_location | property location | RECORD | Location captures address, parcel, GPS, access route and jurisdiction. | Supports field verification. |
| debrisassistops.intake.damage_type | damage type | RECORD | Damage type distinguishes vegetative, construction, household, hazardous, vehicle or sediment debris. | Routes to correct process. |
| debrisassistops.intake.photo | photo evidence | RECORD | Photos document debris, access, hazards and property context. | Helps triage and reimbursement. |
| debrisassistops.eligibility.program_area | program area | CONSTRAINT | Eligibility depends on declared incident, jurisdiction, property type and approved program. | Prevents out-of-scope work. |
| debrisassistops.eligibility.owner_status | owner status | METHOD | Owner, tenant, HOA or business status affects authority and assistance path. | Clarifies permissions. |
| debrisassistops.eligibility.duplicate_aid | duplicate aid check | QUALITY_CHECK | Check compares insurance, private contractor and other public assistance. | Avoids improper duplicate benefits. |
| debrisassistops.eligibility.private_property | private property limit | CONSTRAINT | Private property debris removal requires special authority and documentation. | Protects legal boundaries. |
| debrisassistops.rightofentry.roe_form | right-of-entry form | RECORD | ROE grants permission for inspection, debris removal and access conditions. | Enables lawful work. |
| debrisassistops.rightofentry.identity | owner identity proof | SAFETY_RULE | Ownership or authority is verified before ROE acceptance. | Prevents trespass or fraud. |
| debrisassistops.rightofentry.scope | ROE scope | CONSTRAINT | Scope states what crews may remove, access and disturb. | Limits unintended damage. |
| debrisassistops.rightofentry.revocation | ROE revocation | METHOD | Owner can revoke permission under defined process before work stage. | Preserves property rights. |
| debrisassistops.triage.hazard_priority | hazard priority | MODEL | Priority considers blocked access, public safety, utilities, mold, chemicals, instability and vulnerable residents. | Sends crews to highest need. |
| debrisassistops.triage.access_blocked | access blocked | FAILURE_MODE | Blocked roads, gates, dogs, water or unstable structures delay assessment. | Requires coordination. |
| debrisassistops.triage.vulnerable | vulnerable resident | MODEL | Elderly, disabled, medically fragile or low-resource households may receive priority under policy. | Supports equity. |
| debrisassistops.triage.environment | environmental risk | SAFETY_RULE | Asbestos, fuel, chemicals, sewage or biomedical waste trigger specialist handling. | Prevents unsafe cleanup. |
| debrisassistops.field.inspection | field inspection | METHOD | Inspector verifies debris type, volume, access, hazard and eligibility markers. | Confirms intake facts. |
| debrisassistops.field.volume_estimate | volume estimate | MEASUREMENT | Volume estimate records cubic yards, category and confidence. | Supports resource planning. |
| debrisassistops.field.tagging | property tag | METHOD | Tag or digital marker shows inspection status, ROE, hazards and work authorization. | Guides crews. |
| debrisassistops.field.denial | field denial | RECORD | Denial records reason such as ineligible, unsafe, no ROE or already cleared. | Supports appeals. |
| debrisassistops.contractor.work_packet | work packet | RECORD | Packet includes property, scope, debris category, hazards, access and documentation requirements. | Hands off cleanly to contractor. |
| debrisassistops.contractor.assignment | contractor assignment | METHOD | Assignment uses zone, capacity, equipment, material type and priority. | Deploys resources efficiently. |
| debrisassistops.contractor.monitor | debris monitor | QUALITY_CHECK | Monitor observes work, volume, category and site damage. | Controls contractor claims. |
| debrisassistops.contractor.safety | contractor safety | SAFETY_RULE | Contractors follow PPE, traffic, utility, chainsaw, heavy equipment and hazard controls. | Reduces injury. |
| debrisassistops.operations.separation | debris separation | METHOD | Residents may separate vegetative, construction, appliances, hazardous and electronics. | Speeds compliant pickup. |
| debrisassistops.operations.pickup_schedule | pickup schedule | METHOD | Schedule groups cases by zone, material and access constraints. | Improves route efficiency. |
| debrisassistops.operations.load_ticket | load ticket | RECORD | Load ticket records truck, origin, debris type, volume/weight and disposal site. | Supports reimbursement. |
| debrisassistops.operations.disposal_site | disposal site | RECORD | Disposal site must accept category and document entry, weight and environmental rules. | Maintains compliance. |
| debrisassistops.communication.ack | acknowledgment | METHOD | Acknowledgment gives case number, eligibility caveat and next step. | Confirms report. |
| debrisassistops.communication.prep_notice | preparation notice | METHOD | Notice explains sorting, placement, deadlines and what not to put out. | Reduces rejected piles. |
| debrisassistops.communication.delay | delay notice | METHOD | Delay notice explains access, hazard, capacity, weather or contractor issue. | Keeps residents informed. |
| debrisassistops.communication.close_notice | closeout notice | METHOD | Closeout notice states removed, ineligible, referred or no debris found. | Closes resident loop. |
| debrisassistops.records.case_file | case file | RECORD | File stores intake, ROE, inspection, work packet, tickets, photos and communications. | Creates audit trail. |
| debrisassistops.records.fema | reimbursement record | RECORD | Eligible work is documented to meet reimbursement or grant rules. | Protects public funding. |
| debrisassistops.records.retention | retention rule | CONSTRAINT | Records follow disaster, procurement and environmental retention schedules. | Supports later review. |
| debrisassistops.records.privacy | privacy limit | CONSTRAINT | Personal and property details are protected from unnecessary public release. | Protects residents. |
| debrisassistops.qa.roe_audit | ROE audit | QUALITY_CHECK | Audit checks authorization before private property work. | Prevents unlawful entry. |
| debrisassistops.qa.ticket_reconcile | ticket reconciliation | QUALITY_CHECK | Load tickets reconcile with assignments, monitors and disposal receipts. | Detects billing errors. |
| debrisassistops.qa.damage_claim | damage claim route | METHOD | Property damage claims route to contractor, insurer or city review. | Handles cleanup harm. |
| debrisassistops.metrics.cubic_yards | cubic yards removed | MEASUREMENT | Cubic yards removed by type and zone show progress. | Tracks recovery. |
| debrisassistops.metrics.case_age | case age | MEASUREMENT | Case age tracks time from intake to closeout. | Finds delays. |
| debrisassistops.closeout.final_inspection | final inspection | QUALITY_CHECK | Final inspection confirms removal scope and site condition. | Verifies completion. |
| debrisassistops.closeout.lessons | lessons learned | METHOD | Review captures intake gaps, contractor issues, communication and equity concerns. | Improves next disaster. |
| debrisassistops.governance.program_owner | program owner | RECORD | Program owner coordinates emergency management, public works, legal and finance. | Avoids fragmented control. |
