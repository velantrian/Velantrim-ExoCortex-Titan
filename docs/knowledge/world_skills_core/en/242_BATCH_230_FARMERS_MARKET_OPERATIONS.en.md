# BATCH_230 — Farmers Market Operations Detail
# world_skills_core · source: world_skills_core:batch_230:farmers_market_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| farmersmarket.vendor.vendor_application | Farmers market vendor application | invariant | Application records business, products, permits, insurance, farm or producer status and contact. | onboard vendor |
| farmersmarket.vendor.product_category | Market product category | invariant | Category separates produce, meat, dairy, bakery, prepared food, crafts, flowers or services. | plan mix |
| farmersmarket.vendor.permit_check | Vendor permit check | invariant | Check verifies health, food, business, tax, fire or temporary event permits where needed. | compliance |
| farmersmarket.vendor.insurance_record | Vendor insurance record | variant | Record tracks liability coverage, certificate dates and market requirements. | risk transfer |
| farmersmarket.vendor.vendor_rules_ack | Vendor rules acknowledgment | invariant | Acknowledgment covers arrival, stall, waste, pricing, safety, conduct and departure rules. | shared norms |
| farmersmarket.layout.stall_assignment | Market stall assignment | invariant | Assignment maps vendor to stall, size, power, vehicle access and product category. | organize site |
| farmersmarket.layout.site_map | Farmers market site map | invariant | Map shows stalls, entrances, exits, toilets, waste, first aid, power and emergency access. | spatial control |
| farmersmarket.layout.arrival_window | Vendor arrival window | invariant | Window controls setup timing, traffic, unloading and pedestrian safety. | avoid chaos |
| farmersmarket.layout.vehicle_control | Market vehicle control | invariant | Control limits vehicles during public hours and manages loading zones. | crowd safety |
| farmersmarket.layout.weather_layout | Weather layout adjustment | variant | Adjustment changes tents, weights, aisles, drainage or closures due to weather. | adapt site |
| farmersmarket.food.food_safety_check | Market food safety check | invariant | Check observes temperature, covers, handwashing, sampling, labels and permit conditions. | protect customers |
| farmersmarket.food.temperature_log | Vendor temperature log | variant | Log tracks cold or hot holding for regulated foods. | evidence |
| farmersmarket.food.sampling_rule | Food sampling rule | invariant | Rule controls sample size, utensils, hand hygiene, covers and allergy awareness. | safe tasting |
| farmersmarket.food.allergen_label | Market allergen label | variant | Label communicates allergens in baked, prepared or packaged goods. | customer safety |
| farmersmarket.food.recall_notice | Market recall notice | invariant | Notice removes affected product, informs vendor and records customer communication where needed. | fast risk response |
| farmersmarket.payments.token_program | Market token program | variant | Program converts card, SNAP or voucher value into market tokens or credits. | payment access |
| farmersmarket.payments.vendor_reimbursement | Vendor reimbursement | invariant | Reimbursement reconciles tokens, vouchers, fees, sales reports and payout. | pay vendors |
| farmersmarket.payments.stall_fee | Market stall fee | invariant | Fee charges vendor by day, season, size, category or services. | market revenue |
| farmersmarket.payments.cash_control | Farmers market cash control | invariant | Control manages token booth cash, receipts, deposits, refunds and variance. | money safety |
| farmersmarket.payments.sales_reporting | Vendor sales reporting | variant | Reporting collects sales totals or categories when market requires metrics. | measure activity |
| farmersmarket.operations.market_open | Market opening round | invariant | Round checks stalls, signage, toilets, waste, first aid, weather, staff and access. | open safely |
| farmersmarket.operations.market_close | Market closeout | invariant | Closeout clears vendors, trash, signs, payments, lost items, incidents and site condition. | leave site clean |
| farmersmarket.operations.market_manager | Market manager role | invariant | Manager coordinates vendors, customers, safety, rules, payments, incidents and host site. | on-site authority |
| farmersmarket.operations.volunteer_assignment | Market volunteer assignment | variant | Assignment covers token booth, wayfinding, surveys, setup, cleanup or crowd help. | extra hands |
| farmersmarket.operations.supply_kit | Farmers market supply kit | invariant | Kit includes signs, tape, forms, first aid, weights, pens, bags, radios and cleanup tools. | ready market |
| farmersmarket.customer.info_booth | Market information booth | invariant | Booth answers vendor location, payment tokens, rules, lost items, complaints and emergencies. | customer anchor |
| farmersmarket.customer.accessibility_path | Market accessibility path | invariant | Path keeps aisles, ramps, curb cuts and accessible parking usable. | inclusive flow |
| farmersmarket.customer.crowd_flow | Farmers market crowd flow | invariant | Flow manages queues, aisles, entrances, exits, strollers, bikes and dogs. | comfortable movement |
| farmersmarket.customer.pet_policy | Market pet policy | variant | Policy defines where pets may go, leash rules, food areas and service animals. | reduce conflict |
| farmersmarket.customer.complaint_log | Farmers market complaint log | invariant | Log records vendor, product, safety, pricing, access, noise or behavior complaint. | service recovery |
| farmersmarket.safety.tent_weight | Tent weight requirement | invariant | Requirement prevents tents from moving in wind and injuring people. | wind safety |
| farmersmarket.safety.trip_hazard | Market trip hazard | invariant | Hazard includes cords, tent legs, uneven pavement, mats, boxes or produce spills. | prevent falls |
| farmersmarket.safety.first_aid | Farmers market first aid | invariant | First aid process records injury, response, EMS call and follow-up. | incident readiness |
| farmersmarket.safety.fire_safety | Market fire safety | variant | Safety controls cooking fuel, generators, extension cords, extinguishers and clearances. | prevent fire |
| farmersmarket.safety.emergency_access | Market emergency access | invariant | Access keeps lanes open for ambulance, fire, police or evacuation. | response path |
| farmersmarket.waste.waste_station | Market waste station | invariant | Station separates trash, recycling, compost and vendor waste if supported. | clean event |
| farmersmarket.waste.grease_disposal | Market grease disposal | variant | Disposal controls cooking oil or grease from prepared food vendors. | protect drains |
| farmersmarket.waste.produce_recovery | Unsold produce recovery | variant | Recovery coordinates donation, compost, vendor return or disposal. | reduce waste |
| farmersmarket.waste.site_cleanup | Farmers market site cleanup | invariant | Cleanup removes trash, signs, spills, marks and vendor debris after market. | host relationship |
| farmersmarket.waste.restroom_service | Market restroom service | variant | Service checks portable toilets or facility bathrooms for supplies, cleanliness and issues. | basic comfort |
| farmersmarket.weather.wind_action | Market wind action | invariant | Action adds weights, lowers tents, pauses setup or closes when wind exceeds rule. | prevent tent incidents |
| farmersmarket.weather.heat_plan | Market heat plan | variant | Plan adds shade, water, staff breaks, vendor advice and customer messaging. | heat safety |
| farmersmarket.metrics.market_kpi | Farmers market KPI | variant | KPI tracks vendors, attendance, sales, incidents, complaints, tokens and waste. | manage market |
| farmersmarket.continuity.site_closure | Farmers market site closure | invariant | Closure process notifies vendors, customers, host, staff and payment partners. | controlled cancellation |
