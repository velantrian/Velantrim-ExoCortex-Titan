# BATCH 367: Public Health Laboratory Surge Operations

**KnowledgeUnits:** 44  
**Namespace:** `labsurgeops.*`  
**Scope:** sample intake, accessioning, staffing, batching, result reporting, QA and demobilization.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| labsurgeops.activation.trigger | surge trigger | MODEL | Surge triggers include outbreak, disaster, backlog, new testing program or lab outage. | Starts expanded lab workflow. |
| labsurgeops.activation.command | lab command role | RECORD | Command assigns lead, sections, reporting cadence and escalation contacts. | Keeps surge accountable. |
| labsurgeops.activation.capacity | capacity estimate | MEASUREMENT | Capacity estimates instruments, staff, shifts, reagents, accessioning and courier limits. | Prevents unrealistic promises. |
| labsurgeops.activation.priority_policy | priority policy | CONSTRAINT | Priority defines which specimens run first under scarcity. | Protects urgent public health work. |
| labsurgeops.intake.specimen_arrival | specimen arrival | RECORD | Arrival records courier, time, package, temperature and count. | Starts custody and timing. |
| labsurgeops.intake.chain | chain of custody | RECORD | Custody logs every handoff for regulated or high-risk specimens. | Preserves evidence integrity. |
| labsurgeops.intake.triage | intake triage | METHOD | Triage separates urgent, routine, rejected, damaged and special handling samples. | Keeps flow controlled. |
| labsurgeops.intake.rejection | rejection reason | RECORD | Rejection records leaked, unlabeled, wrong medium, expired or missing form. | Supports correction. |
| labsurgeops.accessioning.accession_id | accession ID | RECORD | Accession ID links specimen, patient, submitter, test and barcode. | Prevents mix-ups. |
| labsurgeops.accessioning.barcode | barcode process | METHOD | Barcode labels tubes, forms, racks and batches. | Reduces manual error. |
| labsurgeops.accessioning.demographic_match | demographic match | QUALITY_CHECK | Patient fields are checked for name, DOB, ID and submitter consistency. | Prevents wrong results. |
| labsurgeops.accessioning.missing_data | missing data queue | METHOD | Missing fields route to submitter query or conditional processing. | Keeps backlog visible. |
| labsurgeops.staffing.shift_plan | shift plan | RECORD | Shift plan covers accessioning, extraction, testing, review, reporting and support roles. | Uses staff efficiently. |
| labsurgeops.staffing.cross_training | cross-training | METHOD | Staff are trained for safe secondary roles during surge. | Adds flexible capacity. |
| labsurgeops.staffing.fatigue | fatigue control | SAFETY_RULE | Long surge shifts require breaks, rotation and error monitoring. | Protects quality. |
| labsurgeops.staffing.competency | competency check | QUALITY_CHECK | Staff perform only tasks within documented competency. | Maintains lab standards. |
| labsurgeops.supplies.reagent_stock | reagent stock | MEASUREMENT | Stock tracks kits, controls, consumables and burn rate. | Prevents sudden stop. |
| labsurgeops.supplies.shortage | shortage protocol | METHOD | Shortage protocol triggers substitutions, allocation or partner referral. | Keeps essential testing moving. |
| labsurgeops.supplies.lot_control | lot control | RECORD | Reagent lots link to test batches and QC outcomes. | Supports investigations. |
| labsurgeops.supplies.ppe | PPE supply | SAFETY_RULE | PPE levels match biosafety risk and sample volume. | Protects staff. |
| labsurgeops.batching.batch_design | batch design | METHOD | Batches group specimens by test, priority, instrument and controls. | Improves throughput. |
| labsurgeops.batching.control_set | control set | QUALITY_CHECK | Positive, negative and internal controls are included as required. | Validates runs. |
| labsurgeops.batching.rerun_queue | rerun queue | METHOD | Failed or inconclusive samples route to rerun with reason. | Keeps unresolved work visible. |
| labsurgeops.batching.contamination | contamination risk | FAILURE_MODE | Cross-contamination can occur during aliquot, extraction or amplification steps. | Requires strict separation. |
| labsurgeops.testing.instrument_status | instrument status | RECORD | Instrument status tracks uptime, maintenance, errors and capacity. | Guides scheduling. |
| labsurgeops.testing.method_validation | method validation | CONSTRAINT | New or modified methods require validation or approved verification. | Protects result reliability. |
| labsurgeops.testing.turnaround | turnaround target | MEASUREMENT | TAT tracks receipt-to-result by priority and test type. | Shows surge performance. |
| labsurgeops.testing.backlog | backlog measure | MEASUREMENT | Backlog counts specimens waiting by stage and age. | Drives staffing decisions. |
| labsurgeops.result.technical_review | technical review | QUALITY_CHECK | Technical review checks controls, curves, flags and instrument notes. | Catches run issues. |
| labsurgeops.result.clinical_review | result review | QUALITY_CHECK | Result review checks patient match, interpretation and reportability. | Prevents bad release. |
| labsurgeops.result.critical_notice | critical result notice | SAFETY_RULE | Critical results follow urgent notification policy. | Enables rapid public health action. |
| labsurgeops.result.correction | correction process | METHOD | Corrected results preserve original, reason, approver and notification. | Maintains auditability. |
| labsurgeops.reporting.elr | electronic lab reporting | METHOD | ELR sends structured results to surveillance systems. | Reduces manual entry. |
| labsurgeops.reporting.submitter | submitter report | METHOD | Submitters receive results through approved secure channel. | Closes request loop. |
| labsurgeops.reporting.dashboard | lab dashboard | MEASUREMENT | Dashboard tracks volume, positivity, TAT, backlog and failures. | Supports command decisions. |
| labsurgeops.reporting.data_quality | data quality check | QUALITY_CHECK | Reports check missing demographics, duplicate accessions and invalid codes. | Improves surveillance data. |
| labsurgeops.biosafety.risk_assessment | biosafety assessment | SAFETY_RULE | Risk assessment matches pathogen, procedure, PPE and containment. | Protects workers. |
| labsurgeops.biosafety.exposure | exposure response | SAFETY_RULE | Exposure response documents incident, medical evaluation and corrective action. | Controls lab safety events. |
| labsurgeops.qa.proficiency | proficiency support | QUALITY_CHECK | Surge workflows preserve required proficiency and QC records. | Maintains accreditation. |
| labsurgeops.qa.deviation | deviation log | RECORD | Deviations capture process exceptions and corrective action. | Makes surge compromises visible. |
| labsurgeops.demob.stepdown | stepdown criteria | METHOD | Stepdown uses backlog, demand, staffing and partner capacity. | Ends surge responsibly. |
| labsurgeops.demob.inventory | demob inventory | QUALITY_CHECK | Inventory reconciles reagents, specimens, waste and borrowed equipment. | Restores normal operations. |
| labsurgeops.demob.records | record closeout | RECORD | Records are archived by test, batch, result and incident. | Supports audit. |
| labsurgeops.review.after_action | after-action review | METHOD | Review captures bottlenecks, errors, staffing and supply lessons. | Improves next surge. |
