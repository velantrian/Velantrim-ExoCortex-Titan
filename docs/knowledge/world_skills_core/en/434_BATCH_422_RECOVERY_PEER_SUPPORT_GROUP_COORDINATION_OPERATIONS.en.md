# BATCH 422: Recovery Peer Support Group Coordination Operations

**KnowledgeUnits:** 44  
**Namespace:** `peersupportops.*`  
**Scope:** intake, facilitator scheduling, ground rules, referrals, attendance and outcomes.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| peersupportops.activation.need_signal | need signal | MODEL | Need signal includes displacement stress, grief, isolation, recovery fatigue or repeated outreach requests. | Starts groups. |
| peersupportops.activation.group_model | group model | RECORD | Model distinguishes open group, closed cohort, topic group, family group or virtual group. | Defines format. |
| peersupportops.activation.partner | partner roster | RECORD | Roster lists mental health, community, faith, survivor and recovery organizations. | Builds support network. |
| peersupportops.activation.command_link | command link | RECORD | Coordination links behavioral health, case management, public information and referral partners. | Maintains oversight. |
| peersupportops.intake.participant | participant intake | RECORD | Intake captures contact, language, access needs, topic interest and safety concerns. | Supports placement. |
| peersupportops.intake.consent | consent record | RECORD | Consent explains peer nature, privacy limits, data use and referral boundaries. | Sets expectation. |
| peersupportops.intake.group_fit | group fit | MODEL | Fit considers topic, age, culture, loss type, language, schedule and support needs. | Improves match. |
| peersupportops.intake.crisis_screen | crisis screen | SAFETY_RULE | Acute risk routes to crisis or clinical service rather than peer group alone. | Protects participant. |
| peersupportops.facilitator.roster | facilitator roster | RECORD | Roster lists trained facilitators, languages, availability, lived experience and boundaries. | Schedules leaders. |
| peersupportops.facilitator.training | facilitator training | QUALITY_CHECK | Training covers trauma-informed practice, boundaries, referrals, confidentiality and de-escalation. | Supports quality. |
| peersupportops.facilitator.assignment | facilitator assignment | RECORD | Assignment links facilitator, group, date, topic, location and backup. | Creates schedule. |
| peersupportops.facilitator.backup | backup facilitator | METHOD | Backup handles illness, no-show, overload or crisis escalation. | Adds resilience. |
| peersupportops.schedule.session_calendar | session calendar | RECORD | Calendar records dates, frequency, location, virtual link and capacity. | Coordinates attendance. |
| peersupportops.schedule.reminder | reminder process | METHOD | Reminders use preferred contact, safe language and opt-out option. | Reduces no-shows. |
| peersupportops.schedule.accessibility | accessibility planning | METHOD | Planning covers transport, childcare, interpreters, wheelchair access and quiet space. | Improves inclusion. |
| peersupportops.schedule.cancellation | cancellation process | METHOD | Cancellation records reason, notice, reschedule and participant update. | Reduces confusion. |
| peersupportops.groundrules.confidentiality | confidentiality rule | SAFETY_RULE | Group rule explains privacy expectations and legal/safety limits. | Builds trust. |
| peersupportops.groundrules.respect | respect rule | METHOD | Rules support turn-taking, nonjudgment, no coercion and cultural respect. | Keeps group safe. |
| peersupportops.groundrules.no_advice_pressure | advice boundary | METHOD | Participants share experience without pressuring others into decisions. | Prevents harm. |
| peersupportops.groundrules.crisis_boundary | crisis boundary | SAFETY_RULE | Group is not emergency care; crisis concerns escalate immediately. | Clarifies limits. |
| peersupportops.referrals.resource_list | resource list | RECORD | List includes crisis lines, counseling, casework, legal aid, housing and benefits. | Enables handoff. |
| peersupportops.referrals.warm_handoff | warm handoff | METHOD | Facilitator connects participant to service with consent when urgent or complex. | Reduces drop-off. |
| peersupportops.referrals.followup | referral follow-up | METHOD | Follow-up checks whether participant reached referred service where appropriate. | Closes loop. |
| peersupportops.referrals.unmet_need | unmet need record | RECORD | Record captures service gaps, waitlists, transport or language barriers. | Informs planning. |
| peersupportops.attendance.signin | attendance sign-in | RECORD | Sign-in tracks attendance using privacy-protective identifiers where possible. | Shows participation. |
| peersupportops.attendance.no_show | no-show process | METHOD | No-show follow-up respects consent and safe contact preferences. | Maintains connection. |
| peersupportops.attendance.capacity | capacity limit | CONSTRAINT | Capacity defines safe group size, waitlist and alternate session pathway. | Protects quality. |
| peersupportops.attendance.repeat_pattern | repeat pattern | MEASUREMENT | Pattern tracks repeat attendance and drop-off without excessive personal detail. | Measures engagement. |
| peersupportops.safety.distress_signal | distress signal | SAFETY_RULE | Facilitator watches for dissociation, panic, anger, hopelessness or withdrawal. | Enables support. |
| peersupportops.safety.deescalation | de-escalation | METHOD | De-escalation uses calm break, co-facilitator, private check and referral route. | Maintains safety. |
| peersupportops.safety.incident_report | incident report | RECORD | Incident records crisis, threat, injury, confidentiality breach or mandated escalation. | Supports review. |
| peersupportops.safety.facilitator_support | facilitator support | METHOD | Facilitators receive debrief, supervision or rotation after difficult sessions. | Prevents burnout. |
| peersupportops.communication.public_notice | public notice | METHOD | Notice states group purpose, schedule, eligibility, peer nature and how to join. | Guides residents. |
| peersupportops.communication.partner_update | partner update | METHOD | Partners receive aggregate attendance, referral gaps and schedule changes. | Coordinates services. |
| peersupportops.communication.language | language access | METHOD | Groups use interpreter, bilingual facilitator or separate language-specific session. | Improves access. |
| peersupportops.communication.feedback | feedback process | METHOD | Participants can provide anonymous feedback on usefulness, safety and barriers. | Improves group. |
| peersupportops.records.case_minimum | minimum record | SAFETY_RULE | Records avoid detailed personal stories and store only coordination data. | Protects privacy. |
| peersupportops.records.session_note | session note | RECORD | Note records topic, attendance count, referrals, incidents and logistics issues. | Creates continuity. |
| peersupportops.records.retention | retention rule | CONSTRAINT | Records follow behavioral health, volunteer, privacy and grant schedules. | Controls lifecycle. |
| peersupportops.metrics.sessions_held | sessions held | MEASUREMENT | Count tracks sessions held, canceled, virtual and in-person. | Shows activity. |
| peersupportops.metrics.attendance | attendance metric | MEASUREMENT | Metric tracks participants by session, topic and language without exposing identity. | Shows reach. |
| peersupportops.metrics.referral_count | referral count | MEASUREMENT | Count tracks referrals from group to clinical, casework or social services. | Shows linkage. |
| peersupportops.qa.facilitator_review | facilitator review | QUALITY_CHECK | Review checks ground rules, boundaries, referrals, incidents and feedback. | Improves quality. |
| peersupportops.review.after_action | after-action review | METHOD | Review captures group fit, facilitator capacity, safety, referrals and participant feedback. | Improves future coordination. |
