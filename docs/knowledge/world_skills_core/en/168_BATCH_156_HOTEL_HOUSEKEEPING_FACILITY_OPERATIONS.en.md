# BATCH_156 — Hotel Housekeeping & Facility Operations Detail
# world_skills_core · source: world_skills_core:batch_156:hotel_housekeeping_facility_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| hotelops.rooms.room_status | Room status | invariant | Room status tracks whether a room is occupied, vacant, dirty, clean, inspected, out-of-order or out-of-service. | номер как operational state |
| hotelops.rooms.room_assignment | Housekeeping room assignment | invariant | Room assignment distributes rooms by attendant workload, room type, floor, priority and checkout pattern. | смена должна быть выполнима |
| hotelops.rooms.checkout_room | Checkout room cleaning | invariant | Checkout cleaning resets room after guest departure with linen change, bathroom sanitation, surfaces, amenities and inspection. | номер для нового гостя |
| hotelops.rooms.stayover_service | Stayover service | variant | Stayover service refreshes an occupied room according to guest preference, policy, privacy and sustainability rules. | сервис без нарушения приватности |
| hotelops.rooms.dnd_rule | Do-not-disturb rule | invariant | DND rule limits room entry and requires escalation when safety, welfare or policy thresholds are reached. | уважение плюс безопасность |
| hotelops.rooms.priority_room | Priority room | variant | Priority room is cleaned or inspected first because guest arrival, VIP, complaint or room move requires it. | не все комнаты равны |
| hotelops.rooms.room_inspection | Room inspection | invariant | Inspection verifies cleanliness, function, amenities, safety, smell, damage and brand standards before release. | clean is checked |
| hotelops.rooms.release_to_frontdesk | Release to front desk | invariant | Release confirms room is ready for sale or check-in after cleaning and inspection are complete. | avoid guest wait |
| hotelops.linen.linen_par | Linen par level | invariant | Linen par level defines how many sets are needed for rooms, laundry cycle, reserve and peak occupancy. | запас без хаоса |
| hotelops.linen.linen_sorting | Linen sorting | invariant | Sorting separates sheets, towels, damaged items, stains and special handling before laundry. | качество и hygiene |
| hotelops.linen.laundry_turnaround | Laundry turnaround | invariant | Laundry turnaround measures time from dirty linen collection to clean linen available for rooms. | bottleneck housekeeping |
| hotelops.linen.stain_treatment | Linen stain treatment | variant | Stain treatment should match stain type, fabric, time and laundry chemistry before heat sets it. | не закрепить пятно |
| hotelops.linen.linen_loss | Linen loss control | invariant | Linen loss control tracks missing, damaged, discarded or misused linen by floor, vendor or process. | towels are inventory |
| hotelops.linen.vendor_laundry_check | Vendor laundry check | variant | Vendor laundry check verifies counts, quality, packaging, delivery time and rejected items from external laundry. | outsource still needs control |
| hotelops.public_area.lobby_cleaning | Lobby cleaning cycle | invariant | Lobby cleaning cycle maintains visible public areas through scheduled checks, spills, waste, glass and high-touch points. | first impression |
| hotelops.public_area.restroom_check | Public restroom check | invariant | Restroom checks verify supplies, cleanliness, odor, fixtures, floor safety and guest complaints. | small room, high impact |
| hotelops.public_area.corridor_standard | Corridor standard | invariant | Corridor standard covers vacuuming, lighting, smell, wall damage, carts, noise and emergency access. | guest path matters |
| hotelops.public_area.event_turnover | Event space turnover | variant | Event turnover resets rooms between functions with layout, cleaning, AV, waste, linens and timing constraints. | banquets move fast |
| hotelops.maintenance.maintenance_ticket | Hotel maintenance ticket | invariant | Ticket records room, issue, priority, reporter, status, technician and closure evidence. | defect becomes work |
| hotelops.maintenance.out_of_order | Out-of-order room | invariant | Out-of-order status removes a room from sale due to maintenance, safety, damage or deep cleaning. | protect guest experience |
| hotelops.maintenance.preventive_room_check | Preventive room check | variant | Preventive room check inspects HVAC, plumbing, lights, locks, furniture and finishes before guest complaints. | fix before failure |
| hotelops.maintenance.guest_reported_defect | Guest-reported defect | invariant | Guest defect report links complaint, room, urgency, recovery action and maintenance follow-up. | issue plus service recovery |
| hotelops.maintenance.water_leak_response | Water leak response | invariant | Leak response isolates source, protects guest areas, documents damage and escalates restoration if needed. | stop damage early |
| hotelops.maintenance.lock_battery | Electronic lock battery | variant | Lock battery maintenance prevents guest lockouts and security issues from low-power door hardware. | small battery, big frustration |
| hotelops.guest.lost_property_log | Lost property log | invariant | Lost property log records found item, location, date, finder, storage, claim and disposal status. | trust and evidence |
| hotelops.guest.guest_recovery | Guest recovery action | variant | Recovery action addresses service failure with apology, fix, compensation or follow-up within authority limits. | repair the relationship |
| hotelops.guest.special_request | Guest special request | variant | Special requests may include pillows, accessibility, allergies, crib, room location or cleaning preferences. | personalize operations |
| hotelops.guest.privacy_entry | Guest privacy entry control | invariant | Entry control governs when staff may enter occupied rooms and how entry is documented or announced. | privacy as control |
| hotelops.safety.cart_safety | Housekeeping cart safety | invariant | Cart safety controls hallway placement, chemicals, sharp objects, guest access and emergency egress. | cart is mobile workspace |
| hotelops.safety.chemical_labeling | Hotel chemical labeling | invariant | Cleaning chemicals require proper labels, dilution, storage and staff understanding of hazards. | avoid wrong chemical use |
| hotelops.safety.slip_hazard | Slip hazard control | invariant | Slip hazard control uses wet-floor signs, fast cleanup, mat checks and escalation for leaks or spills. | prevent guest injury |
| hotelops.safety.bedbug_protocol | Bedbug protocol | variant | Bedbug protocol isolates room, preserves evidence, moves guest carefully and coordinates pest control. | avoid spreading issue |
| hotelops.safety.sharps_found | Sharps found procedure | invariant | Sharps found procedure protects staff by avoiding hand pickup and using approved container and reporting. | hidden injury risk |
| hotelops.safety.emergency_room_check | Emergency room check | variant | Emergency checks may verify rooms or floors during alarms, welfare concerns or evacuation support under hotel policy. | safety during abnormal events |
| hotelops.inventory.amenity_par | Amenity par stock | invariant | Amenity par stock defines required quantities of soaps, paper goods, coffee, minibar items or guest supplies. | stock supports service |
| hotelops.inventory.minibar_reconciliation | Minibar reconciliation | variant | Minibar reconciliation compares consumed items, charges, expiry dates and restocking records. | small inventory, billing risk |
| hotelops.inventory.cleaning_supply_usage | Cleaning supply usage | invariant | Usage tracking identifies waste, theft, wrong dilution, vendor issues or abnormal occupancy effects. | supplies as controllable cost |
| hotelops.inventory.room_asset_check | Room asset check | invariant | Asset checks monitor irons, kettles, remotes, hangers, hairdryers, furniture and safety items. | prevent missing equipment |
| hotelops.planning.occupancy_forecast | Occupancy forecast for housekeeping | invariant | Forecast occupancy drives staffing, linen, room priorities, public area cycles and inventory needs. | demand before shift |
| hotelops.planning.labor_minutes_per_room | Labor minutes per room | variant | Minutes per room estimate depends on room type, stayover, checkout, brand standard and attendant experience. | workload math |
| hotelops.planning.deep_clean_schedule | Deep clean schedule | invariant | Deep cleaning rotates rooms or areas through tasks beyond daily cleaning, such as vents, carpets and detailed fixtures. | long-term quality |
| hotelops.planning.turn_down_service | Turndown service | variant | Turndown service prepares room for evening use with guest preference, timing, privacy and staffing constraints. | luxury workflow |
| hotelops.quality.brand_standard_audit | Brand standard audit | invariant | Audit checks rooms and public areas against documented hotel standards and evidence. | consistency across shifts |
| hotelops.quality.complaint_trend | Housekeeping complaint trend | invariant | Complaint trend analysis groups issues by room, floor, staff, defect type or recurring root cause. | complaints become improvement |
