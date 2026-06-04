# BATCH 390: Emergency Mass Feeding Kitchen Coordination

**KnowledgeUnits:** 44  
**Namespace:** `massfeedingops.*`  
**Scope:** menus, supply, production, delivery, food safety, volunteers, counts and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| massfeedingops.activation.trigger | feeding trigger | MODEL | Trigger includes sheltering, displacement, power outage, field crews or access loss. | Starts meal coordination. |
| massfeedingops.activation.lead_agency | lead agency | RECORD | Lead agency coordinates kitchen, partners, logistics, public health and sites. | Clarifies responsibility. |
| massfeedingops.activation.capacity | kitchen capacity | MEASUREMENT | Capacity estimates meals per period by staff, equipment, space and supplies. | Prevents overcommitment. |
| massfeedingops.activation.service_model | service model | RECORD | Model distinguishes fixed kitchen, mobile kitchen, catered meals or shelf-stable meals. | Defines operation. |
| massfeedingops.menu.menu_plan | menu plan | RECORD | Menu plan lists meals, portions, dates, ingredients and nutrition assumptions. | Guides production. |
| massfeedingops.menu.dietary | dietary needs | METHOD | Dietary planning considers allergies, medical, religious, cultural and infant needs. | Improves safe access. |
| massfeedingops.menu.shelf_stable | shelf-stable option | METHOD | Shelf-stable meals support delivery gaps or no-cook environments. | Adds resilience. |
| massfeedingops.menu.menu_change | menu change | METHOD | Menu changes record supply, safety or demand reasons. | Keeps staff aligned. |
| massfeedingops.supply.inventory | food inventory | MEASUREMENT | Inventory tracks ingredients, prepared meals, packaging, water and special diets. | Shows available supply. |
| massfeedingops.supply.receiving | food receiving | QUALITY_CHECK | Receiving checks source, temperature, condition, date and quantity. | Protects food safety. |
| massfeedingops.supply.reorder | reorder trigger | MODEL | Reorder uses meal counts, burn rate, delivery time and reserve. | Prevents meal gaps. |
| massfeedingops.supply.donation | donated food control | SAFETY_RULE | Donated food must meet safety, packaging and traceability rules. | Prevents illness. |
| massfeedingops.production.batch | production batch | RECORD | Batch records menu, quantity, staff, start/end, lot ingredients and destination. | Creates traceability. |
| massfeedingops.production.portion | portion control | METHOD | Portion standards align count, nutrition and inventory. | Reduces waste. |
| massfeedingops.production.hot_hold | hot holding | SAFETY_RULE | Hot foods maintain required temperature until service or delivery. | Prevents foodborne illness. |
| massfeedingops.production.cold_hold | cold holding | SAFETY_RULE | Cold foods stay under required temperature limits. | Maintains safety. |
| massfeedingops.foodsafety.haccp | food safety plan | SAFETY_RULE | Plan covers receiving, storage, prep, cooking, holding, transport and service. | Controls illness risk. |
| massfeedingops.foodsafety.temp_log | temperature log | RECORD | Logs record cooking, holding, cooling, transport and corrective actions. | Provides evidence. |
| massfeedingops.foodsafety.allergen | allergen control | SAFETY_RULE | Allergens are labeled and separated where feasible. | Protects recipients. |
| massfeedingops.foodsafety.ill_worker | ill worker rule | SAFETY_RULE | Ill food workers are excluded or reassigned by policy. | Prevents outbreaks. |
| massfeedingops.delivery.delivery_id | delivery ID | RECORD | Delivery ID links meals, route, driver, time, site and count. | Tracks outbound meals. |
| massfeedingops.delivery.route | route planning | METHOD | Routes consider shelters, field sites, road closures, time and temperature. | Gets meals there safely. |
| massfeedingops.delivery.handoff | handoff proof | RECORD | Receiver confirms quantity, condition, time and temperature if required. | Closes delivery loop. |
| massfeedingops.delivery.delay | delay response | METHOD | Delays trigger site notice, temperature check, replacement or discard decision. | Protects safety. |
| massfeedingops.service.site_count | site meal count | MEASUREMENT | Sites report requested, delivered, served, leftover and unmet meals. | Sizes production. |
| massfeedingops.service.queue | service queue | METHOD | Queue layout handles access, shade, disability, children and crowd flow. | Keeps service orderly. |
| massfeedingops.service.leftovers | leftover handling | SAFETY_RULE | Leftovers are reused, donated or discarded only under safety rules. | Prevents unsafe reuse. |
| massfeedingops.service.feedback | recipient feedback | METHOD | Feedback captures dietary gaps, timing, quality and access issues. | Improves service. |
| massfeedingops.volunteers.role | volunteer role | RECORD | Roles include prep, packing, loading, serving, cleaning and runner. | Organizes labor. |
| massfeedingops.volunteers.training | food safety training | SAFETY_RULE | Volunteers receive hygiene, allergen, temperature and conduct briefing. | Reduces mistakes. |
| massfeedingops.volunteers.supervision | supervision | METHOD | Volunteers work under kitchen lead or station captain. | Maintains quality. |
| massfeedingops.volunteers.fatigue | fatigue control | SAFETY_RULE | Long kitchen shifts require breaks, hydration and rotation. | Protects workers. |
| massfeedingops.sanitation.cleaning | cleaning schedule | RECORD | Schedule covers surfaces, equipment, floors, dishwashing and waste. | Maintains hygiene. |
| massfeedingops.sanitation.waste | waste handling | METHOD | Waste is sorted, removed and stored away from food. | Reduces pests and contamination. |
| massfeedingops.sanitation.water | water and handwash | SAFETY_RULE | Handwashing and safe water must be available for prep and service. | Enables safe operation. |
| massfeedingops.sanitation.pest | pest control | METHOD | Food and waste storage reduce pests. | Protects kitchen. |
| massfeedingops.reporting.daily_report | daily report | RECORD | Report summarizes meals produced, delivered, served, wasted and unmet. | Feeds command. |
| massfeedingops.reporting.cost | cost record | RECORD | Costs track food, labor, equipment, transport, packaging and donations. | Supports reimbursement. |
| massfeedingops.reporting.special_diet | special diet report | MEASUREMENT | Report tracks special diet demand and fulfillment. | Guides menu planning. |
| massfeedingops.records.retention | retention rule | CONSTRAINT | Records follow food safety, finance, emergency and grant schedules. | Preserves audit. |
| massfeedingops.qa.safety_audit | safety audit | QUALITY_CHECK | Audit checks temperature logs, cleaning, allergens, receiving and worker hygiene. | Prevents outbreaks. |
| massfeedingops.qa.count_reconcile | count reconciliation | QUALITY_CHECK | Meal counts reconcile production, delivery, service and leftovers. | Controls waste and funding. |
| massfeedingops.demob.kitchen_close | kitchen closeout | METHOD | Closeout cleans, inventories, disposes food, returns equipment and archives records. | Ends feeding safely. |
| massfeedingops.review.after_action | after-action review | METHOD | Review captures capacity, diet needs, routes, volunteers and food safety lessons. | Improves next response. |
