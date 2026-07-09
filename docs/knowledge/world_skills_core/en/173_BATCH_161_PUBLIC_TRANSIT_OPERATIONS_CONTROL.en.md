# BATCH_161 — Public Transit Operations Control Detail
# world_skills_core · source: world_skills_core:batch_161:public_transit_operations_control
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| transitops.service.headway | Headway | invariant | Headway is the time interval between vehicles on the same route or line. | frequency passengers feel |
| transitops.service.running_time | Running time | invariant | Running time estimates travel duration between points under scheduled operating conditions. | schedule realism |
| transitops.service.recovery_time | Recovery time | invariant | Recovery time gives operators and vehicles buffer at terminals before next trip. | absorb small delays |
| transitops.service.block | Vehicle block | invariant | Block is a sequence of trips assigned to one vehicle during a service day. | vehicle work package |
| transitops.service.trip | Transit trip | invariant | Trip is a scheduled one-way movement between origin and destination on a route. | atomic service unit |
| transitops.service.short_turn | Short turn | variant | Short turn reverses a delayed vehicle before route end to restore spacing or cover demand. | recover headway |
| transitops.control.dispatcher | Transit dispatcher | invariant | Dispatcher monitors service, incidents, operators, vehicles and field resources during operations. | control center role |
| transitops.control.headway_management | Headway management | invariant | Headway management adjusts departures or holds vehicles to reduce bunching and gaps. | even service matters |
| transitops.control.holding | Vehicle holding | variant | Holding delays a vehicle at a stop or terminal to restore spacing or meet transfer needs. | intentional delay |
| transitops.control.bunching | Bus bunching | invariant | Bunching occurs when vehicles on same route get too close and uneven passenger loads worsen delay. | gap creates more gap |
| transitops.control.turnback | Rail turnback | variant | Turnback uses crossover or terminal movement to reverse trains before full route completion. | recover disrupted line |
| transitops.control.control_log | Operations control log | invariant | Control log records decisions, incidents, times, messages, resources and service changes. | operational memory |
| transitops.depot.pull_out | Depot pull-out | invariant | Pull-out sends vehicles from depot to route start according to block, operator, inspection and fueling readiness. | service starts before first stop |
| transitops.depot.pull_in | Depot pull-in | invariant | Pull-in returns vehicle to depot after service for inspection, fueling, cleaning or defect reporting. | end of service loop |
| transitops.depot.vehicle_assignment | Transit vehicle assignment | invariant | Assignment matches vehicle to block by type, capacity, range, accessibility, maintenance status and route constraints. | right bus or train |
| transitops.depot.operator_sign_on | Operator sign-on | invariant | Sign-on confirms operator attendance, qualification, work assignment, notices and readiness. | people start service |
| transitops.depot.defect_card | Transit defect card | invariant | Defect card reports vehicle problems from operator or maintenance for triage and repair. | safety feedback |
| transitops.depot.spare_ratio | Spare vehicle ratio | variant | Spare ratio provides reserve vehicles for maintenance, breakdowns or demand variation. | resilience fleet |
| transitops.disruption.service_gap | Service gap | invariant | Service gap is a missing or long interval in scheduled service affecting passenger waiting time. | passenger pain point |
| transitops.disruption.detour | Transit detour | variant | Detour reroutes service around construction, incident, flood, event or obstruction. | keep line moving |
| transitops.disruption.bus_bridge | Bus bridge | variant | Bus bridge replaces disrupted rail segment using buses between affected stations. | temporary substitute |
| transitops.disruption.incident_commander | Transit incident commander | variant | Incident commander coordinates field response, control center, emergency services and service recovery. | one response lead |
| transitops.disruption.service_suspension | Service suspension | invariant | Suspension stops service on route or segment when safety, infrastructure or resources prevent operation. | stop when unsafe |
| transitops.disruption.recovery_plan | Transit recovery plan | invariant | Recovery plan restores service through vehicle repositioning, operator relief, schedule adjustment and customer messaging. | return to normal |
| transitops.passenger.realtime_info | Real-time passenger information | invariant | Real-time info shows predicted arrivals, disruptions, platform changes or service alerts. | reduce uncertainty |
| transitops.passenger.service_alert | Service alert | invariant | Service alert communicates disruption, affected routes, alternatives, duration and updates. | clear public message |
| transitops.passenger.transfer_protection | Transfer protection | variant | Transfer protection delays connection within limits to preserve passenger movement without cascading service harm. | help connections |
| transitops.passenger.crowding_monitor | Crowding monitor | variant | Crowding monitor tracks passenger loads and crowd risk by vehicle, stop, station or time. | capacity awareness |
| transitops.passenger.accessibility_disruption | Accessibility disruption | invariant | Accessibility disruption reports elevator, ramp, low-floor vehicle or station access issues. | equal access needs visibility |
| transitops.passenger.platform_management | Platform management | variant | Platform management controls crowd distribution, boarding flow, safety lines and information during peak or disruption. | station as flow system |
| transitops.fares.fare_validator | Fare validator | invariant | Fare validator reads ticket, card, phone or pass and records validation outcome. | payment gate |
| transitops.fares.fare_capping | Fare capping | variant | Fare capping limits passenger charges over period when rules and trips qualify. | fair pricing automation |
| transitops.fares.fare_evasion_check | Fare evasion check | variant | Inspection checks proof of payment under policy while managing fairness, safety and documentation. | revenue protection |
| transitops.fares.ticket_machine_fault | Ticket machine fault | invariant | Machine fault affects passenger access, cash/card handling, refunds and maintenance response. | fare system reliability |
| transitops.safety.operator_fatigue | Operator fatigue risk | invariant | Fatigue risk depends on shifts, breaks, overtime, sleep opportunity and route stress. | human safety factor |
| transitops.safety.speed_restriction | Speed restriction | invariant | Speed restriction limits vehicle speed due to track, road, weather, work zone or safety condition. | safety over timetable |
| transitops.safety.radio_protocol | Transit radio protocol | invariant | Radio protocol structures messages by unit, location, issue, priority and acknowledgement. | avoid control confusion |
| transitops.safety.passenger_incident | Passenger incident | invariant | Passenger incident records medical, security, behavior, injury or assistance event and response. | support and evidence |
| transitops.safety.near_miss | Transit near miss | invariant | Near miss captures unsafe event without injury or collision and supports safety improvement. | learn before crash |
| transitops.safety.road_supervisor | Road supervisor | variant | Road supervisor provides field support for operators, incidents, detours, observations and customer issues. | control center eyes |
| transitops.metrics.on_time_performance | On-time performance | invariant | OTP measures service against schedule within defined early and late thresholds. | schedule reliability |
| transitops.metrics.excess_wait_time | Excess wait time | invariant | Excess wait time measures additional passenger waiting caused by irregular service. | passenger-centered reliability |
| transitops.metrics.missed_trip | Missed trip | invariant | Missed trip occurs when scheduled service is not operated as planned. | service not delivered |
| transitops.metrics.passenger_load_factor | Passenger load factor | variant | Load factor compares passenger count with seated or total capacity. | crowding metric |
