# BATCH_217 — Coworking Space Operations Detail
# world_skills_core · source: world_skills_core:batch_217:coworking_space_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| cowork.member.member_onboarding | Coworking member onboarding | invariant | Onboarding sets plan, identity, access, billing, rules, amenities and communication channels. | start membership |
| cowork.member.plan_type | Coworking plan type | invariant | Plan defines hot desk, dedicated desk, office, virtual office, day pass or meeting-room bundle. | service entitlement |
| cowork.member.member_profile | Member profile | invariant | Profile stores contacts, company, billing, access level, emergency contact and preferences. | account anchor |
| cowork.member.house_rules_ack | House rules acknowledgment | invariant | Acknowledgment records acceptance of noise, guests, security, meeting room and conduct rules. | shared space norms |
| cowork.member.offboarding | Coworking member offboarding | invariant | Offboarding removes access, closes billing, collects keys and handles mail or deposits. | clean exit |
| cowork.access.access_credential | Coworking access credential | invariant | Credential grants door, floor, room or after-hours access according to membership. | controlled entry |
| cowork.access.guest_registration | Coworking guest registration | invariant | Registration records visitor, host, time, purpose, access limit and badge if used. | visitor control |
| cowork.access.after_hours_access | After-hours coworking access | variant | Access applies extra rules for security, HVAC, support and incident response. | quiet-hours control |
| cowork.access.lost_credential | Lost credential process | invariant | Process disables credential, issues replacement and records risk. | prevent misuse |
| cowork.access.door_event_review | Door event review | variant | Review checks access logs for incident, lockout, tailgating or unauthorized entry. | security evidence |
| cowork.rooms.room_booking | Meeting room booking | invariant | Booking reserves room, time, host, attendees, equipment and billing rule. | manage shared rooms |
| cowork.rooms.room_setup | Meeting room setup | invariant | Setup prepares layout, screen, video, whiteboard, supplies, catering or signage. | ready meeting |
| cowork.rooms.no_show_release | Room no-show release | variant | Release returns unused room to inventory after grace period. | reduce waste |
| cowork.rooms.overrun_handling | Meeting overrun handling | invariant | Handling extends, bills, relocates or clears room when booking exceeds time. | protect next booking |
| cowork.rooms.room_turnover | Meeting room turnover | invariant | Turnover cleans surfaces, resets furniture, removes trash and checks equipment. | next user ready |
| cowork.amenity.mail_handling | Coworking mail handling | variant | Handling receives, sorts, notifies, stores and releases mail for authorized members. | virtual office support |
| cowork.amenity.print_service | Coworking print service | variant | Service controls printer access, quotas, faults, supplies and confidential output. | shared office tool |
| cowork.amenity.coffee_station | Coworking coffee station | invariant | Station needs stocking, cleaning, machine checks, spills and supply ordering. | daily amenity |
| cowork.amenity.phone_booth | Phone booth management | variant | Management controls availability, time limits, cleaning, ventilation and acoustic use. | private calls |
| cowork.amenity.internet_support | Coworking internet support | invariant | Support handles Wi-Fi access, outages, VLAN rules, guest network and escalation. | core utility |
| cowork.community.event_calendar | Coworking event calendar | variant | Calendar schedules workshops, networking, member demos, socials and partner events. | community engine |
| cowork.community.event_registration | Coworking event registration | variant | Registration captures attendee, capacity, payment, dietary needs and check-in. | event control |
| cowork.community.member_intro | Member introduction | variant | Intro connects members by consent, interest, industry or collaboration need. | build network |
| cowork.community.notice_board | Coworking notice board | variant | Board shares announcements, events, policies, openings and member offers. | shared awareness |
| cowork.community.conduct_issue | Member conduct issue | invariant | Issue records noise, harassment, cleanliness, security, guest or rule violation. | protect community |
| cowork.billing.membership_invoice | Coworking membership invoice | invariant | Invoice charges plan, desks, rooms, services, deposits, discounts and taxes. | bill services |
| cowork.billing.proration | Coworking proration | variant | Proration adjusts partial month, upgrade, downgrade, move-in or move-out charges. | fair billing |
| cowork.billing.failed_payment | Coworking failed payment | invariant | Failure triggers notice, retry, access review and account follow-up. | revenue control |
| cowork.billing.deposit_return | Coworking deposit return | variant | Return checks damages, keys, unpaid balance and lease terms before refund. | close money |
| cowork.billing.room_overage | Meeting room overage | variant | Overage bills excess time, guests, equipment or service beyond plan allowance. | entitlement control |
| cowork.facility.opening_round | Coworking opening round | invariant | Round checks doors, lights, HVAC, coffee, rooms, cleanliness, mail and tickets. | start day |
| cowork.facility.closing_round | Coworking closing round | invariant | Round secures rooms, trash, doors, equipment, lights, guests and incident notes. | end day |
| cowork.facility.cleaning_ticket | Coworking cleaning ticket | invariant | Ticket records spill, restroom issue, trash, meeting room mess or special cleaning. | keep space usable |
| cowork.facility.maintenance_ticket | Coworking maintenance ticket | invariant | Ticket captures furniture, HVAC, plumbing, electrical, network, access or appliance issue. | fix shared space |
| cowork.facility.capacity_monitor | Coworking capacity monitor | variant | Monitor tracks desks, rooms, occupancy, guest load and crowding patterns. | space planning |
| cowork.security.package_release | Package release control | variant | Control verifies member authorization before releasing packages or deliveries. | avoid loss |
| cowork.security.incident_report | Coworking incident report | invariant | Report documents theft, injury, conflict, unauthorized access, damage or safety concern. | formal record |
| cowork.security.emergency_contact | Coworking emergency contact | invariant | Contact list supports fire, medical, building, police, landlord and member escalation. | rapid response |
| cowork.security.camera_policy | Coworking camera policy | variant | Policy defines where cameras operate, review authorization and privacy boundaries. | trust and evidence |
| cowork.security.fire_drill | Coworking fire drill | invariant | Drill tests evacuation routes, alarms, assembly area and staff roles. | safety readiness |
| cowork.admin.staff_shift | Coworking staff shift | invariant | Shift assigns front desk, community, facility, events and support responsibilities. | coverage |
| cowork.admin.vendor_coordination | Coworking vendor coordination | invariant | Coordination manages cleaners, maintenance, IT, coffee, security and event suppliers. | external work |
| cowork.metrics.coworking_kpi | Coworking KPI | variant | KPI tracks occupancy, churn, room utilization, incidents, tickets, event attendance and revenue. | manage space |
| cowork.continuity.access_system_outage | Access system outage | invariant | Outage process handles manual entry, member notice, security patrol and credential recovery. | keep space usable |
