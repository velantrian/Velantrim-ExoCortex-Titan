# BATCH 377: Emergency Procurement Operations

**KnowledgeUnits:** 44  
**Namespace:** `emergprocops.*`  
**Scope:** urgent requisitions, vendor checks, approvals, delivery proof, exceptions and audit.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| emergprocops.intake.requisition_id | requisition ID | RECORD | Requisition ID links request, incident, item, requester, funding and status. | Tracks urgent buying. |
| emergprocops.intake.mission_need | mission need | RECORD | Need describes operational problem, quantity, delivery deadline and consequence. | Justifies urgency. |
| emergprocops.intake.priority | priority level | MODEL | Priority reflects life safety, continuity, scarcity, deadline and command direction. | Orders scarce procurement work. |
| emergprocops.intake.specification | specification | RECORD | Specification defines acceptable product/service, standards and substitution limits. | Reduces wrong purchases. |
| emergprocops.authority.emergency_declaration | emergency authority | CONSTRAINT | Emergency procurement relies on declared authority or policy trigger. | Keeps purchases lawful. |
| emergprocops.authority.approval_path | approval path | METHOD | Approval path states requester, finance, procurement, legal and incident command roles. | Speeds controlled action. |
| emergprocops.authority.threshold | threshold rule | CONSTRAINT | Dollar thresholds define quote, competition, waiver and signature requirements. | Controls risk. |
| emergprocops.authority.documentation | authority documentation | RECORD | File records why normal process could not meet mission need. | Supports audit. |
| emergprocops.vendor.vendor_id | vendor ID | RECORD | Vendor ID links supplier, contacts, tax, banking, certifications and performance. | Creates vendor trace. |
| emergprocops.vendor.responsibility | responsibility check | QUALITY_CHECK | Check reviews sanctions, debarment, license, insurance and conflict where feasible. | Avoids bad vendors. |
| emergprocops.vendor.capacity | capacity check | METHOD | Capacity checks inventory, staffing, delivery ability and lead time. | Prevents empty promises. |
| emergprocops.vendor.conflict | conflict disclosure | SAFETY_RULE | Conflicts of interest are documented and escalated. | Protects integrity. |
| emergprocops.sourcing.quote | quote process | METHOD | Quotes are obtained when time and market allow. | Preserves value. |
| emergprocops.sourcing.single_source | single-source justification | RECORD | Justification explains why only one vendor is practical. | Makes exception reviewable. |
| emergprocops.sourcing.market_scan | market scan | METHOD | Fast market scan checks availability, price reasonableness and alternatives. | Reduces price abuse. |
| emergprocops.sourcing.substitution | substitution | METHOD | Substitutions are approved when equivalent and mission-safe. | Keeps response moving. |
| emergprocops.contract.purchase_order | purchase order | RECORD | PO records vendor, item, price, terms, funding, delivery and approver. | Controls obligation. |
| emergprocops.contract.emergency_terms | emergency terms | CONSTRAINT | Terms cover delivery, cancellation, liability, insurance and inspection. | Reduces dispute. |
| emergprocops.contract.verbal_order | verbal order control | METHOD | Verbal emergency orders are documented and converted to written record quickly. | Handles speed without losing control. |
| emergprocops.contract.change_order | change order | METHOD | Changes record scope, price, time, reason and approval. | Prevents uncontrolled growth. |
| emergprocops.finance.funding_source | funding source | RECORD | Funding source links budget, grant, disaster code or reimbursement category. | Supports finance. |
| emergprocops.finance.cost_reasonable | cost reasonableness | QUALITY_CHECK | Price is checked against quotes, catalog, history or market constraint. | Reduces overpayment. |
| emergprocops.finance.advance | advance payment | CONSTRAINT | Advance payment requires higher review and risk controls. | Protects funds. |
| emergprocops.finance.tax_exempt | tax exemption | METHOD | Tax exemption or public status is applied where appropriate. | Avoids unnecessary cost. |
| emergprocops.delivery.delivery_proof | delivery proof | RECORD | Proof records item, quantity, condition, time, receiver and location. | Confirms receipt. |
| emergprocops.delivery.partial | partial delivery | METHOD | Partial delivery records backorder, substitutions and remaining need. | Keeps mission aware. |
| emergprocops.delivery.inspection | inspection | QUALITY_CHECK | Inspection checks quantity, quality, damage, expiration and specification. | Prevents bad acceptance. |
| emergprocops.delivery.discrepancy | discrepancy | RECORD | Discrepancy logs shortage, overage, damage, wrong item or late delivery. | Starts correction. |
| emergprocops.inventory.handoff | inventory handoff | METHOD | Received goods hand off to logistics, warehouse or using department. | Avoids lost supplies. |
| emergprocops.inventory.asset_tag | asset tag | RECORD | Durable equipment receives asset tag or control number. | Supports property control. |
| emergprocops.inventory.consumable | consumable issue | RECORD | Consumables record issue location, quantity and mission use where needed. | Supports reimbursement. |
| emergprocops.compliance.waiver | procurement waiver | RECORD | Waiver cites policy section, reason, approver and duration. | Makes exception auditable. |
| emergprocops.compliance.debarment | debarment check | SAFETY_RULE | Debarment or sanctions check is completed before or promptly after emergency award. | Protects grant eligibility. |
| emergprocops.compliance.small_business | socioeconomic note | METHOD | Emergency buying may still record local, small or disadvantaged vendor use. | Supports policy reporting. |
| emergprocops.compliance.record_retention | record retention | CONSTRAINT | Records follow procurement, finance, grant and disaster retention rules. | Preserves audit trail. |
| emergprocops.risk.fraud_flag | fraud flag | MODEL | Red flags include inflated price, shell vendor, conflict, duplicate invoice or false delivery. | Targets review. |
| emergprocops.risk.vendor_failure | vendor failure | FAILURE_MODE | Failure includes non-delivery, poor quality, unsafe goods or abandoned work. | Triggers contingency. |
| emergprocops.risk.contingency | contingency supplier | METHOD | Backup suppliers are identified for critical goods. | Reduces mission failure. |
| emergprocops.audit.file_complete | file completeness | QUALITY_CHECK | File includes need, authority, vendor, price, PO, delivery, invoice and payment. | Prepares audit. |
| emergprocops.audit.invoice_match | three-way match | QUALITY_CHECK | Invoice is matched to PO and receipt before payment. | Prevents improper payment. |
| emergprocops.metrics.cycle_time | procurement cycle time | MEASUREMENT | Cycle time measures requisition-to-delivery. | Shows responsiveness. |
| emergprocops.metrics.spend | emergency spend | MEASUREMENT | Spend tracks category, vendor, funding and mission. | Supports oversight. |
| emergprocops.closeout.contract_close | contract closeout | METHOD | Closeout confirms delivery, payment, disputes, warranties and records. | Ends purchase cleanly. |
| emergprocops.review.after_action | after-action review | METHOD | Review captures bottlenecks, vendor issues, pricing and policy gaps. | Improves emergency buying. |
