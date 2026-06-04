# BATCH 385: Temporary Traffic Control After Disasters

**KnowledgeUnits:** 44  
**Namespace:** `disastertrafficops.*`  
**Scope:** detours, barricades, signals, flaggers, emergency access, inspections and demobilization.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| disastertrafficops.activation.trigger | traffic control trigger | MODEL | Trigger includes road damage, debris, evacuation, utility work, flooding or emergency repair. | Starts temporary control plan. |
| disastertrafficops.activation.traffic_lead | traffic lead | RECORD | Lead coordinates public works, police, fire, transit and contractors. | Clarifies responsibility. |
| disastertrafficops.activation.priority_route | priority route | MODEL | Priority routes include emergency access, evacuation, hospitals, shelters and supply corridors. | Protects critical movement. |
| disastertrafficops.activation.safety_brief | safety briefing | SAFETY_RULE | Brief covers work zones, night visibility, floodwater, downed wires and driver behavior. | Protects crews. |
| disastertrafficops.plan.control_plan | control plan | RECORD | Plan records closure, detour, devices, staffing, timing and approval. | Makes field setup deliberate. |
| disastertrafficops.plan.mutcd_check | standards check | CONSTRAINT | Devices and layouts follow applicable temporary traffic control standards. | Keeps setups defensible. |
| disastertrafficops.plan.emergency_access | emergency access | SAFETY_RULE | Fire, EMS and police access is preserved or rerouted. | Maintains response capability. |
| disastertrafficops.plan.accessibility | accessibility | METHOD | Pedestrian, transit and disability access are considered when feasible. | Reduces public harm. |
| disastertrafficops.devices.barricade | barricade | METHOD | Barricades block unsafe roads or lanes with clear approach warning. | Prevents entry. |
| disastertrafficops.devices.cones | cones and drums | METHOD | Cones/drums channel vehicles around hazards and work areas. | Defines travel path. |
| disastertrafficops.devices.signs | temporary signs | METHOD | Signs warn, guide, detour and explain closures. | Reduces confusion. |
| disastertrafficops.devices.lighting | lighting | SAFETY_RULE | Night or low-visibility setups need lights or reflective devices. | Improves visibility. |
| disastertrafficops.detour.detour_route | detour route | METHOD | Detour route checks capacity, bridge limits, turns, transit and emergency access. | Avoids new bottlenecks. |
| disastertrafficops.detour.map_update | map update | METHOD | Detours update GIS, dispatch, public websites and navigation partners when possible. | Keeps routing current. |
| disastertrafficops.detour.local_access | local access | CONSTRAINT | Local access rules allow residents, businesses or responders where safe. | Balances closure and access. |
| disastertrafficops.detour.truck_route | truck route | METHOD | Heavy vehicles need route checks for height, weight, turning and pavement condition. | Prevents damage. |
| disastertrafficops.flagging.flagger_assignment | flagger assignment | RECORD | Assignment records location, shift, supervisor, radio and traffic pattern. | Controls staffing. |
| disastertrafficops.flagging.training | flagger training | SAFETY_RULE | Flaggers need training, PPE and escape path. | Reduces injury. |
| disastertrafficops.flagging.radio | radio coordination | METHOD | Opposing flaggers coordinate via radio or visible line when alternating traffic. | Prevents head-on conflicts. |
| disastertrafficops.flagging.relief | relief schedule | METHOD | Relief schedule manages fatigue, heat, cold and long shifts. | Maintains attention. |
| disastertrafficops.signals.temporary_signal | temporary signal | METHOD | Temporary signals control one-lane or damaged intersections when flagging is impractical. | Improves flow. |
| disastertrafficops.signals.generator | signal power | METHOD | Generator or battery supports critical signals during outage. | Maintains intersection control. |
| disastertrafficops.signals.timing | timing adjustment | METHOD | Signal timing adjusts for detour volumes and emergency routes. | Reduces congestion. |
| disastertrafficops.signals.failure | signal failure | FAILURE_MODE | Failed signals require stop control, police/manual control or repair. | Keeps intersections safe. |
| disastertrafficops.field.install | field installation | METHOD | Crews install devices per plan and site conditions. | Creates real-world control. |
| disastertrafficops.field.inspection | field inspection | QUALITY_CHECK | Inspection checks device placement, visibility, stability and public behavior. | Catches unsafe setups. |
| disastertrafficops.field.adjustment | field adjustment | METHOD | Layout changes when traffic, water, debris or work scope changes. | Keeps control relevant. |
| disastertrafficops.field.damage | device damage | RECORD | Damaged or missing devices are logged and replaced. | Maintains control. |
| disastertrafficops.communication.public_notice | public notice | METHOD | Notices state closures, detours, expected duration and safety advice. | Helps drivers plan. |
| disastertrafficops.communication.dispatch | dispatch notification | METHOD | Dispatch receives current closures and emergency access routes. | Supports responders. |
| disastertrafficops.communication.partner | partner notice | METHOD | Transit, schools, utilities and neighboring jurisdictions receive updates. | Aligns operations. |
| disastertrafficops.communication.change_notice | change notice | METHOD | Route or schedule changes are communicated quickly. | Reduces surprises. |
| disastertrafficops.records.device_log | device log | RECORD | Log tracks devices placed, moved, damaged, recovered and stored. | Controls inventory. |
| disastertrafficops.records.work_log | work log | RECORD | Work log captures crews, equipment, hours and site changes. | Supports reimbursement. |
| disastertrafficops.records.photo | photo documentation | RECORD | Photos document layout, hazards and changes. | Supports audit and claims. |
| disastertrafficops.records.retention | retention rule | CONSTRAINT | Traffic control records follow public works and disaster retention rules. | Preserves evidence. |
| disastertrafficops.qa.drive_through | drive-through review | QUALITY_CHECK | Supervisor drives route to verify understandable guidance. | Improves driver experience. |
| disastertrafficops.qa.crash_review | crash review | QUALITY_CHECK | Crashes or near misses trigger layout review. | Reduces repeated incidents. |
| disastertrafficops.qa.compliance | compliance check | QUALITY_CHECK | Device setups are checked against standards and approved deviations. | Protects liability. |
| disastertrafficops.metrics.closure_count | closure count | MEASUREMENT | Counts track closures, restrictions, detours and reopenings. | Shows network status. |
| disastertrafficops.metrics.response_time | setup response time | MEASUREMENT | Time from request to installed control shows readiness. | Finds bottlenecks. |
| disastertrafficops.demob.device_recovery | device recovery | METHOD | Devices are retrieved, inspected, cleaned and restocked. | Ends control safely. |
| disastertrafficops.demob.reopen_check | reopen check | QUALITY_CHECK | Road reopens after hazard cleared and traffic control removed/changed. | Prevents unsafe reopening. |
| disastertrafficops.review.after_action | after-action review | METHOD | Review captures detour quality, device shortages, crashes and partner coordination. | Improves next disaster. |
