# BATCH_181 — Procurement Card Controls Detail
# world_skills_core · source: world_skills_core:batch_181:procurement_card_controls_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| pcardops.setup.card_issuance | Procurement card issuance | invariant | Issuance assigns card to approved employee with role, limits, training and policy acknowledgment. | controlled purchasing access |
| pcardops.setup.cardholder_agreement | Cardholder agreement | invariant | Agreement states allowed use, receipt duties, prohibited purchases, security and consequences. | rules accepted |
| pcardops.setup.credit_limit | P-card credit limit | invariant | Limit caps spending per transaction, day, month or cycle according to role and risk. | reduce exposure |
| pcardops.setup.merchant_category | Merchant category control | variant | MCC control blocks or allows supplier categories based on policy and card purpose. | prevent wrong suppliers |
| pcardops.setup.single_purchase_limit | Single purchase limit | invariant | Limit prevents splitting large purchases or bypassing procurement thresholds. | transaction guard |
| pcardops.setup.card_activation | Card activation control | invariant | Activation confirms cardholder identity, training completion and system setup before use. | no silent card |
| pcardops.transaction.receipt_required | Receipt required | invariant | Receipt proves vendor, date, amount, tax, items and business purpose. | purchase evidence |
| pcardops.transaction.business_purpose | Business purpose | invariant | Purpose explains why purchase was necessary for organization activity. | not just what was bought |
| pcardops.transaction.tax_review | Sales tax review | variant | Review checks whether tax was charged correctly or exemption should apply. | avoid tax leakage |
| pcardops.transaction.split_purchase | Split purchase detection | invariant | Detection identifies multiple related transactions used to avoid limits or approval. | anti-circumvention |
| pcardops.transaction.personal_use | Personal use flag | invariant | Flag marks transaction appearing unrelated to business or policy. | misuse control |
| pcardops.transaction.emergency_purchase | Emergency purchase note | variant | Note documents urgent purchase justification, approver and follow-up after normal process. | exception with record |
| pcardops.reconcile.monthly_reconciliation | Monthly card reconciliation | invariant | Reconciliation matches statement, receipts, coding, approvals and disputed items. | close billing cycle |
| pcardops.reconcile.statement_review | Statement review | invariant | Review checks all posted card transactions against supporting documents and limits. | cardholder accountability |
| pcardops.reconcile.cost_center_coding | Cost center coding | invariant | Coding assigns purchase to correct department, project, grant or account. | accounting accuracy |
| pcardops.reconcile.missing_receipt | Missing receipt affidavit | variant | Affidavit documents lost receipt, purchase details and cardholder certification. | fallback evidence |
| pcardops.reconcile.approver_signoff | Approver signoff | invariant | Signoff confirms supervisor or budget owner reviewed transaction legitimacy. | independent review |
| pcardops.reconcile.late_reconciliation | Late reconciliation | invariant | Late reconciliation indicates cardholder or approver missed deadline and may trigger escalation. | control timeliness |
| pcardops.dispute.charge_dispute | Card charge dispute | invariant | Dispute challenges incorrect, duplicate, fraudulent or undelivered charge with issuer or vendor. | recover money |
| pcardops.dispute.fraud_report | P-card fraud report | invariant | Fraud report records unauthorized transaction, card status, issuer contact and investigation. | act quickly |
| pcardops.dispute.temporary_credit | Temporary credit | variant | Credit may appear while dispute is reviewed and must be tracked until final resolution. | avoid false close |
| pcardops.dispute.vendor_credit | Vendor credit tracking | invariant | Credit tracking ensures returned goods or billing corrections appear on statement. | close refund loop |
| pcardops.dispute.duplicate_charge | Duplicate charge review | invariant | Review compares same vendor, amount, date, receipt and description to detect double billing. | common error |
| pcardops.dispute.card_replacement | Card replacement workflow | invariant | Replacement controls lost, stolen, compromised or damaged card with cancellation and reissue. | protect account |
| pcardops.policy.prohibited_purchase | Prohibited purchase list | invariant | List defines items or services not allowed on card regardless of limit. | clear boundaries |
| pcardops.policy.gift_card_control | Gift card purchase control | variant | Gift cards require extra controls because they are cash-like and hard to trace. | high misuse risk |
| pcardops.policy.travel_overlap | Travel and p-card overlap | variant | Overlap rules clarify whether travel, meals, lodging or fuel belong on travel card or p-card. | avoid policy conflict |
| pcardops.policy.grant_restriction | Grant-funded purchase restriction | invariant | Grant restriction checks allowability, period, budget line and documentation before charge. | funder compliance |
| pcardops.policy.asset_threshold | Asset threshold rule | invariant | Rule blocks or flags purchases that should enter fixed asset or inventory process. | asset visibility |
| pcardops.policy.contract_leakage | Contract leakage | variant | Leakage occurs when cardholders buy outside preferred contracts or negotiated suppliers. | procurement value loss |
| pcardops.audit.audit_sampling | P-card audit sampling | invariant | Sampling selects transactions by risk, amount, MCC, cardholder, lateness or random method. | focused review |
| pcardops.audit.exception_report | P-card exception report | invariant | Report flags missing receipts, blocked attempts, split purchases, late approvals and unusual vendors. | monitor patterns |
| pcardops.audit.cardholder_review | Cardholder periodic review | invariant | Review verifies cardholder still needs card, has proper limits and completed training. | access lifecycle |
| pcardops.audit.inactive_card | Inactive card review | variant | Inactive review may cancel or lower limits on unused cards to reduce exposure. | remove dormant risk |
| pcardops.audit.high_risk_vendor | High-risk vendor flag | variant | Flag marks vendors associated with cash-like goods, personal benefit, sanctions or policy concerns. | stronger review |
| pcardops.audit.corrective_action | P-card corrective action | invariant | Action addresses policy breach through repayment, training, warning, suspension or investigation. | enforce controls |
| pcardops.admin.limit_change | Card limit change | invariant | Limit change requires documented business need, approval, effective date and review. | controlled flexibility |
| pcardops.admin.card_suspension | Card suspension | invariant | Suspension stops card use due to missing reconciliation, misuse, employment change or investigation. | stop risk |
| pcardops.admin.employee_departure | Departing employee card closure | invariant | Closure cancels card, collects receipts, resolves transactions and removes system access. | offboarding control |
| pcardops.admin.training_record | P-card training record | invariant | Training record confirms cardholder and approver understand policies and tools. | competence evidence |
| pcardops.admin.policy_update | P-card policy update | variant | Update communicates rule changes, system changes and effective date to cardholders. | keep behavior current |
| pcardops.admin.records_retention | P-card records retention | invariant | Retention defines how long statements, receipts, approvals, disputes and audits are kept. | audit trail |
| pcardops.metrics.spend_by_category | P-card spend by category | invariant | Category report shows spending by MCC, supplier, department and purpose. | spend visibility |
| pcardops.metrics.decline_analysis | P-card decline analysis | variant | Declines reveal blocked vendors, wrong limits, fraud attempts or training issues. | control signal |
