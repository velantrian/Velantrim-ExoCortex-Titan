# BATCH_194 — Restaurant Front-of-House Operations Detail
# world_skills_core · source: world_skills_core:batch_194:restaurant_front_of_house_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| foh.reservation.booking | Restaurant reservation | invariant | Booking records guest name, party size, time, contact, notes and seating preference. | plan demand |
| foh.reservation.deposit | Reservation deposit | variant | Deposit secures high-demand, large-party or special-event booking under policy. | reduce no-shows |
| foh.reservation.waitlist | Restaurant waitlist | invariant | Waitlist tracks party size, quoted time, contact, priority and seated status. | manage walk-ins |
| foh.reservation.table_hold | Table hold rule | variant | Rule defines how long late reservation is kept before release. | protect seating flow |
| foh.reservation.special_request | Guest special request | variant | Request notes occasion, accessibility, allergy alert, seating preference or service detail. | personalize service |
| foh.host.floor_plan | Dining room floor plan | invariant | Plan maps tables, sections, capacity, station assignments and blocked seats. | seat intelligently |
| foh.host.seating_rotation | Seating rotation | invariant | Rotation balances server workload, table availability and guest needs. | fair service load |
| foh.host.quote_time | Wait quote time | invariant | Quote estimates seating delay from table turns, parties ahead and room capacity. | set expectations |
| foh.host.table_status | Table status | invariant | Status marks dirty, clean, seated, ordered, entree, dessert, paid or reserved. | dining room visibility |
| foh.host.guest_greeting | Guest greeting | invariant | Greeting confirms party, reservation, needs and first impression. | hospitality starts here |
| foh.service.server_section | Server section | invariant | Section assigns tables, guests and responsibility to a server or team. | accountability |
| foh.service.steps_of_service | Steps of service | invariant | Steps sequence greet, drinks, order, checkback, clearing, dessert, payment and farewell. | consistent experience |
| foh.service.menu_knowledge | Menu knowledge | invariant | Staff know ingredients, preparation, allergens, pairings, availability and substitutions. | answer accurately |
| foh.service.allergy_alert | Allergy alert workflow | invariant | Workflow communicates guest allergy to server, kitchen, POS and manager as required. | high-risk service |
| foh.service.table_touch | Manager table touch | variant | Touch checks guest satisfaction, delays, special occasions or recovery needs. | catch problems early |
| foh.order.pos_order | POS order entry | invariant | Entry sends items, modifiers, seat numbers, coursing and timing to kitchen or bar. | translate request |
| foh.order.modifier_control | Order modifier control | invariant | Control captures substitutions, doneness, sides, removals and allergy flags clearly. | avoid wrong food |
| foh.order.course_fire | Course fire | variant | Fire tells kitchen when to prepare next course based on pacing. | timing coordination |
| foh.order.void_comp | Void and comp control | invariant | Control records reason, approval and financial impact for removed or discounted items. | prevent leakage |
| foh.order.86_item | Eighty-six item | variant | 86 communicates unavailable menu item to staff and POS. | stop selling out item |
| foh.bar.drink_ticket | Drink ticket | invariant | Ticket communicates beverage order, modifiers, seat, timing and responsible server. | bar workflow |
| foh.bar.id_check | Alcohol ID check | invariant | Check verifies guest age and refusal conditions under local rules. | legal service |
| foh.bar.cutoff | Alcohol service cutoff | invariant | Cutoff stops service when guest condition or policy requires refusal. | responsible service |
| foh.bar.tab_management | Bar tab management | variant | Tab links drinks, guest, payment method and closing process. | avoid unpaid tabs |
| foh.bar.beer_wine_pairing | Beverage pairing suggestion | variant | Suggestion matches drink to food, budget and guest preference. | service value |
| foh.flow.ticket_time | Ticket time | invariant | Time measures order entry to delivery and signals kitchen or service delay. | pace control |
| foh.flow.runner_handoff | Food runner handoff | invariant | Handoff delivers correct plates by table, seat, allergy and temperature. | finish kitchen work |
| foh.flow.busser_turn | Table turn | invariant | Turn clears, cleans, resets and releases table for next seating. | capacity recovery |
| foh.flow.delay_notice | Guest delay notice | invariant | Notice explains delay, expected timing and recovery action. | reduce uncertainty |
| foh.flow.large_party_coordination | Large party coordination | variant | Coordination manages preorders, seating, pacing, checks, gratuity and service team. | complex table |
| foh.payment.check_split | Check split | variant | Split divides bill by seat, item, equal share or payment method. | guest convenience |
| foh.payment.cashout | Server cashout | invariant | Cashout reconciles sales, cash, tips, comps, voids and credit slips. | end-shift control |
| foh.payment.tip_pool | Tip pool record | variant | Record allocates tips according to role, hours, sales or policy. | fair distribution |
| foh.payment.gift_card | Gift card redemption | variant | Redemption applies stored value and records remaining balance. | noncash payment |
| foh.payment.chargeback | Restaurant chargeback | variant | Chargeback case gathers receipt, authorization, signature and service evidence. | dispute response |
| foh.recovery.complaint_log | Guest complaint log | invariant | Log records issue, table, staff, food, action, comp and follow-up. | learn from failures |
| foh.recovery.remake_request | Remake request | invariant | Request sends incorrect, cold or unacceptable item back through kitchen workflow. | fix meal |
| foh.recovery.guest_incident | Guest incident record | invariant | Record documents injury, illness claim, conflict, property loss or disruptive behavior. | risk record |
| foh.recovery.manager_escalation | Manager escalation | invariant | Escalation brings authority for safety, refund, refusal, allergy or severe dissatisfaction. | right level response |
| foh.recovery.review_response | Public review response | variant | Response acknowledges issue, avoids private data and routes resolution where appropriate. | reputation care |
| foh.close.sidework | FOH sidework | invariant | Sidework covers cleaning, restocking, polishing, menus, stations and closing tasks. | service readiness |
| foh.close.cash_drawer | Restaurant cash drawer | invariant | Drawer is counted, reconciled, secured and handed off with variance note. | money control |
| foh.close.shift_log | Front-of-house shift log | invariant | Log summarizes covers, sales, incidents, staffing, shortages and guest issues. | handover memory |
| foh.metrics.foh_kpi | Front-of-house KPI | variant | KPI tracks covers, average check, table turn, wait time, comps, reviews and labor. | manage experience |
