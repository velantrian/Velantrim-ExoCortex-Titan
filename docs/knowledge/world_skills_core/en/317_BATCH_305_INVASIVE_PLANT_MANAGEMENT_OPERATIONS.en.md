# BATCH_305 — Invasive Plant Management Operations Detail
# world_skills_core · source: world_skills_core:batch_305:invasive_plant_management_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| invasiveops.mapping.invasive_patch | Invasive plant patch record | invariant | Record stores species, location, area, density, landowner, date and treatment history. | map infestation |
| invasiveops.mapping.survey_route | Invasive plant survey route | invariant | Route defines search area, timing, access, target species and observer. | organize survey |
| invasiveops.mapping.early_detection | Early detection invasive report | variant | Report flags new, small or high-risk infestation needing rapid response. | prevent spread |
| invasiveops.mapping.priority_zone | Invasive plant priority zone | variant | Zone ranks infestation by habitat value, spread risk, access and feasibility. | target effort |
| invasiveops.identification.species_id | Invasive plant species identification | invariant | Identification uses leaves, stems, flowers, fruits, roots, season and lookalike checks. | avoid mistakes |
| invasiveops.identification.lookalike_risk | Native lookalike risk | invariant | Risk occurs when invasive resembles native or desirable species during removal. | prevent damage |
| invasiveops.identification.phenology_window | Invasive plant phenology window | variant | Window tracks growth stage for detection, treatment timing and seed prevention. | time work |
| invasiveops.prioritization.rapid_response | Invasive rapid response priority | invariant | Priority treats small new infestations before they become established. | reduce future cost |
| invasiveops.prioritization.containment_strategy | Invasive containment strategy | variant | Strategy limits spread from large infestation when eradication is unrealistic. | manage boundaries |
| invasiveops.prioritization.asset_protection | Invasive asset protection | variant | Protection prioritizes rare habitat, waterways, trails, infrastructure or restoration sites. | protect value |
| invasiveops.removal.hand_pulling | Invasive hand pulling | invariant | Pulling removes entire plant and root where soil, species and timing make it effective. | low-impact removal |
| invasiveops.removal.digging | Invasive plant digging | variant | Digging removes roots, crowns, rhizomes or bulbs with soil disturbance control. | remove perennials |
| invasiveops.removal.cutting | Invasive plant cutting | invariant | Cutting reduces biomass or seed production but may need follow-up for regrowth. | suppress plants |
| invasiveops.removal.mowing | Invasive plant mowing | variant | Mowing treats larger areas at timed intervals before seed set. | reduce spread |
| invasiveops.removal.girdling | Invasive tree girdling | variant | Girdling interrupts vascular flow on selected woody invasive stems where appropriate. | kill standing tree |
| invasiveops.herbicide.spot_treatment | Invasive spot herbicide treatment | variant | Treatment applies approved herbicide only to target plants with minimal off-target exposure. | precise control |
| invasiveops.herbicide.cut_stump_treatment | Cut-stump invasive treatment | invariant | Treatment applies herbicide to freshly cut stump to prevent resprouting. | control woody plants |
| invasiveops.herbicide.weather_check | Herbicide weather check | invariant | Check reviews wind, rain, temperature, drift risk, water buffers and label limits. | apply safely |
| invasiveops.herbicide.applicator_record | Herbicide applicator record | invariant | Record stores certified applicator, product, rate, location, date, weather and target species. | legal trace |
| invasiveops.biocontrol.biocontrol_release | Invasive plant biocontrol release | variant | Release uses approved host-specific organisms with permits, monitoring and containment awareness. | add tool |
| invasiveops.disposal.seed_head_bagging | Invasive seed head bagging | invariant | Bagging prevents mature seeds from spreading during removal and transport. | stop spread |
| invasiveops.disposal.plant_material_disposal | Invasive plant material disposal | invariant | Disposal handles landfill, solarization, drying, burning if legal or controlled composting. | prevent regrowth |
| invasiveops.disposal.equipment_cleaning | Invasive work equipment cleaning | invariant | Cleaning removes seeds, fragments and soil from boots, tools, tires and machinery. | prevent spread |
| invasiveops.followup.regrowth_check | Invasive regrowth check | invariant | Check revisits treated patches for sprouts, missed plants or new seedlings. | sustain control |
| invasiveops.followup.seedbank_monitoring | Invasive seedbank monitoring | variant | Monitoring tracks seedlings emerging from persistent seedbank after treatment. | plan years |
| invasiveops.followup.retreatment_plan | Invasive retreatment plan | invariant | Plan schedules follow-up based on species biology, treatment success and season. | prevent rebound |
| invasiveops.restoration.revegetation | Post-removal revegetation | invariant | Revegetation installs native or desired cover after invasive removal to occupy niche. | reduce reinvasion |
| invasiveops.restoration.mulch_cover | Post-removal mulch cover | variant | Mulch suppresses seedlings, protects soil and reduces erosion where suitable. | stabilize site |
| invasiveops.restoration.erosion_risk | Invasive removal erosion risk | variant | Risk rises when removal exposes soil on slope, bank, trail or drainage area. | plan stabilization |
| invasiveops.safety.ppe | Invasive plant management PPE | invariant | PPE covers gloves, eye protection, long sleeves, respirator if needed and boots. | protect crew |
| invasiveops.safety.toxic_plant | Toxic invasive plant hazard | invariant | Hazard includes sap burns, allergens, thorns, toxic berries or irritant dust. | avoid exposure |
| invasiveops.safety.terrain_hazard | Invasive treatment terrain hazard | variant | Hazard includes slopes, wetlands, ticks, heat, water, traffic or remote work. | plan safety |
| invasiveops.volunteers.volunteer_pull | Invasive volunteer pull event | variant | Event organizes target species, tools, safety, ID training, disposal and records. | mobilize community |
| invasiveops.volunteers.quality_check | Invasive volunteer quality check | invariant | Check confirms volunteers removed target plants correctly and avoided natives. | maintain accuracy |
| invasiveops.volunteers.public_education | Invasive plant public education | variant | Education explains identification, reporting, disposal, garden alternatives and spread prevention. | reduce introductions |
| invasiveops.records.treatment_log | Invasive treatment log | invariant | Log records species, method, area, labor, material, weather, disposal and follow-up date. | trace work |
| invasiveops.records.before_after_photo | Invasive before-after photo | invariant | Photos document infestation, treatment, regrowth and restoration progress. | visual evidence |
| invasiveops.records.permission_record | Invasive management permission record | variant | Record stores landowner approval, access terms, herbicide permission and notification. | work lawfully |
| invasiveops.reporting.program_report | Invasive plant program report | invariant | Report summarizes acres surveyed, treated, species, outcomes, costs and priorities. | manage program |
| invasiveops.reporting.new_detection_notice | New invasive detection notice | variant | Notice alerts partners about new species, location, risk and response need. | coordinate response |
| invasiveops.metrics.cover_reduction | Invasive cover reduction KPI | invariant | KPI measures decrease in target invasive cover after treatment. | evaluate success |
| invasiveops.metrics.followup_completion | Invasive follow-up completion KPI | variant | KPI tracks scheduled follow-up visits completed on time. | avoid rebound |
| invasiveops.coordination.partner_network | Invasive partner network coordination | variant | Coordination links parks, roads, utilities, landowners, volunteers and conservation groups. | scale control |
| invasiveops.close.site_closeout | Invasive site closeout | invariant | Closeout records final treatment, disposal, restoration, follow-up schedule and map update. | finish cycle |
