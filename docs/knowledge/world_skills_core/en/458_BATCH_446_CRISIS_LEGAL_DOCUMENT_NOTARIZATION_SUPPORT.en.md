# BATCH 446: Crisis Legal Document Notarization Support

**KnowledgeUnits:** 44  
**Namespace:** `notarysupportops.*`  
**Scope:** intake, identity, appointment scheduling, mobile notary, records and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| notarysupportops.intake.request_source | request source | RECORD | Source records legal clinic, survivor center, shelter desk, caseworker, hotline, court partner or self-referral. | Shows entry path. |
| notarysupportops.intake.client_profile | client profile | RECORD | Profile captures contact, language, safe contact, location, mobility barrier and document urgency. | Defines support. |
| notarysupportops.intake.document_type | document type | RECORD | Type records affidavit, authorization, school form, insurance form, benefits form, power-related document or sworn statement. | Frames request. |
| notarysupportops.intake.urgency_score | urgency score | MODEL | Score weighs filing deadline, benefits cutoff, court date, school enrollment, housing need and travel barrier. | Prioritizes appointments. |
| notarysupportops.eligibility.crisis_link | crisis link | CONTROL | Link verifies notarization need is related to displacement, lost documents, recovery claims or urgent access. | Targets support. |
| notarysupportops.eligibility.scope_boundary | scope boundary | CONTROL | Boundary separates notary logistics from legal advice, drafting, representation or document validity opinions. | Prevents role confusion. |
| notarysupportops.eligibility.duplicate_check | duplicate check | CONTROL | Check compares client, document type, appointment, notary and prior support records. | Avoids duplicate scheduling. |
| notarysupportops.identity.id_available | ID available | RECORD | Record captures government ID, temporary ID, witness option, credible identifying witness or missing-ID issue. | Prepares appointment. |
| notarysupportops.identity.name_match | name match | CONTROL | Match compares document name, ID name, translation, spelling variation and supporting records. | Prevents rejection. |
| notarysupportops.identity.witness_need | witness need | RECORD | Need records required witnesses, witness eligibility, contact and scheduling constraints. | Avoids failed appointment. |
| notarysupportops.identity.language_support | language support | PROCESS | Support arranges interpreter, translated instructions or bilingual staff where allowed. | Improves access. |
| notarysupportops.documents.completeness_check | completeness check | CONTROL | Check confirms document is filled, unsigned where required, dated correctly and ready for notary process. | Prevents wasted visit. |
| notarysupportops.documents.legal_referral | legal referral | PROCESS | Referral sends drafting, advice, contested issues or complex authority questions to legal professionals. | Keeps scope safe. |
| notarysupportops.documents.copy_plan | copy plan | PROCESS | Plan handles original, copies, scan, upload, mailing and client retention needs. | Supports next filing. |
| notarysupportops.documents.secure_storage | secure storage | CONTROL | Storage protects documents awaiting appointment from loss, disclosure or unauthorized access. | Preserves privacy. |
| notarysupportops.scheduling.appointment_slot | appointment slot | RECORD | Slot records notary, location, time, duration, required IDs, witnesses and accessibility needs. | Organizes service. |
| notarysupportops.scheduling.reminder_process | reminder process | PROCESS | Reminder confirms time, documents, ID, witnesses, interpreter and travel plan. | Reduces no-shows. |
| notarysupportops.scheduling.no_show | no-show process | PROCESS | Process logs missed appointment, contact attempts, reschedule rule and urgency review. | Keeps cases moving. |
| notarysupportops.scheduling.priority_queue | priority queue | MODEL | Queue orders cases by deadline, vulnerability, travel barrier, document readiness and notary availability. | Allocates fairly. |
| notarysupportops.mobile.mobile_request | mobile notary request | RECORD | Request records site, client mobility barrier, security, privacy space and document readiness. | Enables field service. |
| notarysupportops.mobile.site_readiness | site readiness | CONTROL | Readiness checks safe location, table, lighting, privacy, witnesses, ID and access permission. | Prevents failed visit. |
| notarysupportops.mobile.route_plan | route plan | PROCESS | Route groups mobile stops by urgency, geography, notary availability and security constraints. | Saves time. |
| notarysupportops.mobile.safety_check | safety check | CONTROL | Check reviews weather, road access, site security, client distress and stop-work triggers. | Protects staff. |
| notarysupportops.notary.roster | notary roster | RECORD | Roster lists notaries, commission status, jurisdiction, language, mobile capacity and availability. | Guides assignment. |
| notarysupportops.notary.commission_check | commission check | CONTROL | Check verifies active commission, jurisdiction, remote-notary rules and expiration. | Supports compliance. |
| notarysupportops.notary.conflict_check | conflict check | CONTROL | Check flags notary conflicts, personal interest, prohibited document type or role incompatibility. | Protects validity. |
| notarysupportops.fees.fee_waiver | fee waiver | RECORD | Waiver records eligible fee support, funding source, approval and notary payment arrangement. | Reduces access barrier. |
| notarysupportops.fees.invoice_match | invoice match | CONTROL | Match compares appointment, notary service, fee cap, waiver and payment request. | Prevents overpayment. |
| notarysupportops.fees.transport_support | transport support | PROCESS | Support coordinates transit voucher, ride, mobile notary or alternate site when travel blocks service. | Improves access. |
| notarysupportops.privacy.minimum_data | minimum data | CONTROL | Minimum data limits records to scheduling, identity readiness, document type and closure status. | Reduces exposure. |
| notarysupportops.privacy.safe_contact | safe contact | CONTROL | Safe contact records whether calls, texts, emails or voicemail may mention legal document support. | Protects clients. |
| notarysupportops.privacy.document_handling | document handling | CONTROL | Handling restricts viewing, copying, scanning and storage to necessary authorized staff. | Preserves confidentiality. |
| notarysupportops.records.case_file | case file | RECORD | File links intake, identity readiness, appointment, notary, fee support, proof and closeout. | Supports audit. |
| notarysupportops.records.appointment_log | appointment log | RECORD | Log tracks scheduled, completed, rescheduled, no-show, canceled, mobile and referred appointments. | Shows flow. |
| notarysupportops.records.exception_log | exception log | RECORD | Log captures missing ID, incomplete document, witness absence, notary conflict, unsafe site or fee issue. | Enables review. |
| notarysupportops.communication.client_update | client update | PROCESS | Update explains appointment, needed ID, witness, document readiness, fee support and next filing step. | Reduces confusion. |
| notarysupportops.communication.partner_update | partner update | PROCESS | Update informs legal clinics or caseworkers of scheduling status without unnecessary document detail. | Coordinates care. |
| notarysupportops.communication.referral_handoff | referral handoff | PROCESS | Handoff routes legal advice, translation, replacement ID, court filing or benefits submission needs. | Completes pathway. |
| notarysupportops.metrics.completion_rate | completion rate | METRIC | Rate compares eligible requests, scheduled appointments and completed notarizations. | Measures service. |
| notarysupportops.metrics.failed_reason_mix | failed reason mix | METRIC | Mix groups missing ID, incomplete form, no witness, no-show, conflict, mobile access and fee barrier. | Shows bottlenecks. |
| notarysupportops.metrics.deadline_met | deadline met | METRIC | Metric tracks notarizations completed before filing, school, benefits, housing or court deadlines. | Measures impact. |
| notarysupportops.closeout.client_confirmation | client confirmation | PROCESS | Confirmation verifies notarized document received, copies handled and next submission route understood. | Closes loop. |
| notarysupportops.closeout.record_retention | record retention | CONTROL | Retention defines what program records are kept, redacted, archived or destroyed. | Protects privacy. |
| notarysupportops.closeout.after_action | after-action note | RECORD | Note captures ID barriers, mobile demand, notary capacity, privacy issues and referral gaps. | Improves next cycle. |
