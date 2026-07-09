# BATCH 396: Disaster Welfare Check Operations

**KnowledgeUnits:** 44  
**Namespace:** `welfarecheckops.*`  
**Scope:** requests, prioritization, field assignment, contact attempts, outcomes and referrals.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| welfarecheckops.intake.request_source | request source | RECORD | Source records family, hotline, agency, shelter, field crew or digital form origin. | Shows who asked. |
| welfarecheckops.intake.subject_identity | subject identity | RECORD | Identity captures name, age estimate, address, phone, language and known vulnerabilities. | Defines search target. |
| welfarecheckops.intake.location_uncertainty | location uncertainty | CONSTRAINT | Intake marks uncertain addresses, evacuated areas, shelters or last known locations. | Guides search planning. |
| welfarecheckops.intake.consent_note | consent note | RECORD | Consent or legal basis notes explain why information can be used or shared. | Protects privacy. |
| welfarecheckops.triage.priority_score | priority score | MODEL | Score weighs medical dependence, age, disability, isolation, hazard zone and time since contact. | Sorts workload. |
| welfarecheckops.triage.life_safety | life safety flag | SAFETY_RULE | Life-safety indicators route immediately to emergency responders. | Prevents delay. |
| welfarecheckops.triage.duplicate_request | duplicate request check | QUALITY_CHECK | Duplicate check links repeated requests for the same person or address. | Reduces wasted visits. |
| welfarecheckops.triage.service_boundary | service boundary | CONSTRAINT | Boundary defines when the request belongs to law enforcement, EMS, sheltering or casework. | Routes correctly. |
| welfarecheckops.assignment.team_assignment | team assignment | RECORD | Assignment lists team, vehicle, route, PPE, communications and check targets. | Deploys field work. |
| welfarecheckops.assignment.route_batch | route batch | METHOD | Route batch groups checks by geography, priority and access conditions. | Saves time. |
| welfarecheckops.assignment.safety_brief | safety briefing | SAFETY_RULE | Brief covers hazards, access limits, hostile situations, animals and weather. | Protects teams. |
| welfarecheckops.assignment.call_before_visit | call-before-visit | METHOD | Teams attempt phone or text before physical visit when appropriate. | Reduces unnecessary dispatch. |
| welfarecheckops.contact.phone_attempt | phone attempt | RECORD | Phone attempt records number, time, result, voicemail and callback instructions. | Builds contact history. |
| welfarecheckops.contact.text_attempt | text attempt | RECORD | Text attempt records message type, language, delivery status and response. | Expands reach. |
| welfarecheckops.contact.door_knock | door knock | METHOD | Door knock follows safety, identification, privacy and no-entry rules. | Checks residence safely. |
| welfarecheckops.contact.neighbor_info | neighbor information | RECORD | Neighbor information records source, reliability, date and privacy limits. | Adds context. |
| welfarecheckops.field.access_blocked | access blocked | CONSTRAINT | Blocked access records road closure, damage, security, floodwater or unsafe structure. | Explains incomplete check. |
| welfarecheckops.field.no_answer | no answer outcome | RECORD | No-answer outcome records evidence observed, attempts made and next action. | Avoids premature closure. |
| welfarecheckops.field.found_safe | found safe | RECORD | Safe outcome records condition, location, needs, consent and notification permission. | Closes simple cases. |
| welfarecheckops.field.needs_assistance | needs assistance | RECORD | Assistance outcome captures food, water, medical, transport, shelter or mobility needs. | Starts referral. |
| welfarecheckops.escalation.medical_referral | medical referral | METHOD | Medical needs are handed to EMS, clinic, shelter medical desk or public health pathway. | Connects care. |
| welfarecheckops.escalation.shelter_referral | shelter referral | METHOD | Shelter referral notes eligibility, transport need, accessible bed and receiving site. | Moves people to safety. |
| welfarecheckops.escalation.utility_referral | utility referral | METHOD | Utility needs include oxygen power, heat, cooling, water or critical equipment support. | Reduces service risk. |
| welfarecheckops.escalation.casework_referral | casework referral | METHOD | Casework referral covers long-term recovery, benefits, documents and unmet needs. | Supports recovery. |
| welfarecheckops.communication.requester_update | requester update | METHOD | Requester update shares allowed outcome detail, next steps and privacy limits. | Reduces anxiety. |
| welfarecheckops.communication.command_sitrep | command sitrep | RECORD | Situation report summarizes checks assigned, completed, urgent needs and blocked areas. | Informs operations. |
| welfarecheckops.communication.language | language support | METHOD | Interpreters or translated scripts support contact attempts and consent. | Improves access. |
| welfarecheckops.communication.do_not_share | do-not-share flag | SAFETY_RULE | Do-not-share flag restricts location or condition updates when safety requires. | Protects subjects. |
| welfarecheckops.records.case_log | case log | RECORD | Case log stores intake, triage, attempts, field notes, outcome and referrals. | Creates audit trail. |
| welfarecheckops.records.photo_note | photo note | RECORD | Photos document access barriers or posted notices only when policy allows. | Supports field evidence. |
| welfarecheckops.records.map_pin | map pin | RECORD | Map pin represents checked, pending, blocked or escalated locations. | Visualizes workload. |
| welfarecheckops.records.retention | retention rule | CONSTRAINT | Records follow emergency, privacy, health and public records schedules. | Controls lifecycle. |
| welfarecheckops.qa.supervisor_review | supervisor review | QUALITY_CHECK | Supervisor reviews high-priority closures, unresolved cases and safety incidents. | Prevents missed risk. |
| welfarecheckops.qa.outcome_consistency | outcome consistency | QUALITY_CHECK | QA checks that outcomes match attempts, evidence and referrals. | Improves reliability. |
| welfarecheckops.qa.backlog_review | backlog review | METHOD | Backlog review reprioritizes aging requests and blocked checks. | Keeps cases moving. |
| welfarecheckops.qa.duplicate_resolution | duplicate resolution | METHOD | Linked duplicate requests inherit the latest verified status and requester updates. | Reduces confusion. |
| welfarecheckops.metrics.completion_rate | completion rate | MEASUREMENT | Completion rate tracks finished checks versus assigned checks by priority. | Shows throughput. |
| welfarecheckops.metrics.time_to_contact | time to contact | MEASUREMENT | Time to contact measures intake-to-first-attempt and intake-to-confirmed-outcome. | Exposes delays. |
| welfarecheckops.metrics.referral_rate | referral rate | MEASUREMENT | Referral rate shows share needing medical, shelter, utility or casework help. | Plans resources. |
| welfarecheckops.metrics.blocked_area | blocked area count | MEASUREMENT | Blocked count tracks addresses not reachable by reason and geography. | Guides access work. |
| welfarecheckops.demob.case_closure | case closure | METHOD | Closure requires outcome, requester handling, referral status and unresolved notes. | Ends cases cleanly. |
| welfarecheckops.demob.transfer | case transfer | RECORD | Transfer moves unresolved welfare checks to recovery, social services or local agency owner. | Maintains continuity. |
| welfarecheckops.demob.data_archive | data archive | METHOD | Archive stores final logs, maps, exports and privacy restrictions. | Preserves records. |
| welfarecheckops.review.after_action | after-action review | METHOD | Review captures request surge, prioritization, field safety, referral gaps and privacy lessons. | Improves future checks. |
