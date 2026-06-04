# BATCH 432: Emergency Public Wi-Fi Access Support Operations

**KnowledgeUnits:** 44  
**Namespace:** `publicwifiops.*`  
**Scope:** sites, credentials, device help, privacy, security, accessibility and uptime reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| publicwifiops.activation.trigger | activation trigger | MODEL | Trigger includes telecom outage, sheltering, benefits deadlines, school needs or charging site demand. | Starts Wi-Fi support. |
| publicwifiops.activation.site_selection | site selection | METHOD | Site checks backhaul, power, coverage, accessibility, shelter, security and crowd capacity. | Places access. |
| publicwifiops.activation.service_model | service model | RECORD | Model distinguishes open hotspot, credentialed access, device lab or mobile Wi-Fi. | Defines operation. |
| publicwifiops.activation.command_link | command link | RECORD | Operation links IT, public information, facilities, security and partner agencies. | Maintains oversight. |
| publicwifiops.site.coverage_map | coverage map | RECORD | Map shows usable zones, weak spots, indoor/outdoor access and device help desk. | Guides users. |
| publicwifiops.site.signage | signage | METHOD | Signs show network name, hours, rules, help desk and privacy warning. | Reduces confusion. |
| publicwifiops.site.accessibility | accessibility check | QUALITY_CHECK | Site checks seating, wheelchair path, shade, lighting and multilingual signs. | Improves access. |
| publicwifiops.site.capacity | site capacity | MEASUREMENT | Capacity tracks seats, concurrent users, bandwidth and support staff. | Prevents overload. |
| publicwifiops.credentials.ssid | SSID record | RECORD | SSID record captures network name, location, start time and owner. | Controls access. |
| publicwifiops.credentials.password | password handling | SAFETY_RULE | Passwords rotate by policy and are distributed through approved channels. | Reduces misuse. |
| publicwifiops.credentials.guest_terms | guest terms | CONSTRAINT | Terms define acceptable use, time limits, privacy expectations and support boundaries. | Sets rules. |
| publicwifiops.credentials.reset | credential reset | METHOD | Reset handles compromised, stale or misprinted credentials. | Restores control. |
| publicwifiops.device.device_help | device help intake | RECORD | Intake records issue type, device, language, urgency and privacy consent. | Organizes support. |
| publicwifiops.device.connection_steps | connection steps | METHOD | Staff guide users through Wi-Fi selection, password, portal and basic troubleshooting. | Gets online. |
| publicwifiops.device.no_admin | no-admin boundary | CONSTRAINT | Staff avoid changing system settings beyond approved basic help. | Reduces liability. |
| publicwifiops.device.accessible_device | accessible device help | METHOD | Support covers screen readers, captions, font size and adaptive input needs. | Improves inclusion. |
| publicwifiops.privacy.notice | privacy notice | SAFETY_RULE | Notice warns public Wi-Fi is not for sensitive activity without protections. | Protects users. |
| publicwifiops.privacy.screen_privacy | screen privacy | METHOD | Seating and staff scripts reduce exposure of benefits, legal or medical forms. | Preserves dignity. |
| publicwifiops.privacy.data_minimum | data minimum | SAFETY_RULE | Help desk avoids collecting passwords, account data or personal content. | Reduces exposure. |
| publicwifiops.privacy.child_safety | child safety | CONSTRAINT | Youth device use follows site supervision and acceptable-use rules. | Protects minors. |
| publicwifiops.security.network_isolation | network isolation | SAFETY_RULE | Public clients are isolated from staff, facility and sensitive networks. | Reduces cyber risk. |
| publicwifiops.security.content_risk | content risk | METHOD | Staff route abuse, harassment or illegal-use concerns to supervisor process. | Controls misuse. |
| publicwifiops.security.fake_hotspot | fake hotspot warning | SAFETY_RULE | Users are warned to verify official network names and avoid lookalike hotspots. | Prevents fraud. |
| publicwifiops.security.incident | security incident | RECORD | Incident records outage, abuse, suspected compromise, harassment or device theft. | Supports review. |
| publicwifiops.operations.staff_roster | staff roster | RECORD | Roster covers IT lead, greeters, device helpers, interpreter and security contact. | Maintains coverage. |
| publicwifiops.operations.shift_brief | shift brief | METHOD | Brief covers credentials, outages, privacy script, escalation and common device issues. | Aligns staff. |
| publicwifiops.operations.equipment | equipment inventory | RECORD | Inventory tracks routers, cables, batteries, signs, tables and loaner devices. | Controls assets. |
| publicwifiops.operations.cleaning | station cleaning | METHOD | Cleaning handles shared tables, keyboards, loaners and high-touch items. | Reduces illness. |
| publicwifiops.uptime.status_check | status check | QUALITY_CHECK | Check tests connection, speed, captive portal, power and coverage. | Confirms service. |
| publicwifiops.uptime.outage_log | outage log | RECORD | Log records start, end, cause, users affected and workaround. | Tracks reliability. |
| publicwifiops.uptime.bandwidth | bandwidth metric | MEASUREMENT | Metric tracks throughput, congestion and device count. | Guides capacity. |
| publicwifiops.uptime.backup | backup connectivity | METHOD | Backup uses alternate carrier, satellite, hotspot, mesh or wired connection. | Maintains access. |
| publicwifiops.communication.public_notice | public notice | METHOD | Notice states locations, hours, rules, device help and accessibility. | Guides residents. |
| publicwifiops.communication.status_update | status update | METHOD | Updates announce outage, relocation, password change or capacity limit. | Reduces frustration. |
| publicwifiops.communication.partner_update | partner update | METHOD | Partners receive Wi-Fi site status, document upload hours and device support limits. | Aligns referrals. |
| publicwifiops.records.daily_log | daily log | RECORD | Log stores users served, device help, incidents, outages and equipment issues. | Creates audit trail. |
| publicwifiops.records.retention | retention rule | CONSTRAINT | IT, incident and support records follow privacy and emergency retention schedules. | Preserves audit. |
| publicwifiops.records.change_log | change log | RECORD | Change log records password rotations, equipment moves, outage workarounds and site notices. | Supports troubleshooting. |
| publicwifiops.metrics.users_served | users served | MEASUREMENT | Count tracks estimated users, help sessions and peak times. | Shows demand. |
| publicwifiops.metrics.uptime | uptime metric | MEASUREMENT | Uptime compares available hours with planned service hours. | Shows reliability. |
| publicwifiops.metrics.help_resolution | help resolution | MEASUREMENT | Resolution tracks device help completed, referred or unresolved. | Improves support. |
| publicwifiops.qa.site_review | site review | QUALITY_CHECK | Review checks signs, privacy, security, accessibility, uptime and staff scripts. | Improves quality. |
| publicwifiops.demob.closeout | closeout | METHOD | Closeout removes credentials, equipment, signs and archives incident logs. | Ends safely. |
| publicwifiops.review.after_action | after-action review | METHOD | Review captures backhaul, privacy, device help, accessibility and uptime lessons. | Improves future Wi-Fi. |
