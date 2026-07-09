# BATCH_238 — Food Bank Warehouse Operations Detail
# world_skills_core · source: world_skills_core:batch_238:food_bank_warehouse_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| foodbankops.donation.donor_offer | Food bank donor offer | invariant | Offer records donor, product, quantity, condition, pickup window and restrictions. | evaluate donation |
| foodbankops.donation.donation_acceptance | Food bank donation acceptance | invariant | Acceptance checks product safety, date, packaging, storage need and mission fit. | protect inventory |
| foodbankops.donation.receipt_record | Food bank donor receipt | invariant | Receipt documents donated goods, weight, date, donor and acknowledgment route. | donor accountability |
| foodbankops.donation.reject_reason | Food bank donation rejection | invariant | Rejection records unsafe, expired, damaged, unlabeled or unsuitable goods and communication. | avoid risk |
| foodbankops.donation.food_drive | Food bank food drive intake | variant | Intake manages event source, boxes, sorting load, volunteers and acknowledgment. | community supply |
| foodbankops.receiving.appointment_dock | Food bank receiving dock appointment | variant | Appointment schedules carrier, donor, dock, product type, labor and equipment. | smooth receiving |
| foodbankops.receiving.weight_capture | Food bank weight capture | invariant | Capture records pallet, case, bulk or mixed donation weight by category. | inventory measure |
| foodbankops.receiving.condition_check | Food bank receiving condition check | invariant | Check reviews temperature, pests, packaging, leakage, damage and contamination. | safe stock |
| foodbankops.receiving.lot_date | Food bank lot and date capture | invariant | Capture records lot, best-by, production date or traceability mark when present. | recall readiness |
| foodbankops.receiving.putaway_task | Food bank putaway task | invariant | Task assigns product to dry, cooler, freezer, quarantine or sorting area. | correct storage |
| foodbankops.sorting.sort_category | Food bank sorting category | invariant | Category separates grains, cans, produce, dairy, protein, hygiene, infant or special diet items. | usable inventory |
| foodbankops.sorting.quality_sort | Food bank quality sort | invariant | Sort removes dented, leaking, open, contaminated, unlabeled or unsafe items. | protect clients |
| foodbankops.sorting.repack_line | Food bank repack line | variant | Line converts bulk goods into household, agency or program packs with labels. | distribute usable units |
| foodbankops.sorting.volunteer_line | Food bank volunteer sorting line | variant | Line assigns roles, safety briefing, bins, pace, supervision and cleanup. | productive volunteers |
| foodbankops.sorting.allergen_separation | Food bank allergen separation | variant | Separation keeps allergens or special diet products identified and not misrepresented. | protect recipients |
| foodbankops.inventory.location_control | Food bank location control | invariant | Control tracks product by aisle, rack, bin, cooler, freezer or quarantine location. | find stock |
| foodbankops.inventory.fifo_rotation | Food bank FIFO rotation | invariant | Rotation moves older acceptable product forward and flags short-dated stock. | reduce waste |
| foodbankops.inventory.cycle_count | Food bank cycle count | invariant | Count verifies selected SKUs, lots, locations and variances against system. | inventory accuracy |
| foodbankops.inventory.quarantine_hold | Food bank quarantine hold | invariant | Hold isolates questionable product pending safety, recall, pest or quality decision. | prevent release |
| foodbankops.inventory.product_master | Food bank product master | invariant | Master records item name, category, storage type, pack size, allergens and handling notes. | consistent data |
| foodbankops.agency.agency_order | Food bank agency order | invariant | Order records partner agency, items, quantities, pickup time, limits and substitutions. | fulfill demand |
| foodbankops.agency.allocation_rule | Food bank allocation rule | variant | Rule distributes scarce goods by agency size, program need, fairness or priority. | equitable supply |
| foodbankops.agency.pick_ticket | Food bank pick ticket | invariant | Ticket lists locations, items, quantities, lot constraints and staging lane. | guide picking |
| foodbankops.agency.substitution_note | Food bank substitution note | variant | Note records unavailable item, approved substitute, quantity change and agency notice. | manage shortages |
| foodbankops.agency.agency_compliance | Partner agency compliance record | invariant | Record tracks agreements, food safety training, monitoring, reports and corrective actions. | protect network |
| foodbankops.cold.cold_receiving | Food bank cold receiving | invariant | Receiving verifies temperature, time, product condition, storage route and exception. | cold safety |
| foodbankops.cold.cooler_log | Food bank cooler log | invariant | Log records cooler temperature, alarm, corrective action and product impact. | maintain chain |
| foodbankops.cold.freezer_log | Food bank freezer log | invariant | Log records freezer status, defrost issues, door checks and temperature trends. | protect frozen food |
| foodbankops.cold.produce_sort | Food bank produce sort | variant | Sort separates usable, immediate-use, compost, animal feed or discard produce. | reduce waste |
| foodbankops.cold.refrigerated_staging | Refrigerated staging | variant | Staging holds picked cold orders by agency, time, route and temperature control. | safe dispatch |
| foodbankops.distribution.pick_wave | Food bank pick wave | invariant | Wave groups orders by route, agency, product zone or pickup window. | efficient picking |
| foodbankops.distribution.loading_check | Food bank loading check | invariant | Check verifies agency, order, pallet count, cold items, paperwork and seal if used. | correct shipment |
| foodbankops.distribution.route_dispatch | Food bank route dispatch | variant | Dispatch assigns driver, truck, route, stops, temperature checks and proof of delivery. | outbound control |
| foodbankops.distribution.mobile_pantry | Food bank mobile pantry loadout | variant | Loadout prepares product mix, tables, signage, volunteers, cold control and records. | community distribution |
| foodbankops.distribution.proof_delivery | Food bank proof of delivery | invariant | Proof records recipient, time, items, quantity, condition and exceptions. | close order |
| foodbankops.recall.recall_notice | Food bank recall notice | invariant | Notice identifies affected product, lots, locations, agencies and hold instructions. | stop distribution |
| foodbankops.recall.trace_query | Food bank trace query | invariant | Query finds received, stored, shipped or discarded quantities for affected product. | recall scope |
| foodbankops.recall.agency_notification | Food bank agency notification | invariant | Notification tells partners what to hold, return, destroy or report. | network safety |
| foodbankops.recall.disposition_record | Food bank recall disposition | invariant | Record documents product returned, destroyed, released or unaccounted with approval. | audit trail |
| foodbankops.safety.forklift_check | Food bank forklift check | invariant | Check verifies battery, forks, tires, horn, brakes, leaks and operator readiness. | warehouse safety |
| foodbankops.safety.pest_log | Food bank pest log | invariant | Log tracks evidence, traps, contractor findings, sanitation actions and affected stock. | food protection |
| foodbankops.safety.volunteer_safety | Food bank volunteer safety briefing | invariant | Briefing covers lifting, blades, allergens, forklift zones, PPE and reporting. | reduce injury |
| foodbankops.reporting.inventory_report | Food bank inventory report | invariant | Report summarizes on-hand, short-dated, quarantined, received, shipped and waste. | operational visibility |
| foodbankops.metrics.foodbank_kpi | Food bank warehouse KPI | variant | KPI tracks pounds received, pounds distributed, waste, order fill, cold exceptions and volunteer hours. | manage warehouse |
