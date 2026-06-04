# BATCH 426: Disaster Senior Outreach Visit Scheduling Operations

**KnowledgeUnits:** 44  
**Namespace:** `seniorvisitops.*`  
**Scope:** referrals, priority, route planning, safety, contact attempts, needs and follow-up.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| seniorvisitops.intake.referral_source | referral source | RECORD | Source records hotline, clinic, utility, neighbor, shelter, caseworker or family. | Shows origin. |
| seniorvisitops.intake.senior_profile | senior profile | RECORD | Profile captures name, age, address, contact, language, access and safe-contact limits. | Defines visit target. |
| seniorvisitops.intake.vulnerability | vulnerability record | RECORD | Record notes mobility, isolation, oxygen, medication, cognition, heat/cold risk or caregiver absence. | Supports priority. |
| seniorvisitops.intake.consent_basis | consent basis | RECORD | Consent or welfare-check basis documents why outreach is appropriate. | Protects privacy. |
| seniorvisitops.priority.priority_score | priority score | MODEL | Score weighs medical dependence, isolation, outage, missed contact, age and hazard zone. | Orders visits. |
| seniorvisitops.priority.life_safety | life safety flag | SAFETY_RULE | Immediate danger routes to emergency services rather than routine visit. | Prevents delay. |
| seniorvisitops.priority.duplicate_referral | duplicate referral check | QUALITY_CHECK | Check links repeated referrals for the same person or address. | Reduces wasted visits. |
| seniorvisitops.priority.revisit_rule | revisit rule | CONSTRAINT | Revisit timing depends on risk level, prior outcome and available capacity. | Maintains coverage. |
| seniorvisitops.route.route_batch | route batch | METHOD | Batch groups visits by geography, priority, road access and team capacity. | Saves time. |
| seniorvisitops.route.travel_time | travel time | MEASUREMENT | Estimate includes road closures, weather, stairs and rural access. | Plans shift. |
| seniorvisitops.route.access_notes | access notes | RECORD | Notes capture gate code, apartment, elevator, pets, mobility or language support. | Prevents failed visit. |
| seniorvisitops.route.map_status | map status | RECORD | Map marks pending, attempted, completed, escalated and blocked visits. | Visualizes work. |
| seniorvisitops.team.team_assignment | team assignment | RECORD | Assignment lists team members, vehicle, route, PPE, phone and supervisor. | Deploys safely. |
| seniorvisitops.team.role_brief | role brief | METHOD | Brief defines contact, observation, referral, documentation and escalation roles. | Aligns team. |
| seniorvisitops.team.interpreter_need | interpreter need | RECORD | Need records language, phone interpreter or bilingual team assignment. | Improves access. |
| seniorvisitops.team.badge | badge rule | SAFETY_RULE | Teams carry identification and explain role before asking questions. | Builds trust. |
| seniorvisitops.safety.field_brief | field safety brief | SAFETY_RULE | Brief covers hazards, pets, conflict, weather, unsafe structures and withdrawal rules. | Protects team. |
| seniorvisitops.safety.buddy_system | buddy system | SAFETY_RULE | Visits use buddy or check-in system when risk warrants. | Reduces field risk. |
| seniorvisitops.safety.no_entry | no-entry rule | CONSTRAINT | Teams avoid entering unsafe or private spaces unless policy and safety allow. | Controls liability. |
| seniorvisitops.safety.incident | incident report | RECORD | Incident records injury, threat, medical event, unsafe site or missing person concern. | Supports review. |
| seniorvisitops.contact.phone_attempt | phone attempt | RECORD | Attempt records number, time, result, voicemail and next action. | Builds contact history. |
| seniorvisitops.contact.door_attempt | door attempt | RECORD | Door attempt records time, answer, observation, note left and safety issues. | Tracks visit. |
| seniorvisitops.contact.neighbor_info | neighbor information | RECORD | Neighbor information captures source, reliability, privacy limits and lead. | Adds context. |
| seniorvisitops.contact.no_contact | no-contact outcome | METHOD | No-contact rules define retry, welfare escalation or closure by risk. | Prevents missed danger. |
| seniorvisitops.needs.needs_screen | needs screen | RECORD | Screen covers food, water, medication, power, cooling/heating, transport and caregiver support. | Identifies support. |
| seniorvisitops.needs.home_safety | home safety observation | QUALITY_CHECK | Observation notes heat/cold, fall hazards, utilities, sanitation and access. | Flags risks. |
| seniorvisitops.needs.social_isolation | isolation note | RECORD | Note records loneliness, no caregiver, no phone or lost community contact. | Guides support. |
| seniorvisitops.needs.supply_request | supply request | RECORD | Request captures items needed, urgency, delivery constraints and referral owner. | Starts help. |
| seniorvisitops.referral.medical | medical referral | METHOD | Medical concerns route to EMS, clinic, nurse line or public health pathway. | Connects care. |
| seniorvisitops.referral.casework | casework referral | METHOD | Casework handles benefits, housing, repairs, documents and long-term support. | Supports recovery. |
| seniorvisitops.referral.utility | utility referral | METHOD | Utility referral handles outage priority, medical baseline, reconnection or device power. | Reduces risk. |
| seniorvisitops.referral.transport | transport referral | METHOD | Transport referral supports clinic, shelter, cooling center or supply pickup trips. | Restores access. |
| seniorvisitops.followup.followup_date | follow-up date | RECORD | Date records next call, revisit, referral check or closure review. | Maintains continuity. |
| seniorvisitops.followup.referral_check | referral check | QUALITY_CHECK | Check confirms whether urgent referral was accepted or completed. | Closes loop. |
| seniorvisitops.followup.status_update | status update | METHOD | Update informs referral source within privacy limits. | Reduces duplicate requests. |
| seniorvisitops.followup.case_close | case close | RECORD | Closure records safe, referred, moved, unreachable, escalated or deceased outcome. | Ends case. |
| seniorvisitops.records.visit_log | visit log | RECORD | Log stores referral, priority, attempts, observations, needs, referrals and outcome. | Creates audit trail. |
| seniorvisitops.records.privacy | privacy rule | SAFETY_RULE | Records minimize health and household details while preserving safety facts. | Protects seniors. |
| seniorvisitops.records.retention | retention rule | CONSTRAINT | Records follow emergency, aging services, privacy and grant schedules. | Controls lifecycle. |
| seniorvisitops.metrics.visits_completed | visits completed | MEASUREMENT | Count tracks visits completed by route, priority and outcome. | Shows output. |
| seniorvisitops.metrics.time_to_visit | time to visit | MEASUREMENT | Time measures referral to first attempt and confirmed outcome. | Reveals delay. |
| seniorvisitops.metrics.unmet_need | unmet need count | MEASUREMENT | Count tracks food, medical, utility, transport and social support gaps. | Guides resources. |
| seniorvisitops.qa.supervisor_review | supervisor review | QUALITY_CHECK | Review checks high-risk closures, no-contact cases and referral completion. | Improves safety. |
| seniorvisitops.review.after_action | after-action review | METHOD | Review captures priority rules, route planning, safety, contact barriers and referral lessons. | Improves future outreach. |
