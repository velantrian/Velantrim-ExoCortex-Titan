# BATCH_213 — Locksmith Service Operations Detail
# world_skills_core · source: world_skills_core:batch_213:locksmith_service_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| lockops.intake.service_call | Locksmith service call | invariant | Call records customer, location, lock type, urgency, access issue, authorization and contact. | open secure job |
| lockops.intake.identity_authorization | Locksmith authorization check | invariant | Check verifies customer has right to request entry, rekey or key work. | prevent misuse |
| lockops.intake.property_permission | Property permission evidence | invariant | Evidence may include ID, lease, ownership, manager approval or vehicle registration. | lawful service |
| lockops.intake.emergency_lockout | Emergency lockout | variant | Lockout request prioritizes access need, safety, identity and dispatch speed. | urgent entry |
| lockops.intake.risk_screen | Locksmith risk screen | invariant | Screen flags domestic dispute, eviction, law enforcement, unsafe site or suspicious request. | do not enable harm |
| lockops.dispatch.technician_dispatch | Locksmith technician dispatch | invariant | Dispatch assigns tech, vehicle, skill, tools, ETA and job notes. | route expert |
| lockops.dispatch.route_eta | Locksmith route ETA | variant | ETA accounts for traffic, emergency priority, parts and location. | customer expectation |
| lockops.dispatch.after_hours | After-hours locksmith process | variant | Process handles premium pricing, safety check-in, limited parts and escalation. | night work control |
| lockops.dispatch.cancel_arrival | Cancel-on-arrival | invariant | Record documents customer canceled, gained entry, no authorization or unsafe condition. | explain no work |
| lockops.dispatch.work_order | Locksmith work order | invariant | Work order captures scope, labor, parts, authorization, photos and completion notes. | job record |
| lockops.key.key_blank_identification | Key blank identification | invariant | Identification matches profile, length, shoulder, blade and manufacturer reference. | cut right key |
| lockops.key.key_cutting | Key cutting | invariant | Cutting duplicates or originates key using machine, code, depth and quality check. | produce working key |
| lockops.key.key_control | Locksmith key control | invariant | Control tracks customer keys, blanks, restricted keys, custody and disposal. | protect security |
| lockops.key.restricted_keyway | Restricted keyway | variant | Keyway limits duplication to authorized parties and controlled blanks. | access governance |
| lockops.key.master_key_record | Master key record | variant | Record documents hierarchy, changes, issued keys and authorization. | high-risk system |
| lockops.lock.rekey | Rekey service | invariant | Rekey changes cylinder pinning or coding so old key no longer operates. | reset access |
| lockops.lock.cylinder_service | Cylinder service | invariant | Service cleans, repairs, repins, replaces or tests lock cylinder. | restore operation |
| lockops.lock.lock_install | Lock installation | invariant | Installation fits hardware, strike, latch, alignment, fasteners and function. | physical security |
| lockops.lock.lock_repair | Lock repair | invariant | Repair addresses sticking, misalignment, broken latch, worn parts or damaged hardware. | keep door working |
| lockops.lock.hardware_grade | Hardware grade | variant | Grade indicates durability or security rating suitable for use context. | choose appropriate lock |
| lockops.access.non_destructive_entry | Non-destructive entry | variant | Entry attempts lawful opening with minimal damage before destructive methods. | preserve hardware |
| lockops.access.destructive_entry | Destructive entry | variant | Entry damages lock or hardware when authorized and necessary. | last resort |
| lockops.access.vehicle_lockout | Vehicle lockout service | variant | Service opens vehicle using authorized method while protecting airbags, glass, weather seals and electronics. | avoid damage |
| lockops.access.safe_opening | Safe opening workflow | variant | Workflow verifies authorization, safe type, lock, contents sensitivity and documentation. | high-security job |
| lockops.access.exit_device | Exit device service | variant | Service checks panic hardware, latch, dogging, alarm interface and code requirements. | life safety |
| lockops.electronic.access_control_reader | Access control reader | variant | Reader installation or service checks credentials, wiring, controller, door hardware and logs. | electronic entry |
| lockops.electronic.electrified_lock | Electrified lock | variant | Lock integrates power, fail-safe or fail-secure behavior, fire alarm and access rules. | door logic |
| lockops.electronic.keypad_programming | Keypad programming | variant | Programming manages codes, users, schedules, master code and audit needs. | code governance |
| lockops.electronic.battery_check | Electronic lock battery check | invariant | Check verifies battery status, replacement, date and low-battery alerts. | avoid lockout |
| lockops.electronic.audit_log | Electronic lock audit log | variant | Log records access events, programming changes, failed attempts and time settings. | trace access |
| lockops.safe.security_seal | Locksmith security seal | variant | Seal indicates whether container, safe, key cabinet or hardware was opened or altered. | tamper evidence |
| lockops.safe.customer_presence | Customer presence rule | invariant | Rule defines when authorized customer must be present during opening, keying or safe work. | accountability |
| lockops.safe.evidence_handling | Locksmith evidence handling | variant | Handling protects keys, locks, photos and parts involved in investigation or dispute. | preserve facts |
| lockops.safe.drill_point_record | Safe drill point record | variant | Record documents destructive opening location, reason and repair recommendation. | transparency |
| lockops.safe.resecure | Re-secure after entry | invariant | Re-secure restores lock, temporary closure or replacement after entry work. | do not leave vulnerable |
| lockops.inventory.lock_hardware_stock | Lock hardware stock | invariant | Stock tracks cylinders, locks, strikes, closers, blanks, batteries and specialty parts. | ready van |
| lockops.inventory.tool_control | Locksmith tool control | invariant | Control protects picks, decoders, programmers, key machines and restricted tools. | sensitive equipment |
| lockops.inventory.part_serial | Lock part serial record | variant | Record tracks serialized or restricted hardware issued to customer. | trace controlled parts |
| lockops.billing.service_invoice | Locksmith service invoice | invariant | Invoice lists trip, labor, parts, emergency fee, authorization and payment. | close job |
| lockops.billing.price_quote | Locksmith price quote | invariant | Quote states service call, labor range, parts and conditions before work. | avoid surprise |
| lockops.quality.function_test | Lock function test | invariant | Test checks key operation, latch, strike, deadbolt throw, door close and user instruction. | prove security |
| lockops.quality.customer_signature | Locksmith customer signature | invariant | Signature confirms work completed, keys returned, site secured and charges accepted. | handoff evidence |
| lockops.metrics.locksmith_kpi | Locksmith KPI | variant | KPI tracks response time, first-visit completion, callbacks, authorization issues and parts use. | manage service |
| lockops.continuity.lost_key_incident | Lost key incident process | invariant | Process documents lost controlled key, affected doors, rekey need and notifications. | contain exposure |
