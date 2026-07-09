# BATCH 413: Recovery Grant Application Document Review Operations

**KnowledgeUnits:** 44  
**Namespace:** `grantdocreviewops.*`  
**Scope:** completeness, eligibility, budget, attachments, signatures, submission and corrections.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| grantdocreviewops.intake.request_source | request source | RECORD | Source records applicant, caseworker, nonprofit, portal, clinic or agency referral. | Shows entry path. |
| grantdocreviewops.intake.grant_program | grant program | RECORD | Program record captures funder, grant name, deadline, purpose and applicant type. | Defines review. |
| grantdocreviewops.intake.applicant_profile | applicant profile | RECORD | Profile captures household, organization or business identity and contact. | Supports eligibility. |
| grantdocreviewops.intake.deadline | deadline capture | SAFETY_RULE | Deadline records due date, time zone, portal cutoff and submission method. | Prevents late filing. |
| grantdocreviewops.eligibility.basic_check | basic eligibility | QUALITY_CHECK | Check compares applicant, geography, disaster impact, income or entity status to rules. | Avoids wasted effort. |
| grantdocreviewops.eligibility.duplication | duplication check | QUALITY_CHECK | Review checks insurance, prior grants, loans, donations or benefits overlap. | Prevents duplicate funding. |
| grantdocreviewops.eligibility.exclusion | exclusion check | CONSTRAINT | Exclusions identify ineligible costs, entities, locations or time periods. | Reduces denial risk. |
| grantdocreviewops.eligibility.exception | exception note | RECORD | Exception note documents waiver, special rule or funder clarification. | Preserves rationale. |
| grantdocreviewops.completeness.checklist | completeness checklist | RECORD | Checklist lists required forms, attachments, budget, signatures and certifications. | Organizes packet. |
| grantdocreviewops.completeness.missing_item | missing item | RECORD | Missing item records owner, source, due time and workaround. | Drives cleanup. |
| grantdocreviewops.completeness.version_control | version control | METHOD | Versions track draft, revised, final and submitted documents. | Prevents wrong file. |
| grantdocreviewops.completeness.final_scan | final scan | QUALITY_CHECK | Final scan verifies required fields, page limits, filenames and attachments. | Improves submission. |
| grantdocreviewops.budget.cost_category | cost category | RECORD | Budget categories map costs to allowed uses and funding codes. | Clarifies request. |
| grantdocreviewops.budget.cost_basis | cost basis | RECORD | Basis records estimate, invoice, receipt, quote or standard rate. | Supports amount. |
| grantdocreviewops.budget.match_funds | match funds | RECORD | Match record captures required match, source, documentation and restrictions. | Meets conditions. |
| grantdocreviewops.budget.math_check | math check | QUALITY_CHECK | Review checks totals, subtotals, percentages and narrative-budget consistency. | Prevents errors. |
| grantdocreviewops.attachments.identity | identity attachment | RECORD | Identity attachment supports applicant status, ownership, residency or authority. | Proves applicant. |
| grantdocreviewops.attachments.damage | damage attachment | RECORD | Damage evidence includes photos, inspection, loss statement, insurance or repair estimate. | Supports need. |
| grantdocreviewops.attachments.finance | financial attachment | RECORD | Finance documents include income, tax, bank, payroll, receipts or hardship proof. | Supports eligibility. |
| grantdocreviewops.attachments.naming | file naming rule | METHOD | Files use program-required names, applicant ID and document type. | Prevents portal confusion. |
| grantdocreviewops.signatures.signature_required | signature required | CONSTRAINT | Signature list identifies who must sign forms, certifications and releases. | Prevents invalid submission. |
| grantdocreviewops.signatures.authority | signing authority | QUALITY_CHECK | Authority verifies officer, owner, guardian, power of attorney or applicant role. | Ensures validity. |
| grantdocreviewops.signatures.date_check | date check | QUALITY_CHECK | Signature dates match current version and program timing rules. | Avoids rejection. |
| grantdocreviewops.signatures.e_signature | e-signature path | METHOD | Electronic signature follows funder, identity and consent requirements. | Enables remote filing. |
| grantdocreviewops.submission.portal_account | portal account | RECORD | Account record captures login owner, MFA, applicant ID and support contact. | Enables submission. |
| grantdocreviewops.submission.upload_order | upload order | METHOD | Upload order follows funder categories and avoids duplicate attachments. | Reduces errors. |
| grantdocreviewops.submission.confirmation | confirmation proof | RECORD | Proof records confirmation number, timestamp, email receipt or screenshot. | Verifies filing. |
| grantdocreviewops.submission.backup_method | backup method | METHOD | Backup uses email, mail, dropbox or agency contact if portal fails. | Prevents missed deadline. |
| grantdocreviewops.corrections.deficiency_notice | deficiency notice | RECORD | Notice records funder request, missing item, deadline and response method. | Starts correction. |
| grantdocreviewops.corrections.response_plan | response plan | METHOD | Plan assigns owner, document source, review and submission time. | Keeps response organized. |
| grantdocreviewops.corrections.resubmission | resubmission proof | RECORD | Proof captures corrected upload, email, mail tracking or portal status. | Closes deficiency. |
| grantdocreviewops.corrections.withdrawal | withdrawal record | RECORD | Withdrawal records applicant decision, reason, funder notice and alternate referral. | Ends packet cleanly. |
| grantdocreviewops.communication.applicant_update | applicant update | METHOD | Update explains missing items, risks, deadline, submission status and next steps. | Reduces uncertainty. |
| grantdocreviewops.communication.funder_question | funder question | RECORD | Question log captures clarification request, answer, date and staff. | Preserves guidance. |
| grantdocreviewops.communication.partner_handoff | partner handoff | METHOD | Handoff gives caseworker or advisor packet status and unresolved issues. | Coordinates support. |
| grantdocreviewops.communication.language | language support | METHOD | Translation or interpreter support helps applicant understand forms and certifications. | Improves access. |
| grantdocreviewops.privacy.minimum_data | minimum data | SAFETY_RULE | Review stores only documents needed for grant and audit. | Reduces exposure. |
| grantdocreviewops.privacy.secure_storage | secure storage | SAFETY_RULE | Sensitive financial and identity files are restricted and encrypted or locked. | Protects applicant. |
| grantdocreviewops.records.case_log | case log | RECORD | Log stores review checklist, eligibility notes, budget, submission and corrections. | Creates continuity. |
| grantdocreviewops.metrics.completion_rate | completion rate | MEASUREMENT | Rate tracks packets completed, submitted, deficient, denied or withdrawn. | Shows throughput. |
| grantdocreviewops.metrics.deficiency_rate | deficiency rate | MEASUREMENT | Deficiency rate tracks funder correction requests by category. | Improves review. |
| grantdocreviewops.metrics.time_to_submit | time to submit | MEASUREMENT | Time measures intake to confirmed submission. | Reveals delays. |
| grantdocreviewops.qa.peer_review | peer review | QUALITY_CHECK | Peer review samples high-value or deadline-sensitive applications before submission. | Reduces mistakes. |
| grantdocreviewops.review.after_action | after-action review | METHOD | Review captures eligibility confusion, attachment gaps, portal failures and correction lessons. | Improves future reviews. |
