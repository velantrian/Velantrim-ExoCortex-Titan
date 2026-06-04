# BATCH 437: Disaster Food Truck Mobile Meal Route Operations

**KnowledgeUnits:** 44  
**Namespace:** `mobilemealrouteops.*`  
**Scope:** route planning, menus, permits, food safety, counts, accessibility and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| mobilemealrouteops.intake.service_request | service request | RECORD | Request records community site, estimated need, access constraints, meal type and contact person. | Defines demand. |
| mobilemealrouteops.intake.population_profile | population profile | MODEL | Profile notes seniors, children, outdoor workers, shelters, dietary needs and language needs. | Shapes service. |
| mobilemealrouteops.intake.site_readiness | site readiness | CONTROL | Readiness checks parking, queue space, lighting, security, waste, handwashing and accessible approach. | Prevents bad deployments. |
| mobilemealrouteops.route.stop_list | stop list | RECORD | Stop list captures locations, time windows, meal counts, contact, access notes and backup stop. | Guides route. |
| mobilemealrouteops.route.priority_model | priority model | MODEL | Priority weighs unmet need, distance from fixed sites, mobility barriers, heat risk and service gaps. | Allocates fairly. |
| mobilemealrouteops.route.detour_check | detour check | PROCESS | Detour check reviews closures, debris, flooding, curfews, fuel availability and vehicle limits. | Keeps routes feasible. |
| mobilemealrouteops.route.turnaround_time | turnaround time | METRIC | Time measures arrival setup, serving, cleanup and departure per stop. | Improves scheduling. |
| mobilemealrouteops.menu.meal_pattern | meal pattern | MODEL | Pattern defines hot meals, shelf-stable packs, snacks, hydration and culturally appropriate options. | Fits conditions. |
| mobilemealrouteops.menu.dietary_flag | dietary flag | RECORD | Flag marks vegetarian, allergy-aware, diabetic-friendly, soft food, infant or religious dietary needs. | Supports inclusion. |
| mobilemealrouteops.menu.substitution_rule | substitution rule | CONTROL | Rule allows safe substitutions when planned menu items are unavailable. | Prevents improvisation risk. |
| mobilemealrouteops.menu.hydration_plan | hydration plan | PROCESS | Plan pairs meals with water, electrolyte guidance, ice constraints and heat safety messages. | Addresses heat stress. |
| mobilemealrouteops.permits.mobile_food_permit | mobile food permit | RECORD | Permit record tracks food truck license, temporary event approval, health conditions and expiration. | Supports compliance. |
| mobilemealrouteops.permits.site_permission | site permission | CONTROL | Permission confirms property owner, public agency or incident command approval for each stop. | Avoids conflicts. |
| mobilemealrouteops.permits.fire_clearance | fire clearance | CONTROL | Clearance checks propane, generator placement, extinguishers, spacing and emergency vehicle access. | Reduces fire risk. |
| mobilemealrouteops.foodsafety.temperature_log | temperature log | RECORD | Log records hot holding, cold holding, departure, arrival and corrective actions. | Protects food safety. |
| mobilemealrouteops.foodsafety.handwashing_station | handwashing station | CONTROL | Station provides water, soap, towels, waste capture or approved alternate controls. | Supports hygiene. |
| mobilemealrouteops.foodsafety.cross_contact | cross-contact control | CONTROL | Control separates allergens, raw items, ready-to-eat items, utensils and serving surfaces. | Reduces illness risk. |
| mobilemealrouteops.foodsafety.leftover_rule | leftover rule | CONTROL | Rule defines discard, donation prohibition, safe return or approved reuse boundaries. | Prevents unsafe leftovers. |
| mobilemealrouteops.vehicle.pretrip_check | pretrip check | PROCESS | Check covers fuel, refrigeration, generator, tires, water, propane, utensils, supplies and route packet. | Prevents breakdowns. |
| mobilemealrouteops.vehicle.generator_status | generator status | RECORD | Status captures fuel level, runtime, noise limits, ventilation and backup power plan. | Keeps equipment reliable. |
| mobilemealrouteops.vehicle.water_tank | water tank | RECORD | Tank record notes potable fill, wastewater capacity, refill site and dump plan. | Maintains sanitation. |
| mobilemealrouteops.queue.site_layout | site layout | MODEL | Layout separates serving line, accessible lane, shade, vehicle movement, waste and staff-only areas. | Reduces crowd risk. |
| mobilemealrouteops.queue.accessible_service | accessible service | PROCESS | Accessible service offers seated wait, caregiver pickup, reachable counter or walk-up alternative. | Includes vulnerable users. |
| mobilemealrouteops.queue.language_signage | language signage | CONTROL | Signage gives meal type, hours, eligibility, allergy notice and line instructions in needed languages. | Reduces confusion. |
| mobilemealrouteops.queue.crowd_trigger | crowd trigger | CONTROL | Trigger calls support when line length, conflict, heat exposure or traffic blockage exceeds threshold. | Keeps site safe. |
| mobilemealrouteops.counts.meal_count | meal count | RECORD | Count tracks loaded meals, served meals, remaining meals, spoiled meals and transfers. | Supports reconciliation. |
| mobilemealrouteops.counts.household_estimate | household estimate | METRIC | Estimate records individuals served by broad group without unnecessary personal data. | Measures reach. |
| mobilemealrouteops.counts.turnaway_log | turnaway log | RECORD | Log captures unmet demand, reason, referral given and next supply request. | Shows gaps. |
| mobilemealrouteops.supplies.service_kit | service kit | RECORD | Kit includes gloves, sanitizer, bags, utensils, napkins, trash bags, signs and incident forms. | Enables field service. |
| mobilemealrouteops.supplies.restock_trigger | restock trigger | CONTROL | Trigger defines when meals, water, fuel, PPE or disposables require replenishment. | Maintains continuity. |
| mobilemealrouteops.supplies.waste_plan | waste plan | PROCESS | Plan handles trash, grease, gray water, cardboard, spoiled food and site cleanup. | Leaves site safe. |
| mobilemealrouteops.staffing.role_roster | role roster | RECORD | Roster assigns driver, cook, server, line monitor, safety lead, count recorder and translator. | Clarifies duties. |
| mobilemealrouteops.staffing.food_handler_boundary | food handler boundary | CONTROL | Boundary limits food contact to trained or authorized staff under proper hygiene controls. | Protects safety. |
| mobilemealrouteops.staffing.break_plan | break plan | PROCESS | Plan schedules hydration, cooling, rest and replacement during long routes. | Reduces fatigue. |
| mobilemealrouteops.communication.arrival_notice | arrival notice | PROCESS | Notice informs site contacts and community channels about time, menu, line rules and delays. | Improves turnout. |
| mobilemealrouteops.communication.delay_update | delay update | PROCESS | Update reports road, supply, safety or equipment delay and revised service window. | Manages expectations. |
| mobilemealrouteops.communication.referral_message | referral message | PROCESS | Message directs unmet users to fixed feeding sites, delivery programs or next route stop. | Reduces abandonment. |
| mobilemealrouteops.security.cashless_rule | cashless rule | CONTROL | Rule bars payment collection when service is relief-funded or donation-supported. | Prevents confusion. |
| mobilemealrouteops.security.conflict_escalation | conflict escalation | PROCESS | Escalation routes arguments, threats, traffic conflict or crowd stress to safety lead. | Protects staff and public. |
| mobilemealrouteops.reporting.daily_summary | daily summary | RECORD | Summary reports stops, meals served, unmet demand, incidents, temperature exceptions and supply needs. | Briefs command. |
| mobilemealrouteops.reporting.partner_credit | partner credit | RECORD | Credit records provider, donor, agency and volunteer contributions without overstating counts. | Supports transparency. |
| mobilemealrouteops.metrics.route_efficiency | route efficiency | METRIC | Efficiency compares meals served, route time, fuel, stops completed and turnaways. | Improves planning. |
| mobilemealrouteops.closeout.site_close | site close | PROCESS | Close verifies trash removal, wastewater handling, equipment stowage, count reconciliation and departure notice. | Ends stop cleanly. |
| mobilemealrouteops.closeout.after_action | after-action note | RECORD | Note captures menu fit, route issues, safety, access, counts and partner improvements. | Improves next route. |
