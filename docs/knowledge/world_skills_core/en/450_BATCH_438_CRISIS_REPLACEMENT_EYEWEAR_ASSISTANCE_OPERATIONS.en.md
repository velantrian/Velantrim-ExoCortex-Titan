# BATCH 438: Crisis Replacement Eyewear Assistance Operations

**KnowledgeUnits:** 44  
**Namespace:** `eyewearassistops.*`  
**Scope:** intake, prescription proof, vendor coordination, fitting, delivery, payment and follow-up.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| eyewearassistops.intake.request_source | request source | RECORD | Source records shelter desk, clinic, school, hotline, caseworker, outreach team or self-referral. | Shows entry path. |
| eyewearassistops.intake.client_profile | client profile | RECORD | Profile captures contact, age group, language, safe contact, mobility barrier and caregiver details. | Defines support. |
| eyewearassistops.intake.loss_context | loss context | RECORD | Context notes glasses lost, damaged, inaccessible, disaster-destroyed or unsafe to use. | Frames eligibility. |
| eyewearassistops.intake.urgency | urgency model | MODEL | Urgency weighs driving, work, school, medication reading, mobility, caregiving and safety dependence. | Prioritizes cases. |
| eyewearassistops.eligibility.disaster_link | disaster link | CONTROL | Link verifies the eyewear need is caused or worsened by crisis displacement, damage or access loss. | Targets aid. |
| eyewearassistops.eligibility.program_limit | program limit | CONTROL | Limit defines covered frame, lens, repair, exam, shipping and replacement boundaries. | Controls cost. |
| eyewearassistops.eligibility.duplicate_check | duplicate check | CONTROL | Check compares client, household, prescription and vendor records for duplicate requests. | Prevents double issue. |
| eyewearassistops.prescription.proof_source | proof source | RECORD | Source records existing prescription, optometrist record, school screening, clinic note or prior lens label. | Establishes basis. |
| eyewearassistops.prescription.expiry_check | prescription expiry check | CONTROL | Check flags expired, missing, unreadable or clinically insufficient prescription proof. | Routes next step. |
| eyewearassistops.prescription.record_release | record release | PROCESS | Release obtains client consent for provider-to-program prescription confirmation. | Protects privacy. |
| eyewearassistops.prescription.exam_referral | exam referral | PROCESS | Referral schedules an eye exam when proof is unavailable or no longer valid. | Solves missing data. |
| eyewearassistops.vendor.vendor_roster | vendor roster | RECORD | Roster lists optical shops, mobile clinics, labs, repair partners, coverage terms and contacts. | Guides coordination. |
| eyewearassistops.vendor.availability_check | availability check | PROCESS | Check confirms appointment slots, frame stock, lens turnaround, repair capacity and delivery options. | Sets expectations. |
| eyewearassistops.vendor.service_order | service order | RECORD | Order captures prescription, frame choice, lens type, coverage code, price cap and expected completion. | Starts production. |
| eyewearassistops.vendor.quality_issue | quality issue | STATE | Issue flags wrong prescription, poor fit, damaged frame, late order or missing coating. | Triggers correction. |
| eyewearassistops.fitting.frame_selection | frame selection | PROCESS | Selection matches size, bridge fit, durability, available stock, age and safety needs. | Improves usable outcome. |
| eyewearassistops.fitting.measurements | measurements | RECORD | Measurements capture pupillary distance, segment height when needed, frame size and fitting notes. | Supports accurate lenses. |
| eyewearassistops.fitting.accessible_tryon | accessible try-on | PROCESS | Try-on offers seated, low-vision, child, elder or mobility-accommodated fitting support. | Reduces barriers. |
| eyewearassistops.fitting.repair_option | repair option | MODEL | Repair option weighs frame damage, lens condition, part availability, cost and timing. | Avoids unnecessary replacement. |
| eyewearassistops.lenses.lens_type | lens type | RECORD | Lens type records single vision, bifocal, progressive, reader, safety, child or special-use lens category. | Specifies order. |
| eyewearassistops.lenses.coating_limit | coating limit | CONTROL | Limit defines covered coatings such as scratch resistance or excludes nonessential upgrades. | Controls spending. |
| eyewearassistops.lenses.safety_need | safety need | RECORD | Safety need captures work, school lab, cleanup, driving or protective eyewear requirement. | Matches risk. |
| eyewearassistops.payment.voucher_issue | voucher issue | RECORD | Voucher records amount, vendor, client, expiration, allowed service and approval authority. | Controls payment. |
| eyewearassistops.payment.price_cap | price cap | CONTROL | Cap limits frame, lens, exam, repair and shipping costs according to program rules. | Protects budget. |
| eyewearassistops.payment.invoice_match | invoice match | CONTROL | Match compares invoice, voucher, service order, proof of receipt and exception approvals. | Prevents overpayment. |
| eyewearassistops.payment.donation_credit | donation credit | RECORD | Credit records donated frames, pro bono exams, lab discounts and partner contributions. | Tracks resources. |
| eyewearassistops.delivery.pickup_option | pickup option | PROCESS | Pickup option schedules client, caregiver, shelter desk or clinic collection. | Gets eyewear to user. |
| eyewearassistops.delivery.mail_delivery | mail delivery | PROCESS | Mail delivery uses verified address, tracking, privacy-safe label and fallback plan. | Supports displaced clients. |
| eyewearassistops.delivery.handoff_proof | handoff proof | RECORD | Proof records recipient, time, item count, order ID and signature or alternate confirmation. | Closes custody. |
| eyewearassistops.delivery.failed_pickup | failed pickup | STATE | Failed pickup notes missed appointment, moved shelter, unreachable client or returned shipment. | Triggers outreach. |
| eyewearassistops.privacy.minimum_data | minimum data | CONTROL | Minimum data limits shared details to what vendors and caseworkers need for service. | Reduces exposure. |
| eyewearassistops.privacy.child_guardian | child guardian control | CONTROL | Control verifies guardian consent and school or shelter release rules for minors. | Protects children. |
| eyewearassistops.privacy.record_masking | record masking | CONTROL | Masking hides sensitive health, address or case notes from public-facing tracking boards. | Preserves confidentiality. |
| eyewearassistops.records.case_file | case file | RECORD | File links intake, proof, order, voucher, invoice, delivery and follow-up. | Supports audit. |
| eyewearassistops.records.exception_log | exception log | RECORD | Log captures missing proof, urgent approval, vendor delay, fit problem, payment issue and failed pickup. | Enables review. |
| eyewearassistops.records.status_board | status board | RECORD | Board tracks requested, proof pending, ordered, ready, delivered, corrected and closed statuses. | Shows workflow. |
| eyewearassistops.communication.client_update | client update | PROCESS | Update explains next step, appointment, proof need, pickup window or delay in plain language. | Reduces uncertainty. |
| eyewearassistops.communication.vendor_followup | vendor follow-up | PROCESS | Follow-up checks order status, corrections, invoice readiness and delivery options. | Keeps cases moving. |
| eyewearassistops.communication.referral_note | referral note | RECORD | Note routes medical eye symptoms, severe vision loss or injury to clinical care. | Avoids treating emergencies as admin. |
| eyewearassistops.metrics.turnaround_time | turnaround time | METRIC | Time measures intake to usable eyewear delivery by case type. | Measures service speed. |
| eyewearassistops.metrics.correction_rate | correction rate | METRIC | Rate tracks orders requiring refit, remake, prescription correction or vendor rework. | Shows quality. |
| eyewearassistops.metrics.cost_per_case | cost per case | METRIC | Cost metric compares vouchers, donations, exams, repairs, shipping and replacements. | Guides funding. |
| eyewearassistops.closeout.fit_confirmation | fit confirmation | PROCESS | Confirmation checks comfort, usable vision, pickup proof and unresolved concerns. | Ensures real benefit. |
| eyewearassistops.closeout.after_action | after-action note | RECORD | Note captures vendor performance, proof bottlenecks, payment issues and outreach lessons. | Improves next cycle. |
