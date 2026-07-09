# BATCH 395: Emergency Shelter Registration Data Quality Operations

**KnowledgeUnits:** 44  
**Namespace:** `shelterregdqops.*`  
**Scope:** duplicate household records, missing fields, privacy, dashboards and audits.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| shelterregdqops.intake.required_fields | required fields | RECORD | Required fields define minimum household, contact, accessibility, language and consent data. | Standardizes registration. |
| shelterregdqops.intake.optional_fields | optional fields | CONSTRAINT | Optional fields are separated from eligibility-critical data. | Reduces intake burden. |
| shelterregdqops.intake.field_help | field help text | METHOD | Field guidance explains how staff should enter names, dates, addresses and special needs. | Reduces inconsistent data. |
| shelterregdqops.intake.paper_form | paper fallback form | RECORD | Paper form mirrors digital fields and captures time, staff and shelter site. | Supports outages. |
| shelterregdqops.identity.name_standard | name standard | METHOD | Name entry standard handles nicknames, suffixes, hyphens and transliteration. | Improves matching. |
| shelterregdqops.identity.birthdate | birthdate quality | QUALITY_CHECK | Birthdate entries check impossible dates, missing year and inconsistent format. | Catches errors early. |
| shelterregdqops.identity.household_link | household link | RECORD | Household link connects members, head/contact person and shared service needs. | Prevents fragmented cases. |
| shelterregdqops.identity.anonymous_entry | anonymous entry | CONSTRAINT | Anonymous or privacy-protected entry follows policy when identity cannot be collected. | Maintains access. |
| shelterregdqops.duplicate.match_rule | duplicate match rule | MODEL | Duplicate rule compares name, birthdate, phone, prior address, household and shelter history. | Finds repeated records. |
| shelterregdqops.duplicate.probable_match | probable match queue | RECORD | Probable matches are queued for human review before merging. | Avoids wrong merges. |
| shelterregdqops.duplicate.confirm_merge | confirmed merge | METHOD | Merge keeps source IDs, audit note, reviewer and reason. | Preserves traceability. |
| shelterregdqops.duplicate.false_match | false match flag | RECORD | False match flag prevents repeatedly proposing the same nonduplicate pair. | Saves reviewer time. |
| shelterregdqops.missing.missing_report | missing field report | MEASUREMENT | Report counts missing required and high-value fields by site, shift and form source. | Targets cleanup. |
| shelterregdqops.missing.followup_queue | follow-up queue | RECORD | Queue lists records needing contact, staff correction or supervisor review. | Organizes remediation. |
| shelterregdqops.missing.bulk_cleanup | bulk cleanup | METHOD | Bulk cleanup corrects safe format errors without changing substantive household facts. | Improves quality. |
| shelterregdqops.missing.unreachable | unreachable record | RECORD | Unreachable records document contact attempts and unresolved missing information. | Keeps uncertainty visible. |
| shelterregdqops.privacy.minimum | data minimization | SAFETY_RULE | Registration collects only operationally justified data for shelter and assistance functions. | Reduces privacy risk. |
| shelterregdqops.privacy.consent | consent record | RECORD | Consent records data sharing choices, explanation, date and staff member. | Supports lawful sharing. |
| shelterregdqops.privacy.role_access | role-based access | SAFETY_RULE | Access differs for intake, medical desk, logistics, casework, security and reporting roles. | Limits exposure. |
| shelterregdqops.privacy.sensitive_flags | sensitive flag control | SAFETY_RULE | Domestic violence, medical and minor-related flags are visible only to authorized roles. | Protects residents. |
| shelterregdqops.dashboard.occupancy | occupancy dashboard | MEASUREMENT | Dashboard shows registered residents, households, beds used and special accommodation needs. | Guides shelter operations. |
| shelterregdqops.dashboard.data_quality | data quality dashboard | MEASUREMENT | Dashboard tracks duplicates, missing fields, stale records and unresolved corrections. | Shows cleanup progress. |
| shelterregdqops.dashboard.site_compare | site comparison | MEASUREMENT | Site comparison highlights intake error rates across shelters and shifts. | Directs training. |
| shelterregdqops.dashboard.refresh_time | refresh timestamp | RECORD | Refresh timestamp shows when the dashboard last loaded validated data. | Prevents stale decisions. |
| shelterregdqops.audit.audit_log | audit log | RECORD | Audit log records create, view, edit, merge, export and delete events. | Enables accountability. |
| shelterregdqops.audit.export_review | export review | QUALITY_CHECK | Exports are checked for purpose, fields, recipients, approvals and secure transfer. | Controls data leakage. |
| shelterregdqops.audit.sample_check | sample check | QUALITY_CHECK | Sample audit compares source forms, digital records and correction notes. | Tests reliability. |
| shelterregdqops.audit.issue_register | issue register | RECORD | Register tracks data quality findings, owner, deadline, fix and verification. | Manages remediation. |
| shelterregdqops.reporting.daily_count | daily count report | MEASUREMENT | Daily count reconciles registrations, check-ins, departures and overnight census. | Supports command updates. |
| shelterregdqops.reporting.demographics | demographics report | MEASUREMENT | Demographic reporting aggregates age bands, language and accessibility without exposing individuals. | Supports planning. |
| shelterregdqops.reporting.partner_share | partner sharing file | RECORD | Partner file includes only agreed fields and documented sharing basis. | Coordinates services safely. |
| shelterregdqops.reporting.discrepancy | discrepancy note | RECORD | Discrepancy notes explain differences between shelter counts, meal counts and registrations. | Prevents false precision. |
| shelterregdqops.workflow.shift_handoff | shift handoff | METHOD | Handoff lists unresolved merges, missing-field queues, system issues and privacy concerns. | Maintains continuity. |
| shelterregdqops.workflow.training_tip | training tip | METHOD | Training tips address common intake mistakes found in quality review. | Improves next shift. |
| shelterregdqops.workflow.supervisor_review | supervisor review | QUALITY_CHECK | Supervisor reviews high-risk edits, merge disputes and sensitive access concerns. | Adds control. |
| shelterregdqops.workflow.closeout | record closeout | METHOD | Closeout marks departure, destination category, referrals and unresolved data issues. | Completes record lifecycle. |
| shelterregdqops.system.offline_sync | offline sync | METHOD | Offline sync reconciles paper, spreadsheet or mobile records after connectivity returns. | Prevents lost intakes. |
| shelterregdqops.system.validation_rule | validation rule | QUALITY_CHECK | Validation rules flag impossible values, blank required fields and invalid codes. | Improves entry quality. |
| shelterregdqops.system.code_set | code set | RECORD | Code sets standardize shelter sites, services, languages, accommodations and referral outcomes. | Enables clean reporting. |
| shelterregdqops.system.backup | backup procedure | SAFETY_RULE | Backups protect registration data from loss while following access and retention rules. | Preserves continuity. |
| shelterregdqops.metrics.duplicate_rate | duplicate rate | MEASUREMENT | Duplicate rate tracks duplicate records per registrations by site and period. | Measures cleanup burden. |
| shelterregdqops.metrics.completeness | completeness rate | MEASUREMENT | Completeness rate measures required fields present and verified. | Shows readiness. |
| shelterregdqops.metrics.correction_age | correction age | MEASUREMENT | Correction age measures time from data issue creation to closure. | Reveals backlog. |
| shelterregdqops.review.after_action | after-action review | METHOD | Review captures intake design, privacy issues, dashboard use and audit lessons. | Improves future shelters. |
