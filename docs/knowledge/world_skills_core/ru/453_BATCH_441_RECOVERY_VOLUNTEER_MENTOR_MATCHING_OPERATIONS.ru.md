# BATCH 441: Recovery Volunteer Mentor Matching Operations

**KnowledgeUnits:** 44  
**Namespace:** `mentormatchops.*`  
**Scope:** intake, goals, mentor skills, boundaries, scheduling, check-ins and outcomes.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| mentormatchops.intake.participant_source | participant source | RECORD | Source records caseworker, recovery center, workforce partner, school, nonprofit or self-referral. | Shows entry path. |
| mentormatchops.intake.participant_profile | participant profile | RECORD | Profile captures contact, language, recovery stage, access limits, preferred schedule and support needs. | Defines matching context. |
| mentormatchops.intake.consent | mentoring consent | CONTROL | Consent explains voluntary participation, communication channels, privacy limits and ending process. | Sets trust. |
| mentormatchops.intake.safeguarding_screen | safeguarding screen | CONTROL | Screen flags minors, vulnerable adults, trauma risk, conflict risk and mandatory reporting boundaries. | Protects participants. |
| mentormatchops.goals.goal_statement | goal statement | RECORD | Statement names the practical aim such as job search, documents, study, housing steps or routines. | Guides matching. |
| mentormatchops.goals.goal_scope | goal scope | CONTROL | Scope prevents mentors from acting as lawyers, clinicians, financial advisers or case managers. | Keeps role safe. |
| mentormatchops.goals.step_plan | step plan | PROCESS | Plan breaks goals into small tasks, deadlines, resources and check-in points. | Makes support concrete. |
| mentormatchops.goals.progress_marker | progress marker | METRIC | Marker tracks completed actions, barriers removed and next milestone. | Shows movement. |
| mentormatchops.mentor.application | mentor application | RECORD | Application captures identity, contact, skills, availability, languages, lived experience and restrictions. | Builds mentor pool. |
| mentormatchops.mentor.background_check | background check | CONTROL | Check records required screening, reference, credential or organization approval. | Reduces risk. |
| mentormatchops.mentor.skill_profile | skill profile | RECORD | Profile maps skills such as resume help, budgeting, school navigation, transport planning or digital access. | Supports fit. |
| mentormatchops.mentor.training_complete | training complete | CONTROL | Training covers boundaries, trauma-informed conduct, privacy, escalation and documentation. | Standardizes support. |
| mentormatchops.match.criteria | match criteria | MODEL | Criteria weighs goals, language, schedule, location, skill, lived experience, risk and preference. | Improves fit. |
| mentormatchops.match.conflict_check | conflict check | CONTROL | Check looks for personal conflicts, service conflicts, dependency risk or prior negative contact. | Avoids harm. |
| mentormatchops.match.introduction_plan | introduction plan | PROCESS | Plan sets first meeting channel, agenda, staff presence and confirmation messages. | Starts safely. |
| mentormatchops.match.rematch_trigger | rematch trigger | CONTROL | Trigger allows rematch for no-shows, boundary concerns, poor fit, changed goals or safety issue. | Keeps support viable. |
| mentormatchops.boundaries.role_boundary | role boundary | CONTROL | Boundary defines what mentors can discuss, document, promise and escalate. | Prevents overreach. |
| mentormatchops.boundaries.communication_rule | communication rule | CONTROL | Rule defines approved channels, hours, group messages, recording limits and emergency contact route. | Protects both sides. |
| mentormatchops.boundaries.gift_policy | gift policy | CONTROL | Policy restricts cash, loans, expensive gifts, personal favors and dependency-forming support. | Reduces exploitation. |
| mentormatchops.boundaries.transport_policy | transport policy | CONTROL | Policy states when rides, meeting locations or home visits are allowed or prohibited. | Manages safety. |
| mentormatchops.schedule.availability_grid | availability grid | RECORD | Grid captures mentor and participant windows, timezone, access needs and blackout dates. | Enables scheduling. |
| mentormatchops.schedule.session_plan | session plan | RECORD | Plan records date, channel, goal focus, materials needed and responsible staff. | Organizes support. |
| mentormatchops.schedule.no_show_process | no-show process | PROCESS | Process logs missed session, contact attempts, grace rules and reschedule path. | Prevents drift. |
| mentormatchops.schedule.cadence_review | cadence review | PROCESS | Review adjusts meeting frequency as goals stabilize, barriers rise or mentor capacity changes. | Keeps fit. |
| mentormatchops.checkin.first_checkin | first check-in | PROCESS | Staff check-in after initial contact asks about fit, comfort, boundaries and next steps. | Catches early issues. |
| mentormatchops.checkin.routine_checkin | routine check-in | PROCESS | Routine check-in reviews progress, barriers, safety, attendance and support quality. | Maintains oversight. |
| mentormatchops.checkin.escalation_flag | escalation flag | STATE | Flag marks distress, abuse concern, legal issue, medical crisis, housing danger or mentor misconduct. | Routes help. |
| mentormatchops.checkin.closure_readiness | closure readiness | MODEL | Readiness weighs goal completion, participant confidence, mentor availability and referral needs. | Plans ending. |
| mentormatchops.records.match_file | match file | RECORD | File links profiles, consent, criteria, sessions, check-ins, incidents, outcomes and closure. | Supports audit. |
| mentormatchops.records.session_note | session note | RECORD | Note records attendance, topic, action steps, referrals and boundary concerns without sensitive overdetail. | Preserves continuity. |
| mentormatchops.records.incident_log | incident log | RECORD | Log captures safety concern, complaint, breach, missed contacts, inappropriate request or escalation. | Enables oversight. |
| mentormatchops.records.data_minimization | data minimization | CONTROL | Minimization limits notes to operational need and avoids unnecessary trauma detail. | Protects dignity. |
| mentormatchops.communication.welcome_message | welcome message | PROCESS | Message explains match purpose, first session, boundaries, contact channel and staff support. | Reduces confusion. |
| mentormatchops.communication.resource_handoff | resource handoff | PROCESS | Handoff shares approved templates, referral lists, worksheets or digital tools aligned to goals. | Supports action. |
| mentormatchops.communication.pause_notice | pause notice | PROCESS | Notice explains temporary pause, staff contact and reactivation path when match cannot continue. | Maintains clarity. |
| mentormatchops.outcomes.goal_completed | goal completed | STATE | Completion records achieved task, participant confirmation, date and remaining needs. | Marks success. |
| mentormatchops.outcomes.referral_completed | referral completed | METRIC | Metric tracks successful connections to training, benefits, housing help, counseling or job services. | Measures value. |
| mentormatchops.outcomes.participant_feedback | participant feedback | RECORD | Feedback captures usefulness, respect, accessibility, cultural fit and improvement ideas. | Improves program. |
| mentormatchops.metrics.match_rate | match rate | METRIC | Rate compares eligible participants, active mentors, successful matches and waitlist. | Shows capacity. |
| mentormatchops.metrics.retention_rate | retention rate | METRIC | Retention tracks matches still active after set intervals and reasons for ending. | Measures stability. |
| mentormatchops.metrics.boundary_incidents | boundary incidents | METRIC | Metric counts boundary breaches, complaints, escalations and corrective actions. | Monitors safety. |
| mentormatchops.closeout.closure_session | closure session | PROCESS | Session reviews progress, final referrals, feedback, records and future re-entry option. | Ends respectfully. |
| mentormatchops.closeout.mentor_debrief | mentor debrief | PROCESS | Debrief captures mentor workload, barriers, training needs and safeguarding concerns. | Supports volunteers. |
| mentormatchops.closeout.after_action | after-action note | RECORD | Note summarizes matching bottlenecks, risks, outcomes and program improvements. | Improves next cycle. |
