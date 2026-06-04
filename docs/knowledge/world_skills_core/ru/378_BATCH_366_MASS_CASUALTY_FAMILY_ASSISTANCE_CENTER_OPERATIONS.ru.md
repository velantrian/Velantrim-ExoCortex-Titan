# BATCH 366: Mass Casualty Family Assistance Center Operations

**KnowledgeUnits:** 44  
**Namespace:** `faccenterops.*`  
**Scope:** registration, victim accounting, behavioral support, briefings, privacy and demobilization.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| faccenterops.activation.trigger | activation trigger | MODEL | Center activates after mass casualty, missing persons surge or major family information need. | Creates organized family support. |
| faccenterops.activation.authority | activation authority | RECORD | Authority records lead agency, incident command, site and operational period. | Clarifies governance. |
| faccenterops.activation.site | site selection | METHOD | Site selection considers privacy, security, accessibility, media separation and transport. | Protects families. |
| faccenterops.activation.layout | layout plan | METHOD | Layout separates registration, waiting, briefing, counseling, interviews and private rooms. | Reduces chaos. |
| faccenterops.registration.family_id | family record ID | RECORD | Family ID links inquirer, victim/missing person, relationship, contacts and language. | Creates traceable support case. |
| faccenterops.registration.relationship | relationship verification | METHOD | Relationship is checked before sensitive victim information is shared. | Protects privacy. |
| faccenterops.registration.group_link | family group link | RECORD | Related family members are linked to avoid duplicate interviews and inconsistent updates. | Keeps communication coherent. |
| faccenterops.registration.access_badge | access badge | METHOD | Badge or wristband controls entry and family-only areas. | Maintains secure environment. |
| faccenterops.victim.accounting | victim accounting | RECORD | Accounting links missing, injured, deceased, unidentified and located persons. | Supports accurate updates. |
| faccenterops.victim.reconciliation | reconciliation process | QUALITY_CHECK | Reconciliation compares hospitals, morgue, shelters, law enforcement and witness lists. | Reduces conflicting information. |
| faccenterops.victim.unidentified | unidentified person process | SAFETY_RULE | Unidentified persons are handled by medical examiner or authorized officials. | Prevents improper identification. |
| faccenterops.victim.status_confidence | status confidence | MODEL | Status confidence ranks confirmed, probable, unconfirmed or incorrect information. | Prevents rumor release. |
| faccenterops.interview.ante_mortem | ante-mortem interview | METHOD | Authorized staff collect identifying details for missing/deceased identification. | Supports victim identification. |
| faccenterops.interview.evidence_handling | evidence handling | SAFETY_RULE | Photos, dental, DNA or property details follow chain and consent rules. | Protects sensitive evidence. |
| faccenterops.interview.retrauma | retrauma control | METHOD | Interviews minimize repeated questioning and use trauma-informed practice. | Protects families. |
| faccenterops.interview.interpreter | interpreter support | METHOD | Interpreters support interviews and briefings without becoming evidence handlers. | Improves accuracy. |
| faccenterops.briefing.schedule | briefing schedule | RECORD | Briefings occur at predictable times even when updates are limited. | Reduces uncertainty. |
| faccenterops.briefing.approved_info | approved information | CONSTRAINT | Briefings use only cleared information from incident command and victim accounting. | Avoids false statements. |
| faccenterops.briefing.private_notice | private notification | SAFETY_RULE | Death or sensitive status is communicated privately by authorized personnel. | Preserves dignity. |
| faccenterops.briefing.question_log | question log | RECORD | Family questions are logged, assigned and answered when verified. | Keeps concerns visible. |
| faccenterops.behavioral.support_station | support station | METHOD | Behavioral support offers crisis counseling, spiritual care and quiet spaces. | Supports distressed families. |
| faccenterops.behavioral.acute_distress | acute distress response | SAFETY_RULE | Severe distress, self-harm risk or medical crisis triggers clinical/emergency help. | Protects safety. |
| faccenterops.behavioral.staff_support | staff support | METHOD | Staff and volunteers receive breaks, defusing and supervision. | Reduces secondary trauma. |
| faccenterops.behavioral.children | child support | METHOD | Child-friendly space and safeguarding rules support minors at the center. | Protects children. |
| faccenterops.privacy.media_boundary | media boundary | SAFETY_RULE | Media are physically and procedurally separated from families. | Prevents exploitation. |
| faccenterops.privacy.data_minimum | minimum data | CONSTRAINT | Center collects only data needed for identification, notification and support. | Reduces privacy risk. |
| faccenterops.privacy.confidential_room | confidential room | METHOD | Sensitive conversations occur in private rooms. | Preserves dignity. |
| faccenterops.privacy.access_log | access log | RECORD | Access to family/victim data is logged. | Detects misuse. |
| faccenterops.services.food_water | basic services | METHOD | Families receive water, food, restrooms, charging and seating. | Supports long waits. |
| faccenterops.services.transport | transport support | METHOD | Transport may connect families to hospitals, lodging, reunification or home. | Reduces practical barriers. |
| faccenterops.services.lodging | lodging support | METHOD | Lodging support coordinates hotels, vouchers or partner shelters. | Helps out-of-area families. |
| faccenterops.services.documents | document support | METHOD | Families may need letters, death-related instructions or service referrals. | Helps next steps. |
| faccenterops.security.entry | entry control | METHOD | Entry control screens credentials, threats and unauthorized persons. | Keeps center safe. |
| faccenterops.security.threat | threat assessment | SAFETY_RULE | Threats, stalking, custody disputes or offender presence trigger security escalation. | Protects vulnerable families. |
| faccenterops.security.incident | incident report | RECORD | Incidents record facts, response, escalation and follow-up. | Supports safety review. |
| faccenterops.partners.liaison | partner liaison | METHOD | Liaisons coordinate hospitals, law enforcement, coroner, Red Cross, faith groups and interpreters. | Aligns support network. |
| faccenterops.partners.role_card | role card | RECORD | Role cards define what each agency can and cannot tell families. | Prevents mixed messages. |
| faccenterops.records.case_file | case file | RECORD | Case file stores registration, inquiries, updates, services and notifications. | Creates audit trail. |
| faccenterops.records.retention | retention rule | CONSTRAINT | Records follow incident, privacy, legal and victim services retention rules. | Controls lifecycle. |
| faccenterops.metrics.family_count | family count | MEASUREMENT | Count tracks families served, active cases, briefings and service needs. | Shows workload. |
| faccenterops.metrics.information_lag | information lag | MEASUREMENT | Lag measures time from confirmed status to family notification. | Highlights delays. |
| faccenterops.qa.info_audit | information audit | QUALITY_CHECK | Audit checks whether disclosed information was approved and documented. | Reduces harm. |
| faccenterops.demobilization.transition | transition plan | METHOD | Transition moves open cases to victim services, medical examiner or case managers. | Prevents abandonment. |
| faccenterops.demobilization.site_close | site closeout | METHOD | Closeout secures records, returns site, debriefs staff and updates families. | Ends operation responsibly. |
