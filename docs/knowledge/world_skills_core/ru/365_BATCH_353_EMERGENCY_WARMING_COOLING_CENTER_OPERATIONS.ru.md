# BATCH 353: Emergency Warming and Cooling Center Operations

**KnowledgeUnits:** 44  
**Namespace:** `tempcenterops.*`  
**Scope:** activation thresholds, staffing, supplies, transport, communications, safety and closure.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| tempcenterops.activation.threshold | activation threshold | MODEL | Threshold uses temperature, wind chill, heat index, smoke, outage or public health guidance. | Defines opening trigger. |
| tempcenterops.activation.authority | activation authority | RECORD | Authority records agency decision, time, sites and expected duration. | Clarifies responsibility. |
| tempcenterops.activation.site_ready | site readiness | QUALITY_CHECK | Site is checked for HVAC, water, toilets, accessibility, exits, seating and power. | Prevents unsafe activation. |
| tempcenterops.activation.hours | operating hours | RECORD | Hours define opening, overnight status, meal periods and closure plan. | Sets public expectation. |
| tempcenterops.site.capacity | capacity count | MEASUREMENT | Capacity counts seats, sleeping space if any, staff, pets and accessibility space. | Avoids overcrowding. |
| tempcenterops.site.layout | layout plan | METHOD | Layout separates intake, seating, rest, supplies, pets, staff and quiet space. | Makes operations flow. |
| tempcenterops.site.accessibility | accessibility check | QUALITY_CHECK | Routes, restrooms, signage and seating support disability access. | Keeps service inclusive. |
| tempcenterops.site.backup_power | backup power | CONSTRAINT | Backup power supports critical lighting, communications, refrigeration and HVAC where available. | Improves resilience. |
| tempcenterops.staffing.roster | staff roster | RECORD | Roster tracks roles, shifts, contacts, credentials and relief coverage. | Keeps center staffed. |
| tempcenterops.staffing.briefing | shift briefing | METHOD | Briefing covers weather, capacity, incidents, supplies, vulnerable guests and closing plan. | Aligns team. |
| tempcenterops.staffing.volunteer | volunteer management | SAFETY_RULE | Volunteers are registered, assigned and supervised. | Reduces safeguarding risk. |
| tempcenterops.staffing.fatigue | fatigue control | MODEL | Long activations require breaks, relief and overnight staffing rules. | Protects staff performance. |
| tempcenterops.intake.sign_in | sign-in | METHOD | Sign-in may record count, name or anonymous use depending on policy. | Balances accountability and access. |
| tempcenterops.intake.needs_screen | needs screen | METHOD | Screen identifies medical, mobility, language, transport, pet or charging needs. | Connects guests to support. |
| tempcenterops.intake.privacy | privacy boundary | SAFETY_RULE | Guest information is minimized and protected. | Reduces fear and misuse. |
| tempcenterops.intake.referral | referral pathway | METHOD | Guests can be referred to shelter, outreach, clinic, transport or benefits help. | Extends beyond temporary relief. |
| tempcenterops.supplies.water | water supply | RECORD | Water stock is planned by occupancy, hours and heat/cold conditions. | Prevents dehydration. |
| tempcenterops.supplies.food | food and snacks | METHOD | Food plan covers simple meals, snacks, dietary limits and food safety. | Supports extended stays. |
| tempcenterops.supplies.hygiene | hygiene supplies | RECORD | Supplies include tissues, sanitizer, masks, menstrual products and cleaning materials. | Maintains dignity and sanitation. |
| tempcenterops.supplies.charging | device charging | METHOD | Charging stations are supervised and capacity-limited. | Helps guests contact family/services. |
| tempcenterops.health.heat_illness | heat illness watch | SAFETY_RULE | Staff watch for heat illness signs and escalate to medical response. | Protects life safety. |
| tempcenterops.health.cold_exposure | cold exposure watch | SAFETY_RULE | Staff watch for hypothermia, frostbite or exposure risk. | Protects guests in cold events. |
| tempcenterops.health.medical_escalation | medical escalation | METHOD | Medical concerns route to EMS, nurse, public health or clinic partner. | Avoids unsafe onsite improvisation. |
| tempcenterops.health.infection_control | infection control | METHOD | Cleaning, ventilation, masking or spacing follows current public health guidance. | Reduces disease spread. |
| tempcenterops.transport.route_info | route information | METHOD | Public communications include transit routes, pickup points and accessible transport. | Helps people reach center. |
| tempcenterops.transport.shuttle | shuttle coordination | METHOD | Shuttle plan covers stops, schedule, driver contacts and accessibility. | Supports high-need guests. |
| tempcenterops.transport.return_trip | return trip | METHOD | Closure plan includes safe return or next destination transport. | Avoids stranding people. |
| tempcenterops.transport.partner_dispatch | partner dispatch | METHOD | Outreach, transit, police non-emergency or nonprofits may help transport. | Coordinates field access. |
| tempcenterops.communication.public_notice | public notice | METHOD | Notice states location, hours, eligibility, pets, transport, supplies and contacts. | Directs public clearly. |
| tempcenterops.communication.partner_alert | partner alert | METHOD | Partners receive activation, referral rules and resource needs. | Aligns outreach network. |
| tempcenterops.communication.language | language access | METHOD | Core notices are translated or interpreted for local high-need languages. | Improves access. |
| tempcenterops.communication.status_update | status update | METHOD | Updates announce capacity, hours changes, relocation or closure. | Prevents wasted trips. |
| tempcenterops.security.access | access control | METHOD | Access controls entry, restricted rooms, after-hours movement and staff-only areas. | Keeps center orderly. |
| tempcenterops.security.conduct | conduct rules | METHOD | Rules address safety, weapons, harassment, pets, quiet areas and substance policy. | Sets shared expectations. |
| tempcenterops.security.incident | incident report | RECORD | Incidents record facts, action, escalation and follow-up. | Supports review. |
| tempcenterops.security.deescalation | de-escalation | METHOD | Staff use de-escalation and support referral where safe. | Reduces conflict. |
| tempcenterops.records.sitrep | situation report | RECORD | Sitrep tracks occupancy, supplies, incidents, staffing and open needs. | Feeds emergency management. |
| tempcenterops.records.costs | cost record | RECORD | Costs track labor, food, supplies, transport, facility and contracts. | Supports reimbursement. |
| tempcenterops.records.retention | retention rule | CONSTRAINT | Records follow emergency management, privacy and grant retention rules. | Keeps audit trail. |
| tempcenterops.metrics.utilization | utilization metric | MEASUREMENT | Utilization tracks visitors by hour, day, site and condition. | Guides future activation. |
| tempcenterops.metrics.unmet_need | unmet need | MEASUREMENT | Unmet need captures turnaways, transport barriers and supply shortages. | Improves planning. |
| tempcenterops.closeout.close_trigger | close trigger | METHOD | Closure occurs when weather, hazard, power or public health conditions improve. | Ends activation safely. |
| tempcenterops.closeout.site_restore | site restoration | METHOD | Site is cleaned, supplies inventoried, damages recorded and keys returned. | Restores host facility. |
| tempcenterops.review.after_action | after-action review | METHOD | Review captures timing, outreach, capacity, incidents and improvement actions. | Strengthens future response. |
