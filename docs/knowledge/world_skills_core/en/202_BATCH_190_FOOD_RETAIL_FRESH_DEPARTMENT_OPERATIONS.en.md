# BATCH_190 — Food Retail Fresh Department Operations Detail
# world_skills_core · source: world_skills_core:batch_190:food_retail_fresh_department_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| freshretail.receiving.delivery_window | Fresh delivery window | invariant | Window controls arrival time for produce, meat, dairy, bakery or prepared foods. | freshness starts at door |
| freshretail.receiving.temperature_check | Receiving temperature check | invariant | Check records product temperature for chilled, frozen or hot-held items at receipt. | cold chain gate |
| freshretail.receiving.vendor_quality | Vendor quality check | invariant | Check reviews count, condition, date code, packaging, odor, damage and specification. | reject bad stock early |
| freshretail.receiving.lot_trace | Fresh lot trace | invariant | Trace links case, supplier, lot, date and department for recall and rotation. | know origin |
| freshretail.receiving.reject_credit | Fresh receiving rejection | invariant | Rejection records product, reason, quantity, vendor and credit or replacement action. | protect margin |
| freshretail.storage.coldroom_zone | Coldroom zone | invariant | Zone separates products by temperature, category, allergen, odor, raw/cooked and contamination risk. | storage discipline |
| freshretail.storage.date_code | Fresh date code | invariant | Date code controls sale-by, use-by, pack, thaw or prep timing. | rotate correctly |
| freshretail.storage.fifo_fefo | FIFO and FEFO rotation | invariant | Rotation uses first-in-first-out or first-expire-first-out based on category. | reduce waste |
| freshretail.storage.covering_label | Covering and labeling | invariant | Covered labeled product shows identity, date, owner and status. | prevent mystery food |
| freshretail.storage.thaw_control | Controlled thawing | variant | Thawing keeps product under safe temperature and time conditions before sale or prep. | avoid unsafe thaw |
| freshretail.display.case_temperature | Display case temperature | invariant | Case temperature maintains safe and quality range during merchandising. | shelf cold chain |
| freshretail.display.case_load_limit | Display case load limit | invariant | Load limit prevents blocking airflow and overfilling refrigerated display. | cold air must move |
| freshretail.display.planogram | Fresh department planogram | variant | Planogram sets product placement, facings, flow, adjacency and promotional space. | sell and replenish |
| freshretail.display.misting_control | Produce misting control | variant | Misting supports produce appearance but can create spoilage or slip risk if misused. | water with judgment |
| freshretail.display.hot_hold | Hot-hold display | variant | Hot-hold display keeps prepared foods above required holding condition and time limit. | ready-to-eat safety |
| freshretail.prep.prep_schedule | Fresh prep schedule | invariant | Schedule plans cutting, grinding, slicing, baking or packaging based on demand and shelf life. | make at right time |
| freshretail.prep.sanitary_setup | Fresh prep sanitary setup | invariant | Setup verifies clean surfaces, tools, PPE, handwash and separation before food handling. | safe start |
| freshretail.prep.recipe_yield | Fresh recipe yield | variant | Yield compares expected output to input weight and waste. | margin control |
| freshretail.prep.allergen_control | Fresh allergen control | invariant | Control prevents undeclared allergen contact through separation, labeling, cleaning and recipe discipline. | protect customers |
| freshretail.prep.knife_safety | Fresh knife safety | invariant | Safety covers sharp tools, cut gloves, storage, handling and focused cutting. | common injury risk |
| freshretail.pack.scale_label | Scale label | invariant | Label prints price, weight, item, date, barcode and required consumer information. | sell accurately |
| freshretail.pack.tare_control | Tare control | invariant | Tare subtracts package weight so customer pays for product only. | fair pricing |
| freshretail.pack.modified_atmosphere | Modified atmosphere packaging | variant | Packaging changes gas environment to preserve product where process is validated. | extend shelf life |
| freshretail.pack.leak_check | Package leak check | invariant | Check identifies broken seals, dripping, torn wrap or swollen packs. | quality and safety |
| freshretail.pack.country_origin | Country of origin label | variant | Label communicates origin where category and jurisdiction require it. | compliance display |
| freshretail.floor.replenishment | Fresh replenishment | invariant | Replenishment fills display from backroom while checking date, quality and temperature. | shelf never blind |
| freshretail.floor.culling | Fresh culling | invariant | Culling removes spoiled, damaged, expired, wilted or unsafe items from sale. | protect customer trust |
| freshretail.floor.markdown | Fresh markdown | variant | Markdown reduces price for short-dated or cosmetically imperfect product within policy. | recover value |
| freshretail.floor.customer_request | Fresh customer request | invariant | Request may require slicing, custom cut, advice, substitution or special order. | service interaction |
| freshretail.floor.cross_merchandising | Cross-merchandising | variant | Display pairs related fresh items with sauces, bakery, herbs or meal components. | increase basket |
| freshretail.shrink.shrink_log | Fresh shrink log | invariant | Log records discarded, donated, marked-down, damaged or expired quantity and reason. | margin visibility |
| freshretail.shrink.spoilage_trend | Spoilage trend | variant | Trend identifies over-ordering, temperature issues, weak rotation or supplier quality problems. | attack root cause |
| freshretail.shrink.production_planning | Fresh production planning | invariant | Planning uses sales, weather, events, season and shelf life to set prep quantity. | make enough, not too much |
| freshretail.shrink.donation_route | Fresh donation route | variant | Route sends safe unsold food to approved donation partner under policy. | reduce waste |
| freshretail.shrink.inventory_count | Fresh inventory count | invariant | Count measures on-hand product, backroom, display and work-in-process. | order accurately |
| freshretail.safety.handwash_compliance | Fresh handwash compliance | invariant | Compliance ensures staff wash hands at required transitions and contamination events. | behavior control |
| freshretail.safety.cleaning_schedule | Fresh cleaning schedule | invariant | Schedule covers counters, slicers, grinders, cases, drains, floors, tools and bins. | sanitation rhythm |
| freshretail.safety.slicer_control | Deli slicer control | invariant | Control includes guard use, cleaning, lockout, blade handling and assigned trained users. | severe injury risk |
| freshretail.safety.foreign_material | Fresh foreign material control | invariant | Control prevents glass, plastic, metal, wood or packaging fragments entering food. | protect product |
| freshretail.safety.recall_pull | Fresh recall pull | invariant | Pull removes affected lots from shelf, backroom and prep areas and records disposition. | fast risk removal |
| freshretail.people.department_open | Fresh department opening | invariant | Opening checks temperatures, displays, cleanliness, dates, production plan and staffing. | day starts controlled |
| freshretail.people.department_close | Fresh department close | invariant | Close secures product, cleans equipment, records shrink, checks cases and prepares next day. | reset department |
| freshretail.people.skill_matrix | Fresh department skill matrix | variant | Matrix tracks who can cut, slice, bake, receive, close, order or train. | staff capability |
| freshretail.metrics.fresh_kpi | Fresh department KPI | variant | KPI tracks sales, margin, shrink, availability, temperature compliance, labor and complaints. | manage fresh tradeoffs |
