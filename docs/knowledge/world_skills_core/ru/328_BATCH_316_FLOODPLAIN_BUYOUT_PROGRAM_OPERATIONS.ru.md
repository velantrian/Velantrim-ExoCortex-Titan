# BATCH 316: Floodplain Buyout Program Operations

**KnowledgeUnits:** 44  
**Namespace:** `floodbuyoutops.*`  
**Scope:** eligibility, appraisals, offers, relocation, demolition, deed restrictions, grants and monitoring.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| floodbuyoutops.intake.property_interest | property interest | RECORD | Intake captures owner, parcel, flood history, occupancy, structure type and voluntary interest. | Buyout begins as voluntary program record, not forced acquisition. |
| floodbuyoutops.intake.flood_history | flood history file | RECORD | Claims, high-water marks, photos, repair permits and disaster records are assembled. | Demonstrates repetitive loss and benefit justification. |
| floodbuyoutops.intake.owner_contact | owner contact log | RECORD | All calls, letters, meetings and decisions are logged with date and staff. | Keeps communication transparent across long program timelines. |
| floodbuyoutops.eligibility.fema_rule | grant eligibility rule | CONSTRAINT | Eligibility depends on grant program, hazard mitigation purpose, ownership and documentation. | Prevents spending effort on parcels that cannot be reimbursed. |
| floodbuyoutops.eligibility.voluntary | voluntary participation | SAFETY_RULE | Owner participation must remain voluntary unless a separate legal process exists. | Protects trust and program legality. |
| floodbuyoutops.eligibility.cost_benefit | cost-benefit screen | MODEL | Benefit-cost analysis compares avoided future damage with acquisition and restoration costs. | Helps rank projects for funding. |
| floodbuyoutops.eligibility.environmental_review | environmental review | CONSTRAINT | Historic, environmental, floodplain, wetlands and contamination reviews may be required. | Acquisition cannot skip compliance. |
| floodbuyoutops.appraisal.appraiser_selection | appraiser selection | METHOD | Qualified appraisers follow program standards and conflict rules. | Fair market value must be defensible. |
| floodbuyoutops.appraisal.pre_flood_value | pre-flood value | MODEL | Some programs use pre-event market value under defined rules. | Affects owner offer and fairness after disaster damage. |
| floodbuyoutops.appraisal.review_appraisal | review appraisal | QUALITY_CHECK | Independent review checks method, comparables, assumptions and parcel details. | Reduces disputes and audit findings. |
| floodbuyoutops.appraisal.owner_appeal | owner appeal | METHOD | Owner can provide evidence or request reconsideration per program policy. | Builds due process into valuation. |
| floodbuyoutops.offer.offer_packet | offer packet | RECORD | Packet includes value, eligible costs, conditions, timeline, relocation info and contacts. | Owner understands decision before signing. |
| floodbuyoutops.offer.acceptance | offer acceptance | RECORD | Acceptance is documented with signatures, contingencies and required next steps. | Moves parcel into closing workflow. |
| floodbuyoutops.offer.withdrawal | withdrawal option | DECISION_RULE | Owner may withdraw before binding closing under program terms. | Supports voluntary nature. |
| floodbuyoutops.offer.duplication_benefits | duplication of benefits | QUALITY_CHECK | Insurance, grants and other aid are checked to avoid duplicate public payment. | Protects grant compliance. |
| floodbuyoutops.relocation.advisory | relocation advisory | METHOD | Staff provide information on housing options, benefits, timelines and documentation. | Helps households move without losing program deadlines. |
| floodbuyoutops.relocation.tenant_notice | tenant notice | SAFETY_RULE | Tenants receive required notices and relocation protections where applicable. | Buyout programs affect residents beyond owners. |
| floodbuyoutops.relocation.special_needs | special needs coordination | METHOD | Elderly, disabled or low-income residents may need case management and referrals. | Reduces harm during displacement from risk areas. |
| floodbuyoutops.closing.title_search | title search | QUALITY_CHECK | Title search identifies liens, easements, heirs, mortgages and ownership defects. | Clean title is needed before acquisition. |
| floodbuyoutops.closing.closing_docs | closing documents | RECORD | Deed, settlement statement, grant forms, releases and payment records are retained. | Creates auditable acquisition file. |
| floodbuyoutops.closing.mortgage_payoff | mortgage payoff | METHOD | Lienholders are paid or released according to closing instructions. | Prevents unresolved claims on acquired land. |
| floodbuyoutops.demolition.utility_disconnect | utility disconnect | METHOD | Gas, electric, water, sewer and telecom are disconnected before demolition. | Protects workers and infrastructure. |
| floodbuyoutops.demolition.asbestos_survey | asbestos survey | CONSTRAINT | Structures may require asbestos, lead or hazardous material survey. | Demolition must not create health hazards. |
| floodbuyoutops.demolition.contractor_procurement | demolition procurement | METHOD | Contractors are selected with scope, insurance, permits, debris rules and schedule. | Makes demolition controlled and grant-compliant. |
| floodbuyoutops.demolition.site_clearance | site clearance | QUALITY_CHECK | Final clearance verifies structure removal, debris disposal, grading and stabilization. | Parcel becomes safe open space. |
| floodbuyoutops.deed.open_space_restriction | open-space restriction | CONSTRAINT | Deed restriction usually limits future development and enclosed structures. | Ensures mitigation benefit persists. |
| floodbuyoutops.deed.allowed_use | allowed use | DECISION_RULE | Allowed uses may include parks, trails, agriculture or habitat if compatible with flood storage. | Land remains useful without recreating flood risk. |
| floodbuyoutops.deed.recording | deed recording | RECORD | Restriction is recorded with county or land records and linked to grant file. | Future owners see permanent limits. |
| floodbuyoutops.deed.encroachment_check | encroachment check | INSPECTION | Post-buyout land is checked for dumping, sheds, fences or unauthorized fill. | Protects open-space covenant. |
| floodbuyoutops.grant.application | grant application | RECORD | Application includes scope, budget, maps, benefit-cost, properties, schedule and compliance. | Funding approval depends on complete package. |
| floodbuyoutops.grant.match_tracking | match tracking | RECORD | Local match, in-kind, administrative costs and eligible expenses are tracked separately. | Prevents reimbursement errors. |
| floodbuyoutops.grant.reimbursement | reimbursement request | METHOD | Requests include invoices, proof of payment, closing docs, demolition records and progress. | Converts local spending into grant cash flow. |
| floodbuyoutops.grant.scope_change | scope change | METHOD | Property list, budget or schedule changes require grant approval where applicable. | Avoids unsupported costs. |
| floodbuyoutops.grant.audit_file | audit file | RECORD | Audit file preserves eligibility, procurement, environmental, financial and closeout documents. | Makes multi-year program defensible. |
| floodbuyoutops.community.public_meeting | public meeting | METHOD | Meetings explain voluntary process, timelines, land future and contacts. | Reduces rumor and supports informed decisions. |
| floodbuyoutops.community.equity_review | equity review | QUALITY_CHECK | Review checks whether outreach and benefits reach vulnerable communities fairly. | Avoids mitigation that helps only easier parcels. |
| floodbuyoutops.community.neighbor_issue | neighbor issue log | RECORD | Adjacent owners may report weeds, drainage, trespass or maintenance concerns. | Buyout land still needs local stewardship. |
| floodbuyoutops.monitoring.annual_inspection | annual inspection | INSPECTION | Annual visits check open-space use, vegetation, dumping, erosion and restriction compliance. | Ensures land stays compliant after closeout. |
| floodbuyoutops.monitoring.maintenance_plan | maintenance plan | METHOD | Plan covers mowing, invasive control, trash, signage, access and habitat goals. | Prevents vacant lots from becoming neglected. |
| floodbuyoutops.monitoring.flood_storage | flood storage function | MODEL | Open parcels preserve flood conveyance, storage and reduced exposure. | Program success is risk reduction, not only demolition count. |
| floodbuyoutops.reporting.closeout | grant closeout | RECORD | Closeout summarizes acquired parcels, costs, restrictions, demolition and monitoring obligations. | Formally completes funding cycle. |
| floodbuyoutops.reporting.dashboard | program dashboard | RECORD | Dashboard tracks interested, eligible, appraised, offered, closed, demolished and monitored parcels. | Shows bottlenecks in a complex pipeline. |
| floodbuyoutops.reporting.lessons | lessons learned | METHOD | Staff review outreach, appraisal disputes, contractor issues, grant delays and maintenance. | Improves next disaster recovery cycle. |
| floodbuyoutops.risk.residual_risk | residual risk | MODEL | Buyouts reduce property exposure but do not eliminate flooding for roads or remaining structures. | Keeps community planning realistic. |

