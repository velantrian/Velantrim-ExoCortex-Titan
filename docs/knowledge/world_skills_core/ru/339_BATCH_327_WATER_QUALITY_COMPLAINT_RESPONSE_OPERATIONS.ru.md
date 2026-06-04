# BATCH 327: Water Quality Complaint Response Operations

**KnowledgeUnits:** 44  
**Namespace:** `wqcomplaintops.*`  
**Scope:** intake, discoloration, taste/odor, pressure, sampling, flushing, customer communication and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| wqcomplaintops.intake.case_id | complaint case ID | RECORD | Каждой жалобе назначают case ID, адрес, account, caller, time and concern type. | Связывает field response, samples and customer follow-up. |
| wqcomplaintops.intake.concern_type | concern type | RECORD | Complaint categorized as discoloration, taste, odor, particles, pressure, illness concern or service issue. | Determines first response path. |
| wqcomplaintops.intake.time_pattern | time pattern | RECORD | Intake records whether issue is constant, first draw, after construction, after flushing or seasonal. | Pattern often indicates premise versus distribution source. |
| wqcomplaintops.intake.neighbor_check | neighbor check | METHOD | Staff ask whether neighbors or nearby accounts have similar symptoms. | Distinguishes local plumbing from main-scale event. |
| wqcomplaintops.intake.risk_screen | risk screen | DECISION_RULE | Illness, chemical odor, fuel smell or widespread pressure loss triggers escalation. | Separates routine aesthetic complaints from potential public health events. |
| wqcomplaintops.discoloration.color_note | color note | OBSERVATION | Brown, red, black, white or blue-green water suggests different source hypotheses. | Guides sampling and field investigation. |
| wqcomplaintops.discoloration.first_draw | first-draw issue | MODEL | Discoloration only after stagnation often points to premise plumbing or service line. | Avoids unnecessary main flushing when house plumbing is source. |
| wqcomplaintops.discoloration.system_disturbance | system disturbance | FAILURE_MODE | Valve work, hydrant use, main break or flow reversal can mobilize sediment. | Explains clustered calls after operations. |
| wqcomplaintops.discoloration.black_particles | black particles | OBSERVATION | Black particles may come from rubber gaskets, manganese, carbon filters or water heaters. | Prevents single-cause assumptions. |
| wqcomplaintops.tasteodor.chlorine | chlorine taste | OBSERVATION | Chlorine smell can increase after booster changes, low demand or source-water changes. | May be normal within limits but needs communication. |
| wqcomplaintops.tasteodor.earthy | earthy odor | OBSERVATION | Earthy or musty odor can indicate geosmin/MIB from source water or reservoirs. | Often aesthetic but can generate many calls. |
| wqcomplaintops.tasteodor.rotten_egg | rotten egg odor | OBSERVATION | Sulfur odor at hot tap only often points to water heater conditions. | Field staff can isolate premise issue. |
| wqcomplaintops.tasteodor.fuel_chemical | fuel or chemical odor | SAFETY_RULE | Fuel-like odor requires rapid escalation, sampling and possible advisory review. | Some odors may indicate hazardous contamination. |
| wqcomplaintops.pressure.low_pressure | low pressure complaint | METHOD | Response checks nearby work, pressure zone, valves, pumps, PRVs and service blockage. | Low pressure can be service issue or system event. |
| wqcomplaintops.pressure.air_in_water | air in water | OBSERVATION | Milky water that clears from bottom upward usually indicates entrained air. | Helps reassure while checking recent main work. |
| wqcomplaintops.pressure.surge | pressure surge | FAILURE_MODE | Customer reports of banging or sudden flow changes may indicate transient pressure. | Can point to valve operation or pump control issues. |
| wqcomplaintops.sampling.sample_plan | complaint sample plan | METHOD | Sampling plan selects tap, first draw/flushed, upstream/downstream and parameters. | Samples must match the hypothesis. |
| wqcomplaintops.sampling.chain | sample chain | RECORD | Complaint samples get ID, time, collector, location, preservation and custody record. | Makes results traceable and defensible. |
| wqcomplaintops.sampling.field_tests | field tests | MEASUREMENT | Field checks may include chlorine residual, temperature, pH, turbidity and odor note. | Gives immediate context before lab results. |
| wqcomplaintops.sampling.bacti_trigger | bacti trigger | DECISION_RULE | Bacteriological sampling is triggered by pressure loss, main break, intrusion risk or illness cluster. | Focuses lab work on public health risk. |
| wqcomplaintops.field.hydrant_flush | hydrant flushing | METHOD | Targeted flushing clears local mains after confirming direction and downstream impact. | Can resolve sediment but may spread discoloration if done poorly. |
| wqcomplaintops.field.service_flush | service line flush | METHOD | Service flush checks whether issue clears at customer-side or utility-side point. | Helps locate source between main, service and premise. |
| wqcomplaintops.field.valve_check | valve status check | METHOD | Field crews verify valve positions and recent operations near complaint cluster. | Mispositioned valves can create stagnant water. |
| wqcomplaintops.field.dead_end_check | dead-end check | INSPECTION | Dead-end mains are checked for low residual, sediment and flushing need. | Chronic complaints often cluster at low-turnover ends. |
| wqcomplaintops.communication.initial_response | initial response | METHOD | Customer receives case number, expected response time and basic safety guidance. | Reduces anxiety and repeat calls. |
| wqcomplaintops.communication.plain_language | plain-language explanation | METHOD | Staff explain possible causes without overpromising before evidence. | Maintains trust during investigation. |
| wqcomplaintops.communication.advisory_link | advisory link | DECISION_RULE | If conditions meet advisory criteria, communications shift to official public notice process. | Keeps complaint workflow aligned with emergency rules. |
| wqcomplaintops.communication.followup | follow-up call | METHOD | Follow-up reports field findings, sample status, action taken and next steps. | Closes the loop with the customer. |
| wqcomplaintops.cluster.cluster_detection | complaint cluster | MODEL | Multiple nearby complaints within a time window indicate possible distribution event. | Triggers map review and coordinated response. |
| wqcomplaintops.cluster.operations_overlay | operations overlay | METHOD | Complaint map is compared with flushing, breaks, valve work, hydrant use and source changes. | Connects symptoms to utility activity. |
| wqcomplaintops.cluster.priority_area | priority area | DECISION_RULE | Sensitive facilities, illness concerns and widespread clusters receive faster response. | Protects higher-risk customers first. |
| wqcomplaintops.records.case_notes | case notes | RECORD | Notes capture actions, names, times, photos, sample IDs, results and customer contacts. | Creates audit trail. |
| wqcomplaintops.records.result_link | result link | RECORD | Lab and field results are linked to the complaint case and map. | Prevents orphaned data. |
| wqcomplaintops.records.closeout_code | closeout code | RECORD | Closeout code identifies cause: premise plumbing, main sediment, operations, unknown or resolved. | Enables trend analysis. |
| wqcomplaintops.qa.response_time | response time metric | MEASUREMENT | Time from intake to first action and closeout is measured. | Shows customer service performance. |
| wqcomplaintops.qa.repeat_complaint | repeat complaint check | QUALITY_CHECK | Repeated complaints at same address or area are flagged for deeper review. | Prevents superficial closure of chronic issues. |
| wqcomplaintops.qa.sample_validity | sample validity | QUALITY_CHECK | Sample results are reviewed for location, method, holding time and context. | Avoids acting on poor samples. |
| wqcomplaintops.corrective.flushing_plan | corrective flushing plan | METHOD | Recurrent sediment complaints may lead to scheduled flushing or UDF route change. | Turns reactive response into preventive maintenance. |
| wqcomplaintops.corrective.corrosion_review | corrosion review | METHOD | Metallic taste, blue-green stains or lead/copper concerns trigger corrosion-control review. | Connects complaints to chemistry and materials. |
| wqcomplaintops.corrective.source_change | source change review | METHOD | Taste/odor events after source or treatment change are analyzed with operations data. | Explains system-wide aesthetic shifts. |
| wqcomplaintops.reporting.trend_report | trend report | RECORD | Reports summarize counts by type, area, cause, season and resolution. | Helps managers target infrastructure or treatment fixes. |
| wqcomplaintops.reporting.public_faq | public FAQ | METHOD | Common complaint causes and safe steps are documented for customer-facing staff. | Improves consistency of answers. |
| wqcomplaintops.reporting.management_alert | management alert | DECISION_RULE | Unusual clusters, illness claims or chemical odors generate management alert. | Ensures leadership sees potential high-risk events. |
| wqcomplaintops.review.lessons | lessons learned | METHOD | After notable events, staff review intake, field actions, samples, communications and closeout. | Improves future complaint response. |

