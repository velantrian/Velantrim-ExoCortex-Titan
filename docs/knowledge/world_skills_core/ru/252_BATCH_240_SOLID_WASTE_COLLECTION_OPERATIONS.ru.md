# BATCH_240 — Solid Waste Collection Operations Detail
# world_skills_core · source: world_skills_core:batch_240:solid_waste_collection_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| wasteops.route.route_plan | Solid waste route plan | invariant | Plan assigns streets, stops, sequence, truck, crew, disposal site and service day. | organize collection |
| wasteops.route.route_balancing | Waste route balancing | variant | Balancing adjusts route size by stops, tonnage, traffic, distance and disposal time. | fair workload |
| wasteops.route.gps_track | Waste truck GPS track | variant | Track records route completion, missed areas, travel time and exceptions. | verify service |
| wasteops.route.holiday_shift | Waste holiday route shift | variant | Shift changes service day, public notice, staffing and transfer station timing. | maintain service |
| wasteops.route.weather_adjustment | Waste route weather adjustment | invariant | Adjustment accounts for snow, heat, flooding, wind, road closure or unsafe access. | safe service |
| wasteops.cart.cart_inventory | Waste cart inventory | invariant | Inventory tracks cart serial, size, address, ownership, delivery, repair and removal. | asset control |
| wasteops.cart.cart_delivery | Waste cart delivery | variant | Delivery records address, cart type, placement, resident notice and photo. | start service |
| wasteops.cart.cart_repair | Waste cart repair | invariant | Repair tracks broken lid, wheel, axle, body, missing cart or replacement. | keep usable bins |
| wasteops.cart.cart_overflow | Waste cart overflow note | variant | Note records chronic overflow, education, extra cart need or enforcement path. | manage volume |
| wasteops.cart.setout_rule | Waste setout rule | invariant | Rule defines placement, timing, lid closure, weight, bagging and obstruction limits. | collect efficiently |
| wasteops.miss.missed_pickup | Missed waste pickup | invariant | Record captures address, material, service day, reason, crew note and recovery. | fix miss |
| wasteops.miss.blocked_cart | Blocked waste cart | invariant | Record notes vehicle, snow, construction, locked gate or access issue preventing pickup. | explain nonservice |
| wasteops.miss.late_setout | Late setout record | variant | Record documents cart placed after collection and resident communication. | reduce disputes |
| wasteops.miss.recovery_route | Missed pickup recovery route | variant | Route groups valid misses for same-day or next-day collection. | restore trust |
| wasteops.contamination.contamination_tag | Waste contamination tag | invariant | Tag explains prohibited material, photo, date, address and corrective instruction. | educate resident |
| wasteops.contamination.hazardous_item | Hazardous item finding | invariant | Finding records chemicals, batteries, sharps, hot ashes or unsafe waste and response. | protect crews |
| wasteops.contamination.yard_waste_mix | Yard waste contamination | variant | Record flags plastic bags, trash, soil, treated wood or oversized branches. | protect compost |
| wasteops.contamination.enforcement_case | Waste enforcement case | variant | Case tracks repeated violations, warnings, fines, hearings or service limits. | enforce rules |
| wasteops.bulky.bulky_pickup_request | Bulky pickup request | invariant | Request records item, address, fee, date, restrictions and collection instructions. | schedule large items |
| wasteops.bulky.mattress_handling | Mattress pickup handling | variant | Handling captures wrapping rule, contamination, crew safety and disposal destination. | safe pickup |
| wasteops.bulky.appliance_pickup | Appliance pickup | variant | Pickup records refrigerant status, size, location, fee and recycling route. | compliant disposal |
| wasteops.bulky.illegal_dumping | Waste illegal dumping | invariant | Report records location, items, photos, cleanup crew, enforcement and cost. | remove dumping |
| wasteops.transfer.transfer_ticket | Waste transfer ticket | invariant | Ticket records truck, route, load weight, material type, time and disposal site. | tonnage accounting |
| wasteops.transfer.scale_house | Waste scale house process | invariant | Process weighs inbound/outbound trucks, checks material and issues ticket. | accurate loads |
| wasteops.transfer.load_rejection | Waste load rejection | variant | Rejection records prohibited material, contamination, unsafe load and corrective route. | protect facility |
| wasteops.transfer.disposal_allocation | Waste disposal allocation | variant | Allocation routes loads to landfill, transfer, compost, recycling or special handling. | correct endpoint |
| wasteops.safety.pretrip_check | Waste truck pre-trip check | invariant | Check covers brakes, hydraulics, lights, tires, mirrors, cameras, compactor and leaks. | safe vehicle |
| wasteops.safety.backing_policy | Waste truck backing policy | invariant | Policy limits backing, requires spotter or camera use and documents exceptions. | prevent collisions |
| wasteops.safety.lift_arm_hazard | Automated lift arm hazard | invariant | Hazard control keeps people, cars, wires and obstructions clear during lift. | prevent injury |
| wasteops.safety.needle_stick | Waste crew sharps exposure | invariant | Exposure record captures injury, first aid, medical referral, location and prevention. | worker safety |
| wasteops.safety.heat_stress | Waste crew heat stress control | variant | Control adjusts water, rest, pacing, route timing and symptoms monitoring. | prevent illness |
| wasteops.customer.account_service | Waste customer account service | invariant | Service record links address, cart size, start/stop, billing class and exemptions. | customer support |
| wasteops.customer.special_assistance | Waste special assistance pickup | variant | Pickup serves approved residents needing walk-up or assisted cart collection. | accessible service |
| wasteops.customer.complaint_resolution | Waste complaint resolution | invariant | Resolution handles noise, spill, miss, damaged property, behavior or billing concern. | close issue |
| wasteops.operations.spill_cleanup | Waste truck spill cleanup | invariant | Cleanup removes leaked garbage, liquids, glass or debris and documents route. | clean streets |
| wasteops.operations.truck_full | Waste truck full event | variant | Event records route point, disposal trip, delay, missed stops and recovery plan. | continue route |
| wasteops.operations.deadhead_time | Waste deadhead time | variant | Time tracks travel from route to disposal or yard without collection. | route efficiency |
| wasteops.operations.crew_shortage | Waste crew shortage plan | invariant | Plan reassigns routes, overtime, contractors, delayed service and public notice. | maintain service |
| wasteops.finance.fee_adjustment | Waste service fee adjustment | variant | Adjustment records cart size, vacancy, hardship, exemption, error or service change. | billing accuracy |
| wasteops.finance.contractor_invoice | Waste contractor invoice review | variant | Review compares invoices to routes, tonnage, contract rates and exceptions. | pay correctly |
| wasteops.reporting.daily_route_report | Solid waste daily route report | invariant | Report summarizes completed routes, misses, tons, incidents, truck issues and complaints. | operational visibility |
| wasteops.reporting.tonnage_report | Waste tonnage report | invariant | Report tracks landfill, recycling, compost, bulky and special waste by period. | planning data |
| wasteops.metrics.waste_collection_kpi | Solid waste collection KPI | variant | KPI tracks misses, tons per route, safety incidents, contamination, complaints and cost. | manage service |
| wasteops.continuity.facility_shutdown | Waste facility shutdown response | invariant | Response reroutes trucks, stages loads, communicates delays and records disposal alternatives. | service continuity |
