# BATCH_186 — Industrial Laundry Operations Detail
# world_skills_core · source: world_skills_core:batch_186:industrial_laundry_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| laundryops.intake.soil_sort | Soil sorting | invariant | Soil sorting separates textiles by customer, fabric, color, soil level, infection risk and process route. | dirty side begins right |
| laundryops.intake.bag_opening | Laundry bag opening | invariant | Bag opening checks for sharps, foreign objects, counts and special handling labels. | protect workers and machines |
| laundryops.intake.weight_capture | Load weight capture | invariant | Weight capture sets wash formula, machine loading, productivity and customer billing data. | kilograms drive process |
| laundryops.intake.customer_lot | Customer lot tracking | invariant | Lot tracking links textiles to customer, pickup, batch, process and delivery. | avoid mix-up |
| laundryops.intake.rewash_flag | Rewash flag | variant | Flag marks items needing second process because of stain, odor, reject or contamination. | quality loop |
| laundryops.intake.repair_flag | Textile repair flag | variant | Flag routes damaged items to mending, replacement, discard or customer approval. | extend linen life |
| laundryops.wash.wash_formula | Wash formula | invariant | Formula defines water level, temperature, chemistry, mechanical action and time by textile type. | recipe for cleaning |
| laundryops.wash.detergent_dose | Detergent dosing | invariant | Dosing must match soil, load weight, water quality and formula. | chemistry control |
| laundryops.wash.alkalinity_control | Alkalinity control | variant | Alkalinity affects soil removal and textile life and must be balanced by formula. | clean without damage |
| laundryops.wash.disinfection_step | Laundry disinfection step | invariant | Disinfection step uses validated time, temperature or chemistry where hygiene requirement applies. | infection control |
| laundryops.wash.rinse_quality | Rinse quality | invariant | Rinse removes soils and residual chemicals that could irritate users or damage textiles. | finish the wash |
| laundryops.wash.water_hardness | Laundry water hardness | variant | Hardness affects detergent performance, scaling and textile feel. | water changes chemistry |
| laundryops.machine.tunnel_washer | Tunnel washer | variant | Tunnel washer moves loads through sequential zones for high-volume continuous washing. | industrial throughput |
| laundryops.machine.washer_extractor | Washer-extractor | invariant | Washer-extractor washes and spins batches before drying or finishing. | batch workhorse |
| laundryops.machine.load_balance | Load balance | invariant | Balanced load protects machine bearings, spin performance and safety. | avoid vibration damage |
| laundryops.machine.preventive_maintenance | Laundry preventive maintenance | invariant | PM covers belts, bearings, pumps, valves, lint, sensors, chemicals and safety devices. | uptime protection |
| laundryops.machine.lint_control | Lint control | invariant | Lint removal reduces fire risk, airflow restriction and product contamination. | small fibers, big risk |
| laundryops.machine.energy_recovery | Laundry heat recovery | variant | Heat recovery reuses wastewater or exhaust heat where system economics and hygiene allow. | reduce utility cost |
| laundryops.dry.dryer_loading | Dryer loading | invariant | Dryer load size affects drying time, wrinkles, energy, fire risk and textile wear. | do not overload |
| laundryops.dry.moisture_target | Moisture target | invariant | Target residual moisture supports ironing, folding or storage without overdrying. | finish quality |
| laundryops.dry.cooldown_cycle | Dryer cooldown cycle | invariant | Cooldown reduces heat retention and fire risk before unloading or cart storage. | hot linen risk |
| laundryops.dry.fire_risk | Laundry fire risk | invariant | Fire risk increases with lint, heat, oils, overdrying, blocked airflow and hot storage. | prevention critical |
| laundryops.dry.tumbler_alarm | Dryer alarm response | invariant | Alarm response checks heat, airflow, door, sensor, lint and load before restart. | do not ignore alarm |
| laundryops.finish.ironing_line | Flatwork ironing line | invariant | Ironing line dries, presses and folds sheets or table linen using heat, pressure and speed control. | smooth flatwork |
| laundryops.finish.feeder | Ironer feeder | variant | Feeder aligns linen into ironer to reduce wrinkles, jams and unsafe hand placement. | quality and safety |
| laundryops.finish.folding | Laundry folding | invariant | Folding standardizes size, count, presentation and packing for delivery. | usable output |
| laundryops.finish.garment_press | Garment pressing | variant | Pressing shapes uniforms or garments while controlling heat, fabric, finish and identification. | professional appearance |
| laundryops.finish.stack_count | Stack count | invariant | Count verifies finished bundles match customer order, packing slip or route requirement. | avoid shortages |
| laundryops.finish.reject_station | Laundry reject station | invariant | Reject station removes stained, torn, wet, misfolded or wrong items from clean flow. | quality gate |
| laundryops.hygiene.clean_dirty_separation | Clean-dirty separation | invariant | Separation prevents soiled textiles, carts, air or staff from contaminating clean output. | core hygiene barrier |
| laundryops.hygiene.hand_hygiene_point | Laundry hand hygiene point | invariant | Hygiene stations support transitions between soil side and clean side. | worker behavior control |
| laundryops.hygiene.cart_sanitization | Laundry cart sanitization | invariant | Sanitization prevents dirty carts from contaminating clean textiles. | transport surface matters |
| laundryops.hygiene.barrier_washer | Barrier washer | variant | Barrier washer loads from dirty side and unloads clean side through physical separation. | built-in segregation |
| laundryops.hygiene.infection_control_linen | Infection-control linen | variant | High-risk linen follows special bagging, sorting, washing and PPE procedures. | protect staff and users |
| laundryops.hygiene.clean_storage | Clean linen storage | invariant | Storage protects clean textiles from dust, moisture, pests, traffic and dirty items. | preserve clean status |
| laundryops.delivery.route_manifest | Laundry route manifest | invariant | Manifest lists customer, bags, carts, counts, products, pickups and deliveries. | route accountability |
| laundryops.delivery.cart_label | Laundry cart label | invariant | Label identifies customer, contents, clean/dirty status, route and delivery point. | prevent wrong drop |
| laundryops.delivery.linen_shortage | Linen shortage report | invariant | Report documents missing quantity, cause, customer impact and corrective action. | service recovery |
| laundryops.delivery.customer_par | Customer par level | invariant | Par level defines expected linen quantity at customer site and in laundry cycle. | inventory balance |
| laundryops.delivery.delivery_exception | Laundry delivery exception | variant | Exception records late, missing, damaged, contaminated or rejected delivery item. | close issue |
| laundryops.quality.stain_trend | Stain trend analysis | variant | Trend analysis identifies recurring stain types, customers, textiles or process failures. | improve wash |
| laundryops.quality.textile_life | Textile life tracking | invariant | Tracking monitors uses, losses, repairs and discard to manage replacement cost. | linen is capital |
| laundryops.quality.customer_complaint | Laundry customer complaint | invariant | Complaint records quality, count, delivery, odor, damage or billing issue and response. | feedback loop |
| laundryops.quality.process_audit | Laundry process audit | invariant | Audit checks sorting, formula, machine settings, hygiene separation, counts and records. | verify operation |
