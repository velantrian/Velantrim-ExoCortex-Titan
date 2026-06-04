# BATCH 435: Disaster Prescription Delivery Route Coordination

**KnowledgeUnits:** 44  
**Namespace:** `prescriptionrouteops.*`  
**Scope:** requests, pharmacy pickup, cold chain, privacy, routing, failed delivery and proof.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| prescriptionrouteops.intake.request_source | request source | RECORD | Source records hotline, clinic, shelter desk, caseworker, pharmacy, caregiver or outreach team. | Shows entry path. |
| prescriptionrouteops.intake.patient_contact | patient contact | RECORD | Contact captures safe phone, alternate contact, delivery address, language and privacy preference. | Enables reachability. |
| prescriptionrouteops.intake.medication_need | medication need | RECORD | Need describes refill, replacement, urgent pickup, temperature-sensitive item or delivery barrier. | Frames service. |
| prescriptionrouteops.intake.consent | delivery consent | CONTROL | Consent confirms the patient or authorized person permits pickup, transport and limited status updates. | Protects privacy. |
| prescriptionrouteops.eligibility.disaster_barrier | disaster barrier | MODEL | Barrier distinguishes evacuation, road closure, pharmacy outage, mobility limit, shelter stay or lost transport. | Prioritizes relief cases. |
| prescriptionrouteops.eligibility.authorization_check | authorization check | CONTROL | Authorization verifies patient identity, proxy permission and pharmacy release rules before pickup. | Prevents improper release. |
| prescriptionrouteops.eligibility.scope_limit | scope limit | CONTROL | Scope limit separates routine convenience delivery from disaster access support. | Keeps resources targeted. |
| prescriptionrouteops.pharmacy.pickup_window | pickup window | RECORD | Pickup window records pharmacy hours, ready time, staff contact, queue constraints and after-hours fallback. | Prevents wasted trips. |
| prescriptionrouteops.pharmacy.package_label | package label | CONTROL | Package label uses neutral route code and recipient confirmation without exposing medication details. | Reduces disclosure risk. |
| prescriptionrouteops.pharmacy.release_log | release log | RECORD | Release log captures pharmacy handoff person, time, package count and exception notes. | Creates custody trail. |
| prescriptionrouteops.pharmacy.partial_fill | partial fill | STATE | Partial fill flags items unavailable, short-filled or awaiting prescriber approval. | Sets user expectations. |
| prescriptionrouteops.coldchain.temperature_need | temperature need | RECORD | Temperature need marks refrigeration, insulation, no-freeze limits or room-temperature handling. | Protects medication quality. |
| prescriptionrouteops.coldchain.packout | cold-chain packout | PROCESS | Packout selects cooler, gel packs, separator, temperature indicator and route duration limit. | Controls exposure. |
| prescriptionrouteops.coldchain.excursion_note | excursion note | RECORD | Excursion note records time outside target conditions and pharmacy guidance for disposition. | Supports safe decisions. |
| prescriptionrouteops.routing.priority_score | priority score | MODEL | Priority weighs medical urgency, cold-chain limit, distance, caregiver absence, shelter status and road access. | Orders stops fairly. |
| prescriptionrouteops.routing.zone_group | zone group | MODEL | Zone group clusters requests by pharmacy, shelter, neighborhood, road detour and driver availability. | Saves time and fuel. |
| prescriptionrouteops.routing.route_manifest | route manifest | RECORD | Manifest lists coded stops, package counts, custody notes, contact instructions and proof requirements. | Guides drivers. |
| prescriptionrouteops.routing.access_check | access check | PROCESS | Access check reviews road closures, curfews, security zones, fuel limits and daylight constraints. | Avoids unsafe trips. |
| prescriptionrouteops.driver.assignment | driver assignment | RECORD | Assignment records driver, vehicle, credential status, route segment and backup contact. | Creates accountability. |
| prescriptionrouteops.driver.briefing | driver briefing | PROCESS | Briefing covers privacy, custody, temperature handling, refusal handling and emergency escalation. | Standardizes conduct. |
| prescriptionrouteops.driver.safety_stop | safety stop | CONTROL | Safety stop halts delivery when threats, inaccessible roads or unclear recipient identity appear. | Protects staff and supplies. |
| prescriptionrouteops.delivery.identity_match | identity match | CONTROL | Identity match confirms recipient or authorized proxy using approved nonpublic details. | Prevents wrong-person handoff. |
| prescriptionrouteops.delivery.handoff_proof | handoff proof | RECORD | Handoff proof records time, recipient role, coded package count and signature or alternate confirmation. | Closes custody. |
| prescriptionrouteops.delivery.proxy_release | proxy release | CONTROL | Proxy release documents caregiver, shelter nurse or caseworker authority when patient cannot receive directly. | Handles real conditions. |
| prescriptionrouteops.delivery.no_contact | no-contact method | PROCESS | No-contact method uses approved secure placement only when policy and patient consent allow it. | Reduces exposure. |
| prescriptionrouteops.failed.no_answer | no-answer attempt | STATE | No-answer attempt records call, door attempt, time, driver note and next action. | Prevents silent failure. |
| prescriptionrouteops.failed.address_issue | address issue | STATE | Address issue flags missing unit, changed shelter bed, unsafe site or contradictory directions. | Triggers correction. |
| prescriptionrouteops.failed.return_to_pharmacy | return to pharmacy | PROCESS | Return process sends undelivered medication back to pharmacy or secure cache with custody documentation. | Protects chain of custody. |
| prescriptionrouteops.privacy.minimum_data | minimum data | CONTROL | Minimum data limits driver-visible details to route need, contact method, package count and handoff rule. | Reduces sensitive exposure. |
| prescriptionrouteops.privacy.status_channel | status channel | CONTROL | Status channel defines who may receive pickup, out-for-delivery, failed-delivery and delivered updates. | Avoids oversharing. |
| prescriptionrouteops.privacy.record_masking | record masking | CONTROL | Masking keeps medication names out of dispatch boards when not necessary for safe handling. | Protects health privacy. |
| prescriptionrouteops.records.case_file | case file | RECORD | Case file links request, consent, pharmacy release, route manifest, proof and closure notes. | Supports audit. |
| prescriptionrouteops.records.exception_log | exception log | RECORD | Exception log captures shortages, delays, exposure events, refusal, failed delivery and safety incidents. | Improves control. |
| prescriptionrouteops.records.reconciliation | reconciliation | PROCESS | Reconciliation compares requested packages, picked-up packages, delivered packages and returns. | Finds missing items. |
| prescriptionrouteops.coordination.prescriber_contact | prescriber contact | PROCESS | Prescriber contact routes refill authorization or replacement questions through approved clinical channels. | Solves prescription blockers. |
| prescriptionrouteops.coordination.shelter_med_desk | shelter medical desk | PROCESS | Shelter desk coordination aligns delivery with resident location, privacy rules and medical support hours. | Improves handoff. |
| prescriptionrouteops.coordination.pharmacy_network | pharmacy network | MODEL | Network maps open pharmacies, outage status, delivery partners, cold-chain capacity and contact reliability. | Guides routing. |
| prescriptionrouteops.communication.patient_update | patient update | PROCESS | Update gives concise status, expected window, failed-attempt process and callback route. | Reduces anxiety. |
| prescriptionrouteops.communication.delay_notice | delay notice | PROCESS | Delay notice explains access, pharmacy, weather or security cause without exposing medication details. | Maintains trust. |
| prescriptionrouteops.metrics.delivery_rate | delivery rate | METRIC | Delivery rate tracks completed handoffs against route attempts and request volume. | Measures service. |
| prescriptionrouteops.metrics.failed_reason_mix | failed reason mix | METRIC | Mix groups no answer, address issue, pharmacy delay, access closure, safety stop and return. | Shows bottlenecks. |
| prescriptionrouteops.metrics.coldchain_compliance | cold-chain compliance | METRIC | Compliance tracks temperature-sensitive packages delivered within handling limits. | Protects quality. |
| prescriptionrouteops.closeout.patient_confirmation | patient confirmation | PROCESS | Confirmation verifies receipt, identifies remaining barriers and records whether follow-up is needed. | Closes loop. |
| prescriptionrouteops.closeout.after_action | after-action note | RECORD | After-action note captures route lessons, partner issues, privacy concerns and improvement tasks. | Improves next activation. |
