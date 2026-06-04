# BATCH 447: Disaster Temporary ID Appointment Support

**KnowledgeUnits:** 44  
**Namespace:** `tempidapptops.*`  
**Scope:** intake, identity proof, agency scheduling, transport, fee support, reminders and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| tempidapptops.intake.request_source | request source | RECORD | Source records shelter desk, survivor center, caseworker, school liaison, legal clinic or hotline. | Shows entry path. |
| tempidapptops.intake.client_profile | client profile | RECORD | Profile captures contact, safe contact, language, current address, mobility limits and urgency. | Defines support. |
| tempidapptops.intake.id_loss_context | ID loss context | RECORD | Context notes lost, stolen, destroyed, expired, inaccessible or never-issued identification. | Frames need. |
| tempidapptops.intake.deadline | deadline | RECORD | Deadline records benefits, housing, job, school, travel, medical or court date requiring ID. | Prioritizes cases. |
| tempidapptops.eligibility.disaster_link | disaster link | CONTROL | Link verifies the ID barrier is related to disaster damage, displacement or service disruption. | Targets assistance. |
| tempidapptops.eligibility.document_type | document type | RECORD | Type separates temporary ID, replacement card, state ID, driver license, school ID or agency credential. | Routes correctly. |
| tempidapptops.eligibility.duplicate_check | duplicate check | CONTROL | Check compares client, agency, appointment, document type and prior support records. | Avoids duplication. |
| tempidapptops.proof.proof_inventory | proof inventory | RECORD | Inventory lists birth record, address proof, school record, benefits letter, witness form or police report. | Shows readiness. |
| tempidapptops.proof.missing_proof | missing proof state | STATE | State flags missing, damaged, inconsistent, translated or agency-rejected proof. | Triggers help. |
| tempidapptops.proof.alternate_proof | alternate proof | MODEL | Alternate proof maps agency-accepted substitutes for address, identity, residency or disaster loss. | Solves blockers. |
| tempidapptops.proof.copy_packet | copy packet | PROCESS | Packet organizes copies, originals, translations, affidavits and appointment checklist. | Reduces failed visits. |
| tempidapptops.agency.agency_directory | agency directory | RECORD | Directory lists offices, hours, appointment links, ID requirements, fees and accessibility notes. | Guides scheduling. |
| tempidapptops.agency.requirement_check | requirement check | CONTROL | Check confirms current agency rules for proof, photos, forms, payment and disaster exceptions. | Prevents bad advice. |
| tempidapptops.agency.exception_path | exception path | PROCESS | Path identifies emergency, disaster, fee-waiver, mobile unit or supervisor review options. | Opens access. |
| tempidapptops.scheduling.slot_search | slot search | PROCESS | Search compares locations, dates, accessibility, transport options and deadline fit. | Finds workable appointment. |
| tempidapptops.scheduling.appointment_record | appointment record | RECORD | Record captures agency, slot, confirmation number, documents needed, travel plan and reminder schedule. | Controls case. |
| tempidapptops.scheduling.reschedule_rule | reschedule rule | CONTROL | Rule defines when to reschedule for missing proof, illness, transport failure or agency closure. | Avoids wasted trips. |
| tempidapptops.scheduling.group_booking | group booking | PROCESS | Booking clusters clients by shelter, site, agency and transport route where allowed. | Saves capacity. |
| tempidapptops.transport.transport_need | transport need | RECORD | Need records mobility barrier, distance, transit access, caregiver, child accompaniment or safety risk. | Plans travel. |
| tempidapptops.transport.voucher_issue | transport voucher | RECORD | Voucher records ride, transit pass, fuel support, accessible vehicle or volunteer driver. | Enables attendance. |
| tempidapptops.transport.pickup_window | pickup window | RECORD | Window captures pickup time, location, driver contact, return plan and no-show rule. | Reduces missed appointments. |
| tempidapptops.transport.failed_transport | failed transport | STATE | State logs no ride, late driver, client no-show, unsafe route or agency delay. | Supports rescheduling. |
| tempidapptops.fees.fee_amount | fee amount | RECORD | Amount records agency fee, photo fee, card fee, mailing fee and waiver eligibility. | Shows cost barrier. |
| tempidapptops.fees.fee_support | fee support | PROCESS | Support issues voucher, payment authorization, nonprofit fund or agency waiver request. | Removes barrier. |
| tempidapptops.fees.receipt_match | receipt match | CONTROL | Match compares appointment, fee approval, receipt, card type and client confirmation. | Prevents overpayment. |
| tempidapptops.forms.form_packet | form packet | RECORD | Packet records completed application, disaster statement, address form, interpreter request and consent. | Prepares visit. |
| tempidapptops.forms.signature_check | signature check | CONTROL | Check confirms where signatures must happen before staff, agency or notary. | Prevents invalid forms. |
| tempidapptops.forms.translation_need | translation need | RECORD | Need records language, document type, certified translation requirement and due date. | Supports access. |
| tempidapptops.reminders.reminder_schedule | reminder schedule | PROCESS | Schedule sends proof checklist, time, location, transport and safe-contact reminders. | Reduces no-shows. |
| tempidapptops.reminders.day_before_check | day-before check | PROCESS | Check confirms documents, ride, caregiver, interpreter, payment and agency status. | Prevents failure. |
| tempidapptops.reminders.missed_contact | missed contact | STATE | State records unanswered calls, bounced text, shelter move or changed number. | Triggers outreach. |
| tempidapptops.privacy.safe_contact | safe contact | CONTROL | Safe contact defines whether ID support can be mentioned by call, text, email or voicemail. | Protects clients. |
| tempidapptops.privacy.minimum_data | minimum data | CONTROL | Minimum data limits records to appointment support, proof readiness and closure. | Reduces exposure. |
| tempidapptops.privacy.document_handling | document handling | CONTROL | Handling restricts copies, scans, storage and transport of identity documents. | Prevents misuse. |
| tempidapptops.records.case_file | case file | RECORD | File links intake, proof, appointment, transport, fees, reminders and closeout. | Supports audit. |
| tempidapptops.records.status_board | status board | RECORD | Board tracks proof pending, scheduled, reminded, attended, issued, mailed, failed and closed. | Shows workflow. |
| tempidapptops.records.exception_log | exception log | RECORD | Log captures missing proof, no appointment, no-show, agency rejection, fee issue or transport failure. | Enables review. |
| tempidapptops.communication.client_update | client update | PROCESS | Update explains proof needs, appointment plan, transport, fee support and next step. | Reduces confusion. |
| tempidapptops.communication.partner_handoff | partner handoff | PROCESS | Handoff routes legal, translation, vital records, benefits or housing needs to partner services. | Completes pathway. |
| tempidapptops.metrics.attendance_rate | attendance rate | METRIC | Rate compares scheduled appointments, attended appointments and no-shows. | Measures effectiveness. |
| tempidapptops.metrics.issuance_rate | issuance rate | METRIC | Rate tracks attended appointments that produce temporary or replacement ID. | Shows outcome. |
| tempidapptops.metrics.failure_reason_mix | failure reason mix | METRIC | Mix groups proof gap, fee barrier, transport failure, agency closure, no-show and rejection. | Reveals bottlenecks. |
| tempidapptops.closeout.client_confirmation | client confirmation | PROCESS | Confirmation verifies ID issued, mailed, pending or denied and records follow-up need. | Closes loop. |
| tempidapptops.closeout.after_action | after-action note | RECORD | Note captures agency bottlenecks, proof gaps, transport issues and waiver lessons. | Improves next cycle. |
