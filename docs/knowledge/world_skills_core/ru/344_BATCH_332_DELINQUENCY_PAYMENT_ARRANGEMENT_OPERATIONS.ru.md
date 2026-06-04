# BATCH 332: Delinquency Payment Arrangement Operations

**KnowledgeUnits:** 44  
**Namespace:** `payarrangeops.*`  
**Scope:** eligibility, agreements, reminders, defaults, assistance referrals, holds and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| payarrangeops.intake.account_status | account status | RECORD | Staff review balance, age, notices, holds, prior arrangements and shutoff status. | Starts arrangement from current facts. |
| payarrangeops.intake.customer_contact | customer contact | RECORD | Contact log captures request date, channel, representative and customer statements. | Creates history for later disputes. |
| payarrangeops.eligibility.policy | eligibility policy | CONSTRAINT | Policy defines who may receive arrangement, minimum payment and maximum term. | Keeps decisions consistent. |
| payarrangeops.eligibility.prior_default | prior default screen | QUALITY_CHECK | Previous broken plans affect eligibility or required down payment. | Prevents endless rollovers. |
| payarrangeops.eligibility.hardship | hardship flag | RECORD | Hardship status records medical, income, disaster or legal protections when applicable. | Supports special handling. |
| payarrangeops.eligibility.service_class | service class | DECISION_RULE | Residential, commercial, landlord and municipal accounts may follow different rules. | Risk and policy differ by class. |
| payarrangeops.agreement.plan_terms | plan terms | RECORD | Agreement states balance, down payment, installments, due dates and current charges. | Customer and utility share the same expectation. |
| payarrangeops.agreement.current_bill | current bill rule | CONSTRAINT | Many plans require paying new bills plus installment. | Prevents arrears from growing. |
| payarrangeops.agreement.signature | acceptance record | RECORD | Customer acceptance is recorded by signature, voice consent, portal click or note. | Makes plan enforceable. |
| payarrangeops.agreement.plain_language | plain language | METHOD | Terms explain default, shutoff risk, assistance and contact options clearly. | Reduces accidental default. |
| payarrangeops.payment.down_payment | down payment | DECISION_RULE | Down payment may be required before hold or reconnection. | Shows commitment and reduces arrears. |
| payarrangeops.payment.installment | installment schedule | METHOD | Installments are scheduled weekly, biweekly or monthly by policy. | Aligns repayment with customer cash flow. |
| payarrangeops.payment.autopay | autopay option | METHOD | Customers may enroll in autopay for installments. | Reduces missed payments. |
| payarrangeops.payment.allocation | payment allocation | METHOD | Payments are allocated between current charges, fees and arrangement balance. | Prevents accounting confusion. |
| payarrangeops.reminder.reminder_schedule | reminder schedule | METHOD | SMS, email, letter or call reminders are sent before installment due dates. | Improves completion rate. |
| payarrangeops.reminder.failed_notice | failed payment notice | RECORD | Missed installment notice states cure deadline and consequence. | Gives chance to correct before default. |
| payarrangeops.reminder.contact_preference | contact preference | RECORD | Preferred language and channel are stored. | Makes reminders more likely to be seen. |
| payarrangeops.default.default_trigger | default trigger | DECISION_RULE | Default occurs after missed installment, unpaid current bill or returned payment per policy. | Defines when collections resume. |
| payarrangeops.default.grace_period | grace period | CONSTRAINT | Grace periods and cure windows are policy-controlled. | Prevents premature shutoff. |
| payarrangeops.default.reinstatement | reinstatement rule | DECISION_RULE | Broken plans may be reinstated with payment or supervisor approval. | Gives flexibility without losing control. |
| payarrangeops.default.collections_resume | collections resume | METHOD | Account is returned to notice or shutoff workflow after default. | Keeps delinquency process synchronized. |
| payarrangeops.hold.shutoff_hold | shutoff hold | RECORD | Active arrangement places coded hold on disconnection actions. | Avoids wrongful shutoff. |
| payarrangeops.hold.hold_expiry | hold expiry | DECISION_RULE | Hold expires at plan completion, default, cancellation or date limit. | Prevents permanent accidental protection. |
| payarrangeops.hold.order_cancel | field order cancellation | METHOD | Existing shutoff orders are cancelled or paused after approved plan. | Aligns field work with account status. |
| payarrangeops.assistance.referral | assistance referral | METHOD | Customers may be referred to charity, government aid or conservation help. | Connects payment problem to support options. |
| payarrangeops.assistance.pledge | agency pledge | RECORD | Third-party pledge amount, expiration and contact are recorded. | Avoids relying on vague promises. |
| payarrangeops.assistance.confirmation | aid confirmation | QUALITY_CHECK | Assistance is confirmed before applying credit or hold where policy requires. | Prevents false account updates. |
| payarrangeops.communication.summary | plan summary | RECORD | Customer receives written summary after arrangement creation. | Reduces disputes. |
| payarrangeops.communication.agent_script | agent script | METHOD | Scripts guide staff through eligibility, terms, hardship and warnings. | Improves consistency across agents. |
| payarrangeops.communication.escalation | supervisor escalation | DECISION_RULE | Exceptions outside policy require supervisor approval and reason. | Controls discretion. |
| payarrangeops.records.note_quality | note quality | QUALITY_CHECK | Notes include facts, policy basis, promise amount and next date. | Makes account history usable. |
| payarrangeops.records.document_link | document link | RECORD | Letters, signed agreements and payment confirmations are linked to account. | Preserves evidence. |
| payarrangeops.records.audit | audit trail | RECORD | System records user, timestamps, changes and approvals. | Protects against unauthorized arrangements. |
| payarrangeops.qa.duplicate_plan | duplicate plan check | QUALITY_CHECK | Staff check for existing active plans before creating another. | Prevents conflicting schedules. |
| payarrangeops.qa.amount_math | amount math check | QUALITY_CHECK | Plan balance, installment total and fees are reconciled. | Avoids under- or over-collection. |
| payarrangeops.qa.equity_review | equity review | MODEL | Completion and denial rates can be reviewed by area or customer class. | Detects unfair policy effects. |
| payarrangeops.reporting.active_plans | active plans report | MEASUREMENT | Report tracks number, balance, installment status and risk. | Shows exposure under arrangements. |
| payarrangeops.reporting.default_rate | default rate | MEASUREMENT | Default rate by plan type, term and customer class is tracked. | Helps tune policy. |
| payarrangeops.reporting.assistance_outcome | assistance outcome | MEASUREMENT | Reports show referrals, pledges, completed aid and avoided shutoffs. | Measures customer-support impact. |
| payarrangeops.reporting.cashflow | cashflow forecast | MODEL | Expected installment payments estimate near-term collections. | Supports finance planning. |
| payarrangeops.review.policy_review | policy review | METHOD | Regular review adjusts terms based on defaults, arrears, equity and operations. | Keeps arrangements realistic. |
| payarrangeops.review.post_moratorium | post-moratorium review | METHOD | After shutoff pauses, plans are staged to avoid overwhelming field crews. | Smooths transition back to normal operations. |
| payarrangeops.security.identity | identity verification | SAFETY_RULE | Staff verify account authority before discussing balances or plans. | Protects customer privacy. |
| payarrangeops.closeout.plan_complete | plan complete | RECORD | Completed arrangements are closed with final payment date and status. | Clears holds and reports success. |

