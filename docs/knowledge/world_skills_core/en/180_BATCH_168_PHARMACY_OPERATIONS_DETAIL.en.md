# BATCH_168 — Pharmacy Operations Detail
# world_skills_core · source: world_skills_core:batch_168:pharmacy_operations_detail
# KnowledgeUnits: 44
# ВНИМАНИЕ: операционные знания; не медицинская рекомендация, не дозировки и не замена фармацевта.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| pharmops.intake.prescription_intake | Prescription intake | invariant | Intake receives prescription, patient information, prescriber details, product request and required documentation. | start dispensing workflow |
| pharmops.intake.patient_profile | Pharmacy patient profile | invariant | Profile stores demographics, allergies, medication history, preferences, insurance and safety notes. | context for verification |
| pharmops.intake.prescriber_validation | Prescriber validation | invariant | Validation checks prescriber identity, authority, contact and required identifiers. | ensure legitimate order |
| pharmops.intake.insurance_adjudication | Insurance adjudication | variant | Adjudication checks coverage, copay, prior authorization, rejection codes and billing response. | payment workflow |
| pharmops.intake.prior_authorization_flag | Prior authorization flag | variant | Flag indicates payer approval is needed before dispensing or reimbursement. | prevent stalled pickup |
| pharmops.intake.refill_eligibility | Refill eligibility | invariant | Eligibility checks remaining refills, timing, prescription status and policy restrictions. | avoid unauthorized refill |
| pharmops.verify.clinical_verification | Pharmacist verification | invariant | Verification reviews order appropriateness, patient context, safety alerts and legal requirements. | professional gate |
| pharmops.verify.duplicate_therapy_alert | Duplicate therapy alert | variant | Alert flags overlapping therapy classes or products for pharmacist assessment. | catch possible duplication |
| pharmops.verify.allergy_alert | Allergy alert | invariant | Allergy alert highlights recorded sensitivity or allergy for pharmacist review before dispensing. | safety warning |
| pharmops.verify.interaction_alert | Interaction alert | variant | Interaction alert identifies possible interaction requiring professional evaluation and documentation. | decision support |
| pharmops.verify.high_alert_medication | High-alert medication flag | invariant | High-alert flag marks products requiring extra verification, storage or workflow controls. | reduce serious error risk |
| pharmops.verify.clarification_request | Prescriber clarification request | invariant | Clarification request records question, contact attempts, response and order change if any. | resolve ambiguity |
| pharmops.fill.pick_list | Pharmacy pick list | invariant | Pick list identifies product, strength, form, quantity, location and prescription link. | select correct stock |
| pharmops.fill.ndc_match | Product code match | invariant | Code match verifies selected package matches intended product identifier where applicable. | barcode discipline |
| pharmops.fill.counting_process | Medication counting process | invariant | Counting process measures quantity using clean tray, device or unit package under workflow rules. | quantity accuracy |
| pharmops.fill.label_generation | Prescription label generation | invariant | Label generation prints patient, product, directions from prescription, warnings, pharmacy and identifiers. | label carries instructions |
| pharmops.fill.final_check | Pharmacy final check | invariant | Final check compares prescription, product, label, quantity and patient before release. | last safety gate |
| pharmops.fill.will_call_bin | Will-call bin | variant | Will-call bin stores filled prescriptions awaiting pickup with patient separation and privacy controls. | organized pickup |
| pharmops.inventory.perpetual_inventory | Perpetual inventory | invariant | Perpetual inventory updates stock on receipt, dispensing, return, adjustment and waste. | stock truth |
| pharmops.inventory.reorder_point | Pharmacy reorder point | variant | Reorder point triggers purchase based on usage, lead time, safety stock and seasonality. | avoid stockout |
| pharmops.inventory.expiry_rotation | Expiry rotation | invariant | Rotation places earlier expiry first and removes expired stock from dispensing area. | FEFO in pharmacy |
| pharmops.inventory.refrigerator_log | Pharmacy refrigerator log | invariant | Log records storage temperature and excursions for cold-chain medicines or vaccines. | cold storage evidence |
| pharmops.inventory.quarantine_bin | Pharmacy quarantine bin | invariant | Quarantine separates recalled, expired, damaged or suspect products from usable stock. | do not dispense held stock |
| pharmops.inventory.return_to_stock | Return-to-stock process | variant | Return-to-stock reverses uncollected filled prescriptions according to privacy, stability and policy rules. | recover inventory safely |
| pharmops.controlled.controlled_storage | Controlled medication storage | invariant | Controlled storage restricts access and maintains security for regulated medicines. | protect high-risk stock |
| pharmops.controlled.controlled_reconciliation | Controlled reconciliation | invariant | Reconciliation compares physical count with records, receipts, dispensing and waste. | detect discrepancy |
| pharmops.controlled.waste_witness | Controlled waste witness | invariant | Witnessed waste documents disposal quantity, reason, staff and required signatures. | no unobserved loss |
| pharmops.controlled.audit_discrepancy | Controlled discrepancy | invariant | Discrepancy requires investigation, documentation and escalation under policy. | serious inventory signal |
| pharmops.dispense.pickup_verification | Pickup verification | invariant | Pickup checks patient or agent identity, prescription, payment and counseling requirements. | right person receives |
| pharmops.dispense.counseling_offer | Counseling offer | invariant | Counseling offer gives pharmacist opportunity to answer questions and explain safe use per policy. | patient communication gate |
| pharmops.dispense.delivery_workflow | Pharmacy delivery workflow | variant | Delivery workflow controls address, privacy, temperature, proof of delivery and failed delivery. | dispensing beyond counter |
| pharmops.dispense.partial_fill | Partial fill | variant | Partial fill documents dispensed quantity, remaining balance, reason and follow-up. | stockout without losing order |
| pharmops.dispense.transfer_request | Prescription transfer request | variant | Transfer request sends or receives prescription information between pharmacies under rules. | continuity across locations |
| pharmops.dispense.patient_refusal | Patient refusal record | invariant | Refusal records prescription not taken, reason if known, counseling notes and stock disposition. | close abandoned workflow |
| pharmops.safety.medication_error_report | Medication error report | invariant | Error report captures event, stage, product, patient impact, discovery and corrective action. | learn from mistakes |
| pharmops.safety.near_miss | Pharmacy near miss | invariant | Near miss catches error before patient receives medication and supports process improvement. | prevent future harm |
| pharmops.safety.look_alike_sound_alike | LASA control | invariant | LASA control separates or highlights products with similar names or packages. | reduce selection errors |
| pharmops.safety.barcode_scan_rate | Barcode scan rate | variant | Scan rate monitors whether barcode verification is used at required workflow points. | measure safety behavior |
| pharmops.recall.recall_notice | Pharmacy recall notice | invariant | Recall notice identifies affected product, lot, action level, patient notification and documentation needs. | respond quickly |
| pharmops.recall.lot_search | Pharmacy lot search | invariant | Lot search finds inventory and dispensed prescriptions affected by a recall or quality issue. | trace affected stock |
| pharmops.recall.patient_notification | Recall patient notification | variant | Patient notification communicates recall action using approved message, contact path and privacy safeguards. | protect patients |
| pharmops.records.privacy_screen | Pharmacy privacy control | invariant | Privacy control protects health information at counter, phone, labels, bins and systems. | confidentiality in workflow |
| pharmops.records.audit_trail | Pharmacy audit trail | invariant | Audit trail records profile changes, verification, dispensing, reversals, overrides and inventory adjustments. | accountability |
| pharmops.records.record_retention | Pharmacy record retention | invariant | Retention rules define how long prescriptions, logs, claims and safety records are kept. | evidence after sale |
