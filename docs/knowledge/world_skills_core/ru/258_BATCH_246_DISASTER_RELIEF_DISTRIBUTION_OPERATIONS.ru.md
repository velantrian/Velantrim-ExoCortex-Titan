# BATCH_246 — Disaster Relief Distribution Operations Detail
# world_skills_core · source: world_skills_core:batch_246:disaster_relief_distribution_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| reliefops.intake.survivor_intake | Disaster relief survivor intake | invariant | Intake records household, disaster impact, location, immediate needs and contact. | start assistance |
| reliefops.intake.identity_check | Relief identity check | invariant | Check verifies identity enough for program rules while preserving emergency access. | reduce misuse |
| reliefops.intake.household_profile | Relief household profile | variant | Profile captures household size, age groups, disability, language, pets and transportation needs. | tailor support |
| reliefops.intake.duplicate_screen | Relief duplicate screen | invariant | Screen checks prior assistance, household overlap, address duplication and referral history. | fair distribution |
| reliefops.intake.privacy_notice | Relief privacy notice | invariant | Notice explains data use, sharing, retention, voluntary fields and consent. | informed service |
| reliefops.eligibility.damage_category | Disaster relief damage category | variant | Category records destroyed, major, minor, affected, displaced or utility outage status. | prioritize aid |
| reliefops.eligibility.program_rule | Relief program eligibility rule | invariant | Rule defines who qualifies, documentation, geography, date, need and assistance limit. | consistent decisions |
| reliefops.eligibility.vulnerability_priority | Relief vulnerability priority | variant | Priority considers age, disability, medical dependence, pregnancy, income or access barrier. | equitable triage |
| reliefops.eligibility.exception_review | Relief eligibility exception review | variant | Review handles missing documents, informal housing, displacement or special hardship. | avoid unfair exclusion |
| reliefops.inventory.donation_receiving | Disaster relief donation receiving | invariant | Receiving records item, donor, quantity, condition, restrictions and storage need. | supply input |
| reliefops.inventory.item_category | Relief inventory item category | invariant | Category separates water, food, hygiene, cleanup, bedding, baby, medical support or tools. | organized stock |
| reliefops.inventory.expiration_check | Relief supply expiration check | invariant | Check flags expired food, medicine, formula, batteries or perishable goods. | safe distribution |
| reliefops.inventory.kit_build | Relief kit build | variant | Build assembles standard household, hygiene, cleanup or shelter kits with count control. | fast handout |
| reliefops.inventory.stock_count | Relief inventory stock count | invariant | Count tracks on-hand, committed, distributed, damaged, expired and inbound quantities. | supply visibility |
| reliefops.inventory.reorder_trigger | Relief reorder trigger | variant | Trigger flags low stock, surge demand, route need or special population shortage. | maintain supply |
| reliefops.site.site_selection | Relief distribution site selection | invariant | Selection checks access, safety, parking, utilities, shelter, visibility and community reach. | usable site |
| reliefops.site.site_layout | Relief distribution site layout | invariant | Layout defines intake, queue, eligibility, pickup, loading, exits and private support area. | safe flow |
| reliefops.site.queue_management | Relief queue management | invariant | Management handles arrival order, priority needs, shade, water, updates and crowd calming. | humane waiting |
| reliefops.site.accessibility_support | Relief site accessibility support | invariant | Support provides ramps, seating, interpreters, mobility help and alternate pickup. | inclusive aid |
| reliefops.site.traffic_control | Relief distribution traffic control | variant | Control separates vehicles, pedestrians, trucks, emergency access and staging. | prevent conflict |
| reliefops.distribution.voucher_issue | Relief voucher issue | variant | Issue records approved household, item or service, value, vendor and expiration. | controlled assistance |
| reliefops.distribution.direct_handout | Relief direct handout | invariant | Handout records household, items, quantities, staff, date and any exceptions. | accountable aid |
| reliefops.distribution.bulk_agency_order | Relief agency bulk order | variant | Order sends supplies to partner shelter, clinic, pantry or community site. | extend reach |
| reliefops.distribution.delivery_route | Relief delivery route | variant | Route serves homebound, isolated, shelter, rural or blocked-access households. | reach people |
| reliefops.distribution.proof_distribution | Proof of relief distribution | invariant | Proof records signature, scan, photo, witness or staff attestation as allowed. | audit trail |
| reliefops.referral.referral_screen | Disaster relief referral screen | invariant | Screen identifies needs for shelter, medical, benefits, legal, mental health or rebuilding help. | connect services |
| reliefops.referral.partner_directory | Relief partner directory | invariant | Directory lists agencies, services, eligibility, capacity, hours and contact. | navigation |
| reliefops.referral.warm_referral | Relief warm referral | variant | Referral connects survivor directly to partner with consent and essential details. | reduce drop-off |
| reliefops.referral.unmet_need | Disaster unmet need record | invariant | Record captures aid gap, urgency, household, barrier and escalation path. | target resources |
| reliefops.safety.site_safety_briefing | Relief site safety briefing | invariant | Briefing covers hazards, weather, conflict, traffic, lifting, PPE and emergency roles. | protect team |
| reliefops.safety.heat_cold_control | Relief heat or cold control | variant | Control provides shade, warming, water, breaks, monitoring and vulnerable-person support. | reduce harm |
| reliefops.safety.conflict_deescalation | Relief conflict de-escalation | invariant | De-escalation uses calm communication, boundaries, supervisor support and security referral. | safer site |
| reliefops.safety.incident_report | Relief distribution incident report | invariant | Report records injury, conflict, lost child, theft, vehicle issue, exposure or near miss. | incident trail |
| reliefops.safety.supply_security | Relief supply security | invariant | Security controls warehouse, site, truck, high-demand items, keys and after-hours storage. | prevent loss |
| reliefops.reporting.situation_report | Relief distribution situation report | invariant | Report summarizes demand, distributed items, stock, staffing, incidents and gaps. | command awareness |
| reliefops.reporting.demographic_summary | Relief demographic summary | variant | Summary aggregates non-identifying household needs, language, geography and vulnerability. | equity monitoring |
| reliefops.reporting.donor_report | Disaster relief donor report | variant | Report documents received goods, distribution outcomes, restrictions and remaining stock. | donor accountability |
| reliefops.reporting.after_action | Relief after-action note | variant | Note captures lessons, bottlenecks, partner issues, unmet needs and improvements. | learn |
| reliefops.volunteer.volunteer_checkin | Relief volunteer check-in | invariant | Check-in records identity, role, shift, training, waiver and supervisor. | manage volunteers |
| reliefops.volunteer.role_assignment | Relief volunteer role assignment | variant | Assignment places volunteers in intake, packing, loading, translation, traffic or cleanup. | useful staffing |
| reliefops.volunteer.shift_closeout | Relief volunteer shift closeout | invariant | Closeout records hours, issues, supplies, handoff and release time. | continuity |
| reliefops.finance.expense_tracking | Relief distribution expense tracking | variant | Tracking records purchase, transport, rental, staffing, reimbursement code and documentation. | financial control |
| reliefops.metrics.relief_distribution_kpi | Disaster relief distribution KPI | variant | KPI tracks households served, wait time, stockouts, referrals, incidents, equity reach and cost. | manage relief |
| reliefops.continuity.site_relocation | Relief site relocation response | invariant | Response moves distribution due to hazard, crowding, access loss or operational failure. | keep aid flowing |
