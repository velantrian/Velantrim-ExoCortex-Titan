# BATCH 429: Recovery Job Placement Intake Operations

**KnowledgeUnits:** 44  
**Namespace:** `jobplacementops.*`  
**Scope:** skills, documents, transport, childcare, employer referrals, follow-up and outcomes.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| jobplacementops.intake.request_source | request source | RECORD | Source records workforce center, shelter, benefits desk, employer, school or outreach. | Shows entry path. |
| jobplacementops.intake.applicant_profile | applicant profile | RECORD | Profile captures contact, work status, language, location and safe-contact limits. | Defines participant. |
| jobplacementops.intake.disaster_impact | disaster impact | RECORD | Impact records job loss, reduced hours, relocation, business closure or caregiving disruption. | Explains need. |
| jobplacementops.intake.urgency | urgency model | MODEL | Urgency weighs income gap, housing risk, family needs, deadline and available openings. | Prioritizes help. |
| jobplacementops.skills.skill_inventory | skill inventory | RECORD | Inventory captures occupations, certifications, tools, languages, software and soft skills. | Matches jobs. |
| jobplacementops.skills.transferable | transferable skills | METHOD | Staff map prior experience to adjacent roles and recovery jobs. | Expands options. |
| jobplacementops.skills.training_need | training need | RECORD | Need records license renewal, safety card, digital skill or short course. | Starts training referral. |
| jobplacementops.skills.work_preferences | work preferences | RECORD | Preferences capture schedule, location, wage, physical limits and remote options. | Improves fit. |
| jobplacementops.documents.resume | resume support | METHOD | Staff help update resume, work history and disaster employment gap. | Improves applications. |
| jobplacementops.documents.id_work_auth | work document check | QUALITY_CHECK | Check identifies ID, authorization, certifications and missing documents. | Avoids hiring delay. |
| jobplacementops.documents.reference | reference list | RECORD | References record contacts, role, permission and availability. | Supports applications. |
| jobplacementops.documents.missing_doc | missing document | RECORD | Missing document logs source, replacement path, owner and deadline. | Drives completion. |
| jobplacementops.barriers.transport | transport barrier | RECORD | Barrier captures commute, vehicle loss, fuel, transit, accessible ride or route gap. | Routes support. |
| jobplacementops.barriers.childcare | childcare barrier | RECORD | Barrier captures hours, age, provider need, school schedule and voucher referral. | Enables work. |
| jobplacementops.barriers.equipment | equipment barrier | RECORD | Barrier records clothing, tools, phone, internet, laptop or PPE needs. | Supports readiness. |
| jobplacementops.barriers.health | health limitation | RECORD | Limitation records safe work constraints and referral needs without medical overcollection. | Protects applicant. |
| jobplacementops.employer.employer_roster | employer roster | RECORD | Roster lists hiring employers, roles, wages, location, schedule and requirements. | Builds openings. |
| jobplacementops.employer.job_order | job order | RECORD | Job order captures duties, pay, hours, start date, screening and contact. | Defines referral. |
| jobplacementops.employer.recovery_job | recovery job tag | RECORD | Recovery jobs are tagged for cleanup, logistics, caregiving, construction or public service. | Matches disaster context. |
| jobplacementops.employer.quality_check | employer quality check | QUALITY_CHECK | Check screens legitimacy, wage, safety, discrimination risk and contact accuracy. | Protects applicants. |
| jobplacementops.matching.match_score | match score | MODEL | Score compares skills, documents, barriers, preferences and employer requirements. | Prioritizes referrals. |
| jobplacementops.matching.referral | employer referral | RECORD | Referral records applicant, job, employer, date, documents sent and next step. | Creates trail. |
| jobplacementops.matching.warm_handoff | warm handoff | METHOD | Staff confirm employer contact, interview time and applicant readiness. | Reduces drop-off. |
| jobplacementops.matching.not_fit | not-fit reason | RECORD | Reason captures skill gap, schedule, transport, wage, documentation or preference. | Improves matching. |
| jobplacementops.support.transport_referral | transport referral | METHOD | Transport support connects applicant to voucher, route planning or ride program. | Enables interview/work. |
| jobplacementops.support.childcare_referral | childcare referral | METHOD | Childcare support connects applicant to provider, subsidy or emergency care path. | Enables attendance. |
| jobplacementops.support.clothing_referral | clothing referral | METHOD | Clothing support covers interview clothes, work boots, uniforms or PPE. | Improves readiness. |
| jobplacementops.support.digital_access | digital access | METHOD | Digital support covers email, applications, scans, phone and internet access. | Completes applications. |
| jobplacementops.followup.interview_check | interview check | METHOD | Follow-up confirms interview attended, outcome, barriers and next steps. | Maintains momentum. |
| jobplacementops.followup.placement_status | placement status | RECORD | Status records hired, pending, rejected, no-show, withdrew or training referral. | Tracks outcome. |
| jobplacementops.followup.retention_check | retention check | METHOD | Staff check after start for schedule, transport, childcare and workplace issues. | Supports retention. |
| jobplacementops.followup.reopen | reopen rule | METHOD | Case reopens for job loss, failed match, new documents or changed barrier. | Handles change. |
| jobplacementops.privacy.minimum_data | minimum data | SAFETY_RULE | Intake stores only job placement, eligibility and follow-up data needed. | Reduces exposure. |
| jobplacementops.privacy.consent_share | consent to share | RECORD | Consent records what can be shared with employers and partners. | Protects applicant. |
| jobplacementops.communication.applicant_update | applicant update | METHOD | Update explains referrals, documents, barriers, deadlines and employer responses. | Reduces uncertainty. |
| jobplacementops.communication.partner_update | partner update | METHOD | Partners receive aggregate skill needs, barriers, openings and placement outcomes. | Coordinates workforce. |
| jobplacementops.records.case_log | case log | RECORD | Log stores intake, skills, barriers, referrals, follow-ups and outcomes. | Creates continuity. |
| jobplacementops.records.retention | retention rule | CONSTRAINT | Workforce, privacy, grant and employer referral records follow schedules. | Preserves audit. |
| jobplacementops.metrics.applicants_served | applicants served | MEASUREMENT | Count tracks applicants by status, sector interest and barrier type. | Shows demand. |
| jobplacementops.metrics.referral_rate | referral rate | MEASUREMENT | Rate tracks applicants referred to employers or training. | Shows output. |
| jobplacementops.metrics.placement_rate | placement rate | MEASUREMENT | Rate tracks confirmed hires among active applicants. | Measures outcome. |
| jobplacementops.qa.case_review | case review | QUALITY_CHECK | Review checks skills, consent, referrals, barriers and follow-up completeness. | Improves reliability. |
| jobplacementops.demob.transfer | transfer plan | METHOD | Ongoing cases transfer to workforce center or partner agency. | Maintains support. |
| jobplacementops.review.after_action | after-action review | METHOD | Review captures skill gaps, employer quality, transport, childcare and retention lessons. | Improves future placement. |
