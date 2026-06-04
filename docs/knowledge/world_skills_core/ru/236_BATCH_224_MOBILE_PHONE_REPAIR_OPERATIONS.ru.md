# BATCH_224 — Mobile Phone Repair Operations Detail
# world_skills_core · source: world_skills_core:batch_224:mobile_phone_repair_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| phonerepair.intake.device_intake | Phone repair device intake | invariant | Intake records customer, device, model, serial/IMEI, symptom, condition and passcode policy. | open repair |
| phonerepair.intake.privacy_notice | Phone repair privacy notice | invariant | Notice explains data handling, access limits, backup responsibility and customer consent. | protect data |
| phonerepair.intake.condition_photo | Phone condition photo | invariant | Photos document cracks, dents, liquid indicators, missing parts and screen state. | baseline |
| phonerepair.intake.repair_quote | Phone repair quote | invariant | Quote states diagnosis, parts, labor, risks, warranty and approval. | informed consent |
| phonerepair.intake.warranty_check | Device warranty check | variant | Check identifies manufacturer, shop, insurance or prior repair coverage. | billing route |
| phonerepair.diagnostic.power_test | Phone power test | invariant | Test checks charging, boot, battery behavior, buttons and visible error state. | reproduce symptom |
| phonerepair.diagnostic.screen_test | Screen function test | invariant | Test checks touch, pixels, brightness, cracks, proximity and display response. | common fault |
| phonerepair.diagnostic.port_test | Charging port test | invariant | Test checks cable fit, debris, charging, data connection and looseness. | port workflow |
| phonerepair.diagnostic.camera_test | Phone camera test | variant | Test checks front, rear, focus, flash, image artifacts and app access. | verify module |
| phonerepair.diagnostic.liquid_damage_check | Liquid damage check | variant | Check looks for corrosion, indicators, residue and board risk. | repair risk |
| phonerepair.parts.part_compatibility | Phone part compatibility | invariant | Compatibility checks model, revision, region, color, connector and feature support. | avoid wrong part |
| phonerepair.parts.screen_assembly | Screen assembly part | variant | Part may include glass, digitizer, OLED/LCD, frame or sensors. | know replacement scope |
| phonerepair.parts.battery_part | Phone battery part | variant | Part must match device, capacity, connector, safety and supplier quality. | power component |
| phonerepair.parts.small_parts | Phone small parts | variant | Small parts include seals, screws, brackets, mesh, adhesive and gaskets. | tiny but critical |
| phonerepair.parts.parts_inventory | Phone repair parts inventory | invariant | Inventory tracks stock, cost, supplier, quality, defects and returns. | first-visit repair |
| phonerepair.repair.esd_control | ESD control | invariant | Control uses mats, straps, grounding and handling to reduce static damage. | protect electronics |
| phonerepair.repair.screw_map | Phone screw map | invariant | Map tracks screw size and location to avoid board or screen damage. | tiny order matters |
| phonerepair.repair.adhesive_removal | Adhesive removal | invariant | Removal uses heat, tools and care to separate screen or battery without damage. | safe disassembly |
| phonerepair.repair.battery_safety | Battery safety | invariant | Safety avoids puncture, bending, overheating, swelling or shorting lithium battery. | high-risk component |
| phonerepair.repair.water_resistance_limit | Water-resistance limit | invariant | Repair may reduce sealing unless tested and restored under controlled process. | set expectation |
| phonerepair.workflow.screen_replacement | Screen replacement workflow | invariant | Workflow removes damaged assembly, transfers parts if needed, installs, seals and tests. | common repair |
| phonerepair.workflow.battery_replacement | Battery replacement workflow | invariant | Workflow removes battery, installs compatible part, checks charging and records cycle. | restore runtime |
| phonerepair.workflow.port_cleaning | Charging port cleaning | variant | Cleaning removes lint or debris without damaging pins or seals. | simple fix |
| phonerepair.workflow.board_repair_route | Board repair route | variant | Route sends micro-soldering or board-level work to qualified bench or vendor. | specialized work |
| phonerepair.workflow.data_recovery_route | Data recovery route | variant | Route handles nonbooting device with consent, privacy and realistic limits. | data-sensitive job |
| phonerepair.test.post_repair_test | Phone post-repair test | invariant | Test confirms repaired function plus core phone, charging, audio, camera and connectivity. | prove repair |
| phonerepair.test.biometric_test | Biometric function test | variant | Test checks fingerprint or face unlock where repair may affect sensor. | feature validation |
| phonerepair.test.call_audio_test | Call and audio test | invariant | Test checks speaker, microphone, earpiece, vibration and call path. | phone basics |
| phonerepair.test.network_test | Phone network test | variant | Test checks Wi-Fi, Bluetooth, cellular detection or SIM recognition as applicable. | connectivity |
| phonerepair.test.final_cleanup | Device final cleanup | invariant | Cleanup removes adhesive residue, fingerprints, dust and temporary labels. | professional finish |
| phonerepair.privacy.customer_data_boundary | Customer data boundary | invariant | Boundary limits browsing, copying or viewing personal data beyond repair need and consent. | trust |
| phonerepair.privacy.passcode_policy | Phone passcode policy | invariant | Policy controls when passcode is needed, stored, avoided or customer-assisted. | privacy control |
| phonerepair.privacy.data_backup_advice | Backup responsibility notice | invariant | Notice tells customer repair can risk data and backup is customer responsibility unless contracted. | expectation |
| phonerepair.privacy.device_wipe | Device wipe authorization | variant | Wipe requires explicit customer approval and documentation. | irreversible action |
| phonerepair.privacy.abandoned_device | Abandoned phone process | invariant | Process handles notice, storage, legal timeline, data privacy and disposal. | close old jobs |
| phonerepair.billing.invoice | Phone repair invoice | invariant | Invoice lists diagnosis, part, labor, tax, discount, warranty and payment. | close money |
| phonerepair.billing.deposit | Repair deposit | variant | Deposit reserves part or bench time and defines refund rules. | reduce no-shows |
| phonerepair.billing.refund | Phone repair refund | variant | Refund handles failed part, customer cancellation, warranty return or goodwill adjustment. | service recovery |
| phonerepair.warranty.repair_warranty | Phone repair warranty | invariant | Warranty defines covered part, labor, duration, exclusions and claim path. | expectation clarity |
| phonerepair.warranty.comeback | Phone repair comeback | invariant | Comeback records repeated issue, part failure, workmanship concern and resolution. | quality loop |
| phonerepair.admin.technician_skill | Phone technician skill record | invariant | Record tracks device families, microsoldering, data privacy, ESD and battery safety competence. | assign work |
| phonerepair.admin.tool_calibration | Phone repair tool check | variant | Check covers heat plate, microscope, screwdrivers, testers and ESD tools. | reliable bench |
| phonerepair.metrics.phone_repair_kpi | Phone repair KPI | variant | KPI tracks turnaround, comeback rate, part defects, margin, data incidents and customer reviews. | manage shop |
| phonerepair.continuity.part_shortage | Phone part shortage process | invariant | Process informs customer, offers alternatives, holds device or cancels with documented choice. | keep trust |
