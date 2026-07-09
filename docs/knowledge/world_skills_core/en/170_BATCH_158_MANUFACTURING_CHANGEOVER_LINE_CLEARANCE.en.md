# BATCH_158 — Manufacturing Changeover & Line Clearance Detail
# world_skills_core · source: world_skills_core:batch_158:manufacturing_changeover_line_clearance
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| mfgchg.plan.changeover_plan | Changeover plan | invariant | Changeover plan defines product switch, sequence, people, tools, materials, cleaning, checks and restart criteria. | переход без импровизации |
| mfgchg.plan.smed | SMED | variant | SMED separates internal and external setup work to reduce equipment downtime during changeover. | меньше простоя |
| mfgchg.plan.changeover_window | Changeover window | invariant | Changeover window is the scheduled time allowed between last good unit of old run and first good unit of new run. | measure the gap |
| mfgchg.plan.runout_quantity | Runout quantity | variant | Runout quantity estimates remaining old material to avoid excess leftovers or shortage before changeover. | finish run cleanly |
| mfgchg.plan.sequence_optimization | Product sequence optimization | variant | Sequence optimization orders products to reduce cleaning, allergen risk, color changes, tool swaps or waste. | порядок уменьшает потери |
| mfgchg.plan.changeover_kit | Changeover kit | invariant | Changeover kit prepares tools, parts, labels, gauges, forms and consumables before stopping the line. | не искать во время остановки |
| mfgchg.clearance.line_clearance | Line clearance | invariant | Line clearance confirms old product, labels, components, documents and waste are removed before new run. | prevent mix-up |
| mfgchg.clearance.previous_label_removal | Previous label removal | invariant | Removing previous labels prevents wrong product identity on new units or packages. | label errors are serious |
| mfgchg.clearance.component_reconciliation | Component reconciliation | invariant | Reconciliation compares issued, used, returned, scrapped and remaining components for a run. | material accountability |
| mfgchg.clearance.wip_control | WIP control at changeover | invariant | WIP control identifies, segregates and resolves in-process material before product switch. | no orphan material |
| mfgchg.clearance.scrap_disposition | Scrap disposition | invariant | Scrap disposition records what was discarded, why, quantity, authorization and disposal route. | waste with evidence |
| mfgchg.clearance.room_line_status | Room and line status | invariant | Status sign or system state shows whether area is running, cleaning, clearing, setup, hold or released. | everyone sees state |
| mfgchg.cleaning.cleaning_matrix | Cleaning matrix | invariant | Cleaning matrix defines required cleaning level between products based on risk, residue, allergen, color or contamination. | not all switches equal |
| mfgchg.cleaning.dry_clean | Dry clean changeover | variant | Dry cleaning removes residue without water where moisture damages product, equipment or microbial control. | low-moisture context |
| mfgchg.cleaning.wet_clean | Wet clean changeover | variant | Wet cleaning uses water, chemistry, contact time and drying where residue or hygiene risk requires it. | stronger but slower |
| mfgchg.cleaning.cleaning_verification | Cleaning verification | invariant | Verification checks that cleaning was performed and visible or measured residue meets acceptance criteria. | clean before setup |
| mfgchg.cleaning.allergen_clean | Allergen changeover clean | variant | Allergen clean controls cross-contact through validated cleaning, sequencing, inspection and sometimes testing. | protect sensitive consumers |
| mfgchg.cleaning.drying_release | Drying release | invariant | Drying release confirms equipment is dry enough before restart when moisture could affect product or safety. | water after cleaning matters |
| mfgchg.setup.tooling_change | Tooling change | invariant | Tooling change replaces dies, guides, molds, heads, nozzles or fixtures required for the new product. | physical setup |
| mfgchg.setup.format_part | Format part | invariant | Format part adapts machine geometry to size, shape, pack, container or product variant. | correct part for SKU |
| mfgchg.setup.parameter_setpoint | Parameter setpoint | invariant | Setpoint changes adjust speed, temperature, pressure, torque, fill volume or timing for the new run. | recipe into machine |
| mfgchg.setup.recipe_loading | Recipe loading | invariant | Recipe loading selects approved machine settings or process parameters tied to product version. | avoid manual drift |
| mfgchg.setup.sensor_adjustment | Sensor adjustment | variant | Sensor adjustment aligns detection, photoeyes, checkweighers or vision systems to new format. | detection follows product |
| mfgchg.setup.guard_reinstallation | Guard reinstallation | invariant | Guard reinstallation confirms safety guards and interlocks are restored after setup work. | speed cannot beat safety |
| mfgchg.quality.first_off | First-off approval | invariant | First-off approval verifies first acceptable unit against specification before routine production. | approve before volume |
| mfgchg.quality.golden_sample | Golden sample | variant | Golden sample provides a physical reference for appearance, fit, color, assembly or pack standard. | compare with known good |
| mfgchg.quality.challenge_test | Challenge test | variant | Challenge test proves detector, rejector, sensor or control responds correctly before production release. | safety control works |
| mfgchg.quality.checkweigher_setup | Checkweigher setup | variant | Checkweigher setup verifies target weight, limits, reject function and data recording for new product. | weight compliance |
| mfgchg.quality.vision_system_teach | Vision system teach | variant | Vision teach updates image references, tolerances and reject rules for packaging or product changes. | camera must learn variant |
| mfgchg.quality.startup_samples | Startup samples | invariant | Startup samples are inspected during ramp-up to confirm stable process before full-rate release. | early drift detection |
| mfgchg.material.new_material_issue | New material issue | invariant | New material issue provides approved components, ingredients or packaging for the incoming run. | correct material at line |
| mfgchg.material.old_material_return | Old material return | invariant | Old material return sends unused previous materials back with identification, quantity and condition. | prevent mix-up and loss |
| mfgchg.material.lot_traceability | Lot traceability at changeover | invariant | Lot traceability links materials used after changeover to batch, time, line and product. | recall boundary |
| mfgchg.material.label_roll_control | Label roll control | invariant | Label roll control tracks issue, use, return and destruction of printed labels or packaging. | printed identity risk |
| mfgchg.material.material_staging | Material staging | variant | Staging places next-run materials near the line without mixing with current-run materials. | ready but segregated |
| mfgchg.restart.ramp_up | Production ramp-up | invariant | Ramp-up increases speed after restart while monitoring quality, jams, rejects, yield and stability. | do not jump to full speed |
| mfgchg.restart.line_release | Line release | invariant | Line release confirms clearance, cleaning, setup, quality checks, materials and documents are complete. | formal go signal |
| mfgchg.restart.reject_stream_check | Reject stream check | invariant | Reject stream check verifies rejected units are separated, counted and not returned to good product. | bad output stays out |
| mfgchg.restart.startup_waste | Startup waste | variant | Startup waste captures material lost during tuning, testing and stabilization after changeover. | cost of transition |
| mfgchg.restart.handover_note | Changeover handover note | invariant | Handover note records status, issues, settings, deviations and next checks for incoming operators. | shift memory |
| mfgchg.metrics.changeover_time | Changeover time metric | invariant | Changeover time measures from last good old unit to first good new unit under agreed definition. | common metric |
| mfgchg.metrics.first_pass_yield | First-pass yield after changeover | invariant | FPY after changeover shows how many startup units pass without rework or rejection. | quality of restart |
| mfgchg.metrics.setup_loss | Setup loss | variant | Setup loss captures downtime, waste, labor and speed loss caused by changeover activity. | transition cost |
| mfgchg.metrics.changeover_review | Changeover review | invariant | Review identifies delays, missing tools, cleaning issues, defects and improvement actions after changeover. | learn after switch |
