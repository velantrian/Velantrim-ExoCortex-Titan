# BATCH 420: Emergency Public Charging Station Operations

**KnowledgeUnits:** 44  
**Namespace:** `chargingstationops.*`  
**Scope:** site setup, power, queues, device safety, accessibility, security and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| chargingstationops.activation.trigger | activation trigger | MODEL | Trigger includes power outage, sheltering, communications need or public service disruption. | Starts charging support. |
| chargingstationops.activation.site_selection | site selection | METHOD | Site checks power source, shelter, access, supervision, weather cover and crowd space. | Chooses workable site. |
| chargingstationops.activation.service_model | service model | RECORD | Model distinguishes self-serve tables, supervised charging, lockers or mobile charging. | Defines operation. |
| chargingstationops.activation.command_link | command link | RECORD | Station reports to logistics, facilities, safety, public information and security. | Maintains oversight. |
| chargingstationops.power.power_source | power source | RECORD | Source records grid, generator, battery, solar, vehicle or building circuit. | Tracks supply. |
| chargingstationops.power.load_limit | load limit | MEASUREMENT | Limit calculates safe device count by circuit, generator and equipment rating. | Prevents overload. |
| chargingstationops.power.cable_plan | cable plan | METHOD | Cable plan routes cords, strips and chargers to avoid trip and fire hazards. | Keeps setup safe. |
| chargingstationops.power.backup_plan | backup plan | METHOD | Backup plan handles outage, generator failure, battery depletion or equipment loss. | Maintains continuity. |
| chargingstationops.setup.table_layout | table layout | METHOD | Layout separates intake, charging, waiting, accessibility and staff areas. | Improves flow. |
| chargingstationops.setup.signage | signage | RECORD | Signs show hours, limits, queue rules, safety and pickup process. | Reduces confusion. |
| chargingstationops.setup.weather_cover | weather cover | SAFETY_RULE | Charging is protected from rain, heat, dust and wind where feasible. | Protects devices. |
| chargingstationops.setup.fire_clearance | fire clearance | SAFETY_RULE | Setup keeps outlets, batteries and exits clear with fire equipment accessible. | Reduces fire risk. |
| chargingstationops.queue.checkin | check-in | RECORD | Check-in records user, device type, time, station slot and claim method if supervised. | Tracks devices. |
| chargingstationops.queue.time_limit | time limit | CONSTRAINT | Time limits define fair charging duration and extension rules. | Expands access. |
| chargingstationops.queue.priority | priority rule | MODEL | Priority may support medical devices, emergency contacts, accessibility needs or responders. | Handles urgent need. |
| chargingstationops.queue.waitlist | waitlist | RECORD | Waitlist records name/code, device type, need and contact method. | Manages demand. |
| chargingstationops.device.labeling | device labeling | METHOD | Labels connect device, charger, slot and owner without exposing private data. | Prevents mixups. |
| chargingstationops.device.compatibility | compatibility check | METHOD | Staff check connector, wattage, adapter and device condition before charging. | Avoids damage. |
| chargingstationops.device.battery_safety | battery safety | SAFETY_RULE | Swollen, hot, wet or damaged batteries are isolated and not charged. | Prevents fire. |
| chargingstationops.device.medical_device | medical device | SAFETY_RULE | Medical devices receive priority and may require dedicated safe power. | Protects health. |
| chargingstationops.accessibility.access_lane | access lane | METHOD | Accessible line and table height support wheelchairs, elders and mobility needs. | Improves access. |
| chargingstationops.accessibility.seating | seating support | METHOD | Waiting area includes seats, shade, water and clear pathways where possible. | Reduces hardship. |
| chargingstationops.accessibility.language | language support | METHOD | Signs and scripts use common local languages and simple icons. | Improves comprehension. |
| chargingstationops.accessibility.assistance | assistance request | RECORD | Staff record needs for help plugging, lifting, reading labels or pickup. | Supports users. |
| chargingstationops.security.supervision | supervision rule | SAFETY_RULE | Station is supervised or uses lockers to reduce theft and disputes. | Protects devices. |
| chargingstationops.security.claim_check | claim check | METHOD | Claim check uses ticket, code, ID policy or matching label. | Returns correct device. |
| chargingstationops.security.lost_device | lost device report | RECORD | Lost device report captures owner claim, slot, time, staff and investigation. | Handles loss. |
| chargingstationops.security.conflict | conflict handling | METHOD | Conflict over queue, time or device routes to supervisor/security. | Reduces escalation. |
| chargingstationops.operations.staff_roster | staff roster | RECORD | Roster covers lead, check-in, device monitor, runner, safety and security contact. | Maintains coverage. |
| chargingstationops.operations.shift_brief | shift brief | METHOD | Brief covers load limits, queue rules, safety triggers, lost device and escalation. | Aligns staff. |
| chargingstationops.operations.equipment_count | equipment count | MEASUREMENT | Count tracks power strips, chargers, adapters, labels, tables and lockers. | Shows readiness. |
| chargingstationops.operations.cleaning | cleaning routine | METHOD | Routine cleans tables, high-touch areas and cable clutter. | Keeps station orderly. |
| chargingstationops.communication.public_notice | public notice | METHOD | Notice states location, hours, limits, priority rules, accessibility and safety restrictions. | Guides residents. |
| chargingstationops.communication.status_update | status update | METHOD | Updates announce wait time, closure, relocation, outage or equipment issue. | Reduces frustration. |
| chargingstationops.records.daily_log | daily log | RECORD | Log stores hours, staff, device count, incidents, outages and equipment issues. | Creates audit trail. |
| chargingstationops.records.incident | incident report | RECORD | Incident records injury, shock, fire, theft, damaged device or conflict. | Supports review. |
| chargingstationops.records.equipment_log | equipment log | RECORD | Equipment log records chargers, cords, batteries, strips, labels and missing items. | Controls assets. |
| chargingstationops.records.retention | retention rule | CONSTRAINT | Records follow emergency, privacy, facility and incident retention schedules. | Preserves audit. |
| chargingstationops.metrics.devices_charged | devices charged | MEASUREMENT | Count tracks devices charged by type and time period. | Shows output. |
| chargingstationops.metrics.wait_time | wait time | MEASUREMENT | Wait time measures queue length and time to slot. | Reveals bottleneck. |
| chargingstationops.metrics.power_uptime | power uptime | MEASUREMENT | Uptime tracks hours station power is available versus planned. | Shows reliability. |
| chargingstationops.qa.safety_walk | safety walk | QUALITY_CHECK | Walk checks cords, heat, load, batteries, exits and crowding. | Prevents hazards. |
| chargingstationops.demob.closeout | station closeout | METHOD | Closeout returns devices, powers down, counts equipment and archives logs. | Ends safely. |
| chargingstationops.review.after_action | after-action review | METHOD | Review captures site choice, load limits, queue fairness, security and device safety lessons. | Improves future charging. |
