# BATCH 357: Crisis Hotline Referral Operations

**KnowledgeUnits:** 44  
**Namespace:** `crisishotlineops.*`  
**Scope:** call triage, safety assessment, warm handoffs, resource directories, documentation and QA.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| crisishotlineops.intake.contact_id | contact ID | RECORD | Contact ID links caller, channel, time, queue, counselor and outcome. | Creates traceable hotline contact. |
| crisishotlineops.intake.channel | contact channel | RECORD | Channel distinguishes voice, text, chat, relay, app or partner transfer. | Supports different workflows. |
| crisishotlineops.intake.presenting_issue | presenting issue | RECORD | Presenting issue summarizes caller concern in respectful neutral language. | Guides triage. |
| crisishotlineops.intake.location | location capture | METHOD | Location is sought when needed for emergency response or local referral. | Enables relevant help. |
| crisishotlineops.triage.risk_level | risk level | MODEL | Risk level considers immediate danger, intent, means, support and protective factors. | Guides response intensity. |
| crisishotlineops.triage.safety_question | safety question | METHOD | Safety questions assess immediate harm risk without scripted interrogation. | Clarifies urgency. |
| crisishotlineops.triage.third_party | third-party concern | METHOD | Third-party callers are guided to support, consent limits and emergency options. | Handles indirect risk. |
| crisishotlineops.triage.non_crisis | non-crisis routing | METHOD | Non-crisis needs route to information, benefits, housing, clinic or community resources. | Keeps hotline useful. |
| crisishotlineops.safety.safety_plan | safety plan | METHOD | Safety plan identifies coping steps, contacts, environment changes and follow-up route. | Supports immediate stability. |
| crisishotlineops.safety.imminent_risk | imminent risk | SAFETY_RULE | Imminent risk may require emergency service activation under policy. | Protects life safety. |
| crisishotlineops.safety.mandated_report | mandated report | CONSTRAINT | Abuse, neglect or danger reports follow jurisdiction and program rules. | Meets legal duties. |
| crisishotlineops.safety.least_intrusive | least intrusive response | MODEL | Response aims for least intrusive safe intervention consistent with risk. | Balances safety and autonomy. |
| crisishotlineops.referral.resource_match | resource match | METHOD | Referral matches need, location, eligibility, hours, language and capacity. | Avoids useless referrals. |
| crisishotlineops.referral.warm_handoff | warm handoff | METHOD | Warm handoff connects caller directly to provider with consent. | Reduces drop-off. |
| crisishotlineops.referral.cold_referral | cold referral | METHOD | Cold referral gives contact details, hours, eligibility and what to expect. | Supports caller action. |
| crisishotlineops.referral.no_resource | no resource found | FAILURE_MODE | No-resource result records unmet need and alternative safety/support steps. | Shows service gaps. |
| crisishotlineops.directory.current_status | current status | RECORD | Resource status includes open, closed, waitlist, restricted or unknown. | Keeps referrals realistic. |
| crisishotlineops.directory.eligibility | eligibility filter | METHOD | Eligibility filters by age, residence, insurance, income, issue, identity or documentation. | Avoids wrong handoffs. |
| crisishotlineops.directory.capacity | capacity check | METHOD | Capacity check verifies beds, appointments, crisis slots or intake windows when possible. | Prevents dead-end referrals. |
| crisishotlineops.directory.language | language availability | RECORD | Directory tracks interpreter, bilingual staff and translated materials. | Supports accessible referral. |
| crisishotlineops.communication.active_listening | active listening | METHOD | Counselor uses reflective listening, validation and pacing. | Helps caller stabilize. |
| crisishotlineops.communication.deescalation | de-escalation | METHOD | De-escalation reduces panic, anger or overwhelm through calm structured support. | Improves safety. |
| crisishotlineops.communication.boundaries | scope boundary | CONSTRAINT | Hotline does not replace medical, legal or emergency services. | Prevents false promises. |
| crisishotlineops.communication.accessibility | accessibility support | METHOD | Relay, text, interpretation or alternate channel supports communication barriers. | Keeps service reachable. |
| crisishotlineops.privacy.confidentiality | confidentiality rule | SAFETY_RULE | Confidentiality is explained with limits for safety and legal duties. | Builds informed trust. |
| crisishotlineops.privacy.minimal_data | minimal data | CONSTRAINT | Hotline collects only data needed for safety, referral and reporting. | Reduces privacy burden. |
| crisishotlineops.privacy.consent_share | consent to share | RECORD | Consent to share is recorded before provider handoff when required. | Protects caller choice. |
| crisishotlineops.privacy.anonymous | anonymous caller | METHOD | Anonymous callers can receive support unless emergency action requires more information. | Preserves access. |
| crisishotlineops.documentation.contact_note | contact note | RECORD | Note records risk, support provided, referrals, consent and follow-up. | Supports continuity and audit. |
| crisishotlineops.documentation.risk_rationale | risk rationale | RECORD | Risk rationale explains why level and response were chosen. | Makes decisions reviewable. |
| crisishotlineops.documentation.followup_task | follow-up task | RECORD | Follow-up task records callback, provider confirmation or supervisor review. | Prevents open loops. |
| crisishotlineops.documentation.retention | retention rule | CONSTRAINT | Notes, recordings and chats follow privacy, clinical and grant retention rules. | Controls sensitive data. |
| crisishotlineops.followup.callback | callback | METHOD | Callback follows consent, safety plan and timing rules. | Maintains support after contact. |
| crisishotlineops.followup.provider_confirm | provider confirmation | METHOD | Confirmation checks whether handoff or referral was accepted when program allows. | Improves closed-loop support. |
| crisishotlineops.followup.unreachable | unreachable process | METHOD | Unreachable follow-up uses privacy-safe attempts and escalation if risk requires. | Balances safety and privacy. |
| crisishotlineops.staffing.supervision | clinical supervision | QUALITY_CHECK | Supervisors review high-risk contacts and counselor support needs. | Improves safety and staff care. |
| crisishotlineops.staffing.breaks | break rule | SAFETY_RULE | Counselors need breaks after intense contacts and long shifts. | Reduces burnout. |
| crisishotlineops.staffing.training | training curriculum | METHOD | Training covers crisis skills, risk policy, cultural humility, resources and documentation. | Builds competence. |
| crisishotlineops.qa.call_review | contact review | QUALITY_CHECK | Sample contacts are reviewed for risk assessment, empathy, policy and referral accuracy. | Improves hotline quality. |
| crisishotlineops.qa.resource_error | resource error correction | METHOD | Bad referral data triggers directory update and staff notice. | Prevents repeat errors. |
| crisishotlineops.metrics.answer_time | answer time | MEASUREMENT | Answer time tracks how quickly contacts reach counselor. | Shows access. |
| crisishotlineops.metrics.abandonment | abandonment rate | MEASUREMENT | Abandonment tracks contacts leaving before service. | Signals staffing pressure. |
| crisishotlineops.metrics.outcome | outcome category | MEASUREMENT | Outcome categories include stabilized, referral, emergency dispatch, follow-up or information only. | Shows service pattern. |
| crisishotlineops.closeout.shift_handoff | shift handoff | METHOD | Shift handoff flags open follow-ups, high-risk cases and resource changes. | Maintains continuity. |
