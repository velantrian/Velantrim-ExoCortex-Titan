# BATCH 417: Community Tool Lending Library Operations

**KnowledgeUnits:** 44  
**Namespace:** `toollibraryops.*`  
**Scope:** inventory, checkout, safety brief, returns, damage, maintenance and reporting.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| toollibraryops.activation.service_model | service model | RECORD | Model defines fixed library, mobile checkout, recovery center desk or partner cache. | Defines operation. |
| toollibraryops.activation.partner | partner roster | RECORD | Roster lists nonprofits, makerspaces, hardware stores, libraries and volunteer repair groups. | Coordinates capacity. |
| toollibraryops.activation.scope | tool scope | CONSTRAINT | Scope defines allowed tool categories, prohibited tools and user groups. | Controls risk. |
| toollibraryops.activation.command_link | command link | RECORD | Operation reports to donations, logistics, recovery, safety and finance leads. | Maintains oversight. |
| toollibraryops.inventory.item_master | item master | RECORD | Master lists tool ID, type, condition, owner, accessories and restrictions. | Standardizes stock. |
| toollibraryops.inventory.label | label method | METHOD | Labels attach unique ID, category, return point and safety marker. | Tracks tools. |
| toollibraryops.inventory.receiving | receiving check | QUALITY_CHECK | Receiving checks donations for condition, completeness, safety and suitability. | Blocks unsafe tools. |
| toollibraryops.inventory.stock_count | stock count | MEASUREMENT | Count tracks available, checked out, maintenance, lost and retired tools. | Shows inventory. |
| toollibraryops.membership.user_registration | user registration | RECORD | Registration captures borrower identity, contact, address area, agreement and eligibility. | Enables checkout. |
| toollibraryops.membership.eligibility | eligibility rule | CONSTRAINT | Eligibility defines disaster-affected users, age, residency, project type or partner referral. | Preserves fairness. |
| toollibraryops.membership.agreement | borrower agreement | RECORD | Agreement covers safe use, return date, liability, damage and privacy. | Sets expectations. |
| toollibraryops.membership.privacy | privacy rule | SAFETY_RULE | Borrower data is limited to checkout, contact and audit needs. | Reduces exposure. |
| toollibraryops.checkout.request | checkout request | RECORD | Request records tool, borrower, project, pickup time, due date and accessories. | Starts loan. |
| toollibraryops.checkout.availability | availability check | QUALITY_CHECK | Check confirms tool is available, safe, complete and appropriate. | Prevents bad loan. |
| toollibraryops.checkout.issue | checkout issue | RECORD | Issue records tool ID, condition, accessories, due date, staff and borrower. | Creates trail. |
| toollibraryops.checkout.limit | checkout limit | CONSTRAINT | Limits define loan duration, quantity, high-risk tools and renewal rules. | Extends access. |
| toollibraryops.safety.briefing | safety briefing | METHOD | Brief covers PPE, tool limits, hazards, power, ladders and stop-use triggers. | Reduces injury. |
| toollibraryops.safety.skill_boundary | skill boundary | SAFETY_RULE | High-risk tools require training, referral or exclusion. | Controls risk. |
| toollibraryops.safety.ppe | PPE note | METHOD | Staff recommend or issue PPE tied to tool and task. | Improves safe use. |
| toollibraryops.safety.manual | manual access | RECORD | Manual, checklist or QR guide is linked to each tool category. | Supports correct use. |
| toollibraryops.returns.return_check | return check | QUALITY_CHECK | Return checks tool ID, condition, cleanliness, accessories and damage. | Restores stock. |
| toollibraryops.returns.late_return | late return | RECORD | Late return records contact attempts, extension, lost status or fee policy. | Controls availability. |
| toollibraryops.returns.cleaning | cleaning process | METHOD | Returned tools are cleaned, dried and staged before reissue. | Preserves tools. |
| toollibraryops.returns.restock | restock method | METHOD | Safe complete tools move back to available inventory. | Keeps library usable. |
| toollibraryops.damage.damage_report | damage report | RECORD | Report captures broken, missing, dull, unsafe or incomplete tool condition. | Starts repair. |
| toollibraryops.damage.borrower_note | borrower note | RECORD | Borrower note records incident, misuse, normal wear or pre-existing issue. | Clarifies cause. |
| toollibraryops.damage.loss | loss record | RECORD | Loss records missing tool, replacement path, owner and financial handling. | Explains variance. |
| toollibraryops.damage.retirement | retirement rule | METHOD | Unsafe or uneconomic tools are retired, recycled or used for parts. | Protects users. |
| toollibraryops.maintenance.maintenance_queue | maintenance queue | RECORD | Queue tracks tools needing sharpening, repair, battery, calibration or inspection. | Organizes work. |
| toollibraryops.maintenance.repair_assignment | repair assignment | METHOD | Assignment sends tool to volunteer, vendor or staff with due date. | Restores stock. |
| toollibraryops.maintenance.preventive | preventive maintenance | METHOD | Preventive schedule covers blades, batteries, cords, lubrication and fasteners. | Extends life. |
| toollibraryops.maintenance.post_repair_check | post-repair check | QUALITY_CHECK | Repaired tools are tested before return to circulation. | Confirms safety. |
| toollibraryops.logistics.pickup_site | pickup site | RECORD | Site record captures hours, storage, signage, staff, security and access. | Organizes service. |
| toollibraryops.logistics.mobile_route | mobile route | METHOD | Route delivers tool access to recovery areas by demand and inventory. | Expands reach. |
| toollibraryops.logistics.storage | storage rule | SAFETY_RULE | Storage separates sharp, powered, fuel, battery and heavy tools. | Prevents accidents. |
| toollibraryops.logistics.security | security control | SAFETY_RULE | High-value tools use locked storage, signout and periodic count. | Reduces loss. |
| toollibraryops.communication.public_notice | public notice | METHOD | Notice states tool types, hours, eligibility, safety rules and return expectations. | Guides residents. |
| toollibraryops.communication.shortage | shortage message | METHOD | Shortage message explains waitlist, substitutions and donation needs. | Manages demand. |
| toollibraryops.reporting.daily_summary | daily summary | MEASUREMENT | Summary reports checkouts, returns, late items, damage, inventory and demand. | Informs managers. |
| toollibraryops.metrics.utilization | utilization rate | MEASUREMENT | Utilization tracks tool use by category and time. | Guides stock. |
| toollibraryops.metrics.damage_rate | damage rate | MEASUREMENT | Damage rate tracks damage by tool type, borrower class and cause. | Improves safety. |
| toollibraryops.metrics.turnaround | turnaround time | MEASUREMENT | Turnaround measures return to available or repair completion. | Reveals bottleneck. |
| toollibraryops.qa.audit_count | audit count | QUALITY_CHECK | Periodic audit reconciles physical tools with checkout and maintenance records. | Controls inventory. |
| toollibraryops.review.after_action | after-action review | METHOD | Review captures inventory mix, safety brief quality, returns, damage and maintenance lessons. | Improves future library. |
