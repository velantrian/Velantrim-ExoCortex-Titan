# BATCH_301 — Compost Site Operations Detail
# world_skills_core · source: world_skills_core:batch_301:compost_site_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| compostops.inventory.site_record | Compost site record | invariant | Record stores location, capacity, feedstock types, piles, equipment, users and permit status. | manage site |
| compostops.inventory.pile_record | Compost pile record | invariant | Record tracks pile ID, start date, feedstock, volume, temperature, turns and maturity. | trace batch |
| compostops.inventory.feedstock_source | Compost feedstock source | invariant | Source identifies leaves, food scraps, wood chips, garden waste, manure or market waste. | control inputs |
| compostops.intake.feedstock_check | Compost feedstock check | invariant | Check screens material for contamination, moisture, odor, size and allowed status. | protect pile |
| compostops.intake.contamination_rejection | Compost contamination rejection | invariant | Rejection removes plastic, metal, glass, chemicals, diseased waste or prohibited material. | keep clean |
| compostops.intake.carbon_nitrogen_balance | Compost carbon nitrogen balance | invariant | Balance mixes brown carbon-rich and green nitrogen-rich materials for microbial activity. | compost efficiently |
| compostops.intake.bulking_agent | Compost bulking agent | variant | Agent such as wood chips improves structure, porosity and odor control. | improve aeration |
| compostops.moisture.moisture_check | Compost moisture check | invariant | Check estimates whether pile is too dry, too wet or near optimal moisture. | guide watering |
| compostops.moisture.water_addition | Compost water addition | variant | Addition moistens dry pile during building or turning without causing runoff. | support microbes |
| compostops.moisture.excess_moisture | Excess compost moisture | invariant | Excess moisture causes anaerobic conditions, odor, leachate and slow decomposition. | prevent nuisance |
| compostops.temperature.temperature_log | Compost temperature log | invariant | Log records pile temperature by depth, location, date and operator. | monitor process |
| compostops.temperature.thermophilic_phase | Compost thermophilic phase | invariant | Phase uses high microbial heat to accelerate decomposition and reduce pathogens if managed. | process safely |
| compostops.temperature.cool_pile | Cool compost pile | variant | Cool pile may indicate low nitrogen, dryness, small size, poor aeration or maturity. | diagnose issue |
| compostops.turning.turn_schedule | Compost turning schedule | invariant | Schedule sets when pile is mixed based on temperature, oxygen, moisture and odor. | aerate pile |
| compostops.turning.loader_turning | Compost loader turning | variant | Loader turning mixes pile with bucket while managing space, safety and contamination. | process volume |
| compostops.turning.hand_turning | Compost hand turning | variant | Hand turning suits small bins and uses forks, aerators or manual mixing. | maintain small site |
| compostops.aeration.passive_aeration | Passive compost aeration | invariant | Aeration uses structure, perforated pipes or pile design to provide oxygen without frequent turning. | reduce labor |
| compostops.aeration.odor_from_anaerobic | Anaerobic compost odor | invariant | Odor indicates low oxygen, excess moisture, compacted pile or wrong feedstock balance. | correct process |
| compostops.curing.curing_pile | Compost curing pile | invariant | Curing allows compost to stabilize after active decomposition before use or distribution. | finish product |
| compostops.curing.maturity_check | Compost maturity check | invariant | Check reviews temperature stability, smell, texture, recognizable feedstock and plant safety. | avoid immature use |
| compostops.curing.screening | Compost screening | variant | Screening removes oversized wood, plastic, stones and unfinished material from finished compost. | improve quality |
| compostops.odors.odor_complaint | Compost odor complaint | invariant | Complaint records location, wind, feedstock, pile condition, timing and corrective action. | manage nuisance |
| compostops.odors.cover_material | Compost cover material | variant | Cover material such as leaves, finished compost or chips reduces odors and flies. | control surface |
| compostops.odors.leachate_control | Compost leachate control | invariant | Control prevents liquid runoff through site grading, cover, moisture management and containment. | protect water |
| compostops.pests.fly_control | Compost fly control | invariant | Control uses prompt covering, moisture balance, pile heat, screening and clean site edges. | reduce pests |
| compostops.pests.rodent_prevention | Compost rodent prevention | invariant | Prevention excludes meat, secures bins, covers feedstocks, removes spills and monitors burrows. | protect site |
| compostops.pests.wildlife_contact | Compost wildlife contact | variant | Contact risk increases with exposed food waste, odors, open bins or poor fencing. | adjust operations |
| compostops.users.dropoff_user_rule | Compost drop-off user rule | invariant | Rule tells users accepted materials, hours, contamination limits, container use and contact path. | guide users |
| compostops.users.training | Compost user training | variant | Training explains sorting, pile building, safety, tools, reporting and finished compost use. | reduce errors |
| compostops.users.volunteer_shift | Compost volunteer shift | variant | Shift assigns intake monitoring, turning, screening, cleanup and record tasks. | organize labor |
| compostops.equipment.thermometer | Compost thermometer | invariant | Thermometer measures internal pile heat and must be clean, long enough and readable. | monitor pile |
| compostops.equipment.loader_safety | Compost loader safety | invariant | Safety covers pedestrians, pile stability, slopes, backing, visibility and bucket handling. | prevent incidents |
| compostops.equipment.screen_maintenance | Compost screen maintenance | variant | Maintenance checks mesh, frame, motor, guards, clogging and cleaned oversized material. | keep screening |
| compostops.safety.bioaerosol_dust | Compost bioaerosol and dust safety | invariant | Safety reduces inhalation through moisture control, masks if needed, wind awareness and hygiene. | protect workers |
| compostops.safety.sharps_contamination | Compost sharps contamination | invariant | Sharps require stop, isolation, safe removal, reporting and possible feedstock source review. | prevent injury |
| compostops.safety.heat_pile_burn | Hot compost pile burn risk | variant | Risk occurs from hot pile interiors, steam, equipment surfaces or spontaneous heating concern. | work safely |
| compostops.records.input_log | Compost input log | invariant | Log records feedstock type, source, date, volume, contamination and operator. | trace inputs |
| compostops.records.turning_log | Compost turning log | invariant | Log records turn date, pile ID, temperature, moisture, odor and actions. | document process |
| compostops.records.distribution_log | Compost distribution log | variant | Log records finished compost volume, recipient, date, quality and restrictions. | track output |
| compostops.reporting.site_report | Compost site operations report | invariant | Report summarizes inputs, outputs, contamination, odors, temperatures, labor and complaints. | manage site |
| compostops.metrics.contamination_rate | Compost contamination rate KPI | invariant | KPI measures rejected or removed contamination by source, period and material type. | improve sorting |
| compostops.metrics.processing_time | Compost processing time KPI | variant | KPI tracks days from pile creation to mature compost by recipe and season. | improve process |
| compostops.coordination.waste_program | Compost waste program coordination | variant | Coordination aligns collection, education, market waste, haulers and compost users. | integrate service |
| compostops.close.batch_closeout | Compost batch closeout | invariant | Closeout confirms maturity, screening, distribution, records, pile cleanup and lessons learned. | finish batch |
