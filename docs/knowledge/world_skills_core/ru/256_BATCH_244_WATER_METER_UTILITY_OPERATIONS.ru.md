# BATCH_244 — Water Meter Utility Operations Detail
# world_skills_core · source: world_skills_core:batch_244:water_meter_utility_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| watermeter.read.route_schedule | Water meter read route schedule | invariant | Schedule assigns meter route, reader, cycle, service area and expected count. | organize reads |
| watermeter.read.read_capture | Water meter read capture | invariant | Capture records meter ID, reading, date, method, reader and exception code. | billing input |
| watermeter.read.remote_read | Remote meter read | variant | Read collects AMR or AMI value, signal, timestamp, battery and communication status. | automated data |
| watermeter.read.manual_read | Manual meter read | variant | Read captures visual dial or register value with access and condition notes. | fallback data |
| watermeter.read.high_low_exception | Water read high-low exception | invariant | Exception flags unusual consumption versus history, season, occupancy or prior read. | prevent bad bills |
| watermeter.install.new_meter_order | Water meter install order | invariant | Order records account, address, meter size, service type, appointment and parts. | start install |
| watermeter.install.meter_set | Water meter set | invariant | Set records meter serial, register, endpoint, location, size, reading and installer. | asset activation |
| watermeter.install.exchange_order | Water meter exchange order | variant | Order replaces old meter for age, failure, upgrade, test, damage or size change. | maintain accuracy |
| watermeter.install.endpoint_pairing | Meter endpoint pairing | variant | Pairing links radio endpoint, meter, account, location and network test. | data connectivity |
| watermeter.install.install_photo | Water meter install photo | variant | Photo documents meter, register, valves, location, seal and access condition. | field evidence |
| watermeter.leak.continuous_flow_alert | Continuous water flow alert | invariant | Alert flags possible leak from interval data, threshold, duration and account history. | catch leaks |
| watermeter.leak.customer_leak_notice | Customer leak notice | variant | Notice communicates abnormal use, checking guidance, contact path and billing rules. | reduce loss |
| watermeter.leak.field_leak_check | Water meter field leak check | invariant | Check inspects meter, indicator, service line signs, box, valves and visible usage. | verify issue |
| watermeter.leak.utility_side_leak | Utility-side leak referral | variant | Referral routes suspected main, service, valve or meter-box leak to repair crew. | stop system loss |
| watermeter.tamper.tamper_flag | Water meter tamper flag | invariant | Flag records broken seal, bypass, reversed meter, magnet, cut wire or unauthorized use. | protect revenue |
| watermeter.tamper.investigation_case | Water meter tamper investigation | variant | Case records evidence, photos, account history, field findings and enforcement route. | resolve tamper |
| watermeter.tamper.seal_control | Water meter seal control | invariant | Control tracks seal number, installation, removal, staff, reason and inventory. | chain of custody |
| watermeter.billing.estimated_bill | Estimated water bill | invariant | Estimate uses rules for missing, failed, inaccessible or questionable read. | keep billing cycle |
| watermeter.billing.billing_exception | Water billing exception | invariant | Exception holds bill for high use, zero use, rollover, wrong meter or account issue. | billing accuracy |
| watermeter.billing.adjustment_review | Water bill adjustment review | variant | Review evaluates leak credit, meter error, misread, vacancy or policy exception. | fair correction |
| watermeter.billing.final_read | Water account final read | invariant | Read closes account for move-out, ownership change, shutoff or transfer. | settle account |
| watermeter.billing.consumption_history | Water consumption history | variant | History compares usage by period, meter, account, weather and occupancy signal. | explain bills |
| watermeter.service.appointment_window | Water meter service appointment | invariant | Appointment records customer contact, access, window, technician, task and notes. | coordinate visit |
| watermeter.service.no_access | Water meter no-access record | invariant | Record captures locked gate, dog, buried box, absent customer or unsafe condition. | reschedule evidence |
| watermeter.service.meter_box_cleanout | Water meter box cleanout | variant | Cleanout removes dirt, water, roots, insects or debris for safe access. | restore access |
| watermeter.service.valve_operation | Water meter valve operation | invariant | Operation records curb stop, angle valve, meter valve action and condition. | control water |
| watermeter.service.customer_contact | Water meter customer contact | invariant | Contact logs notice, door tag, phone, email, complaint or appointment confirmation. | communication trail |
| watermeter.shutoff.nonpay_shutoff | Water nonpayment shutoff | variant | Shutoff records eligibility, notice, field action, meter status and restoration requirements. | enforce billing |
| watermeter.shutoff.emergency_shutoff | Water emergency shutoff | invariant | Shutoff responds to leak, damage, contamination risk, fire support or safety hazard. | protect system |
| watermeter.shutoff.reconnect_order | Water reconnect order | invariant | Order records payment, authorization, field reconnect, read, seal and customer notice. | restore service |
| watermeter.shutoff.wrongful_shutoff | Water wrongful shutoff review | invariant | Review checks address, account, notice, field proof and corrective action. | prevent harm |
| watermeter.asset.meter_inventory | Water meter inventory | invariant | Inventory tracks meters, registers, endpoints, sizes, serials, status and storage. | asset control |
| watermeter.asset.test_bench | Water meter test bench | variant | Test records meter accuracy, flow points, result, calibration and disposition. | verify accuracy |
| watermeter.asset.retired_meter | Retired water meter | invariant | Retirement records removal, final read, reason, scrap, test or storage action. | lifecycle control |
| watermeter.asset.size_change | Water meter size change | variant | Change updates meter size for demand, service type, billing class or policy. | proper billing |
| watermeter.quality.read_audit | Water meter read audit | invariant | Audit compares field reads, photos, remote data, route exceptions and billing holds. | data quality |
| watermeter.quality.gps_verification | Meter location GPS verification | variant | Verification updates coordinates, address, pit location and route notes. | find meter |
| watermeter.quality.device_alarm | Water meter device alarm | invariant | Alarm flags reverse flow, cut wire, low battery, leak, burst or communication loss. | targeted response |
| watermeter.field.safety_hazard | Water meter field safety hazard | invariant | Hazard records traffic, confined access, animals, insects, needles, ice or electrical risk. | protect workers |
| watermeter.field.traffic_control | Water meter traffic control | variant | Control protects technician working near road, sidewalk or driveway. | safe access |
| watermeter.reporting.route_completion | Water meter route completion report | invariant | Report summarizes reads completed, estimates, exceptions, no-access and device issues. | operational visibility |
| watermeter.reporting.revenue_protection | Water utility revenue protection report | variant | Report tracks tamper, stopped meters, zero usage, estimates and recoveries. | protect revenue |
| watermeter.metrics.water_meter_kpi | Water meter operations KPI | variant | KPI tracks read rate, estimate rate, leaks, tamper cases, no-access and bill holds. | manage utility |
| watermeter.continuity.ami_outage | AMI network outage response | invariant | Response switches to estimates, manual reads, vendor repair and customer communication. | billing continuity |
