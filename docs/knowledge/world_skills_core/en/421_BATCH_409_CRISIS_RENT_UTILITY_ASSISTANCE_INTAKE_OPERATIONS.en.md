# BATCH 409: Crisis Rent and Utility Assistance Intake Operations

**KnowledgeUnits:** 45  
**Namespace:** `rentutilityintakeops.*`  
**Scope:** screening, documents, landlord/utility contact, pledges, payments, denials and follow-up.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| rentutilityintakeops.intake.request_source | request source | RECORD | Source records hotline, nonprofit, shelter, benefits desk, utility, landlord or walk-in. | Shows entry path. |
| rentutilityintakeops.intake.household | household profile | RECORD | Profile captures household size, address, income, disaster impact, arrears and contact. | Supports screening. |
| rentutilityintakeops.intake.assistance_type | assistance type | RECORD | Type distinguishes rent, deposit, mortgage, electric, gas, water, internet or reconnection. | Routes case. |
| rentutilityintakeops.intake.urgency | urgency model | MODEL | Urgency weighs eviction date, shutoff date, health risk, children, disability and displacement. | Prioritizes help. |
| rentutilityintakeops.screening.program_fit | program fit | MODEL | Fit matches household to eligible funding streams and service area rules. | Selects path. |
| rentutilityintakeops.screening.income_check | income check | QUALITY_CHECK | Income check records wages, benefits, unemployment, self-employment or hardship statement. | Supports eligibility. |
| rentutilityintakeops.screening.hardship | hardship statement | RECORD | Statement describes disaster, job loss, medical cost, displacement or utility burden. | Documents need. |
| rentutilityintakeops.screening.duplication | duplication check | QUALITY_CHECK | Check compares prior assistance, insurance, FEMA, landlord credits and utility programs. | Prevents duplicate payment. |
| rentutilityintakeops.documents.document_list | document list | RECORD | List includes ID, lease, bill, ledger, income proof, hardship and payment instructions. | Organizes case. |
| rentutilityintakeops.documents.missing_doc | missing document | RECORD | Missing document records item, owner, deadline and workaround if allowed. | Keeps case moving. |
| rentutilityintakeops.documents.upload | upload support | METHOD | Staff help scan/upload records under privacy rules. | Completes file. |
| rentutilityintakeops.documents.redaction | redaction rule | SAFETY_RULE | Sensitive numbers are redacted when not needed for payment or eligibility. | Protects identity. |
| rentutilityintakeops.landlord.contact | landlord contact | RECORD | Contact records landlord/manager name, phone, email, payment method and verification. | Enables rent payment. |
| rentutilityintakeops.landlord.ledger | rent ledger | RECORD | Ledger captures months owed, fees, credits, court costs and payment deadline. | Verifies arrears. |
| rentutilityintakeops.landlord.w9_vendor | vendor setup | METHOD | Vendor setup collects required tax/payment information for landlord or property manager. | Enables payment. |
| rentutilityintakeops.landlord.hold_agreement | hold agreement | RECORD | Hold agreement records pause on eviction or fees while assistance is processed. | Protects tenancy. |
| rentutilityintakeops.utility.account_verify | utility account verify | QUALITY_CHECK | Verification checks customer, account number, service address, balance and shutoff date. | Prevents wrong payment. |
| rentutilityintakeops.utility.utility_contact | utility contact | RECORD | Contact records provider, department, representative, extension and confirmation number. | Tracks communication. |
| rentutilityintakeops.utility.payment_plan | payment plan | RECORD | Plan records arrears, installment terms, reconnection, deposits and assistance pledge. | Coordinates relief. |
| rentutilityintakeops.utility.medical_need | medical need flag | SAFETY_RULE | Medical device or health risk flag routes to utility protection or urgent review. | Prevents harm. |
| rentutilityintakeops.pledge.pledge_record | pledge record | RECORD | Pledge records amount, funding source, recipient, conditions, expiration and approver. | Commits funds. |
| rentutilityintakeops.pledge.partial_payment | partial payment | METHOD | Partial support documents remaining balance and other resources needed. | Sets expectations. |
| rentutilityintakeops.pledge.pledge_letter | pledge letter | RECORD | Letter confirms amount, case ID, payee and processing timeline. | Reassures landlord/utility. |
| rentutilityintakeops.pledge.expiration | pledge expiration | CONSTRAINT | Expiration rule defines when unused pledge returns to available funds. | Controls budget. |
| rentutilityintakeops.payment.payment_request | payment request | RECORD | Request links case, payee, amount, documents, approval and funding code. | Starts payment. |
| rentutilityintakeops.payment.payee_validation | payee validation | QUALITY_CHECK | Validation checks landlord, utility or vendor identity and payment destination. | Prevents fraud. |
| rentutilityintakeops.payment.disbursement | disbursement record | RECORD | Record captures payment date, method, reference, amount and payee confirmation. | Closes finance loop. |
| rentutilityintakeops.payment.reconciliation | reconciliation | QUALITY_CHECK | Reconciliation matches pledge, payment, ledger/utility posting and remaining balance. | Ensures accuracy. |
| rentutilityintakeops.denial.denial_reason | denial reason | RECORD | Reason captures ineligibility, missing documents, duplicate benefit, exhausted funds or no response. | Explains outcome. |
| rentutilityintakeops.denial.notice | denial notice | RECORD | Notice tells applicant reason, appeal/review path and alternate referrals. | Maintains fairness. |
| rentutilityintakeops.denial.appeal | appeal review | METHOD | Appeal reviews new evidence, error, deadline or exceptional hardship. | Corrects decisions. |
| rentutilityintakeops.denial.referral | alternate referral | METHOD | Denied cases receive other benefits, legal aid, mediation or payment-plan referral. | Reduces dead end. |
| rentutilityintakeops.followup.status_check | status check | METHOD | Staff check payment posting, eviction hold, reconnection or resident outcome. | Confirms effect. |
| rentutilityintakeops.followup.unreachable | unreachable process | METHOD | Attempts, backup contact and closure reason are recorded. | Keeps audit fair. |
| rentutilityintakeops.followup.reopen | reopen rule | METHOD | Case can reopen for new shutoff, eviction notice, returned payment or new documents. | Handles change. |
| rentutilityintakeops.followup.case_close | case close | RECORD | Closure records final payment, denial, referral, balance and household notification. | Ends case. |
| rentutilityintakeops.privacy.minimum_data | minimum data | SAFETY_RULE | Intake stores only needed identity, housing, utility and income data. | Reduces exposure. |
| rentutilityintakeops.privacy.safe_contact | safe contact | SAFETY_RULE | Safe contact controls messages for domestic violence, shared housing or insecure phone access. | Protects applicants. |
| rentutilityintakeops.privacy.role_access | role access | SAFETY_RULE | Role access limits who can view income, landlord, utility and payment details. | Controls records. |
| rentutilityintakeops.reporting.daily_summary | daily summary | MEASUREMENT | Summary reports applications, approvals, denials, payments, holds and urgent risks. | Informs fund managers. |
| rentutilityintakeops.metrics.approval_rate | approval rate | MEASUREMENT | Rate tracks approvals among completed applications by program and reason. | Shows effectiveness. |
| rentutilityintakeops.metrics.time_to_payment | time to payment | MEASUREMENT | Time measures intake to disbursement or denial. | Reveals bottlenecks. |
| rentutilityintakeops.metrics.funds_remaining | funds remaining | MEASUREMENT | Remaining funds track committed, paid, expired and available balances. | Controls budget. |
| rentutilityintakeops.review.after_action | after-action review | METHOD | Review captures document barriers, landlord/utility coordination, payment delays and denial fairness. | Improves future intake. |
| rentutilityintakeops.landlord.rent_ledger | Книга аренды | RECORD | В книге регистрируются месяцы задолженности, сборы, кредиты, судебные издержки и сроки оплаты. | Проверяет задолженность. |
