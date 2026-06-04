# BATCH 363: Public Health Disease Investigation Operations

**KnowledgeUnits:** 44  
**Namespace:** `diseaseinvestops.*`  
**Scope:** case intake, interviews, exposure tracing, lab coordination, isolation guidance and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| diseaseinvestops.intake.case_id | case ID | RECORD | Case ID links person, disease, report source, dates, jurisdiction and investigator. | Creates traceable investigation. |
| diseaseinvestops.intake.report_source | report source | RECORD | Source distinguishes lab, clinician, school, employer, shelter, hospital or self-report. | Shows where detection began. |
| diseaseinvestops.intake.reportable_check | reportable condition check | CONSTRAINT | Staff confirm whether condition meets reportable criteria and timeframe. | Prioritizes legally required work. |
| diseaseinvestops.intake.priority | priority level | MODEL | Priority uses severity, transmissibility, setting, vulnerability and outbreak signal. | Allocates investigator time. |
| diseaseinvestops.identity.person_match | person match | METHOD | Person match uses demographics, contact, medical record and address. | Prevents duplicate case files. |
| diseaseinvestops.identity.duplicate_case | duplicate case | FAILURE_MODE | Duplicate case occurs when multiple reports describe the same person/event. | Requires merge control. |
| diseaseinvestops.identity.jurisdiction | jurisdiction assignment | CONSTRAINT | Jurisdiction depends on residence, diagnosis site, exposure site or event setting. | Sends work to correct agency. |
| diseaseinvestops.identity.privacy | privacy boundary | SAFETY_RULE | Identifiable health data is shared only by role and legal authority. | Protects sensitive records. |
| diseaseinvestops.interview.script | interview script | METHOD | Script gathers symptoms, onset, contacts, locations, occupation and risk setting. | Makes interviews consistent. |
| diseaseinvestops.interview.consent | interview consent | METHOD | Investigator explains purpose, privacy limits and voluntary elements where applicable. | Builds cooperation. |
| diseaseinvestops.interview.language | language access | METHOD | Interpreter or translated material supports non-dominant language speakers. | Improves data quality. |
| diseaseinvestops.interview.unreachable | unreachable case | FAILURE_MODE | Unreachable status records attempts, channels and next escalation. | Prevents silent loss. |
| diseaseinvestops.symptom.onset | onset date | RECORD | Onset date anchors infectious period, exposure window and monitoring. | Drives tracing logic. |
| diseaseinvestops.symptom.severity | severity marker | RECORD | Severity records hospitalization, ICU, death, complications or recovery. | Supports surveillance. |
| diseaseinvestops.symptom.risk_factor | risk factor | RECORD | Risk factors include age, pregnancy, immune status, occupation or congregate setting. | Guides public health action. |
| diseaseinvestops.symptom.recovery | recovery status | METHOD | Recovery status follows defined clinical or public health criteria. | Supports closure decisions. |
| diseaseinvestops.lab.specimen | specimen record | RECORD | Specimen record stores type, collection date, accession, test and lab. | Links evidence to case. |
| diseaseinvestops.lab.result | lab result | RECORD | Result includes positive, negative, inconclusive, pending or variant/subtype where relevant. | Supports classification. |
| diseaseinvestops.lab.turnaround | turnaround time | MEASUREMENT | Turnaround tracks collection-to-result and report-to-action time. | Shows system speed. |
| diseaseinvestops.lab.retest | retest route | METHOD | Retesting is requested when result conflicts with symptoms or public health need. | Improves confidence. |
| diseaseinvestops.exposure.window | exposure window | MODEL | Exposure window is calculated from incubation period and onset/test date. | Narrows source search. |
| diseaseinvestops.exposure.setting | exposure setting | RECORD | Setting records household, workplace, school, food, travel, healthcare or event. | Identifies risk clusters. |
| diseaseinvestops.exposure.contact_list | contact list | RECORD | Contact list records people or groups potentially exposed. | Starts notification workflow. |
| diseaseinvestops.exposure.common_source | common source hypothesis | MODEL | Common source hypothesis links multiple cases to place, food, event or product. | Supports outbreak detection. |
| diseaseinvestops.tracing.contact_notify | contact notification | METHOD | Contacts are notified with exposure, guidance and privacy-safe information. | Reduces spread. |
| diseaseinvestops.tracing.monitoring | monitoring plan | METHOD | Monitoring tracks symptoms, test needs, work/school restrictions and end date. | Keeps exposed people visible. |
| diseaseinvestops.tracing.high_risk | high-risk contact | MODEL | High-risk contact has close, prolonged or vulnerable-setting exposure. | Prioritizes action. |
| diseaseinvestops.tracing.refusal | refusal handling | METHOD | Refusal is documented and managed with education, escalation or legal review. | Preserves due process. |
| diseaseinvestops.guidance.isolation | isolation guidance | SAFETY_RULE | Isolation guidance gives duration, precautions, emergency signs and support route. | Limits transmission. |
| diseaseinvestops.guidance.work_school | work or school note | METHOD | Notes communicate restriction dates without unnecessary health details. | Supports compliance. |
| diseaseinvestops.guidance.household | household guidance | METHOD | Household guidance covers separation, hygiene, masks, cleaning and vulnerable members. | Protects close contacts. |
| diseaseinvestops.guidance.support | support referral | METHOD | Cases needing food, medicine, housing or income help are referred. | Makes isolation feasible. |
| diseaseinvestops.outbreak.cluster_flag | cluster flag | MODEL | Cluster flag triggers when cases share time, place, strain or exposure. | Detects outbreaks early. |
| diseaseinvestops.outbreak.line_list | line list | RECORD | Line list summarizes cases, exposures, dates, labs and outcomes. | Supports outbreak management. |
| diseaseinvestops.outbreak.control_measure | control measure | METHOD | Control measures may include cleaning, exclusion, testing, vaccination or public notice. | Reduces onward spread. |
| diseaseinvestops.outbreak.partner_coord | partner coordination | METHOD | Partners include schools, employers, healthcare, labs and regulators. | Aligns actions. |
| diseaseinvestops.reporting.state_report | state report | METHOD | Required reports are sent to state or national surveillance systems. | Meets legal reporting. |
| diseaseinvestops.reporting.dashboard | dashboard update | MEASUREMENT | Dashboards aggregate counts, rates, settings and outcomes. | Guides response planning. |
| diseaseinvestops.reporting.data_quality | data quality check | QUALITY_CHECK | Fields are checked for missing onset, lab, setting, outcome and duplicates. | Improves surveillance. |
| diseaseinvestops.records.case_note | case note | RECORD | Notes record actions, calls, guidance, referrals and rationale. | Supports continuity. |
| diseaseinvestops.records.retention | retention rule | CONSTRAINT | Records follow public health, privacy and legal retention schedules. | Controls lifecycle. |
| diseaseinvestops.qa.supervisor_review | supervisor review | QUALITY_CHECK | High-risk, outbreak and complex cases receive supervisor review. | Improves consistency. |
| diseaseinvestops.closeout.case_closure | case closure | METHOD | Closure occurs after investigation, guidance, reporting and outcome fields complete. | Ends work cleanly. |
| diseaseinvestops.review.after_action | after-action review | METHOD | Review captures timeliness, data gaps, partner issues and control impact. | Improves future investigations. |
