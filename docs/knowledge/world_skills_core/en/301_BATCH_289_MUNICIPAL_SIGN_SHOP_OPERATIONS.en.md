# BATCH_289 — Municipal Sign Shop Operations Detail
# world_skills_core · source: world_skills_core:batch_289:municipal_sign_shop_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| signshopops.intake.sign_work_order | Sign shop work order | invariant | Order records requested sign, quantity, location, priority, due date and requester. | start production |
| signshopops.intake.sign_request_review | Sign request review | invariant | Review checks authority, standard, legend, size, color, location and duplication. | avoid wrong signs |
| signshopops.intake.emergency_sign_order | Emergency sign order | variant | Order prioritizes stop, detour, closure, hazard or storm replacement signs. | restore control |
| signshopops.design.standard_sign_layout | Standard sign layout | invariant | Layout follows approved dimensions, fonts, colors, borders, symbols and reflectivity. | consistent sign |
| signshopops.design.custom_sign_layout | Custom sign layout | variant | Layout handles local messages while preserving readability, contrast, size and authority. | special need |
| signshopops.design.legend_proof | Sign legend proof | invariant | Proof verifies spelling, arrows, route numbers, times, symbols and regulatory wording. | prevent errors |
| signshopops.design.artwork_file_control | Sign artwork file control | variant | Control stores templates, versions, approvals, source files and print-ready exports. | manage designs |
| signshopops.materials.sheeting_type | Sign sheeting type | invariant | Type defines retroreflective performance, durability, color and approved application. | choose material |
| signshopops.materials.substrate_blank | Sign substrate blank | invariant | Blank may be aluminum, composite or other approved panel with thickness and size. | build base |
| signshopops.materials.ink_film | Sign ink or film | variant | Material creates legend, color, symbols or overlays with durability and compatibility requirements. | create face |
| signshopops.materials.hardware_pack | Sign hardware pack | variant | Pack includes bolts, brackets, bands, posts, caps and breakaway parts for installation. | prepare delivery |
| signshopops.fabrication.blank_cutting | Sign blank cutting | invariant | Cutting creates required panel size, shape, corners and holes from stock material. | prepare blank |
| signshopops.fabrication.surface_prep | Sign surface preparation | invariant | Preparation cleans, deburrs and readies substrate for sheeting, printing or film. | improve adhesion |
| signshopops.fabrication.digital_printing | Sign digital printing | variant | Printing applies graphics onto sheeting or film using approved color and curing process. | produce legend |
| signshopops.fabrication.plotter_cut_film | Plotter-cut sign film | variant | Cut film creates letters, symbols or overlays from reflective or opaque material. | precise graphics |
| signshopops.fabrication.lamination | Sign lamination | variant | Lamination protects printed signs from UV, abrasion, graffiti and weather. | extend life |
| signshopops.fabrication.hole_punching | Sign hole punching | invariant | Holes match mounting hardware, post pattern and sign orientation requirements. | install fit |
| signshopops.quality.color_check | Sign color check | invariant | Check verifies color matches approved standard and remains legible under expected lighting. | ensure compliance |
| signshopops.quality.reflectivity_check | Sign reflectivity check | invariant | Check confirms sheeting class, lot, orientation and visible reflective performance. | night visibility |
| signshopops.quality.dimension_check | Sign dimension check | invariant | Check verifies size, border, hole placement, corner radius and layout alignment. | quality control |
| signshopops.quality.final_proof_check | Sign final proof check | invariant | Check compares completed sign to approved order before packaging or delivery. | catch mistakes |
| signshopops.inventory.blank_stock | Sign blank stock | invariant | Stock tracks blank sizes, shapes, quantities, reorder points and reserved inventory. | maintain supply |
| signshopops.inventory.sheeting_stock | Reflective sheeting stock | invariant | Stock tracks rolls, colors, grades, lot numbers, age and storage conditions. | material control |
| signshopops.inventory.finished_sign_stock | Finished sign stock | variant | Stock includes common signs ready for rapid replacement or field installation. | speed response |
| signshopops.inventory.stockout_risk | Sign shop stockout risk | variant | Risk occurs when critical blanks, sheeting or hardware fall below emergency need. | avoid delay |
| signshopops.records.material_lot_record | Sign material lot record | invariant | Record links sheeting, ink, film or laminate lots to produced signs. | trace quality |
| signshopops.records.production_log | Sign shop production log | invariant | Log records orders completed, quantities, materials, labor, equipment and issues. | track output |
| signshopops.records.scrap_record | Sign shop scrap record | variant | Record documents misprints, damaged blanks, obsolete signs and recyclable material. | control waste |
| signshopops.records.delivery_record | Sign delivery record | invariant | Record tracks signs delivered to crews, warehouse, contractor, site or requesting department. | trace handoff |
| signshopops.equipment.printer_maintenance | Sign printer maintenance | invariant | Maintenance covers print heads, calibration, ink, curing, media feed and test prints. | keep printer ready |
| signshopops.equipment.plotter_maintenance | Vinyl plotter maintenance | variant | Maintenance checks blades, mats, tracking, pressure, software connection and cut quality. | reliable cutting |
| signshopops.equipment.laminator_safety | Sign laminator safety | variant | Safety covers rollers, heat, pinch points, jams, cleaning and lockout steps. | protect staff |
| signshopops.safety.chemical_handling | Sign shop chemical handling | invariant | Handling covers inks, solvents, cleaners, adhesives, ventilation, storage and PPE. | safe shop |
| signshopops.safety.cutting_tool_safety | Sign shop cutting tool safety | invariant | Safety covers cutters, punches, drills, deburring tools, gloves and eye protection. | prevent injury |
| signshopops.safety.material_storage | Sign material storage safety | variant | Storage prevents roll damage, falling panels, sharp edges, blocked exits and fire risks. | orderly shop |
| signshopops.coordination.field_crew_handoff | Sign shop field crew handoff | invariant | Handoff gives crews correct signs, posts, hardware, maps, priorities and installation notes. | install correctly |
| signshopops.coordination.engineering_approval | Sign engineering approval | variant | Approval confirms new regulatory or guide signs meet traffic engineering decision and authority. | govern changes |
| signshopops.coordination.procurement_reorder | Sign shop procurement reorder | invariant | Reorder initiates purchase of blanks, sheeting, hardware, inks or tools before stockout. | sustain production |
| signshopops.reporting.backlog_report | Sign shop backlog report | invariant | Report summarizes open orders by priority, type, due date, materials and requester. | manage queue |
| signshopops.reporting.production_cost_report | Sign production cost report | variant | Report estimates material, labor, equipment, waste and overhead per order or sign type. | manage budget |
| signshopops.metrics.order_cycle_time | Sign shop order cycle time KPI | invariant | KPI measures time from approved request to completed sign or delivery. | improve service |
| signshopops.metrics.rework_rate | Sign shop rework rate KPI | variant | KPI tracks signs remade because of design, spelling, material, production or order errors. | reduce waste |
| signshopops.continuity.disaster_sign_stock | Disaster sign stock | variant | Stock holds barricade, detour, closure, hazard and emergency direction signs for rapid deployment. | emergency readiness |
| signshopops.close.order_closeout | Sign shop order closeout | invariant | Closeout confirms production, QA, delivery, inventory adjustment, records and requester notice. | finish order |
