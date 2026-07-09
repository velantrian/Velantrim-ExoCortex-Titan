# BATCH 358: Community Resource Directory Maintenance Operations

**KnowledgeUnits:** 44  
**Namespace:** `resourcedirops.*`  
**Scope:** provider records, eligibility, hours, capacity, verification, taxonomy and updates.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| resourcedirops.provider.provider_id | provider ID | RECORD | Provider ID links organization, sites, services, contacts and verification history. | Creates stable directory record. |
| resourcedirops.provider.organization | organization record | RECORD | Organization record stores legal name, public name, parent agency and service area. | Prevents duplicate listings. |
| resourcedirops.provider.site | site record | RECORD | Site record stores address, phone, accessibility, hours and geographic coordinates. | Supports accurate referral. |
| resourcedirops.provider.contact_owner | contact owner | RECORD | Contact owner is the person or role responsible for updates. | Makes verification possible. |
| resourcedirops.service.service_taxonomy | service taxonomy | MODEL | Taxonomy classifies food, housing, health, legal, benefits, transport and crisis resources. | Makes search consistent. |
| resourcedirops.service.service_record | service record | RECORD | Service record describes what is offered, to whom, where and how. | Separates site from service. |
| resourcedirops.service.modality | service modality | RECORD | Modality distinguishes walk-in, appointment, phone, online, outreach or mobile service. | Helps users access correctly. |
| resourcedirops.service.boundary | service boundary | CONSTRAINT | Directory states what the provider does not offer or cannot guarantee. | Prevents misleading referrals. |
| resourcedirops.eligibility.criteria | eligibility criteria | RECORD | Criteria include age, residence, income, insurance, identity, documents or issue type. | Avoids wrong referrals. |
| resourcedirops.eligibility.documents | document requirements | RECORD | Requirements list IDs, proofs, applications or referrals needed. | Helps callers prepare. |
| resourcedirops.eligibility.fees | fee information | RECORD | Fee information states free, sliding scale, insurance, copay or donation. | Reduces surprise costs. |
| resourcedirops.eligibility.restrictions | restrictions | CONSTRAINT | Restrictions include waitlists, capacity limits, legal limits or temporary closures. | Keeps referrals realistic. |
| resourcedirops.hours.regular | regular hours | RECORD | Regular hours state days, opening, closing and intake cutoff. | Supports basic access. |
| resourcedirops.hours.holiday | holiday hours | RECORD | Holiday and seasonal exceptions are stored separately. | Prevents stale open/closed status. |
| resourcedirops.hours.emergency | emergency hours | RECORD | Emergency hours may activate during disasters, heat, cold or public health events. | Supports crisis response. |
| resourcedirops.hours.last_confirmed | last confirmed timestamp | RECORD | Last confirmed timestamp shows when hours were verified. | Signals reliability. |
| resourcedirops.capacity.status | capacity status | RECORD | Status shows open, limited, waitlist, full, closed or unknown. | Reduces dead-end referrals. |
| resourcedirops.capacity.update_source | capacity source | RECORD | Source records provider self-update, call verification, API, partner or field report. | Shows confidence. |
| resourcedirops.capacity.expiry | capacity expiry | CONSTRAINT | Time-sensitive capacity status expires after defined period. | Prevents stale availability. |
| resourcedirops.capacity.alert | capacity alert | METHOD | Alert notifies hotline or partners when key resource status changes. | Keeps front line current. |
| resourcedirops.verification.schedule | verification schedule | METHOD | Records are verified on risk-based cycle by service type and change frequency. | Keeps directory fresh. |
| resourcedirops.verification.call_script | verification script | METHOD | Script checks service, eligibility, hours, capacity, contact and accessibility. | Standardizes updates. |
| resourcedirops.verification.failed_contact | failed contact | FAILURE_MODE | Failed verification records attempts, channels and confidence downgrade. | Exposes uncertain listings. |
| resourcedirops.verification.provider_portal | provider portal | METHOD | Providers can submit updates through controlled portal with review. | Speeds maintenance. |
| resourcedirops.update.change_request | change request | RECORD | Change request records proposed edit, source, evidence and reviewer. | Controls modifications. |
| resourcedirops.update.review | editorial review | QUALITY_CHECK | Review checks clarity, taxonomy, duplicates, safety and policy before publish. | Prevents bad directory data. |
| resourcedirops.update.publish | publish workflow | METHOD | Publish workflow changes public record, timestamp and change log. | Makes updates traceable. |
| resourcedirops.update.rollback | rollback | METHOD | Rollback restores prior listing after error or disputed change. | Limits harm. |
| resourcedirops.quality.duplicate | duplicate detection | QUALITY_CHECK | Duplicate detection matches name, address, phone, website and service overlap. | Keeps search clean. |
| resourcedirops.quality.dead_link | dead link check | QUALITY_CHECK | Websites, forms, maps and phone links are checked for failure. | Prevents unusable referrals. |
| resourcedirops.quality.plain_language | plain language | QUALITY_CHECK | Listings use clear public wording rather than internal program names. | Helps users understand. |
| resourcedirops.quality.accessibility | accessibility detail | RECORD | Accessibility records transit, parking, ramps, language, TTY and accommodation process. | Supports equitable access. |
| resourcedirops.search.keyword | keyword synonyms | METHOD | Synonyms connect user language to taxonomy terms. | Improves search discovery. |
| resourcedirops.search.geo_filter | geographic filter | METHOD | Search can filter by distance, jurisdiction, service area or transit access. | Finds relevant nearby help. |
| resourcedirops.search.priority | priority ranking | MODEL | Ranking considers service fit, availability, proximity, eligibility and recency. | Improves referral quality. |
| resourcedirops.search.sensitive_terms | sensitive search terms | SAFETY_RULE | Sensitive categories avoid exposing users or providers to stigma or unsafe disclosure. | Protects privacy and dignity. |
| resourcedirops.integration.hotline | hotline integration | METHOD | Hotline systems use directory records for referral and call notes. | Aligns data with counseling. |
| resourcedirops.integration.casework | casework integration | METHOD | Caseworkers can link referrals and outcomes to directory entries. | Supports closed-loop service. |
| resourcedirops.integration.api | API feed | METHOD | API feed shares approved listings with partner systems. | Reduces duplicate directories. |
| resourcedirops.integration.open_data | public data policy | CONSTRAINT | Public feeds exclude sensitive or restricted provider data. | Controls misuse. |
| resourcedirops.governance.data_owner | data owner | RECORD | Data owner defines taxonomy, standards, verification and publication rules. | Keeps directory accountable. |
| resourcedirops.governance.risk_tier | risk tier | MODEL | High-risk resources like crisis, shelter or medical listings require stricter verification. | Reduces harmful referrals. |
| resourcedirops.metrics.freshness | freshness metric | MEASUREMENT | Freshness measures percent of listings verified within target window. | Shows data health. |
| resourcedirops.closeout.retire_listing | retire listing | METHOD | Closed programs are retired with reason, date and replacement referrals if known. | Prevents obsolete referrals. |
