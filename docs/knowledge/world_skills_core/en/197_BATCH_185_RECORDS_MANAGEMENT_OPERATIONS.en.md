# BATCH_185 — Records Management Operations Detail
# world_skills_core · source: world_skills_core:batch_185:records_management_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| recops.class.record_classification | Record classification | invariant | Classification assigns record to category based on function, content, owner and retention rule. | know what it is |
| recops.class.file_plan | File plan | invariant | File plan organizes record categories, locations, naming and ownership. | structured storage |
| recops.class.record_series | Record series | invariant | Series groups similar records created by same process and retention need. | manage in batches |
| recops.class.vital_record | Vital record | variant | Vital record is essential for continuity, legal rights or recovery after disaster. | protect first |
| recops.class.transitory_record | Transitory record | invariant | Transitory record has short-term value and should not be kept longer than needed. | reduce clutter |
| recops.class.metadata_required | Required records metadata | invariant | Metadata captures title, owner, date, category, retention, security and location. | find and govern records |
| recops.retention.retention_schedule | Retention schedule | invariant | Schedule defines how long each record series is kept and what happens after. | lifecycle rule |
| recops.retention.trigger_event | Retention trigger event | invariant | Trigger starts retention clock, such as closure, termination, expiration or completion. | time starts from event |
| recops.retention.retention_hold | Retention hold | invariant | Hold suspends normal destruction because of legal, audit, investigation or business need. | do not destroy |
| recops.retention.schedule_update | Retention schedule update | variant | Update changes rules after legal, business or regulatory review. | keep rules current |
| recops.retention.owner_approval | Retention owner approval | invariant | Owner approval confirms retention rule and disposition for business area. | accountability |
| recops.retention.retention_exception | Retention exception | variant | Exception documents why record deviates from normal retention. | controlled deviation |
| recops.legal.legal_hold_notice | Legal hold notice | invariant | Notice tells custodians what records to preserve and what actions are prohibited. | preservation instruction |
| recops.legal.custodian_ack | Custodian acknowledgment | invariant | Acknowledgment confirms recipient understood and accepted hold obligations. | prove notice |
| recops.legal.hold_scope | Legal hold scope | invariant | Scope defines matter, records, dates, custodians, systems and keywords. | preserve enough, not everything |
| recops.legal.hold_release | Legal hold release | invariant | Release ends preservation duty and returns records to normal retention where allowed. | restart lifecycle |
| recops.legal.collection_log | Records collection log | invariant | Log records collected sources, dates, tools, custodians and chain of custody. | evidence integrity |
| recops.legal.spoliation_risk | Spoliation risk | invariant | Risk arises when records may be altered, deleted or lost after preservation duty begins. | serious legal exposure |
| recops.storage.physical_box | Physical records box | invariant | Box record links contents, barcode, owner, retention, location and access restrictions. | warehouse control |
| recops.storage.offsite_storage | Offsite records storage | variant | Offsite storage needs inventory, retrieval SLA, environmental controls and destruction service. | external custody |
| recops.storage.electronic_repository | Electronic records repository | invariant | Repository stores records with access controls, metadata, retention and audit trails. | digital recordkeeping |
| recops.storage.access_control | Records access control | invariant | Access control limits who may view, modify, export or destroy records. | protect information |
| recops.storage.version_control | Record version control | invariant | Version control distinguishes draft, final, superseded and approved versions. | avoid wrong record |
| recops.storage.backup_not_record | Backup not record copy | invariant | Backup is for recovery and should not be treated as primary recordkeeping repository. | avoid governance confusion |
| recops.digitization.scan_spec | Records scan specification | invariant | Scan spec defines resolution, format, color, OCR, naming and quality checks. | consistent digitization |
| recops.digitization.indexing | Records indexing | invariant | Indexing adds metadata that lets scanned records be searched and retrieved. | scan without index is pile |
| recops.digitization.quality_check | Digitization quality check | invariant | QC checks page count, legibility, orientation, completeness and metadata accuracy. | trust digital copy |
| recops.digitization.source_disposition | Source paper disposition | variant | Disposition decides whether paper original is retained, destroyed or returned after scanning. | paper lifecycle |
| recops.digitization.ocr_correction | OCR correction | variant | Correction improves searchability for critical fields or poor-quality scans. | text layer quality |
| recops.digitization.chain_of_custody | Digitization chain of custody | invariant | Chain records handoff from box or file to scanning, QC, repository and return or destruction. | preserve accountability |
| recops.disposition.disposition_review | Disposition review | invariant | Review confirms records are eligible for destruction or transfer and no hold applies. | final gate |
| recops.disposition.destruction_certificate | Destruction certificate | invariant | Certificate documents records destroyed, method, date, vendor and authorization. | proof of disposal |
| recops.disposition.secure_shredding | Secure shredding | variant | Shredding destroys paper records to reduce information exposure. | physical privacy |
| recops.disposition.digital_delete | Digital deletion | invariant | Deletion removes eligible electronic records from active repository according to approved process. | digital cleanup |
| recops.disposition.archive_transfer | Archive transfer | variant | Transfer moves permanent records to archive with metadata, rights and preservation requirements. | keep long-term value |
| recops.disposition.disposition_freeze | Disposition freeze | invariant | Freeze stops planned destruction when hold, audit or incident arises. | pause destruction |
| recops.audit.inventory_audit | Records inventory audit | invariant | Audit compares expected records with actual boxes, files, systems and metadata. | find gaps |
| recops.audit.access_audit | Records access audit | invariant | Audit reviews who accessed, exported, modified or deleted records. | security visibility |
| recops.audit.retention_compliance | Retention compliance check | invariant | Check compares record age and status with schedule and holds. | enforce lifecycle |
| recops.audit.orphan_record | Orphan record | invariant | Orphan record lacks owner, category or retention rule and needs remediation. | unmanaged risk |
| recops.audit.disposition_sampling | Disposition sampling | variant | Sampling verifies destroyed records matched approval list and no exceptions were present. | trust but verify |
| recops.training.custodian_training | Records custodian training | invariant | Training teaches classification, retention, holds, storage, privacy and disposition duties. | people create compliance |
| recops.training.policy_ack | Records policy acknowledgment | invariant | Acknowledgment records that staff accepted recordkeeping responsibilities. | accountability |
| recops.reporting.records_kpi | Records management KPI | variant | KPI tracks classification, overdue disposition, holds, retrieval time, audit issues and storage cost. | manage program |
