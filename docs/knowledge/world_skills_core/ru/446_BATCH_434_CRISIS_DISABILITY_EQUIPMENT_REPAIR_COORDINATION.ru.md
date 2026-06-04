# BATCH 434: Crisis Disability Equipment Repair Coordination

**KnowledgeUnits:** 44  
**Namespace:** `disabilityrepairops.*`  
**Scope:** intake, device type, safety triage, parts, vendors, loaners, delivery and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| disabilityrepairops.intake.request_source | request source | RECORD | Source records user, caregiver, shelter, clinic, hotline, caseworker or outreach team. | Shows entry path. |
| disabilityrepairops.intake.user_profile | user profile | RECORD | Profile captures contact, location, language, caregiver and safe-contact limits. | Defines support. |
| disabilityrepairops.intake.device_need | device need | RECORD | Need records device failure, lost equipment, damaged accessory or unsafe function. | Frames request. |
| disabilityrepairops.intake.urgency | urgency model | MODEL | Urgency weighs mobility, medical dependence, caregiver absence, shelter access and safety risk. | Prioritizes cases. |
| disabilityrepairops.device.device_type | device type | RECORD | Type distinguishes wheelchair, walker, scooter, CPAP, oxygen support, lift or communication device. | Routes repair. |
| disabilityrepairops.device.model_info | model information | RECORD | Model info records brand, serial, size, power, battery and accessory details. | Finds parts. |
| disabilityrepairops.device.ownership | ownership status | RECORD | Status records owned, rented, insurer-provided, loaner, donated or unknown. | Determines pathway. |
| disabilityrepairops.device.user_constraint | user constraint | RECORD | Constraint captures fit, weight, transfer, charging, transport and caregiver needs. | Ensures usability. |
| disabilityrepairops.triage.safety_screen | safety screen | SAFETY_RULE | Screen checks brakes, frame, battery, oxygen, wiring, stability and immediate danger. | Prevents harm. |
| disabilityrepairops.triage.stop_use | stop-use rule | SAFETY_RULE | Unsafe device is removed from use or limited until repair/loaner is arranged. | Protects user. |
| disabilityrepairops.triage.medical_escalation | medical escalation | METHOD | Health or device-dependence concerns route to clinical or emergency support. | Avoids under-response. |
| disabilityrepairops.triage.access_impact | access impact | MEASUREMENT | Impact measures lost mobility, communication, sleep, breathing support or daily living function. | Sets priority. |
| disabilityrepairops.parts.parts_needed | parts needed | RECORD | Parts list captures tires, brakes, battery, charger, cushion, tubing, filters or fasteners. | Starts sourcing. |
| disabilityrepairops.parts.compatibility | compatibility check | QUALITY_CHECK | Check confirms part fits model, size, voltage, pressure or safety requirement. | Avoids bad repair. |
| disabilityrepairops.parts.source | parts source | METHOD | Source routes to vendor, manufacturer, donor cache, repair shop or insurer. | Finds material. |
| disabilityrepairops.parts.backorder | backorder record | RECORD | Backorder records delay, substitute, loaner need and user update. | Maintains continuity. |
| disabilityrepairops.vendor.vendor_roster | vendor roster | RECORD | Roster lists repair shops, DME suppliers, technicians, delivery and emergency contacts. | Coordinates capacity. |
| disabilityrepairops.vendor.credential | vendor credential | QUALITY_CHECK | Credential checks license, authorization, insurance or manufacturer capability where needed. | Protects quality. |
| disabilityrepairops.vendor.work_order | vendor work order | RECORD | Work order captures device, issue, parts, pickup, estimate, approval and deadline. | Starts repair. |
| disabilityrepairops.vendor.estimate | estimate record | RECORD | Estimate records cost, labor, parts, timeline, warranty and funding source. | Supports decision. |
| disabilityrepairops.loaner.loaner_need | loaner need | RECORD | Need records device type, size, duration, transport, charger and safety constraints. | Restores function. |
| disabilityrepairops.loaner.match | loaner match | METHOD | Match considers user size, device fit, caregiver ability and environment. | Makes loaner useful. |
| disabilityrepairops.loaner.issue_log | loaner issue log | RECORD | Log records loaner ID, condition, user, accessories, issue and return date. | Tracks assets. |
| disabilityrepairops.loaner.return_check | return check | QUALITY_CHECK | Return checks condition, cleaning, accessories and damage. | Keeps stock usable. |
| disabilityrepairops.delivery.pickup | device pickup | METHOD | Pickup plan covers address, access, caregiver, packaging and chain of custody. | Moves device safely. |
| disabilityrepairops.delivery.delivery | repaired delivery | RECORD | Delivery records device return, fit check, user confirmation and unresolved concerns. | Closes handoff. |
| disabilityrepairops.delivery.transport | transport coordination | METHOD | Transport supports user movement while device is unavailable. | Reduces isolation. |
| disabilityrepairops.delivery.failed | failed delivery | RECORD | Failure records no contact, access barrier, wrong device, weather or vendor issue. | Enables reschedule. |
| disabilityrepairops.funding.funding_check | funding check | METHOD | Check routes to insurance, Medicaid, nonprofit, disaster fund, warranty or private pay. | Finds payment. |
| disabilityrepairops.funding.authorization | authorization record | RECORD | Authorization records payer approval, amount, conditions and expiration. | Controls spending. |
| disabilityrepairops.funding.invoice | invoice reconciliation | QUALITY_CHECK | Invoice matches estimate, work order, parts, delivery and approval. | Prevents overpayment. |
| disabilityrepairops.funding.denial | denial pathway | METHOD | Denial routes to appeal, alternate fund, loaner extension or case management. | Avoids dead end. |
| disabilityrepairops.communication.user_update | user update | METHOD | Update explains status, loaner, parts delay, appointment and safety precautions. | Reduces uncertainty. |
| disabilityrepairops.communication.partner_update | partner update | METHOD | Partners receive aggregate repair backlogs, part shortages and urgent needs. | Coordinates support. |
| disabilityrepairops.privacy.minimum_data | minimum data | SAFETY_RULE | Records avoid unnecessary medical detail while preserving device function needs. | Protects user. |
| disabilityrepairops.records.case_log | case log | RECORD | Log stores intake, triage, parts, vendor, loaner, funding, delivery and closeout. | Creates continuity. |
| disabilityrepairops.records.retention | retention rule | CONSTRAINT | Repair, loaner, finance and privacy records follow retention schedules. | Preserves audit. |
| disabilityrepairops.records.device_photo | device photo record | RECORD | Photos document device condition, serial plate, damage and repaired state when consent allows. | Supports repair review. |
| disabilityrepairops.metrics.repairs_completed | repairs completed | MEASUREMENT | Count tracks repairs completed by device type, vendor and urgency. | Shows output. |
| disabilityrepairops.metrics.loaner_days | loaner days | MEASUREMENT | Metric tracks loaner duration and overdue returns. | Manages stock. |
| disabilityrepairops.metrics.time_to_restore | time to restore | MEASUREMENT | Time measures intake to repaired device or workable loaner. | Reveals delay. |
| disabilityrepairops.qa.case_review | case review | QUALITY_CHECK | Review checks safety triage, fit, funding, delivery and closeout completeness. | Improves reliability. |
| disabilityrepairops.demob.transfer | transfer plan | METHOD | Ongoing cases transfer to DME provider, case manager or disability agency. | Maintains support. |
| disabilityrepairops.review.after_action | after-action review | METHOD | Review captures device patterns, part shortages, loaner fit, vendor delays and funding lessons. | Improves future repairs. |
