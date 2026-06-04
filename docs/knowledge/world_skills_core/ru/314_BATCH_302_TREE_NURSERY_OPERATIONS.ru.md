# BATCH_302 — Tree Nursery Operations Detail
# world_skills_core · source: world_skills_core:batch_302:tree_nursery_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| treenurseryops.inventory.nursery_record | Tree nursery record | invariant | Record stores site, beds, containers, species, irrigation, inventory, staff and history. | manage nursery |
| treenurseryops.inventory.plant_lot | Nursery plant lot | invariant | Lot groups trees by species, source, propagation date, container size and status. | trace stock |
| treenurseryops.inventory.species_mix | Tree nursery species mix | variant | Mix balances climate suitability, diversity, site demand, pest risk and program goals. | plan inventory |
| treenurseryops.inventory.size_class | Tree nursery size class | invariant | Class groups seedlings, liners, containers, balled stock or caliper sizes. | organize stock |
| treenurseryops.propagation.seed_collection | Tree seed collection | variant | Collection records species, location, date, permission, ripeness and storage conditions. | start stock |
| treenurseryops.propagation.seed_treatment | Tree seed treatment | invariant | Treatment may include cleaning, stratification, scarification, soaking or temperature control. | improve germination |
| treenurseryops.propagation.cutting_propagation | Tree cutting propagation | variant | Propagation uses cuttings, rooting media, humidity, hormone if allowed and labels. | clone plants |
| treenurseryops.propagation.germination_record | Tree germination record | invariant | Record tracks sowing date, medium, temperature, moisture, emergence and survival. | monitor success |
| treenurseryops.potting.potting_media | Tree potting media | invariant | Media supports drainage, aeration, moisture and nutrients suitable for tree roots. | grow healthy stock |
| treenurseryops.potting.upshift | Tree nursery upshift | invariant | Upshift moves plant into larger container before root restriction harms growth. | maintain vigor |
| treenurseryops.potting.root_pruning | Tree nursery root pruning | variant | Pruning corrects circling, kinked or excessive roots during container production. | improve structure |
| treenurseryops.potting.labeling | Tree nursery labeling | invariant | Label identifies species, lot, date, size, source and treatment history. | prevent mixups |
| treenurseryops.irrigation.irrigation_zone | Tree nursery irrigation zone | invariant | Zone groups stock by water need, container size, exposure and valve layout. | water accurately |
| treenurseryops.irrigation.moisture_check | Nursery moisture check | invariant | Check assesses container or bed moisture, drainage, wilt, overwatering and weather. | prevent stress |
| treenurseryops.irrigation.emitter_check | Nursery emitter check | variant | Check finds clogged, missing, misaligned or leaking emitters and uneven coverage. | maintain irrigation |
| treenurseryops.irrigation.water_quality | Nursery water quality | variant | Quality includes salts, pH, alkalinity, contaminants and suitability for irrigation. | protect plants |
| treenurseryops.nutrition.fertilizer_plan | Tree nursery fertilizer plan | invariant | Plan sets nutrient type, rate, timing and monitoring by species and growth stage. | support growth |
| treenurseryops.nutrition.deficiency_check | Tree nutrient deficiency check | variant | Check observes chlorosis, poor growth, leaf symptoms, soil test or media issue. | diagnose nutrition |
| treenurseryops.pest.scouting | Tree nursery pest scouting | invariant | Scouting checks insects, disease, weeds, browsing, root problems and environmental stress. | detect early |
| treenurseryops.pest.quarantine_hold | Nursery quarantine hold | invariant | Hold isolates suspect stock after pest, disease, invasive weed or source concern. | prevent spread |
| treenurseryops.pest.weed_control | Tree nursery weed control | variant | Control uses mulching, hand weeding, sanitation, spacing or approved treatments. | reduce competition |
| treenurseryops.structure.staking | Tree nursery staking | variant | Staking supports young trees when needed without restricting trunk development. | improve form |
| treenurseryops.structure.pruning | Tree nursery structural pruning | invariant | Pruning develops leader, branch spacing, clearance and stable future form. | produce quality |
| treenurseryops.structure.spacing | Nursery spacing | invariant | Spacing prevents crowding, poor airflow, leaning, shade stress and access problems. | maintain quality |
| treenurseryops.hardening.hardening_off | Tree hardening off | invariant | Hardening gradually exposes plants to outdoor light, wind, temperature and water stress. | prepare planting |
| treenurseryops.hardening.winter_protection | Nursery winter protection | variant | Protection includes grouping, mulch, covers, windbreaks, irrigation and freeze monitoring. | reduce losses |
| treenurseryops.hardening.transport_readiness | Tree transport readiness | invariant | Readiness checks watering, staking, labels, rootball, container stability and load sequence. | ship safely |
| treenurseryops.distribution.plant_request | Tree nursery plant request | invariant | Request records species, size, quantity, destination, planting date and program. | allocate stock |
| treenurseryops.distribution.stock_reservation | Nursery stock reservation | variant | Reservation holds plants for project, school, park, giveaway or replacement planting. | prevent conflicts |
| treenurseryops.distribution.delivery_record | Tree nursery delivery record | invariant | Record tracks plants, lot, condition, recipient, route, date and acceptance. | trace handoff |
| treenurseryops.quality.root_quality_check | Tree root quality check | invariant | Check looks for circling, girdling, kinked, dry, diseased or insufficient roots. | plant success |
| treenurseryops.quality.crown_quality_check | Tree crown quality check | invariant | Check reviews leader, branch structure, damage, pests, vigor and species form. | deliver quality |
| treenurseryops.quality.specification_match | Tree nursery specification match | variant | Match confirms species, size, container, health and form meet project requirements. | avoid rejection |
| treenurseryops.safety.lifting_handling | Nursery lifting and handling safety | invariant | Safety covers heavy containers, carts, posture, team lifts, wet surfaces and gloves. | protect staff |
| treenurseryops.safety.tool_safety | Tree nursery tool safety | invariant | Safety covers pruners, knives, saws, potting tools, sanitation and storage. | prevent injury |
| treenurseryops.safety.heat_work | Tree nursery heat work safety | variant | Safety adjusts shifts, water, shade and workload during hot nursery operations. | protect workers |
| treenurseryops.records.propagation_log | Tree nursery propagation log | invariant | Log records seed or cutting source, treatment, date, media, germination and success. | trace origins |
| treenurseryops.records.pest_treatment_log | Tree nursery pest treatment log | invariant | Log tracks pest issue, treatment, date, lot, applicator, result and restrictions. | document control |
| treenurseryops.records.inventory_count | Tree nursery inventory count | invariant | Count reconciles living stock, losses, reservations, distributions and size classes. | know stock |
| treenurseryops.reporting.loss_report | Tree nursery loss report | variant | Report summarizes mortality by species, lot, cause, season and production stage. | improve process |
| treenurseryops.metrics.survival_rate | Tree nursery survival rate KPI | invariant | KPI tracks living plants versus started or received plants by lot and species. | assess quality |
| treenurseryops.metrics.ready_stock_rate | Tree nursery ready-stock rate KPI | variant | KPI measures share of requested plants meeting quality and size at distribution time. | meet demand |
| treenurseryops.coordination.planting_program | Tree nursery planting program coordination | variant | Coordination matches nursery stock with parks, streets, schools, restoration or giveaway schedules. | align supply |
| treenurseryops.close.season_closeout | Tree nursery season closeout | invariant | Closeout updates inventory, losses, winter protection, records, sanitation and next season needs. | finish season |
