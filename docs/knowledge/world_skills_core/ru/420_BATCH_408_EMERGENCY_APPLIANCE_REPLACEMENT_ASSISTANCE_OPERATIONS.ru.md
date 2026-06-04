# BATCH 408: Emergency Appliance Replacement Assistance Operations

**KnowledgeUnits:** 44  
**Namespace:** `appliancereplaceops.*`  
**Scope:** intake, eligibility, damage proof, vendor coordination, delivery, installation and warranty.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| appliancereplaceops.intake.request_source | request source | RECORD | Source records caseworker, survivor center, housing agency, hotline or partner referral. | Shows entry path. |
| appliancereplaceops.intake.household | household profile | RECORD | Profile captures residents, address, displacement, income, vulnerabilities and contact. | Supports eligibility. |
| appliancereplaceops.intake.appliance_type | appliance type | RECORD | Type distinguishes refrigerator, stove, washer, dryer, freezer, heater or accessibility appliance. | Defines need. |
| appliancereplaceops.intake.urgency | urgency model | MODEL | Urgency weighs food safety, medical storage, children, elder care, accessibility and habitability. | Prioritizes cases. |
| appliancereplaceops.eligibility.criteria | eligibility criteria | CONSTRAINT | Criteria define disaster impact, residence, ownership/tenancy, income and duplication of benefits. | Preserves fairness. |
| appliancereplaceops.eligibility.tenant_owner | tenant owner rule | CONSTRAINT | Rule clarifies landlord responsibility, tenant property and lease-related limitations. | Avoids wrong payment. |
| appliancereplaceops.eligibility.duplicate_benefit | duplicate benefit check | QUALITY_CHECK | Check compares insurance, FEMA, nonprofit, warranty and landlord coverage. | Prevents duplication. |
| appliancereplaceops.eligibility.exception | exception record | RECORD | Exception records special medical, accessibility or safety need and approval. | Allows flexibility. |
| appliancereplaceops.damage.photo_proof | photo proof | RECORD | Photos document damaged appliance, serial plate, room, waterline or fire impact when allowed. | Supports decision. |
| appliancereplaceops.damage.inspection_note | inspection note | RECORD | Note records field verification, unsafe condition, appliance age and feasibility. | Validates claim. |
| appliancereplaceops.damage.disposal_status | disposal status | RECORD | Status records whether damaged unit remains, was removed or requires pickup. | Plans delivery. |
| appliancereplaceops.damage.repair_vs_replace | repair replace model | MODEL | Model weighs safety, cost, availability, warranty and recovery timeline. | Chooses path. |
| appliancereplaceops.spec.size | size specification | RECORD | Spec captures dimensions, hookups, capacity, fuel type, voltage and doorway constraints. | Prevents mismatch. |
| appliancereplaceops.spec.accessibility | accessibility spec | RECORD | Accessibility notes controls, height, visibility, mobility access and caregiver use. | Improves usability. |
| appliancereplaceops.spec.energy | energy requirement | CONSTRAINT | Appliance must match electrical, gas, venting and local installation requirements. | Prevents hazard. |
| appliancereplaceops.spec.substitution | substitution rule | METHOD | Substitution uses approved equivalent when exact model is unavailable. | Keeps service moving. |
| appliancereplaceops.vendor.vendor_roster | vendor roster | RECORD | Roster lists approved vendors, items, prices, delivery area, installation ability and contacts. | Coordinates supply. |
| appliancereplaceops.vendor.quote | quote record | RECORD | Quote records model, price, delivery, installation, disposal, taxes and expiration. | Supports approval. |
| appliancereplaceops.vendor.order | purchase order | RECORD | Order links household, appliance, funding source, vendor and delivery terms. | Starts fulfillment. |
| appliancereplaceops.vendor.stock_check | stock check | QUALITY_CHECK | Stock check confirms availability, lead time, substitutions and backorder risk. | Avoids delay. |
| appliancereplaceops.delivery.schedule | delivery schedule | RECORD | Schedule records date, window, address, contact, access and old-unit pickup. | Plans handoff. |
| appliancereplaceops.delivery.access_check | access check | METHOD | Check covers stairs, elevator, driveway, doorway, pets, debris and resident availability. | Prevents failed delivery. |
| appliancereplaceops.delivery.failed_delivery | failed delivery | RECORD | Failure records no access, wrong size, unsafe install, weather or vendor issue. | Enables reschedule. |
| appliancereplaceops.delivery.confirmation | delivery confirmation | RECORD | Confirmation captures appliance delivered, condition, resident signature and photos if allowed. | Closes delivery. |
| appliancereplaceops.install.install_need | installation need | RECORD | Need records hookup, leveling, venting, water line, gas technician or electrician. | Plans safe setup. |
| appliancereplaceops.install.licensed_work | licensed work rule | SAFETY_RULE | Gas, electrical or code-sensitive work uses qualified providers where required. | Prevents unsafe install. |
| appliancereplaceops.install.functional_test | functional test | QUALITY_CHECK | Test checks startup, leaks, cooling/heating, drainage and error messages. | Confirms usability. |
| appliancereplaceops.install.user_brief | user briefing | METHOD | Resident receives basic use, safety, warranty and maintenance information. | Reduces problems. |
| appliancereplaceops.disposal.old_unit_pickup | old unit pickup | METHOD | Pickup removes damaged appliance when safe, authorized and included. | Clears hazard. |
| appliancereplaceops.disposal.recycling | recycling path | METHOD | Recycling separates refrigerant, metal, electronics or hazardous parts according to rules. | Supports compliance. |
| appliancereplaceops.disposal.disposal_proof | disposal proof | RECORD | Proof records vendor, date, item and disposal/recycling route. | Supports audit. |
| appliancereplaceops.disposal.contaminated | contaminated appliance | SAFETY_RULE | Mold, floodwater or fire-contaminated units follow handling and PPE precautions. | Protects crews. |
| appliancereplaceops.warranty.warranty_record | warranty record | RECORD | Warranty captures model, serial, start date, vendor, coverage and resident copy. | Supports future service. |
| appliancereplaceops.warranty.claim_path | claim pathway | METHOD | Claim path explains who contacts vendor, manufacturer or program for defects. | Handles failures. |
| appliancereplaceops.warranty.service_call | service call | RECORD | Service call records defect, appointment, provider, outcome and cost responsibility. | Tracks follow-up. |
| appliancereplaceops.warranty.resident_packet | resident packet | RECORD | Packet includes receipt, warranty, safety notes and program contact. | Gives clarity. |
| appliancereplaceops.finance.funding_source | funding source | RECORD | Funding source links grant, nonprofit, insurance gap or public program. | Supports accounting. |
| appliancereplaceops.finance.approval | approval record | RECORD | Approval records eligibility, amount, approver, vendor and conditions. | Controls spending. |
| appliancereplaceops.finance.invoice_reconcile | invoice reconciliation | QUALITY_CHECK | Invoice checks order, delivery, installation, disposal and approved price. | Prevents overpayment. |
| appliancereplaceops.records.case_log | case log | RECORD | Log stores intake, proof, specs, vendor, delivery, installation, warranty and closeout. | Creates continuity. |
| appliancereplaceops.metrics.delivery_time | delivery time | MEASUREMENT | Metric measures approval to delivered and installed appliance. | Shows delay. |
| appliancereplaceops.metrics.failed_rate | failed delivery rate | MEASUREMENT | Rate tracks failed deliveries by reason and vendor. | Improves planning. |
| appliancereplaceops.metrics.households_served | households served | MEASUREMENT | Count tracks households and appliance types completed. | Shows output. |
| appliancereplaceops.review.after_action | after-action review | METHOD | Review captures eligibility, sizing, vendor lead times, installation safety and warranty lessons. | Improves future aid. |
