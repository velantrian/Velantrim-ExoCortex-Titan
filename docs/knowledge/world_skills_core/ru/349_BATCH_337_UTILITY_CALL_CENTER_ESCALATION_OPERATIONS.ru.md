# BATCH 337: Utility Call Center Escalation Operations

**KnowledgeUnits:** 44  
**Namespace:** `callescops.*`  
**Scope:** tiering, callbacks, supervisors, field coordination, complaints, SLAs, knowledge base and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| callescops.intake.call_reason | call reason | RECORD | Call reason codes identify billing, outage, leak, move, complaint, payment or field issue. | Routes the call to the right workflow. |
| callescops.intake.priority_screen | priority screen | DECISION_RULE | Safety, water outage, sewer backup, medical or media issues get urgent priority. | Prevents high-risk cases from waiting in normal queue. |
| callescops.intake.account_context | account context | METHOD | Agent reviews account status, open orders, recent contacts and alerts before escalation. | Avoids repeating work. |
| callescops.tiering.tier1_scope | tier 1 scope | CONSTRAINT | Tier 1 handles standard scripts, simple account actions and common answers. | Keeps routine calls fast. |
| callescops.tiering.tier2_scope | tier 2 scope | CONSTRAINT | Tier 2 handles complex billing, policy exceptions, technical issues and repeated contacts. | Gives difficult cases deeper review. |
| callescops.tiering.specialist_route | specialist route | METHOD | Calls route to billing, field, water quality, collections, engineering or legal specialists. | Expertise matches issue. |
| callescops.tiering.warm_transfer | warm transfer | METHOD | Agent briefs receiving staff before transferring customer. | Reduces customer repetition. |
| callescops.callbacks.callback_promise | callback promise | RECORD | Callback includes owner, due time, contact number and issue summary. | Makes promises trackable. |
| callescops.callbacks.callback_queue | callback queue | METHOD | Queue sorts callbacks by SLA, priority and staff skill. | Prevents forgotten returns. |
| callescops.callbacks.failed_callback | failed callback | RECORD | Failed attempt logs time, number, voicemail and next attempt. | Shows good-faith follow-up. |
| callescops.callbacks.after_hours | after-hours callback | DECISION_RULE | Urgent after-hours issues route to standby or emergency dispatch. | Keeps safety issues active outside office. |
| callescops.supervisor.supervisor_review | supervisor review | DECISION_RULE | Supervisor handles policy exceptions, angry customers, threats, high credits and escalated complaints. | Adds judgment and authority. |
| callescops.supervisor.approval_note | approval note | RECORD | Supervisor decision records policy basis, facts, approval or denial. | Supports audit and consistency. |
| callescops.supervisor.deescalation | de-escalation | METHOD | Staff use calm language, boundaries and options to reduce conflict. | Improves safety and customer outcomes. |
| callescops.field.field_ticket | field ticket | RECORD | Escalated field ticket includes address, issue, access, hazards, contact and priority. | Gives dispatch actionable information. |
| callescops.field.dispatch_sync | dispatch sync | METHOD | Call center checks field availability, route and emergency load before promising timing. | Prevents unrealistic commitments. |
| callescops.field.result_return | field result return | RECORD | Field result returns diagnosis, action, photos, reads and next steps to customer service. | Allows complete customer follow-up. |
| callescops.field.safety_alert | safety alert | SAFETY_RULE | Threats, dogs, unsafe property or hostile calls are flagged for field crews. | Protects staff. |
| callescops.complaints.formal_complaint | formal complaint | RECORD | Formal complaint records issue, requested remedy, prior contacts and escalation level. | Creates governed path beyond ordinary call. |
| callescops.complaints.regulatory | regulatory complaint | METHOD | Regulator or elected-official complaints receive special tracking and deadlines. | Protects compliance and reputation. |
| callescops.complaints.repeat_contact | repeat contact | QUALITY_CHECK | Multiple contacts on same issue trigger escalation review. | Prevents churn without resolution. |
| callescops.complaints.root_cause | complaint root cause | MODEL | Root cause categories include policy, billing error, field delay, communication or customer misunderstanding. | Helps fix process, not just one case. |
| callescops.sla.response_sla | response SLA | CONSTRAINT | SLA defines response or resolution target by priority and issue type. | Sets measurable service expectations. |
| callescops.sla.breach | SLA breach | FAILURE_MODE | Breached cases are flagged for supervisor action and explanation. | Keeps aged work visible. |
| callescops.sla.pause_rule | SLA pause rule | DECISION_RULE | SLA may pause for customer documents, weather, parts, or third-party dependency. | Makes metrics fair. |
| callescops.knowledge.kb_article | knowledge base article | RECORD | Article stores approved answer, policy, steps, owner and review date. | Keeps agents consistent. |
| callescops.knowledge.kb_gap | knowledge gap | RECORD | Agents flag missing or unclear guidance for update. | Improves self-service and training. |
| callescops.knowledge.script_update | script update | METHOD | Scripts are revised after policy change, incident or repeated confusion. | Keeps call handling current. |
| callescops.quality.call_monitor | call monitoring | QUALITY_CHECK | Supervisors review calls for accuracy, empathy, verification and closeout. | Builds coaching evidence. |
| callescops.quality.coaching | coaching note | RECORD | Coaching records issue, example, expected behavior and follow-up. | Turns QA into improvement. |
| callescops.quality.error_correction | error correction | METHOD | Incorrect advice triggers customer correction and staff feedback. | Repairs harm from bad guidance. |
| callescops.system.crm_case | CRM case | RECORD | CRM case stores call notes, tasks, attachments, SLA, owner and status. | Single source for escalation. |
| callescops.system.queue_status | queue status | RECORD | Status distinguishes new, assigned, waiting, field pending, customer pending, resolved and closed. | Makes backlog manageable. |
| callescops.system.integration_error | integration error | FAILURE_MODE | Billing, outage, AMI or work-order integration failures can hide updates. | Agents need fallback checks. |
| callescops.communication.plain_summary | plain summary | METHOD | Agent summarizes decision, next step, owner and expected timing. | Customer knows what will happen. |
| callescops.communication.bad_news | bad-news delivery | METHOD | Denials or delays are explained with policy basis and options. | Reduces escalation caused by surprise. |
| callescops.communication.accessibility | accessibility support | METHOD | Calls may need relay, translation, large-print follow-up or caregiver authorization. | Expands equitable service. |
| callescops.reporting.escalation_volume | escalation volume | MEASUREMENT | Reports track escalations by reason, tier, age, outcome and owner. | Shows pressure points. |
| callescops.reporting.first_call_resolution | first-call resolution | MEASUREMENT | FCR measures cases solved without escalation or repeat contact. | Indicates knowledge and authority quality. |
| callescops.reporting.top_drivers | top drivers | MODEL | Top escalation drivers reveal policy confusion, field delays or system defects. | Guides improvement work. |
| callescops.review.daily_huddle | daily huddle | METHOD | Teams review hot cases, outages, policy changes and staffing. | Keeps call center aligned. |
| callescops.review.after_event | after-event review | METHOD | Major billing, outage or water-quality events get call-center after-action review. | Improves surge response. |
| callescops.closeout.close_criteria | close criteria | QUALITY_CHECK | Case closes only after answer, action, customer notice or documented no-response. | Prevents premature closure. |
| callescops.closeout.satisfaction_note | satisfaction note | RECORD | Optional satisfaction or sentiment note records unresolved frustration. | Helps identify cases needing management attention. |

