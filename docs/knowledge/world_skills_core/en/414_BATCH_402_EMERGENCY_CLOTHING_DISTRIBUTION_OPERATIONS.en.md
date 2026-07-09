# BATCH 402: Emergency Clothing Distribution Operations

**KnowledgeUnits:** 44  
**Namespace:** `clothingdistops.*`  
**Scope:** intake, sizing, inventory, dignity, laundering, pickup, delivery and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| clothingdistops.activation.trigger | distribution trigger | MODEL | Trigger includes displacement, fire, flood, evacuation, sheltering or loss of personal belongings. | Starts clothing support. |
| clothingdistops.activation.partner | partner roster | RECORD | Roster lists donation centers, shelters, nonprofits, retailers, laundry and transport partners. | Coordinates help. |
| clothingdistops.activation.service_model | service model | RECORD | Model distinguishes closet, voucher, mobile delivery, shelter table or appointment pickup. | Defines operation. |
| clothingdistops.activation.command_link | command link | RECORD | Operation reports to donations, sheltering, logistics and public information leads. | Keeps oversight. |
| clothingdistops.intake.household | household intake | RECORD | Intake captures household members, sizes, urgent needs, language and pickup/delivery constraints. | Defines demand. |
| clothingdistops.intake.item_need | item need | RECORD | Need lists shirts, pants, underwear, socks, coats, shoes, baby items or work clothing. | Guides selection. |
| clothingdistops.intake.priority | priority level | MODEL | Priority weighs no clothing, weather exposure, children, medical needs and work/school deadlines. | Orders service. |
| clothingdistops.intake.privacy | privacy rule | SAFETY_RULE | Clothing needs and sizes are handled discreetly with minimal personal data. | Preserves dignity. |
| clothingdistops.sizing.size_profile | size profile | RECORD | Profile records size range, shoe size, gender preference, child age and fit notes. | Improves match. |
| clothingdistops.sizing.substitution | substitution rule | METHOD | Substitution uses acceptable alternatives when exact size or style is unavailable. | Keeps service moving. |
| clothingdistops.sizing.tryon_policy | try-on policy | CONSTRAINT | Try-on rules define hygiene, privacy, returns and fitting space. | Prevents discomfort. |
| clothingdistops.sizing.special_need | special need | RECORD | Special need covers adaptive clothing, maternity, uniforms, steel-toe shoes or sensory concerns. | Supports real use. |
| clothingdistops.inventory.item_master | item master | RECORD | Item master classifies garment type, size, condition, season, gender-neutral use and restrictions. | Standardizes stock. |
| clothingdistops.inventory.receiving | receiving check | QUALITY_CHECK | Receiving checks cleanliness, damage, appropriateness, size labels and bag condition. | Protects quality. |
| clothingdistops.inventory.sorting | sorting method | METHOD | Sorting groups items by type, size, season, condition and priority category. | Speeds selection. |
| clothingdistops.inventory.stock_count | stock count | MEASUREMENT | Count tracks units received, issued, discarded, laundered and remaining. | Shows availability. |
| clothingdistops.donations.acceptance | acceptance criteria | CONSTRAINT | Criteria reject dirty, damaged, unsafe or unsuitable clothing. | Reduces burden. |
| clothingdistops.donations.unsolicited | unsolicited goods | METHOD | Unsolicited clothing is routed to sorting, storage, partner transfer or disposal. | Controls overflow. |
| clothingdistops.donations.retail_donation | retail donation | RECORD | Retail donation records donor, new items, sizes, restrictions and receipt needs. | Maintains accountability. |
| clothingdistops.donations.shortage_request | shortage request | METHOD | Requests target specific sizes, coats, shoes, underwear, socks or baby items. | Fills gaps. |
| clothingdistops.hygiene.laundering | laundering pathway | METHOD | Used clothing needing cleaning is routed to laundry before issue. | Protects recipients. |
| clothingdistops.hygiene.contamination | contamination rule | SAFETY_RULE | Smoke, mold, floodwater, pest or chemical contamination requires rejection or specialized handling. | Prevents harm. |
| clothingdistops.hygiene.new_underwear | new underwear rule | SAFETY_RULE | Underwear and socks are issued new where policy requires. | Maintains hygiene. |
| clothingdistops.hygiene.storage_clean | clean storage | SAFETY_RULE | Clean clothing is stored dry, pest-free and separated from rejected goods. | Preserves quality. |
| clothingdistops.issue.pick_list | pick list | RECORD | Pick list converts household needs into items, sizes, quantities and substitutions. | Guides staff. |
| clothingdistops.issue.dignity_choice | dignity choice | METHOD | Residents can choose among available options where feasible. | Preserves autonomy. |
| clothingdistops.issue.issue_limit | issue limit | CONSTRAINT | Limits define quantity per person, category or time period. | Extends supply. |
| clothingdistops.issue.receipt | issue receipt | RECORD | Receipt records household, items, sizes, quantities, date and staff. | Supports inventory. |
| clothingdistops.pickup.appointment | pickup appointment | RECORD | Appointment records time, location, household, prepared package and access needs. | Organizes handoff. |
| clothingdistops.pickup.queue | pickup queue | METHOD | Queue handles walk-ins, appointments, urgent cases and privacy-sensitive requests. | Manages demand. |
| clothingdistops.pickup.return_exchange | exchange policy | CONSTRAINT | Exchange rules define wrong size, unsuitable item, hygiene and inventory update process. | Improves fit. |
| clothingdistops.pickup.site_setup | site setup | METHOD | Setup provides sorting tables, private area, signage, staff flow and security. | Improves service. |
| clothingdistops.delivery.delivery_request | delivery request | RECORD | Request captures address, sizes, access, contact window and mobility barriers. | Enables outreach. |
| clothingdistops.delivery.route_plan | route plan | METHOD | Route groups deliveries by area, urgency and package readiness. | Saves time. |
| clothingdistops.delivery.no_contact | no-contact policy | METHOD | Policy defines doorstep leave, retry, hold or return based on safety and privacy. | Controls loss. |
| clothingdistops.delivery.confirmation | delivery confirmation | RECORD | Confirmation records recipient, time, items delivered and unresolved needs. | Closes handoff. |
| clothingdistops.communication.public_notice | public notice | METHOD | Notice states available items, hours, eligibility, donation rules and shortage needs. | Guides community. |
| clothingdistops.communication.partner_update | partner update | METHOD | Partners receive inventory gaps, demand, service hours and referral instructions. | Aligns support. |
| clothingdistops.communication.language | language access | METHOD | Signs and scripts use common local languages and simple size terms. | Improves access. |
| clothingdistops.communication.weather_alert | weather alert | METHOD | Alerts emphasize coats, rain gear, heat clothing or footwear during weather risk. | Prioritizes safety. |
| clothingdistops.metrics.households_served | households served | MEASUREMENT | Metric counts households and people served by item category and site. | Shows reach. |
| clothingdistops.metrics.size_stockout | size stockout | MEASUREMENT | Stockout tracks missing sizes, shoe sizes and seasonal categories. | Guides donations. |
| clothingdistops.metrics.discard_rate | discard rate | MEASUREMENT | Discard rate tracks unusable donations by reason. | Improves donor guidance. |
| clothingdistops.review.after_action | after-action review | METHOD | Review captures sizing, dignity, laundering, donation quality, delivery and reporting lessons. | Improves future distribution. |
