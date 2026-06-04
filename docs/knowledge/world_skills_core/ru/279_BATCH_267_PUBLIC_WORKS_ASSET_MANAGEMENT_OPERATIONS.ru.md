# BATCH_267 — Public Works Asset Management Operations Detail
# world_skills_core · source: world_skills_core:batch_267:public_works_asset_management_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| pwasset.inventory.asset_register | Public works asset register | invariant | Register stores asset ID, type, location, owner, install date, status and source. | know assets |
| pwasset.inventory.asset_type | Public works asset type | invariant | Type classifies roads, signs, pipes, culverts, signals, parks, facilities or fleet assets. | organize inventory |
| pwasset.inventory.location_accuracy | Asset location accuracy | invariant | Accuracy records coordinates, address, segment, side, offset and confidence. | find asset |
| pwasset.inventory.parent_child | Public works parent-child asset | variant | Relationship links system, segment, component, subcomponent and replaceable part. | model hierarchy |
| pwasset.inventory.field_collection | Public works field collection | variant | Collection captures asset details by GPS, mobile form, photo and condition. | build inventory |
| pwasset.condition.condition_rating | Asset condition rating | invariant | Rating scores observed condition using standard scale, date, assessor and method. | compare assets |
| pwasset.condition.defect_code | Public works defect code | invariant | Code identifies crack, corrosion, settlement, missing part, blockage, wear or failure. | standardize findings |
| pwasset.condition.criticality_score | Asset criticality score | invariant | Score reflects safety, service impact, replacement cost, redundancy and public exposure. | prioritize work |
| pwasset.condition.remaining_life | Asset remaining useful life | variant | Estimate combines age, condition, material, environment and maintenance history. | plan renewal |
| pwasset.condition.inspection_cycle | Asset inspection cycle | invariant | Cycle sets frequency by asset type, risk, regulation, age and condition. | keep data current |
| pwasset.workhistory.work_order_link | Asset work order link | invariant | Link connects maintenance, repair, complaint or project work to asset ID. | history trace |
| pwasset.workhistory.failure_event | Public works asset failure event | invariant | Event records date, cause, service impact, emergency response and repair. | learn failures |
| pwasset.workhistory.preventive_task | Asset preventive maintenance task | variant | Task schedules cleaning, lubrication, repainting, flushing, inspection or calibration. | reduce failures |
| pwasset.workhistory.cost_record | Asset cost record | invariant | Record captures labor, materials, equipment, contractor and overhead by asset. | lifecycle cost |
| pwasset.lifecycle.lifecycle_plan | Public works lifecycle plan | invariant | Plan defines maintain, rehabilitate, replace, abandon or monitor strategy over time. | long-term stewardship |
| pwasset.lifecycle.renewal_candidate | Asset renewal candidate | variant | Candidate flags asset needing rehab or replacement by risk, condition and cost. | capital planning |
| pwasset.lifecycle.level_of_service | Public works level of service | invariant | Service level defines target condition, response time, reliability or availability. | set expectations |
| pwasset.lifecycle.intervention_trigger | Asset intervention trigger | invariant | Trigger starts work when condition, age, risk, complaint or failure threshold is met. | timely action |
| pwasset.lifecycle.deferred_maintenance | Deferred maintenance record | variant | Record documents postponed work, reason, risk, cost growth and review date. | expose backlog |
| pwasset.budget.capital_plan | Public works capital plan | invariant | Plan prioritizes projects, years, costs, funding sources, assets and outcomes. | fund renewal |
| pwasset.budget.operating_budget | Asset operating budget | variant | Budget covers routine maintenance, inspection, emergency repair and service contracts. | sustain assets |
| pwasset.budget.unit_cost | Public works unit cost | invariant | Cost tracks price per lane-mile, sign, catch basin, pipe foot or facility unit. | estimate work |
| pwasset.budget.funding_constraint | Asset funding constraint | variant | Constraint records grant, bond, utility fee, tax, eligibility or expiration condition. | plan funding |
| pwasset.risk.risk_matrix | Public works asset risk matrix | invariant | Matrix combines likelihood of failure and consequence into priority class. | risk-based decisions |
| pwasset.risk.safety_exposure | Asset safety exposure | invariant | Exposure records crash, collapse, flooding, trip, electrical or contamination potential. | protect public |
| pwasset.risk.climate_stressor | Asset climate stressor | variant | Stressor notes heat, freeze, flood, fire, drought, corrosion or storm load. | adapt plans |
| pwasset.data.data_standard | Public works asset data standard | invariant | Standard defines required fields, domains, naming, geometry and update rules. | clean data |
| pwasset.data.duplicate_asset | Duplicate asset resolution | invariant | Resolution merges repeated records, preserves history and selects authoritative ID. | avoid double count |
| pwasset.data.data_quality_audit | Asset data quality audit | invariant | Audit checks missing fields, impossible dates, map errors, orphan records and duplicates. | reliable inventory |
| pwasset.data.system_integration | Asset system integration | variant | Integration links GIS, work orders, finance, permits, SCADA or document systems. | connected operations |
| pwasset.reporting.condition_report | Public works condition report | invariant | Report summarizes condition distribution by asset class, district, age and risk. | management view |
| pwasset.reporting.backlog_report | Public works maintenance backlog report | invariant | Report lists overdue work, deferred maintenance, risk class and estimated cost. | manage backlog |
| pwasset.reporting.performance_report | Public works performance report | variant | Report compares service levels, failures, response times, cost and condition trends. | accountability |
| pwasset.reporting.map_dashboard | Public works asset map dashboard | variant | Dashboard displays assets, condition, work, risks, projects and filters. | spatial decisions |
| pwasset.governance.asset_owner | Public works asset owner | invariant | Owner defines responsible department, program, budget, data steward and decision authority. | clear accountability |
| pwasset.governance.change_control | Asset data change control | invariant | Control records edits, approvals, bulk updates, imports and audit trail. | protect inventory |
| pwasset.governance.policy_update | Asset management policy update | variant | Update sets inspection, condition, renewal, prioritization and reporting expectations. | consistent practice |
| pwasset.projects.project_asset_link | Capital project asset link | invariant | Link connects project scope to affected assets, removals, additions and condition reset. | update inventory |
| pwasset.projects.asbuilt_capture | Public works as-built capture | variant | Capture records installed assets, materials, dimensions, coordinates and contractor documents. | current records |
| pwasset.projects.handover_check | Asset handover check | invariant | Check confirms new asset data, warranties, manuals, inspections and maintenance plan. | operational readiness |
| pwasset.metrics.asset_kpi | Public works asset management KPI | variant | KPI tracks inventory completeness, condition, backlog, renewal rate, failures and data quality. | manage assets |
| pwasset.continuity.emergency_asset_update | Emergency asset update | variant | Update records temporary repair, damaged asset, closure and later permanent work. | crisis memory |
| pwasset.close.asset_retirement | Public works asset retirement | invariant | Retirement records removal, abandonment, replacement, disposal and final status. | lifecycle closure |
| pwasset.audit.asset_audit_trail | Asset audit trail | invariant | Trail records creation, condition changes, work links, costs, projects and retirement. | defensible history |
