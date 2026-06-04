# BATCH_242 — Community Health Outreach Operations Detail
# world_skills_core · source: world_skills_core:batch_242:community_health_outreach_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| healthoutreach.plan.population_segment | Health outreach population segment | invariant | Segment defines community, risk factor, language, geography, age or service barrier. | focus outreach |
| healthoutreach.plan.needs_assessment | Community health needs assessment | variant | Assessment combines local data, partner input, field observations and resident feedback. | choose priorities |
| healthoutreach.plan.outreach_goal | Health outreach goal | invariant | Goal states education, referral, screening, enrollment, follow-up or trust-building outcome. | guide work |
| healthoutreach.plan.site_selection | Outreach site selection | variant | Selection chooses schools, shelters, clinics, markets, faith sites or mobile locations. | reach people |
| healthoutreach.plan.risk_boundary | Outreach risk boundary | invariant | Boundary avoids diagnosis, dosing or promises outside program authority and clinical supervision. | safe scope |
| healthoutreach.team.field_team_roster | Health outreach field team roster | invariant | Roster assigns staff, roles, language skills, credentials, contact and shift. | field coverage |
| healthoutreach.team.briefing | Health outreach team briefing | invariant | Briefing covers goals, safety, scripts, referrals, supplies, privacy and escalation. | aligned team |
| healthoutreach.team.peer_worker | Peer outreach worker role | variant | Role uses lived experience for engagement, navigation, trust and follow-up support. | improve access |
| healthoutreach.team.interpreter_support | Outreach interpreter support | variant | Support matches language, privacy, cultural context and documentation needs. | clear communication |
| healthoutreach.team.debrief | Health outreach debrief | invariant | Debrief captures contacts, issues, safety concerns, referrals, supplies and lessons. | improve next shift |
| healthoutreach.event.event_booking | Health outreach event booking | invariant | Booking records site, date, permits, host contact, space, utilities and audience. | secure venue |
| healthoutreach.event.table_setup | Outreach table setup | variant | Setup places signs, materials, forms, privacy screen, sharps box if needed and supplies. | ready station |
| healthoutreach.event.crowd_flow | Outreach crowd flow | variant | Flow manages queue, greeting, private conversation, referral and exit. | respectful service |
| healthoutreach.event.mobile_unit | Health outreach mobile unit | variant | Unit plan covers vehicle, route, parking, power, supplies, staff and weather. | extend reach |
| healthoutreach.event.safety_plan | Outreach event safety plan | invariant | Plan covers staff check-ins, conflict, weather, emergency contacts and site hazards. | protect team |
| healthoutreach.education.message_guide | Health education message guide | invariant | Guide provides approved plain-language messages, limits, translations and source owner. | consistent education |
| healthoutreach.education.material_inventory | Outreach material inventory | invariant | Inventory tracks flyers, kits, forms, languages, quantities and reorder points. | avoid shortages |
| healthoutreach.education.cultural_adaptation | Health message cultural adaptation | variant | Adaptation adjusts examples, language, imagery and delivery with community input. | improve relevance |
| healthoutreach.education.misinformation_response | Health misinformation response | variant | Response listens, corrects gently with approved facts and routes complex questions. | build trust |
| healthoutreach.education.consent_script | Outreach consent script | invariant | Script explains voluntary participation, privacy, data use, limits and referral choices. | informed contact |
| healthoutreach.referral.referral_directory | Health outreach referral directory | invariant | Directory lists clinics, benefits, shelters, food, transport, mental health and eligibility. | navigation |
| healthoutreach.referral.warm_handoff | Outreach warm handoff | variant | Handoff connects participant to partner with consent, contact details and next step. | reduce drop-off |
| healthoutreach.referral.eligibility_check | Outreach eligibility check | variant | Check screens program fit using approved questions without making final clinical decisions. | route correctly |
| healthoutreach.referral.closed_loop | Closed-loop outreach referral | invariant | Loop records referral, confirmation, barrier, follow-up attempt and outcome. | ensure connection |
| healthoutreach.referral.crisis_escalation | Outreach crisis escalation | invariant | Escalation routes immediate danger, severe distress or abuse concern to trained responders. | safety net |
| healthoutreach.data.contact_log | Health outreach contact log | invariant | Log records nonclinical contact type, location, topic, referral and consented identifiers. | measure reach |
| healthoutreach.data.privacy_minimum | Outreach privacy minimum | invariant | Minimum limits collected data to program need, consent and retention rules. | protect people |
| healthoutreach.data.paper_form_control | Outreach paper form control | invariant | Control secures forms, counts pages, transfers to office and logs destruction. | data custody |
| healthoutreach.data.data_quality_check | Outreach data quality check | invariant | Check reviews missing fields, duplicate contacts, inconsistent site codes and follow-up flags. | reliable reporting |
| healthoutreach.data.dashboard_update | Outreach dashboard update | variant | Update summarizes contacts, referrals, events, populations, geography and trends. | operational insight |
| healthoutreach.followup.followup_queue | Health outreach follow-up queue | invariant | Queue prioritizes pending referrals, high-barrier participants, missed contacts and time limits. | continue support |
| healthoutreach.followup.contact_attempt | Outreach contact attempt | invariant | Attempt records date, channel, result, message left and next step. | track effort |
| healthoutreach.followup.barrier_note | Outreach barrier note | variant | Note captures transport, language, cost, documents, fear, schedule or access barrier. | target help |
| healthoutreach.followup.partner_feedback | Outreach partner feedback | variant | Feedback confirms referral fit, capacity issue, missing information or service gap. | improve network |
| healthoutreach.followup.case_closure | Outreach follow-up closure | invariant | Closure records completed, unreachable, declined, referred elsewhere or expired status. | close loop |
| healthoutreach.partners.partner_mou | Health outreach partner MOU | variant | MOU defines roles, data sharing, referrals, supplies, staffing and communication. | shared governance |
| healthoutreach.partners.host_site_check | Outreach host site check | invariant | Check confirms space, privacy, accessibility, utilities, restrooms and safety contacts. | viable event |
| healthoutreach.partners.community_advisor | Community health advisor input | variant | Input gathers local concerns, trust issues, messaging feedback and outreach timing. | community fit |
| healthoutreach.supplies.outreach_kit | Health outreach kit | invariant | Kit contains approved materials, forms, PPE, badges, chargers, water and incident tools. | field readiness |
| healthoutreach.supplies.sensitive_supply | Sensitive outreach supply control | invariant | Control tracks items needing custody, expiration, temperature, disposal or supervisor approval. | avoid misuse |
| healthoutreach.incident.field_incident | Health outreach field incident | invariant | Incident records staff safety issue, participant conflict, injury, exposure or property problem. | incident trail |
| healthoutreach.reporting.grant_report | Health outreach grant report | variant | Report summarizes activities, outputs, outcomes, demographics, barriers and spending. | funder accountability |
| healthoutreach.metrics.outreach_kpi | Community health outreach KPI | variant | KPI tracks contacts, referrals, closed-loop rate, events, barriers, reach equity and follow-up. | manage outreach |
| healthoutreach.continuity.public_health_alert | Outreach public health alert response | invariant | Response updates scripts, sites, partners, safety rules, referral paths and reporting cadence. | adapt quickly |
