# BATCH_272 — Pavement Management Operations Detail
# world_skills_core · source: world_skills_core:batch_272:pavement_management_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| pavementops.inventory.pavement_section | Pavement section record | invariant | Record defines road segment, surface type, limits, lanes, construction history and ownership. | organize network |
| pavementops.inventory.functional_class | Pavement functional class | variant | Class links roadway importance, traffic role, bus routes, freight use and emergency access. | rank assets |
| pavementops.inventory.surface_type | Pavement surface type | invariant | Type distinguishes asphalt, concrete, composite, gravel, brick or specialized surface. | select methods |
| pavementops.inventory.traffic_loading | Pavement traffic loading record | variant | Record estimates vehicle volume, heavy trucks, bus loads and equivalent axle demand. | predict wear |
| pavementops.survey.condition_survey | Pavement condition survey | invariant | Survey captures distress, roughness, rutting, cracking, drainage and ride quality by segment. | assess condition |
| pavementops.survey.windshield_survey | Pavement windshield survey | variant | Survey uses visual drive-by rating to screen large networks quickly. | rapid review |
| pavementops.survey.automated_data_collection | Automated pavement data collection | variant | Collection uses imaging, lasers, GPS and sensors to measure cracking, roughness and rutting. | scale surveys |
| pavementops.survey.ground_truth_check | Pavement ground truth check | invariant | Check verifies automated or desktop ratings against field observations and photos. | improve accuracy |
| pavementops.distress.alligator_cracking | Alligator cracking code | invariant | Code describes interconnected fatigue cracks often linked to structural failure or base weakness. | trigger repair |
| pavementops.distress.longitudinal_crack | Longitudinal crack code | invariant | Code records cracks parallel to traffic from joints, shrinkage, reflection or construction seams. | plan sealing |
| pavementops.distress.transverse_crack | Transverse crack code | invariant | Code records crosswise cracks from temperature, reflection, age or material movement. | prevent water |
| pavementops.distress.rutting | Pavement rutting code | invariant | Rutting records wheel path depressions caused by traffic, mix instability or base deformation. | safety risk |
| pavementops.distress.pothole | Pothole distress code | invariant | Code captures bowl-shaped pavement loss with size, depth, hazard and repair urgency. | patch hazard |
| pavementops.distress.raveling | Raveling distress code | variant | Raveling records aggregate loss, binder aging, poor compaction or surface oxidation. | surface treatment |
| pavementops.distress.faulting | Concrete slab faulting code | variant | Faulting records vertical offset between slabs from pumping, base loss or load transfer failure. | ride quality |
| pavementops.scoring.pavement_condition_index | Pavement condition index | invariant | Index converts observed distresses and severity into a comparable network score. | compare sections |
| pavementops.scoring.remaining_service_life | Remaining service life estimate | variant | Estimate projects useful life from condition, age, traffic, climate and treatment history. | plan renewal |
| pavementops.scoring.priority_score | Pavement project priority score | invariant | Score combines condition, traffic, equity, safety, cost, utility conflicts and policy weights. | rank projects |
| pavementops.treatment.crack_sealing | Crack sealing treatment | invariant | Treatment seals eligible cracks before water intrusion accelerates pavement damage. | preserve surface |
| pavementops.treatment.surface_seal | Surface seal treatment | variant | Treatment applies fog seal, slurry, microsurfacing or chip seal to slow aging. | extend life |
| pavementops.treatment.mill_overlay | Mill and overlay treatment | invariant | Treatment removes worn surface and places new asphalt layer within structural limits. | renew pavement |
| pavementops.treatment.full_depth_repair | Full-depth pavement repair | invariant | Repair removes failed layers and rebuilds surface, base or subbase at localized locations. | fix structure |
| pavementops.treatment.reconstruction | Pavement reconstruction | invariant | Reconstruction replaces pavement structure when preservation or overlay cannot restore performance. | reset asset |
| pavementops.treatment.concrete_panel_replacement | Concrete panel replacement | variant | Replacement removes failed slabs, restores base support, dowels and curing before reopening. | repair concrete |
| pavementops.selection.treatment_decision_tree | Pavement treatment decision tree | invariant | Decision tree links distress pattern, severity, traffic and cost to appropriate treatment. | avoid wrong fix |
| pavementops.selection.do_nothing_option | Pavement do-nothing option | variant | Option records deferred treatment consequences, risk, cost escalation and monitoring needs. | transparent tradeoff |
| pavementops.selection.utility_coordination | Pavement utility coordination | invariant | Coordination checks planned water, sewer, gas, telecom or electric work before resurfacing. | avoid rework |
| pavementops.program.annual_paving_program | Annual paving program | invariant | Program bundles candidate streets, budgets, design status, public notices and construction windows. | deliver projects |
| pavementops.program.multi_year_plan | Pavement multi-year plan | invariant | Plan forecasts projects, funding, condition targets and preservation backlog over several years. | strategic planning |
| pavementops.program.equity_screen | Pavement equity screen | variant | Screen compares investment distribution, complaints, transit routes and vulnerable areas. | fair allocation |
| pavementops.budget.unit_cost_library | Pavement unit cost library | invariant | Library stores typical costs for treatments, traffic control, striping, ramps and contingencies. | estimate budget |
| pavementops.budget.funding_constraint | Pavement funding constraint | invariant | Constraint limits project selection by available funds, grant rules, match and fiscal timing. | realistic plan |
| pavementops.budget.life_cycle_cost | Pavement life-cycle cost | variant | Cost compares preservation, overlay and reconstruction timing over long-term asset performance. | spend wisely |
| pavementops.field.pothole_work_order | Pothole work order | invariant | Order records location, severity, material, crew, repair date, weather and recurrence. | patch defects |
| pavementops.field.cut_restoration | Utility cut restoration | variant | Restoration checks trench patch, compaction, joints, surface quality and warranty responsibility. | protect pavement |
| pavementops.field.drainage_related_distress | Drainage-related pavement distress | invariant | Distress links water, ponding, blocked drains or base saturation to pavement failure. | fix root cause |
| pavementops.quality.core_sampling | Pavement core sampling | variant | Sampling measures layer thickness, material type, compaction or distress mechanism. | verify structure |
| pavementops.quality.compaction_check | Pavement compaction check | invariant | Check confirms density, rolling, temperature window and acceptance criteria for asphalt work. | quality control |
| pavementops.quality.smoothness_acceptance | Pavement smoothness acceptance | variant | Acceptance measures ride quality and requires correction when thresholds are exceeded. | better ride |
| pavementops.reporting.network_condition_report | Pavement network condition report | invariant | Report summarizes condition distribution, backlog, treatment mix, spending and trend. | inform decisions |
| pavementops.reporting.project_delivery_report | Pavement project delivery report | variant | Report tracks completed lane miles, costs, delays, change orders and remaining budget. | monitor program |
| pavementops.metrics.backlog_value | Pavement backlog value KPI | invariant | KPI estimates cost to bring pavement network to target condition. | funding signal |
| pavementops.metrics.preservation_ratio | Pavement preservation ratio KPI | variant | KPI compares preventive treatments to reactive reconstruction or emergency repair. | program balance |
| pavementops.close.segment_history_update | Pavement segment history update | invariant | Update records completed treatment, date, contractor, cost, materials and new condition baseline. | close lifecycle |
