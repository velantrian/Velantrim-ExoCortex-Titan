# BATCH_300 — Urban Farm Operations Detail
# world_skills_core · source: world_skills_core:batch_300:urban_farm_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| urbanfarmops.planning.farm_plan | Urban farm plan | invariant | Plan defines crops, beds, soil, irrigation, volunteers, harvest, distribution and records. | organize season |
| urbanfarmops.planning.crop_calendar | Urban farm crop calendar | invariant | Calendar schedules seeding, transplanting, succession planting, harvest and bed turnover. | time work |
| urbanfarmops.planning.bed_layout | Urban farm bed layout | invariant | Layout maps beds, paths, irrigation lines, compost, wash area, storage and access. | use space |
| urbanfarmops.planning.production_target | Urban farm production target | variant | Target estimates harvest volume by crop, bed, season, donation or sales channel. | plan output |
| urbanfarmops.soil.soil_test | Urban farm soil test | invariant | Test checks nutrients, pH, organic matter, texture, salts and potential contaminants. | guide amendments |
| urbanfarmops.soil.amendment_plan | Urban farm amendment plan | invariant | Plan adds compost, lime, fertilizer or organic matter based on soil test and crop needs. | improve soil |
| urbanfarmops.soil.compaction_management | Urban farm compaction management | variant | Management uses paths, broadforking, mulch, cover crops and restricted traffic. | protect beds |
| urbanfarmops.soil.contamination_control | Urban farm soil contamination control | invariant | Control uses raised beds, clean soil, testing, crop restrictions or barriers where needed. | food safety |
| urbanfarmops.irrigation.irrigation_zone | Urban farm irrigation zone | invariant | Zone groups beds by crop water need, valve, pressure, hose or drip line. | water efficiently |
| urbanfarmops.irrigation.drip_line_check | Urban farm drip line check | invariant | Check finds clogs, leaks, pressure problems, missing emitters and damaged tubing. | maintain irrigation |
| urbanfarmops.irrigation.water_schedule | Urban farm watering schedule | variant | Schedule adjusts timing by weather, crop stage, soil moisture and water rules. | prevent stress |
| urbanfarmops.irrigation.rainwater_use | Urban farm rainwater use | variant | Use manages tanks, first flush, screens, pumps, irrigation limits and safety. | conserve water |
| urbanfarmops.crops.seed_starting | Urban farm seed starting | invariant | Starting controls tray media, moisture, temperature, light, labels and hardening before transplant. | produce seedlings |
| urbanfarmops.crops.transplanting | Urban farm transplanting | invariant | Transplanting sets spacing, depth, watering, timing, weather and plant handling. | establish crops |
| urbanfarmops.crops.succession_planting | Succession planting | variant | Planting staggers sowing dates to maintain continuous harvest. | smooth supply |
| urbanfarmops.crops.cover_crop | Urban farm cover crop | variant | Cover crop protects soil, adds biomass, suppresses weeds and supports fertility. | improve beds |
| urbanfarmops.pests.scouting | Urban farm pest scouting | invariant | Scouting checks insects, disease, weeds, animal damage and stress by crop. | detect early |
| urbanfarmops.pests.ipm_action | Urban farm IPM action | invariant | Action uses prevention, monitoring, thresholds, physical controls and approved treatments. | manage pests |
| urbanfarmops.pests.exclusion_netting | Urban farm exclusion netting | variant | Netting protects crops from insects, birds or small mammals while allowing growth. | reduce damage |
| urbanfarmops.harvest.harvest_window | Urban farm harvest window | invariant | Window defines crop maturity, weather, distribution deadline and staff availability. | harvest quality |
| urbanfarmops.harvest.harvest_log | Urban farm harvest log | invariant | Log records crop, quantity, bed, date, destination, quality and handler. | track yield |
| urbanfarmops.harvest.postharvest_handling | Urban farm postharvest handling | invariant | Handling includes cooling, washing if appropriate, sorting, packing and shade. | preserve quality |
| urbanfarmops.harvest.cull_management | Urban farm cull management | variant | Culls are composted, donated if safe, fed to approved use or discarded. | reduce waste |
| urbanfarmops.foodsafety.wash_station | Urban farm wash station | invariant | Station separates dirty harvest, potable water, clean surfaces, drainage and tools. | reduce contamination |
| urbanfarmops.foodsafety.wash_water_disposal | Urban farm wash water disposal | variant | Disposal routes produce wash water away from clean areas, crops and storm drains. | prevent contamination |
| urbanfarmops.foodsafety.tool_sanitation | Urban farm tool sanitation | invariant | Sanitation cleans knives, bins, tables and harvest containers between uses. | food safety |
| urbanfarmops.foodsafety.traceability | Urban farm produce traceability | invariant | Traceability links produce to bed, harvest date, handler and distribution destination. | recall readiness |
| urbanfarmops.foodsafety.worker_hygiene | Urban farm worker hygiene | invariant | Hygiene includes handwashing, illness policy, gloves if used, toilets and training. | protect produce |
| urbanfarmops.volunteers.volunteer_shift | Urban farm volunteer shift | invariant | Shift assigns tasks, supervisor, tools, safety briefing, sign-in and closeout. | organize help |
| urbanfarmops.volunteers.skill_task_match | Urban farm skill-task match | variant | Match assigns volunteers to seeding, weeding, harvest, wash, delivery or maintenance by ability. | work safely |
| urbanfarmops.volunteers.youth_program | Urban farm youth program | variant | Program adapts tools, supervision, tasks, consent and learning goals for youth participants. | safe education |
| urbanfarmops.distribution.donation_delivery | Urban farm donation delivery | invariant | Delivery records recipient, crop, weight, time, food safety condition and confirmation. | feed community |
| urbanfarmops.distribution.market_box | Urban farm market box | variant | Box combines crops for sale or share with packing list and quality check. | distribute produce |
| urbanfarmops.distribution.cold_handoff | Urban farm cold handoff | variant | Handoff maintains shade, cooling, time control and clean containers until recipient receives produce. | preserve quality |
| urbanfarmops.infrastructure.tool_storage | Urban farm tool storage | invariant | Storage keeps tools clean, dry, secure, labeled and safe to access. | protect assets |
| urbanfarmops.infrastructure.fence_gate | Urban farm fence and gate | invariant | Fence and gate manage security, animals, hours, deliveries and emergency access. | protect site |
| urbanfarmops.infrastructure.shade_structure | Urban farm shade structure | variant | Structure supports workers, wash station, seedlings or harvest staging. | reduce heat |
| urbanfarmops.records.input_record | Urban farm input record | invariant | Record tracks seeds, compost, amendments, treatments, suppliers, dates and beds. | trace inputs |
| urbanfarmops.records.crop_failure_record | Urban farm crop failure record | variant | Record captures cause, weather, pest, soil issue, planting date and lesson. | improve plan |
| urbanfarmops.reporting.production_report | Urban farm production report | invariant | Report summarizes harvest totals, crop performance, volunteer hours, distribution and losses. | evaluate season |
| urbanfarmops.metrics.yield_per_bed | Urban farm yield per bed KPI | invariant | KPI compares harvest weight or count to bed area and crop plan. | improve productivity |
| urbanfarmops.metrics.volunteer_retention | Urban farm volunteer retention KPI | variant | KPI tracks repeat participation, training completion and task reliability. | manage people |
| urbanfarmops.coordination.food_bank_link | Urban farm food bank coordination | variant | Coordination aligns crop preferences, delivery times, packaging and food safety needs. | match demand |
| urbanfarmops.close.season_closeout | Urban farm season closeout | invariant | Closeout clears crops, plants cover, stores tools, winterizes water and updates records. | finish season |
