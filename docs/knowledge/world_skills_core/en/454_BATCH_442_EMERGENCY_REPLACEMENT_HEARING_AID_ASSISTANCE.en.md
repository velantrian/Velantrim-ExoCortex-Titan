# BATCH 442: Emergency Replacement Hearing Aid Assistance

**KnowledgeUnits:** 44  
**Namespace:** `hearingaidassistops.*`  
**Scope:** intake, device proof, batteries, vendor coordination, fitting, delivery and follow-up.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| hearingaidassistops.intake.request_source | request source | RECORD | Source records shelter desk, clinic, school, caseworker, disability advocate, hotline or self-referral. | Shows entry path. |
| hearingaidassistops.intake.client_profile | client profile | RECORD | Profile captures contact, communication preference, interpreter need, caregiver and current location. | Defines support. |
| hearingaidassistops.intake.device_loss | device loss context | RECORD | Context records lost, damaged, water-exposed, inaccessible, dead battery or charger failure. | Frames request. |
| hearingaidassistops.intake.urgency | urgency model | MODEL | Urgency weighs safety alerts, work, school, caregiving, medical communication and shelter navigation. | Prioritizes cases. |
| hearingaidassistops.eligibility.disaster_link | disaster link | CONTROL | Link verifies the hearing support need is caused or worsened by crisis conditions. | Targets assistance. |
| hearingaidassistops.eligibility.program_limit | program limit | CONTROL | Limit defines covered batteries, chargers, repairs, loaners, replacement and fitting boundaries. | Controls cost. |
| hearingaidassistops.eligibility.duplicate_check | duplicate check | CONTROL | Check compares client, device type, vendor record and prior benefit records. | Prevents double issue. |
| hearingaidassistops.proof.device_proof | device proof | RECORD | Proof includes audiology record, prior invoice, device photo, serial number, clinic note or caseworker confirmation. | Establishes need. |
| hearingaidassistops.proof.audiology_release | audiology release | PROCESS | Release obtains permission to confirm device or prescription details with audiology provider. | Protects privacy. |
| hearingaidassistops.proof.proof_exception | proof exception | CONTROL | Exception allows temporary batteries, loaner or referral when proof is unavailable but need is urgent. | Avoids harmful delay. |
| hearingaidassistops.device.device_type | device type | RECORD | Type records behind-ear, in-ear, receiver-in-canal, cochlear accessory, charger or assistive listening device. | Specifies support. |
| hearingaidassistops.device.serial_record | serial record | RECORD | Serial record captures known serial number, side, color, model and distinguishing features. | Supports replacement. |
| hearingaidassistops.device.side_match | side match | CONTROL | Match verifies left, right or bilateral device need before order or fitting. | Prevents mismatch. |
| hearingaidassistops.device.water_damage | water damage state | STATE | State flags water exposure, corrosion, intermittent function or drying attempt. | Guides repair path. |
| hearingaidassistops.batteries.battery_type | battery type | RECORD | Type records zinc-air size, rechargeable charger, cable, dome, tubing or wax guard need. | Enables quick aid. |
| hearingaidassistops.batteries.battery_issue | battery issue | PROCESS | Issue provides correct batteries with safe storage, expiration check and handling instruction. | Restores function fast. |
| hearingaidassistops.batteries.recharge_plan | recharge plan | PROCESS | Plan finds power access, replacement charger, cable, charging schedule or public charging support. | Keeps device usable. |
| hearingaidassistops.vendor.vendor_roster | vendor roster | RECORD | Roster lists audiologists, hearing aid providers, repair labs, nonprofits and emergency contacts. | Guides referral. |
| hearingaidassistops.vendor.availability_check | availability check | PROCESS | Check confirms appointments, repair capacity, loaners, parts, battery stock and fitting times. | Sets expectations. |
| hearingaidassistops.vendor.service_order | service order | RECORD | Order captures device type, proof, funding code, repair or replacement request and expected date. | Starts service. |
| hearingaidassistops.vendor.quality_issue | quality issue | STATE | Issue flags wrong device, poor fit, feedback, late order, missing accessory or unresolved programming. | Triggers correction. |
| hearingaidassistops.fitting.communication_support | communication support | PROCESS | Support provides written notes, captioning, interpreter, quiet room or caregiver participation during fitting. | Improves access. |
| hearingaidassistops.fitting.fit_check | fit check | PROCESS | Check reviews comfort, retention, ear mold, dome size, feedback, volume and user handling. | Ensures usability. |
| hearingaidassistops.fitting.programming_referral | programming referral | PROCESS | Referral sends cases needing device programming or clinical adjustment to qualified provider. | Avoids unsafe adjustment. |
| hearingaidassistops.fitting.user_instruction | user instruction | PROCESS | Instruction covers basic use, battery changes, charging, cleaning, storage and follow-up route. | Supports daily use. |
| hearingaidassistops.loaner.loaner_issue | loaner issue | RECORD | Issue records loaner device, accessory, return expectation, condition and user acknowledgment. | Bridges delay. |
| hearingaidassistops.loaner.return_tracking | return tracking | PROCESS | Tracking monitors due date, condition, cleaning, reassignment and lost loaner exceptions. | Protects inventory. |
| hearingaidassistops.payment.funding_source | funding source | RECORD | Source records grant, donation, nonprofit fund, insurance gap, clinic discount or public benefit. | Tracks resources. |
| hearingaidassistops.payment.price_cap | price cap | CONTROL | Cap limits batteries, repair, replacement, charger, fitting and shipping cost. | Protects budget. |
| hearingaidassistops.payment.invoice_match | invoice match | CONTROL | Match compares approval, service order, proof, delivery confirmation and invoice. | Prevents overpayment. |
| hearingaidassistops.delivery.pickup_option | pickup option | PROCESS | Option schedules client, caregiver, shelter desk, clinic pickup or accessible delivery. | Gets aid to user. |
| hearingaidassistops.delivery.handoff_proof | handoff proof | RECORD | Proof records recipient, device or accessory, date, status and signature or alternate confirmation. | Closes custody. |
| hearingaidassistops.delivery.failed_pickup | failed pickup | STATE | Failed pickup notes unreachable client, moved shelter, missed appointment or returned shipment. | Triggers follow-up. |
| hearingaidassistops.privacy.minimum_data | minimum data | CONTROL | Minimum data limits shared health, address and disability details to service need. | Reduces exposure. |
| hearingaidassistops.privacy.communication_preference | communication preference | CONTROL | Preference records text, email, relay, caregiver, written note or interpreter-supported contact. | Respects access. |
| hearingaidassistops.records.case_file | case file | RECORD | File links intake, proof, vendor order, funding, handoff, fitting and follow-up. | Supports audit. |
| hearingaidassistops.records.status_board | status board | RECORD | Board tracks proof pending, battery issued, ordered, repaired, loaned, fitted, delivered and closed. | Shows workflow. |
| hearingaidassistops.records.exception_log | exception log | RECORD | Log captures missing proof, urgent loaner, vendor delay, wrong accessory, failed pickup and payment exception. | Enables review. |
| hearingaidassistops.communication.client_update | client update | PROCESS | Update explains proof needs, appointment, device status, pickup window or delay in accessible format. | Keeps user informed. |
| hearingaidassistops.communication.referral_note | referral note | RECORD | Note routes ear pain, sudden hearing loss, injury or device-related medical concern to clinical care. | Avoids admin-only response. |
| hearingaidassistops.metrics.turnaround_time | turnaround time | METRIC | Time measures intake to usable hearing support by case type. | Measures speed. |
| hearingaidassistops.metrics.loaner_utilization | loaner utilization | METRIC | Utilization tracks loaners issued, returned, overdue, repaired and available. | Manages inventory. |
| hearingaidassistops.closeout.use_confirmation | use confirmation | PROCESS | Confirmation checks that the client can use the device or accessory and knows follow-up steps. | Ensures benefit. |
| hearingaidassistops.closeout.after_action | after-action note | RECORD | Note captures vendor gaps, proof bottlenecks, battery demand and communication access lessons. | Improves next activation. |
