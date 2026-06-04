# BATCH_280 — Catch Basin Maintenance Operations Detail
# world_skills_core · source: world_skills_core:batch_280:catch_basin_maintenance_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| catchbasinops.inventory.basin_record | Catch basin asset record | invariant | Record stores basin ID, location, grate type, sump depth, outlet, condition and ownership. | manage asset |
| catchbasinops.inventory.drainage_area | Catch basin drainage area | invariant | Area identifies streets, parcels, slopes and surfaces contributing runoff to the basin. | understand load |
| catchbasinops.inventory.outlet_connection | Catch basin outlet connection | invariant | Connection links basin to storm pipe, combined sewer, ditch, pond or outfall. | trace flow |
| catchbasinops.inventory.priority_basin | Priority catch basin | variant | Priority basin has flood history, heavy debris, steep approach, school route or critical facility nearby. | rank work |
| catchbasinops.inspection.routine_basin_inspection | Routine catch basin inspection | invariant | Inspection checks grate, frame, sump sediment, standing water, outlet, odor and structural condition. | find needs |
| catchbasinops.inspection.prestorm_check | Pre-storm basin check | variant | Check clears high-risk basins before forecast heavy rain or snowmelt. | prevent flooding |
| catchbasinops.inspection.poststorm_check | Post-storm basin check | variant | Check reviews clogged grates, ponding, washout, sediment movement and new damage after storm. | verify recovery |
| catchbasinops.inspection.confined_space_screen | Catch basin confined-space screen | invariant | Screen determines entry risk, atmospheric hazards, access limits and permit requirements. | protect workers |
| catchbasinops.condition.clogged_grate | Clogged catch basin grate | invariant | Clog blocks surface inflow with leaves, trash, sediment, snow, ice or debris. | restore intake |
| catchbasinops.condition.sediment_sump | Catch basin sediment sump | invariant | Sump stores sand, grit and solids that must be removed before reducing capacity. | maintain storage |
| catchbasinops.condition.standing_water | Catch basin standing water | variant | Standing water may indicate blocked outlet, flat grade, sump design, sediment or pipe obstruction. | diagnose drainage |
| catchbasinops.condition.frame_settlement | Catch basin frame settlement | invariant | Settlement creates pavement dip, trip hazard, ponding or grate misalignment around structure. | repair frame |
| catchbasinops.condition.broken_grate | Broken catch basin grate | invariant | Broken grate creates vehicle, bicycle, pedestrian and debris-entry hazards. | replace grate |
| catchbasinops.condition.structural_crack | Catch basin structural crack | variant | Crack in wall, frame or lid may indicate load damage, settlement or deterioration. | plan repair |
| catchbasinops.cleaning.vacuum_cleaning | Catch basin vacuum cleaning | invariant | Cleaning removes sediment, water and debris using vacuum truck and proper disposal. | restore capacity |
| catchbasinops.cleaning.hand_clear_grate | Catch basin hand grate clearing | invariant | Clearing removes surface debris without full vacuum cleaning when sump capacity remains. | quick fix |
| catchbasinops.cleaning.jetting_outlet | Catch basin outlet jetting | variant | Jetting clears lateral blockage, sediment, roots or grease-like deposits from outlet pipe. | restore flow |
| catchbasinops.cleaning.leaf_season_cleaning | Leaf season basin cleaning | variant | Cleaning targets basins before and during heavy leaf fall to reduce flooding. | seasonal control |
| catchbasinops.repairs.frame_reset | Catch basin frame reset | invariant | Reset adjusts frame and grate to pavement elevation with stable support and patching. | remove dip |
| catchbasinops.repairs.grate_replacement | Catch basin grate replacement | invariant | Replacement uses correct size, load rating, bicycle-safe pattern and seating. | restore safety |
| catchbasinops.repairs.masonry_repair | Catch basin masonry repair | variant | Repair fixes brick, block, mortar, concrete wall or chimney deterioration. | preserve structure |
| catchbasinops.repairs.outlet_repair | Catch basin outlet repair | variant | Repair addresses broken pipe, offset joint, root intrusion or collapsed connection. | restore drainage |
| catchbasinops.flooding.local_ponding | Local ponding complaint | invariant | Complaint records water depth, duration, storm intensity, blocked basin and affected property. | triage flooding |
| catchbasinops.flooding.repeat_flood_location | Repeat flood location | variant | Location has recurring ponding requiring drainage review beyond simple cleaning. | root cause |
| catchbasinops.flooding.emergency_basin_response | Emergency catch basin response | invariant | Response clears blocked basin during active flooding with traffic and crew safety controls. | reduce damage |
| catchbasinops.environment.sediment_disposal | Catch basin sediment disposal | invariant | Disposal follows rules for wet sediment, contamination, dewatering, transport and documentation. | legal handling |
| catchbasinops.environment.illicit_discharge_sign | Illicit discharge sign | invariant | Sign includes unusual odor, color, sheen, sewage, chemicals or dry-weather flow. | trigger investigation |
| catchbasinops.environment.floatable_trash | Catch basin floatable trash | variant | Trash retained at inlet or sump can enter waterways if not removed. | reduce pollution |
| catchbasinops.equipment.vac_truck_setup | Vacuum truck setup | invariant | Setup positions truck, cones, hose, boom, water supply and safe work zone. | clean safely |
| catchbasinops.equipment.nozzle_selection | Jetting nozzle selection | variant | Nozzle choice depends on pipe size, blockage type, distance, roots and sediment load. | clear blockage |
| catchbasinops.equipment.hose_decontamination | Basin cleaning hose decontamination | variant | Decontamination removes contaminated material before transport, storage or maintenance. | hygiene |
| catchbasinops.safety.traffic_control | Catch basin traffic control | invariant | Control protects crews working at curb, lane, intersection or bike lane inlets. | worker safety |
| catchbasinops.safety.grate_lifting | Catch basin grate lifting safety | invariant | Safety covers heavy grates, pinch points, hooks, ergonomics and unstable frames. | avoid injury |
| catchbasinops.safety.atmospheric_hazard | Catch basin atmospheric hazard | invariant | Hazard includes low oxygen, toxic gas, flammable vapor or sewer gas near structure. | prevent exposure |
| catchbasinops.data.cleaning_record | Catch basin cleaning record | invariant | Record stores date, crew, sediment quantity, condition, photos, defects and disposal. | maintenance history |
| catchbasinops.data.gis_update | Catch basin GIS update | variant | Update corrects location, attributes, connection, inspection status or missing asset. | improve map |
| catchbasinops.reporting.flooding_report | Catch basin flooding report | invariant | Report summarizes ponding calls, blocked basins, response actions, damage and follow-up work. | manage risk |
| catchbasinops.reporting.sediment_report | Catch basin sediment report | variant | Report tracks removed sediment volume, hotspots, disposal weights and cleaning frequency. | plan service |
| catchbasinops.metrics.cleaning_cycle | Catch basin cleaning cycle KPI | invariant | KPI measures time or interval between cleanings for priority and normal basins. | schedule work |
| catchbasinops.metrics.clog_recurrence | Catch basin clog recurrence KPI | variant | KPI tracks repeated clogs by basin, debris type, season and upstream source. | target prevention |
| catchbasinops.coordination.street_sweeping_link | Catch basin street sweeping link | variant | Link coordinates inlet cleaning with sweeping routes to reduce sediment and leaf load. | prevent clogs |
| catchbasinops.coordination.utility_conflict | Catch basin utility conflict | variant | Conflict involves underground utilities, road work or private drainage connected to basin. | avoid damage |
| catchbasinops.continuity.winter_inlet_blockage | Winter catch basin blockage | variant | Blockage comes from snow windrows, ice, frozen grates or meltwater refreeze. | winter drainage |
| catchbasinops.close.work_order_closeout | Catch basin work order closeout | invariant | Closeout confirms cleaning or repair, photos, disposal record, map update and complaint response. | finish work |
