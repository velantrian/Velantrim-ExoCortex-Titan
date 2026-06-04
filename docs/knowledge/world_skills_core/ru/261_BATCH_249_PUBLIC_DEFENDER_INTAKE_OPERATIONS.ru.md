# BATCH_249 — Public Defender Intake Operations Detail
# world_skills_core · source: world_skills_core:batch_249:public_defender_intake_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| pdintake.eligibility.application_intake | Public defender application intake | invariant | Intake records applicant, case, charges, court, custody status and contact. | start representation review |
| pdintake.eligibility.financial_screen | Public defender financial screen | invariant | Screen captures income, assets, household, obligations and allowed eligibility factors. | determine qualification |
| pdintake.eligibility.custody_priority | Public defender custody priority | variant | Priority flags detained clients, imminent hearings, juveniles or urgent deadlines. | triage quickly |
| pdintake.eligibility.incomplete_application | Incomplete defender application | invariant | Record tracks missing financial, identity, case or signature information and deadline. | complete file |
| pdintake.eligibility.fee_order | Public defender fee order | variant | Order records court fee, contribution, waiver or reimbursement requirement. | financial compliance |
| pdintake.conflict.conflict_check | Public defender conflict check | invariant | Check searches clients, witnesses, victims, codefendants, prior cases and staff conflicts. | avoid conflict |
| pdintake.conflict.codefendant_flag | Codefendant conflict flag | invariant | Flag identifies multiple defendants needing separate counsel or conflict review. | protect loyalty |
| pdintake.conflict.witness_match | Witness conflict match | variant | Match compares witnesses, victims or informants against current and former client lists. | ethical review |
| pdintake.conflict.conflict_waiver | Conflict waiver record | variant | Record captures approved waiver process when permitted by law and ethics. | document exception |
| pdintake.conflict.outside_panel | Outside counsel panel referral | variant | Referral sends conflict case to assigned outside counsel with case packet. | maintain representation |
| pdintake.case.case_open | Public defender case open | invariant | Case open creates matter, client, charges, court dates, assigned unit and deadlines. | start file |
| pdintake.case.charge_record | Defender charge record | invariant | Record captures statute, count, severity, arrest date, docket and charging document. | know case |
| pdintake.case.court_date | Public defender court date | invariant | Date records hearing type, court, judge, time, transport and notice status. | avoid missed hearings |
| pdintake.case.deadline_tickler | Defender deadline tickler | invariant | Tickler tracks discovery, motions, bail, plea, trial, appeal or filing deadlines. | protect rights |
| pdintake.case.detainer_flag | Client detainer flag | variant | Flag records warrants, holds, immigration, probation or other custody constraints. | plan defense |
| pdintake.assignment.assignment_rule | Public defender assignment rule | invariant | Rule routes case by court, charge type, unit, workload, language and conflicts. | fair assignment |
| pdintake.assignment.attorney_assignment | Public defender attorney assignment | invariant | Assignment links attorney, investigator, social worker, supervisor and support staff. | representation team |
| pdintake.assignment.workload_check | Public defender workload check | invariant | Check compares caseload, complexity, custody, deadlines and attorney availability. | avoid overload |
| pdintake.assignment.reassignment | Public defender reassignment | variant | Reassignment records conflict, workload, specialty, leave, client issue or court change. | continuity |
| pdintake.client.initial_contact | Public defender initial client contact | invariant | Contact explains representation status, confidentiality, next court date and urgent facts. | build connection |
| pdintake.client.jail_contact | Public defender jail contact | variant | Contact schedules visit, phone, video or message through facility rules. | reach detained client |
| pdintake.client.language_need | Public defender language need | invariant | Need records interpreter, translated documents, preferred language and communication accommodations. | effective communication |
| pdintake.client.contact_update | Client contact update | invariant | Update records phone, address, email, alternate contact and custody transfer. | maintain reach |
| pdintake.client.safety_concern | Defender client safety concern | variant | Concern notes mental health crisis, threats, medical need or urgent social service referral. | protect client |
| pdintake.documents.charging_document | Charging document intake | invariant | Intake stores complaint, indictment, information, citation or petition in case file. | know allegations |
| pdintake.documents.discovery_request | Public defender discovery request | invariant | Request asks prosecution or agency for reports, media, lab, witness and evidence materials. | prepare defense |
| pdintake.documents.release_form | Client release form | variant | Form authorizes records, medical, school, employment or service information where appropriate. | gather mitigation |
| pdintake.documents.document_scan | Defender document scan | invariant | Scan indexes court notices, orders, applications, correspondence and discovery by case. | retrievable file |
| pdintake.court.court_notification | Public defender court notification | invariant | Notification sends assignment, appearance, eligibility or conflict information to court. | coordinate docket |
| pdintake.court.calendar_sync | Defender calendar sync | variant | Sync updates hearings, deadlines, attorney availability and reminders. | avoid conflicts |
| pdintake.court.bail_review_flag | Bail review flag | variant | Flag identifies custody, bail amount, risk, conditions and hearing need. | early advocacy |
| pdintake.court.appearance_record | Public defender appearance record | invariant | Record tracks attorney appearance, waiver, substitution or withdrawal. | official representation |
| pdintake.services.investigator_request | Defender investigator request | variant | Request records facts to investigate, witnesses, locations, deadlines and priority. | support defense |
| pdintake.services.social_work_referral | Defender social work referral | variant | Referral captures housing, treatment, benefits, family, mitigation or reentry need. | holistic defense |
| pdintake.services.expert_request | Defender expert request | variant | Request records forensic, mental health, language, technical or mitigation expertise need. | specialized support |
| pdintake.quality.intake_review | Public defender intake review | invariant | Review checks eligibility, conflicts, assignment, documents, contact and deadlines. | prevent errors |
| pdintake.quality.confidentiality_check | Defender confidentiality check | invariant | Check limits access, conversations, files and communications to authorized staff. | protect privilege |
| pdintake.reporting.intake_backlog | Defender intake backlog report | invariant | Report shows pending applications, conflict checks, assignments, contacts and deadlines. | manage office |
| pdintake.reporting.court_coverage | Public defender court coverage report | variant | Report tracks calendars, assigned attorneys, unrepresented cases and coverage gaps. | staff courts |
| pdintake.metrics.pd_intake_kpi | Public defender intake KPI | variant | KPI tracks time to assignment, conflict rate, detained contacts, workload and missed deadlines. | manage intake |
| pdintake.continuity.mass_arrest | Public defender mass arrest response | variant | Response triages custody, eligibility, conflicts, court coverage, client contact and records. | surge capacity |
| pdintake.continuity.system_outage | Defender intake system outage | invariant | Outage plan uses paper forms, conflict fallback, assignment log and later entry. | continue service |
| pdintake.ethics.withdrawal_route | Defender withdrawal route | invariant | Route documents conflict, eligibility, client request or court-approved withdrawal steps. | ethical exit |
| pdintake.communication.family_inquiry | Public defender family inquiry | variant | Inquiry response respects confidentiality while giving general court or contact guidance. | handle calls |
