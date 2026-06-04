# BATCH_187 — Mailroom & Document Scanning Operations Detail
# world_skills_core · source: world_skills_core:batch_187:mailroom_document_scanning_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| mailops.intake.mail_receipt | Mail receipt log | invariant | Receipt log records date, sender, carrier, item type, tracking number and recipient. | prove arrival |
| mailops.intake.courier_handoff | Courier handoff | invariant | Handoff captures custody, signature, time, package count and exception notes. | chain of custody |
| mailops.intake.security_screening | Mail security screening | invariant | Screening checks for suspicious packages, damage, leaks, odors, unknown sender or prohibited items. | protect workplace |
| mailops.intake.priority_sort | Mail priority sort | invariant | Sort separates urgent, registered, legal, financial, confidential and routine items. | route by risk |
| mailops.intake.undeliverable_mail | Undeliverable mail | invariant | Undeliverable item lacks valid recipient, address or department and needs research or return. | prevent lost documents |
| mailops.intake.confidential_mail | Confidential mail handling | invariant | Confidential mail is restricted by recipient, access rule, sealed state and delivery evidence. | privacy control |
| mailops.prep.document_prep | Document prep | invariant | Prep removes staples, repairs pages, unfolds, separates batches and adds separator sheets. | scanner-ready input |
| mailops.prep.batch_sheet | Scan batch sheet | invariant | Batch sheet identifies job, source, owner, document type, count and indexing rules. | control the batch |
| mailops.prep.page_count | Page count control | invariant | Count compares expected, prepared, scanned and indexed pages. | catch missing pages |
| mailops.prep.exception_item | Mailroom exception item | invariant | Exception item needs special handling because of damage, oversize, illegibility, sensitivity or mismatch. | do not force flow |
| mailops.prep.barcode_separator | Barcode separator | variant | Separator barcode tells scanner or capture system where a document or batch starts. | automate splitting |
| mailops.scan.scanner_profile | Scanner profile | invariant | Profile sets resolution, color mode, duplex, file type, compression and enhancement. | consistent images |
| mailops.scan.duplex_capture | Duplex capture | invariant | Duplex capture scans both sides and suppresses blank pages only under controlled rules. | avoid missing backs |
| mailops.scan.image_quality | Scan image quality | invariant | Quality checks skew, crop, contrast, blank pages, streaks, orientation and completeness. | readable record |
| mailops.scan.rescan_request | Rescan request | invariant | Rescan corrects missing, blurred, skewed, cropped or wrong-document images. | fix before archive |
| mailops.scan.oversize_scan | Oversize document scan | variant | Oversize scan uses large-format device, stitching or special handling for plans and posters. | fit unusual media |
| mailops.ocr.ocr_capture | OCR capture | variant | OCR converts document images into searchable text with confidence scores. | search and extract |
| mailops.ocr.ocr_confidence | OCR confidence review | invariant | Review flags fields or pages where recognition confidence is too low. | humans check weak text |
| mailops.ocr.handwriting_limit | Handwriting OCR limit | variant | Handwriting recognition is less reliable and may require manual keying or double entry. | know automation limits |
| mailops.ocr.zonal_ocr | Zonal OCR | variant | Zonal OCR extracts data from predefined areas such as invoice number, date or account. | structured capture |
| mailops.index.document_type | Document type index | invariant | Index assigns captured item to type such as invoice, claim, contract, form or correspondence. | drives workflow |
| mailops.index.metadata_field | Metadata field | invariant | Field stores values such as date, sender, account, case, department, retention class or owner. | find later |
| mailops.index.validation_rule | Index validation rule | invariant | Rule checks required fields, format, allowed values and cross-field consistency. | prevent bad metadata |
| mailops.index.double_keying | Double keying | variant | Two operators enter critical fields independently and mismatches are reconciled. | reduce errors |
| mailops.index.lookup_match | Lookup match | variant | Match compares indexed data to customer, vendor, case or employee master records. | route correctly |
| mailops.workflow.routing_queue | Document routing queue | invariant | Queue sends indexed documents to department, case worker, approver or system integration. | work moves onward |
| mailops.workflow.sla_clock | Mailroom SLA clock | invariant | SLA clock measures receipt-to-scan, scan-to-index, and index-to-route time. | control delay |
| mailops.workflow.priority_exception | Priority exception | variant | Exception accelerates legal, payment, deadline or safety-related documents. | deadlines matter |
| mailops.workflow.return_to_sender | Return-to-sender workflow | invariant | Workflow records reason, approval, packaging and dispatch evidence for returned item. | close impossible delivery |
| mailops.workflow.physical_delivery | Internal physical delivery | invariant | Delivery route moves items to recipients with route, signature or mailbox evidence. | last-mile control |
| mailops.qa.sample_review | Scan QA sampling | invariant | Sampling reviews batches for missing pages, bad images, wrong type and metadata defects. | quality evidence |
| mailops.qa.defect_code | Document capture defect code | invariant | Code classifies error such as missing page, wrong index, unreadable image or duplicate scan. | learn from errors |
| mailops.qa.reconciliation | Mailroom reconciliation | invariant | Reconciliation compares received items, scanned batches, routed records and held exceptions. | no item disappears |
| mailops.qa.duplicate_document | Duplicate document detection | variant | Detection finds repeated scans or re-submitted documents by metadata, barcode or image similarity. | avoid duplicate cases |
| mailops.qa.operator_feedback | Capture operator feedback | variant | Feedback gives operators defect patterns and corrected examples. | improve accuracy |
| mailops.records.retention_class | Mailroom retention class | invariant | Retention class links document type to storage, legal hold and destruction rules. | lifecycle from intake |
| mailops.records.original_handling | Original document handling | invariant | Original handling defines return, archive, shred or temporary hold after scanning. | paper fate |
| mailops.records.secure_shred | Secure shredding | invariant | Shred process records authorization, container, vendor or internal destruction evidence. | dispose safely |
| mailops.records.audit_trail | Capture audit trail | invariant | Audit trail records receipt, prep, scan, index, QA, routing, access and disposition events. | explain history |
| mailops.records.legal_hold_flag | Legal hold flag | invariant | Hold flag prevents destruction or alteration while investigation, litigation or audit requires preservation. | stop normal disposal |
| mailops.equipment.scanner_maintenance | Scanner maintenance | invariant | Maintenance covers rollers, glass, feed path, calibration, firmware and cleaning. | image quality depends on equipment |
| mailops.equipment.feed_jam | Scanner feed jam | invariant | Jam response clears pages, verifies order, rescans affected pages and records exception. | avoid missing pages |
| mailops.metrics.mailroom_kpi | Mailroom KPI | variant | KPI tracks volumes, turnaround, defects, backlog, SLA misses, exceptions and cost. | manage service |
| mailops.continuity.backlog_recovery | Mailroom backlog recovery | invariant | Recovery prioritizes aged, deadline-critical and high-risk documents after outage or surge. | catch up safely |
