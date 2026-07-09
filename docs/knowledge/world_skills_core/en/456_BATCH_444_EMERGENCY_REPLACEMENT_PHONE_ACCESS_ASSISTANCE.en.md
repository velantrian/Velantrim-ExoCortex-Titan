# BATCH 444: Emergency Replacement Phone Access Assistance

**KnowledgeUnits:** 44  
**Namespace:** `phoneaccessops.*`  
**Scope:** intake, eligibility, device sourcing, activation, charging, privacy and follow-up.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| phoneaccessops.intake.request_source | request source | RECORD | Source records shelter desk, survivor center, caseworker, hotline, clinic, school or outreach team. | Shows entry path. |
| phoneaccessops.intake.client_contact | client contact | RECORD | Contact records current safe channel, alternate contact, location, language and communication risk. | Enables coordination. |
| phoneaccessops.intake.loss_context | loss context | RECORD | Context notes phone lost, damaged, stolen, uncharged, inaccessible, disconnected or lacking service. | Frames need. |
| phoneaccessops.intake.urgency_score | urgency score | MODEL | Score weighs medical contact, benefits access, family reunification, work, school and safety alert needs. | Prioritizes cases. |
| phoneaccessops.eligibility.disaster_link | disaster link | CONTROL | Link verifies access problem is caused or worsened by disaster, displacement, outage or loss. | Targets devices. |
| phoneaccessops.eligibility.program_limit | program limit | CONTROL | Limit defines covered device, SIM, plan duration, charger, minutes, data and replacement boundaries. | Controls cost. |
| phoneaccessops.eligibility.duplicate_check | duplicate check | CONTROL | Check compares client, household, device ID, SIM, prior issue and active benefit records. | Prevents double issue. |
| phoneaccessops.sourcing.device_pool | device pool | RECORD | Pool records donated phones, new prepaid devices, refurbished devices, chargers, SIMs and accessories. | Tracks stock. |
| phoneaccessops.sourcing.condition_check | condition check | PROCESS | Check reviews screen, battery, ports, lock status, IMEI, charger compatibility and basic function. | Avoids bad issue. |
| phoneaccessops.sourcing.sanitation | device sanitation | PROCESS | Sanitation cleans surfaces, removes prior accessories and marks device ready for issue. | Protects users. |
| phoneaccessops.sourcing.accessory_match | accessory match | CONTROL | Match pairs charger, cable, wall plug, case, SIM tool or accessibility accessory with device. | Prevents unusable kits. |
| phoneaccessops.activation.identity_need | identity need | RECORD | Need records required identity proof, program exception, proxy support or missing-document barrier. | Prepares activation. |
| phoneaccessops.activation.plan_selection | plan selection | MODEL | Selection matches emergency minutes, texts, data, hotspot need, duration and network coverage. | Fits use. |
| phoneaccessops.activation.sim_registration | SIM registration | PROCESS | Registration links SIM, device, client, plan, activation date and privacy-safe account notes. | Enables service. |
| phoneaccessops.activation.test_call | test call | PROCESS | Test verifies call, text, data, voicemail, emergency alerts and charger function before handoff. | Confirms usability. |
| phoneaccessops.charging.charger_issue | charger issue | RECORD | Issue records charger type, cable, plug, power bank, solar option or public charging referral. | Keeps device usable. |
| phoneaccessops.charging.power_bank_pool | power bank pool | RECORD | Pool tracks charged banks, capacity, issue status, return expectation and recharge cycle. | Supports outages. |
| phoneaccessops.charging.safe_charging | safe charging guidance | PROCESS | Guidance covers heat, water, damaged cables, shared stations, overnight charging and theft prevention. | Reduces risk. |
| phoneaccessops.privacy.data_wipe | data wipe | CONTROL | Wipe confirms donated devices are reset and previous user data is removed before issue. | Protects privacy. |
| phoneaccessops.privacy.minimum_data | minimum data | CONTROL | Minimum data limits program records to eligibility, device, SIM, plan and contact need. | Reduces exposure. |
| phoneaccessops.privacy.safe_contact | safe contact rule | CONTROL | Rule records whether calls, texts, voicemail or account notices may reveal location or case status. | Protects survivors. |
| phoneaccessops.privacy.account_password | account password control | CONTROL | Control sets client-owned password or PIN and avoids staff retaining unnecessary access. | Preserves autonomy. |
| phoneaccessops.handoff.issue_agreement | issue agreement | RECORD | Agreement records device, SIM, plan duration, support limits, loss rules and client acknowledgment. | Sets expectations. |
| phoneaccessops.handoff.accessible_setup | accessible setup | PROCESS | Setup configures font size, captions, emergency contacts, language, accessibility settings and shortcuts. | Improves use. |
| phoneaccessops.handoff.handoff_proof | handoff proof | RECORD | Proof records recipient, device ID, SIM, charger, plan and date. | Closes custody. |
| phoneaccessops.support.user_orientation | user orientation | PROCESS | Orientation explains calling, texting, charging, voicemail, plan limit, emergency alerts and support contact. | Enables use. |
| phoneaccessops.support.number_update | number update | PROCESS | Update helps client notify caseworkers, family, clinics, schools or benefits contacts of new number. | Restores connections. |
| phoneaccessops.support.troubleshooting | troubleshooting | PROCESS | Troubleshooting covers no service, dead battery, locked device, SIM error, data issue and lost charger. | Resolves issues. |
| phoneaccessops.security.theft_risk | theft risk guidance | PROCESS | Guidance covers public charging, visible storage, password, tracking limits and reporting lost device. | Reduces loss. |
| phoneaccessops.security.misuse_boundary | misuse boundary | CONTROL | Boundary defines program response to resale, harassment, fraud, duplicate claims or unsafe use. | Protects program. |
| phoneaccessops.records.case_file | case file | RECORD | File links intake, eligibility, device source, activation, handoff, support and closeout. | Supports audit. |
| phoneaccessops.records.inventory_log | inventory log | RECORD | Log tracks device ID, IMEI, SIM, charger, plan, status, loss and retirement. | Maintains control. |
| phoneaccessops.records.exception_log | exception log | RECORD | Log captures activation failure, missing ID, network gap, defective device, privacy risk or loss. | Enables review. |
| phoneaccessops.records.consent_note | consent note | RECORD | Note records permission for activation help, partner coordination, safe contact and follow-up. | Documents consent. |
| phoneaccessops.communication.client_update | client update | PROCESS | Update explains approval, pickup, activation status, plan duration and support options through safe channel. | Reduces uncertainty. |
| phoneaccessops.communication.partner_coordination | partner coordination | PROCESS | Coordination asks carriers, donors, refurbishers or nonprofits for devices, SIMs, plans or support. | Expands capacity. |
| phoneaccessops.communication.referral_handoff | referral handoff | PROCESS | Handoff routes cases needing long-term broadband, benefits phones, assistive tech or safety planning. | Keeps support moving. |
| phoneaccessops.metrics.issue_rate | issue rate | METRIC | Rate tracks eligible requests filled with working phone access. | Measures reach. |
| phoneaccessops.metrics.activation_success | activation success | METRIC | Success compares attempted activations, working activations, failures and pending cases. | Shows bottlenecks. |
| phoneaccessops.metrics.followup_contact | follow-up contact metric | METRIC | Metric tracks whether client could be reached after issue and whether phone remains usable. | Confirms benefit. |
| phoneaccessops.metrics.device_failure_rate | device failure rate | METRIC | Rate tracks issued devices that fail, return, need replacement or cannot hold charge. | Improves sourcing. |
| phoneaccessops.closeout.use_confirmation | use confirmation | PROCESS | Confirmation verifies calls, texts, charging, service plan and remaining barriers. | Closes loop. |
| phoneaccessops.closeout.lost_device_process | lost device process | PROCESS | Process records loss, suspends service when needed, evaluates replacement and updates inventory. | Controls risk. |
| phoneaccessops.closeout.after_action | after-action note | RECORD | Note captures device shortages, activation blockers, privacy issues and partner improvements. | Improves next cycle. |
