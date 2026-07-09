# BATCH_209 — Car Wash Operations Detail
# world_skills_core · source: world_skills_core:batch_209:car_wash_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| carwash.queue.vehicle_queue | Car wash vehicle queue | invariant | Queue manages arrival order, lane choice, payment status and vehicle readiness. | keep line moving |
| carwash.queue.package_selection | Wash package selection | invariant | Selection maps customer choice to wash steps, chemicals, extras and price. | sell correct service |
| carwash.queue.vehicle_precheck | Vehicle precheck | invariant | Precheck notes damage, loose items, racks, antennas, mirrors and special risks before wash. | avoid disputes |
| carwash.queue.membership_scan | Car wash membership scan | variant | Scan validates subscription, plate, barcode, account status and included package. | automate repeat customers |
| carwash.queue.wait_time_notice | Car wash wait notice | variant | Notice communicates delay, lane closure or service time to customers. | set expectations |
| carwash.tunnel.conveyor_entry | Conveyor entry | variant | Entry aligns vehicle, neutral gear, brake release, spacing and driver instruction. | safe tunnel start |
| carwash.tunnel.tunnel_controller | Tunnel controller | invariant | Controller sequences sensors, conveyor, arches, brushes, blowers and safety stops. | wash choreography |
| carwash.tunnel.vehicle_spacing | Vehicle spacing | invariant | Spacing prevents collision and gives equipment time to reset between vehicles. | protect cars |
| carwash.tunnel.emergency_stop | Tunnel emergency stop | invariant | Stop halts conveyor or equipment when unsafe condition appears. | immediate safety |
| carwash.tunnel.exit_signal | Car wash exit signal | invariant | Signal tells driver when to shift, steer and leave safely. | avoid exit mishap |
| carwash.chemical.presoak | Presoak application | invariant | Presoak loosens soil before friction or rinse steps. | start cleaning |
| carwash.chemical.detergent_dilution | Detergent dilution | invariant | Dilution ratio controls cleaning, cost, equipment compatibility and finish safety. | chemistry balance |
| carwash.chemical.wax_application | Wax application | variant | Wax or protectant is applied by package and surface compatibility. | value add |
| carwash.chemical.spot_free_rinse | Spot-free rinse | variant | Rinse uses treated water to reduce mineral spotting after wash. | better finish |
| carwash.chemical.chemical_sds | Car wash chemical SDS | invariant | SDS provides hazard, PPE, storage, spill and first-aid information for products. | staff safety |
| carwash.equipment.brush_inspection | Brush inspection | invariant | Inspection checks wear, debris, alignment, rotation and vehicle-contact risk. | prevent scratches |
| carwash.equipment.nozzle_check | Spray nozzle check | invariant | Check confirms nozzles are unclogged, aimed and producing correct pattern. | even coverage |
| carwash.equipment.blower_alignment | Blower alignment | variant | Alignment directs air to dry vehicle without striking or stressing parts. | dry safely |
| carwash.equipment.water_reclaim | Water reclaim system | variant | System filters and reuses wash water where quality and regulation allow. | reduce water use |
| carwash.equipment.preventive_maintenance | Car wash preventive maintenance | invariant | PM covers conveyor, pumps, sensors, brushes, valves, reclaim, blowers and controls. | uptime |
| carwash.detail.interior_vacuum | Interior vacuum service | variant | Service removes loose debris from floors, seats, mats and trunk by package. | detail add-on |
| carwash.detail.window_cleaning | Car wash window cleaning | variant | Cleaning handles interior or exterior glass streaks, residue and edges. | finish visibility |
| carwash.detail.tire_dressing | Tire dressing | variant | Dressing applies finish to tires while avoiding tread, brakes or slippery overspray. | appearance extra |
| carwash.detail.mat_cleaning | Floor mat cleaning | variant | Cleaning washes, dries and returns mats without soaking interior. | customer-visible detail |
| carwash.detail.quality_walkaround | Detail quality walkaround | invariant | Walkaround checks missed spots, damage, wet areas, loose items and customer requests. | final gate |
| carwash.safety.driver_instruction | Driver instruction | invariant | Instruction tells customer gear, brakes, steering, windows, wipers and exit behavior. | prevent incidents |
| carwash.safety.slip_control | Car wash slip control | invariant | Control manages wet floors, hoses, mats, signage and drainage. | worker and customer safety |
| carwash.safety.electrical_water_risk | Electrical and water risk | invariant | Risk control protects panels, cords, pumps and staff around wet electrical systems. | dangerous combination |
| carwash.safety.confined_trench | Conveyor pit or trench safety | variant | Safety controls access, lockout, ventilation and fall risk when servicing pits. | maintenance hazard |
| carwash.safety.vehicle_damage_claim | Vehicle damage claim | invariant | Claim records customer report, photos, video review, precheck and resolution path. | dispute evidence |
| carwash.customer.point_of_sale | Car wash point of sale | invariant | POS captures package, discounts, payment, membership, receipt and upsell. | revenue point |
| carwash.customer.membership_admin | Membership administration | variant | Administration handles signup, billing, plate changes, cancellation and failed payments. | subscription control |
| carwash.customer.complaint_rewash | Rewash request | invariant | Request evaluates missed cleaning, package promise, timing and approval for rewash. | service recovery |
| carwash.customer.lost_item | Lost item report | variant | Report documents item, vehicle, time, search, video if allowed and customer contact. | handle belongings |
| carwash.customer.weather_policy | Car wash weather policy | variant | Policy controls closures, rain guarantees, freezing conditions and rescheduling. | weather affects service |
| carwash.environment.drain_screen | Car wash drain screen | invariant | Screen captures debris before wastewater system or reclaim process. | protect plumbing |
| carwash.environment.wastewater_compliance | Car wash wastewater compliance | invariant | Compliance follows discharge, reclaim, separator and chemical handling requirements. | avoid violations |
| carwash.environment.chemical_inventory | Car wash chemical inventory | invariant | Inventory tracks containers, usage, storage, reorder, leaks and expired products. | control consumables |
| carwash.environment.freeze_protection | Freeze protection | variant | Protection drains, heats or shuts down lines and equipment during freezing weather. | prevent damage |
| carwash.environment.noise_control | Car wash noise control | variant | Control manages blower, vacuum, traffic and operating-hour impacts. | neighbor relation |
| carwash.admin.shift_open | Car wash shift opening | invariant | Opening verifies equipment, chemicals, cash, lanes, safety checks and staffing. | day starts ready |
| carwash.admin.shift_close | Car wash shift close | invariant | Close reconciles sales, cleans site, secures chemicals, logs faults and prepares next day. | reset site |
| carwash.metrics.carwash_kpi | Car wash KPI | variant | KPI tracks cars per hour, chemical cost, downtime, claims, memberships and rewash rate. | manage wash |
| carwash.continuity.tunnel_downtime | Car wash tunnel downtime | invariant | Downtime procedure stops sales, redirects customers, logs fault and coordinates repair. | recover service |
