# BATCH_178 — Mortgage & Loan Servicing Operations Detail
# world_skills_core · source: world_skills_core:batch_178:mortgage_loan_servicing_operations
# KnowledgeUnits: 44
# ВНИМАНИЕ: операционные знания; не финансовая, инвестиционная или юридическая консультация.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| loanserv.boarding.loan_boarding | Loan boarding | invariant | Boarding loads loan terms, borrower data, collateral, escrow, payment rules and documents into servicing system. | start servicing accurately |
| loanserv.boarding.data_validation | Servicing data validation | invariant | Validation checks balances, rates, dates, fees, escrow, investor and document consistency. | prevent downstream errors |
| loanserv.boarding.welcome_notice | Servicing welcome notice | invariant | Notice tells borrower servicer identity, payment address, contact channels and effective date. | borrower knows where to pay |
| loanserv.boarding.document_exception | Boarding document exception | invariant | Exception flags missing or inconsistent note, mortgage, insurance, tax, escrow or transfer records. | fix before trouble |
| loanserv.boarding.investor_code | Investor code | variant | Investor code links loan to owner, reporting rules, remittance, loss mitigation and servicing requirements. | rules depend on owner |
| loanserv.boarding.service_transfer | Servicing transfer | invariant | Transfer moves servicing rights and records between servicers with borrower notice and data reconciliation. | handoff risk |
| loanserv.payments.payment_processing | Loan payment processing | invariant | Processing applies borrower funds to interest, principal, escrow, fees or suspense according to rules. | money allocation |
| loanserv.payments.payment_effective_date | Payment effective date | invariant | Effective date determines when payment is credited for delinquency, interest or reporting. | date matters |
| loanserv.payments.suspense_account | Suspense account | invariant | Suspense holds partial or unidentified funds until enough information exists to apply them. | money not lost |
| loanserv.payments.late_fee_assessment | Late fee assessment | variant | Fee assessment follows note terms, grace period, payment date and applicable restrictions. | charge only if allowed |
| loanserv.payments.autopay_setup | Autopay setup | variant | Setup records borrower authorization, account, amount, frequency, start date and cancellation path. | recurring payment control |
| loanserv.payments.payment_reversal | Payment reversal | invariant | Reversal corrects returned, misapplied or invalid payment with audit trail and borrower impact review. | undo carefully |
| loanserv.escrow.escrow_analysis | Escrow analysis | invariant | Analysis compares projected taxes, insurance, cushion, payments and shortages or surplus. | yearly escrow truth |
| loanserv.escrow.tax_disbursement | Tax disbursement | invariant | Disbursement pays property tax from escrow by due date, parcel and taxing authority. | avoid tax default |
| loanserv.escrow.insurance_disbursement | Insurance disbursement | invariant | Disbursement pays hazard, flood or other required insurance premium from escrow. | protect collateral |
| loanserv.escrow.shortage_spread | Escrow shortage spread | variant | Shortage spread distributes escrow deficit over allowed period in borrower payment. | smooth repayment |
| loanserv.escrow.surplus_refund | Escrow surplus refund | variant | Surplus refund returns excess escrow when rules and thresholds require it. | give back overcollection |
| loanserv.escrow.force_placed_insurance | Force-placed insurance | invariant | Force placement may occur when required coverage lapses and borrower does not provide proof. | collateral protection |
| loanserv.customer.statement | Periodic statement | invariant | Statement shows payment due, transaction activity, fees, escrow, delinquency messages and contact data. | borrower visibility |
| loanserv.customer.payoff_quote | Payoff quote | invariant | Quote calculates amount needed to satisfy loan by date, including principal, interest, fees and escrow treatment. | close loan accurately |
| loanserv.customer.research_request | Borrower research request | invariant | Request investigates payment, balance, escrow, credit reporting or document questions. | structured inquiry |
| loanserv.customer.complaint_case | Servicing complaint case | invariant | Complaint case records issue, borrower impact, deadlines, evidence, response and corrective action. | regulated service recovery |
| loanserv.customer.address_change | Borrower address change | invariant | Address change updates contact information with identity verification and notice controls. | send notices correctly |
| loanserv.customer.successor_contact | Successor-in-interest contact | variant | Successor contact handles person claiming interest after death, divorce or transfer under required process. | sensitive servicing path |
| loanserv.delinquency.delinquency_bucket | Delinquency bucket | invariant | Bucket classifies loan by days past due or missed payment count. | collections priority |
| loanserv.delinquency.collection_call | Collection call record | invariant | Call record logs contact attempt, outcome, promise, hardship note and compliance disclosures. | evidence of outreach |
| loanserv.delinquency.promise_to_pay | Promise to pay | variant | Promise records borrower commitment amount, date and follow-up without guaranteeing cure. | track expected cure |
| loanserv.delinquency.loss_mitigation_package | Loss mitigation package | invariant | Package collects borrower documents for assistance review under investor and regulatory rules. | evaluate alternatives |
| loanserv.delinquency.forbearance_tracking | Forbearance tracking | variant | Tracking records temporary payment relief terms, start, end, reviews and exit path. | temporary status |
| loanserv.delinquency.repayment_plan | Repayment plan | variant | Plan spreads arrears across future payments under approved terms and monitoring. | cure over time |
| loanserv.foreclosure.referral_hold | Foreclosure referral hold | invariant | Hold prevents referral when account has active restriction, assistance review, dispute or required notice gap. | avoid wrongful escalation |
| loanserv.foreclosure.notice_milestone | Foreclosure notice milestone | invariant | Milestone tracks required borrower notices, dates, cure periods and documentation. | timeline control |
| loanserv.foreclosure.attorney_referral | Attorney referral | variant | Referral sends eligible defaulted loan to legal counsel with documents and status. | controlled handoff |
| loanserv.foreclosure.sale_date_tracking | Sale date tracking | invariant | Tracking monitors scheduled foreclosure sale, postponements, holds and investor reporting. | critical date |
| loanserv.foreclosure.reinstatement_quote | Reinstatement quote | invariant | Quote calculates amount needed to cure default without paying loan in full. | cure figure |
| loanserv.foreclosure.bankruptcy_flag | Bankruptcy flag | invariant | Flag changes contact, collection, legal and system handling after bankruptcy notice. | special protection |
| loanserv.investor.remittance | Investor remittance | invariant | Remittance sends collected funds to investor according to servicing agreement. | money to owner |
| loanserv.investor.reporting | Investor reporting | invariant | Reporting provides loan status, balances, payments, delinquency, escrow and loss mitigation data. | owner visibility |
| loanserv.investor.advance_tracking | Servicer advance tracking | variant | Advances track servicer-paid amounts for taxes, insurance, principal, interest or expenses. | recoverable outlay |
| loanserv.investor.custodial_account | Custodial account reconciliation | invariant | Reconciliation compares borrower funds, disbursements, deposits, remittances and bank balances. | trust money control |
| loanserv.investor.audit_trail | Servicing audit trail | invariant | Audit trail records changes, payments, notices, calls, approvals, overrides and system events. | accountable servicing |
| loanserv.closeout.loan_paid_in_full | Paid-in-full workflow | invariant | Workflow confirms payoff receipt, lien release, escrow disposition, final statement and record closure. | end servicing cleanly |
| loanserv.closeout.lien_release | Lien release tracking | invariant | Tracking ensures recorded security interest is released after payoff under required timeline. | clear collateral |
| loanserv.closeout.document_retention | Servicing record retention | invariant | Retention defines how long loan documents, statements, calls, notices and transactions are kept. | records after payoff |
