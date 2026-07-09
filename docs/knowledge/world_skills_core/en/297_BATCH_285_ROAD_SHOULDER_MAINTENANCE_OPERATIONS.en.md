# BATCH_285 — Road Shoulder Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_285:road_shoulder_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| shoulderops.inventory.shoulder_segment | Road shoulder segment record | invariant | Record stores shoulder type, width, surface, slope, route, side and maintenance history. | manage asset |
| shoulderops.inventory.paved_shoulder | Paved shoulder record | invariant | Record captures asphalt or concrete shoulder condition, width, edge line and drainage features. | maintain pavement |
| shoulderops.inventory.gravel_shoulder | Gravel shoulder record | variant | Record captures aggregate type, depth, grading condition, edge drop and replenishment history. | maintain gravel |
| shoulderops.inventory.safety_priority | Shoulder safety priority | variant | Priority ranks shoulders near curves, hills, bike routes, narrow lanes, schools or crash sites. | choose work |
| shoulderops.inspection.routine_shoulder_patrol | Routine shoulder patrol | invariant | Patrol checks drop-offs, ruts, erosion, vegetation, debris, drainage, signs and edge condition. | find defects |
| shoulderops.inspection.post_storm_shoulder_check | Post-storm shoulder check | variant | Check looks for washouts, sediment, blocked ditches, fallen limbs and soft shoulders. | restore road |
| shoulderops.inspection.complaint_inspection | Shoulder complaint inspection | invariant | Inspection responds to reports of drop-off, rutting, ponding, debris or unsafe edge. | verify complaint |
| shoulderops.defect.edge_dropoff | Road shoulder edge drop-off | invariant | Drop-off is vertical difference between travel lane and shoulder that can affect vehicle control. | repair hazard |
| shoulderops.defect.shoulder_rutting | Shoulder rutting | invariant | Rutting forms wheel depressions from traffic, soft material, drainage failure or repeated parking. | restore profile |
| shoulderops.defect.shoulder_erosion | Shoulder erosion | invariant | Erosion removes shoulder material through runoff, ditch flow, wave action or slope failure. | protect edge |
| shoulderops.defect.soft_shoulder | Soft shoulder condition | variant | Condition means shoulder cannot support vehicle due to saturation, weak base or loose material. | warn drivers |
| shoulderops.defect.vegetation_encroachment | Shoulder vegetation encroachment | variant | Encroachment narrows shoulder, hides signs, blocks drainage or reduces sight distance. | clear edge |
| shoulderops.grading.shoulder_blading | Shoulder blading | invariant | Blading reshapes unpaved shoulder to remove ruts, restore slope and move material. | improve drainage |
| shoulderops.grading.cross_slope | Shoulder cross slope | invariant | Slope carries water away from pavement toward ditch or roadside drainage. | prevent ponding |
| shoulderops.grading.material_pullup | Shoulder material pull-up | variant | Pull-up recovers displaced aggregate from edge or ditch line back onto shoulder. | conserve material |
| shoulderops.grading.washboarding_control | Gravel shoulder washboarding control | variant | Control grades corrugations from traffic, braking, speed or loose aggregate. | smooth surface |
| shoulderops.materials.aggregate_replenishment | Shoulder aggregate replenishment | invariant | Replenishment adds gravel or crushed stone where shoulder material is lost or thin. | restore support |
| shoulderops.materials.shoulder_stabilization | Shoulder stabilization | variant | Stabilization uses aggregate, geotextile, binder or drainage improvement to resist rutting. | strengthen shoulder |
| shoulderops.materials.recycled_asphalt_shoulder | Recycled asphalt shoulder | variant | Recycled asphalt can improve shoulder stability and dust control where allowed. | reuse material |
| shoulderops.drainage.shoulder_ponding | Shoulder ponding | invariant | Ponding indicates poor slope, blocked ditch, settlement, rutting or inlet problem. | fix drainage |
| shoulderops.drainage.ditch_relation | Shoulder ditch relation | invariant | Shoulder performance depends on ditch capacity, flow line, vegetation and outlet condition. | coordinate drainage |
| shoulderops.drainage.washout_repair | Shoulder washout repair | invariant | Repair replaces lost material, restores slope, controls runoff and checks culvert or ditch. | prevent recurrence |
| shoulderops.edge.pavement_edge_support | Pavement edge support | invariant | Shoulder supports pavement edge and reduces cracking, breakoff or edge raveling. | protect road |
| shoulderops.edge.edge_line_visibility | Shoulder edge line visibility | variant | Visibility helps drivers identify pavement edge, especially at night or in wet conditions. | improve guidance |
| shoulderops.edge.edge_patch | Road edge patch | variant | Patch repairs broken pavement edge before shoulder work or resurfacing. | restore transition |
| shoulderops.workorders.dropoff_repair_order | Shoulder drop-off repair order | invariant | Order specifies location, severity, material, traffic control, grading and completion evidence. | correct hazard |
| shoulderops.workorders.grading_order | Shoulder grading work order | invariant | Order assigns route, equipment, material, ditch care, safety controls and priority. | schedule crew |
| shoulderops.workorders.debris_removal_order | Shoulder debris removal order | variant | Order removes tire pieces, cargo, rocks, litter, crash debris or dumped material. | clear recovery area |
| shoulderops.safety.traffic_control | Shoulder work traffic control | invariant | Control protects maintenance crews with signs, cones, shadow vehicles and lane encroachment limits. | worker safety |
| shoulderops.safety.recovery_area | Roadside recovery area | invariant | Shoulder provides space for stopped vehicles, emergency maneuvers, breakdowns and enforcement. | road safety |
| shoulderops.safety.bicycle_shoulder_use | Bicycle shoulder use | variant | Shoulder condition affects cyclists where shoulder functions as bike accommodation. | protect cyclists |
| shoulderops.safety.mailbox_fixed_object | Shoulder fixed-object concern | variant | Concern includes mailbox, post, guardrail end, sign or utility near shoulder edge. | reduce hazards |
| shoulderops.signage.soft_shoulder_sign | Soft shoulder warning sign | variant | Sign warns drivers where shoulder cannot safely support stopping, recovery or heavy vehicles. | communicate hazard |
| shoulderops.complaints.edge_drop_complaint | Shoulder edge-drop complaint | invariant | Complaint reports unsafe pavement edge, vehicle pull, bike hazard or tire damage. | respond quickly |
| shoulderops.complaints.dust_complaint | Gravel shoulder dust complaint | variant | Complaint identifies dust from traffic, dry material, grading or roadside activity. | manage nuisance |
| shoulderops.complaints.debris_complaint | Shoulder debris complaint | variant | Complaint reports objects, trash, glass, dead animals, fallen limbs or spill material. | dispatch cleanup |
| shoulderops.reporting.shoulder_condition_report | Shoulder condition report | invariant | Report summarizes defects, drop-offs, rutting, erosion, complaints and completed work. | manage network |
| shoulderops.reporting.material_usage_report | Shoulder material usage report | variant | Report tracks aggregate, asphalt, stabilizer, labor, equipment and route quantities. | control cost |
| shoulderops.metrics.dropoff_response_time | Shoulder drop-off response time KPI | invariant | KPI measures time from hazard report to make-safe or repair. | improve safety |
| shoulderops.metrics.gravel_loss_rate | Shoulder gravel loss rate KPI | variant | KPI estimates aggregate loss by route, storm, traffic, slope and maintenance cycle. | plan material |
| shoulderops.coordination.paving_program_link | Shoulder paving program link | variant | Link coordinates shoulder rebuilding with resurfacing, edge line, drainage and guardrail work. | avoid rework |
| shoulderops.coordination.vegetation_program_link | Shoulder vegetation coordination | variant | Coordination aligns mowing, brush cutting and shoulder grading to maintain clear zone. | improve access |
| shoulderops.continuity.emergency_shoulder_repair | Emergency shoulder repair | variant | Repair responds to washout, crash damage, sinkhole, flood erosion or severe drop-off. | restore safety |
| shoulderops.close.work_closeout | Road shoulder work closeout | invariant | Closeout confirms defect corrected, materials recorded, photos stored and complaint resolved. | finish work |
