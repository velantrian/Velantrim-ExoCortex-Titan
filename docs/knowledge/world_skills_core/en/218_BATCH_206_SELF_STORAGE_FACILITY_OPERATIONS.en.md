# BATCH_206 — Self-Storage Facility Operations Detail
# world_skills_core · source: world_skills_core:batch_206:self_storage_facility_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| storageops.rental.unit_inventory | Storage unit inventory | invariant | Inventory lists unit number, size, type, status, lock state, rate and features. | know rentable space |
| storageops.rental.unit_status | Storage unit status | invariant | Status shows vacant, reserved, rented, delinquent, overlocked, maintenance or auction hold. | control availability |
| storageops.rental.reservation | Storage unit reservation | invariant | Reservation holds unit size, price, customer, move-in date and expiration. | promise space |
| storageops.rental.lease_agreement | Storage lease agreement | invariant | Agreement defines rent, access, prohibited items, lien rules, insurance and termination. | legal frame |
| storageops.rental.move_in | Storage move-in | invariant | Move-in verifies identity, lease, payment, lock, gate code and unit condition. | start tenancy |
| storageops.access.gate_code | Storage gate code | invariant | Code controls customer access and logs entry to facility. | access identity |
| storageops.access.access_hours | Facility access hours | invariant | Hours define when customers may enter building, gate, office or unit area. | time boundary |
| storageops.access.lock_check | Storage lock check | invariant | Check confirms rented units are customer-locked and vacant units are company-controlled. | security basics |
| storageops.access.tailgate_alert | Storage tailgate alert | variant | Alert flags vehicle or person entering behind authorized customer without credential. | site security |
| storageops.access.access_suspend | Access suspension | invariant | Suspension restricts gate access due to delinquency, legal hold, safety or account issue. | enforce lease |
| storageops.account.customer_profile | Storage customer profile | invariant | Profile stores identity, contacts, authorized users, payment method and communication preference. | account anchor |
| storageops.account.authorized_user | Authorized storage user | variant | User is allowed by tenant to access or manage unit under defined limits. | delegated access |
| storageops.account.rate_change | Storage rate change | invariant | Change updates rent with required notice, effective date and account record. | pricing control |
| storageops.account.insurance_option | Storage insurance option | variant | Option records tenant coverage, protection plan or waiver where offered. | risk transfer |
| storageops.account.autopay | Storage autopay | variant | Autopay stores payment authorization, schedule, failure handling and cancellation. | reduce delinquency |
| storageops.payment.rent_charge | Storage rent charge | invariant | Charge applies rent, fees, taxes, discounts and due date to account. | billing basis |
| storageops.payment.late_fee | Storage late fee | invariant | Fee applies according to lease, grace period and jurisdiction rules. | delinquency signal |
| storageops.payment.payment_posting | Payment posting | invariant | Posting records amount, method, date, account, receipt and allocation. | account accuracy |
| storageops.payment.refund_credit | Storage refund or credit | variant | Credit adjusts overpayment, move-out proration, service issue or approved correction. | fair account |
| storageops.payment.chargeback_case | Storage chargeback case | variant | Case gathers lease, receipts, access logs and communication to respond to dispute. | defend payment |
| storageops.delinquency.delinquency_notice | Delinquency notice | invariant | Notice informs tenant of overdue balance, fees, access impact and cure deadline. | required communication |
| storageops.delinquency.overlock | Unit overlock | invariant | Overlock adds company lock to restrict access after delinquency or legal trigger. | secure collateral |
| storageops.delinquency.lien_timeline | Storage lien timeline | variant | Timeline tracks statutory notices, publication, auction and redemption deadlines. | lawful process |
| storageops.delinquency.payment_plan | Storage payment plan | variant | Plan documents agreed payments, access rules and failure consequences. | controlled exception |
| storageops.delinquency.auction_hold | Auction hold | invariant | Hold stops sale due to payment, bankruptcy, legal issue, military protection or management review. | prevent wrongful sale |
| storageops.auction.inventory_walkthrough | Auction inventory walkthrough | invariant | Walkthrough documents visible contents without unnecessary disturbance, with photos and witness if required. | auction evidence |
| storageops.auction.auction_listing | Storage auction listing | variant | Listing describes unit, photos, terms, date, location and bidding rules. | transparent sale |
| storageops.auction.bidder_registration | Auction bidder registration | variant | Registration records bidder identity, terms acceptance, deposit and tax status if needed. | controlled sale |
| storageops.auction.sale_result | Storage auction sale result | invariant | Result records winning bid, payment, buyer, cleanup deadline and tenant account application. | close auction |
| storageops.auction.personal_record_handling | Personal record handling | invariant | Handling protects sensitive documents, photos or personal data found during auction cleanup. | privacy after sale |
| storageops.facility.daily_walk | Storage facility daily walk | invariant | Walk checks gates, doors, locks, cameras, lights, leaks, pests, trash and safety hazards. | eyes on property |
| storageops.facility.unit_condition | Unit condition report | invariant | Report records cleanliness, damage, odor, moisture, door, floor and wall state. | rentable readiness |
| storageops.facility.climate_control | Climate control monitoring | variant | Monitoring tracks temperature, humidity, alarms and HVAC function for climate units. | protect stored goods |
| storageops.facility.pest_monitoring | Storage pest monitoring | invariant | Monitoring checks traps, droppings, nests, food waste and entry points. | prevent infestation |
| storageops.facility.maintenance_ticket | Storage maintenance ticket | invariant | Ticket records repair need, unit, priority, vendor, completion and tenant impact. | fix facility |
| storageops.security.camera_review | Storage camera review | variant | Review examines time window for incident, access dispute, theft claim or safety issue. | evidence support |
| storageops.security.incident_report | Storage incident report | invariant | Report documents break-in, injury, fire, water leak, dispute, vandalism or suspicious activity. | formal record |
| storageops.security.lock_cut | Lock cut procedure | invariant | Procedure controls authorized lock removal with reason, witness, photos and chain of custody. | high-risk action |
| storageops.security.prohibited_items | Prohibited storage items | invariant | Prohibition covers hazardous, illegal, perishable, living, stolen or nuisance materials. | reduce risk |
| storageops.security.emergency_access | Emergency unit access | variant | Access may occur for fire, leak, odor, hazard or legal order with documentation. | protect property |
| storageops.moveout.notice_to_vacate | Notice to vacate | invariant | Notice records tenant intent, date, balance, access and move-out requirements. | plan vacancy |
| storageops.moveout.moveout_inspection | Storage move-out inspection | invariant | Inspection verifies empty unit, damage, lock removal, cleanliness and final charges. | return to inventory |
| storageops.metrics.storage_kpi | Self-storage KPI | variant | KPI tracks occupancy, delinquency, move-ins, move-outs, rate growth, auctions and incidents. | manage facility |
| storageops.continuity.gate_outage | Storage gate outage procedure | invariant | Procedure defines manual access, customer notice, security patrol and repair escalation. | keep site usable |
