# BATCH_165 — Broadcast & Media Playout Operations Detail
# world_skills_core · source: world_skills_core:batch_165:broadcast_media_playout_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| playout.schedule.playout_schedule | Playout schedule | invariant | Playout schedule orders programs, ads, promos, live segments and continuity elements by time. | эфирный план |
| playout.schedule.as_run_log | As-run log | invariant | As-run log records what actually aired with times, durations, IDs and exceptions. | доказать эфир |
| playout.schedule.clock_format | Broadcast clock format | variant | Clock format defines repeated hour structure with breaks, programs, IDs and continuity slots. | predictable schedule |
| playout.schedule.break_pattern | Ad break pattern | invariant | Break pattern defines where commercial or promo breaks occur within content and regulatory limits. | ads fit content |
| playout.schedule.late_change | Late schedule change | variant | Late change updates playlist close to air and increases risk of timing, rights or asset errors. | urgent but risky |
| playout.schedule.secondary_event | Secondary event | variant | Secondary event triggers logo, graphic, subtitle, audio change or other automation over main content. | more than video |
| playout.ingest.media_ingest | Media ingest | invariant | Ingest brings media files into playout system with metadata, validation and storage placement. | content enters chain |
| playout.ingest.house_id | House ID | invariant | House ID uniquely identifies asset for scheduling, QC, rights and playback. | one asset identifier |
| playout.ingest.metadata_check | Metadata check | invariant | Metadata check verifies title, duration, language, version, rights, rating and technical details. | wrong data can air wrong item |
| playout.ingest.file_format_check | File format check | invariant | Format check confirms codec, wrapper, frame rate, resolution, audio layout and delivery spec. | technical compatibility |
| playout.ingest.proxy_creation | Proxy creation | variant | Proxy creation makes lower-resolution copies for review, logging or remote workflows. | faster handling |
| playout.ingest.asset_versioning | Asset versioning | invariant | Versioning distinguishes cuts, languages, edits, fixes, captions or regional variants. | avoid airing old version |
| playout.qc.technical_qc | Technical QC | invariant | Technical QC checks audio, video, file structure, loudness, black, freeze, artifacts and compliance markers. | catch defects before air |
| playout.qc.editorial_qc | Editorial QC | variant | Editorial QC checks content suitability, language, graphics, branding, rating and obvious mismatch. | technical pass is not enough |
| playout.qc.loudness_check | Loudness check | invariant | Loudness check verifies audio level against target standard and delivery requirements. | avoid jarring audio |
| playout.qc.caption_qc | Caption QC | invariant | Caption QC checks timing, completeness, language, encoding and readability of subtitles or captions. | accessibility and compliance |
| playout.qc.black_frame_detection | Black frame detection | invariant | Detection identifies unintended black frames or freeze that may indicate content or transfer error. | prevent dead air look |
| playout.qc.qc_fail_workflow | QC fail workflow | invariant | Failure workflow quarantines asset, documents issue, notifies owner and tracks replacement or waiver. | no silent bad asset |
| playout.automation.playlist_load | Playlist load | invariant | Playlist load transfers approved schedule into automation system for controlled playback. | schedule becomes operation |
| playout.automation.event_timing | Event timing | invariant | Timing aligns start, duration, joins and transitions so channel stays on clock. | seconds matter |
| playout.automation.scte_marker | SCTE marker | variant | SCTE marker signals ad insertion, regional break or downstream automation action. | machine-readable break |
| playout.automation.logo_insertion | Logo insertion | variant | Logo insertion overlays channel branding according to schedule, region, content type or rights. | identity on air |
| playout.automation.failover_server | Playout failover server | invariant | Failover server provides backup playback when primary automation or server fails. | continuity resilience |
| playout.automation.manual_takeover | Manual takeover | variant | Manual takeover lets operator control playlist, source, break or emergency content during automation issue. | human fallback |
| playout.live.live_source_booking | Live source booking | invariant | Booking reserves incoming live feed, circuit, satellite, IP stream, studio or contribution path. | live path planned |
| playout.live.line_check | Live line check | invariant | Line check verifies video, audio, latency, return communication and routing before live handoff. | test before air |
| playout.live.countdown | Live countdown | invariant | Countdown coordinates director, master control, talent, source and automation before live join. | shared timing |
| playout.live.live_delay | Live delay | variant | Delay provides buffer for compliance, profanity, technical switching or safety control. | live with guardrail |
| playout.live.breakaway | Breakaway | variant | Breakaway exits live content to scheduled item, emergency content or local programming. | controlled exit |
| playout.live.return_to_schedule | Return to schedule | invariant | Return to schedule realigns playlist after live overrun, underrun or interruption. | recover clock |
| playout.ads.ad_insertion | Ad insertion | invariant | Ad insertion places commercial spots according to schedule, contract, region and technical markers. | revenue in playout |
| playout.ads.copy_rotation | Copy rotation | variant | Copy rotation selects ad versions by campaign rule, frequency, market or legal clearance. | correct creative |
| playout.ads.makegood | Makegood | variant | Makegood compensates missed or faulty ad delivery with replacement airing or commercial arrangement. | repair ad obligation |
| playout.ads.ad_separation | Ad separation | invariant | Separation rules prevent conflicting or duplicate ads from airing too close together. | protect advertiser rules |
| playout.ads.regional_split | Regional split | variant | Regional split sends different ads or content to different markets from one schedule structure. | localize output |
| playout.continuity.dead_air_alarm | Dead-air alarm | invariant | Dead-air alarm detects silence, black, frozen or missing signal conditions requiring immediate response. | protect channel |
| playout.continuity.off_air_monitor | Off-air monitor | invariant | Off-air monitor watches the actual broadcast or stream output rather than only internal playlist. | real viewer signal |
| playout.continuity.emergency_message | Emergency message insertion | variant | Emergency message insertion interrupts or overlays programming under authorized public safety procedure. | priority information |
| playout.continuity.channel_branding | Channel branding check | invariant | Branding check confirms correct logo, bug, graphics, voiceover and regional identity. | avoid wrong channel feel |
| playout.continuity.incident_log | Broadcast incident log | invariant | Incident log records timing, impact, cause, actions, recovery and notifications for on-air faults. | learn and report |
| playout.rights.rights_window | Rights window | invariant | Rights window defines when and where content may be aired or streamed. | avoid unauthorized airing |
| playout.rights.embargo | Embargo | variant | Embargo prevents content release before agreed time, event, region or authorization. | timing restriction |
| playout.rights.content_rating | Content rating | invariant | Content rating affects scheduling, warnings, parental controls and regulatory compliance. | suitability control |
| playout.rights.music_cue_sheet | Music cue sheet | variant | Cue sheet records music used for rights reporting and royalty processing. | downstream rights data |
