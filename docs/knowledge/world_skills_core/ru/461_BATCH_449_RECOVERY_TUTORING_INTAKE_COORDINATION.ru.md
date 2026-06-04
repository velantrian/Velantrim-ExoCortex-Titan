# BATCH 449: Recovery Tutoring Intake Coordination

**KnowledgeUnits:** 44  
**Namespace:** `tutoringintakeops.*`  
**Scope:** student screening, subjects, schedule, tutor matching, safeguarding, attendance and outcomes.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| tutoringintakeops.intake.referral_source | referral source | RECORD | Source records school liaison, caregiver, shelter desk, caseworker, teacher, youth program or self-referral. | Shows entry path. |
| tutoringintakeops.intake.student_profile | student profile | RECORD | Profile captures grade, school, language, displacement status, caregiver, contact and access needs. | Defines support. |
| tutoringintakeops.intake.consent | caregiver consent | CONTROL | Consent confirms participation, communication channel, data sharing and pickup or online rules. | Protects students. |
| tutoringintakeops.intake.priority_score | priority score | MODEL | Score weighs missed school, exam deadline, reading/math gap, language barrier, disability need and instability. | Prioritizes support. |
| tutoringintakeops.screening.learning_need | learning need | RECORD | Need records subjects, assignments, grade standards, teacher notes and student goals. | Frames tutoring. |
| tutoringintakeops.screening.baseline_check | baseline check | PROCESS | Check uses short task, teacher input or assignment review to identify starting level. | Avoids guessing. |
| tutoringintakeops.screening.access_barrier | access barrier | RECORD | Barrier records transport, device, internet, quiet space, caregiver schedule or safety concern. | Plans logistics. |
| tutoringintakeops.screening.special_support | special support | RECORD | Support records IEP-style accommodations, assistive tech, sensory needs, language supports or referral need. | Improves fit. |
| tutoringintakeops.subject.subject_area | subject area | RECORD | Area separates reading, writing, math, science, language, homework, test prep or credit recovery. | Matches tutor. |
| tutoringintakeops.subject.goal_plan | goal plan | PROCESS | Plan sets short goals, assignments, materials, frequency and review date. | Makes sessions useful. |
| tutoringintakeops.subject.material_list | material list | RECORD | List captures textbooks, packets, online platform, calculator, notebook, login or printed tasks. | Prevents delays. |
| tutoringintakeops.tutor.application | tutor application | RECORD | Application records identity, skills, grades served, languages, availability, background check and restrictions. | Builds tutor pool. |
| tutoringintakeops.tutor.skill_profile | skill profile | RECORD | Profile maps subject skill, age comfort, special support training, online tools and language capacity. | Enables matching. |
| tutoringintakeops.tutor.background_check | background check | CONTROL | Check verifies required screening, references, safeguarding training and approval status. | Protects students. |
| tutoringintakeops.tutor.training_complete | training complete | CONTROL | Training covers boundaries, trauma awareness, mandated reporting, lesson notes and escalation. | Standardizes practice. |
| tutoringintakeops.match.match_criteria | match criteria | MODEL | Criteria weighs subject, grade, language, schedule, location, personality, safeguarding and access needs. | Improves fit. |
| tutoringintakeops.match.conflict_check | conflict check | CONTROL | Check flags prior conflict, household relationship, prohibited contact or role overlap. | Reduces risk. |
| tutoringintakeops.match.introduction_session | introduction session | PROCESS | Session introduces student, caregiver, tutor, goals, boundaries, schedule and reporting. | Starts clearly. |
| tutoringintakeops.match.rematch_trigger | rematch trigger | CONTROL | Trigger allows rematch for no-shows, poor fit, safety concern, subject mismatch or schedule change. | Keeps service viable. |
| tutoringintakeops.schedule.availability_grid | availability grid | RECORD | Grid captures student, caregiver, tutor, site, online window and blackout dates. | Enables scheduling. |
| tutoringintakeops.schedule.session_record | session record | RECORD | Record captures date, duration, site or platform, subject, attendance and next task. | Tracks activity. |
| tutoringintakeops.schedule.transport_plan | transport plan | PROCESS | Plan coordinates safe location, transit, caregiver pickup, shelter route or online alternative. | Supports attendance. |
| tutoringintakeops.schedule.no_show_process | no-show process | PROCESS | Process logs missed session, outreach, reschedule, safeguarding check and pattern review. | Prevents drift. |
| tutoringintakeops.safeguarding.site_rule | site rule | CONTROL | Rule defines approved locations, visibility, adult presence, online settings and prohibited one-to-one contexts. | Protects students. |
| tutoringintakeops.safeguarding.contact_rule | contact rule | CONTROL | Rule limits direct messaging, private accounts, late contact and unsupervised communication. | Maintains boundaries. |
| tutoringintakeops.safeguarding.incident_flag | incident flag | STATE | Flag marks distress, disclosure, harassment, injury, missing child, unsafe pickup or boundary breach. | Triggers escalation. |
| tutoringintakeops.safeguarding.report_route | report route | PROCESS | Route tells tutors how to report safeguarding, academic concern or access barrier. | Ensures response. |
| tutoringintakeops.attendance.attendance_log | attendance log | RECORD | Log records present, late, no-show, canceled, online issue and reason when known. | Measures participation. |
| tutoringintakeops.attendance.pattern_review | pattern review | PROCESS | Review checks repeated absences, transport problems, caregiver conflict or unsuitable schedule. | Fixes barriers. |
| tutoringintakeops.attendance.makeup_session | makeup session | PROCESS | Session reschedules missed support within tutor capacity and student deadline. | Maintains progress. |
| tutoringintakeops.records.case_file | case file | RECORD | File links intake, consent, screening, match, sessions, attendance, safeguarding and outcomes. | Supports audit. |
| tutoringintakeops.records.session_note | session note | RECORD | Note records topic, work completed, barriers, next step and referral need without excess personal detail. | Preserves continuity. |
| tutoringintakeops.records.exception_log | exception log | RECORD | Log captures no tutor, schedule gap, access issue, safety concern, tech failure or withdrawal. | Enables review. |
| tutoringintakeops.records.consent_note | consent note | RECORD | Note records caregiver permissions, school coordination limits, media restrictions and data sharing. | Documents boundaries. |
| tutoringintakeops.communication.caregiver_update | caregiver update | PROCESS | Update explains schedule, progress, materials, attendance, concerns and next steps. | Keeps support aligned. |
| tutoringintakeops.communication.school_update | school update | PROCESS | Update shares aggregate or consented progress with teacher or liaison. | Connects academics. |
| tutoringintakeops.communication.referral_handoff | referral handoff | PROCESS | Handoff routes counseling, special education, device access, meals, transport or enrollment issues. | Addresses wider needs. |
| tutoringintakeops.outcomes.goal_progress | goal progress | METRIC | Progress tracks completed assignments, reading level change, math skills, attendance or teacher feedback. | Shows impact. |
| tutoringintakeops.outcomes.student_feedback | student feedback | RECORD | Feedback captures confidence, usefulness, comfort, barriers and preferred support. | Improves fit. |
| tutoringintakeops.metrics.match_rate | match rate | METRIC | Rate compares screened students, available tutors, active matches and waitlist. | Shows capacity. |
| tutoringintakeops.metrics.retention_rate | retention rate | METRIC | Rate tracks students continuing after set sessions and reasons for exit. | Measures stability. |
| tutoringintakeops.metrics.subject_gap | subject gap metric | METRIC | Metric tracks unmet demand by subject, grade band, language and tutor availability. | Guides recruitment. |
| tutoringintakeops.closeout.closure_summary | closure summary | RECORD | Summary records goals met, remaining needs, referrals, feedback and re-entry option. | Ends support cleanly. |
| tutoringintakeops.closeout.after_action | after-action note | RECORD | Note captures tutor gaps, safeguarding issues, access barriers and outcome lessons. | Improves next cycle. |
