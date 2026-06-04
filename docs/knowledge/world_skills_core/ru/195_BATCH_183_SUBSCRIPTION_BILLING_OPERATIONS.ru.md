# BATCH_183 — Subscription Billing Operations Detail
# world_skills_core · source: world_skills_core:batch_183:subscription_billing_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| subbill.catalog.plan_catalog | Subscription plan catalog | invariant | Plan catalog defines products, prices, billing periods, entitlements, currencies and eligibility. | source of billing truth |
| subbill.catalog.price_version | Price version | invariant | Price version preserves historical pricing while allowing new offers or changes for future customers. | do not overwrite past |
| subbill.catalog.addon | Subscription add-on | variant | Add-on grants extra feature, seat, usage or service alongside base plan. | modular revenue |
| subbill.catalog.trial_plan | Trial plan | variant | Trial plan gives temporary access with defined duration, conversion rule and billing trigger. | controlled free access |
| subbill.catalog.discount_code | Discount code | variant | Discount code applies approved price reduction by amount, percent, duration or eligibility. | promotion control |
| subbill.catalog.entitlement_map | Entitlement map | invariant | Entitlement map links paid plan or add-on to actual product access. | billing drives access |
| subbill.lifecycle.subscription_start | Subscription start | invariant | Start date sets access, billing cycle, renewal schedule and revenue period. | clock begins |
| subbill.lifecycle.renewal_event | Renewal event | invariant | Renewal creates next billing period, invoice or charge attempt according to subscription terms. | recurring cycle |
| subbill.lifecycle.plan_upgrade | Plan upgrade | variant | Upgrade increases service level and may trigger proration, entitlement change and immediate charge. | mid-cycle change |
| subbill.lifecycle.plan_downgrade | Plan downgrade | variant | Downgrade reduces service level and may apply now or next renewal depending on policy. | avoid surprise access loss |
| subbill.lifecycle.seat_change | Seat quantity change | variant | Seat change adjusts billable quantity, entitlements and possible proration. | quantity as billing input |
| subbill.lifecycle.subscription_pause | Subscription pause | variant | Pause temporarily stops billing or access under defined eligibility and restart rule. | controlled interruption |
| subbill.proration.proration_rule | Proration rule | invariant | Rule calculates partial-period charge or credit when subscription changes mid-cycle. | fair partial billing |
| subbill.proration.credit_balance | Customer credit balance | invariant | Credit balance stores unused value to apply to future invoices or refund workflow. | value not lost |
| subbill.proration.midcycle_invoice | Mid-cycle invoice | variant | Mid-cycle invoice bills immediate changes outside normal renewal invoice. | charge now |
| subbill.proration.effective_date | Billing effective date | invariant | Effective date determines when price, plan or quantity change affects invoice and entitlement. | date controls math |
| subbill.invoice.invoice_generation | Subscription invoice generation | invariant | Generation creates invoice lines from plan, usage, discounts, taxes, credits and period. | bill from rules |
| subbill.invoice.invoice_line_item | Invoice line item | invariant | Line item shows charge, credit, tax, period, quantity or adjustment separately. | explain amount |
| subbill.invoice.tax_calculation | Subscription tax calculation | variant | Tax calculation depends on product, customer location, exemption, jurisdiction and tax engine. | compliance complexity |
| subbill.invoice.invoice_finalization | Invoice finalization | invariant | Finalization locks invoice for payment, delivery and accounting handoff. | stop changing draft |
| subbill.invoice.invoice_void | Invoice void | variant | Void cancels invoice before or after issue according to accounting and policy rules. | remove invalid bill |
| subbill.invoice.credit_note | Credit note | invariant | Credit note documents approved reduction or reversal of billed amount. | auditable correction |
| subbill.payment.payment_attempt | Payment attempt | invariant | Attempt submits charge to payment method, gateway or processor and records outcome. | collect cash |
| subbill.payment.payment_failure | Payment failure | invariant | Failure records decline reason, gateway code, retry eligibility and customer notification. | start recovery |
| subbill.payment.retry_schedule | Payment retry schedule | variant | Retry schedule spaces charge attempts to recover failed payments without excessive attempts. | dunning rhythm |
| subbill.payment.payment_method_update | Payment method update | invariant | Update replaces card, bank or wallet details with secure tokenized handling. | keep billing active |
| subbill.payment.chargeback | Subscription chargeback | invariant | Chargeback disputes a collected payment and requires evidence, service status and accounting handling. | revenue at risk |
| subbill.payment.refund | Subscription refund | variant | Refund returns collected funds with reason, approval, amount and link to invoice or payment. | controlled reversal |
| subbill.dunning.dunning_notice | Dunning notice | invariant | Notice tells customer payment failed, action needed, deadline and service consequence. | recover without surprise |
| subbill.dunning.grace_period | Billing grace period | variant | Grace period allows access or payment recovery before suspension or cancellation. | customer-friendly buffer |
| subbill.dunning.suspension | Service suspension | invariant | Suspension restricts access after failed payment or policy trigger while preserving account record. | access follows payment status |
| subbill.dunning.reactivation | Subscription reactivation | invariant | Reactivation restores access after payment, approval or issue resolution. | recover customer |
| subbill.cancel.cancel_request | Cancellation request | invariant | Request records customer intent, date, reason, effective date and retention offer status. | start churn workflow |
| subbill.cancel.end_of_term_cancel | End-of-term cancellation | variant | Cancellation at renewal prevents future billing while keeping service through paid term. | predictable end |
| subbill.cancel.immediate_cancel | Immediate cancellation | variant | Immediate cancel stops access now and may trigger credit or refund review. | fast stop |
| subbill.cancel.winback_offer | Winback offer | variant | Winback offer attempts retention with discount, plan change or support path under policy. | reduce churn |
| subbill.reporting.mrr | Monthly recurring revenue | invariant | MRR normalizes recurring subscription revenue to monthly value. | subscription KPI |
| subbill.reporting.churn_rate | Subscription churn rate | invariant | Churn rate measures lost customers or recurring revenue over period. | retention signal |
| subbill.reporting.expansion_revenue | Expansion revenue | variant | Expansion revenue comes from upgrades, add-ons, seats or usage growth in existing accounts. | growth inside base |
| subbill.reporting.deferred_revenue_handoff | Deferred revenue handoff | invariant | Handoff sends billing period, invoice, service dates and credits to revenue accounting. | accounting boundary |
| subbill.reporting.billing_exception | Billing exception report | invariant | Report flags failed invoices, tax errors, stuck renewals, uncollected payments and manual overrides. | operations control |
| subbill.control.manual_override | Billing manual override | invariant | Override changes price, invoice, credit or status and needs reason, approval and audit trail. | high-risk action |
| subbill.control.audit_trail | Subscription billing audit trail | invariant | Audit trail records plan changes, invoices, payments, cancellations, credits and user actions. | explain history |
| subbill.control.reconciliation | Billing reconciliation | invariant | Reconciliation compares billing system, payment processor, bank, GL and revenue reports. | systems agree |
