# BATCH_212 — Auto Body Repair Shop Operations Detail
# world_skills_core · source: world_skills_core:batch_212:auto_body_repair_shop_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| autobody.intake.repair_intake | Auto body repair intake | invariant | Intake records customer, vehicle, claim, damage area, drivability, photos and authorization. | open repair file |
| autobody.intake.vehicle_checkin | Vehicle check-in | invariant | Check-in captures mileage, fuel, warning lights, belongings, keys and pre-existing damage. | baseline evidence |
| autobody.intake.insurance_claim | Insurance claim link | variant | Link connects estimate, insurer, adjuster, claim number, approvals and supplements. | claim workflow |
| autobody.intake.customer_authorization | Repair authorization | invariant | Authorization allows tear-down, estimate, storage, repair or parts order according to scope. | permission control |
| autobody.intake.drivability_assessment | Drivability assessment | invariant | Assessment determines whether vehicle can be safely moved, stored or driven. | safety and logistics |
| autobody.estimate.damage_photo | Damage photo set | invariant | Photos document impact area, panels, gaps, VIN, odometer and hidden indicators. | visual evidence |
| autobody.estimate.initial_estimate | Initial body repair estimate | invariant | Estimate lists visible damage, labor operations, parts, materials, scans and assumptions. | first cost view |
| autobody.estimate.supplement_request | Repair supplement request | invariant | Request adds hidden damage, extra labor, parts or procedures discovered after tear-down. | adjust scope |
| autobody.estimate.oem_procedure_check | OEM procedure check | variant | Check verifies manufacturer repair, calibration, welding or replacement procedure. | repair correctly |
| autobody.estimate.total_loss_flag | Total loss flag | variant | Flag indicates repair may exceed economic or insurer threshold. | avoid wasted work |
| autobody.parts.parts_order | Auto body parts order | invariant | Order lists part number, side, quantity, supplier, ETA, price and claim linkage. | supply repair |
| autobody.parts.parts_mirror_match | Parts mirror match | invariant | Match compares received part to damaged part, estimate and vehicle options. | prevent wrong install |
| autobody.parts.backorder | Body shop parts backorder | variant | Backorder delays repair and triggers customer, insurer and schedule updates. | manage wait |
| autobody.parts.core_return | Auto body core return | variant | Return sends bumper, headlamp, module or reusable component back under supplier rule. | recover credit |
| autobody.parts.parts_cart | Repair parts cart | invariant | Cart keeps job-specific parts, clips, hardware and labels together. | avoid mix-up |
| autobody.teardown.damage_discovery | Tear-down damage discovery | invariant | Discovery exposes hidden structural, mechanical, electrical or trim damage. | find full scope |
| autobody.teardown.hardware_bag | Hardware bagging | invariant | Bagging labels fasteners, clips and small parts by panel or operation. | reassembly discipline |
| autobody.teardown.pre_repair_scan | Pre-repair scan | variant | Scan records diagnostic codes and affected systems before repair. | electronic baseline |
| autobody.teardown.repair_plan | Body repair plan | invariant | Plan sequences structural, panel, mechanical, paint, calibration and quality steps. | shop roadmap |
| autobody.teardown.blueprint_meeting | Repair blueprint meeting | variant | Meeting aligns estimator, technician, parts and production on full repair plan. | reduce surprises |
| autobody.repair.frame_measure | Frame measurement | variant | Measurement compares vehicle structure to specification after collision damage. | structural accuracy |
| autobody.repair.panel_replacement | Panel replacement | invariant | Replacement follows approved cut, weld, bond, fastener or seam procedure. | restore body |
| autobody.repair.panel_repair | Panel repair | invariant | Repair reshapes, fills or refinishes damaged panel within quality and safety limits. | save part where suitable |
| autobody.repair.corrosion_protection | Corrosion protection | invariant | Protection restores coatings, seam sealer, cavity wax or primer after repair. | long-term durability |
| autobody.repair.adjacent_damage | Adjacent damage note | variant | Note identifies damage near repair area that may be unrelated, prior or supplement-worthy. | scope clarity |
| autobody.paint.paint_code | Paint code verification | invariant | Verification confirms vehicle paint code, variant, refinish area and blend needs. | color starts right |
| autobody.paint.surface_prep | Paint surface preparation | invariant | Prep cleans, sands, masks, primes and controls dust before coating. | finish quality |
| autobody.paint.color_match | Paint color match | invariant | Match uses formula, spray-out, lighting and blend strategy to reduce mismatch. | visible quality |
| autobody.paint.booth_schedule | Paint booth schedule | variant | Schedule coordinates jobs, cure times, booth capacity, masking and materials. | bottleneck control |
| autobody.paint.paint_material_log | Paint material log | invariant | Log tracks primer, base, clear, reducer, hardener, lot and usage. | cost and trace |
| autobody.reassembly.reassembly_check | Reassembly check | invariant | Check ensures panels, trim, lights, sensors, clips and seals are installed correctly. | put back whole |
| autobody.reassembly.gap_alignment | Gap and alignment check | invariant | Check confirms panel gaps, flushness, closures and weather sealing. | body fit |
| autobody.reassembly.post_repair_scan | Post-repair scan | variant | Scan checks electronic systems after repair and before delivery. | hidden faults |
| autobody.reassembly.calibration_need | Calibration need | variant | Need flags ADAS, cameras, sensors or steering systems requiring calibration. | modern repair |
| autobody.reassembly.road_test | Body shop road test | variant | Test confirms noise, alignment, warning lights, drivability and water leaks where appropriate. | final function |
| autobody.quality.quality_gate | Body repair quality gate | invariant | Gate checks estimate completion, fit, finish, cleanliness, scans, calibrations and paperwork. | release standard |
| autobody.quality.detail_delivery | Delivery detail | invariant | Detail cleans vehicle, removes dust, checks glass, interior and exterior presentation. | customer impression |
| autobody.quality.customer_walkaround | Customer delivery walkaround | invariant | Walkaround explains repairs, warranty, care instructions and remaining issues. | transparent handoff |
| autobody.quality.comeback | Body shop comeback | invariant | Comeback records customer return for defect, noise, paint, fit or missed item. | quality loop |
| autobody.quality.warranty_note | Repair warranty note | variant | Note states covered repair areas, limits, duration and claim path. | expectation clarity |
| autobody.admin.production_board | Body shop production board | invariant | Board shows jobs by stage, owner, parts, target date and blockers. | manage flow |
| autobody.admin.sublet_work | Sublet repair work | variant | Work outsourced for glass, alignment, calibration, mechanical or specialty repair. | external dependency |
| autobody.metrics.cycle_time | Auto body cycle time KPI | variant | KPI measures drop-off to delivery, touch time, supplement delay and parts delay. | manage throughput |
| autobody.continuity.paint_booth_down | Paint booth downtime plan | invariant | Plan resequences work, updates customers and coordinates repair during booth outage. | keep shop moving |
