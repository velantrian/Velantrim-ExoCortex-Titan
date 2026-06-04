# BATCH 364: Quarantine and Isolation Support Operations

**KnowledgeUnits:** 44  
**Namespace:** `qisupportops.*`  
**Scope:** eligibility, wellness checks, supplies, housing, employer/school notes and closure.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| qisupportops.intake.support_id | support ID | RECORD | Support ID links person, disease event, need, dates and assigned worker. | Tracks assistance. |
| qisupportops.intake.referral_source | referral source | RECORD | Source distinguishes investigator, clinic, shelter, hotline, employer or self-referral. | Shows entry path. |
| qisupportops.intake.need_summary | need summary | RECORD | Summary captures food, medicine, housing, income, caregiving, transport or communication need. | Guides support plan. |
| qisupportops.intake.urgency | urgency level | MODEL | Urgency reflects medical risk, lack of supplies, unsafe housing or dependent care. | Prioritizes service. |
| qisupportops.eligibility.order_status | order status | RECORD | Status records recommended, required, voluntary or completed isolation/quarantine. | Defines support window. |
| qisupportops.eligibility.residency | residency check | CONSTRAINT | Program may require jurisdiction, exposure link or case status. | Keeps service in scope. |
| qisupportops.eligibility.household | household assessment | METHOD | Household assessment checks ability to separate, share bathroom and protect vulnerable people. | Determines practical feasibility. |
| qisupportops.eligibility.duplicate_support | duplicate support check | QUALITY_CHECK | Check prevents overlapping aid from multiple programs unless allowed. | Controls resources. |
| qisupportops.plan.support_plan | support plan | RECORD | Plan lists needs, actions, providers, delivery dates and follow-up cadence. | Turns guidance into practical help. |
| qisupportops.plan.end_date | end date | RECORD | End date follows public health guidance, symptom status and test rules. | Clarifies when support changes. |
| qisupportops.plan.contingency | contingency plan | METHOD | Contingency covers worsening symptoms, housing loss, supply delay or caregiver failure. | Prevents crisis escalation. |
| qisupportops.plan.language | language preference | RECORD | Preferred language is used for instructions and wellness calls. | Improves comprehension. |
| qisupportops.wellness.check_call | wellness check | METHOD | Check asks about symptoms, needs, adherence barriers and safety. | Maintains contact. |
| qisupportops.wellness.medical_escalation | medical escalation | SAFETY_RULE | Severe symptoms trigger medical advice line, clinic or emergency response. | Protects health. |
| qisupportops.wellness.missed_contact | missed contact | FAILURE_MODE | Missed contact triggers retry, alternate contact or field/partner check by risk. | Avoids silent deterioration. |
| qisupportops.wellness.behavioral | behavioral support | METHOD | Isolation distress can route to crisis line or mental health support. | Reduces harm. |
| qisupportops.supplies.food | food support | METHOD | Food support arranges delivery, pantry referral, vouchers or prepared meals. | Makes isolation possible. |
| qisupportops.supplies.medicine | medicine access | METHOD | Medicine support coordinates pharmacy delivery or refill assistance without dosing advice. | Maintains treatment continuity. |
| qisupportops.supplies.hygiene | hygiene kit | RECORD | Hygiene kit may include masks, sanitizer, cleaning supplies and thermometers. | Supports infection control. |
| qisupportops.supplies.delivery | contactless delivery | SAFETY_RULE | Delivery protects staff, privacy and infection control. | Reduces exposure. |
| qisupportops.housing.safe_room | safe room assessment | METHOD | Assessment checks separate room, ventilation, bathroom and household risks. | Determines home feasibility. |
| qisupportops.housing.alternate_site | alternate housing | METHOD | Hotel, shelter isolation unit or medical respite may be arranged when home is unsafe. | Protects household and community. |
| qisupportops.housing.site_rules | site rules | CONSTRAINT | Alternate site has rules for visitors, meals, monitoring, transport and exit. | Maintains safety. |
| qisupportops.housing.discharge | housing discharge | METHOD | Discharge aligns with end date, transport and destination plan. | Prevents abandonment. |
| qisupportops.income.work_note | work note | METHOD | Work note confirms restriction dates without unnecessary diagnosis detail. | Helps employment compliance. |
| qisupportops.income.school_note | school note | METHOD | School note supports absence, remote learning or return date. | Reduces penalty. |
| qisupportops.income.benefit_referral | benefit referral | METHOD | Referral connects to paid leave, unemployment, food, rent or utility aid. | Reduces economic barrier. |
| qisupportops.income.employer_contact | employer contact | CONSTRAINT | Employer contact occurs only with consent or legal authority. | Protects privacy. |
| qisupportops.caregiving.dependent_plan | dependent care plan | METHOD | Plan addresses children, elders, animals or disabled dependents. | Makes isolation realistic. |
| qisupportops.caregiving.caregiver_ppe | caregiver precautions | SAFETY_RULE | Caregiver guidance covers PPE, hygiene, distance and symptom monitoring. | Reduces household spread. |
| qisupportops.caregiving.backup | backup caregiver | METHOD | Backup caregiver is identified when primary caregiver becomes ill or unavailable. | Protects dependents. |
| qisupportops.communication.daily_script | daily script | METHOD | Script provides clear guidance, rights, responsibilities and support options. | Keeps messaging consistent. |
| qisupportops.communication.end_notice | end notice | METHOD | End notice explains end date, return precautions and ongoing symptoms guidance. | Closes uncertainty. |
| qisupportops.communication.conflict | nonadherence conflict | METHOD | Nonadherence is addressed with barrier-solving before enforcement escalation. | Improves cooperation. |
| qisupportops.records.case_note | case note | RECORD | Note records needs, contacts, deliveries, guidance and escalations. | Supports continuity. |
| qisupportops.records.privacy | privacy rule | SAFETY_RULE | Health and support records are restricted by role and need. | Protects sensitive data. |
| qisupportops.records.retention | retention rule | CONSTRAINT | Records follow public health, grant and privacy retention rules. | Controls lifecycle. |
| qisupportops.logistics.vendor | vendor coordination | METHOD | Vendors or nonprofits deliver food, housing or transport under agreement. | Extends capacity. |
| qisupportops.logistics.inventory | support inventory | MEASUREMENT | Inventory tracks kits, supplies, vouchers and delivery capacity. | Prevents shortages. |
| qisupportops.metrics.completion | completion rate | MEASUREMENT | Completion rate tracks support cases closed with end guidance delivered. | Shows follow-through. |
| qisupportops.metrics.unmet_need | unmet need | MEASUREMENT | Unmet need records unavailable housing, supplies, income support or language access. | Guides resource gaps. |
| qisupportops.qa.case_review | case review | QUALITY_CHECK | Sample reviews check eligibility, privacy, timeliness and support accuracy. | Improves program quality. |
| qisupportops.closeout.closure_reason | closure reason | RECORD | Closure states completed, transferred, unreachable, declined, ineligible or deceased. | Makes outcome explicit. |
| qisupportops.review.lessons | lessons learned | METHOD | Program review captures barriers, partner gaps and equity issues. | Improves future support. |
