# BATCH 335: Customer Move-In and Move-Out Utility Operations

**KnowledgeUnits:** 44  
**Namespace:** `moveutilityops.*`  
**Scope:** applications, identity, start/stop dates, reads, deposits, transfers, final bills and records.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| moveutilityops.application.service_request | service request | RECORD | Request captures customer, service address, start/stop date, contact, class and requested action. | Creates official handoff between customer service, billing and field work. |
| moveutilityops.application.required_fields | required fields | QUALITY_CHECK | Application is checked for missing identity, date, address, meter and billing data. | Prevents incomplete account setup. |
| moveutilityops.application.tenant_owner | tenant-owner distinction | RECORD | Account role records owner, tenant, property manager or authorized agent. | Determines deposits, notices and responsibility. |
| moveutilityops.application.service_class | service class | DECISION_RULE | Residential, commercial, irrigation and fire-service accounts follow different setup rules. | Keeps billing and operations aligned. |
| moveutilityops.identity.id_check | identity check | SAFETY_RULE | Applicant identity is verified before opening or transferring service. | Reduces fraud and mistaken accounts. |
| moveutilityops.identity.authorized_agent | authorized agent | RECORD | Agent authority is documented through lease, management agreement, power or portal permissions. | Prevents unauthorized changes. |
| moveutilityops.identity.privacy_notice | privacy notice | CONSTRAINT | Customer data collection follows privacy and retention rules. | Protects sensitive account information. |
| moveutilityops.identity.fraud_flag | fraud flag | DECISION_RULE | Suspicious identity, repeated unpaid accounts or document mismatch trigger supervisor review. | Controls account-opening risk. |
| moveutilityops.dates.start_date | start date | RECORD | Start date determines billing responsibility and activation timing. | Avoids overlap or gap between occupants. |
| moveutilityops.dates.stop_date | stop date | RECORD | Stop date ends customer responsibility after final read and policy checks. | Prevents billing old occupant after move-out. |
| moveutilityops.dates.same_day | same-day transfer | METHOD | Same-day move-out/move-in coordinates final and initial reads on one service. | Reduces field trips and billing disputes. |
| moveutilityops.dates.backdate | backdate rule | CONSTRAINT | Backdated service changes require evidence and approval. | Prevents manipulation of billing responsibility. |
| moveutilityops.reads.final_read | final read | RECORD | Final read captures meter value at stop date or field visit. | Anchors final bill. |
| moveutilityops.reads.initial_read | initial read | RECORD | Initial read becomes opening balance for new customer usage. | Prevents inherited consumption. |
| moveutilityops.reads.estimated_move | estimated move read | METHOD | If actual read is unavailable, estimate method and true-up rule are recorded. | Keeps account moving while preserving correction path. |
| moveutilityops.reads.read_dispute | read dispute | QUALITY_CHECK | Move read disputes compare AMI, photo, field read and usage pattern. | Protects both departing and incoming customer. |
| moveutilityops.deposits.deposit_rule | deposit rule | CONSTRAINT | Deposit requirement depends on credit policy, account class, prior history and risk. | Sets consistent financial security. |
| moveutilityops.deposits.deposit_waiver | deposit waiver | DECISION_RULE | Waiver may apply for good history, assistance status, landlord guarantee or regulation. | Allows fair exceptions. |
| moveutilityops.deposits.refund | deposit refund | METHOD | Deposit is refunded or applied to final bill after account closure conditions are met. | Closes financial obligation cleanly. |
| moveutilityops.deposits.transfer | deposit transfer | METHOD | Existing deposit can transfer to new service if policy permits. | Reduces customer friction. |
| moveutilityops.transfers.account_transfer | account transfer | METHOD | Transfer moves customer from old premise to new premise with dates, reads and balance handling. | Maintains continuity without duplicate profiles. |
| moveutilityops.transfers.balance_rule | balance transfer rule | CONSTRAINT | Prior balances may block, transfer or require payment arrangement. | Prevents arrears hiding behind address changes. |
| moveutilityops.transfers.landlord_rollover | landlord rollover | METHOD | Service may revert to owner between tenants under agreement. | Keeps water active for cleaning and showing property. |
| moveutilityops.transfers.multi_unit | multi-unit transfer | METHOD | Apartment or commercial multi-unit moves require unit, meter and landlord verification. | Avoids cross-unit billing. |
| moveutilityops.field.turn_on | turn-on order | RECORD | Field order lists meter, valve, address, date, access and safety notes. | Gives crew clear activation instructions. |
| moveutilityops.field.turn_off | turn-off order | RECORD | Stop service may create shutoff, lock, read or no-field-needed order. | Matches field work to policy and customer request. |
| moveutilityops.field.access_issue | access issue | FAILURE_MODE | Locked gates, pits, dogs or missing meters are logged as exceptions. | Keeps application from falsely completing. |
| moveutilityops.field.leak_check | activation leak check | INSPECTION | Crew checks visible leaks when restoring service. | Prevents damage after move-in. |
| moveutilityops.billing.final_bill | final bill | RECORD | Final bill includes usage, fees, deposits, credits and forwarding address. | Settles departing customer's account. |
| moveutilityops.billing.first_bill | first bill | QUALITY_CHECK | First bill is checked for correct dates, rate, read and service address. | Catches setup errors early. |
| moveutilityops.billing.proration | proration | METHOD | Partial periods are prorated by service dates and rate rules. | Fairly allocates charges. |
| moveutilityops.billing.forwarding | forwarding address | RECORD | Move-out captures forwarding email/mail address for final bill and refund. | Allows final communication. |
| moveutilityops.communication.confirmation | service confirmation | METHOD | Customer receives confirmation number, dates, requirements and contact path. | Reduces uncertainty. |
| moveutilityops.communication.access_instruction | access instruction | METHOD | Customer receives instructions for meter access, appointment window or valve location. | Improves field completion. |
| moveutilityops.communication.denial | denial notice | RECORD | Denial explains reason, missing proof, deposit, debt or policy barrier. | Makes negative outcome reviewable. |
| moveutilityops.records.case_file | case file | RECORD | Application, identity proof, reads, field orders, billing and notes are linked. | Creates audit trail. |
| moveutilityops.records.crm_note | CRM note | RECORD | Staff notes summarize decision, exceptions, promises and next steps. | Keeps call center aligned. |
| moveutilityops.records.document_retention | document retention | CONSTRAINT | Move records are retained by billing and privacy policy. | Supports disputes and audits. |
| moveutilityops.qa.duplicate_account | duplicate account check | QUALITY_CHECK | System checks whether customer or premise already has active account. | Prevents duplicate billing. |
| moveutilityops.qa.address_match | address match | QUALITY_CHECK | GIS, meter, parcel and postal address are compared. | Avoids wrong-premise service. |
| moveutilityops.qa.pending_orders | pending order check | QUALITY_CHECK | Staff checks open shutoff, repair, meter or complaint orders before move completion. | Prevents conflicting workflows. |
| moveutilityops.reporting.move_volume | move volume report | MEASUREMENT | Reports track starts, stops, transfers, exceptions and aging. | Shows workload and seasonal demand. |
| moveutilityops.reporting.error_trend | error trend | MODEL | Trends reveal address, read, deposit or identity process weaknesses. | Turns move errors into process fixes. |
| moveutilityops.review.process_improvement | process improvement | METHOD | Regular review updates forms, portal prompts, scripts and field routing. | Reduces repeat move-service defects. |

