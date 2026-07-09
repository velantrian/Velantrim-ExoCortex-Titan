# BATCH 329: Water Meter Replacement Program Operations

**KnowledgeUnits:** 44  
**Namespace:** `meterreplaceops.*`  
**Scope:** inventory, scheduling, access, installs, testing, AMI activation, exceptions and billing handoff.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| meterreplaceops.inventory.meter_id | meter ID | RECORD | Meter record includes serial, account, size, location, register, endpoint and install date. | Forms the worklist for replacement. |
| meterreplaceops.inventory.age_filter | age filter | DECISION_RULE | Replacement candidates are selected by age, failure, size, read errors or AMI transition. | Targets meters most likely to under-register or fail. |
| meterreplaceops.inventory.size_class | size class | RECORD | Small residential and large commercial meters follow different workflows. | Scheduling, testing and billing risk differ by size. |
| meterreplaceops.inventory.location_note | location note | RECORD | Location notes describe pit, basement, mechanical room, access hours and hazards. | Reduces missed appointments. |
| meterreplaceops.scheduling.route_batch | route batch | METHOD | Work is grouped by neighborhood, meter type, crew skill and parts. | Improves productivity. |
| meterreplaceops.scheduling.appointment | appointment scheduling | METHOD | Customer appointments confirm access, shutoff impact, pets and contact details. | Prevents wasted truck rolls. |
| meterreplaceops.scheduling.no_access | no-access case | RECORD | No-access attempts are logged with notice, date, reason and next action. | Supports escalation and accurate backlog. |
| meterreplaceops.scheduling.critical_customer | critical customer | DECISION_RULE | Medical, industrial or continuous-use accounts need special scheduling. | Avoids harmful service interruption. |
| meterreplaceops.access.pit_condition | meter pit condition | INSPECTION | Pit is checked for water, insects, traffic, lid condition, confined-space concerns and setter access. | Protects crew and equipment. |
| meterreplaceops.access.indoor_access | indoor access | SAFETY_RULE | Indoor work respects identity, privacy, property protection and safe work area. | Maintains trust and reduces claims. |
| meterreplaceops.access.valve_operability | valve operability | INSPECTION | Inlet/outlet valves are checked before removal. | Meter change fails if water cannot be isolated. |
| meterreplaceops.access.frozen_pipe | frozen or brittle pipe | FAILURE_MODE | Old piping, corrosion or freezing can make replacement risky. | Crews may need plumber or repair plan. |
| meterreplaceops.install.old_read | old meter final read | RECORD | Final read is recorded before removal with photo or electronic capture. | Protects billing accuracy. |
| meterreplaceops.install.remove_meter | meter removal | METHOD | Removal uses pressure relief, spill control and thread protection. | Prevents leaks and property damage. |
| meterreplaceops.install.new_meter | new meter install | METHOD | New meter is installed with correct flow direction, gaskets, spacing and register orientation. | Ensures accurate measurement. |
| meterreplaceops.install.leak_check | leak check | QUALITY_CHECK | Connections and valves are checked under pressure after install. | Prevents callbacks and property damage. |
| meterreplaceops.install.plumbing_issue | plumbing issue | FAILURE_MODE | Cross-threading, bad setters, old valves or unsupported pipes become exception cases. | Replacement program must handle field reality. |
| meterreplaceops.testing.bench_test | bench test | QUALITY_CHECK | Removed meters may be tested for accuracy by flow range. | Confirms under-registration and replacement benefit. |
| meterreplaceops.testing.large_meter | large meter test | METHOD | Large meters may need in-situ testing, bypass planning or calibrated test bench. | Commercial billing impact can be large. |
| meterreplaceops.testing.initial_read | initial read | RECORD | New meter initial read is entered as starting point. | Prevents billing discontinuity. |
| meterreplaceops.ami.endpoint_pair | endpoint pairing | METHOD | AMI endpoint is paired with meter ID, account and location. | Avoids reads assigned to wrong customer. |
| meterreplaceops.ami.signal_check | signal check | QUALITY_CHECK | Endpoint signal, register read and network join are verified. | Confirms meter can be read remotely. |
| meterreplaceops.ami.tamper_alarm | tamper alarm | RECORD | Tamper, reverse flow or leak alerts are configured and tested where available. | Turns meter into operational sensor. |
| meterreplaceops.ami.exception_queue | AMI exception queue | METHOD | Failed activation, weak signal or mismatched reads go to exception queue. | Prevents silent non-reading meters. |
| meterreplaceops.billing.handoff | billing handoff | RECORD | Billing receives old read, new serial, install date, initial read and account link. | Protects customer bills. |
| meterreplaceops.billing.proration | proration | METHOD | Billing period may be split between old and new meter if needed. | Avoids unfair charges. |
| meterreplaceops.billing.high_low_review | high-low review | QUALITY_CHECK | First bills after replacement are reviewed for unusual consumption changes. | Detects installation or data errors. |
| meterreplaceops.billing.customer_question | billing question response | METHOD | Staff explain why new meters may register usage differently. | Reduces disputes after replacement. |
| meterreplaceops.exceptions.wrong_size | wrong size | FAILURE_MODE | Field crew may find meter size or connection differs from records. | Requires parts, record correction and sometimes reschedule. |
| meterreplaceops.exceptions.account_mismatch | account mismatch | FAILURE_MODE | Meter location may not match account or address. | Must resolve before install to avoid billing crossovers. |
| meterreplaceops.exceptions.leak_found | leak found | DECISION_RULE | Existing customer-side leaks found during replacement are documented and communicated. | Separates utility work from private repair. |
| meterreplaceops.exceptions.refusal | refusal | RECORD | Customer refusal is logged with reason, notice and policy next step. | Supports program completion and fairness. |
| meterreplaceops.materials.stock_control | stock control | RECORD | Meters, endpoints, gaskets, couplings and lids are tracked by lot and crew. | Prevents field shortages. |
| meterreplaceops.materials.serial_scan | serial scan | QUALITY_CHECK | Serial numbers are scanned instead of typed where possible. | Reduces data-entry mistakes. |
| meterreplaceops.safety.pressure | pressure safety | SAFETY_RULE | Crews relieve pressure and avoid sudden water release. | Prevents injury and property damage. |
| meterreplaceops.safety.traffic | traffic safety | SAFETY_RULE | Meter pits in streets require traffic control and safe vehicle placement. | Protects crews and drivers. |
| meterreplaceops.records.work_order | work order | RECORD | Work order includes old/new serials, reads, photos, issues, installer and completion status. | Creates auditable replacement record. |
| meterreplaceops.records.photo | photo evidence | RECORD | Photos show old meter, new meter, reads, pit condition and repairs. | Supports QA and billing disputes. |
| meterreplaceops.records.asset_update | asset update | METHOD | Asset system updates meter, endpoint, warranty, location and lifecycle status. | Keeps inventory current. |
| meterreplaceops.qa.field_audit | field audit | QUALITY_CHECK | Supervisor checks sample of installs for leaks, data accuracy and workmanship. | Protects program quality. |
| meterreplaceops.qa.data_reconciliation | data reconciliation | QUALITY_CHECK | Work orders, AMI, billing and inventory are reconciled after batches. | Finds orphaned or mismatched installs. |
| meterreplaceops.reporting.progress | progress dashboard | RECORD | Dashboard tracks scheduled, completed, no-access, exceptions, activations and costs. | Shows program throughput. |
| meterreplaceops.reporting.benefit | program benefit | MODEL | Benefits include reduced apparent losses, fewer estimates, better leak alerts and accurate billing. | Explains why replacement matters. |
| meterreplaceops.review.lessons | lessons learned | METHOD | Program reviews access problems, parts, customer response and data errors. | Improves future replacement waves. |

