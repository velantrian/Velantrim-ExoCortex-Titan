# BATCH_170 — Event Venue Operations Detail
# world_skills_core · source: world_skills_core:batch_170:event_venue_operations_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| venueops.ticketing.ticket_manifest | Ticket manifest | invariant | Manifest lists tickets, sections, seats, prices, holds, comps and sales status. | seat inventory truth |
| venueops.ticketing.scan_gate | Ticket scan gate | invariant | Scan gate validates barcode, pass, credential or wristband and records entry event. | access proof |
| venueops.ticketing.duplicate_scan | Duplicate scan | invariant | Duplicate scan indicates ticket already used or copied and requires exception handling. | fraud or mistake |
| venueops.ticketing.will_call | Will-call pickup | variant | Will-call verifies identity and releases reserved tickets or credentials at venue. | controlled pickup |
| venueops.ticketing.box_office_reconciliation | Box office reconciliation | invariant | Reconciliation compares sales, refunds, cash, card, comps and ticket inventory. | money and seats align |
| venueops.ticketing.accessible_seating | Accessible seating management | invariant | Accessible seating protects suitable locations, companion seats and conversion rules. | inclusive access |
| venueops.access.credential_zone | Event credential zone | invariant | Credential zones restrict backstage, production, media, VIP, vendor or staff areas. | not every pass opens all |
| venueops.access.bag_check | Bag check operation | variant | Bag check screens items according to policy while managing privacy, speed and prohibited goods. | safety at entry |
| venueops.access.reentry_policy | Re-entry policy | variant | Re-entry policy defines whether guests can leave and return using stamp, scan or credential. | control perimeter |
| venueops.access.queue_management | Entry queue management | invariant | Queue management uses lanes, signage, staff, barriers and information to control arrival flow. | first crowd bottleneck |
| venueops.access.gate_rate | Gate throughput rate | invariant | Gate rate measures guests processed per gate per time under current screening rules. | entry capacity |
| venueops.access.prohibited_item_log | Prohibited item log | invariant | Log records confiscated, returned or refused items with policy basis and incident details. | accountable screening |
| venueops.crowd.crowd_flow_plan | Crowd flow plan | invariant | Plan maps guest movement between gates, concourses, seating, toilets, concessions and exits. | people as flow |
| venueops.crowd.capacity_limit | Venue capacity limit | invariant | Capacity limit defines maximum occupancy by permit, layout, exits, seating or event configuration. | never exceed safe capacity |
| venueops.crowd.pinching_point | Crowd pinch point | invariant | Pinch point is a narrow or conflicting area where crowd density and delay can increase risk. | find bottlenecks |
| venueops.crowd.egress_plan | Event egress plan | invariant | Egress plan manages how audience exits after event using routes, staff, lighting and transport coordination. | leaving is also operation |
| venueops.crowd.front_of_stage_barrier | Front-of-stage barrier | variant | Barrier separates audience from stage and creates controlled access for security and medical response. | high-energy crowd zone |
| venueops.crowd.crowd_density_monitor | Crowd density monitor | variant | Monitoring estimates crowd density by observation, cameras, counters or reports. | risk before crush |
| venueops.production.stage_changeover | Stage changeover | invariant | Changeover moves equipment, instruments, scenery or setup between acts under timing and safety constraints. | show keeps moving |
| venueops.production.load_in | Event load-in | invariant | Load-in brings production, vendor and event equipment into venue with dock, labor, lift and schedule controls. | build the event |
| venueops.production.load_out | Event load-out | invariant | Load-out removes equipment after event while managing fatigue, traffic, inventory and damage risk. | teardown safely |
| venueops.production.power_drop | Temporary power drop | invariant | Power drop provides event power with load, cable routing, protection and authorized connection. | electricity for show |
| venueops.production.sound_check | Sound check | variant | Sound check verifies audio routing, levels, monitors, microphones and room response before doors or show. | technical readiness |
| venueops.production.run_of_show | Run of show | invariant | Run of show sequences cues, times, speakers, performances, breaks and operational notes. | shared event script |
| venueops.vendor.vendor_checkin | Vendor check-in | invariant | Check-in verifies vendor identity, space, permits, insurance, load-in time and rules. | controlled marketplace |
| venueops.vendor.food_vendor_inspection | Food vendor inspection | variant | Inspection checks permit, temperature, hygiene, setup, allergen information and waste controls. | food safety at venue |
| venueops.vendor.merch_inventory | Merchandise inventory | variant | Merch inventory tracks items, starting count, sales, comps, returns and settlement. | product plus money |
| venueops.vendor.settlement_sheet | Vendor settlement sheet | invariant | Settlement sheet records sales, fees, commissions, taxes, cash, card and payout. | close financials |
| venueops.vendor.waste_plan | Event waste plan | invariant | Waste plan sets bins, streams, pickup, staff, signage and post-event cleaning. | cleanup built in |
| venueops.vendor.water_station | Water station | variant | Water station supports hydration, crowd welfare and reduced medical incidents during event. | simple welfare control |
| venueops.safety.safety_briefing | Event safety briefing | invariant | Briefing aligns staff on risks, roles, communications, evacuation, medical and incident reporting. | everyone knows response |
| venueops.safety.incident_log | Venue incident log | invariant | Incident log records injuries, ejections, disturbances, hazards, lost children or property damage. | event memory |
| venueops.safety.medical_post | Event medical post | variant | Medical post provides visible first-response location and escalation path for guest health incidents. | care access |
| venueops.safety.weather_watch | Event weather watch | variant | Weather watch tracks lightning, wind, heat, rain or cold that may affect outdoor event safety. | sky changes plan |
| venueops.safety.evacuation_trigger | Evacuation trigger | invariant | Trigger defines conditions requiring partial or full evacuation and authority to initiate it. | decision before panic |
| venueops.safety.radio_channel_plan | Radio channel plan | invariant | Plan assigns channels for security, production, operations, medical, guest services and command. | avoid radio chaos |
| venueops.guest.lost_child_protocol | Lost child protocol | invariant | Protocol protects child, verifies guardian, controls information and records reunification. | sensitive incident |
| venueops.guest.lost_property | Event lost property | invariant | Lost property workflow records item, finder, location, storage, claim and disposal. | trust after event |
| venueops.guest.accessibility_service | Event accessibility service | invariant | Accessibility service supports entry, seating, toilets, viewing, communication and assistance routes. | inclusive event |
| venueops.guest.complaint_resolution | Event complaint resolution | variant | Resolution handles guest issue through listening, correction, relocation, refund path or escalation. | recover experience |
| venueops.guest.information_point | Guest information point | invariant | Info point answers wayfinding, schedules, policies, lost items and service questions. | reduce confusion |
| venueops.close.post_event_report | Post-event report | invariant | Report summarizes attendance, incidents, revenue notes, staffing, complaints, timings and lessons. | improve next event |
| venueops.close.damage_walkthrough | Damage walkthrough | invariant | Walkthrough records venue damage, missing assets, cleaning issues and chargeback evidence. | protect venue asset |
| venueops.close.staff_debrief | Staff debrief | variant | Debrief captures operational issues, safety concerns, guest feedback and improvement actions. | learn while fresh |
