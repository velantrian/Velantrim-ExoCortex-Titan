# BATCH 370: Emergency Public Information Joint Information Center Operations

**KnowledgeUnits:** 44  
**Namespace:** `jicops.*`  
**Scope:** message clearance, rumor control, media briefings, translations and archiving.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| jicops.activation.trigger | activation trigger | MODEL | JIC activates when incident information demand exceeds routine communications. | Centralizes public messaging. |
| jicops.activation.lead_pio | lead PIO | RECORD | Lead public information officer coordinates agencies, approvals and release cadence. | Clarifies authority. |
| jicops.activation.roster | JIC roster | RECORD | Roster lists writers, monitors, translators, media staff and approvals. | Organizes communications labor. |
| jicops.activation.workspace | workspace setup | METHOD | Workspace includes phones, internet, monitors, briefing area and shared files. | Makes JIC functional. |
| jicops.message.objective | message objective | RECORD | Objective states what the public needs to know, do, avoid or expect. | Keeps wording action-focused. |
| jicops.message.audience | audience segment | RECORD | Audience distinguishes residents, evacuees, media, partners, languages and access needs. | Targets messages. |
| jicops.message.key_message | key message | METHOD | Key messages use confirmed facts, action steps, uncertainty and next update time. | Reduces confusion. |
| jicops.message.call_to_action | call to action | SAFETY_RULE | Public safety instructions are specific, feasible and time-bound. | Helps people act. |
| jicops.clearance.fact_check | fact check | QUALITY_CHECK | Facts are checked with operations, planning, safety or technical source. | Prevents false releases. |
| jicops.clearance.approval_path | approval path | METHOD | Approval path identifies who clears technical, legal, policy and incident command content. | Speeds safe release. |
| jicops.clearance.fast_release | fast release | METHOD | Preapproved templates allow urgent warnings with duty officer clearance. | Saves time in danger. |
| jicops.clearance.version | version record | RECORD | Version records draft, approver, time, channel and changes. | Supports audit. |
| jicops.channels.press_release | press release | METHOD | Press release gives confirmed facts, quotes, actions and contacts. | Serves media. |
| jicops.channels.social | social media post | METHOD | Social posts summarize action and link to canonical source. | Reaches fast-moving audiences. |
| jicops.channels.website | website update | METHOD | Website is canonical location for long-form updates and archives. | Reduces fragmented information. |
| jicops.channels.alert | emergency alert | SAFETY_RULE | Emergency alerts use official alerting criteria and concise protective action wording. | Avoids alert fatigue. |
| jicops.media.briefing_schedule | briefing schedule | RECORD | Briefings occur at predictable times with known spokespeople. | Reduces rumor pressure. |
| jicops.media.spokesperson | spokesperson | RECORD | Spokesperson is briefed on facts, limits and anticipated questions. | Keeps public voice coherent. |
| jicops.media.qanda | Q&A log | RECORD | Questions and answers are logged for consistency and follow-up. | Prevents mixed responses. |
| jicops.media.pool | media pool | METHOD | Media pool controls access when scene safety or privacy limits movement. | Balances transparency and safety. |
| jicops.rumor.monitoring | rumor monitoring | METHOD | Staff monitor social, calls, media and partner reports for misinformation. | Detects harmful narratives. |
| jicops.rumor.risk_rank | rumor risk rank | MODEL | Rumors are ranked by reach, harm, credibility and action impact. | Prioritizes response. |
| jicops.rumor.correction | correction message | METHOD | Corrections state what is true, what action to take and official source. | Reduces misinformation. |
| jicops.rumor.record | rumor record | RECORD | Rumor log stores claim, source, action and outcome. | Supports after-action review. |
| jicops.translation.priority | translation priority | MODEL | Translation priority uses life safety, affected languages and legal requirements. | Uses language capacity wisely. |
| jicops.translation.review | translation review | QUALITY_CHECK | Translated messages are checked against source facts and protective actions. | Prevents dangerous drift. |
| jicops.translation.plain_language | plain language | METHOD | Messages avoid jargon and explain uncertainty simply. | Improves public understanding. |
| jicops.translation.accessible | accessible format | METHOD | Accessible formats include captions, alt text, large print or audio where feasible. | Supports inclusive alerts. |
| jicops.partners.partner_sync | partner sync | METHOD | Agencies receive shared talking points and update schedule. | Keeps partners aligned. |
| jicops.partners.elected_official | elected official update | METHOD | Officials receive approved facts and constituent guidance. | Reduces unofficial messaging. |
| jicops.partners.call_center | call center script | METHOD | Call centers receive current scripts, FAQs and escalation rules. | Aligns public answers. |
| jicops.partners.community_org | community organization route | METHOD | Trusted organizations relay messages to hard-to-reach groups. | Expands reach. |
| jicops.monitoring.media_clip | media clipping | RECORD | Clips capture broadcast, print, online and social coverage. | Shows message spread. |
| jicops.monitoring.sentiment | sentiment signal | MEASUREMENT | Sentiment signals confusion, fear, anger or misinformation. | Guides future messages. |
| jicops.monitoring.hotline_topics | hotline topics | MEASUREMENT | Hotline and 311 topics reveal public information gaps. | Improves FAQs. |
| jicops.monitoring.web_metrics | web metrics | MEASUREMENT | Page views, searches and clicks show information demand. | Guides placement. |
| jicops.archive.release_archive | release archive | RECORD | Archive stores all released messages by channel and time. | Preserves record. |
| jicops.archive.approval_archive | approval archive | RECORD | Drafts and approvals are retained for accountability. | Supports investigation. |
| jicops.archive.photo_video | media asset archive | RECORD | Photos, video and graphics store rights, caption and release status. | Prevents misuse. |
| jicops.archive.retention | retention rule | CONSTRAINT | Records follow incident, public records and legal hold schedules. | Controls lifecycle. |
| jicops.staffing.shift_handoff | shift handoff | METHOD | Handoff covers open approvals, rumors, briefings, partner needs and next updates. | Maintains continuity. |
| jicops.staffing.burnout | staff fatigue | SAFETY_RULE | Communications staff need breaks during high-pressure information surges. | Maintains judgment. |
| jicops.qa.message_audit | message audit | QUALITY_CHECK | Audit checks accuracy, approvals, accessibility and archive completeness. | Improves reliability. |
| jicops.demob.stepdown | stepdown | METHOD | JIC demobilizes when demand falls and routine PIO can resume. | Ends surge cleanly. |
