# BATCH 359: Emergency Family Reunification Operations

**KnowledgeUnits:** 44  
**Namespace:** `familyreunifyops.*`  
**Scope:** inquiries, identity checks, privacy, matching, welfare calls, notifications and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| familyreunifyops.intake.inquiry_id | inquiry ID | RECORD | Inquiry ID links requester, missing person, event, time, channel and status. | Creates traceable reunification case. |
| familyreunifyops.intake.requester_info | requester information | RECORD | Requester record captures contact, relationship, language and urgency. | Enables safe follow-up. |
| familyreunifyops.intake.missing_profile | missing person profile | RECORD | Profile records name, age, description, last known place and special needs. | Supports matching. |
| familyreunifyops.intake.event_link | event link | RECORD | Case links to shelter, evacuation, hospital, school, disaster zone or incident. | Narrows search context. |
| familyreunifyops.identity.requester_check | requester identity check | SAFETY_RULE | Requester identity and relationship are checked before private information release. | Protects evacuees and survivors. |
| familyreunifyops.identity.subject_check | subject identity check | METHOD | Subject identity is matched with name, date, photo, documents or trusted witness. | Reduces false matches. |
| familyreunifyops.identity.proxy | proxy requester | CONSTRAINT | Attorneys, agencies or friends need lawful basis or consent for sensitive data. | Avoids unauthorized disclosure. |
| familyreunifyops.identity.minor_guard | minor safeguard | SAFETY_RULE | Minor inquiries require extra guardianship and safeguarding checks. | Protects children. |
| familyreunifyops.privacy.consent | consent to notify | RECORD | Located person consent is recorded before sharing location unless law requires otherwise. | Respects autonomy. |
| familyreunifyops.privacy.safe_contact | safe contact screen | SAFETY_RULE | Staff screen for domestic violence, stalking, custody or trafficking risk before notification. | Prevents harmful disclosure. |
| familyreunifyops.privacy.minimum | minimum disclosure | CONSTRAINT | Notifications disclose only needed facts, not full shelter or medical details unless approved. | Limits privacy exposure. |
| familyreunifyops.privacy.confidential_site | confidential site | CONSTRAINT | Some shelters, hospitals or protection sites cannot be disclosed publicly. | Protects vulnerable people. |
| familyreunifyops.matching.match_queue | match queue | METHOD | Cases enter queue by urgency, age, vulnerability and available clues. | Prioritizes scarce staff time. |
| familyreunifyops.matching.name_variants | name variants | METHOD | Matching checks spelling, aliases, transliteration and nicknames. | Avoids missed matches. |
| familyreunifyops.matching.demographic_match | demographic match | MODEL | Match considers age, gender, description, language, address and companions. | Improves confidence. |
| familyreunifyops.matching.location_match | location match | MODEL | Last known location is compared with shelter rosters, transport logs and facility lists. | Narrows search. |
| familyreunifyops.matching.photo_match | photo match | METHOD | Photo comparison is used with consent and human review. | Helps when names are uncertain. |
| familyreunifyops.matching.false_positive | false positive | FAILURE_MODE | False positive occurs when similar identity details lead to wrong match. | Requires verification before release. |
| familyreunifyops.sources.shelter_roster | shelter roster | RECORD | Shelter roster can confirm presence, party, needs and consent status. | Connects inquiries to shelter data. |
| familyreunifyops.sources.hospital_liaison | hospital liaison | METHOD | Hospital liaison follows medical privacy rules while checking patient status. | Handles health-related searches. |
| familyreunifyops.sources.school_list | school list | METHOD | School or childcare lists support child reunification under safeguarding rules. | Protects minors during evacuation. |
| familyreunifyops.sources.transport_manifest | transport manifest | RECORD | Transport manifests show evacuation buses, pickup points and destinations. | Tracks movement. |
| familyreunifyops.welfare.welfare_call | welfare call | METHOD | Welfare call verifies safety and preferred contact route of located person. | Confirms status before notification. |
| familyreunifyops.welfare.unreachable | unreachable subject | METHOD | Unreachable status triggers repeat checks, field referral or partner query. | Keeps search active. |
| familyreunifyops.welfare.vulnerable | vulnerable person flag | MODEL | Disability, age, medical need or isolation increases follow-up priority. | Focuses protective action. |
| familyreunifyops.welfare.deceased_protocol | deceased protocol | SAFETY_RULE | Death notification follows coroner, law enforcement or official family liaison rules. | Prevents improper notification. |
| familyreunifyops.notification.match_notice | match notification | METHOD | Match notice gives approved contact path and next steps. | Helps family reconnect safely. |
| familyreunifyops.notification.no_match | no-match update | METHOD | No-match update states search continues and requests additional useful details. | Maintains communication. |
| familyreunifyops.notification.language | language support | METHOD | Notifications use requester language or interpreter when available. | Improves comprehension. |
| familyreunifyops.notification.documented | notification record | RECORD | Record stores who was notified, when, by whom and what was disclosed. | Supports audit. |
| familyreunifyops.escalation.law_enforcement | law enforcement escalation | METHOD | Escalation occurs for missing children, suspected crime, threats or welfare danger. | Uses proper authority. |
| familyreunifyops.escalation.child_welfare | child welfare escalation | SAFETY_RULE | Child protection agency is engaged when custody or abuse concerns appear. | Protects minors. |
| familyreunifyops.escalation.embassy | consular escalation | METHOD | Foreign nationals may need consular or embassy contact under policy. | Supports international families. |
| familyreunifyops.escalation.mass_casualty | mass casualty link | METHOD | Mass casualty incidents coordinate with family assistance center and official lists. | Avoids fragmented notification. |
| familyreunifyops.records.case_file | case file | RECORD | File stores inquiry, checks, sources, match rationale, consent and notifications. | Creates single evidence trail. |
| familyreunifyops.records.retention | retention rule | CONSTRAINT | Records follow emergency, privacy and legal retention schedules. | Controls sensitive data. |
| familyreunifyops.records.access | access control | SAFETY_RULE | Only authorized reunification staff can view sensitive cases. | Protects privacy. |
| familyreunifyops.records.audit_log | audit log | RECORD | Audit log tracks searches, views and disclosures. | Detects misuse. |
| familyreunifyops.communication.public_form | public inquiry form | METHOD | Public form asks for useful details without overcollecting sensitive data. | Improves intake quality. |
| familyreunifyops.communication.hotline_script | hotline script | METHOD | Script explains process, privacy limits and expected update cadence. | Reduces panic and confusion. |
| familyreunifyops.metrics.open_cases | open cases | MEASUREMENT | Open cases track unmatched, pending consent, matched and closed inquiries. | Shows workload. |
| familyreunifyops.metrics.match_time | match time | MEASUREMENT | Match time measures inquiry-to-confirmed outcome. | Indicates system speed. |
| familyreunifyops.qa.match_review | match review | QUALITY_CHECK | Sensitive matches receive second-person review before disclosure. | Reduces harmful errors. |
| familyreunifyops.closeout.closure_reason | closure reason | RECORD | Closure reason records reunited, safe-notified, withdrawn, duplicate, referred or unresolved. | Makes outcome explicit. |
