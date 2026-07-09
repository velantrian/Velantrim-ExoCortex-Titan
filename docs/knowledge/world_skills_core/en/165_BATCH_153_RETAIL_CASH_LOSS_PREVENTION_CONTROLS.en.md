# BATCH_153 — Retail Cash Office & Loss Prevention Controls
# world_skills_core · source: world_skills_core:batch_153:retail_cash_loss_prevention_controls
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| retailctrl.cash.till_float | Till float | invariant | Till float is the starting cash assigned to a register before sales begin. | касса стартует с известной суммы |
| retailctrl.cash.cashier_assignment | Cashier assignment | invariant | Cashier assignment links a till, user, shift, permissions and accountability period. | кто отвечал за кассу |
| retailctrl.cash.no_sale_event | No-sale event | variant | No-sale event opens the cash drawer without a sale and should be logged for exception review. | сигнал для контроля |
| retailctrl.cash.cash_drop | Cash drop | invariant | Cash drop removes excess cash from till to safe or cash office with record, witness or secure bag. | меньше денег в кассе |
| retailctrl.cash.safe_count | Safe count | invariant | Safe count compares actual cash, change fund, deposits and expected balances at a defined time. | контроль сейфа |
| retailctrl.cash.end_of_day_count | End-of-day cash count | invariant | End-of-day count reconciles sales, refunds, cash drops, card totals, vouchers and till variances. | закрыть день |
| retailctrl.cash.till_variance | Till variance | invariant | Till variance is the difference between expected and counted cash or payment totals. | найти over/short |
| retailctrl.cash.dual_control | Cash dual control | variant | Dual control requires two authorized people for sensitive cash handling, safe access or count verification. | снизить fraud risk |
| retailctrl.cash.bank_deposit_bag | Bank deposit bag | invariant | Deposit bag links sealed cash, count sheet, store, date and bank delivery record. | traceable cash transfer |
| retailctrl.cash.change_order | Change order | variant | Change order requests coins and small notes to maintain register operations during expected demand. | не остаться без сдачи |
| retailctrl.pos.void_transaction | Void transaction | invariant | Void transaction cancels a sale before completion and should capture reason, user and authorization. | контролировать отмены |
| retailctrl.pos.refund_control | Refund control | invariant | Refund control verifies receipt, item, policy, payment method, reason and approval threshold. | возврат не должен быть loophole |
| retailctrl.pos.price_override | Price override | variant | Price override changes item price manually and should require reason and authorization based on threshold. | скидка под контролем |
| retailctrl.pos.manager_approval | Manager approval | invariant | Manager approval gates high-risk actions such as refunds, overrides, cash payout or till correction. | не все может кассир |
| retailctrl.pos.gift_card_activation | Gift card activation control | invariant | Gift card activation should reconcile sold cards, activated value, payment and fraud alerts. | stored value risk |
| retailctrl.pos.coupon_validation | Coupon validation | variant | Coupon validation checks eligibility, expiry, item match, customer limit and duplicate redemption. | промо без утечки |
| retailctrl.pos.manual_card_entry | Manual card entry | variant | Manual card entry increases fraud risk and should be monitored by frequency, value and reason. | обход обычного чтения карты |
| retailctrl.pos.offline_mode | POS offline mode | variant | Offline mode allows sales during connectivity loss but creates later reconciliation and payment risk. | continuity with exposure |
| retailctrl.inventory.shrinkage | Retail shrinkage | invariant | Shrinkage is inventory loss from theft, damage, error, spoilage, fraud or process gaps. | потеря не только кража |
| retailctrl.inventory.cycle_count | Retail cycle count | invariant | Cycle count checks selected inventory regularly instead of waiting for full stocktake. | early discrepancy detection |
| retailctrl.inventory.stock_adjustment | Stock adjustment | invariant | Stock adjustment changes inventory record and should record reason, user, evidence and approval. | учет не менять без следа |
| retailctrl.inventory.damaged_goods | Damaged goods control | invariant | Damaged goods process separates unsellable items, records cause, value and disposal or vendor claim path. | не возвращать в продажу |
| retailctrl.inventory.high_value_lockup | High-value lockup | variant | High-value lockup protects expensive or theft-prone items with controlled access and count routines. | рискованные SKU |
| retailctrl.inventory.receiving_discrepancy | Receiving discrepancy | invariant | Receiving discrepancy identifies mismatch between purchase order, delivery note, physical goods and system entry. | shrink can start at dock |
| retailctrl.inventory.rtv_process | Return-to-vendor process | variant | RTV process tracks goods sent back to vendor with authorization, quantities, credit and shipping evidence. | recover value |
| retailctrl.loss.cctv_log | CCTV review log | variant | CCTV review log records who reviewed footage, why, time range and findings without unnecessary privacy exposure. | video как controlled evidence |
| retailctrl.loss.incident_report | Retail incident report | invariant | Incident report captures theft, violence, damage, accident or policy breach with facts, time and witnesses. | события не теряются |
| retailctrl.loss.exception_report | POS exception report | invariant | Exception report highlights unusual refunds, voids, discounts, no-sales, gift cards or manual entries. | patterns over anecdotes |
| retailctrl.loss.employee_purchase | Employee purchase control | variant | Employee purchase policy separates staff shopping from work duties and requires approved discounts or checks. | reduce conflict |
| retailctrl.loss.bag_check_policy | Bag check policy | variant | Bag check policy must be consistent, lawful, respectful and documented to avoid arbitrary enforcement. | контроль без унижения |
| retailctrl.loss.known_theft_pattern | Known theft pattern | variant | Known theft pattern uses repeated behaviors, product targets and timing to guide prevention without profiling unfairly. | focus on behavior |
| retailctrl.loss.returns_fraud_signal | Returns fraud signal | variant | Returns fraud signal includes repeated no-receipt returns, mismatched items, high-value attempts or identity patterns. | investigate carefully |
| retailctrl.loss.cash_refund_abuse | Cash refund abuse | invariant | Cash refund abuse occurs when refund process is used to extract cash without legitimate return basis. | high-risk transaction |
| retailctrl.loss.internal_collusion | Internal collusion risk | variant | Collusion risk rises when staff and outsiders coordinate refunds, discounts, fake returns or inventory movement. | one control is not enough |
| retailctrl.access.key_control | Retail key control | invariant | Key control tracks issue, return, access level, lost keys and lock changes for store and cash areas. | physical access matters |
| retailctrl.access.alarm_code | Alarm code control | invariant | Alarm code control assigns unique codes, removes leavers and reviews after incidents or role changes. | no shared secrets |
| retailctrl.access.backroom_access | Backroom access control | variant | Backroom access limits inventory, cash office and receiving areas to authorized staff and vendors. | reduce uncontrolled movement |
| retailctrl.access.safe_access_log | Safe access log | invariant | Safe access log records date, time, user, purpose and irregularities during safe opening. | accountability for cash |
| retailctrl.reporting.daily_sales_reconciliation | Daily sales reconciliation | invariant | Daily reconciliation compares POS totals, payment processor, deposits, refunds, discounts and inventory movements. | one daily truth |
| retailctrl.reporting.shrink_dashboard | Shrink dashboard | variant | Shrink dashboard tracks shrink by store, department, SKU, time, cause and action status. | see where loss happens |
| retailctrl.reporting.loss_case_file | Loss case file | invariant | Case file keeps incident reports, evidence, interviews, actions and closure decision for significant loss events. | structured investigation |
| retailctrl.reporting.policy_exception | Policy exception tracking | invariant | Exception tracking records approved deviations from retail policy and reviews whether they become pattern. | exceptions can become leakage |
| retailctrl.reporting.training_record | Loss prevention training record | invariant | Training record confirms staff learned cash handling, returns, safety, reporting and escalation procedures. | controls need people |
| retailctrl.reporting.post_incident_review | Retail post-incident review | variant | Review after major loss event identifies control gaps, staff needs, layout risks and procedural improvements. | learn from loss |
