# BATCH_200 — Funeral Home Operations Detail
# world_skills_core · source: world_skills_core:batch_200:funeral_home_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| funeralops.call.first_call | Funeral first call | invariant | First call records decedent identity, location, caller, next of kin, time and immediate needs. | start case carefully |
| funeralops.call.case_number | Funeral case number | invariant | Case number uniquely links authorizations, care, arrangements, permits, services and billing. | track respectfully |
| funeralops.call.next_of_kin | Next-of-kin verification | invariant | Verification identifies authorized person for decisions, releases and arrangements. | right authority |
| funeralops.call.removal_request | Removal request | invariant | Request coordinates transfer from place of death with identity, location, timing and staff. | first logistics |
| funeralops.call.after_hours_protocol | After-hours protocol | variant | Protocol covers calls, removals, staffing, facility access and urgent family support outside office hours. | service never fully sleeps |
| funeralops.transfer.transfer_chain | Decedent transfer chain | invariant | Chain records custody, identity checks, location, staff, vehicle and receiving time. | dignity and trace |
| funeralops.transfer.identity_tag | Decedent identity tag | invariant | Tag links decedent to case number and required identifiers throughout care. | prevent misidentification |
| funeralops.transfer.personal_effects | Personal effects inventory | invariant | Inventory records clothing, jewelry, documents or valuables received and released. | protect belongings |
| funeralops.transfer.vehicle_log | Funeral vehicle log | invariant | Log records trip, staff, mileage, cleaning, equipment and case. | transport accountability |
| funeralops.transfer.facility_intake | Care facility intake | invariant | Intake confirms identity, condition, authorizations, refrigeration or care pathway. | begin care workflow |
| funeralops.arrange.arrangement_meeting | Arrangement meeting | invariant | Meeting gathers family wishes, disposition choice, service details, products and documents. | plan ceremony and care |
| funeralops.arrange.disposition_authorization | Disposition authorization | invariant | Authorization permits burial, cremation, donation, shipment or other legal disposition. | legal permission |
| funeralops.arrange.service_type | Funeral service type | invariant | Type defines viewing, ceremony, graveside, memorial, direct disposition or private family service. | shape operations |
| funeralops.arrange.price_disclosure | Funeral price disclosure | invariant | Disclosure provides required itemized pricing and choices before selection. | transparent decisions |
| funeralops.arrange.prearrangement_file | Prearrangement file | variant | File stores prepaid or preplanned wishes, contracts, merchandise and contacts. | honor prior plans |
| funeralops.documents.death_certificate | Death certificate workflow | invariant | Workflow coordinates required data, certifier, filing, copies and corrections. | official record |
| funeralops.documents.permit_request | Burial or cremation permit | invariant | Permit authorizes disposition under local requirements. | cannot proceed without it |
| funeralops.documents.obituary_draft | Obituary draft | variant | Draft captures life details, survivors, service information, photo and publication approval. | public notice |
| funeralops.documents.veteran_benefits | Veteran benefit request | variant | Request coordinates flag, honors, cemetery, marker or benefit forms where eligible. | service entitlement |
| funeralops.documents.shipping_document | Human remains shipping document | variant | Document supports transport across regions with permits, container, carrier and receiving funeral home. | cross-border care |
| funeralops.care.refrigeration_log | Funeral refrigeration log | invariant | Log records location, time, condition and checks for decedent in controlled storage. | preservation control |
| funeralops.care.preparation_plan | Decedent preparation plan | invariant | Plan defines washing, dressing, cosmetics, casketing, restoration limits and family requests. | respectful readiness |
| funeralops.care.embalming_authorization | Embalming authorization | variant | Authorization documents permission, reason, disclosure and responsible professional where embalming is chosen. | regulated care |
| funeralops.care.clothing_inventory | Clothing inventory | invariant | Inventory records garments, shoes, jewelry and special items for viewing or burial. | avoid loss |
| funeralops.care.viewing_readiness | Viewing readiness check | invariant | Check confirms identity, presentation, room, casket, flowers, photos and family instructions. | dignified viewing |
| funeralops.merch.casket_selection | Casket selection | variant | Selection records model, size, color, price, availability and delivery timing. | product fit |
| funeralops.merch.urn_selection | Urn selection | variant | Selection records urn, keepsake, engraving, capacity, delivery and family approval. | memorial product |
| funeralops.merch.flower_order | Funeral flower order | variant | Order captures arrangement type, message, delivery time and placement. | ceremony detail |
| funeralops.merch.printed_materials | Printed memorial materials | variant | Materials include programs, prayer cards, register book, photos and service folders. | guest support |
| funeralops.merch.inventory_control | Funeral merchandise inventory | invariant | Control tracks stock, special orders, returns, damaged items and assignment to case. | avoid shortages |
| funeralops.service.service_schedule | Funeral service schedule | invariant | Schedule coordinates staff, venue, clergy, celebrant, music, transport, cemetery and family arrival. | event timeline |
| funeralops.service.room_setup | Funeral room setup | invariant | Setup arranges seating, casket or urn, flowers, photos, guest book, audio and accessibility. | respectful space |
| funeralops.service.procession_plan | Funeral procession plan | variant | Plan coordinates vehicles, route, timing, flags, lead car and cemetery arrival. | move together |
| funeralops.service.livestream | Funeral livestream | variant | Livestream setup checks camera, audio, privacy, link, recording and support. | remote attendance |
| funeralops.service.graveside_handoff | Graveside handoff | invariant | Handoff coordinates cemetery staff, committal service, lowering, flowers and family movement. | final stage |
| funeralops.crematory.cremation_chain | Cremation chain of custody | variant | Chain records identity, authorization, container, retort, time, processor and release. | irreversible process control |
| funeralops.crematory.cremated_remains_release | Cremated remains release | variant | Release verifies recipient, container, documentation, date and signature. | return correctly |
| funeralops.crematory.implant_check | Implant and device check | variant | Check identifies devices that may require special handling before cremation. | equipment and safety |
| funeralops.aftercare.aftercare_call | Funeral aftercare call | variant | Call offers grief resources, document reminders, feedback and unresolved-item follow-up. | support after service |
| funeralops.aftercare.document_packet | Family document packet | invariant | Packet includes certified copies, permits, receipts, service records and next-step information. | family administration |
| funeralops.admin.case_file_audit | Funeral case file audit | invariant | Audit checks authorizations, identity, permits, prices, care logs, service notes and releases. | compliance evidence |
| funeralops.admin.payment_record | Funeral payment record | invariant | Record tracks deposits, insurance assignment, balances, receipts and refunds. | financial clarity |
| funeralops.metrics.funeral_kpi | Funeral home KPI | variant | KPI tracks case volume, document errors, service timing, family feedback and aftercare completion. | manage sensitive service |
| funeralops.continuity.capacity_plan | Funeral home capacity plan | invariant | Plan covers surge deaths, refrigeration capacity, staffing, vehicles and mutual aid. | operate during crisis |
