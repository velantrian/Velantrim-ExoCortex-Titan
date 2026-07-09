# BATCH 381: Emergency Volunteer Donations Hotline Operations

**KnowledgeUnits:** 44  
**Namespace:** `donationhotlineops.*`  
**Scope:** offer intake, scripts, routing, CRM notes, fraud flags, callbacks and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| donationhotlineops.intake.call_id | call ID | RECORD | Call ID links caller, offer type, time, channel, agent and outcome. | Tracks hotline work. |
| donationhotlineops.intake.offer_type | offer type | RECORD | Type distinguishes volunteer time, goods, cash, services, equipment or space. | Routes correctly. |
| donationhotlineops.intake.caller_contact | caller contact | RECORD | Contact records name, organization, phone, email, location and callback preference. | Enables follow-up. |
| donationhotlineops.intake.urgency | urgency | MODEL | Urgency reflects perishable goods, scarce skills, mission need and timing. | Prioritizes handling. |
| donationhotlineops.script.opening | opening script | METHOD | Opening explains hotline purpose, privacy and current priority needs. | Sets caller expectation. |
| donationhotlineops.script.accepted | accepted-offer script | METHOD | Script captures details and explains next review or deployment step. | Keeps intake consistent. |
| donationhotlineops.script.decline | decline script | METHOD | Decline script thanks caller and explains why offer is not usable now. | Preserves goodwill. |
| donationhotlineops.script.safety | safety script | SAFETY_RULE | Agents warn against self-deployment, unsafe drop-offs or blocked roads. | Prevents response disruption. |
| donationhotlineops.volunteer.skill | volunteer skill record | RECORD | Skill record captures credentials, availability, language, transport and limits. | Supports matching. |
| donationhotlineops.volunteer.screen | screening route | METHOD | Volunteer offers route to reception center, credentialing or partner organization. | Keeps deployment controlled. |
| donationhotlineops.volunteer.spontaneous | spontaneous volunteer | MODEL | Spontaneous volunteers need structured intake before field work. | Reduces safety risk. |
| donationhotlineops.volunteer.remote | remote volunteer offer | METHOD | Remote offers cover calls, translation, data, mapping or admin tasks. | Uses help safely. |
| donationhotlineops.goods.item_detail | item detail | RECORD | Item detail records quantity, condition, packaging, location and transport needs. | Evaluates usefulness. |
| donationhotlineops.goods.acceptance | acceptance criteria | CONSTRAINT | Agents compare goods to current accepted/not-needed lists. | Avoids warehouse burden. |
| donationhotlineops.goods.perishable | perishable offer | SAFETY_RULE | Perishables require food safety, cold chain and rapid matching. | Prevents unsafe donations. |
| donationhotlineops.goods.large_offer | large offer route | METHOD | Bulk or corporate offers route to logistics/donations manager. | Handles complex offers. |
| donationhotlineops.cash.authorized_route | authorized cash route | SAFETY_RULE | Cash donors are directed only to approved finance or nonprofit channels. | Prevents fraud. |
| donationhotlineops.cash.no_card | no card handling | CONSTRAINT | Hotline should not collect payment card data unless authorized system exists. | Protects callers. |
| donationhotlineops.cash.receipt | receipt expectation | METHOD | Agents explain receipt process and official donation page. | Builds trust. |
| donationhotlineops.services.service_offer | service offer | RECORD | Services include transport, lodging, equipment, cleaning, catering or professional support. | Captures non-goods help. |
| donationhotlineops.services.vendor_check | vendor check route | METHOD | Commercial service offers route to procurement or donations review. | Separates gift from contract. |
| donationhotlineops.services.liability | liability question | CONSTRAINT | Liability, insurance and licensing questions are escalated before use. | Reduces risk. |
| donationhotlineops.routing.queue | routing queue | METHOD | Offers route to volunteer, donations, logistics, finance, procurement or public information. | Sends work to owner. |
| donationhotlineops.routing.priority | priority routing | MODEL | Priority uses mission need, scarcity, timing and safety. | Handles urgent offers first. |
| donationhotlineops.routing.partner | partner referral | METHOD | Offers unsuitable for government may route to vetted nonprofits. | Keeps goodwill productive. |
| donationhotlineops.routing.escalation | escalation | METHOD | Unclear, high-value, risky or media-sensitive offers escalate to supervisor. | Controls exceptions. |
| donationhotlineops.crm.note | CRM note | RECORD | Note records offer, script used, route, promise and next action. | Maintains continuity. |
| donationhotlineops.crm.status | status field | RECORD | Status tracks new, routed, accepted, declined, pending, completed or closed. | Shows pipeline. |
| donationhotlineops.crm.duplicate | duplicate check | QUALITY_CHECK | Duplicate checks compare caller, organization, offer and callback. | Prevents repeated work. |
| donationhotlineops.crm.privacy | privacy rule | SAFETY_RULE | Caller data is shared only with teams needing the offer. | Protects donors. |
| donationhotlineops.fraud.red_flag | fraud flag | MODEL | Flags include fee demand, phishing, suspicious charity, inflated value or pressure tactics. | Protects public and response. |
| donationhotlineops.fraud.report | fraud report | METHOD | Suspicious calls route to supervisor, legal, finance or law enforcement as policy requires. | Controls scams. |
| donationhotlineops.fraud.public_warning | public warning | METHOD | Repeated scams can trigger public information warning. | Protects donors. |
| donationhotlineops.callback.callback_task | callback task | RECORD | Task records owner, due time, reason and callback number. | Prevents missed offers. |
| donationhotlineops.callback.no_answer | no-answer process | METHOD | No-answer attempts are logged with retry or closure rule. | Keeps queue clean. |
| donationhotlineops.callback.acceptance_notice | acceptance notice | METHOD | Accepted caller receives delivery, scheduling or credentialing instructions. | Moves offer forward. |
| donationhotlineops.qa.call_review | call review | QUALITY_CHECK | Sample calls check accuracy, tone, privacy, routing and promises. | Improves hotline quality. |
| donationhotlineops.qa.script_update | script update | METHOD | Scripts update as needs, accepted lists and scams change. | Keeps guidance current. |
| donationhotlineops.metrics.call_volume | call volume | MEASUREMENT | Volume tracks calls by hour, type and outcome. | Guides staffing. |
| donationhotlineops.metrics.offer_conversion | offer conversion | MEASUREMENT | Conversion tracks offers that become deployed volunteer time or accepted goods. | Shows usefulness. |
| donationhotlineops.records.retention | retention rule | CONSTRAINT | Hotline records follow incident, privacy and donation retention rules. | Preserves audit trail. |
| donationhotlineops.closeout.pipeline_clear | pipeline clear | METHOD | Closeout resolves pending offers and transfers future donations route. | Ends hotline responsibly. |
| donationhotlineops.closeout.thank_you | donor thank-you | METHOD | Closed accepted offers receive acknowledgement and future official giving route. | Maintains donor trust. |
| donationhotlineops.review.after_action | after-action review | METHOD | Review captures scripts, routing, scams, unmet needs and staffing lessons. | Improves next activation. |
