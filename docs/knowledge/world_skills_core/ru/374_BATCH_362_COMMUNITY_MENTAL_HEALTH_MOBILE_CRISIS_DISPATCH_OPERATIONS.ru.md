# BATCH 362: Community Mental Health Mobile Crisis Dispatch Operations

**KnowledgeUnits:** 44  
**Namespace:** `mobilecrisisops.*`  
**Scope:** intake, risk triage, team assignment, safety planning, handoff and QA.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| mobilecrisisops.intake.call_id | dispatch call ID | RECORD | Call ID links caller, subject, time, location, risk and assigned response. | Creates traceable dispatch record. |
| mobilecrisisops.intake.referral_source | referral source | RECORD | Source distinguishes hotline, 911, clinic, family, school, police or self-referral. | Guides response context. |
| mobilecrisisops.intake.presenting_issue | presenting issue | RECORD | Presenting issue summarizes distress, behavior, needs and caller concern. | Frames triage. |
| mobilecrisisops.intake.location | location assessment | METHOD | Location captures address, access, safety hazards and whether subject is present. | Supports team deployment. |
| mobilecrisisops.triage.risk_level | risk level | MODEL | Risk level considers harm risk, psychosis, substance use, medical need, weapons and support. | Determines response urgency. |
| mobilecrisisops.triage.imminent_danger | imminent danger | SAFETY_RULE | Imminent danger routes to emergency services or co-response per policy. | Protects life safety. |
| mobilecrisisops.triage.medical_screen | medical screen | SAFETY_RULE | Medical symptoms, overdose, injury or altered consciousness trigger medical response. | Avoids wrong responder. |
| mobilecrisisops.triage.weapon_check | weapon check | SAFETY_RULE | Weapon or violence risk changes staging, law enforcement coordination or response type. | Protects teams. |
| mobilecrisisops.triage.consent_context | consent context | CONSTRAINT | Voluntary engagement is preferred, but legal emergency rules may apply. | Balances rights and safety. |
| mobilecrisisops.dispatch.team_match | team match | METHOD | Team assignment considers risk, location, language, age, clinical need and availability. | Sends suitable responders. |
| mobilecrisisops.dispatch.response_time | response time target | MEASUREMENT | Target time depends on urgency, geography and program rules. | Sets operational expectation. |
| mobilecrisisops.dispatch.staging | staging location | METHOD | High-risk calls may stage nearby before approach. | Improves safety. |
| mobilecrisisops.dispatch.status_update | status update | METHOD | Dispatch records en route, arrived, contact made, cleared and follow-up states. | Maintains situational awareness. |
| mobilecrisisops.team.roles | team roles | RECORD | Team roles may include clinician, peer, EMT, caseworker or supervisor. | Clarifies responsibilities. |
| mobilecrisisops.team.equipment | field equipment | RECORD | Equipment includes phone, radio, PPE, forms, resource list and safety kit. | Supports field work. |
| mobilecrisisops.team.briefing | pre-arrival briefing | METHOD | Briefing covers risk, history, caller details, safety plan and engagement approach. | Aligns team. |
| mobilecrisisops.team.fatigue | fatigue control | SAFETY_RULE | Teams need breaks and backup after intense or long calls. | Maintains judgment. |
| mobilecrisisops.engagement.initial_contact | initial contact | METHOD | Contact uses calm identification, consent, respect and space. | Reduces escalation. |
| mobilecrisisops.engagement.deescalation | de-escalation | METHOD | De-escalation uses listening, grounding, choices and reduced stimulation. | Improves safety. |
| mobilecrisisops.engagement.family | family engagement | METHOD | Family or bystanders are engaged when helpful and safe. | Builds support network. |
| mobilecrisisops.engagement.cultural | cultural response | METHOD | Response considers language, culture, disability and prior trauma. | Improves trust. |
| mobilecrisisops.assessment.safety | safety assessment | METHOD | Assessment checks current risk, protective factors, needs and willingness for help. | Guides disposition. |
| mobilecrisisops.assessment.substance | substance use screen | METHOD | Substance use screen informs safety, medical need and referral path. | Avoids misclassification. |
| mobilecrisisops.assessment.housing | social needs screen | METHOD | Housing, food, benefits, transport and caregiving needs are noted. | Connects crisis to practical support. |
| mobilecrisisops.assessment.legal | legal status check | CONSTRAINT | Holds, warrants or court orders are handled by authorized agencies. | Keeps roles lawful. |
| mobilecrisisops.plan.safety_plan | safety plan | RECORD | Safety plan lists warning signs, coping steps, contacts, means reduction and follow-up. | Supports stabilization. |
| mobilecrisisops.plan.least_restrictive | least restrictive option | MODEL | Disposition seeks least restrictive safe care setting. | Protects autonomy. |
| mobilecrisisops.plan.transport | transport plan | METHOD | Transport to clinic, crisis center, shelter or hospital follows safety and consent rules. | Moves person to care. |
| mobilecrisisops.plan.no_transport | no transport plan | METHOD | If no transport, plan records supports, follow-up and safety conditions. | Avoids empty closure. |
| mobilecrisisops.handoff.warm | warm handoff | METHOD | Warm handoff connects person to receiving provider with context and consent. | Reduces drop-off. |
| mobilecrisisops.handoff.ems | EMS handoff | METHOD | EMS handoff communicates risk, medical observations and scene safety. | Supports emergency care. |
| mobilecrisisops.handoff.law_enforcement | law enforcement handoff | SAFETY_RULE | Law enforcement handoff is limited to safety/legal need and documented. | Avoids unnecessary criminalization. |
| mobilecrisisops.handoff.provider | provider referral | METHOD | Provider referral includes eligibility, appointment, records and follow-up task. | Continues care. |
| mobilecrisisops.documentation.note | crisis note | RECORD | Note records risk, interventions, plan, disposition and consent. | Supports continuity. |
| mobilecrisisops.documentation.rationale | disposition rationale | RECORD | Rationale explains why team chose home, referral, crisis center, hospital or emergency route. | Makes decision reviewable. |
| mobilecrisisops.documentation.privacy | privacy boundary | SAFETY_RULE | Sensitive behavioral health information is shared only as allowed and needed. | Protects clients. |
| mobilecrisisops.documentation.retention | retention rule | CONSTRAINT | Dispatch and clinical records follow privacy and program retention rules. | Controls lifecycle. |
| mobilecrisisops.followup.callback | follow-up callback | METHOD | Follow-up confirms safety, appointments, barriers and resource needs. | Reduces recurrence. |
| mobilecrisisops.followup.missed | missed follow-up | METHOD | Missed follow-up triggers retry, partner check or escalation based on risk. | Keeps high-risk cases visible. |
| mobilecrisisops.metrics.diversion | diversion metric | MEASUREMENT | Diversion tracks avoided ED, jail or involuntary transport when safely resolved. | Shows program value. |
| mobilecrisisops.metrics.response | response metric | MEASUREMENT | Metrics track response time, outcomes, repeat calls, demographics and geography. | Guides improvement. |
| mobilecrisisops.qa.case_review | case review | QUALITY_CHECK | Supervisors review high-risk, adverse, repeat or unusual cases. | Improves safety. |
| mobilecrisisops.qa.partner_feedback | partner feedback | METHOD | Feedback from hotline, EMS, police and providers identifies handoff gaps. | Improves coordination. |
| mobilecrisisops.closeout.scene_clear | scene clear | METHOD | Scene clear records team safety, disposition, transport and pending follow-up. | Ends dispatch responsibly. |
