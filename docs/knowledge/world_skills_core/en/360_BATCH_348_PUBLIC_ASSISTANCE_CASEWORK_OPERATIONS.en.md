# BATCH 348: Public Assistance Casework Operations

**KnowledgeUnits:** 44  
**Namespace:** `assistcaseops.*`  
**Scope:** applications, eligibility, documents, interviews, notices, renewals, appeals and fraud controls.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| assistcaseops.intake.application_id | application ID | RECORD | Application ID links applicant, program, date, channel and caseworker. | Creates traceable casework. |
| assistcaseops.intake.program_type | program type | RECORD | Program type distinguishes cash, food, housing, childcare, energy, medical or emergency aid. | Different eligibility rules apply. |
| assistcaseops.intake.channel | intake channel | RECORD | Channel records online, phone, mail, in-person, partner or outreach intake. | Supports access and workload planning. |
| assistcaseops.intake.screening | initial screening | METHOD | Initial screening checks basic residency, household, income and urgent need. | Identifies likely path quickly. |
| assistcaseops.intake.priority | priority handling | MODEL | Priority considers homelessness, hunger, utility shutoff, disability, children or safety risk. | Speeds urgent cases. |
| assistcaseops.identity.identity_proof | identity proof | SAFETY_RULE | Identity proof verifies applicant before benefits or private data release. | Prevents improper access. |
| assistcaseops.identity.household | household composition | RECORD | Household composition records members, relationships and shared expenses. | Determines eligibility and benefit size. |
| assistcaseops.identity.authorized_rep | authorized representative | CONSTRAINT | Representative authority must be documented and limited by program rule. | Protects applicants. |
| assistcaseops.documents.document_list | document checklist | METHOD | Checklist requests only documents needed for eligibility or verification. | Reduces applicant burden. |
| assistcaseops.documents.income | income verification | RECORD | Income verification may include wages, benefits, self-employment or zero-income statement. | Supports fair eligibility decisions. |
| assistcaseops.documents.residency | residency verification | RECORD | Residency proof shows service area or jurisdiction connection. | Prevents wrong program assignment. |
| assistcaseops.documents.expense | expense verification | RECORD | Expenses such as rent, utilities, childcare or medical costs may affect eligibility. | Calculates aid accurately. |
| assistcaseops.documents.missing_notice | missing document notice | METHOD | Notice states exactly what is missing, deadline and submission channel. | Helps applicants complete cases. |
| assistcaseops.interview.schedule | interview schedule | METHOD | Interview is scheduled by program rule, urgency and applicant availability. | Moves case toward determination. |
| assistcaseops.interview.script | interview script | METHOD | Script gathers consistent facts while allowing clarifying questions. | Reduces arbitrary decisions. |
| assistcaseops.interview.barrier | barrier accommodation | METHOD | Accommodation supports disability, language, transport, phone or technology barriers. | Improves access. |
| assistcaseops.interview.no_show | no-show process | METHOD | No-show process records attempt, reschedule option and required notice. | Keeps due process visible. |
| assistcaseops.eligibility.rule_check | rule check | METHOD | Rule check applies income, assets, residency, household and category criteria. | Produces defensible decisions. |
| assistcaseops.eligibility.calculation | benefit calculation | METHOD | Calculation records inputs, deductions, caps and effective dates. | Explains benefit amount. |
| assistcaseops.eligibility.discretion | discretionary review | CONSTRAINT | Discretionary aid uses documented criteria and approval authority. | Prevents favoritism. |
| assistcaseops.eligibility.ineligibility | ineligibility reason | RECORD | Denial reason cites rule, missing proof or factual mismatch. | Supports appeal rights. |
| assistcaseops.notices.approval | approval notice | METHOD | Approval notice states benefit, period, obligations and reporting duties. | Makes decision actionable. |
| assistcaseops.notices.denial | denial notice | METHOD | Denial notice states reason, rule reference and appeal deadline. | Protects due process. |
| assistcaseops.notices.change | change notice | METHOD | Change notice explains reduction, suspension, termination or correction. | Prevents surprise benefit changes. |
| assistcaseops.notices.language | notice language | METHOD | Notices use preferred language and plain wording where possible. | Improves understanding. |
| assistcaseops.payments.authorization | payment authorization | SAFETY_RULE | Payment or voucher requires eligibility decision, approval and funding source. | Controls public funds. |
| assistcaseops.payments.vendor | vendor payment | METHOD | Vendor payment verifies payee, invoice, service and fraud checks. | Prevents misdirected aid. |
| assistcaseops.payments.client | client payment | METHOD | Client payment records amount, method, date and reconciliation status. | Ensures benefit delivery. |
| assistcaseops.payments.overpayment | overpayment | FAILURE_MODE | Overpayment records cause, amount, notice and recovery rule. | Manages financial correction. |
| assistcaseops.renewal.renewal_date | renewal date | RECORD | Renewal date sets when eligibility must be redetermined. | Prevents expired benefits. |
| assistcaseops.renewal.change_report | change reporting | CONSTRAINT | Clients must report certain changes within program timeframes. | Keeps eligibility current. |
| assistcaseops.renewal.auto_data | automated data match | METHOD | Data matches can verify income, employment, death, incarceration or duplicate aid. | Reduces manual burden. |
| assistcaseops.renewal.closure | renewal closure | METHOD | Closure after nonresponse follows notice, deadline and reopening rules. | Keeps caseload accurate. |
| assistcaseops.appeals.appeal_intake | appeal intake | RECORD | Appeal records contested decision, date, representative and deadline status. | Starts formal review. |
| assistcaseops.appeals.case_packet | case packet | RECORD | Case packet includes application, proofs, notes, notices and rule basis. | Prepares hearing. |
| assistcaseops.appeals.hearing_result | hearing result | RECORD | Hearing result updates benefit status, correction and effective date. | Implements due process outcome. |
| assistcaseops.fraud.red_flag | fraud red flag | MODEL | Red flags include inconsistent documents, duplicate identity, hidden income or suspicious vendor. | Targets review without assuming guilt. |
| assistcaseops.fraud.referral | fraud referral | METHOD | Referral sends evidence to investigation under policy. | Separates casework from investigation. |
| assistcaseops.fraud.privacy | privacy boundary | SAFETY_RULE | Fraud controls must protect lawful applicant privacy and avoid discriminatory profiling. | Keeps program fair. |
| assistcaseops.records.case_notes | case notes | RECORD | Notes record facts, contacts, decisions and pending tasks without irrelevant judgment. | Supports continuity and audit. |
| assistcaseops.records.retention | retention rule | CONSTRAINT | Case records follow program retention, privacy and legal hold rules. | Controls sensitive data lifecycle. |
| assistcaseops.metrics.timeliness | timeliness metric | MEASUREMENT | Timeliness tracks application-to-decision and renewal processing time. | Shows service performance. |
| assistcaseops.metrics.error_rate | error rate | MEASUREMENT | Error rate tracks improper approvals, denials, payments and notices. | Guides training and quality. |
| assistcaseops.qa.supervisory_review | supervisory review | QUALITY_CHECK | Sampled decisions and high-risk approvals receive supervisory review. | Improves accuracy and consistency. |
