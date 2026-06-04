# BATCH_189 — Field Service Installation Operations Detail
# world_skills_core · source: world_skills_core:batch_189:field_service_installation_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| fieldinstall.order.work_order | Installation work order | invariant | Work order defines customer, site, equipment, scope, schedule, access and acceptance criteria. | job authority |
| fieldinstall.order.scope_boundary | Scope boundary | invariant | Boundary states what is included, excluded, optional and chargeable. | avoid field disputes |
| fieldinstall.order.site_contact | Site contact | invariant | Contact provides access, approvals, local constraints and issue escalation. | someone can decide |
| fieldinstall.order.previsit_call | Previsit call | invariant | Call confirms address, readiness, access, hazards, power, space and customer availability. | prevent wasted trip |
| fieldinstall.order.permit_check | Installation permit check | variant | Check verifies whether permit, inspection, license or landlord approval is required. | legal readiness |
| fieldinstall.readiness.site_survey | Installation site survey | invariant | Survey captures dimensions, utilities, structure, network, environment and constraints. | reality before install |
| fieldinstall.readiness.readiness_gate | Site readiness gate | invariant | Gate confirms prerequisites before dispatching crew, equipment and materials. | do not arrive too early |
| fieldinstall.readiness.utility_availability | Utility availability | invariant | Availability checks power, water, drain, gas, air, network or other service needed. | system needs inputs |
| fieldinstall.readiness.access_path | Access path | invariant | Path confirms equipment can be moved through doors, stairs, lifts, dock or corridor. | logistics fit |
| fieldinstall.readiness.customer_prerequisite | Customer prerequisite | invariant | Prerequisite is work customer must complete before installation can proceed. | shared responsibility |
| fieldinstall.materials.pick_list | Installation pick list | invariant | Pick list lists equipment, parts, consumables, tools, documents and serial numbers. | pack the job |
| fieldinstall.materials.kit_check | Installation kit check | invariant | Kit check verifies all items before departure against scope and site conditions. | avoid return visit |
| fieldinstall.materials.serial_capture | Installed serial capture | invariant | Serial capture links installed equipment to customer, warranty, configuration and service history. | asset identity |
| fieldinstall.materials.spare_part | Field spare part | variant | Spare part supports common failures or adjustments during installation. | resilience in van |
| fieldinstall.materials.return_material | Return material authorization | invariant | RMA controls unused, damaged, exchanged or defective items returning from site. | inventory discipline |
| fieldinstall.safety.job_hazard_analysis | Job hazard analysis | invariant | Analysis identifies site hazards, controls, PPE, energy sources, work at height and traffic. | plan safe work |
| fieldinstall.safety.lockout_need | Lockout requirement | variant | Requirement applies when installation exposes hazardous energy needing isolation. | protect technicians |
| fieldinstall.safety.ladder_control | Ladder and access control | invariant | Control checks ladder suitability, surface, angle, user competence and exclusion area. | common injury source |
| fieldinstall.safety.hot_work_clearance | Hot work clearance | variant | Clearance controls welding, cutting or heat work near combustible material. | fire prevention |
| fieldinstall.safety.stop_work_authority | Stop work authority | invariant | Authority allows technician to pause job when unsafe condition appears. | safety over schedule |
| fieldinstall.execution.arrival_checkin | Field arrival check-in | invariant | Check-in records arrival time, contact, site access, safety briefing and scope confirmation. | start evidence |
| fieldinstall.execution.layout_marking | Installation layout marking | invariant | Marking places equipment, penetrations, brackets or cable paths before permanent work. | measure before drill |
| fieldinstall.execution.mounting | Equipment mounting | invariant | Mounting secures device according to load, substrate, vibration, clearance and service access. | physical stability |
| fieldinstall.execution.connection | Field connection | invariant | Connection joins power, network, pipe, duct, signal or mechanical interface per specification. | make system work |
| fieldinstall.execution.field_adjustment | Field adjustment | variant | Adjustment adapts minor fit, alignment or configuration issue within approved limits. | real sites vary |
| fieldinstall.config.initial_configuration | Initial configuration | invariant | Configuration sets parameters, address, firmware, user roles, calibration or network identity. | install is not just hardware |
| fieldinstall.config.firmware_version | Firmware version record | variant | Record notes installed software version and update status. | support trace |
| fieldinstall.config.customer_setting | Customer-specific setting | variant | Setting adapts operation to site preference, process, schedule or integration. | usable system |
| fieldinstall.config.network_test | Network connectivity test | variant | Test confirms device communicates with local network, cloud, controller or monitoring system. | data path works |
| fieldinstall.config.security_baseline | Installation security baseline | invariant | Baseline changes default credentials, applies roles and disables unnecessary access. | reduce exposure |
| fieldinstall.test.functional_test | Functional test | invariant | Test proves installed system performs required core functions. | acceptance evidence |
| fieldinstall.test.safety_test | Installation safety test | invariant | Test confirms guards, interlocks, grounding, leaks, alarms or protective devices as applicable. | safe operation |
| fieldinstall.test.calibration_check | Field calibration check | variant | Check verifies measurement or control output against reference or expected value. | trust readings |
| fieldinstall.test.integration_test | Integration test | variant | Test confirms installed item works with existing systems, controls, software or process. | whole system fit |
| fieldinstall.test.defect_punchlist | Installation punchlist | invariant | Punchlist records incomplete work, defects, owner, deadline and closure evidence. | finish visibly |
| fieldinstall.handover.user_training | User handover training | invariant | Training covers normal use, basic care, warnings, support path and documentation. | customer can operate |
| fieldinstall.handover.as_built_record | As-built installation record | invariant | Record captures actual location, routing, serials, settings, deviations and photos. | future service map |
| fieldinstall.handover.acceptance_signature | Acceptance signature | invariant | Signature confirms customer received work, training, documents and noted exceptions. | commercial close |
| fieldinstall.handover.warranty_start | Warranty start record | invariant | Record defines warranty start date, covered items, exclusions and service path. | lifecycle begins |
| fieldinstall.handover.site_cleanup | Site cleanup | invariant | Cleanup removes packaging, debris, temporary marks and waste according to site rules. | leave ready |
| fieldinstall.closeout.time_materials | Time and materials capture | invariant | Capture records labor, travel, parts, consumables and chargeable exceptions. | accurate billing |
| fieldinstall.closeout.photo_evidence | Installation photo evidence | invariant | Photos document before, during, after, labels, defects and final state. | remote proof |
| fieldinstall.closeout.followup_visit | Follow-up visit | variant | Visit resolves punchlist, training gaps, parts delay or post-install adjustment. | close remaining risk |
| fieldinstall.metrics.first_time_fix | Installation first-time-fix | variant | Metric tracks jobs completed without return visit or missing part. | quality and planning |
