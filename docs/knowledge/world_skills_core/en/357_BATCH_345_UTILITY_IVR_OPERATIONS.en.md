# BATCH 345: Utility IVR Operations

**KnowledgeUnits:** 44  
**Namespace:** `ivrops.*`  
**Scope:** menu design, authentication, outage prompts, payments, callbacks, recordings, failover and metrics.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| ivrops.design.call_reason | call reason map | MODEL | IVR design maps common reasons such as outage, billing, payment, move, appointment and emergency. | Builds menus around customer demand. |
| ivrops.design.menu_depth | menu depth | CONSTRAINT | Menu depth limits how many levels a caller must navigate. | Reduces abandonment. |
| ivrops.design.plain_language | plain language prompt | METHOD | Prompts use short familiar language and avoid internal utility jargon. | Helps stressed callers understand options. |
| ivrops.design.language_choice | language choice | METHOD | Language choice is offered early and supports required service languages. | Improves accessibility. |
| ivrops.design.accessibility | accessibility route | SAFETY_RULE | IVR offers operator or accessible route for callers unable to use menus. | Protects service access. |
| ivrops.authentication.account_lookup | account lookup | METHOD | Caller can identify account by account number, phone, address or other approved path. | Speeds routing to account-specific service. |
| ivrops.authentication.risk_level | authentication risk level | MODEL | Risk level determines what actions require stronger authentication. | Keeps low-risk updates easy and sensitive tasks protected. |
| ivrops.authentication.pin | PIN verification | SAFETY_RULE | PIN or shared secret may verify caller for billing or profile actions. | Reduces unauthorized access. |
| ivrops.authentication.failed_attempt | failed attempt control | CONSTRAINT | Failed authentication attempts trigger retry limits or live-agent transfer. | Prevents brute-force and caller frustration. |
| ivrops.outage.outage_prompt | outage prompt | METHOD | Outage prompt lets callers report outage or hear known outage status. | Reduces agent load during events. |
| ivrops.outage.known_outage_match | known outage match | MODEL | Caller address or phone can match known outage records. | Gives relevant restoration information. |
| ivrops.outage.new_report | new outage report | RECORD | New outage report captures account, location, symptoms, hazards and callback number. | Feeds outage management. |
| ivrops.outage.hazard_transfer | hazard transfer | SAFETY_RULE | Wires down, gas smell, flooding or medical risk can route immediately to live/emergency handling. | Protects life safety. |
| ivrops.outage.etr_prompt | ETR prompt | METHOD | Estimated restoration prompt states confidence and last update time. | Avoids stale or over-precise promises. |
| ivrops.billing.balance_prompt | balance prompt | METHOD | Balance prompt states amount due, due date, payment status and dispute route. | Enables simple self-service. |
| ivrops.billing.high_bill_route | high bill route | METHOD | High bill callers route to leak, meter, usage or dispute options. | Sends exceptions to suitable workflow. |
| ivrops.payments.payment_flow | payment flow | METHOD | Payment flow confirms account, amount, method, fee, date and confirmation number. | Prevents misapplied payments. |
| ivrops.payments.pci_boundary | PCI boundary | SAFETY_RULE | Card entry and recording controls keep payment data out of agent and call recordings. | Reduces compliance risk. |
| ivrops.payments.failed_payment | failed payment | FAILURE_MODE | Failed IVR payment reports reason category and next action without exposing sensitive data. | Helps caller recover. |
| ivrops.payments.arrangement_route | arrangement route | METHOD | Payment arrangement route checks eligibility or transfers to specialist queue. | Supports delinquency management. |
| ivrops.callback.callback_offer | callback offer | METHOD | Callback is offered when wait time or queue rules qualify. | Reduces hold time burden. |
| ivrops.callback.number_confirm | number confirmation | QUALITY_CHECK | Callback number is repeated or confirmed before saving. | Avoids missed return calls. |
| ivrops.callback.priority | callback priority | MODEL | Callback priority uses queue, customer risk, service type and time sensitivity. | Manages scarce agent capacity. |
| ivrops.callback.expiry | callback expiry | CONSTRAINT | Callback requests expire after defined attempts or time window. | Keeps queues accurate. |
| ivrops.recording.recording_policy | recording policy | CONSTRAINT | Recording policy states which calls are recorded and which data is masked. | Supports compliance and quality. |
| ivrops.recording.consent_prompt | consent prompt | METHOD | Consent or notification prompt plays where required. | Meets jurisdictional rules. |
| ivrops.recording.retention | recording retention | CONSTRAINT | Recordings are retained by category, risk and legal hold status. | Controls evidence and privacy. |
| ivrops.recording.search | recording search | METHOD | Search uses call ID, account, time, ANI, agent or queue metadata. | Supports disputes and QA. |
| ivrops.routing.skill_queue | skill queue | METHOD | Routing sends callers to billing, outage, move service, language or specialist skills. | Improves first contact resolution. |
| ivrops.routing.after_hours | after-hours route | METHOD | After-hours routing separates emergency, outage, payment and callback options. | Maintains service outside business hours. |
| ivrops.routing.overflow | overflow route | METHOD | Overflow route sends calls to backup queue, contractor or message service. | Protects service during surges. |
| ivrops.routing.vip_sensitive | sensitive customer route | METHOD | Sensitive accounts can route with additional care while preserving policy fairness. | Supports critical customer handling. |
| ivrops.failover.provider_failover | provider failover | METHOD | IVR has backup carrier, hosted platform or manual message plan. | Keeps phone service during outages. |
| ivrops.failover.power_network | power network dependency | FAILURE_MODE | Phone system depends on power, network, carrier and contact-center tools. | Helps continuity planning. |
| ivrops.failover.emergency_message | emergency message | METHOD | Prebuilt emergency message can be activated when systems are degraded. | Gives callers minimal guidance fast. |
| ivrops.failover.manual_transfer | manual transfer | METHOD | Manual transfer plan lists numbers and queues for degraded IVR states. | Keeps calls moving. |
| ivrops.content.prompt_library | prompt library | RECORD | Prompt library stores approved messages, owners, dates and use cases. | Prevents improvised wording. |
| ivrops.content.prompt_update | prompt update | METHOD | Prompt changes go through draft, review, publish and test. | Reduces broken call flows. |
| ivrops.content.seasonal_message | seasonal message | METHOD | Seasonal prompts cover storms, conservation, shutoff moratoriums or billing cycles. | Keeps IVR aligned with current operations. |
| ivrops.qa.test_call | test call | QUALITY_CHECK | Test calls verify menu path, transfers, payment, outage status and language options. | Catches failures before customers. |
| ivrops.qa.transcript_review | transcript review | QUALITY_CHECK | Speech recognition transcripts are reviewed for frequent misunderstood phrases. | Improves menu recognition. |
| ivrops.metrics.containment | containment rate | MEASUREMENT | Containment rate measures calls resolved without agent transfer. | Shows self-service value. |
| ivrops.metrics.abandonment | abandonment rate | MEASUREMENT | Abandonment rate tracks callers leaving before completion or agent contact. | Signals friction and staffing mismatch. |
| ivrops.metrics.failure_reason | failure reason | MEASUREMENT | Failure reasons classify authentication, transfer, payment, speech or system errors. | Guides IVR improvement. |
