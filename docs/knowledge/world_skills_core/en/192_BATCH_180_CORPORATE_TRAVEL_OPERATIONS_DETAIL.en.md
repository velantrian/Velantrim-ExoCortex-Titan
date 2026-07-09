# BATCH_180 — Corporate Travel Operations Detail
# world_skills_core · source: world_skills_core:batch_180:corporate_travel_operations_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| travelops.policy.travel_policy | Corporate travel policy | invariant | Policy defines allowed booking channels, cabin class, hotels, meals, approvals, exceptions and duty of care. | rules before booking |
| travelops.policy.pretrip_approval | Pre-trip approval | invariant | Approval confirms business purpose, budget, dates, destination, traveler and policy compliance. | spend gate |
| travelops.policy.exception_request | Travel exception request | variant | Exception request records why traveler needs nonstandard fare, hotel, route or supplier. | controlled flexibility |
| travelops.policy.preferred_supplier | Preferred travel supplier | variant | Preferred suppliers support negotiated rates, reporting, service levels and traveler tracking. | leverage buying power |
| travelops.policy.booking_window | Advance booking window | variant | Booking window encourages purchase far enough ahead to reduce cost and availability risk. | timing affects fare |
| travelops.policy.trip_purpose_code | Trip purpose code | invariant | Purpose code classifies travel for reporting, tax, project, client or compliance needs. | why travel happened |
| travelops.profile.traveler_profile | Traveler profile | invariant | Profile stores name, contacts, documents, loyalty IDs, preferences and emergency data. | faster accurate booking |
| travelops.profile.passport_expiry | Passport expiry check | invariant | Expiry check flags passport validity risk before international booking. | document readiness |
| travelops.profile.visa_requirement | Visa requirement flag | variant | Flag indicates destination may require visa, permit or entry authorization. | avoid denied boarding |
| travelops.profile.accessibility_need | Traveler accessibility need | variant | Need records assistance, seating, mobility, accommodation or communication requirement. | inclusive travel |
| travelops.profile.risk_contact | Emergency contact | invariant | Contact supports traveler assistance during disruption, illness or security event. | duty of care |
| travelops.profile.data_privacy | Traveler data privacy | invariant | Privacy controls limit access to personal documents, health notes and location data. | sensitive profile |
| travelops.booking.air_booking | Corporate air booking | invariant | Booking selects flight based on policy, schedule, fare, flexibility and traveler need. | route plus rules |
| travelops.booking.hotel_booking | Corporate hotel booking | invariant | Hotel booking considers rate, location, safety, cancellation, amenities and policy caps. | stay control |
| travelops.booking.rail_booking | Corporate rail booking | variant | Rail booking may replace air or car depending on time, cost, policy and geography. | mode choice |
| travelops.booking.car_rental | Car rental booking | variant | Rental booking checks vehicle class, insurance rules, driver eligibility and pickup logistics. | ground mobility |
| travelops.booking.unused_ticket | Unused ticket credit | invariant | Credit tracking preserves value from cancelled or changed air tickets for future use. | avoid lost money |
| travelops.booking.group_travel | Group travel coordination | variant | Group travel coordinates travelers, room blocks, shared transport, manifests and changes. | many travelers, one plan |
| travelops.disruption.flight_disruption | Flight disruption workflow | invariant | Workflow handles delay, cancellation, missed connection, rebooking, hotel and traveler notification. | recover the trip |
| travelops.disruption.traveler_locator | Traveler locator | invariant | Locator identifies travelers in affected region or route during disruption or crisis. | know who is where |
| travelops.disruption.after_hours_support | After-hours travel support | variant | Support provides booking and emergency help outside normal business hours. | travel never sleeps |
| travelops.disruption.weather_waiver | Airline waiver tracking | variant | Waiver tracking helps change travel without fees under airline disruption policy. | use available flexibility |
| travelops.disruption.medical_emergency | Traveler medical emergency workflow | invariant | Workflow routes traveler to assistance provider, manager, insurance and emergency contacts under policy. | duty of care response |
| travelops.disruption.security_alert | Destination security alert | variant | Alert informs travelers and approvers about risk, restrictions or assistance steps. | situational awareness |
| travelops.expense.expense_report | Travel expense report | invariant | Report claims trip costs with receipts, coding, policy checks and approvals. | close spend |
| travelops.expense.receipt_capture | Receipt capture | invariant | Capture preserves proof of purchase, tax, vendor, date, amount and currency. | evidence for reimbursement |
| travelops.expense.per_diem | Per diem | variant | Per diem uses fixed allowance rules by location, date, meal or overnight status. | simpler meal accounting |
| travelops.expense.currency_conversion | Currency conversion | invariant | Conversion records exchange rate source, transaction amount and reimbursement currency. | cross-border accounting |
| travelops.expense.policy_violation | Travel expense violation | invariant | Violation flags out-of-policy spend, missing receipt, late submission or nonbusiness item. | control leakage |
| travelops.expense.corporate_card_match | Corporate card match | invariant | Card match links transaction feed to expense line and trip purpose. | reduce manual entry |
| travelops.duty.risk_rating | Destination risk rating | variant | Risk rating grades destination by security, health, political, environmental or transport factors. | pretrip awareness |
| travelops.duty.check_in | Traveler check-in | variant | Check-in confirms traveler safety during disruption, high-risk trip or emergency. | contact loop |
| travelops.duty.assistance_provider | Travel assistance provider | variant | Provider offers emergency support, medical referral, evacuation coordination or security advice. | specialized support |
| travelops.duty.incident_record | Travel incident record | invariant | Record captures event, traveler, location, actions, contacts, costs and follow-up. | learn and evidence |
| travelops.duty.policy_acknowledgment | Travel policy acknowledgment | invariant | Acknowledgment confirms traveler received relevant rules, safety expectations and responsibilities. | shared responsibility |
| travelops.duty.repatriation_plan | Repatriation plan | variant | Plan coordinates return travel from crisis location under business continuity or safety decision. | get traveler home |
| travelops.reporting.spend_report | Travel spend report | invariant | Report groups spend by supplier, route, department, traveler, purpose and policy status. | manage travel budget |
| travelops.reporting.supplier_performance | Supplier performance report | invariant | Report tracks rates, service, disruptions, refunds, complaints and contract value. | manage vendors |
| travelops.reporting.carbon_report | Travel carbon report | variant | Carbon report estimates travel emissions by route, mode, distance and methodology. | sustainability view |
| travelops.reporting.compliance_rate | Travel compliance rate | invariant | Compliance rate measures bookings and expenses following travel policy. | behavior metric |
| travelops.reporting.savings_tracking | Travel savings tracking | variant | Tracking estimates savings from negotiated rates, advance booking, avoided trips or unused ticket use. | value of program |
| travelops.close.trip_closeout | Trip closeout | invariant | Closeout confirms travel complete, expenses submitted, unused tickets captured and incidents resolved. | finish the trip |
| travelops.close.records_retention | Travel records retention | invariant | Retention defines storage period for approvals, itineraries, expenses, receipts and incident records. | audit readiness |
| travelops.close.audit_sample | Travel audit sample | variant | Sample reviews trips for policy, receipts, approvals, duplicates, personal spend and vendor patterns. | targeted control |
