# BATCH_298 — Outdoor Market Sanitation Operations Detail
# world_skills_core · source: world_skills_core:batch_298:outdoor_market_sanitation_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| marketsanops.planning.sanitation_plan | Outdoor market sanitation plan | invariant | Plan defines waste, toilets, handwashing, cleaning, pests, grease, greywater and closeout. | organize hygiene |
| marketsanops.planning.vendor_sanitation_rules | Vendor sanitation rules | invariant | Rules state waste handling, food debris control, handwashing, grease, cleanup and prohibited dumping. | set expectations |
| marketsanops.planning.site_layout | Market sanitation site layout | invariant | Layout places bins, toilets, wash stations, food vendors, drains and service vehicle routes. | reduce mess |
| marketsanops.waste.vendor_waste_stream | Vendor waste stream | invariant | Waste stream includes packaging, food scraps, produce trim, cardboard, liquids and disposables. | plan bins |
| marketsanops.waste.bin_placement | Market bin placement | invariant | Placement makes bins visible, accessible, serviced and separated from food prep where needed. | encourage disposal |
| marketsanops.waste.cardboard_collection | Market cardboard collection | variant | Collection manages flattened boxes, dry storage, pickup timing and contamination control. | improve recycling |
| marketsanops.waste.food_scrap_collection | Market food scrap collection | variant | Collection separates organic waste where program, bins, liners and hauling are available. | reduce landfill |
| marketsanops.waste.overflow_response | Market waste overflow response | invariant | Response adds service, replaces liners, clears ground litter and records high-demand points. | prevent pests |
| marketsanops.toilets.portable_toilet_count | Portable toilet count | invariant | Count estimates required units from attendance, duration, food service and accessibility needs. | provide capacity |
| marketsanops.toilets.accessible_toilet | Accessible market toilet | invariant | Toilet supports accessible route, clear space, signage, serviceability and placement. | inclusive access |
| marketsanops.toilets.toilet_service_schedule | Market toilet service schedule | invariant | Schedule sets cleaning, pumping, restocking, inspection and emergency service timing. | maintain hygiene |
| marketsanops.toilets.toilet_odor_control | Market toilet odor control | variant | Control uses service frequency, ventilation, additives, placement and spill response. | improve comfort |
| marketsanops.handwashing.handwash_station | Outdoor market handwash station | invariant | Station provides water, soap, towels, waste container and drainage where required. | support hygiene |
| marketsanops.handwashing.station_refill | Handwash station refill | invariant | Refill restores water, soap, towels and wastewater capacity during market hours. | keep usable |
| marketsanops.handwashing.food_vendor_handwash | Food vendor handwash requirement | invariant | Requirement ensures food vendors have handwashing access separate from utensil washing. | food safety |
| marketsanops.cleaning.pre_market_check | Pre-market sanitation check | invariant | Check confirms site clean, bins placed, toilets serviced, wash stations stocked and hazards removed. | open ready |
| marketsanops.cleaning.during_market_patrol | During-market sanitation patrol | invariant | Patrol checks litter, spills, bins, toilets, wash stations, vendor waste and pests. | maintain site |
| marketsanops.cleaning.post_market_cleanup | Post-market cleanup | invariant | Cleanup removes waste, sweeps site, checks stains, services toilets and verifies vendor spaces. | close clean |
| marketsanops.cleaning.spill_response | Market spill response | variant | Response cleans food, drink, oil, wastewater or broken container spills before slips or contamination. | prevent hazards |
| marketsanops.pests.pest_attractant | Market pest attractant | invariant | Attractants include exposed food, overflowing bins, grease, greywater, cardboard and standing water. | prevent pests |
| marketsanops.pests.rodent_observation | Market rodent observation | variant | Observation records droppings, sightings, gnawing, burrows or vendor waste issues. | trigger control |
| marketsanops.pests.insect_control | Market insect control | variant | Control reduces flies, wasps and ants through waste timing, covers, cleaning and vendor practices. | protect food |
| marketsanops.grease.grease_container | Market grease container | invariant | Container collects used cooking oil safely with lid, labeling, placement and pickup plan. | prevent dumping |
| marketsanops.grease.grease_spill | Market grease spill | invariant | Spill creates slip, odor, pest and storm drain risk requiring absorbent and disposal. | respond safely |
| marketsanops.grease.food_truck_grease | Food truck grease control | variant | Control prevents discharge from fryers, traps, mats or washdown into pavement or drains. | protect site |
| marketsanops.greywater.greywater_collection | Market greywater collection | invariant | Collection captures wastewater from handwashing, dishwashing or food prep for proper disposal. | avoid dumping |
| marketsanops.greywater.illegal_discharge | Market illegal greywater discharge | invariant | Discharge into storm drain, tree pit, street or landscape can violate sanitation rules. | enforce rules |
| marketsanops.greywater.wastewater_capacity | Market wastewater capacity | variant | Capacity ensures tanks, containers or service can hold expected wastewater until disposal. | prevent overflow |
| marketsanops.vendor_checks.vendor_space_closeout | Vendor space closeout | invariant | Closeout checks each stall for waste, spills, grease, damage and removed equipment. | enforce cleanup |
| marketsanops.vendor_checks.food_vendor_check | Food vendor sanitation check | invariant | Check reviews handwashing, waste, temperature support, utensil wash setup and wastewater handling. | reduce risk |
| marketsanops.vendor_checks.noncompliance_notice | Vendor sanitation noncompliance notice | invariant | Notice documents rule breach, correction deadline, fee, suspension or referral. | enforce standards |
| marketsanops.safety.slip_trip_hazard | Market sanitation slip or trip hazard | invariant | Hazard includes wet pavement, cords, mats, boxes, broken containers or food spills. | prevent injury |
| marketsanops.safety.sharps_broken_glass | Market sharps or broken glass | variant | Hazard requires safe pickup, container, PPE and area control. | protect workers |
| marketsanops.safety.cleaner_ppe | Market cleaner PPE | invariant | PPE includes gloves, eye protection, high visibility, footwear and biohazard supplies. | protect staff |
| marketsanops.records.sanitation_log | Market sanitation log | invariant | Log records checks, service times, issues, corrective actions, complaints and closeout. | prove service |
| marketsanops.records.service_ticket | Market sanitation service ticket | invariant | Ticket records toilet pumping, waste hauling, street cleaning, pressure washing or pest service. | trace vendors |
| marketsanops.reporting.closeout_report | Outdoor market sanitation closeout report | invariant | Report summarizes waste volumes, issues, vendor compliance, cleaning, complaints and costs. | improve market |
| marketsanops.reporting.waste_volume_report | Market waste volume report | variant | Report tracks trash, recycling, organics, grease and cardboard by date and vendor mix. | plan capacity |
| marketsanops.metrics.clean_site_pass_rate | Market clean-site pass rate KPI | invariant | KPI measures market days closing without unresolved sanitation defects. | monitor quality |
| marketsanops.metrics.vendor_compliance_rate | Market vendor sanitation compliance KPI | variant | KPI tracks vendors meeting waste, grease, greywater and cleanup requirements. | manage vendors |
| marketsanops.coordination.health_inspector | Market health inspector coordination | invariant | Coordination routes food safety or sanitation concerns to appropriate health authority. | align enforcement |
| marketsanops.coordination.waste_hauler | Market waste hauler coordination | variant | Coordination sets pickup times, container types, access, contamination rules and emergency calls. | keep moving |
| marketsanops.continuity.emergency_sanitation_response | Market emergency sanitation response | invariant | Response handles sewage overflow, toilet failure, major spill, contamination or pest outbreak. | protect public |
| marketsanops.close.site_closeout | Outdoor market site closeout | invariant | Closeout confirms vendor cleanup, waste removed, toilets serviced, drains protected and records filed. | finish event |
