# BATCH 351: Public Benefits Call Center Operations

**KnowledgeUnits:** 44  
**Namespace:** `benefitcallops.*`  
**Scope:** eligibility questions, document status, language support, escalations, scripts, privacy and QA.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| benefitcallops.intake.call_id | call ID | RECORD | Call ID links caller, time, program, queue, agent and outcome. | Creates traceable service contact. |
| benefitcallops.intake.reason_code | reason code | RECORD | Reason code classifies eligibility, documents, notices, payments, appeals or technical help. | Shows demand drivers. |
| benefitcallops.intake.account_match | account match | METHOD | Caller is matched to case or application through approved identifiers. | Speeds assistance without guessing. |
| benefitcallops.intake.vulnerability_flag | vulnerability flag | MODEL | Flag notes urgent housing, food, utility, disability or safety risk. | Helps prioritize response. |
| benefitcallops.privacy.identity_verify | identity verification | SAFETY_RULE | Identity is verified before discussing private benefit data. | Protects applicant information. |
| benefitcallops.privacy.minimum_needed | minimum necessary | CONSTRAINT | Agents disclose only information needed for the call purpose. | Limits privacy exposure. |
| benefitcallops.privacy.third_party | third-party caller | CONSTRAINT | Representatives need documented authority before receiving case details. | Prevents unauthorized disclosure. |
| benefitcallops.privacy.recording_notice | recording notice | METHOD | Recording notice or consent plays where required. | Meets call compliance rules. |
| benefitcallops.eligibility.general_info | general eligibility info | METHOD | Agents can explain general rules without making unsupported determinations. | Avoids misleading approvals. |
| benefitcallops.eligibility.rule_boundary | rule boundary | CONSTRAINT | Complex eligibility decisions route to caseworker or specialist. | Keeps call center within authority. |
| benefitcallops.eligibility.pre_screen | pre-screen | METHOD | Pre-screen identifies likely programs, missing facts and next application step. | Helps callers act. |
| benefitcallops.eligibility.change_report | change report guidance | METHOD | Agents explain which household, income or address changes must be reported. | Supports accurate benefits. |
| benefitcallops.documents.status_lookup | document status lookup | METHOD | Agent checks whether submitted documents were received, indexed and reviewed. | Reduces repeat submissions. |
| benefitcallops.documents.missing_list | missing document list | RECORD | Missing list names specific item, due date and accepted submission routes. | Makes next action clear. |
| benefitcallops.documents.upload_help | upload help | METHOD | Agents guide portal, mail, fax or drop-off steps without handling secrets improperly. | Reduces access barriers. |
| benefitcallops.documents.misindexed | misindexed document | FAILURE_MODE | Misindexed documents appear missing because case, person or program link is wrong. | Prevents wrongful delays. |
| benefitcallops.notices.notice_explain | notice explanation | METHOD | Agents translate notice language into plain meaning and deadlines. | Helps callers understand decisions. |
| benefitcallops.notices.deadline_warning | deadline warning | SAFETY_RULE | Agents warn about appeal, renewal and document deadlines when visible. | Protects due process. |
| benefitcallops.notices.reissue | notice reissue | METHOD | Missing or inaccessible notices can be reissued through approved channel. | Restores communication. |
| benefitcallops.payments.payment_status | payment status | METHOD | Agents explain issued, pending, held, returned or corrected payments. | Reduces uncertainty. |
| benefitcallops.payments.card_issue | card issue route | METHOD | Benefit card problems route to replacement, PIN, vendor or fraud process. | Directs caller correctly. |
| benefitcallops.payments.overpayment_call | overpayment call | METHOD | Overpayment calls explain notice, repayment route and appeal boundary. | Handles sensitive debt issues. |
| benefitcallops.language.language_match | language match | METHOD | Caller language is identified early and interpreter route is offered. | Improves equitable access. |
| benefitcallops.language.interpreter_bridge | interpreter bridge | METHOD | Interpreter bridge connects agent, caller and interpreter with privacy reminder. | Keeps multilingual calls usable. |
| benefitcallops.language.translated_script | translated script | RECORD | Approved translated scripts cover common program phrases and warnings. | Reduces inconsistent explanations. |
| benefitcallops.accessibility.tty | TTY relay | METHOD | TTY or relay options support callers with hearing or speech needs. | Maintains access. |
| benefitcallops.accessibility.callback | callback accommodation | METHOD | Callback can support long waits, disabilities or dropped calls. | Reduces service burden. |
| benefitcallops.scripts.script_library | script library | RECORD | Script library stores approved opening, verification, program and closure wording. | Keeps answers consistent. |
| benefitcallops.scripts.knowledge_article | knowledge article | RECORD | Article links policy, workflow, examples and escalation route. | Helps agents answer accurately. |
| benefitcallops.scripts.update_control | script update control | METHOD | Script changes require owner, approval, publish date and retirement of old text. | Prevents outdated guidance. |
| benefitcallops.escalation.caseworker | caseworker escalation | METHOD | Escalation sends case-specific issues to assigned worker or unit. | Resolves beyond-call authority. |
| benefitcallops.escalation.supervisor | supervisor escalation | METHOD | Supervisors handle complaints, threats, policy uncertainty and service failures. | Protects callers and agents. |
| benefitcallops.escalation.emergency_referral | emergency referral | SAFETY_RULE | Imminent hunger, homelessness, violence or medical danger triggers emergency referral path. | Addresses acute risk. |
| benefitcallops.escalation.tech_ticket | technical ticket | METHOD | Portal or system failures create IT ticket with screenshots, error and caller impact. | Fixes access problems. |
| benefitcallops.quality.call_monitor | call monitoring | QUALITY_CHECK | Sample calls are reviewed for accuracy, privacy, tone and completeness. | Improves service quality. |
| benefitcallops.quality.error_correction | error correction | METHOD | Incorrect advice triggers correction, retraining and possible case follow-up. | Limits harm from bad guidance. |
| benefitcallops.quality.coaching | coaching plan | METHOD | Coaching targets repeated gaps in policy, systems or communication. | Builds agent capability. |
| benefitcallops.metrics.wait_time | wait time | MEASUREMENT | Wait time tracks queue delay by program, language and time. | Guides staffing. |
| benefitcallops.metrics.abandonment | abandonment rate | MEASUREMENT | Abandonment shows callers leaving before service. | Signals access problems. |
| benefitcallops.metrics.first_contact | first contact resolution | MEASUREMENT | First contact resolution tracks calls solved without repeat or escalation. | Measures usefulness. |
| benefitcallops.records.call_note | call note | RECORD | Note records verified facts, advice given, tasks and next steps. | Supports case continuity. |
| benefitcallops.records.retention | retention rule | CONSTRAINT | Notes and recordings follow program privacy, retention and legal hold rules. | Controls sensitive records. |
| benefitcallops.continuity.outage_plan | outage plan | METHOD | Outage plan covers phone, eligibility system, portal or payment system downtime. | Keeps service during disruption. |
| benefitcallops.closeout.summary | call closeout summary | METHOD | Agent ends with action items, deadlines, reference number and support route. | Leaves caller with clear next steps. |
