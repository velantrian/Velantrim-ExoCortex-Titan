# BATCH 416: Livestock Emergency Feed Support Operations

**KnowledgeUnits:** 44  
**Namespace:** `livestockfeedops.*`  
**Scope:** requests, herd counts, feed type, sourcing, delivery, safety and reconciliation.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| livestockfeedops.intake.request_source | request source | RECORD | Source records producer, veterinarian, extension, emergency manager, cooperative or hotline. | Shows entry path. |
| livestockfeedops.intake.producer_contact | producer contact | RECORD | Contact captures owner, farm, phone, delivery location and backup contact. | Enables coordination. |
| livestockfeedops.intake.need_reason | need reason | RECORD | Reason records drought, flood, fire, snow, transport disruption or pasture loss. | Explains request. |
| livestockfeedops.intake.urgency | urgency model | MODEL | Urgency weighs remaining feed, animal condition, weather, isolation and water access. | Prioritizes delivery. |
| livestockfeedops.herd.species | species record | RECORD | Species record distinguishes cattle, sheep, goats, horses, poultry, swine or specialty livestock. | Selects feed. |
| livestockfeedops.herd.headcount | herd count | MEASUREMENT | Count captures animals by class, age, weight band and lactation where relevant. | Sizes need. |
| livestockfeedops.herd.vulnerable | vulnerable group | RECORD | Vulnerable group includes young, pregnant, lactating, sick or senior animals. | Adjusts priority. |
| livestockfeedops.herd.location | herd location | RECORD | Location records pasture, barn, evacuation site, county and access constraints. | Supports routing. |
| livestockfeedops.feed.feed_type | feed type | RECORD | Type distinguishes hay, grain, pellets, silage, mineral, milk replacer or species feed. | Defines supply. |
| livestockfeedops.feed.ration_note | ration note | METHOD | Ration note uses producer/veterinary guidance without replacing professional nutrition advice. | Prevents mismatch. |
| livestockfeedops.feed.quantity_estimate | quantity estimate | MEASUREMENT | Estimate calculates requested units by animal count, period and feed type. | Plans stock. |
| livestockfeedops.feed.special_need | special need | RECORD | Special need captures medical diet, feed transition, storage limits or species restrictions. | Protects animals. |
| livestockfeedops.sourcing.supplier_roster | supplier roster | RECORD | Roster lists feed mills, hay brokers, cooperatives, farms and donation sources. | Finds supply. |
| livestockfeedops.sourcing.availability | availability check | QUALITY_CHECK | Check confirms quantity, quality, pickup time, price, loading and transport needs. | Avoids failed sourcing. |
| livestockfeedops.sourcing.donation | donation record | RECORD | Donation captures donor, feed type, quantity, condition, restrictions and receipt needs. | Tracks gifts. |
| livestockfeedops.sourcing.purchase_order | purchase order | RECORD | Order links supplier, feed, quantity, price, funding and delivery terms. | Starts procurement. |
| livestockfeedops.quality.feed_condition | feed condition | QUALITY_CHECK | Condition checks moisture, mold, spoilage, contamination, packaging and lot. | Protects herds. |
| livestockfeedops.quality.species_fit | species fit | SAFETY_RULE | Feed unsuitable for a species or class is not issued without expert approval. | Prevents harm. |
| livestockfeedops.quality.storage | storage check | SAFETY_RULE | Storage protects feed from water, pests, heat, theft and contamination. | Preserves supply. |
| livestockfeedops.quality.recall | recall check | QUALITY_CHECK | Recall or contamination notices are checked for purchased or donated feed. | Avoids unsafe issue. |
| livestockfeedops.delivery.route_plan | route plan | METHOD | Route groups deliveries by geography, urgency, feed type and truck capacity. | Saves time. |
| livestockfeedops.delivery.access_check | access check | METHOD | Check covers roads, gates, mud, bridges, loading area and unloading equipment. | Prevents failed delivery. |
| livestockfeedops.delivery.transport_unit | transport unit | RECORD | Unit records truck, trailer, driver, capacity, route and contact. | Executes movement. |
| livestockfeedops.delivery.delivery_window | delivery window | RECORD | Window records pickup, ETA, site contact, unloading plan and weather risk. | Sets expectations. |
| livestockfeedops.safety.loading | loading safety | SAFETY_RULE | Loading uses equipment, weight limits, traffic control and trained operators. | Prevents injuries. |
| livestockfeedops.safety.biosecurity | biosecurity rule | SAFETY_RULE | Vehicles and staff follow disease-control precautions between farms. | Reduces spread. |
| livestockfeedops.safety.driver | driver safety | SAFETY_RULE | Driver safety covers fatigue, road hazards, animal areas, backing and communication. | Protects crew. |
| livestockfeedops.safety.site_hazard | site hazard | RECORD | Site hazard records aggressive animals, damaged structures, floodwater or unstable ground. | Guides crew. |
| livestockfeedops.issue.issue_record | issue record | RECORD | Record captures producer, feed, quantity, date, source, driver and signature if feasible. | Tracks distribution. |
| livestockfeedops.issue.limit_rule | issue limit | CONSTRAINT | Limits define quantity per herd, period, species or priority. | Extends supply. |
| livestockfeedops.issue.exception | exception issue | RECORD | Exception records urgent animal welfare need, approval and reason. | Allows flexibility. |
| livestockfeedops.issue.refusal | refusal record | RECORD | Refusal records unsuitable feed, access failure, producer cancellation or safety issue. | Explains non-delivery. |
| livestockfeedops.reconcile.stock_count | stock count | MEASUREMENT | Count reconciles received, issued, spoiled, transferred and remaining feed. | Shows inventory. |
| livestockfeedops.reconcile.invoice | invoice reconciliation | QUALITY_CHECK | Invoice checks supplier, quantity, delivery, price and funding code. | Prevents overpayment. |
| livestockfeedops.reconcile.donation_receipt | donation receipt | RECORD | Receipt documents donor acknowledgement, restrictions and disposition. | Supports accountability. |
| livestockfeedops.reconcile.loss | loss record | RECORD | Loss records spoiled, damaged, stolen or unusable feed and reason. | Explains variance. |
| livestockfeedops.communication.producer_update | producer update | METHOD | Update explains delivery status, limits, substitutions, safety notes and next request path. | Reduces uncertainty. |
| livestockfeedops.communication.partner_update | partner update | METHOD | Partners receive feed gaps, delivery barriers, herd needs and supplier status. | Coordinates response. |
| livestockfeedops.communication.public_notice | public notice | METHOD | Notice states request channel, eligible species, required herd information and limits. | Guides producers. |
| livestockfeedops.reporting.daily_summary | daily summary | MEASUREMENT | Summary reports requests, deliveries, feed issued, stock, shortages and urgent herds. | Informs command. |
| livestockfeedops.metrics.herds_served | herds served | MEASUREMENT | Count tracks producers and animals served by species and area. | Shows reach. |
| livestockfeedops.metrics.feed_tons | feed tons | MEASUREMENT | Metric totals feed issued by type, source and destination. | Shows scale. |
| livestockfeedops.metrics.failed_delivery | failed delivery rate | MEASUREMENT | Rate tracks failed or delayed deliveries by reason. | Improves logistics. |
| livestockfeedops.review.after_action | after-action review | METHOD | Review captures sourcing, quality, biosecurity, delivery access and reconciliation lessons. | Improves future feed support. |
