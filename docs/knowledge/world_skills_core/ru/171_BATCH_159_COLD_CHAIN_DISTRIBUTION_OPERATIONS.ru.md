# BATCH_159 — Cold-Chain Distribution Operations Detail
# world_skills_core · source: world_skills_core:batch_159:cold_chain_distribution_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| coldops.lane.temperature_lane | Temperature lane | invariant | Temperature lane defines required range, route, equipment, handovers and monitoring for temperature-sensitive goods. | маршрут под температурой |
| coldops.lane.product_profile | Cold-chain product profile | invariant | Product profile states allowed temperature range, sensitivity, shelf life, packaging and excursion rules. | товар задает режим |
| coldops.lane.lane_qualification | Lane qualification | variant | Lane qualification proves a route and method can maintain required conditions under expected seasons and handling. | проверить путь до запуска |
| coldops.lane.seasonal_profile | Seasonal lane profile | variant | Seasonal profile adjusts packaging, refrigerant, route or controls for hot, cold or mixed weather periods. | лето и зима разные |
| coldops.lane.transit_time | Cold-chain transit time | invariant | Transit time limits must align with packaging duration, product stability and delivery cutoffs. | время расходует thermal budget |
| coldops.lane.risk_point | Temperature risk point | invariant | Risk point is a location or step where goods may warm, freeze, wait or lose monitoring visibility. | слабое место маршрута |
| coldops.pack.thermal_packout | Thermal packout | invariant | Thermal packout combines insulation, refrigerant, product arrangement and duration target. | коробка как microclimate |
| coldops.pack.coolant_conditioning | Coolant conditioning | invariant | Coolant must be conditioned to correct temperature before packing to avoid freezing or insufficient cooling. | хладоэлемент тоже готовят |
| coldops.pack.payload_arrangement | Payload arrangement | invariant | Payload arrangement controls contact with refrigerant, airflow, voids and product stability. | размещение влияет на температуру |
| coldops.pack.temperature_buffer | Temperature buffer | variant | Buffer material can slow temperature change and reduce product exposure to local hot or cold spots. | сгладить перепады |
| coldops.pack.packout_validation | Packout validation | invariant | Validation shows packaging configuration maintains range for expected duration and conditions. | доказать упаковку |
| coldops.pack.label_orientation | Cold-chain label orientation | variant | Labels can instruct orientation, handling, do-not-freeze, keep-refrigerated or urgent unpacking. | инструкция на коробке |
| coldops.vehicle.reefer_pretrip | Reefer pre-trip check | invariant | Pre-trip check verifies unit operation, setpoint, fuel, cleanliness, alarms, doors and temperature record. | truck ready before load |
| coldops.vehicle.setpoint_control | Reefer setpoint control | invariant | Setpoint must match product requirement and be protected from unauthorized change. | one wrong number spoils cargo |
| coldops.vehicle.pre_cooling | Vehicle pre-cooling | invariant | Pre-cooling stabilizes cargo space before loading so goods do not absorb heat from trailer walls and air. | не грузить в теплый кузов |
| coldops.vehicle.airflow_clearance | Reefer airflow clearance | invariant | Airflow clearance prevents blocked evaporators, short-circuiting and uneven temperatures. | холод должен циркулировать |
| coldops.vehicle.door_open_time | Door open time | invariant | Door open time increases thermal load and should be minimized or controlled during loading and delivery. | двери расходуют холод |
| coldops.vehicle.bulkhead_use | Reefer bulkhead use | variant | Bulkhead separates temperature zones or reduces conditioned volume when used correctly. | разделить режимы |
| coldops.monitoring.data_logger | Temperature data logger | invariant | Data logger records temperatures over time and provides evidence for release or investigation. | evidence in shipment |
| coldops.monitoring.probe_placement | Probe placement | invariant | Probe placement must represent product exposure rather than only air near a vent or wall. | измерять риск, не комфорт |
| coldops.monitoring.real_time_alert | Real-time temperature alert | variant | Real-time alert enables intervention during transit if temperature approaches limits. | узнать до прибытия |
| coldops.monitoring.calibrated_sensor | Calibrated temperature sensor | invariant | Sensor calibration supports trust in recorded temperatures and excursion decisions. | thermometer must be true |
| coldops.monitoring.trip_report | Cold-chain trip report | invariant | Trip report links route, time, temperatures, alarms, doors, handovers and exceptions. | shipment story |
| coldops.monitoring.alarm_acknowledgment | Alarm acknowledgment | invariant | Alarm acknowledgment records who saw alert, when, assessment and action taken. | alert must create response |
| coldops.handover.loading_dock_control | Loading dock control | invariant | Dock control manages staging time, door exposure, product checks, vehicle readiness and loading sequence. | handover is risk |
| coldops.handover.staging_time | Cold-chain staging time | invariant | Staging time outside controlled temperature should be limited, measured and justified. | waiting warms product |
| coldops.handover.receiver_check | Receiver temperature check | invariant | Receiver check confirms shipment condition, documents temperatures, packaging state and visible issues. | arrival gate |
| coldops.handover.chain_of_custody | Cold-chain chain of custody | invariant | Chain of custody records custody changes across shipper, carrier, hub, courier and receiver. | who held it when |
| coldops.handover.crossdock_risk | Cold-chain crossdock risk | variant | Crossdock transfer adds exposure, misrouting and monitoring gaps if staging and handover are weak. | fast transfer still risky |
| coldops.handover.delivery_exception | Delivery exception | invariant | Exception records missed delivery, wrong address, refused shipment, delay or uncontrolled exposure. | deviation at last mile |
| coldops.excursion.temperature_excursion | Temperature excursion | invariant | Excursion occurs when product or environment leaves allowed temperature range for defined time or severity. | not automatically discard |
| coldops.excursion.excursion_assessment | Excursion assessment | invariant | Assessment compares excursion data with product stability rules, quality authority and documented evidence. | release decision needs facts |
| coldops.excursion.quarantine | Cold-chain quarantine | invariant | Quarantine prevents use or release of goods until excursion or damage is assessed. | hold before decision |
| coldops.excursion.disposition_decision | Disposition decision | invariant | Disposition decision releases, rejects, reworks or investigates goods based on quality criteria. | final quality call |
| coldops.excursion.root_cause | Cold-chain root cause | invariant | Root cause identifies equipment, process, route, packing, handover, sensor or human failure behind excursion. | fix the system |
| coldops.excursion.corrective_action | Cold-chain corrective action | invariant | Corrective action changes process, training, equipment, packaging or route to prevent recurrence. | learn from excursion |
| coldops.inventory.fefo | FEFO | invariant | First-expire-first-out prioritizes inventory by expiry date rather than receipt date. | shelf life matters |
| coldops.inventory.temperature_zone_storage | Temperature zone storage | invariant | Storage zones separate frozen, chilled, controlled room temperature and ambient goods. | avoid wrong room |
| coldops.inventory.door_alarm | Cold room door alarm | variant | Door alarm warns when cold room access remains open too long or temperature rises. | simple control |
| coldops.inventory.defrost_cycle | Defrost cycle | variant | Defrost cycle affects temperature stability and should be understood when interpreting storage readings. | normal fluctuation or issue |
| coldops.inventory.backup_power | Cold-chain backup power | invariant | Backup power protects cold rooms, freezers or monitoring systems during outages. | outage resilience |
| coldops.inventory.stock_rotation_audit | Stock rotation audit | invariant | Audit checks expiry, FEFO, temperature records, quarantine status and physical segregation. | cold inventory discipline |
| coldops.compliance.sop_training | Cold-chain SOP training | invariant | Training ensures staff know packout, monitoring, excursion, handover and documentation duties. | people hold the chain |
| coldops.compliance.release_record | Cold-chain release record | invariant | Release record ties shipment evidence, temperature data, exceptions and quality decision to product lot. | proof before use |
