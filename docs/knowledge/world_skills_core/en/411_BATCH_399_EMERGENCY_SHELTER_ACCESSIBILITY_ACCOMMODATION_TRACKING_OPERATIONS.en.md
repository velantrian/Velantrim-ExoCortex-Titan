# BATCH 399: Emergency Shelter Accessibility Accommodation Tracking Operations

**KnowledgeUnits:** 44  
**Namespace:** `shelteraccessops.*`  
**Scope:** needs intake, assistive devices, bed placement, transport, privacy and follow-up.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| shelteraccessops.intake.need_screen | need screen | RECORD | Screen captures mobility, sensory, cognitive, medical, language and caregiver needs. | Starts accommodation tracking. |
| shelteraccessops.intake.self_report | self-report rule | METHOD | Residents can report needs without diagnostic proof unless policy requires escalation. | Keeps access humane. |
| shelteraccessops.intake.caregiver | caregiver link | RECORD | Caregiver record links helper, contact, role, overnight status and privacy permission. | Supports daily care. |
| shelteraccessops.intake.service_animal | service animal note | RECORD | Service animal note records animal presence, handler needs and relief area guidance. | Protects access. |
| shelteraccessops.privacy.minimum_data | minimum data | SAFETY_RULE | Accommodation records collect only information needed for placement, support and safety. | Reduces privacy risk. |
| shelteraccessops.privacy.visible_flag | visible flag control | SAFETY_RULE | Public-facing flags avoid medical detail and use operational accommodation labels. | Prevents stigma. |
| shelteraccessops.privacy.consent_share | consent to share | RECORD | Consent records whether needs can be shared with medical, transport or partner staff. | Enables coordination. |
| shelteraccessops.privacy.private_discussion | private discussion | METHOD | Sensitive needs are discussed away from lines, dorms and public registration desks. | Preserves dignity. |
| shelteraccessops.devices.device_request | device request | RECORD | Request lists wheelchair, walker, cane, hearing device, charger, cot rail or other support. | Defines supply need. |
| shelteraccessops.devices.inventory_match | inventory match | METHOD | Available devices are matched by size, safety condition, duration and priority. | Issues useful equipment. |
| shelteraccessops.devices.loan_log | loan log | RECORD | Loan log records device ID, resident, issue time, condition and return status. | Tracks assets. |
| shelteraccessops.devices.maintenance | device maintenance | QUALITY_CHECK | Devices are checked for brakes, tips, batteries, cleanliness and safe operation. | Prevents injury. |
| shelteraccessops.beds.accessible_bed | accessible bed placement | METHOD | Placement considers mobility path, restroom distance, caregiver, medical desk and quiet needs. | Improves usability. |
| shelteraccessops.beds.cot_height | cot height need | RECORD | Cot height need records low/high cot, bariatric cot, rail or transfer support. | Prevents falls. |
| shelteraccessops.beds.quiet_area | quiet area | METHOD | Quiet area placement supports sensory, cognitive, sleep or behavioral needs. | Reduces distress. |
| shelteraccessops.beds.family_unit | family unit preservation | CONSTRAINT | Accommodation planning tries to keep household or caregiver units together. | Protects support network. |
| shelteraccessops.transport.arrival_support | arrival support | METHOD | Arrival support coordinates ramp, wheelchair, staff escort or accessible drop-off. | Makes entry possible. |
| shelteraccessops.transport.local_transfer | local transfer | RECORD | Transfer record captures accessible vehicle need, destination, time and escort needs. | Supports movement. |
| shelteraccessops.transport.medical_trip | medical trip | METHOD | Medical trips route through approved transport and care coordination process. | Prevents missed care. |
| shelteraccessops.transport.evacuated_equipment | equipment transport | RECORD | Equipment transport records oxygen, wheelchair, charger or mobility device moved with resident. | Prevents separation. |
| shelteraccessops.communication.language_access | language access | METHOD | Language support identifies interpreter, translated forms or communication board needs. | Improves understanding. |
| shelteraccessops.communication.visual_alert | visual alert | METHOD | Visual alerts support people who cannot hear announcements or alarms. | Improves safety. |
| shelteraccessops.communication.plain_script | plain script | METHOD | Staff use plain scripts for routines, rules, meals, transport and closures. | Reduces confusion. |
| shelteraccessops.communication.resident_update | resident update | METHOD | Updates explain request status, delay reason, alternatives and next check time. | Reduces uncertainty. |
| shelteraccessops.workflow.request_queue | request queue | RECORD | Queue tracks accommodation requests, priority, owner, status and due time. | Manages workload. |
| shelteraccessops.workflow.priority_rule | priority rule | MODEL | Priority weighs life safety, mobility, medical dependence, caregiver absence and wait time. | Orders support. |
| shelteraccessops.workflow.shift_handoff | shift handoff | METHOD | Handoff lists pending requests, device loans, bed moves, transport and privacy cautions. | Maintains continuity. |
| shelteraccessops.workflow.escalation | escalation path | METHOD | Unmet needs escalate to shelter manager, medical desk, disability coordinator or logistics. | Resolves blockers. |
| shelteraccessops.safety.fall_risk | fall risk control | SAFETY_RULE | Fall risk controls include pathways, lighting, cot placement, escort and device checks. | Reduces injury. |
| shelteraccessops.safety.power_dependence | power dependence | SAFETY_RULE | Power-dependent devices require charging access, backup plan and monitoring. | Protects health. |
| shelteraccessops.safety.oxygen_support | oxygen support | SAFETY_RULE | Oxygen support tracks cylinders, concentrators, fire separation and refill pathway. | Controls risk. |
| shelteraccessops.safety.evacuation_assist | evacuation assistance | RECORD | Evacuation assistance note identifies residents needing help during alarm or relocation. | Speeds evacuation. |
| shelteraccessops.reporting.daily_summary | daily summary | RECORD | Summary reports requests open, filled, delayed, device stock and critical gaps. | Informs command. |
| shelteraccessops.reporting.unmet_needs | unmet needs count | MEASUREMENT | Count groups unmet needs by category, reason and site. | Guides resources. |
| shelteraccessops.reporting.access_issue | access issue log | RECORD | Log captures barriers such as inaccessible restroom, doorway, ramp, signage or transport. | Drives fixes. |
| shelteraccessops.reporting.partner_request | partner request | RECORD | Partner requests describe supply, staff, interpreter, transport or specialized care need. | Gets outside help. |
| shelteraccessops.qa.case_review | case review | QUALITY_CHECK | Review checks if request, decision, action and follow-up are documented. | Improves reliability. |
| shelteraccessops.qa.placement_check | placement check | QUALITY_CHECK | Staff verify that bed or area placement actually works for the resident. | Confirms usefulness. |
| shelteraccessops.qa.device_reconciliation | device reconciliation | QUALITY_CHECK | Loaned devices reconcile with inventory, returns, transfers and losses. | Protects stock. |
| shelteraccessops.qa.privacy_audit | privacy audit | QUALITY_CHECK | Audit checks access to accommodation details and improper disclosure risks. | Protects residents. |
| shelteraccessops.metrics.fulfillment_time | fulfillment time | MEASUREMENT | Metric measures request intake to accommodation delivered. | Shows delay. |
| shelteraccessops.metrics.request_volume | request volume | MEASUREMENT | Volume tracks accommodation requests by type, site and shift. | Plans staffing. |
| shelteraccessops.closeout.departure_note | departure note | RECORD | Departure note captures returned devices, referral needs and destination constraints. | Closes record. |
| shelteraccessops.review.after_action | after-action review | METHOD | Review captures access barriers, device stock, staffing, privacy and transport lessons. | Improves future shelters. |
