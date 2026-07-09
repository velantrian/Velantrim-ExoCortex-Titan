# BATCH_198 — Catering Event Production Operations Detail
# world_skills_core · source: world_skills_core:batch_198:catering_event_production_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| caterops.sales.event_inquiry | Catering event inquiry | invariant | Inquiry records client, date, venue, guest count, service style, budget and dietary needs. | start event file |
| caterops.sales.proposal | Catering proposal | invariant | Proposal describes menu, service, staffing, rentals, timing, pricing and assumptions. | sell clearly |
| caterops.sales.contract | Catering contract | invariant | Contract defines scope, payment, guest count deadlines, cancellation, liability and venue rules. | commercial frame |
| caterops.sales.guest_count_guarantee | Guest count guarantee | invariant | Guarantee locks minimum billable guest count before purchasing and staffing. | plan volume |
| caterops.sales.change_order | Catering change order | invariant | Change order records menu, count, timing, equipment or price changes after agreement. | control scope |
| caterops.menu.menu_spec | Catering menu specification | invariant | Spec lists dishes, portions, ingredients, plating, service temperature and allergens. | production recipe |
| caterops.menu.dietary_matrix | Dietary matrix | invariant | Matrix maps vegetarian, vegan, allergen, religious, texture or medical diet requests. | serve safely |
| caterops.menu.tasting_note | Tasting note | variant | Note records client feedback, selected dishes and adjustments. | align expectations |
| caterops.menu.portion_plan | Catering portion plan | invariant | Plan converts guest count and service style into production quantities. | avoid shortage |
| caterops.menu.beverage_plan | Catering beverage plan | variant | Plan estimates drinks, ice, glassware, staffing and service restrictions. | beverage readiness |
| caterops.procure.purchase_list | Catering purchase list | invariant | List aggregates ingredients, disposables, rentals, beverages and service supplies. | buy accurately |
| caterops.procure.vendor_order | Catering vendor order | invariant | Order confirms product, quantity, delivery time, location, price and backup contact. | supply chain |
| caterops.procure.rental_order | Event rental order | variant | Order covers tables, chairs, linens, china, glassware, tenting, power or kitchen gear. | temporary infrastructure |
| caterops.procure.substitution_rule | Ingredient substitution rule | variant | Rule controls approved substitutions for availability, allergy, quality or budget issue. | avoid surprise changes |
| caterops.procure.receiving_check | Catering receiving check | invariant | Check verifies delivered quantity, quality, temperature and match to order. | protect event prep |
| caterops.production.production_schedule | Catering production schedule | invariant | Schedule sequences prep, cooking, chilling, packing, loading and departure. | time the kitchen |
| caterops.production.prep_sheet | Catering prep sheet | invariant | Sheet lists tasks, quantities, owner, deadline and recipe reference. | coordinate labor |
| caterops.production.batch_label | Catering batch label | invariant | Label identifies dish, event, date, allergen, storage condition and count. | avoid mix-up |
| caterops.production.quality_taste_check | Catering taste and quality check | invariant | Check verifies seasoning, texture, appearance, doneness and portion before packing. | event food standard |
| caterops.production.leftover_rule | Catering leftover rule | variant | Rule defines whether leftovers may be served, donated, returned, discarded or packed. | safety and expectation |
| caterops.foodsafe.time_temp_log | Catering time-temperature log | invariant | Log tracks chilled, hot-held, reheated or transported food times and temperatures. | food safety evidence |
| caterops.foodsafe.cooling_control | Catering cooling control | invariant | Control chills cooked food within safe time and container conditions before transport or storage. | prevent growth |
| caterops.foodsafe.allergen_separation | Catering allergen separation | invariant | Separation controls prep, labeling, packing and serving of allergen-sensitive meals. | high-risk guests |
| caterops.foodsafe.handwash_station | Event handwash station | invariant | Station provides accessible hand hygiene for food handlers at venue. | temporary site hygiene |
| caterops.foodsafe.food_disposition | Catering food disposition | invariant | Disposition records served, held, discarded, donated or returned product. | close safety loop |
| caterops.pack.packout_list | Catering packout list | invariant | List covers food, equipment, utensils, labels, rentals, paperwork and emergency supplies. | load completely |
| caterops.pack.hotbox_coldbox | Hotbox and coldbox plan | invariant | Plan assigns foods to insulated transport by temperature, event timing and access order. | maintain condition |
| caterops.pack.load_sequence | Catering load sequence | variant | Sequence places first-needed and fragile items for efficient unloading and protection. | avoid chaos on site |
| caterops.pack.count_check | Catering count check | invariant | Check compares packed items against event order, menu and guest count. | no missing pans |
| caterops.pack.emergency_kit | Catering emergency kit | variant | Kit includes labels, gloves, tape, utensils, small tools, first aid and backup service items. | field resilience |
| caterops.transport.delivery_route | Catering delivery route | invariant | Route plans vehicle, driver, departure, venue dock, parking, access and arrival buffer. | arrive ready |
| caterops.transport.vehicle_temperature | Catering vehicle temperature | variant | Temperature control applies where vehicle or compartment holds chilled or hot food. | transit safety |
| caterops.transport.site_handoff | Venue site handoff | invariant | Handoff confirms arrival, counts, condition, contact, setup area and timing. | transfer to event mode |
| caterops.transport.transport_delay | Catering transport delay | invariant | Delay response informs coordinator, adjusts setup, protects food condition and records impact. | recover event |
| caterops.transport.return_load | Catering return load | variant | Return load collects rentals, equipment, waste, leftover decisions and damage notes. | close logistics |
| caterops.site.setup_plan | Catering site setup plan | invariant | Plan maps buffet, stations, kitchen, bar, guest flow, power, water and waste. | build temporary service |
| caterops.site.service_briefing | Event service briefing | invariant | Briefing covers timeline, menu, allergies, VIPs, roles, safety and communication. | align crew |
| caterops.site.buffet_replenishment | Buffet replenishment | variant | Replenishment keeps presentation, temperature, quantity and allergen separation under control. | service quality |
| caterops.site.plated_service_flow | Plated service flow | variant | Flow coordinates plate-up, runners, table sequence, dietary plates and clearing. | synchronized meal |
| caterops.site.guest_issue | Catering guest issue | invariant | Issue records complaint, allergy concern, missing meal, spill, delay or service problem. | respond visibly |
| caterops.close.event_closeout | Catering event closeout | invariant | Closeout confirms service end, cleanup, rentals, waste, leftovers, client signoff and notes. | finish the event |
| caterops.close.damage_loss | Catering damage or loss | invariant | Record documents broken rentals, lost equipment, venue damage or client claim. | accountability |
| caterops.close.post_event_debrief | Post-event debrief | variant | Debrief reviews food quantity, service timing, client feedback, incidents and margin. | improve next event |
| caterops.metrics.catering_kpi | Catering operations KPI | variant | KPI tracks food cost, labor, packout defects, on-time arrival, complaints and waste. | manage event production |
