# BATCH 352: Homeless Outreach Case Management Operations

**KnowledgeUnits:** 44  
**Namespace:** `outreachcaseops.*`  
**Scope:** field outreach, consent, assessment, referrals, shelter placement, follow-up and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| outreachcaseops.field.location_log | location log | RECORD | Log records outreach site, date, team, weather and observed needs. | Tracks field coverage. |
| outreachcaseops.field.team_safety | team safety check | SAFETY_RULE | Staff check hazards, partner status, radio/phone and exit route before contact. | Protects outreach workers. |
| outreachcaseops.field.engagement | engagement approach | METHOD | Outreach begins with voluntary, trauma-informed contact and practical offer. | Builds trust. |
| outreachcaseops.field.repeat_contact | repeat contact | METHOD | Repeated contacts may be needed before assessment or service acceptance. | Respects client readiness. |
| outreachcaseops.consent.informed_consent | informed consent | SAFETY_RULE | Client consent is obtained before sharing identifiable information unless law permits exception. | Protects autonomy and privacy. |
| outreachcaseops.consent.release_scope | release scope | RECORD | Release states agency, data type, purpose, duration and revocation route. | Makes sharing bounded. |
| outreachcaseops.consent.decline | service decline | RECORD | Decline records offer, reason if given and next safe contact plan. | Avoids coercive service. |
| outreachcaseops.consent.capacity_concern | capacity concern | MODEL | Capacity concern triggers supervisor or clinical consultation when safety or understanding is impaired. | Balances autonomy and protection. |
| outreachcaseops.assessment.vulnerability | vulnerability assessment | METHOD | Assessment covers age, disability, health, victimization, duration homeless and safety risk. | Prioritizes support. |
| outreachcaseops.assessment.needs | needs assessment | RECORD | Needs include shelter, ID, benefits, medical, behavioral health, substance use, transport and food. | Guides case plan. |
| outreachcaseops.assessment.identity_docs | identity documents | RECORD | Document status tracks ID, birth certificate, social/security numbers or immigration papers where relevant. | Enables benefits and housing. |
| outreachcaseops.assessment.encampment_risk | encampment risk | MODEL | Risk considers weather, sanitation, violence, fire, flooding and public works conflict. | Informs response. |
| outreachcaseops.case.plan | case plan | RECORD | Plan records goals, referrals, responsibilities, dates and barriers. | Turns outreach into coordinated action. |
| outreachcaseops.case.owner | case owner | RECORD | One owner coordinates contacts until transfer or closure. | Prevents fragmented help. |
| outreachcaseops.case.priority | priority level | MODEL | Priority reflects vulnerability, risk, eligibility and available placement. | Allocates scarce resources. |
| outreachcaseops.case.barrier | barrier tracking | RECORD | Barriers include documents, phone, transport, pets, partner, belongings or behavioral health. | Makes obstacles explicit. |
| outreachcaseops.referral.shelter | shelter referral | METHOD | Referral checks bed availability, eligibility, curfew, accessibility and client preference. | Improves placement success. |
| outreachcaseops.referral.housing | housing referral | METHOD | Housing referral links assessment, documentation, voucher or coordinated entry status. | Moves beyond emergency shelter. |
| outreachcaseops.referral.health | health referral | METHOD | Health referral connects to clinic, crisis team, detox, medication support or insurance help. | Addresses care needs. |
| outreachcaseops.referral.benefits | benefits referral | METHOD | Benefits referral supports applications for income, food, insurance or disability aid. | Stabilizes client resources. |
| outreachcaseops.placement.bed_match | bed match | METHOD | Bed match considers household, gender policy, accessibility, pets, safety and location. | Reduces failed placements. |
| outreachcaseops.placement.transport | transport coordination | METHOD | Transport plan gets client to shelter, clinic, office or housing appointment. | Prevents missed opportunity. |
| outreachcaseops.placement.warm_handoff | warm handoff | METHOD | Staff directly connect client to receiving program when possible. | Reduces drop-off. |
| outreachcaseops.placement.failed | failed placement | FAILURE_MODE | Placement fails from no-show, rule conflict, capacity change, transport or client choice. | Triggers new plan. |
| outreachcaseops.followup.appointment | appointment follow-up | METHOD | Follow-up confirms attendance, barriers and next step. | Maintains momentum. |
| outreachcaseops.followup.locate | locate attempt | METHOD | Locate attempt uses known sites, phone, partner check or outreach schedule. | Finds clients without stable contact. |
| outreachcaseops.followup.status_update | status update | RECORD | Status update records housed, sheltered, unsheltered, unreachable, declined or transferred. | Keeps caseload accurate. |
| outreachcaseops.followup.reengagement | reengagement | METHOD | Reengagement restarts contact after missed appointments or service declines. | Keeps door open. |
| outreachcaseops.records.case_note | case note | RECORD | Case note records facts, offers, client choices and next action respectfully. | Supports continuity. |
| outreachcaseops.records.hmis | HMIS entry | METHOD | Homeless management system data follows local definitions and consent rules. | Supports coordinated services. |
| outreachcaseops.records.privacy | privacy boundary | SAFETY_RULE | Location and personal data are shared only with need-to-know partners. | Protects vulnerable clients. |
| outreachcaseops.records.retention | retention rule | CONSTRAINT | Outreach records follow program, grant and privacy retention rules. | Controls data lifecycle. |
| outreachcaseops.partners.coordinated_entry | coordinated entry | METHOD | Coordinated entry uses shared assessment and prioritization for housing resources. | Aligns regional housing access. |
| outreachcaseops.partners.public_works | public works liaison | METHOD | Liaison coordinates encampment cleanup timing, notices and belongings policy. | Reduces harm during site actions. |
| outreachcaseops.partners.police_fire | emergency services liaison | METHOD | Liaison supports safety calls without turning routine outreach into enforcement. | Keeps roles clear. |
| outreachcaseops.partners.nonprofit | nonprofit partner | METHOD | Partner referrals share tasks for meals, showers, legal aid, clothing or casework. | Broadens support. |
| outreachcaseops.supplies.field_kit | field kit | RECORD | Kit includes water, snacks, hygiene, forms, PPE, chargers and weather supplies. | Enables practical help. |
| outreachcaseops.supplies.inventory | supply inventory | MEASUREMENT | Inventory tracks issued items, stock and replenishment needs. | Prevents shortages. |
| outreachcaseops.safety.weather | weather protocol | SAFETY_RULE | Extreme heat, cold, smoke or storm changes outreach cadence and referral urgency. | Protects clients and staff. |
| outreachcaseops.safety.incident | incident report | RECORD | Incident report records threat, injury, overdose, death, conflict or mandated report. | Supports safety review. |
| outreachcaseops.metrics.contacts | contact metric | MEASUREMENT | Contacts track unique people, repeat contacts, assessments and referrals. | Shows outreach activity. |
| outreachcaseops.metrics.placement_rate | placement rate | MEASUREMENT | Placement rate tracks shelter or housing placements from outreach contacts. | Measures outcomes. |
| outreachcaseops.qa.supervision | case supervision | QUALITY_CHECK | Supervisors review high-risk cases, documentation and service barriers. | Improves practice. |
| outreachcaseops.closeout.closure_reason | closure reason | RECORD | Closure reason states housed, transferred, declined, unreachable, moved or deceased. | Makes case end explicit. |
