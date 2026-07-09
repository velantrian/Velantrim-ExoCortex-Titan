# BATCH_247 — Election Polling Place Operations Detail
# world_skills_core · source: world_skills_core:batch_247:election_polling_place_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| pollops.setup.site_access | Polling place site access | invariant | Access confirms keys, entry time, parking, utilities, restrooms and emergency exits. | open site |
| pollops.setup.room_layout | Polling place room layout | invariant | Layout places check-in, voting booths, ballot scanner, accessible route and observer area. | orderly voting |
| pollops.setup.signage_posting | Polling place signage posting | invariant | Posting displays required notices, directions, hours, rights, prohibited conduct and accessibility signs. | inform voters |
| pollops.setup.equipment_start | Election equipment startup | invariant | Startup verifies power, seals, zero reports, paper, privacy screens and test status. | ready equipment |
| pollops.setup.supply_check | Polling place supply check | invariant | Check confirms ballots, forms, envelopes, pens, seals, logs, PPE and emergency materials. | avoid shortages |
| pollops.checkin.voter_lookup | Voter check-in lookup | invariant | Lookup finds voter registration, precinct, ballot style, status and required next step. | correct ballot |
| pollops.checkin.identity_rule | Polling place identity rule | variant | Rule applies jurisdiction-specific identity or affirmation process without partisan discretion. | lawful check-in |
| pollops.checkin.address_update | Voter address update at polls | variant | Update records allowed address change, precinct impact, form and ballot path. | handle movers |
| pollops.checkin.provisional_route | Provisional ballot route | invariant | Route sends unresolved eligibility, precinct or registration issues to provisional process. | preserve vote |
| pollops.checkin.line_management | Polling place line management | variant | Management tracks queue length, wait time, accessibility needs, closing-time voters and calm flow. | reduce bottlenecks |
| pollops.ballot.ballot_style | Ballot style control | invariant | Control matches voter precinct, district, party if applicable and language format. | prevent wrong ballot |
| pollops.ballot.ballot_issue | Ballot issue log | invariant | Log records ballot given, voter sequence, spoiled ballot, replacement and initials. | custody |
| pollops.ballot.spoiled_ballot | Spoiled ballot process | invariant | Process voids damaged or mistaken ballot, records count and issues replacement if allowed. | protect count |
| pollops.ballot.assisted_voting | Assisted voting record | variant | Record captures voter-requested assistance while preserving privacy and legal requirements. | accessible voting |
| pollops.ballot.language_ballot | Language ballot support | variant | Support provides translated ballot, interpreter, notice or language assistance as authorized. | language access |
| pollops.accessibility.accessible_route | Polling accessible route | invariant | Route keeps parking, entrance, path, check-in, booth and scanner barrier-free. | inclusive access |
| pollops.accessibility.accessible_device | Accessible voting device | invariant | Device setup verifies audio, tactile controls, privacy, ballot style and printer if used. | independent voting |
| pollops.accessibility.curbside_voting | Curbside voting workflow | variant | Workflow brings check-in, ballot, privacy and custody process to eligible voter outside. | serve mobility needs |
| pollops.accessibility.accommodation_note | Polling accommodation note | variant | Note records assistance, seating, priority access or communication need without exposing choice. | respectful service |
| pollops.observers.observer_checkin | Poll observer check-in | invariant | Check-in records authorized observer, affiliation if required, rules and location. | controlled observation |
| pollops.observers.challenge_process | Voter challenge process | variant | Process records challenge, basis, official response, voter rights and documentation. | orderly dispute |
| pollops.observers.conduct_boundary | Poll observer conduct boundary | invariant | Boundary prevents intimidation, interference, photographing ballots or handling materials. | protect voters |
| pollops.security.ballot_security | Polling place ballot security | invariant | Security protects blank, voted, spoiled and provisional ballots with logs and seals. | custody |
| pollops.security.seal_log | Election seal log | invariant | Log records seal numbers, equipment, ballot containers, changes, witnesses and time. | tamper evidence |
| pollops.security.incident_escalation | Polling place incident escalation | invariant | Escalation routes intimidation, disorder, equipment failure, emergency or legal issue to officials. | keep polls open |
| pollops.security.no_campaign_zone | No-campaign zone control | invariant | Control enforces distance, signage, apparel, materials and complaints under local rule. | neutral site |
| pollops.operations.voter_privacy | Polling voter privacy | invariant | Privacy keeps booths shielded, screens angled, assistance limited and ballots hidden. | secret ballot |
| pollops.operations.equipment_jam | Ballot scanner jam response | variant | Response pauses use, preserves ballots, follows procedure, logs issue and resumes. | avoid loss |
| pollops.operations.power_outage | Polling place power outage | variant | Outage plan uses backup lights, paper process, equipment preservation and authority contact. | continue voting |
| pollops.operations.emergency_closure | Polling emergency closure | variant | Closure records reason, voters present, materials secured, notices and relocation direction. | protect election |
| pollops.incident.voter_complaint | Polling voter complaint | invariant | Complaint records issue, voter contact if given, official response and escalation. | accountability |
| pollops.incident.worker_issue | Poll worker issue | variant | Issue records absence, role confusion, misconduct, illness or replacement. | staff control |
| pollops.incident.accessibility_issue | Polling accessibility issue | invariant | Issue records barrier, temporary fix, voter impact, notification and follow-up. | compliance |
| pollops.incident.media_contact | Polling media contact | variant | Contact routes press questions, filming boundaries and spokesperson escalation. | protect process |
| pollops.close.closing_time_rule | Poll closing time rule | invariant | Rule allows voters in line at closing to vote and records line status. | protect rights |
| pollops.close.ballot_accounting | Polling place ballot accounting | invariant | Accounting reconciles issued, voted, spoiled, provisional, unused and total ballots. | count control |
| pollops.close.equipment_shutdown | Election equipment shutdown | invariant | Shutdown prints reports, secures memory, seals equipment and records totals. | close equipment |
| pollops.close.material_packout | Polling material packout | invariant | Packout separates ballots, logs, forms, seals, supplies and return bags by instruction. | return materials |
| pollops.custody.chain_transfer | Election chain-of-custody transfer | invariant | Transfer records materials, seal numbers, couriers, time, location and signatures. | custody evidence |
| pollops.custody.results_delivery | Polling results delivery | variant | Delivery sends media, reports or tabulation materials through authorized route. | official results |
| pollops.reporting.pollbook_reconciliation | Pollbook reconciliation | invariant | Reconciliation compares check-ins, ballots issued, provisional count and scanner totals. | detect variance |
| pollops.reporting.incident_summary | Polling incident summary | invariant | Summary aggregates incidents, complaints, equipment issues, accessibility and worker notes. | improve next election |
| pollops.metrics.polling_kpi | Polling place KPI | variant | KPI tracks wait times, check-ins, provisional rate, incidents, equipment downtime and accessibility issues. | manage elections |
| pollops.continuity.site_relocation | Polling place relocation response | variant | Response directs voters, secures materials, informs officials and documents continuity. | preserve voting |
