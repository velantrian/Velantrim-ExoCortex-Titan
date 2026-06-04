# BATCH_188 — Laboratory Sample Logistics Operations Detail
# world_skills_core · source: world_skills_core:batch_188:laboratory_sample_logistics_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| samplelog.order.test_order | Laboratory test order | invariant | Test order defines patient or client, sample type, requested tests, priority and destination lab. | start of chain |
| samplelog.order.collection_window | Collection window | invariant | Window defines acceptable time for sample collection relative to test requirement. | timing affects validity |
| samplelog.order.sample_label | Sample label | invariant | Label identifies sample with unique ID, subject, type, time, collector and required tests. | identity control |
| samplelog.order.requisition_form | Requisition form | invariant | Form carries order details, clinical or project context, billing and special instructions. | paperwork follows sample |
| samplelog.order.priority_status | Sample priority status | variant | Status such as routine, urgent or stat changes pickup, transport and accession handling. | speed by need |
| samplelog.collection.collector_id | Collector identification | invariant | Collector ID links collection act to trained person and timestamp. | accountability |
| samplelog.collection.sample_container | Sample container | invariant | Container must match sample, preservative, volume, closure and test requirements. | wrong tube invalidates |
| samplelog.collection.minimum_volume | Minimum sample volume | invariant | Minimum volume is required amount for analysis, repeats and quality control. | enough material |
| samplelog.collection.contamination_risk | Collection contamination risk | invariant | Risk arises from wrong container, skin prep, environment, carryover or mixed materials. | protect result quality |
| samplelog.collection.collection_exception | Collection exception | invariant | Exception records difficult draw, partial volume, delay, leakage, wrong label or patient issue. | tell the lab |
| samplelog.packaging.primary_container | Primary sample container | invariant | Primary container directly holds specimen and must be sealed before transport. | first barrier |
| samplelog.packaging.secondary_packaging | Secondary packaging | invariant | Secondary packaging contains leakage and separates sample from paperwork. | containment layer |
| samplelog.packaging.absorbent_material | Absorbent material | invariant | Absorbent material captures leakage inside compliant transport packaging. | manage spills |
| samplelog.packaging.temperature_packout | Temperature packout | invariant | Packout maintains required ambient, refrigerated, frozen or controlled condition for transport. | stability control |
| samplelog.packaging.dangerous_goods_marking | Dangerous goods marking | variant | Marking communicates regulated biological, chemical or hazardous material transport requirements. | carriers need warning |
| samplelog.chain.chain_of_custody | Sample chain of custody | invariant | Custody record tracks possession, time, condition and transfer signatures. | evidence integrity |
| samplelog.chain.handoff_scan | Handoff barcode scan | variant | Scan records pickup, transfer, arrival and exception events in tracking system. | real-time trace |
| samplelog.chain.seal_integrity | Seal integrity check | invariant | Check confirms tamper seal, bag, container and package closure are intact. | detect interference |
| samplelog.chain.custody_gap | Custody gap | invariant | Gap is missing time, person or location in custody history and needs investigation. | trust issue |
| samplelog.chain.receipt_confirmation | Receipt confirmation | invariant | Confirmation records laboratory receipt, condition, time, accession and rejected items. | close transport |
| samplelog.transport.route_plan | Sample courier route plan | invariant | Route plan orders pickups by priority, time window, temperature and destination. | efficient pickup |
| samplelog.transport.courier_kit | Courier kit | invariant | Kit includes bags, labels, spill materials, PPE, temperature materials and documentation. | ready for exceptions |
| samplelog.transport.vehicle_cleanliness | Sample vehicle cleanliness | invariant | Cleanliness prevents cross-contamination, pests, odor and uncontrolled exposure. | transport hygiene |
| samplelog.transport.temperature_logger | Sample temperature logger | variant | Logger records temperature history for samples needing controlled conditions. | prove condition |
| samplelog.transport.delay_event | Courier delay event | invariant | Delay event records cause, affected samples, time impact and mitigation. | decide sample acceptability |
| samplelog.exception.leaking_sample | Leaking sample | invariant | Leaking sample requires containment, safety response, documentation and lab acceptance decision. | safety and validity |
| samplelog.exception.mislabelled_sample | Mislabelled sample | invariant | Mislabelled sample cannot be trusted without approved correction pathway. | identity risk |
| samplelog.exception.clotted_sample | Clotted sample | variant | Clotting may make certain blood tests invalid or limited. | specimen quality |
| samplelog.exception.hemolysis_flag | Hemolysis flag | variant | Hemolysis indicates red cell breakdown that can interfere with some analyses. | result interference |
| samplelog.exception.temperature_excursion | Sample temperature excursion | invariant | Excursion occurs when sample leaves required temperature range during storage or transit. | stability question |
| samplelog.accession.accession_number | Laboratory accession number | invariant | Accession number assigns received sample to lab workflow, tests and reports. | lab identity |
| samplelog.accession.acceptance_criteria | Sample acceptance criteria | invariant | Criteria define acceptable label, container, volume, time, temperature and condition. | gate before testing |
| samplelog.accession.rejection_reason | Sample rejection reason | invariant | Reason records why sample cannot be tested or needs recollection. | transparent refusal |
| samplelog.accession.split_sample | Split sample | variant | Split creates aliquots for multiple tests, backup, referral or storage. | divide safely |
| samplelog.accession.referral_lab | Referral laboratory | variant | Referral sends sample to external lab with custody, packaging and result tracking. | specialized testing |
| samplelog.storage.short_term_hold | Short-term sample hold | invariant | Hold keeps sample under required condition until testing, repeat or disposal. | controlled waiting |
| samplelog.storage.freeze_thaw_cycle | Freeze-thaw cycle | variant | Cycle can degrade some analytes or materials and must be tracked where relevant. | storage can change sample |
| samplelog.storage.retention_period | Sample retention period | invariant | Period defines how long sample or aliquot is kept after testing. | repeat and audit |
| samplelog.storage.disposal_log | Sample disposal log | invariant | Disposal log records sample ID, date, method, authorization and hazard route. | end of lifecycle |
| samplelog.quality.transport_audit | Sample logistics audit | invariant | Audit checks labels, custody, packaging, temperature, timing, exceptions and training. | verify chain |
| samplelog.quality.courier_training | Courier sample training | invariant | Training covers packaging, custody, temperature, spills, privacy and delivery rules. | people protect samples |
| samplelog.quality.turnaround_metric | Sample logistics turnaround | variant | Metric tracks collection-to-pickup, pickup-to-lab and accession delay. | find bottlenecks |
| samplelog.quality.nonconformance | Sample logistics nonconformance | invariant | Nonconformance documents deviation from procedure, impact assessment and corrective action. | quality loop |
| samplelog.continuity.outage_procedure | Sample logistics outage procedure | invariant | Procedure defines paper tracking, alternate routes, manual receipts and recovery during system outage. | keep chain alive |
