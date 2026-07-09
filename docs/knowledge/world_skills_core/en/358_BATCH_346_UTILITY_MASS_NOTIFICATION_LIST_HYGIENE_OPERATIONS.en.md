# BATCH 346: Utility Mass Notification List Hygiene Operations

**KnowledgeUnits:** 44  
**Namespace:** `notifyhygieneops.*`  
**Scope:** opt-ins, bad contacts, duplicates, language preferences, consent, suppression and audits.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| notifyhygieneops.source.contact_master | contact master | RECORD | Contact master stores account, person, channel, address, consent and status. | Creates a controlled notification base. |
| notifyhygieneops.source.cis_sync | CIS sync | METHOD | Customer information system sync updates account status, service address and contacts. | Keeps lists aligned with billing records. |
| notifyhygieneops.source.portal_sync | portal preference sync | METHOD | Portal preferences update channels, language and opt-in choices. | Respects customer self-service choices. |
| notifyhygieneops.source.callcenter_update | call center update | METHOD | Agents can update verified contact details with audit trail. | Improves data during live interactions. |
| notifyhygieneops.optin.channel_optin | channel opt-in | RECORD | Opt-in records channel, purpose, date, source and proof. | Supports consent compliance. |
| notifyhygieneops.optin.purpose_scope | purpose scope | CONSTRAINT | Consent scope distinguishes outage, billing, marketing, emergency and service notices. | Prevents overuse of consent. |
| notifyhygieneops.optin.double_confirm | double confirmation | METHOD | High-risk channels may use confirmation code or double opt-in. | Reduces wrong-number notifications. |
| notifyhygieneops.optin.minor_guard | minor guard | SAFETY_RULE | Contact preferences avoid collecting or using minor data outside policy. | Protects vulnerable users. |
| notifyhygieneops.optout.unsubscribe | unsubscribe | METHOD | Opt-out path is available by channel and recorded quickly. | Respects customer choice. |
| notifyhygieneops.optout.global_suppression | global suppression | CONSTRAINT | Global suppression blocks nonmandatory communications. | Prevents repeated unwanted contact. |
| notifyhygieneops.optout.mandatory_exception | mandatory exception | CONSTRAINT | Emergency or legally required notices may override some preferences under policy. | Maintains public safety communication. |
| notifyhygieneops.optout.confirmation | opt-out confirmation | RECORD | Opt-out confirmation records channel, time and remaining mandatory categories. | Reduces confusion. |
| notifyhygieneops.quality.bad_email | bad email | FAILURE_MODE | Bad email is detected by bounce, typo pattern, domain error or repeated failure. | Improves deliverability. |
| notifyhygieneops.quality.bad_phone | bad phone | FAILURE_MODE | Bad phone is detected by disconnected number, carrier error or customer correction. | Prevents wasted SMS/calls. |
| notifyhygieneops.quality.bad_address | bad address | FAILURE_MODE | Bad address is detected by returned mail, invalid service match or geocode failure. | Improves postal and geographic targeting. |
| notifyhygieneops.quality.stale_contact | stale contact | MODEL | Contact is stale when unused, unconfirmed or tied to inactive account beyond policy window. | Prioritizes cleanup. |
| notifyhygieneops.dedupe.identity_key | identity key | MODEL | Identity key combines account, person, channel and normalized contact value. | Finds duplicate contacts. |
| notifyhygieneops.dedupe.household_merge | household merge | METHOD | Household merge prevents repeated notices while preserving individual consent. | Reduces notification fatigue. |
| notifyhygieneops.dedupe.business_site | business site contacts | METHOD | Business accounts may keep multiple role-based contacts for safety and operations. | Avoids over-merge errors. |
| notifyhygieneops.dedupe.conflict_resolution | conflict resolution | METHOD | Conflicting preferences are resolved by latest proof, stronger consent or manual review. | Keeps records defensible. |
| notifyhygieneops.language.preference | language preference | RECORD | Language preference is stored per account/person/channel where available. | Sends understandable notices. |
| notifyhygieneops.language.fallback | language fallback | METHOD | Fallback language is chosen when preference is missing or translation unavailable. | Keeps urgent notices flowing. |
| notifyhygieneops.language.translation_tag | translation tag | RECORD | Notification template records language version and approval status. | Prevents sending unapproved translations. |
| notifyhygieneops.language.accessibility | accessibility preference | RECORD | Accessibility preference may include TTY, large print, voice call or email format. | Supports inclusive communication. |
| notifyhygieneops.segmentation.geo_target | geographic targeting | METHOD | Service address, feeder, pressure zone, route or map polygon targets affected customers. | Limits alerts to impacted users. |
| notifyhygieneops.segmentation.customer_class | customer class | METHOD | Customer class segments residential, business, critical, landlord or assistance customers. | Tailors message relevance. |
| notifyhygieneops.segmentation.sensitive_customer | sensitive customer flag | SAFETY_RULE | Sensitive customer flags are protected and used only for approved service purposes. | Balances care and privacy. |
| notifyhygieneops.segmentation.exclusion | exclusion list | CONSTRAINT | Exclusion list removes employees, test accounts, inactive accounts or legal holds as needed. | Prevents improper sends. |
| notifyhygieneops.suppression.quiet_hours | quiet hours | CONSTRAINT | Quiet hours suppress nonurgent messages by channel and jurisdiction. | Reduces nuisance and legal risk. |
| notifyhygieneops.suppression.frequency_cap | frequency cap | CONSTRAINT | Frequency cap limits repeated messages within a time window. | Prevents customer fatigue. |
| notifyhygieneops.suppression.duplicate_send | duplicate send prevention | QUALITY_CHECK | Duplicate send prevention checks campaign, contact, account and event ID. | Avoids repeated alerts. |
| notifyhygieneops.suppression.test_accounts | test account suppression | QUALITY_CHECK | Test accounts are separated from production send lists. | Prevents accidental public campaigns. |
| notifyhygieneops.delivery.bounce_process | bounce process | METHOD | Bounce process classifies hard bounce, soft bounce and temporary provider errors. | Guides cleanup and retries. |
| notifyhygieneops.delivery.sms_carrier | SMS carrier result | RECORD | SMS result stores delivered, failed, filtered, opted out or carrier unknown. | Measures mobile channel health. |
| notifyhygieneops.delivery.voice_result | voice result | RECORD | Voice call result stores answered, voicemail, busy, failed or disconnected. | Supports reachability analysis. |
| notifyhygieneops.delivery.postal_return | postal return | METHOD | Returned mail updates address quality and may trigger verification. | Improves physical notices. |
| notifyhygieneops.audit.consent_proof | consent proof audit | QUALITY_CHECK | Audit samples contacts to verify consent proof and purpose match. | Detects compliance gaps. |
| notifyhygieneops.audit.send_log | send log audit | QUALITY_CHECK | Send logs are reconciled against campaign approvals and target rules. | Shows messages went to intended lists. |
| notifyhygieneops.audit.admin_access | admin access audit | QUALITY_CHECK | List export and admin access are reviewed for need and misuse. | Protects customer data. |
| notifyhygieneops.audit.vendor_controls | vendor controls | CONSTRAINT | Notification vendors must meet privacy, security, retention and incident obligations. | Controls outsourced risk. |
| notifyhygieneops.metrics.deliverability | deliverability rate | MEASUREMENT | Deliverability rate tracks successful sends by channel and list segment. | Shows list health. |
| notifyhygieneops.metrics.optout_rate | opt-out rate | MEASUREMENT | Opt-out rate by campaign reveals fatigue, bad targeting or wording issues. | Improves communication strategy. |
| notifyhygieneops.metrics.coverage_gap | coverage gap | MEASUREMENT | Coverage gap identifies accounts lacking valid reachable contacts. | Prioritizes collection efforts. |
| notifyhygieneops.closeout.hygiene_backlog | hygiene backlog | RECORD | Backlog tracks bad contacts, duplicates, stale records and unresolved conflicts. | Turns data quality into managed work. |
