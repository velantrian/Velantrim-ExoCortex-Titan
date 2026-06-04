# BATCH 344: Utility Customer Portal Operations

**KnowledgeUnits:** 44  
**Namespace:** `portalops.*`  
**Scope:** registration, login, account linking, payments, usage data, alerts, failures and support.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| portalops.registration.account_lookup | account lookup | METHOD | Registration matches customer name, account number, service address or meter data. | Links users to the right utility account. |
| portalops.registration.identity_check | identity check | SAFETY_RULE | Portal registration verifies identity with approved data and fraud controls. | Protects customer records. |
| portalops.registration.email_verify | email verification | METHOD | Email verification confirms a reachable contact before full account access. | Reduces bad login and alert records. |
| portalops.registration.phone_verify | phone verification | METHOD | Phone verification supports alerts, MFA or recovery where policy allows. | Improves account recovery and notification accuracy. |
| portalops.registration.duplicate_profile | duplicate profile | FAILURE_MODE | Duplicate profiles split alerts, payments and account links. | Causes service confusion. |
| portalops.login.mfa | multi-factor authentication | SAFETY_RULE | MFA is required or risk-triggered for sensitive account actions. | Lowers account takeover risk. |
| portalops.login.password_reset | password reset | METHOD | Reset flow verifies contact channel and rate limits attempts. | Restores access without exposing accounts. |
| portalops.login.lockout | lockout control | CONSTRAINT | Failed attempts trigger lockout, cooldown or review. | Balances security and support load. |
| portalops.login.session_timeout | session timeout | SAFETY_RULE | Sensitive sessions expire after inactivity or risk signals. | Protects unattended devices. |
| portalops.account_link.primary_account | primary account link | RECORD | Primary account link stores user, account, role and authorization basis. | Enables controlled self-service. |
| portalops.account_link.multiple_accounts | multiple account support | METHOD | Customers may link several service addresses or business accounts under one profile. | Supports landlords and multi-site users. |
| portalops.account_link.authorized_user | authorized user | CONSTRAINT | Authorized users receive only permitted view or action rights. | Keeps privacy boundaries clear. |
| portalops.account_link.unlink | unlink workflow | METHOD | Account unlinking removes access without deleting billing records. | Handles move-outs and role changes. |
| portalops.profile.contact_update | contact update | METHOD | Customers can update email, phone, mailing address or communication preferences. | Keeps operational contact data current. |
| portalops.profile.preference_center | preference center | METHOD | Preference center controls paperless billing, alerts, language and channel choices. | Reduces unwanted messages. |
| portalops.profile.language | language preference | RECORD | Language preference is stored for portal display and outbound notifications. | Improves customer accessibility. |
| portalops.profile.audit_trail | profile audit trail | RECORD | Sensitive profile changes record user, time, IP/device and field changed. | Supports fraud investigation. |
| portalops.payments.payment_method | payment method | RECORD | Payment method token stores type, provider, status and customer authorization. | Enables secure recurring and one-time payments. |
| portalops.payments.one_time | one-time payment | METHOD | One-time payment confirms amount, account, fee, date and receipt. | Reduces misapplied payments. |
| portalops.payments.autopay | autopay enrollment | METHOD | Autopay enrollment records authorization, start date, limit and cancellation path. | Prevents unauthorized drafts. |
| portalops.payments.failed_payment | failed payment | FAILURE_MODE | Failed payments generate clear status, retry rule, fee notice and support path. | Avoids silent delinquency. |
| portalops.payments.refund_request | refund request | METHOD | Portal can route refund or overpayment questions to billing review. | Keeps financial exceptions controlled. |
| portalops.billing.bill_view | bill view | METHOD | Bill view shows current, past, due, adjusted and final bills with document links. | Lets customers inspect charges. |
| portalops.billing.usage_chart | usage chart | MEASUREMENT | Usage chart shows meter reads, estimates, intervals and comparison periods. | Helps customers understand consumption. |
| portalops.billing.leak_hint | leak hint | MODEL | Usage anomaly hints point to possible leak or meter exception without diagnosing cause. | Encourages timely customer action. |
| portalops.billing.dispute_link | dispute link | METHOD | Billing dispute link captures issue type, bill, evidence and desired resolution. | Routes exceptions to the right queue. |
| portalops.alerts.outage_alert | outage alert opt-in | METHOD | Portal offers outage notification preferences by account and channel. | Improves event communication. |
| portalops.alerts.billing_alert | billing alert | METHOD | Billing alerts notify due date, high usage, payment failure or arrangement status. | Reduces avoidable delinquency. |
| portalops.alerts.service_notice | service notice | METHOD | Service notices inform planned work, shutoff risk, conservation or water quality issues. | Uses portal as communication hub. |
| portalops.alerts.suppression | suppression rule | CONSTRAINT | Suppression blocks duplicate, opted-out or legally restricted messages. | Prevents notification abuse. |
| portalops.support.ticket_create | support ticket | METHOD | Portal support ticket records category, account, description, attachments and priority. | Creates traceable self-service help. |
| portalops.support.chat_handoff | chat handoff | METHOD | Chat or bot handoff sends transcript and account context to support staff. | Avoids customers repeating details. |
| portalops.support.knowledge_base | knowledge base link | METHOD | Portal points customers to approved articles for common tasks. | Deflects routine support demand. |
| portalops.support.escalation | escalation path | METHOD | Failed self-service actions route to billing, field service, IT or call center. | Prevents dead ends. |
| portalops.failure.outage_banner | portal outage banner | METHOD | Portal outage banner announces degraded login, payment, usage or alert features. | Keeps customers informed during platform incidents. |
| portalops.failure.payment_provider | payment provider failure | FAILURE_MODE | Payment provider failure separates portal problem from bank or processor issue. | Guides troubleshooting and reconciliation. |
| portalops.failure.data_latency | data latency | FAILURE_MODE | Usage and payment data may lag source systems and needs visible timestamp. | Prevents false customer assumptions. |
| portalops.security.privacy_notice | privacy notice | CONSTRAINT | Portal explains data use, retention, cookies and customer rights. | Supports legal and trust requirements. |
| portalops.security.access_review | access review | QUALITY_CHECK | Admin and support access to portal data is reviewed periodically. | Limits insider risk. |
| portalops.integration.billing_sync | billing sync | METHOD | Portal synchronizes payments, balances and profile changes with CIS/billing system. | Keeps customer-facing data aligned. |
| portalops.integration.ami_sync | AMI sync | METHOD | Meter usage sync records source, interval, delay and missing-data status. | Makes usage display reliable. |
| portalops.metrics.task_completion | task completion | MEASUREMENT | Metrics track completed registrations, payments, profile updates and tickets. | Shows self-service effectiveness. |
| portalops.metrics.error_rate | error rate | MEASUREMENT | Error rate tracks failed login, payment, sync and page flows. | Identifies platform problems. |
| portalops.closeout.release_review | release review | QUALITY_CHECK | Portal feature releases check security, accessibility, support scripts and rollback. | Reduces customer-impacting defects. |
