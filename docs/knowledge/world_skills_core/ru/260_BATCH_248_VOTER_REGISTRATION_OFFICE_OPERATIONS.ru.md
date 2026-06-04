# BATCH_248 — Voter Registration Office Operations Detail
# world_skills_core · source: world_skills_core:batch_248:voter_registration_office_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| voterreg.application.application_intake | Voter registration application intake | invariant | Intake records applicant, address, date, source, signature and form type. | start registration |
| voterreg.application.online_submission | Online voter registration submission | variant | Submission captures portal data, authentication result, timestamp and validation status. | digital intake |
| voterreg.application.paper_form | Paper voter registration form | invariant | Form handling scans, indexes, batches and tracks physical application custody. | process mail/forms |
| voterreg.application.agency_source | Agency voter registration source | variant | Source identifies motor vehicle, public assistance, school, outreach or third-party drive. | source tracking |
| voterreg.application.deadline_stamp | Voter registration deadline stamp | invariant | Stamp records received or postmarked date for election eligibility deadlines. | deadline control |
| voterreg.verification.identity_match | Voter identity match | invariant | Match checks name, birthdate, ID number or other permitted identifiers. | verify applicant |
| voterreg.verification.residence_check | Voter residence check | invariant | Check confirms address falls in jurisdiction, precinct, district and valid residence type. | assign ballot |
| voterreg.verification.duplicate_check | Voter duplicate check | invariant | Check compares existing records for same person, prior address or alternate spelling. | avoid duplicates |
| voterreg.verification.eligibility_flag | Voter eligibility flag | invariant | Flag records citizenship, age, residency, legal status or other jurisdiction-specific requirement. | determine status |
| voterreg.verification.pending_status | Pending voter registration status | variant | Status holds application awaiting missing information, verification, signature or deadline review. | manage incomplete |
| voterreg.update.address_change | Voter address change | invariant | Change updates residence, mailing address, precinct, districts and notice route. | current list |
| voterreg.update.name_change | Voter name change | invariant | Change records legal name update, signature change if needed and notice. | accurate record |
| voterreg.update.party_change | Voter party affiliation change | variant | Change records permitted party update, deadline, ballot impact and confirmation. | primary eligibility |
| voterreg.update.signature_update | Voter signature update | variant | Update stores current signature reference, date and source for verification use. | signature matching |
| voterreg.update.status_reactivation | Voter status reactivation | variant | Reactivation restores inactive voter after confirmation, voting activity or valid update. | preserve access |
| voterreg.list.precinct_assignment | Voter precinct assignment | invariant | Assignment maps residence to precinct, districts, polling place and ballot style. | correct election |
| voterreg.list.district_mapping | Voter district mapping | invariant | Mapping applies legislative, municipal, school, special and referendum districts. | ballot accuracy |
| voterreg.list.inactive_process | Voter inactive process | invariant | Process marks voter inactive after allowed notice, returned mail or inactivity trigger. | list maintenance |
| voterreg.list.cancellation_record | Voter cancellation record | invariant | Record documents death, move, duplicate, request, felony status or legal cancellation basis. | clean list |
| voterreg.list.batch_update | Voter list batch update | variant | Update applies validated changes from agencies, mail, canvass, court or election activity. | efficient maintenance |
| voterreg.notice.acknowledgment_notice | Voter registration acknowledgment notice | invariant | Notice confirms registration, precinct, polling place, status or missing information. | inform voter |
| voterreg.notice.returned_mail | Voter returned mail record | invariant | Record captures undeliverable notice, address issue, status impact and follow-up. | maintain list |
| voterreg.notice.deficiency_notice | Voter registration deficiency notice | invariant | Notice identifies missing signature, ID, address, eligibility or incomplete field. | cure application |
| voterreg.notice.cancellation_notice | Voter cancellation notice | variant | Notice informs voter of cancellation basis, effective date and appeal or correction path. | due process |
| voterreg.deadline.close_of_books | Close of books | variant | Deadline freezes or limits registration updates before an election under local rule. | election readiness |
| voterreg.deadline.same_day | Same-day registration workflow | variant | Workflow processes election-day registration, proof, ballot style and provisional path if needed. | late access |
| voterreg.deadline.cure_period | Voter registration cure period | invariant | Period allows applicant to fix missing information within defined timeline. | preserve eligibility |
| voterreg.audit.audit_trail | Voter registration audit trail | invariant | Trail records creation, update, user, source, timestamp and reason codes. | accountability |
| voterreg.audit.access_control | Voter registration system access control | invariant | Control assigns user roles, permissions, review, deactivation and login monitoring. | protect list |
| voterreg.audit.change_review | Voter record change review | invariant | Review checks high-risk updates, bulk changes, cancellations and unusual patterns. | detect errors |
| voterreg.audit.thirdparty_batch | Third-party registration batch audit | variant | Audit checks batch count, timeliness, completeness, duplicates and source compliance. | oversee drives |
| voterreg.public.lookup_support | Voter lookup support | variant | Support helps voters verify registration, precinct, polling place and status. | voter service |
| voterreg.public.record_request | Voter registration public record request | variant | Request handles lawful access, protected fields, fees, format and delivery. | transparency |
| voterreg.public.privacy_protection | Voter privacy protection | invariant | Protection restricts confidential addresses, protected voters, personal identifiers and signatures. | safety |
| voterreg.public.assistance_log | Voter registration assistance log | variant | Log records nonpartisan help given, language support, accessibility need and unresolved question. | service evidence |
| voterreg.operations.election_roster | Election roster production | invariant | Production creates pollbooks, voter lists, labels or export files for election use. | prepare voting |
| voterreg.operations.pollbook_sync | Electronic pollbook sync | variant | Sync transfers eligible voters, updates, absentee indicators and ballot style data. | current check-in |
| voterreg.operations.absentee_indicator | Absentee ballot indicator | variant | Indicator marks issued, returned, challenged or cancelled absentee status in voter record. | prevent double voting |
| voterreg.quality.data_validation | Voter registration data validation | invariant | Validation checks required fields, address format, district logic and duplicate risk. | improve accuracy |
| voterreg.quality.error_correction | Voter registration error correction | invariant | Correction fixes clerical, mapping, duplicate or source errors with audit reason. | reliable list |
| voterreg.reporting.registration_report | Voter registration report | invariant | Report summarizes active, inactive, new, updated, cancelled and pending records. | office visibility |
| voterreg.reporting.deadline_report | Voter deadline processing report | variant | Report tracks applications near deadline, pending cures, same-day and late submissions. | manage workload |
| voterreg.metrics.voterreg_kpi | Voter registration KPI | variant | KPI tracks processing time, pending rate, returned mail, duplicates, errors and notices. | manage office |
| voterreg.continuity.system_outage | Voter registration system outage | invariant | Outage plan uses paper intake, queue control, communication and later data entry. | preserve operations |
