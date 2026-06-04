# BATCH_229 — Theater Box Office & Usher Operations Detail
# world_skills_core · source: world_skills_core:batch_229:theater_box_office_usher_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| theaterops.ticket.event_setup | Theater event setup | invariant | Setup defines show, date, venue, seating map, prices, holds, fees and sale windows. | open sales |
| theaterops.ticket.seat_inventory | Theater seat inventory | invariant | Inventory tracks available, sold, held, comp, accessible, blocked and broken seats. | know capacity |
| theaterops.ticket.price_scale | Ticket price scale | variant | Scale assigns price by section, performance, discount, demand or package. | revenue control |
| theaterops.ticket.discount_code | Theater discount code | variant | Code applies student, senior, member, promo, group or comp rule. | controlled discount |
| theaterops.ticket.ticket_fee | Ticket fee | invariant | Fee covers service, facility, delivery, exchange or processing charges. | transparent price |
| theaterops.sales.box_office_sale | Box office sale | invariant | Sale records seat, price, payment, customer, delivery method and receipt. | direct transaction |
| theaterops.sales.online_order | Theater online order | variant | Order links customer, tickets, payment, delivery, confirmation and fraud checks. | digital sales |
| theaterops.sales.group_sale | Theater group sale | variant | Sale handles blocks, deposits, deadlines, seating, final count and group contact. | group workflow |
| theaterops.sales.complimentary_ticket | Complimentary ticket | variant | Comp ticket requires reason, approver, recipient and inventory record. | free seat control |
| theaterops.sales.exchange_request | Ticket exchange request | invariant | Request changes performance, seat, price or patron under policy. | flexible service |
| theaterops.willcall.will_call | Will-call pickup | invariant | Pickup verifies patron identity, order, tickets, payment balance and pickup note. | front desk handoff |
| theaterops.willcall.print_at_home | Print-at-home ticket | variant | Ticket uses barcode, seat, event and validation rules for entry. | remote delivery |
| theaterops.willcall.mobile_ticket | Mobile ticket | variant | Ticket displays barcode or wallet pass for scanning and validation. | phone entry |
| theaterops.willcall.reprint | Ticket reprint | invariant | Reprint voids or marks prior ticket and records reason to prevent duplicate entry. | fraud control |
| theaterops.willcall.lost_ticket | Lost ticket process | invariant | Process verifies customer, order, seat and ID before replacement. | protect seat |
| theaterops.entry.ticket_scan | Ticket scan | invariant | Scan validates event, date, barcode, seat and entry status. | door control |
| theaterops.entry.bag_policy | Theater bag policy | variant | Policy limits bag size, prohibited items, inspection or storage. | safety and speed |
| theaterops.entry.late_seating | Late seating policy | invariant | Policy defines when late patrons may enter without disrupting show. | protect performance |
| theaterops.entry.accessible_entry | Accessible entry | invariant | Entry supports wheelchair, mobility, hearing, vision or companion needs. | inclusive access |
| theaterops.entry.reentry_rule | Theater reentry rule | variant | Rule controls whether scanned patrons may leave and return. | access integrity |
| theaterops.usher.pre_show_brief | Usher pre-show briefing | invariant | Briefing covers seating, late policy, emergency exits, accessibility, VIPs and show notes. | align team |
| theaterops.usher.program_distribution | Program distribution | variant | Distribution gives programs or inserts while monitoring inventory and entrances. | guest information |
| theaterops.usher.seat_assistance | Seat assistance | invariant | Assistance helps patron find row, seat, section and accessible path. | smooth seating |
| theaterops.usher.seat_dispute | Seat dispute | invariant | Dispute resolves duplicate seat, wrong performance, blocked seat or customer conflict. | protect experience |
| theaterops.usher.house_count | House count | invariant | Count tracks scanned patrons, no-shows, comps and attendance. | show record |
| theaterops.show.house_open | House open | invariant | Opening confirms ushers, doors, auditorium, stage clearance, temperature and front-of-house readiness. | admit audience |
| theaterops.show.curtain_hold | Curtain hold | variant | Hold delays start for access, safety, ticketing, weather or production reason. | coordinated delay |
| theaterops.show.intermission_flow | Intermission flow | invariant | Flow manages restrooms, concessions, reentry, seating and timing. | crowd pulse |
| theaterops.show.house_close | House close | invariant | Close clears patrons, checks lost items, damage, spills, programs and incident notes. | reset venue |
| theaterops.show.no_late_entry | No-late-entry show | variant | Rule holds late patrons until interval or denies entry for certain performances. | artistic requirement |
| theaterops.guest.accessibility_request | Accessibility request | invariant | Request records seating, device, interpreter, audio description, captioning or companion need. | plan support |
| theaterops.guest.patron_complaint | Patron complaint | invariant | Complaint records seating, sound, view, staff, refund, safety or behavior issue. | service recovery |
| theaterops.guest.disruptive_patron | Disruptive patron response | invariant | Response de-escalates noise, filming, intoxication, harassment or unsafe conduct. | protect audience |
| theaterops.guest.medical_incident | Theater medical incident | invariant | Incident records location, response, EMS, staff, witnesses and follow-up. | emergency record |
| theaterops.guest.lost_found | Theater lost and found | invariant | Process tags, stores, claims and disposes found items after show. | return property |
| theaterops.refund.refund_policy | Theater refund policy | invariant | Policy defines eligibility, cancellation, exchange, weather, illness or event change handling. | consistent decisions |
| theaterops.refund.cancelled_show | Cancelled show workflow | invariant | Workflow notifies patrons, processes refunds or exchanges and updates inventory. | disruption response |
| theaterops.refund.chargeback_case | Theater chargeback case | variant | Case gathers order, scan, policy, communication and receipt evidence. | payment dispute |
| theaterops.cash.box_office_close | Box office close | invariant | Close reconciles cash, cards, comps, exchanges, refunds, batches and deposit. | financial control |
| theaterops.cash.cash_drawer | Theater cash drawer | invariant | Drawer tracks starting bank, sales, payouts, variance and secure handoff. | cash accountability |
| theaterops.safety.emergency_evac | Theater evacuation support | invariant | Support guides exits, accessible patrons, assembly, crowd communication and incident log. | emergency readiness |
| theaterops.safety.fire_watch | Theater fire watch | variant | Watch applies when alarm, pyrotechnics, impairment or venue rule requires monitoring. | temporary protection |
| theaterops.metrics.theater_kpi | Theater FOH KPI | variant | KPI tracks attendance, ticket yield, scan rate, complaints, refunds, late seating and incidents. | manage front-of-house |
| theaterops.continuity.ticketing_outage | Ticketing system outage | invariant | Outage process uses manual lists, offline scanning, receipts and later reconciliation. | keep doors moving |
