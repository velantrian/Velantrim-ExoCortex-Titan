# BATCH 450: Crisis Vital Records Fee Waiver Support

**KnowledgeUnits:** 44  
**Namespace:** `vitalfeeops.*`  
**Scope:** intake, eligibility, document type, proof, agency forms, submission and status tracking.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| vitalfeeops.intake.request_source | request source | RECORD | Source records survivor center, legal clinic, caseworker, shelter desk, benefits office, school or hotline. | Shows entry path. |
| vitalfeeops.intake.client_profile | client profile | RECORD | Profile captures contact, safe contact, language, current location, household role and deadline. | Defines support. |
| vitalfeeops.intake.record_need | record need | RECORD | Need records birth, death, marriage, divorce, adoption, name-change or amended record request. | Frames document path. |
| vitalfeeops.intake.urgency_score | urgency score | MODEL | Score weighs ID replacement, benefits, school, housing, probate, funeral, employment and court deadlines. | Prioritizes cases. |
| vitalfeeops.eligibility.crisis_link | crisis link | CONTROL | Link verifies records or fee support need is tied to disaster loss, displacement, death or urgent recovery. | Targets aid. |
| vitalfeeops.eligibility.fee_waiver_rule | fee waiver rule | CONTROL | Rule maps agency criteria for fee waiver, indigence, disaster declaration or partner payment. | Guides eligibility. |
| vitalfeeops.eligibility.relationship_check | relationship check | CONTROL | Check verifies requester relationship or authority for restricted vital records. | Prevents rejection. |
| vitalfeeops.eligibility.duplicate_check | duplicate check | CONTROL | Check compares client, record type, agency, submitted form and prior payment support. | Avoids duplicate requests. |
| vitalfeeops.document.document_type | document type | RECORD | Type separates certified copy, informational copy, amendment, search letter or delayed registration. | Routes correctly. |
| vitalfeeops.document.jurisdiction | jurisdiction | RECORD | Jurisdiction records state, county, municipality, country, agency office and filing location. | Finds correct agency. |
| vitalfeeops.document.quantity_needed | quantity needed | RECORD | Quantity records required copies, mailing needs, filing purpose and fee impact. | Controls costs. |
| vitalfeeops.proof.identity_proof | identity proof | RECORD | Proof records accepted ID, temporary ID, witness, notarized statement or agency exception. | Prepares submission. |
| vitalfeeops.proof.relationship_proof | relationship proof | RECORD | Proof captures parent, spouse, child, representative, executor or court-authorized status. | Supports access. |
| vitalfeeops.proof.disaster_proof | disaster proof | RECORD | Proof records loss statement, FEMA-style letter, shelter record, police report or caseworker attestation. | Supports waiver. |
| vitalfeeops.proof.missing_proof | missing proof state | STATE | State flags missing ID, inconsistent names, no relationship proof, foreign record or damaged documents. | Triggers referral. |
| vitalfeeops.forms.form_selection | form selection | PROCESS | Selection chooses correct agency form, waiver form, affidavit, mailing form and payment form. | Prevents rejection. |
| vitalfeeops.forms.completeness_check | completeness check | CONTROL | Check confirms fields, signatures, dates, copy quality, notarization and attachments. | Reduces returns. |
| vitalfeeops.forms.signature_rule | signature rule | CONTROL | Rule states which signatures must be wet, notarized, witnessed or agency-present. | Avoids invalid submission. |
| vitalfeeops.forms.translation_need | translation need | RECORD | Need records translated documents, certified translation requirement and deadline. | Supports complex cases. |
| vitalfeeops.fees.fee_amount | fee amount | RECORD | Amount records search, copy, amendment, expedite, mailing, notary and card processing fees. | Shows cost. |
| vitalfeeops.fees.waiver_packet | waiver packet | RECORD | Packet links fee waiver form, proof, hardship note, disaster proof and approval path. | Builds waiver request. |
| vitalfeeops.fees.partner_payment | partner payment | PROCESS | Payment coordinates nonprofit voucher, agency account, money order, card payment or reimbursement. | Removes barrier. |
| vitalfeeops.fees.receipt_match | receipt match | CONTROL | Match compares payment approval, receipt, agency, record type, quantity and submission. | Prevents overpayment. |
| vitalfeeops.submission.submission_method | submission method | MODEL | Method separates in-person, mail, online, drop box, consulate, court clerk or partner handoff. | Selects workflow. |
| vitalfeeops.submission.packet_scan | packet scan | PROCESS | Scan records submitted documents, redactions, receipt, tracking and client copy where allowed. | Preserves proof. |
| vitalfeeops.submission.mail_tracking | mail tracking | RECORD | Tracking captures carrier, address, date, tracking number, return envelope and delivery status. | Tracks mailed cases. |
| vitalfeeops.submission.agency_receipt | agency receipt | RECORD | Receipt records agency confirmation, file number, expected processing time and contact route. | Enables status checks. |
| vitalfeeops.status.status_board | status board | RECORD | Board tracks proof pending, waiver pending, submitted, agency review, returned, issued, mailed and closed. | Shows pipeline. |
| vitalfeeops.status.status_check | status check | PROCESS | Check follows agency timeline, reference number, mail tracking and escalation rules. | Prevents forgotten cases. |
| vitalfeeops.status.returned_packet | returned packet | STATE | State records reason for return such as missing proof, wrong fee, bad form, signature or jurisdiction. | Triggers correction. |
| vitalfeeops.status.expedite_request | expedite request | PROCESS | Request documents urgent deadline, agency criteria, fee support and escalation contact. | Speeds critical cases. |
| vitalfeeops.privacy.minimum_data | minimum data | CONTROL | Minimum data limits sensitive identity, family and legal details to required processing. | Reduces exposure. |
| vitalfeeops.privacy.safe_contact | safe contact | CONTROL | Safe contact defines whether calls, texts, email or voicemail may mention vital records. | Protects clients. |
| vitalfeeops.privacy.document_storage | document storage | CONTROL | Storage defines secure copies, redaction, retention, destruction and access permissions. | Protects records. |
| vitalfeeops.records.case_file | case file | RECORD | File links intake, eligibility, proof, waiver, submission, payment, status and closeout. | Supports audit. |
| vitalfeeops.records.exception_log | exception log | RECORD | Log captures missing proof, rejected waiver, returned packet, payment issue, wrong agency or mail loss. | Enables review. |
| vitalfeeops.communication.client_update | client update | PROCESS | Update explains proof needs, waiver status, submission date, expected timeline and next step. | Reduces uncertainty. |
| vitalfeeops.communication.agency_contact | agency contact | PROCESS | Contact asks agency about requirements, status, correction options or disaster exceptions. | Solves blockers. |
| vitalfeeops.communication.referral_handoff | referral handoff | PROCESS | Handoff routes complex legal status, amendment, foreign record, custody or probate issue to specialists. | Keeps scope safe. |
| vitalfeeops.metrics.waiver_approval_rate | waiver approval rate | METRIC | Rate compares waiver requests, approvals, denials and pending cases. | Measures access. |
| vitalfeeops.metrics.processing_time | processing time | METRIC | Time measures submission to issued record or final agency response. | Shows delay. |
| vitalfeeops.metrics.return_reason_mix | return reason mix | METRIC | Mix groups proof gap, fee issue, wrong form, wrong agency, signature and identity mismatch. | Reveals bottlenecks. |
| vitalfeeops.closeout.client_receipt | client receipt | PROCESS | Receipt confirms client received record, denial, refund, correction request or next referral. | Closes loop. |
| vitalfeeops.closeout.after_action | after-action note | RECORD | Note captures agency barriers, waiver lessons, proof needs and funding gaps. | Improves next cycle. |
