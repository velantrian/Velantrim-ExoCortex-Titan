# BATCH_279 — Street Sweeping Operations Detail
# world_skills_core · source: world_skills_core:batch_279:street_sweeping_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| sweepops.inventory.sweeping_route | Street sweeping route record | invariant | Record defines route limits, curb miles, direction, frequency, restrictions and assigned equipment. | plan service |
| sweepops.inventory.curb_segment | Sweeping curb segment | invariant | Segment stores block face, parking rules, drainage priority, tree canopy and debris tendency. | organize work |
| sweepops.inventory.no_parking_zone | Sweeping no-parking zone | variant | Zone links street sweeping schedule to curb signs, enforcement windows and resident notices. | clear access |
| sweepops.inventory.hotspot_location | Sweeping hotspot location | variant | Hotspot records repeated leaves, sediment, glass, litter, market waste or drainage debris. | target cleaning |
| sweepops.schedule.recurring_schedule | Recurring sweeping schedule | invariant | Schedule sets day, time, frequency, route order, seasonal changes and holiday exceptions. | predictable service |
| sweepops.schedule.seasonal_leaf_program | Seasonal leaf sweeping program | variant | Program adjusts routes, staffing and disposal for heavy autumn leaf accumulation. | handle season |
| sweepops.schedule.event_cleanup | Event street cleanup schedule | variant | Schedule assigns pre-event and post-event sweeping around parades, markets, stadiums or festivals. | restore streets |
| sweepops.schedule.weather_cancellation | Sweeping weather cancellation | invariant | Cancellation records rain, snow, freezing, flooding or poor visibility that prevents effective sweeping. | avoid wasted runs |
| sweepops.operations.mechanical_broom_sweeping | Mechanical broom sweeping | invariant | Sweeper uses rotating broom and conveyor to remove coarse debris from pavement and gutter. | clean curb |
| sweepops.operations.regenerative_air_sweeping | Regenerative air sweeping | variant | Sweeper uses controlled airflow and vacuum recovery to collect fine particles and debris. | reduce dust |
| sweepops.operations.gutter_pass | Sweeper gutter pass | invariant | Pass follows curb line to remove litter, grit, leaves and sediment near drains. | protect drainage |
| sweepops.operations.centerline_sweeping | Centerline sweeping | variant | Sweeping targets medians, turn lanes, islands or shared center areas where debris accumulates. | clean lanes |
| sweepops.debris.leaf_debris | Leaf debris | invariant | Leaves can block drains, hide hazards, create slippery surfaces and increase organic load. | seasonal risk |
| sweepops.debris.sediment_load | Street sediment load | invariant | Sediment includes soil, sand, construction dirt and winter abrasive residue in gutters. | reduce runoff |
| sweepops.debris.glass_debris | Street glass debris | variant | Glass debris creates tire, bicycle, pedestrian and cleanup hazards requiring priority removal. | safety |
| sweepops.debris.illegal_dumping | Illegal dumping on street | variant | Dumped items exceed normal sweeping and require bulky removal, enforcement or sanitation crew. | route exception |
| sweepops.equipment.sweeper_pretrip | Street sweeper pre-trip check | invariant | Check covers brooms, water, hopper, suction, lights, tires, cameras, controls and safety gear. | ready equipment |
| sweepops.equipment.broom_wear | Sweeper broom wear | invariant | Wear reduces contact pressure, debris pickup and gutter cleaning effectiveness. | replace brooms |
| sweepops.equipment.water_spray_system | Sweeper water spray system | invariant | System suppresses dust through tanks, pumps, nozzles, filters and flow controls. | dust control |
| sweepops.equipment.hopper_dump | Sweeper hopper dump | variant | Dumping empties collected debris at approved site with weight, contamination and safety checks. | continue route |
| sweepops.parking.parked_car_blockage | Parked car sweeping blockage | invariant | Blockage prevents curb cleaning and creates missed sections under scheduled restrictions. | measure access |
| sweepops.parking.enforcement_coordination | Sweeping parking enforcement coordination | invariant | Coordination aligns ticketing or towing with signs, grace periods and route timing. | clear route |
| sweepops.parking.blockage_rate | Sweeping blockage rate | variant | Rate measures curb length unavailable because vehicles or obstacles blocked sweeper access. | improve compliance |
| sweepops.complaints.missed_sweep | Missed street sweeping complaint | invariant | Complaint records location, date, reason, parked cars, weather, equipment failure or route error. | respond fairly |
| sweepops.complaints.dust_complaint | Street sweeping dust complaint | variant | Complaint indicates dry sweeping, failed water spray, fine sediment or unsuitable conditions. | adjust method |
| sweepops.complaints.noise_complaint | Street sweeping noise complaint | variant | Complaint concerns early hours, alarms, brushes, engine noise or repeated passes. | manage nuisance |
| sweepops.disposal.debris_disposal_site | Sweeping debris disposal site | invariant | Site receives collected debris with rules for dumping, contamination, drainage and records. | lawful disposal |
| sweepops.disposal.contaminated_sweepings | Contaminated street sweepings | variant | Contamination includes oil, chemicals, sharps, sewage, dead animals or hazardous waste. | special handling |
| sweepops.disposal.debris_weight_ticket | Sweeping debris weight ticket | invariant | Ticket records load weight, route, date, truck, disposal site and material category. | track output |
| sweepops.waterquality.storm_drain_protection | Storm drain protection by sweeping | invariant | Sweeping removes sediment, nutrients, metals and trash before they enter drainage system. | improve water |
| sweepops.waterquality.priority_watershed_route | Priority watershed sweeping route | variant | Route gets higher frequency near impaired waters, steep streets, industrial areas or drain inlets. | target pollution |
| sweepops.waterquality.mscp_reporting | Sweeping stormwater permit reporting | variant | Reporting connects sweeping activity to stormwater compliance, pollutant reduction and inspection evidence. | support compliance |
| sweepops.safety.operator_blind_spot | Sweeper operator blind spot | invariant | Blind spots around large sweepers require mirrors, cameras, low speed and awareness. | prevent collisions |
| sweepops.safety.reverse_maneuver | Sweeper reverse maneuver | variant | Backing requires controls because sweepers operate near curbs, pedestrians, cyclists and parked cars. | avoid incidents |
| sweepops.safety.sharps_handling | Sharps handling in sweeping | invariant | Handling covers needles, broken glass and dangerous debris found during cleaning. | protect staff |
| sweepops.reporting.daily_route_log | Daily sweeping route log | invariant | Log records route completion, miles, loads, problems, missed blocks and operator notes. | document service |
| sweepops.reporting.monthly_sweeping_report | Monthly sweeping report | variant | Report summarizes curb miles, debris tons, complaints, equipment downtime and missed routes. | manage program |
| sweepops.metrics.curb_miles_swept | Curb miles swept KPI | invariant | KPI measures completed curb distance by route, district, month and service level. | track output |
| sweepops.metrics.debris_tons_collected | Debris tons collected KPI | invariant | KPI measures material removed from streets and supports seasonal or water-quality analysis. | quantify cleanup |
| sweepops.metrics.route_completion_rate | Sweeping route completion rate KPI | variant | KPI compares scheduled routes to completed routes, excluding documented cancellations. | monitor reliability |
| sweepops.coordination.construction_sediment | Construction sediment coordination | variant | Coordination sends recurring dirt sources to inspectors, permit holders or enforcement. | fix source |
| sweepops.coordination.leaf_collection_program | Leaf collection coordination | variant | Coordination aligns sweeping with bagged leaf pickup, vacuum trucks and public messaging. | reduce rework |
| sweepops.continuity.emergency_debris_sweep | Emergency debris sweep | variant | Sweep clears crash debris, storm debris, spill residue or safety hazards outside schedule. | rapid response |
| sweepops.close.route_closeout | Sweeping route closeout | invariant | Closeout confirms route status, missed blocks, disposal tickets, complaints and equipment issues. | finish run |
