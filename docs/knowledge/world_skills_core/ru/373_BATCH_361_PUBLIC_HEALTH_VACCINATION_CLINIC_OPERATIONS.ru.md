# BATCH 361: Public Health Vaccination Clinic Operations

**KnowledgeUnits:** 44  
**Namespace:** `vaxclinicops.*`  
**Scope:** appointment flow, eligibility, consent, cold chain, documentation, observation and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| vaxclinicops.planning.clinic_id | clinic ID | RECORD | Clinic ID links site, date, vaccine type, staff, target group and reporting unit. | Creates operational reference. |
| vaxclinicops.planning.site_layout | site layout | METHOD | Layout separates entry, registration, screening, vaccination, observation and exit. | Keeps flow safe. |
| vaxclinicops.planning.capacity | capacity model | MODEL | Capacity uses vaccinators, observation seats, registration desks, supply and hours. | Prevents overbooking. |
| vaxclinicops.planning.accessibility | accessibility plan | METHOD | Plan covers ramps, seating, language, sensory needs, mobility and transport. | Keeps clinic inclusive. |
| vaxclinicops.appointment.slot | appointment slot | RECORD | Slot records person, vaccine, time, dose need and status. | Manages demand. |
| vaxclinicops.appointment.walkin | walk-in rule | CONSTRAINT | Walk-ins are accepted only if supply, eligibility and staffing allow. | Protects scheduled flow. |
| vaxclinicops.appointment.reminder | reminder | METHOD | Reminder includes time, site, ID, consent, contraindication warning and reschedule path. | Reduces no-shows. |
| vaxclinicops.appointment.no_show | no-show process | METHOD | No-show frees slot, triggers waitlist or follow-up. | Reduces wasted supply. |
| vaxclinicops.eligibility.target_group | target group | CONSTRAINT | Eligibility may depend on age, risk, occupation, residence or outbreak exposure. | Applies public health rules. |
| vaxclinicops.eligibility.dose_interval | dose interval | CONSTRAINT | Dose interval and prior vaccine history are checked before administration. | Prevents wrong timing. |
| vaxclinicops.eligibility.contra_screen | contraindication screen | SAFETY_RULE | Screening checks allergy, illness, prior reaction and product-specific warnings. | Protects patients. |
| vaxclinicops.eligibility.deferral | deferral | METHOD | Deferral records reason, guidance and future eligibility path. | Handles not-yet cases. |
| vaxclinicops.consent.consent_form | consent form | RECORD | Consent records patient/guardian agreement, vaccine, date and required acknowledgments. | Documents authorization. |
| vaxclinicops.consent.guardian | guardian consent | SAFETY_RULE | Minors or dependent adults require proper guardian or legal authority. | Protects legal validity. |
| vaxclinicops.consent.language | language support | METHOD | Consent information is provided in understandable language where possible. | Supports informed choice. |
| vaxclinicops.consent.decline | decline record | RECORD | Decline records refusal if required without coercive pressure. | Supports reporting and follow-up. |
| vaxclinicops.coldchain.receiving | vaccine receiving | METHOD | Receiving records lot, quantity, temperature, time and condition. | Starts cold-chain custody. |
| vaxclinicops.coldchain.storage | storage condition | SAFETY_RULE | Storage follows product temperature, light and handling rules. | Preserves potency. |
| vaxclinicops.coldchain.transport | transport log | RECORD | Transport logs cooler, probes, route, times and temperature. | Supports mobile clinics. |
| vaxclinicops.coldchain.excursion | temperature excursion | FAILURE_MODE | Excursion quarantines doses until viability decision. | Prevents compromised vaccine use. |
| vaxclinicops.inventory.lot_control | lot control | RECORD | Lot, expiration and dose count are linked to every administered dose. | Enables recall and reporting. |
| vaxclinicops.inventory.open_vial | open vial rule | CONSTRAINT | Open vial handling follows product time limit and wastage rule. | Reduces unsafe use. |
| vaxclinicops.inventory.wastage | wastage record | RECORD | Wastage records reason, lot, quantity and approver. | Supports supply accountability. |
| vaxclinicops.inventory.reconciliation | reconciliation | QUALITY_CHECK | End-of-day doses reconcile received, administered, wasted and transferred. | Detects inventory errors. |
| vaxclinicops.registration.checkin | check-in | METHOD | Check-in verifies appointment, identity, eligibility and contact details. | Starts patient flow. |
| vaxclinicops.registration.data_minimum | minimum data | CONSTRAINT | Clinic collects only required demographic, eligibility and reporting fields. | Reduces privacy burden. |
| vaxclinicops.registration.insurance | insurance capture | METHOD | Insurance may be captured for administration billing where allowed. | Supports finance without blocking access. |
| vaxclinicops.registration.queue | queue control | METHOD | Queue control uses signs, staff, appointments and accessibility priority. | Prevents crowding. |
| vaxclinicops.administration.vaccinator | vaccinator credential | SAFETY_RULE | Vaccinator must have authorized scope, training and supervision. | Ensures safe administration. |
| vaxclinicops.administration.product_check | product check | QUALITY_CHECK | Product, dose, route, lot and patient are checked before administration. | Prevents wrong vaccine errors. |
| vaxclinicops.administration.site | administration site | RECORD | Administration site and route are documented when required. | Supports clinical record. |
| vaxclinicops.administration.sharps | sharps safety | SAFETY_RULE | Sharps disposal and needlestick protocol are active onsite. | Protects staff and public. |
| vaxclinicops.observation.wait_period | observation period | CONSTRAINT | Observation time follows product and risk guidance. | Detects immediate reactions. |
| vaxclinicops.observation.reaction | adverse reaction | SAFETY_RULE | Reaction protocol routes to first aid, EMS and reporting. | Protects patient safety. |
| vaxclinicops.observation.seating | observation seating | METHOD | Seating keeps observed patients visible and accessible. | Improves monitoring. |
| vaxclinicops.observation.release | release process | METHOD | Release provides vaccine record, next-dose guidance and side-effect information. | Completes visit. |
| vaxclinicops.documentation.registry | registry entry | RECORD | Dose is reported to immunization registry or required public health system. | Maintains official record. |
| vaxclinicops.documentation.card | vaccination card | RECORD | Patient receives proof with product, lot, date and next action. | Supports continuity. |
| vaxclinicops.documentation.correction | correction process | METHOD | Data errors are corrected through controlled registry or record workflow. | Keeps records accurate. |
| vaxclinicops.reporting.daily | daily report | MEASUREMENT | Daily report counts administered, wasted, demographics, inventory and incidents. | Supports public health management. |
| vaxclinicops.qa.chart_audit | chart audit | QUALITY_CHECK | Sample records check eligibility, consent, lot, registry and observation fields. | Improves compliance. |
| vaxclinicops.security.crowd | crowd safety | SAFETY_RULE | Security plan covers crowding, disruptive visitors, traffic and emergency exits. | Keeps site safe. |
| vaxclinicops.closeout.site_close | site closeout | METHOD | Closeout reconciles inventory, cleans site, secures records and briefs staff. | Ends clinic safely. |
| vaxclinicops.review.after_action | after-action review | METHOD | Review captures throughput, equity, wastage, incidents and access barriers. | Improves next clinic. |
