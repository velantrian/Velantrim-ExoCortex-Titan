# BATCH 336: Utility Account Identity Verification Operations

**KnowledgeUnits:** 44  
**Namespace:** `acctverifyops.*`  
**Scope:** authentication, authorized users, privacy, fraud flags, documents, call handling and audit.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| acctverifyops.auth.account_match | account match | QUALITY_CHECK | Caller identity is matched to account name, address, phone, email or portal credential. | Prevents disclosure to wrong person. |
| acctverifyops.auth.knowledge_factor | knowledge factor | METHOD | Staff may ask non-public account facts such as last payment or meter location. | Adds verification beyond caller ID. |
| acctverifyops.auth.portal_login | portal login | METHOD | Secure portal authentication can authorize self-service changes. | Reduces call-center exposure. |
| acctverifyops.auth.failed_auth | failed authentication | DECISION_RULE | Failed verification limits information and routes to document or supervisor process. | Protects privacy under uncertainty. |
| acctverifyops.authorized.primary_holder | primary holder | RECORD | Primary account holder has default authority for billing and service changes. | Defines baseline permission. |
| acctverifyops.authorized.additional_user | additional user | RECORD | Authorized users are listed with scope, dates and verification basis. | Allows family or staff help without full account transfer. |
| acctverifyops.authorized.property_manager | property manager | RECORD | Property manager authority is tied to owner authorization or management agreement. | Prevents unauthorized tenant account changes. |
| acctverifyops.authorized.remove_user | remove authorized user | METHOD | Removal records requester, date, affected user and scope. | Keeps access current. |
| acctverifyops.privacy.minimum_disclosure | minimum disclosure | SAFETY_RULE | Staff share only data needed for the verified purpose. | Reduces privacy leakage. |
| acctverifyops.privacy.sensitive_fields | sensitive fields | CONSTRAINT | SSN, ID copies, bank data and medical flags have restricted handling. | Protects high-risk information. |
| acctverifyops.privacy.call_recording | call recording notice | CONSTRAINT | Call recording and consent notices follow policy. | Keeps service channel compliant. |
| acctverifyops.privacy.public_records | public records boundary | CONSTRAINT | Some utility data may be public, but personal account details remain protected. | Balances transparency and privacy. |
| acctverifyops.documents.id_document | ID document | RECORD | Accepted ID types, expiration and review result are recorded without unnecessary copies where possible. | Supports high-assurance verification. |
| acctverifyops.documents.lease_deed | lease or deed | RECORD | Occupancy or ownership documents prove authority for service. | Useful for move-in disputes. |
| acctverifyops.documents.business_authority | business authority | RECORD | Business accounts may require officer, tax, license or authorization proof. | Prevents employee misuse. |
| acctverifyops.documents.document_rejection | document rejection | RECORD | Rejection reason is documented when proof is unreadable, mismatched or expired. | Gives customer correction path. |
| acctverifyops.fraud.red_flags | fraud red flags | MODEL | Red flags include rapid address changes, mismatched documents, unusual payment requests or prior tamper. | Helps staff slow risky actions. |
| acctverifyops.fraud.account_takeover | account takeover | FAILURE_MODE | Fraudster attempts to change contact, autopay or service using stolen details. | Requires stronger verification. |
| acctverifyops.fraud.synthetic_identity | synthetic identity | FAILURE_MODE | Fake identity combines real and invented data to open service. | Creates bad debt and privacy risk. |
| acctverifyops.fraud.supervisor_review | supervisor review | DECISION_RULE | Fraud flags route to supervisor before service, refund or contact change. | Adds control at high-risk steps. |
| acctverifyops.call.balance_request | balance request | DECISION_RULE | Balance and due date may require lower verification than service changes. | Matches verification level to risk. |
| acctverifyops.call.service_change | service change request | DECISION_RULE | Start/stop, shutoff, mailing address or authorized user changes require stronger verification. | Protects account control. |
| acctverifyops.call.payment_method | payment method handling | SAFETY_RULE | Staff avoid reading full bank or card data and follow secure payment channel rules. | Reduces financial data exposure. |
| acctverifyops.call.third_party | third-party caller | METHOD | Third parties receive only permitted information unless authorization is verified. | Handles family, landlord and agency calls safely. |
| acctverifyops.field.field_identity | field identity | METHOD | Field staff verify customer on site through work order, address and account notes. | Prevents unauthorized field actions. |
| acctverifyops.field.door_contact | door contact | SAFETY_RULE | Crews avoid discussing sensitive billing details at door without verification. | Protects privacy in shared spaces. |
| acctverifyops.field.badge_check | employee badge check | METHOD | Customers can verify utility employee identity through badge and call-back number. | Reduces impersonation risk. |
| acctverifyops.audit.auth_log | authentication log | RECORD | System logs method, result, user, date and action authorized. | Creates evidence for audits. |
| acctverifyops.audit.override_log | override log | RECORD | Manual overrides capture reason, approver and risk basis. | Controls exceptions. |
| acctverifyops.audit.access_review | access review | QUALITY_CHECK | Periodic review checks staff access and unusual account lookups. | Detects insider misuse. |
| acctverifyops.audit.failed_attempts | failed attempts | MEASUREMENT | Repeated failed authentication attempts are tracked. | Identifies fraud or training issues. |
| acctverifyops.training.script | verification script | METHOD | Scripts guide staff through allowed questions and escalation. | Makes verification consistent. |
| acctverifyops.training.privacy_training | privacy training | METHOD | Staff learn data minimization, fraud signs and safe disclosure. | Reduces accidental exposure. |
| acctverifyops.training.social_engineering | social engineering | MODEL | Attackers use urgency, sympathy or insider-sounding details to bypass checks. | Staff recognize manipulation. |
| acctverifyops.exceptions.emergency | emergency exception | DECISION_RULE | Public safety or leak emergencies may allow limited action while preserving privacy. | Balances safety and account control. |
| acctverifyops.exceptions.deceased_customer | deceased customer | METHOD | Deceased account-holder cases require estate, surviving occupant or legal documents. | Handles sensitive transition. |
| acctverifyops.exceptions.domestic_safety | domestic safety flag | SAFETY_RULE | Address or contact disclosure may be restricted for safety-sensitive accounts. | Protects vulnerable customers. |
| acctverifyops.records.data_update | data update | METHOD | Verified contact changes update CRM, billing, portal and notification systems. | Keeps channels aligned. |
| acctverifyops.records.source_of_truth | source of truth | RECORD | One system is designated authoritative for authorized users and contact data. | Avoids conflicting permissions. |
| acctverifyops.reporting.verification_rate | verification rate | MEASUREMENT | Reports show passed, failed, overridden and escalated authentications. | Measures process health. |
| acctverifyops.reporting.fraud_cases | fraud cases | RECORD | Confirmed fraud and attempted fraud are tracked by type and channel. | Guides controls. |
| acctverifyops.reporting.training_gap | training gap | MODEL | Error patterns indicate script, system or staff training gaps. | Improves program design. |
| acctverifyops.review.policy_review | policy review | METHOD | Verification rules are reviewed after fraud events, privacy complaints or regulation changes. | Keeps controls current. |
| acctverifyops.closeout.case_close | verification case close | RECORD | Document-based verification closes with result, scope and expiry if applicable. | Prevents open-ended access assumptions. |

