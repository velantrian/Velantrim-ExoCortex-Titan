# BATCH 443: Disaster Durable Medical Equipment Lending Operations

**KnowledgeUnits:** 44  
**Namespace:** `dmelendingops.*`  
**Scope:** intake, inventory, fit, cleaning, custody, return and maintenance.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| dmelendingops.intake.request_source | request source | RECORD | Source records shelter desk, clinic, caseworker, discharge planner, caregiver, hotline or outreach team. | Shows entry path. |
| dmelendingops.intake.borrower_profile | borrower profile | RECORD | Profile captures contact, location, language, caregiver, mobility need and safe-contact limits. | Defines support. |
| dmelendingops.intake.equipment_need | equipment need | RECORD | Need records wheelchair, walker, cane, shower chair, commode, hospital bed accessory or transfer aid. | Frames request. |
| dmelendingops.intake.urgency_score | urgency score | MODEL | Score weighs fall risk, discharge timing, shelter access, caregiver absence, medical dependence and distance. | Prioritizes loans. |
| dmelendingops.eligibility.disaster_link | disaster link | CONTROL | Link verifies equipment is needed because of loss, displacement, damage, access barrier or recovery condition. | Targets stock. |
| dmelendingops.eligibility.loan_boundary | loan boundary | CONTROL | Boundary defines short-term loan, replacement bridge, nonclinical support and exclusions. | Prevents scope creep. |
| dmelendingops.eligibility.duplicate_check | duplicate check | CONTROL | Check compares borrower, household, device type, serial number and prior loan records. | Avoids duplicate issue. |
| dmelendingops.inventory.asset_record | asset record | RECORD | Asset record captures device type, serial, size, condition, accessories, location and ownership source. | Tracks inventory. |
| dmelendingops.inventory.availability_status | availability status | STATE | Status marks available, reserved, issued, cleaning, repair, missing, retired or quarantine. | Shows usable stock. |
| dmelendingops.inventory.accessory_set | accessory set | RECORD | Set records cushions, footrests, tips, wheels, brakes, chargers, rails, bags or manuals. | Prevents incomplete loans. |
| dmelendingops.inventory.stock_threshold | stock threshold | CONTROL | Threshold flags minimum quantities by device type and size for reorder or donation request. | Prevents shortages. |
| dmelendingops.fit.size_match | size match | CONTROL | Match checks height, weight range, seat width, grip height, stability and intended environment. | Improves safety. |
| dmelendingops.fit.environment_check | environment check | PROCESS | Check reviews stairs, door width, floor surface, bathroom layout, transport and shelter rules. | Confirms usability. |
| dmelendingops.fit.user_instruction | user instruction | PROCESS | Instruction covers safe use, adjustment, brakes, storage, cleaning responsibility and return contact. | Reduces misuse. |
| dmelendingops.fit.caregiver_brief | caregiver brief | PROCESS | Brief explains transfers, limits, warning signs, equipment care and escalation route. | Supports helpers. |
| dmelendingops.cleaning.intake_cleaning | intake cleaning | PROCESS | Cleaning removes soil, disinfects surfaces, inspects wear and documents readiness before issue. | Protects users. |
| dmelendingops.cleaning.contact_time | disinfectant contact time | CONTROL | Contact time verifies the disinfectant stayed wet long enough for the device category. | Improves sanitation. |
| dmelendingops.cleaning.quarantine_flag | quarantine flag | STATE | Flag separates devices exposed to contamination, pests, bodily fluids or uncertain cleaning history. | Prevents cross-risk. |
| dmelendingops.cleaning.clean_tag | clean tag | RECORD | Tag records cleaned date, staff, method, condition and next inspection need. | Supports trust. |
| dmelendingops.custody.loan_agreement | loan agreement | RECORD | Agreement records borrower, device, accessories, expected return, liability limits and contact path. | Creates custody. |
| dmelendingops.custody.issue_log | issue log | RECORD | Log captures date, staff, device ID, borrower confirmation, condition photo and instruction given. | Documents release. |
| dmelendingops.custody.transfer_between_sites | transfer between sites | PROCESS | Transfer records moving stock between shelter, clinic, warehouse, outreach team or repair vendor. | Keeps inventory accurate. |
| dmelendingops.custody.loss_report | loss report | RECORD | Report captures missing, stolen, damaged, unreturned or destroyed device and recovery steps. | Controls losses. |
| dmelendingops.delivery.pickup_option | pickup option | PROCESS | Option schedules borrower pickup, caregiver pickup, shelter desk handoff or field delivery. | Gets equipment to user. |
| dmelendingops.delivery.accessible_delivery | accessible delivery | PROCESS | Delivery accounts for stairs, curb access, vehicle loading, caregiver presence and setup time. | Prevents failed handoff. |
| dmelendingops.delivery.handoff_proof | handoff proof | RECORD | Proof records recipient role, device ID, accessories, date and signature or alternate confirmation. | Closes custody. |
| dmelendingops.return.return_window | return window | RECORD | Window records due date, reminder cadence, extension rules and alternate return site. | Manages circulation. |
| dmelendingops.return.extension_request | extension request | PROCESS | Request reviews ongoing need, stock pressure, safety status and funding or replacement path. | Balances fairness. |
| dmelendingops.return.receipt_check | receipt check | PROCESS | Check verifies returned device, accessories, condition, cleaning need and damage notes. | Reopens inventory. |
| dmelendingops.return.no_return_followup | no-return follow-up | PROCESS | Follow-up contacts borrower, caregiver or caseworker and records barriers or loss status. | Reduces attrition. |
| dmelendingops.maintenance.condition_inspection | condition inspection | PROCESS | Inspection checks brakes, tips, wheels, welds, frame, batteries, cushions, fasteners and stability. | Finds hazards. |
| dmelendingops.maintenance.repair_ticket | repair ticket | RECORD | Ticket records defect, priority, parts, vendor, cost estimate, approval and completion. | Organizes repair. |
| dmelendingops.maintenance.retirement_rule | retirement rule | CONTROL | Rule removes unsafe, obsolete, repeatedly damaged or uneconomical equipment from circulation. | Protects users. |
| dmelendingops.records.case_file | case file | RECORD | File links intake, eligibility, fit, issue, custody, return, cleaning and closeout. | Supports audit. |
| dmelendingops.records.status_board | status board | RECORD | Board tracks requested, reserved, issued, delivered, extended, overdue, returned, cleaning and retired. | Shows flow. |
| dmelendingops.records.exception_log | exception log | RECORD | Log captures no stock, poor fit, failed delivery, damage, infection concern, overdue or lost item. | Enables review. |
| dmelendingops.communication.borrower_update | borrower update | PROCESS | Update explains availability, pickup, safe use, return date, extension option and maintenance contact. | Reduces confusion. |
| dmelendingops.communication.partner_request | partner request | PROCESS | Request asks donors, clinics or vendors for specific sizes, parts or repair capacity. | Fills gaps. |
| dmelendingops.communication.referral_note | referral note | RECORD | Note routes clinical fitting, complex rehab equipment or permanent replacement needs to qualified services. | Avoids unsafe substitution. |
| dmelendingops.metrics.fulfillment_rate | fulfillment rate | METRIC | Rate tracks eligible requests filled from available stock. | Measures service. |
| dmelendingops.metrics.turnaround_time | turnaround time | METRIC | Time measures request to issued usable equipment. | Shows speed. |
| dmelendingops.metrics.return_rate | return rate | METRIC | Rate compares issued devices, returned devices, overdue devices and lost devices. | Guides inventory planning. |
| dmelendingops.closeout.borrower_confirmation | borrower confirmation | PROCESS | Confirmation verifies device works, barriers remain understood and follow-up is scheduled if needed. | Closes loop. |
| dmelendingops.closeout.after_action | after-action note | RECORD | Note captures shortages, fit issues, cleaning capacity, repair needs and partner improvements. | Improves next activation. |
