# BATCH 425: Crisis Document Translation Request Handling Operations

**KnowledgeUnits:** 44  
**Namespace:** `doctranslationops.*`  
**Scope:** intake, language, document type, confidentiality, assignment, delivery and QA.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| doctranslationops.intake.request_source | request source | RECORD | Source records resident, legal clinic, benefits desk, school, clinic or caseworker. | Shows origin. |
| doctranslationops.intake.requester_profile | requester profile | RECORD | Profile captures name, contact, language, safe contact and assistance context. | Supports follow-up. |
| doctranslationops.intake.document_count | document count | MEASUREMENT | Count records number of pages, files, images and priority sections. | Sizes workload. |
| doctranslationops.intake.deadline | deadline capture | SAFETY_RULE | Deadline records submission date, appointment, appeal, school or medical timing. | Prioritizes work. |
| doctranslationops.language.source_language | source language | RECORD | Source language records document language, script, dialect or uncertainty. | Selects translator. |
| doctranslationops.language.target_language | target language | RECORD | Target language records needed output language, locale and reading level. | Defines output. |
| doctranslationops.language.certified_need | certified need | CONSTRAINT | Some documents require certified, sworn or agency-approved translation. | Routes correctly. |
| doctranslationops.language.interpreter_note | interpreter note | METHOD | Interpreter support may clarify intake without replacing written translation. | Reduces errors. |
| doctranslationops.document.doc_type | document type | RECORD | Type distinguishes ID, lease, notice, benefits, school, medical, insurance or court document. | Routes expertise. |
| doctranslationops.document.sensitivity | sensitivity level | SAFETY_RULE | Sensitivity flags medical, legal, immigration, child, financial or safety data. | Controls access. |
| doctranslationops.document.completeness | completeness check | QUALITY_CHECK | Check confirms pages, signatures, dates, stamps and readable scans. | Prevents missing translation. |
| doctranslationops.document.format_need | format need | RECORD | Format need captures plain text, form field, letter, certified PDF or summary. | Guides delivery. |
| doctranslationops.confidentiality.minimum_data | minimum data | SAFETY_RULE | Staff store only needed document and request information. | Reduces exposure. |
| doctranslationops.confidentiality.access_control | access control | SAFETY_RULE | Sensitive files are restricted to assigned translator, reviewer and supervisor. | Protects requester. |
| doctranslationops.confidentiality.agreement | confidentiality agreement | RECORD | Translators acknowledge confidentiality, conflict and role boundaries. | Creates proof. |
| doctranslationops.confidentiality.secure_transfer | secure transfer | METHOD | Files move through approved secure upload, locked storage or encrypted channel. | Prevents leakage. |
| doctranslationops.assignment.translator_match | translator match | METHOD | Match considers language, credential, topic, urgency, availability and conflict. | Improves quality. |
| doctranslationops.assignment.assignment_record | assignment record | RECORD | Record stores translator, reviewer, document type, deadline and delivery method. | Creates accountability. |
| doctranslationops.assignment.conflict_check | conflict check | QUALITY_CHECK | Check screens adverse parties, personal relationship or sensitive role conflicts. | Protects neutrality. |
| doctranslationops.assignment.backup | backup assignment | METHOD | Backup handles no-show, overload, rare language or deadline risk. | Adds resilience. |
| doctranslationops.workflow.translation_brief | translation brief | METHOD | Brief explains purpose, audience, certification need and formatting constraints. | Guides translator. |
| doctranslationops.workflow.question_log | question log | RECORD | Questions capture unclear handwriting, missing context or ambiguous terms. | Improves accuracy. |
| doctranslationops.workflow.partial_delivery | partial delivery | METHOD | Urgent pages may be delivered first with clear status and remaining work. | Meets deadlines. |
| doctranslationops.workflow.version_control | version control | RECORD | Versions track draft, reviewed, corrected and delivered translations. | Prevents confusion. |
| doctranslationops.qa.peer_review | peer review | QUALITY_CHECK | Review checks completeness, terminology, numbers, names, dates and formatting. | Improves quality. |
| doctranslationops.qa.certification_check | certification check | QUALITY_CHECK | Certified output includes required statement, translator identity and date. | Supports acceptance. |
| doctranslationops.qa.red_flag | red flag | SAFETY_RULE | Legal or medical advice questions route to qualified professionals, not translator judgment. | Maintains boundary. |
| doctranslationops.qa.correction | correction process | METHOD | Corrections record issue, reviewer, translator response and final version. | Fixes errors. |
| doctranslationops.delivery.delivery_method | delivery method | RECORD | Method records pickup, email, secure portal, caseworker handoff or mail. | Controls handoff. |
| doctranslationops.delivery.confirmation | delivery confirmation | RECORD | Confirmation records recipient, date, files, version and unresolved issues. | Closes request. |
| doctranslationops.delivery.client_summary | client summary | METHOD | Summary explains what was translated and any limits or missing pages. | Sets expectations. |
| doctranslationops.delivery.archive_copy | archive copy | CONSTRAINT | Archive rule defines whether translated files are retained, deleted or returned. | Controls lifecycle. |
| doctranslationops.communication.status_update | status update | METHOD | Updates explain received, assigned, in review, delayed, delivered or blocked status. | Reduces uncertainty. |
| doctranslationops.communication.partner_update | partner update | METHOD | Partners receive aggregate language demand, deadlines, capacity and barriers. | Coordinates support. |
| doctranslationops.communication.language_gap | language gap alert | METHOD | Rare language gaps route to partner agencies or professional vendors. | Expands capacity. |
| doctranslationops.records.case_log | case log | RECORD | Log stores intake, files, assignment, review, delivery and deletion/retention decision. | Creates audit trail. |
| doctranslationops.records.cost | cost record | RECORD | Cost tracks volunteer hours, vendor fees, rush fees and funding source. | Supports finance. |
| doctranslationops.records.retention | retention rule | CONSTRAINT | Records follow privacy, legal, grant and document handling schedules. | Preserves audit. |
| doctranslationops.metrics.requests_completed | requests completed | MEASUREMENT | Count tracks completed translations by language, type and urgency. | Shows output. |
| doctranslationops.metrics.turnaround | turnaround time | MEASUREMENT | Time measures intake to delivery by document type and language. | Reveals delay. |
| doctranslationops.metrics.correction_rate | correction rate | MEASUREMENT | Rate tracks reviewed documents needing correction. | Improves QA. |
| doctranslationops.qa.sample_audit | sample audit | QUALITY_CHECK | Audit checks privacy, assignment fit, review proof and delivery confirmation. | Improves reliability. |
| doctranslationops.demob.closeout | closeout | METHOD | Closeout resolves open requests, archives permitted files and deletes restricted files. | Ends safely. |
| doctranslationops.review.after_action | after-action review | METHOD | Review captures language gaps, confidentiality, certified needs, turnaround and QA lessons. | Improves future translation. |
