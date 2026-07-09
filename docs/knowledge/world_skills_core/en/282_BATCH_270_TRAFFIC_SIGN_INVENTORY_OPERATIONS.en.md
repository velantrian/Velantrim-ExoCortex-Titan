# BATCH_270 — Traffic Sign Inventory Operations Detail
# world_skills_core · source: world_skills_core:batch_270:traffic_sign_inventory_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| signinv.inventory.sign_record | Traffic sign inventory record | invariant | Record stores sign ID, type, legend, location, support, direction and status. | know signs |
| signinv.inventory.sign_type | Traffic sign type | invariant | Type classifies regulatory, warning, guide, street-name, parking, school or temporary sign. | organize inventory |
| signinv.inventory.asset_tag | Traffic sign asset tag | variant | Tag links physical marker, barcode, RFID or painted ID to inventory record. | field identification |
| signinv.inventory.support_record | Sign support record | invariant | Record captures post, pole, mast arm, bracket, foundation, height and condition. | manage support |
| signinv.field.gps_collection | Traffic sign GPS collection | invariant | Collection records coordinates, side of road, offset, direction, accuracy and collector. | map sign |
| signinv.field.photo_capture | Traffic sign photo capture | invariant | Photo shows sign face, support, surroundings, visibility and defects. | visual evidence |
| signinv.field.installation_date | Traffic sign installation date | variant | Date records known, estimated or imported install date and source confidence. | lifecycle |
| signinv.condition.face_condition | Sign face condition | invariant | Condition records fading, damage, graffiti, peeling, dirt, bullet holes or missing legend. | maintain readability |
| signinv.condition.support_condition | Sign support condition | invariant | Condition reviews leaning, rust, bending, breakaway hardware, foundation and attachment. | structural safety |
| signinv.condition.visibility_obstruction | Sign visibility obstruction | invariant | Obstruction notes vegetation, parked vehicles, poles, curves, lighting or competing signs. | improve visibility |
| signinv.reflectivity.reflectivity_test | Sign retroreflectivity test | invariant | Test records method, reading, date, sign type, sheeting and result. | nighttime visibility |
| signinv.reflectivity.replacement_threshold | Sign reflectivity replacement threshold | invariant | Threshold defines minimum acceptable visibility by sign type or management method. | decide replacement |
| signinv.reflectivity.night_review | Traffic sign night review | variant | Review checks visibility, glare, headlight response and sign conspicuity in dark conditions. | driver safety |
| signinv.workorder.missing_sign | Missing sign work order | invariant | Work order records sign type, location, urgency, temporary control and replacement. | restore control |
| signinv.workorder.damaged_sign | Damaged sign work order | invariant | Work order captures crash, vandalism, weather, wear, support damage and repair need. | fix defect |
| signinv.workorder.knockdown_response | Sign knockdown response | invariant | Response secures hazard, installs temporary sign if needed and schedules permanent repair. | reduce risk |
| signinv.workorder.vegetation_clearance | Sign vegetation clearance | variant | Order removes branches, weeds or shrubs blocking sign face or sightline. | restore visibility |
| signinv.replacement.replacement_plan | Traffic sign replacement plan | invariant | Plan prioritizes signs by safety, reflectivity, age, condition and route. | renew assets |
| signinv.replacement.batch_replacement | Sign batch replacement | variant | Replacement groups signs by corridor, neighborhood, sheeting age or crew route. | efficient work |
| signinv.replacement.material_spec | Traffic sign material specification | invariant | Specification defines sheeting, substrate, size, legend, color, hardware and support. | build correctly |
| signinv.replacement.install_verification | Sign installation verification | invariant | Verification confirms sign type, location, height, orientation, fasteners and photo. | quality |
| signinv.mapping.map_layer | Traffic sign map layer | invariant | Layer displays sign records, status, condition, work orders and filters. | spatial management |
| signinv.mapping.route_segment | Sign route segment link | variant | Link connects sign to road segment, intersection, milepost or asset corridor. | network context |
| signinv.mapping.intersection_group | Sign intersection group | variant | Group associates stop, yield, street-name, lane and pedestrian signs at one node. | manage intersection |
| signinv.audit.inventory_audit | Traffic sign inventory audit | invariant | Audit compares field signs to records, missing assets, duplicates and location errors. | data quality |
| signinv.audit.duplicate_record | Duplicate sign record resolution | invariant | Resolution merges repeated records, preserves history and confirms physical sign. | clean database |
| signinv.audit.random_sample | Sign inventory random sample | variant | Sample checks selected signs for condition, location, reflectivity and record accuracy. | verify program |
| signinv.regulatory.stop_sign_control | Stop sign control record | invariant | Record tracks stop sign placement, approach, warrant, support and priority. | critical control |
| signinv.regulatory.speed_limit_sign | Speed limit sign record | invariant | Record stores posted speed, ordinance, location, direction and effective limits. | legal clarity |
| signinv.regulatory.parking_sign | Parking sign record | variant | Record captures restriction, days, times, zone, curb limits and ordinance reference. | curb management |
| signinv.school.school_zone_sign | School zone sign record | variant | Record tracks school zone, flashing beacon, times, assemblies and crosswalk relation. | student safety |
| signinv.temporary.temporary_sign | Temporary traffic sign record | variant | Record tracks work zone, event, detour or emergency sign placement and removal date. | avoid forgotten signs |
| signinv.stock.sign_stock | Traffic sign stock inventory | invariant | Stock tracks blanks, finished signs, sheeting, posts, hardware and reorder point. | material readiness |
| signinv.stock.fabrication_order | Sign fabrication order | variant | Order specifies legend, size, material, quantity, due date and requester. | produce sign |
| signinv.stock.scrap_record | Traffic sign scrap record | variant | Record documents retired signs, salvage, disposal, theft risk and material recycling. | asset closure |
| signinv.safety.field_safety | Sign inventory field safety | invariant | Safety covers traffic exposure, high visibility, parking, cones, weather and lone work. | protect staff |
| signinv.safety.lane_work | Traffic sign lane work control | variant | Control defines lane closure, shoulder work, spotter, vehicle placement and signage. | safe repair |
| signinv.communication.public_request | Traffic sign public request | invariant | Request records missing, confusing, damaged, new sign or visibility complaint. | citizen input |
| signinv.communication.agency_coordination | Sign agency coordination | variant | Coordination handles state road, county, utility pole, railroad or private road sign issues. | route ownership |
| signinv.reporting.condition_report | Traffic sign condition report | invariant | Report summarizes signs by condition, age, reflectivity, type, district and backlog. | plan renewal |
| signinv.reporting.work_completion | Sign work completion report | invariant | Report records installed, repaired, removed, pending and material usage. | track output |
| signinv.metrics.sign_inventory_kpi | Traffic sign inventory KPI | variant | KPI tracks inventory completeness, poor condition, reflectivity pass rate, missing signs and repair time. | manage signs |
| signinv.continuity.storm_damage | Traffic sign storm damage response | variant | Response inventories knocked down, missing, blocked or dangerous signs after storm. | restore control |
| signinv.close.sign_retirement | Traffic sign retirement | invariant | Retirement records removal reason, date, replacement, disposal and map update. | close lifecycle |
