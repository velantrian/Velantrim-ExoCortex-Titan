# BATCH_184 — Identity & Access Management Operations Detail
# world_skills_core · source: world_skills_core:batch_184:identity_access_management_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| iamops.identity.identity_record | Identity record | invariant | Identity record links person, account, employee ID, role, manager, status and lifecycle dates. | one person, many systems |
| iamops.identity.unique_identifier | Unique identity identifier | invariant | Unique identifier prevents confusion between people with similar names or reused accounts. | identity anchor |
| iamops.identity.source_of_truth | Identity source of truth | invariant | Source of truth provides authoritative data for joiner, mover, leaver and access decisions. | HR or directory authority |
| iamops.identity.identity_proofing | Identity proofing | variant | Proofing verifies that requester is the claimed person before account or credential issuance. | trust before access |
| iamops.identity.name_change | Identity name change | variant | Name change updates display, legal, email or directory attributes while preserving identity continuity. | do not create duplicate |
| iamops.identity.contractor_identity | Contractor identity | variant | Contractor identity needs sponsor, expiry date, company, role and access scope. | temporary workforce control |
| iamops.joiner.joiner_ticket | Joiner ticket | invariant | Joiner ticket requests accounts and access for new worker based on approved start data. | onboarding access |
| iamops.joiner.birthright_access | Birthright access | variant | Birthright access automatically grants baseline tools for role, department or location. | standard access bundle |
| iamops.joiner.account_provisioning | Account provisioning | invariant | Provisioning creates account, mailbox, groups, MFA and required application access. | worker can start |
| iamops.joiner.manager_approval | Access manager approval | invariant | Manager approval confirms business need and responsibility for requested access. | owner accountability |
| iamops.joiner.seg_duty_check | Segregation-of-duty check | invariant | SoD check detects conflicting access combinations before approval. | prevent toxic combination |
| iamops.joiner.first_login | First login control | variant | First login may require password change, MFA enrollment and policy acknowledgment. | secure activation |
| iamops.mover.role_change | Role change access review | invariant | Role change reviews old and new access when employee changes job, team or location. | mover risk |
| iamops.mover.access_add | Access addition request | invariant | Request documents system, role, reason, owner, approver and duration. | explicit grant |
| iamops.mover.access_remove | Access removal request | invariant | Removal closes access no longer needed because of role, project, risk or departure. | least privilege |
| iamops.mover.temporary_access | Temporary access | variant | Temporary access has expiration date, justification and review path. | avoid permanent exception |
| iamops.mover.emergency_access | Emergency access | variant | Emergency access grants urgent privilege with time limit, monitoring and retrospective approval. | break-glass control |
| iamops.mover.access_transfer | Access transfer | invariant | Transfer must not blindly copy all access from one user without review of need and conflicts. | avoid cloning risk |
| iamops.leaver.termination_feed | Termination feed | invariant | Feed notifies IAM of departure date, time, type and required deprovisioning urgency. | offboarding trigger |
| iamops.leaver.account_disable | Account disable | invariant | Disable stops login while preserving data, mailbox or records as policy requires. | fast access stop |
| iamops.leaver.session_revocation | Session revocation | invariant | Revocation invalidates active tokens or sessions after departure or compromise. | access already open |
| iamops.leaver.asset_handoff | Access asset handoff | variant | Handoff transfers shared mailboxes, files, groups, keys or ownership from departing user. | business continuity |
| iamops.leaver.orphan_account | Orphan account | invariant | Orphan account remains active without valid owner and creates security risk. | find abandoned access |
| iamops.leaver.deprovisioning_evidence | Deprovisioning evidence | invariant | Evidence records disabled systems, dates, exceptions and reviewer. | prove removal |
| iamops.review.access_certification | Access certification | invariant | Certification asks owners or managers to confirm users still need access. | periodic cleanup |
| iamops.review.entitlement_owner | Entitlement owner | invariant | Owner is accountable for approving, reviewing and defining access meaning. | business ownership |
| iamops.review.review_campaign | Access review campaign | variant | Campaign schedules scope, reviewers, deadlines, reminders and escalations. | review operation |
| iamops.review.revocation_tracking | Revocation tracking | invariant | Tracking ensures rejected access is actually removed and verified. | review must produce action |
| iamops.review.exception_acceptance | Access exception acceptance | variant | Acceptance documents why risky access remains, who accepted risk and review date. | controlled risk |
| iamops.review.stale_access | Stale access | invariant | Stale access belongs to inactive users, old roles, expired projects or unused accounts. | remove drift |
| iamops.privileged.pam_vault | Privileged access vault | variant | Vault stores, rotates and controls privileged credentials or sessions. | protect admin power |
| iamops.privileged.privileged_session | Privileged session monitoring | variant | Monitoring records or logs administrative sessions for accountability. | admin actions visible |
| iamops.privileged.just_in_time | Just-in-time privilege | variant | JIT grants elevated access only for approved time and task. | reduce standing privilege |
| iamops.privileged.break_glass | Break-glass account | invariant | Break-glass account provides emergency access under strict storage, monitoring and review. | last-resort access |
| iamops.privileged.service_account | Service account ownership | invariant | Service account needs owner, purpose, credential rotation and usage monitoring. | nonhuman identity |
| iamops.privileged.password_rotation | Privileged credential rotation | invariant | Rotation changes credentials after use, schedule, incident or administrator departure. | limit credential exposure |
| iamops.auth.mfa_enrollment | MFA enrollment | invariant | Enrollment binds user to second factor and recovery method according to policy. | stronger login |
| iamops.auth.mfa_reset | MFA reset | invariant | Reset verifies identity before changing factor, device or recovery method. | high-risk helpdesk action |
| iamops.auth.conditional_access | Conditional access policy | variant | Policy changes access based on device, location, risk, app, user or authentication strength. | context-aware control |
| iamops.auth.password_reset | Password reset workflow | invariant | Reset verifies requester, changes credential and records event. | common identity operation |
| iamops.auth.failed_login_monitor | Failed login monitoring | invariant | Monitoring detects attack, lockout, forgotten password or automation issue. | signal in authentication |
| iamops.control.access_request_audit | Access request audit | invariant | Audit checks approval, SoD, implementation, expiration and business justification. | verify process |
| iamops.control.iam_metrics | IAM operations metrics | variant | Metrics track joiner time, leaver completion, review closure, orphan accounts and privileged use. | manage IAM health |
| iamops.control.policy_violation | IAM policy violation | invariant | Violation records unauthorized sharing, excessive access, bypass or delayed deprovisioning. | control failure |
