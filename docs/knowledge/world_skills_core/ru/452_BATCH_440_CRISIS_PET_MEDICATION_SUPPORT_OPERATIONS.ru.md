# BATCH 440: Crisis Pet Medication Support Operations

**KnowledgeUnits:** 44  
**Namespace:** `petmedsupportops.*`  
**Scope:** intake, veterinary proof, pharmacy, species safety, delivery, cost support and tracking.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| petmedsupportops.intake.request_source | request source | RECORD | Source records pet shelter, owner hotline, veterinary clinic, caseworker, rescue group or outreach team. | Shows entry path. |
| petmedsupportops.intake.owner_contact | owner contact | RECORD | Contact captures safe phone, current location, pickup option, language and alternate handler. | Enables coordination. |
| petmedsupportops.intake.animal_profile | animal profile | RECORD | Profile records species, name, approximate age, size, identifying details and current shelter location. | Identifies animal. |
| petmedsupportops.intake.medication_need | medication need | RECORD | Need describes lost medication, refill barrier, evacuation delay, storage issue or administration support. | Frames request. |
| petmedsupportops.eligibility.crisis_link | crisis link | CONTROL | Link verifies the medication support need is caused by displacement, damage, pharmacy closure or access loss. | Targets aid. |
| petmedsupportops.eligibility.owner_authority | owner authority | CONTROL | Authority confirms owner, foster, shelter manager or rescue representative can request support. | Prevents misuse. |
| petmedsupportops.eligibility.duplicate_check | duplicate check | CONTROL | Check compares owner, animal, clinic, medication class and prior support records. | Avoids duplicate fills. |
| petmedsupportops.vet.proof_source | veterinary proof source | RECORD | Source records prescription, vet confirmation, discharge paper, shelter medical note or medication label. | Establishes basis. |
| petmedsupportops.vet.clinic_contact | clinic contact | PROCESS | Contact requests confirmation, refill approval or clinical guidance through authorized staff. | Solves blockers. |
| petmedsupportops.vet.expiry_review | expiry review | CONTROL | Review flags expired prescriptions, unclear labels, species mismatch or missing dosage authority. | Protects safety. |
| petmedsupportops.vet.escalation | vet escalation | PROCESS | Escalation sends urgent illness, adverse effects or unclear medication questions to a veterinarian. | Avoids unsafe decisions. |
| petmedsupportops.species.species_match | species match | CONTROL | Match verifies medication is intended for the recorded species and animal. | Prevents cross-species errors. |
| petmedsupportops.species.weight_class | weight class | RECORD | Class records weight range when relevant for veterinary confirmation and supply selection. | Supports accuracy. |
| petmedsupportops.species.contra_flag | contraindication flag | STATE | Flag marks known allergy, pregnancy, age risk, concurrent medication or condition requiring vet review. | Prevents harm. |
| petmedsupportops.pharmacy.vendor_roster | pharmacy roster | RECORD | Roster lists veterinary pharmacies, clinics, compounding options, open hours and emergency contacts. | Guides sourcing. |
| petmedsupportops.pharmacy.stock_check | stock check | PROCESS | Check confirms medication availability, substitute policy, pickup time, price and storage need. | Sets expectations. |
| petmedsupportops.pharmacy.release_log | release log | RECORD | Log captures release person, package count, time, storage note and exception. | Creates custody trail. |
| petmedsupportops.pharmacy.compound_order | compound order | RECORD | Order records compound request, vet approval, expected turnaround and pickup or shipping method. | Handles special meds. |
| petmedsupportops.storage.temperature_need | temperature need | RECORD | Need marks refrigeration, no-freeze, light protection, dry storage or short stability window. | Protects quality. |
| petmedsupportops.storage.packout | packout process | PROCESS | Packout selects cooler, label, separation, temperature indicator and route limit when needed. | Maintains handling. |
| petmedsupportops.storage.expiry_check | expiry check | CONTROL | Check reviews expiration, beyond-use date and damaged packaging before release. | Prevents bad supply. |
| petmedsupportops.delivery.pickup_plan | pickup plan | PROCESS | Plan sets owner pickup, shelter desk pickup, clinic pickup, courier or rescue transport. | Moves medication. |
| petmedsupportops.delivery.identity_match | identity match | CONTROL | Match confirms owner or authorized handler using approved details and animal record. | Prevents wrong handoff. |
| petmedsupportops.delivery.handoff_proof | handoff proof | RECORD | Proof records recipient, animal, package count, time and signature or alternate confirmation. | Closes custody. |
| petmedsupportops.delivery.failed_handoff | failed handoff | STATE | Failed handoff logs no contact, moved animal, owner unavailable, unsafe site or returned package. | Triggers next action. |
| petmedsupportops.cost.funding_source | funding source | RECORD | Source records donation, grant, clinic discount, rescue fund, owner copay or emergency voucher. | Tracks resources. |
| petmedsupportops.cost.price_cap | price cap | CONTROL | Cap limits covered medication, exam, compounding, shipping and emergency fees. | Protects budget. |
| petmedsupportops.cost.invoice_match | invoice match | CONTROL | Match compares approval, pharmacy invoice, release proof and payment request. | Prevents overpayment. |
| petmedsupportops.cost.denial_reason | denial reason | RECORD | Reason records ineligible request, missing proof, clinical issue, duplicate support or cost limit. | Explains outcome. |
| petmedsupportops.privacy.minimum_data | minimum data | CONTROL | Minimum data limits shared owner and animal details to service need. | Reduces exposure. |
| petmedsupportops.privacy.shelter_board | shelter board privacy | CONTROL | Board privacy avoids public display of owner contact, medication details or sensitive case notes. | Protects clients. |
| petmedsupportops.privacy.consent_note | consent note | RECORD | Note records permission to coordinate with clinic, pharmacy, shelter or rescue partner. | Supports lawful sharing. |
| petmedsupportops.records.case_file | case file | RECORD | File links intake, proof, vet contact, sourcing, funding, handoff and closure. | Supports audit. |
| petmedsupportops.records.status_board | status board | RECORD | Board tracks proof pending, vet contacted, ordered, ready, delivered, returned and closed. | Shows workflow. |
| petmedsupportops.records.exception_log | exception log | RECORD | Log captures missing proof, stockout, clinical review, temperature issue, failed handoff and payment exception. | Enables review. |
| petmedsupportops.communication.owner_update | owner update | PROCESS | Update explains proof needs, pickup window, cost support, delays and safe next step. | Reduces anxiety. |
| petmedsupportops.communication.shelter_update | shelter update | PROCESS | Update informs authorized shelter staff about status, storage needs and pickup instructions. | Keeps animal care aligned. |
| petmedsupportops.communication.referral_note | referral note | RECORD | Note routes animal illness, worsening symptoms or emergency needs to veterinary care. | Avoids admin-only response. |
| petmedsupportops.metrics.fulfillment_rate | fulfillment rate | METRIC | Rate tracks approved requests that receive medication support. | Measures service. |
| petmedsupportops.metrics.proof_delay | proof delay | METRIC | Delay measures time lost to missing veterinary proof or unreachable clinic. | Shows bottleneck. |
| petmedsupportops.metrics.cost_per_case | cost per case | METRIC | Cost compares medication, compounding, shipping, discounts and subsidies. | Guides funding. |
| petmedsupportops.closeout.owner_confirmation | owner confirmation | PROCESS | Confirmation verifies receipt, remaining barriers and whether veterinary follow-up is needed. | Closes loop. |
| petmedsupportops.closeout.return_process | return process | PROCESS | Return process sends unclaimed or unusable medication to approved pharmacy, clinic or disposal pathway. | Protects custody. |
| petmedsupportops.closeout.after_action | after-action note | RECORD | Note captures vendor gaps, proof delays, species risks and funding needs. | Improves next activation. |
