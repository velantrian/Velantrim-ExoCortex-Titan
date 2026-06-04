# BATCH 431: Disaster Temporary Mail Pickup Operations

**KnowledgeUnits:** 44  
**Namespace:** `mailpickupops.*`  
**Scope:** intake, identity, mail holds, pickup sites, authorization, privacy and reconciliation.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| mailpickupops.intake.request_source | request source | RECORD | Source records resident, shelter, postal partner, caseworker, hotline or outreach desk. | Shows entry path. |
| mailpickupops.intake.resident_profile | resident profile | RECORD | Profile captures name, impacted address, temporary contact and safe-contact limits. | Defines mail owner. |
| mailpickupops.intake.mail_need | mail need | RECORD | Need records hold, forwarding, pickup, benefits mail, medications or legal notices. | Routes support. |
| mailpickupops.intake.urgency | urgency model | MODEL | Urgency weighs medicines, benefits, checks, court notices, identity papers and deadlines. | Prioritizes cases. |
| mailpickupops.identity.primary_id | primary ID | RECORD | Primary ID captures accepted government or postal identity document. | Verifies pickup. |
| mailpickupops.identity.alt_proof | alternate proof | METHOD | Alternate proof uses shelter roster, agency letter, caseworker attestation or prior mail. | Helps displaced residents. |
| mailpickupops.identity.name_variation | name variation | RECORD | Variation records spelling, former name, household member or business alias. | Prevents rejection. |
| mailpickupops.identity.failed_check | failed identity check | RECORD | Failed check records missing proof, mismatch, suspected fraud and referral path. | Controls risk. |
| mailpickupops.hold.mail_hold | mail hold request | RECORD | Hold request records address, dates, postal contact, confirmation and expiration. | Stops unsafe delivery. |
| mailpickupops.hold.forwarding | forwarding request | METHOD | Forwarding routes mail to temporary address, post office or approved pickup site. | Restores access. |
| mailpickupops.hold.release_rule | hold release rule | CONSTRAINT | Release defines who can end hold and what proof is required. | Protects mail. |
| mailpickupops.hold.status_check | hold status check | QUALITY_CHECK | Status check confirms active, pending, expired, rejected or superseded hold. | Keeps case accurate. |
| mailpickupops.site.pickup_site | pickup site | RECORD | Site records location, hours, staffing, storage, security and accessibility. | Organizes service. |
| mailpickupops.site.site_capacity | site capacity | MEASUREMENT | Capacity tracks mail bins, staff, queues, lockers and daily pickup volume. | Prevents overload. |
| mailpickupops.site.accessibility | accessibility check | QUALITY_CHECK | Site checks wheelchair access, signage, language support and safe waiting area. | Improves access. |
| mailpickupops.site.site_closure | site closure | METHOD | Closure records relocation, notice, transfer of mail and unresolved pickups. | Maintains continuity. |
| mailpickupops.authorization.authorized_pickup | authorized pickup | RECORD | Authorization records alternate person, relationship, proof, limits and expiration. | Enables help. |
| mailpickupops.authorization.revocation | revocation | METHOD | Revocation cancels prior authorization and notifies pickup site. | Protects resident. |
| mailpickupops.authorization.minor_mail | minor mail rule | CONSTRAINT | Minor-related mail follows guardian and safety rules. | Prevents improper release. |
| mailpickupops.authorization.business_mail | business mail rule | CONSTRAINT | Business mail requires owner, officer or agent proof. | Protects firms. |
| mailpickupops.privacy.minimum_data | minimum data | SAFETY_RULE | Program stores only identity, address, authorization and pickup data needed. | Reduces exposure. |
| mailpickupops.privacy.private_queue | private handling | METHOD | Sensitive mail questions move away from public line. | Preserves dignity. |
| mailpickupops.privacy.address_safety | address safety flag | SAFETY_RULE | Unsafe address disclosure routes to protected contact process. | Protects residents. |
| mailpickupops.privacy.secure_storage | secure storage | SAFETY_RULE | Mail and records are stored locked with role-limited access. | Prevents exposure. |
| mailpickupops.pickup.checkin | pickup check-in | RECORD | Check-in captures resident, ID check, mail batch, staff and time. | Tracks release. |
| mailpickupops.pickup.mail_match | mail match | QUALITY_CHECK | Staff match name, address, authorization and mail bundle before release. | Prevents wrong handoff. |
| mailpickupops.pickup.signature | pickup signature | RECORD | Signature or receipt confirms mail release and unresolved exceptions. | Creates audit trail. |
| mailpickupops.pickup.unclaimed_mail | unclaimed mail | RECORD | Unclaimed mail records aging, notice attempts, return or transfer action. | Controls backlog. |
| mailpickupops.reconcile.daily_count | daily count | MEASUREMENT | Count reconciles mail received, held, released, transferred and returned. | Shows custody. |
| mailpickupops.reconcile.exception_log | exception log | RECORD | Log captures missing mail, wrong bundle, damaged mail or identity dispute. | Supports resolution. |
| mailpickupops.reconcile.transfer | transfer record | RECORD | Transfer records mail moved between post office, shelter, kiosk or pickup site. | Preserves chain. |
| mailpickupops.reconcile.audit | custody audit | QUALITY_CHECK | Audit samples records against physical mail and release receipts. | Detects errors. |
| mailpickupops.communication.resident_notice | resident notice | METHOD | Notice explains pickup location, hours, ID needs and authorization options. | Guides residents. |
| mailpickupops.communication.partner_update | partner update | METHOD | Partners receive site status, ID barriers, backlogs and policy changes. | Aligns referrals. |
| mailpickupops.communication.language | language support | METHOD | Instructions use common local languages and plain mail terms. | Improves access. |
| mailpickupops.records.case_log | case log | RECORD | Log stores intake, identity, holds, pickup, authorization and closeout. | Creates continuity. |
| mailpickupops.records.retention | retention rule | CONSTRAINT | Mail custody, identity, authorization and privacy records follow retention schedules. | Preserves audit. |
| mailpickupops.records.protected_note | protected note | RECORD | Protected note flags address-safety or custody concerns without exposing details publicly. | Controls sensitive cases. |
| mailpickupops.metrics.pickups_completed | pickups completed | MEASUREMENT | Count tracks completed pickups by site, day and issue type. | Shows output. |
| mailpickupops.metrics.unclaimed_rate | unclaimed rate | MEASUREMENT | Rate tracks mail not picked up within target period. | Reveals barriers. |
| mailpickupops.metrics.id_barrier | ID barrier count | MEASUREMENT | Count tracks failed pickups due to identity or authorization gaps. | Guides support. |
| mailpickupops.qa.supervisor_review | supervisor review | QUALITY_CHECK | Review checks disputes, protected addresses, authorizations and custody gaps. | Improves reliability. |
| mailpickupops.demob.closeout | closeout | METHOD | Closeout transfers remaining mail, archives logs and notifies residents. | Ends operation. |
| mailpickupops.review.after_action | after-action review | METHOD | Review captures identity barriers, site flow, privacy, custody and partner coordination lessons. | Improves future mail support. |
