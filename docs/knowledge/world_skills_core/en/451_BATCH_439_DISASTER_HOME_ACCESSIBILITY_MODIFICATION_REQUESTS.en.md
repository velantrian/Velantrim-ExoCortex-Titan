# BATCH 439: Disaster Home Accessibility Modification Requests

**KnowledgeUnits:** 44  
**Namespace:** `accessmodops.*`  
**Scope:** intake, ramps, grab bars, contractor referral, funding, safety and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| accessmodops.intake.request_source | request source | RECORD | Source records caseworker, survivor center, disability advocate, clinic, shelter desk or self-referral. | Shows entry path. |
| accessmodops.intake.household_profile | household profile | RECORD | Profile captures residents, disability needs, caregiver support, language, contact limits and return timeline. | Defines support. |
| accessmodops.intake.barrier_description | barrier description | RECORD | Description notes stairs, narrow door, bathroom hazard, missing rail, threshold, path surface or entry slope. | Frames modification. |
| accessmodops.intake.damage_context | damage context | RECORD | Context separates preexisting barrier, disaster damage, temporary displacement and repair access issue. | Clarifies eligibility. |
| accessmodops.eligibility.disaster_link | disaster link | CONTROL | Link verifies the modification is needed for safe disaster recovery, return home or temporary occupancy. | Targets assistance. |
| accessmodops.eligibility.ownership_status | ownership status | RECORD | Status records owner, renter, landlord contact, public housing, temporary unit or shared property. | Guides permissions. |
| accessmodops.eligibility.permission_check | permission check | CONTROL | Check confirms landlord, owner, HOA or public agency approval before physical work. | Prevents disputes. |
| accessmodops.assessment.site_visit | site visit | PROCESS | Visit observes entry, bathroom, bedroom access, route surfaces, lighting, drainage and immediate hazards. | Grounds scope. |
| accessmodops.assessment.photo_record | photo record | RECORD | Photo record captures barriers, measurements, damage and completed work with privacy controls. | Supports decisions. |
| accessmodops.assessment.measurement_set | measurement set | RECORD | Measurements include rise, run, doorway width, threshold height, wall backing and fixture location. | Enables design. |
| accessmodops.assessment.priority_score | priority score | MODEL | Score weighs mobility dependence, fall risk, caregiver absence, medical access and return-home deadline. | Orders cases. |
| accessmodops.ramp.temporary_ramp | temporary ramp | MODEL | Temporary ramp identifies modular, portable or threshold ramp options for short-term access. | Speeds return. |
| accessmodops.ramp.slope_check | slope check | CONTROL | Check reviews ramp slope, landing, handrail, surface, drainage and load rating. | Reduces fall risk. |
| accessmodops.ramp.path_clearance | path clearance | PROCESS | Clearance removes debris, mud, cords, loose boards and blocked approach routes. | Makes ramp usable. |
| accessmodops.grabbar.location_plan | grab bar location plan | RECORD | Plan identifies shower, toilet, hallway or entry points based on user transfer pattern. | Improves safety. |
| accessmodops.grabbar.wall_support | wall support check | CONTROL | Check verifies studs, backing, anchors and surface condition before installation. | Prevents failure. |
| accessmodops.grabbar.install_record | install record | RECORD | Record captures bar type, location, installer, date, fasteners and user confirmation. | Supports accountability. |
| accessmodops.bathroom.transfer_path | transfer path | MODEL | Path maps toilet, tub, shower, sink and mobility-device movement constraints. | Finds practical fixes. |
| accessmodops.bathroom.non_slip_control | non-slip control | CONTROL | Control adds mats, strips, drainage attention or temporary surface treatment when appropriate. | Reduces slips. |
| accessmodops.entry.threshold_solution | threshold solution | MODEL | Solution covers beveled threshold, mini-ramp, door adjustment or temporary plate. | Solves common barrier. |
| accessmodops.entry.door_clearance | door clearance | CONTROL | Clearance checks swing, width, hardware reach, storm door conflict and latch height. | Ensures access. |
| accessmodops.contractor.roster | contractor roster | RECORD | Roster lists vetted contractors, volunteer rebuild teams, accessibility specialists and availability. | Enables referral. |
| accessmodops.contractor.scope_packet | scope packet | RECORD | Packet includes measurements, photos, permissions, priority, safety constraints and funding rules. | Reduces rework. |
| accessmodops.contractor.license_check | license check | CONTROL | Check reviews license, insurance, background requirements and program eligibility. | Reduces fraud risk. |
| accessmodops.contractor.site_safety | site safety briefing | PROCESS | Briefing covers utilities, mold, unstable surfaces, pets, residents and stop-work triggers. | Protects crews. |
| accessmodops.funding.funding_source | funding source | RECORD | Source records grant, donation, insurance gap, public benefit, volunteer labor or client contribution. | Tracks resources. |
| accessmodops.funding.cost_cap | cost cap | CONTROL | Cap limits materials, labor, travel, permits and change orders by program rule. | Protects budget. |
| accessmodops.funding.quote_review | quote review | PROCESS | Review compares scope, unit cost, urgency, accessibility impact and available alternatives. | Supports approval. |
| accessmodops.funding.payment_proof | payment proof | RECORD | Proof links invoice, approval, completion photo, client acceptance and exception notes. | Supports audit. |
| accessmodops.safety.stop_work | stop-work trigger | CONTROL | Trigger pauses work for structural danger, electrical exposure, mold, violence, missing permission or unsafe weather. | Prevents harm. |
| accessmodops.safety.user_trial | user trial | PROCESS | Trial lets the resident or caregiver test the modification under supervision when feasible. | Confirms usability. |
| accessmodops.safety.code_boundary | code boundary | CONTROL | Boundary flags when work needs permit, licensed professional or formal inspection. | Avoids unsafe shortcuts. |
| accessmodops.records.case_file | case file | RECORD | File links intake, eligibility, assessment, permissions, scope, funding, work proof and closeout. | Creates traceability. |
| accessmodops.records.status_board | status board | RECORD | Board tracks requested, assessed, permission pending, funded, assigned, installed, inspected and closed. | Shows pipeline. |
| accessmodops.records.exception_log | exception log | RECORD | Log captures denied permission, unsafe site, no access, cost overrun, missed appointment or failed work. | Enables follow-up. |
| accessmodops.communication.client_update | client update | PROCESS | Update explains status, needed documents, appointment window, safety limits and expected next step. | Reduces uncertainty. |
| accessmodops.communication.landlord_notice | landlord notice | PROCESS | Notice requests approval, explains temporary or permanent work and records response. | Clears permission. |
| accessmodops.communication.referral_handoff | referral handoff | PROCESS | Handoff sends cases beyond program capacity to housing repair, disability services or legal aid. | Keeps support moving. |
| accessmodops.metrics.time_to_assessment | time to assessment | METRIC | Metric measures request date to completed site assessment. | Shows access speed. |
| accessmodops.metrics.install_completion | install completion | METRIC | Completion tracks approved modifications installed and accepted by residents. | Measures outcome. |
| accessmodops.metrics.denial_reason_mix | denial reason mix | METRIC | Mix groups permission denial, funding gap, unsafe structure, ineligible request and no contact. | Reveals bottlenecks. |
| accessmodops.closeout.acceptance_note | acceptance note | RECORD | Note records user confirmation, remaining limits, maintenance instructions and referral needs. | Closes case. |
| accessmodops.closeout.followup_check | follow-up check | PROCESS | Check verifies continued usability, safety concerns, repair needs and changed household status. | Catches failures. |
| accessmodops.closeout.after_action | after-action note | RECORD | Note captures contractor performance, funding gaps, common barriers and process improvements. | Improves next cycle. |
