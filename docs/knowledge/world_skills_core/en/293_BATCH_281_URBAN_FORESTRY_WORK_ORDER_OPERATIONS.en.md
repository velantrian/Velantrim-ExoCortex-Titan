# BATCH_281 — Urban Forestry Work Order Operations Detail
# world_skills_core · source: world_skills_core:batch_281:urban_forestry_work_order_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| treeops.inventory.tree_record | Urban tree record | invariant | Record stores tree ID, species, size, location, ownership, condition and maintenance history. | manage trees |
| treeops.inventory.planting_site | Tree planting site record | invariant | Site records available space, soil, utilities, sidewalk constraints, visibility and planting suitability. | choose site |
| treeops.inventory.tree_risk_zone | Tree risk zone | variant | Zone identifies targets such as roads, sidewalks, buildings, playgrounds or power lines near tree. | assess risk |
| treeops.inventory.vacant_tree_pit | Vacant tree pit record | variant | Record tracks empty planting space, stump status, soil condition and replanting priority. | plan planting |
| treeops.intake.resident_tree_request | Resident tree service request | invariant | Request captures pruning, removal, planting, roots, pests, storm damage or visibility concern. | start workflow |
| treeops.intake.emergency_tree_call | Emergency tree call | invariant | Call reports fallen limb, blocked road, power conflict, split trunk or immediate hazard. | triage danger |
| treeops.intake.duplicate_tree_request | Duplicate tree request handling | variant | Handling links repeated resident reports to existing work order or inspection record. | avoid duplication |
| treeops.inspection.tree_condition_assessment | Tree condition assessment | invariant | Assessment reviews crown, trunk, roots, lean, decay, pests, wounds and site stress. | decide action |
| treeops.inspection.risk_assessment | Tree risk assessment | invariant | Assessment combines likelihood of failure, part size, target occupancy and consequences. | prioritize safety |
| treeops.inspection.pest_disease_check | Tree pest and disease check | variant | Check observes insects, fungal signs, dieback, cankers, boring holes or leaf symptoms. | manage health |
| treeops.inspection.sidewalk_root_conflict | Sidewalk root conflict inspection | variant | Inspection evaluates root uplift, tree stability, sidewalk access and repair options. | balance assets |
| treeops.pruning.clearance_pruning | Tree clearance pruning | invariant | Pruning clears roads, sidewalks, signs, signals, buildings and streetlights within standards. | maintain clearance |
| treeops.pruning.structural_pruning | Tree structural pruning | invariant | Pruning improves branch spacing, removes weak attachments and develops stable form. | long-term health |
| treeops.pruning.deadwood_removal | Tree deadwood removal | invariant | Removal takes dead, broken or hanging branches out of crown to reduce hazard. | reduce risk |
| treeops.pruning.line_clearance_coordination | Line clearance coordination | variant | Coordination handles pruning near electric, telecom or service wires with proper owner roles. | avoid hazards |
| treeops.removal.tree_removal_order | Tree removal order | invariant | Order authorizes removal based on risk, death, disease, conflict or construction decision. | remove tree |
| treeops.removal.stump_grinding_order | Stump grinding order | invariant | Order removes stump to safe grade and prepares site for restoration or planting. | finish removal |
| treeops.removal.tree_replacement_rule | Tree replacement rule | variant | Rule defines whether, where and when removed public tree must be replaced. | preserve canopy |
| treeops.planting.species_selection | Urban tree species selection | invariant | Selection matches species to site space, climate, soil, utilities, pests and diversity goals. | plant wisely |
| treeops.planting.planting_work_order | Tree planting work order | invariant | Order specifies species, nursery stock, site prep, staking, mulch, watering and warranty. | install tree |
| treeops.planting.establishment_watering | Tree establishment watering | variant | Watering supports new trees through first seasons based on weather, soil and species. | improve survival |
| treeops.planting.mulch_ring | Tree mulch ring | variant | Mulch moderates soil moisture, protects roots and reduces mower or trimmer damage. | support health |
| treeops.storm.fallen_limb_response | Fallen limb response | invariant | Response removes limb from road, sidewalk, vehicle, structure or park and assesses tree. | restore safety |
| treeops.storm.fallen_tree_response | Fallen tree response | invariant | Response secures area, coordinates utilities, clears access, documents damage and schedules removal. | emergency recovery |
| treeops.storm.hanger_branch | Hanger branch hazard | invariant | Hazard is broken branch lodged in crown that can fall unpredictably. | remove hazard |
| treeops.storm.debris_staging | Tree storm debris staging | variant | Staging collects limbs and logs for chipping, hauling, reuse or disposal. | organize cleanup |
| treeops.notices.resident_notice | Urban forestry resident notice | invariant | Notice informs resident of inspection result, planned work, restrictions, timing and contact. | communicate action |
| treeops.notices.removal_notice | Tree removal notice | variant | Notice explains removal reason, appeal path if any, replacement and schedule. | transparent decision |
| treeops.notices.planting_notice | Tree planting notice | variant | Notice tells adjacent resident species, care expectations, watering and protection needs. | support establishment |
| treeops.workorders.pruning_work_order | Tree pruning work order | invariant | Order records tree ID, pruning type, priority, crew, equipment, traffic control and closeout. | execute pruning |
| treeops.workorders.risk_mitigation_order | Tree risk mitigation order | invariant | Order specifies pruning, cabling, monitoring, removal, access control or target reduction. | reduce risk |
| treeops.workorders.contractor_assignment | Forestry contractor assignment | variant | Assignment sends tree work to contractor with scope, standards, schedule and verification. | expand capacity |
| treeops.safety.chainsaw_safety | Urban forestry chainsaw safety | invariant | Safety covers PPE, drop zone, saw handling, kickback, communication and emergency plan. | protect crew |
| treeops.safety.aerial_tree_work | Aerial tree work safety | invariant | Safety covers bucket truck, climbing, rigging, fall protection, traffic and overhead hazards. | safe access |
| treeops.safety.traffic_control | Tree crew traffic control | invariant | Control protects workers and road users during pruning, removal, chipping or loading. | work safely |
| treeops.data.photo_documentation | Tree work photo documentation | invariant | Photos show condition, defect, work performed, stump, planting and site restoration. | evidence |
| treeops.data.gis_canopy_update | Urban forestry GIS canopy update | variant | Update records tree status, new planting, removal, species correction or work history. | keep inventory |
| treeops.reporting.work_backlog_report | Urban forestry work backlog report | invariant | Report summarizes open requests by type, priority, age, district and crew assignment. | manage demand |
| treeops.reporting.canopy_change_report | Urban canopy change report | variant | Report tracks removals, plantings, survival, species diversity and canopy goals. | monitor canopy |
| treeops.metrics.request_cycle_time | Tree request cycle time KPI | invariant | KPI measures time from request to inspection, decision and work completion. | improve service |
| treeops.metrics.planting_survival_rate | Tree planting survival rate KPI | variant | KPI tracks newly planted trees alive after establishment period by species, contractor and site. | improve planting |
| treeops.coordination.sidewalk_program | Urban forestry sidewalk coordination | variant | Coordination aligns root, pruning, removal or planting decisions with sidewalk repairs. | reduce conflict |
| treeops.coordination.utility_notification | Tree work utility notification | variant | Notification informs utility owner of work near lines, service drops, poles or underground plant. | prevent incident |
| treeops.close.work_order_closeout | Urban forestry work order closeout | invariant | Closeout confirms work done, debris removed, photos stored, inventory updated and notice complete. | finish case |
