# BATCH_169 — Call Center Quality Operations Detail
# world_skills_core · source: world_skills_core:batch_169:call_center_quality_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| callops.queue.service_level | Call center service level | invariant | Service level measures percentage of contacts answered within target time. | queue promise |
| callops.queue.average_speed_answer | Average speed of answer | invariant | ASA measures average wait time before agent answer for handled contacts. | waiting experience |
| callops.queue.abandon_rate | Abandon rate | invariant | Abandon rate shows contacts that leave queue before answer. | demand lost |
| callops.queue.queue_priority | Queue priority | variant | Priority routes contacts by customer type, issue severity, SLA, language or channel. | not every contact equal |
| callops.queue.callback_offer | Callback offer | variant | Callback lets customer keep place without waiting on line if system capacity supports it. | reduce hold frustration |
| callops.queue.overflow_routing | Overflow routing | variant | Overflow routing sends contacts to backup team, vendor or channel when queue exceeds threshold. | protect service level |
| callops.wfm.forecast_volume | Contact volume forecast | invariant | Forecast estimates future contacts by interval, channel, seasonality, events and historical patterns. | staffing starts here |
| callops.wfm.shrinkage | Workforce shrinkage | invariant | Shrinkage accounts for paid time not available for contacts, including breaks, training, absence and meetings. | true capacity |
| callops.wfm.schedule_adherence | Schedule adherence | invariant | Adherence compares agent actual activity to scheduled activity by interval. | schedule discipline |
| callops.wfm.intraday_management | Intraday management | invariant | Intraday adjusts breaks, queues, overtime, training or routing based on actual demand. | day changes live |
| callops.wfm.occupancy | Agent occupancy | invariant | Occupancy measures time agents spend handling contacts or after-call work versus available time. | workload intensity |
| callops.wfm.staffing_gap | Staffing gap | invariant | Gap compares required agents with available agents for an interval. | see undercoverage |
| callops.script.call_opening | Call opening | invariant | Opening confirms brand, agent identity, greeting and readiness to help. | first seconds matter |
| callops.script.identity_verification | Customer identity verification | invariant | Verification checks customer identity before account-specific disclosure or action. | protect account data |
| callops.script.discovery_questions | Discovery questions | invariant | Discovery questions clarify issue, context, urgency, history and desired outcome. | diagnose request |
| callops.script.disclosure_statement | Disclosure statement | variant | Disclosure informs caller of recording, terms, privacy or regulated information where required. | compliance in words |
| callops.script.call_closing | Call closing | invariant | Closing confirms resolution, next steps, reference number and final customer question. | end with clarity |
| callops.script.knowledge_article | Knowledge article | invariant | Article gives agents approved steps, wording, policy and escalation criteria for an issue. | consistent answer |
| callops.qa.scorecard | QA scorecard | invariant | Scorecard rates contact quality against criteria such as accuracy, compliance, empathy and resolution. | structured evaluation |
| callops.qa.calibration_session | QA calibration | invariant | Calibration aligns evaluators on scoring standards using shared examples and discussion. | reduce scorer drift |
| callops.qa.sample_selection | QA sample selection | variant | Sample selection chooses contacts by random, risk, agent, queue, complaint or new process. | what gets reviewed |
| callops.qa.critical_error | Critical error | invariant | Critical error is a severe miss such as privacy breach, misinformation, unauthorized action or abusive conduct. | high-severity quality gap |
| callops.qa.qa_dispute | QA dispute | variant | Dispute lets agent or supervisor challenge score with evidence and reviewer decision. | fairness in scoring |
| callops.qa.trend_analysis | QA trend analysis | invariant | Trend analysis groups quality misses by topic, agent, queue, policy or training gap. | quality becomes improvement |
| callops.escalation.tier_two | Tier-two escalation | invariant | Tier-two handles issues beyond front-line authority, tool access or knowledge. | structured handoff |
| callops.escalation.supervisor_takeover | Supervisor takeover | variant | Takeover moves live customer interaction to supervisor when authority, safety or service recovery requires it. | escalation in real time |
| callops.escalation.ticket_creation | Support ticket creation | invariant | Ticket records issue, customer, evidence, priority, owner, SLA and next action. | asynchronous work |
| callops.escalation.sla_clock | Support SLA clock | invariant | SLA clock measures time to response or resolution from defined start point. | deadline visibility |
| callops.escalation.root_cause_tag | Contact root cause tag | invariant | Root cause tag classifies why customer contacted, not only what agent did. | fix upstream cause |
| callops.escalation.warm_transfer | Warm transfer | variant | Warm transfer briefs receiving agent before customer handoff to avoid repetition. | better transfer |
| callops.complaint.complaint_intake | Complaint intake | invariant | Intake captures dissatisfaction, issue, impact, desired resolution and regulatory sensitivity. | complaint as case |
| callops.complaint.service_recovery | Service recovery | variant | Recovery offers correction, apology, credit, replacement or follow-up within authority. | repair trust |
| callops.complaint.vulnerable_customer_flag | Vulnerable customer flag | variant | Flag prompts extra care, accessibility support or specialist handling under policy. | adapt service |
| callops.complaint.regulatory_complaint | Regulatory complaint | invariant | Regulatory complaint requires special tracking, deadlines, evidence and approved response. | higher compliance risk |
| callops.coaching.coaching_plan | Agent coaching plan | invariant | Coaching plan links observed behavior, goal, action, practice and follow-up review. | quality improvement |
| callops.coaching.side_by_side | Side-by-side coaching | variant | Coach observes live or recorded contacts with agent to identify practical improvements. | learn from real work |
| callops.coaching.knowledge_gap | Agent knowledge gap | invariant | Knowledge gap indicates missing understanding of product, policy, tool or process. | train the right thing |
| callops.coaching.behavioral_feedback | Behavioral feedback | invariant | Feedback focuses on observable behavior and customer impact rather than personality. | coach fairly |
| callops.channels.email_queue | Email queue | variant | Email queue manages asynchronous written contacts with templates, SLA and quality review. | not all contacts are calls |
| callops.channels.chat_concurrency | Chat concurrency | variant | Chat concurrency defines how many simultaneous chats agent can handle safely. | multitasking limit |
| callops.channels.social_media_response | Social media response | variant | Social response balances speed, public tone, privacy and escalation to private channel. | public service desk |
| callops.channels.omnichannel_history | Omnichannel history | invariant | History links previous contacts across channels so customer context is visible. | no repeated story |
| callops.reporting.contact_reason | Contact reason report | invariant | Report shows why customers contact and supports self-service, product fixes or staffing. | demand intelligence |
| callops.reporting.first_contact_resolution | First contact resolution | invariant | FCR measures whether issue is resolved without repeat contact within defined window. | solve once |
