# BATCH 343: Utility Website and Service Status Content Operations

**KnowledgeUnits:** 44  
**Namespace:** `statuscontentops.*`  
**Scope:** alerts, banners, outage pages, FAQs, publishing approvals, timestamps and archives.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| statuscontentops.intake.content_request | content request | RECORD | A content request records event, audience, urgency, owner and desired channel. | Creates controlled intake for public updates. |
| statuscontentops.intake.trigger_type | trigger type | RECORD | Trigger distinguishes outage, planned work, boil notice, billing issue, portal issue or general advisory. | Routes content to the right template. |
| statuscontentops.intake.severity | severity level | MODEL | Severity ranks customer impact, safety risk, service disruption and public visibility. | Determines banner prominence and approval path. |
| statuscontentops.intake.audience | audience segment | RECORD | Audience segment identifies affected geography, customer class, language and accessibility needs. | Avoids broadcasting vague or irrelevant notices. |
| statuscontentops.source.authoritative_feed | authoritative feed | CONSTRAINT | Content should rely on approved OMS, work order, water quality, billing or incident sources. | Prevents rumor-based publishing. |
| statuscontentops.source.field_confirmation | field confirmation | QUALITY_CHECK | Field or control-room confirmation is required for operational facts when available. | Reduces wrong public statements. |
| statuscontentops.source.timestamp_source | timestamp source | RECORD | Source timestamp is stored separately from web publication timestamp. | Shows when information was known. |
| statuscontentops.template.banner | alert banner | METHOD | Banner template contains headline, affected area, action, status and next update time. | Gives customers fast scannable information. |
| statuscontentops.template.status_page | status page block | METHOD | Status page block separates current status, customer action, map, updates and contact path. | Keeps disruption pages coherent. |
| statuscontentops.template.faq | FAQ entry | METHOD | FAQ entry answers likely customer questions with approved plain-language wording. | Reduces call volume. |
| statuscontentops.template.safety_notice | safety notice | SAFETY_RULE | Safety notices emphasize immediate protective action, uncertainty and official contact routes. | Prevents harmful misinterpretation. |
| statuscontentops.template.accessibility | accessibility wording | CONSTRAINT | Content avoids image-only text and supports screen readers, contrast and plain language. | Keeps public notices usable. |
| statuscontentops.approval.owner | content owner | RECORD | Owner signs off operational accuracy and final wording. | Makes accountability explicit. |
| statuscontentops.approval.legal_review | legal review trigger | CONSTRAINT | Legal or compliance review is triggered for liability, privacy, regulatory or enforcement language. | Reduces disclosure risk. |
| statuscontentops.approval.fast_track | fast-track approval | METHOD | Emergency updates may use a pre-approved template and duty officer approval. | Publishes urgent facts quickly. |
| statuscontentops.approval.version_note | version note | RECORD | Each approved version records editor, approver, time and reason. | Supports audit and later review. |
| statuscontentops.publishing.channel_selection | channel selection | METHOD | Web page, banner, social, email, SMS and IVR are chosen by audience and urgency. | Matches channel to customer need. |
| statuscontentops.publishing.homepage_banner | homepage banner | METHOD | Homepage banner is used for broad or high-risk service issues. | Makes critical notices visible. |
| statuscontentops.publishing.outage_map_link | outage map link | METHOD | Status content links to the outage map only when map data is reliable enough. | Avoids sending customers to misleading tools. |
| statuscontentops.publishing.cache_control | cache control | QUALITY_CHECK | Cache, CDN and browser behavior are checked after publishing urgent updates. | Prevents stale public information. |
| statuscontentops.publishing.mobile_check | mobile check | QUALITY_CHECK | Published content is checked on mobile width and low-bandwidth assumptions. | Many customers view during disruption. |
| statuscontentops.update.next_update_time | next update time | RECORD | Notice states when the next update is expected, even if facts are unchanged. | Sets customer expectations. |
| statuscontentops.update.no_change | no-change update | METHOD | No-change update confirms that the utility is still monitoring or repairing. | Reduces uncertainty during long events. |
| statuscontentops.update.etr_change | ETR change note | METHOD | Estimated restoration time changes explain confidence, cause and affected area. | Helps customers plan. |
| statuscontentops.update.partial_restoration | partial restoration | METHOD | Partial restoration content distinguishes restored, still affected and newly affected groups. | Avoids false all-clear messages. |
| statuscontentops.translation.language_queue | language queue | METHOD | Translation queue prioritizes legally required and high-volume languages. | Improves equitable access. |
| statuscontentops.translation.approved_terms | approved terms | RECORD | Approved utility terms preserve meaning for outage, pressure, safety and billing concepts. | Keeps translations consistent. |
| statuscontentops.translation.review | translation review | QUALITY_CHECK | Translated urgent content is reviewed against source facts and critical actions. | Prevents dangerous wording drift. |
| statuscontentops.archive.snapshot | publication snapshot | RECORD | Snapshot preserves page, banner, files and publication time. | Supports records requests and investigations. |
| statuscontentops.archive.retention | retention rule | CONSTRAINT | Status content is retained according to public records and incident retention schedules. | Keeps evidence available. |
| statuscontentops.archive.retire_notice | retire notice | METHOD | Notice is retired or moved to archive after closeout and replacement content is live. | Prevents outdated alerts. |
| statuscontentops.monitoring.analytics | web analytics | MEASUREMENT | Page views, search terms, clicks and referrers show customer information demand. | Guides future content design. |
| statuscontentops.monitoring.call_deflection | call deflection | MODEL | Call volume before/after publishing can indicate whether content answered customer questions. | Measures operational value. |
| statuscontentops.monitoring.error_reports | error reports | RECORD | Staff and customers can report incorrect or confusing content. | Creates correction path. |
| statuscontentops.correction.correction_notice | correction notice | METHOD | Material mistakes are corrected with visible updated wording and timestamp. | Maintains trust. |
| statuscontentops.correction.retraction | retraction | METHOD | Retraction removes unsafe or false content and records why. | Limits harm from bad information. |
| statuscontentops.integration.crm_note | CRM note link | RECORD | Customer-facing content references related CRM knowledge articles or scripts. | Aligns website and call center answers. |
| statuscontentops.integration.incident_bridge | incident bridge | METHOD | Incident command or control-room status feeds the web update cadence. | Keeps public messaging tied to operations. |
| statuscontentops.integration.social_sync | social sync | METHOD | Social posts mirror approved web facts and link back to canonical status page. | Reduces fragmented messaging. |
| statuscontentops.qa.link_check | link check | QUALITY_CHECK | Links, maps, files, forms and contact numbers are checked after publishing. | Avoids broken crisis information. |
| statuscontentops.qa.timezone_check | timezone check | QUALITY_CHECK | Times include timezone and date where ambiguity is possible. | Prevents scheduling confusion. |
| statuscontentops.qa.access_log | access log | RECORD | CMS access log tracks who changed status content. | Supports accountability. |
| statuscontentops.closeout.post_event_review | post-event review | METHOD | Major content events are reviewed for speed, accuracy, accessibility and customer feedback. | Improves future notices. |
| statuscontentops.governance.editor_roster | editor roster | RECORD | Roster names trained staff allowed to publish status content. | Prevents uncontrolled editing. |
