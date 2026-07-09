# BATCH 389: Temporary Shower and Laundry Support Operations

**KnowledgeUnits:** 44  
**Namespace:** `showerlaundryops.*`  
**Scope:** site setup, queues, water, wastewater, hygiene, security, staffing and closeout.

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|---|---|---|---|---|
| showerlaundryops.activation.trigger | activation trigger | MODEL | Trigger includes sheltering, utility outage, contamination, heat, smoke or long recovery. | Starts hygiene support. |
| showerlaundryops.activation.service_model | service model | RECORD | Model distinguishes shower trailer, laundry trailer, fixed facility or mobile route. | Defines operation. |
| showerlaundryops.activation.partner_roles | partner roles | RECORD | Partners include emergency management, nonprofits, vendors, health and site owners. | Aligns support. |
| showerlaundryops.activation.capacity | capacity estimate | MEASUREMENT | Capacity estimates showers, washers, dryers, staff, water, hours and users. | Sets realistic access. |
| showerlaundryops.site.site_selection | site selection | METHOD | Site checks water, wastewater, power, privacy, access, drainage and security. | Chooses workable location. |
| showerlaundryops.site.layout | layout | METHOD | Layout separates entry, queue, changing, shower, laundry, staff and exit. | Protects privacy and flow. |
| showerlaundryops.site.accessibility | accessibility | METHOD | Accessible routes, stalls, seating and assistance are arranged where feasible. | Supports disabled users. |
| showerlaundryops.site.weather | weather protection | METHOD | Shade, heat, cold, lighting and rain protection are planned. | Keeps service usable. |
| showerlaundryops.water.source | water source | SAFETY_RULE | Water source must be approved for shower/hygiene use. | Protects health. |
| showerlaundryops.water.connection | water connection | METHOD | Connections use approved hoses, backflow protection and leak checks. | Prevents contamination. |
| showerlaundryops.water.heating | water heating | SAFETY_RULE | Heating systems are checked for burns, fuel, ventilation and reliability. | Protects users. |
| showerlaundryops.water.conservation | water conservation | METHOD | Time limits, low-flow fixtures or scheduling reduce water demand. | Extends service. |
| showerlaundryops.wastewater.discharge | wastewater discharge | CONSTRAINT | Discharge follows sewer, holding tank or approved disposal route. | Prevents environmental harm. |
| showerlaundryops.wastewater.tank_monitor | tank monitoring | MEASUREMENT | Wastewater tanks are monitored for capacity and service timing. | Prevents overflow. |
| showerlaundryops.wastewater.spill | greywater spill response | SAFETY_RULE | Shower or laundry greywater spills trigger drain shutdown, containment, surface cleaning and wastewater vendor follow-up. | Protects site. |
| showerlaundryops.wastewater.vendor | pumping vendor | RECORD | Vendor records service schedule, contacts, tickets and disposal site. | Controls waste service. |
| showerlaundryops.queue.appointment | appointment window | METHOD | Appointment windows spread demand and protect privacy. | Reduces long waits. |
| showerlaundryops.queue.walkin | walk-in queue | METHOD | Walk-in queue uses numbering, seating, shade and clear rules. | Maintains fairness. |
| showerlaundryops.queue.priority | priority access | METHOD | Priority may support medical needs, elders, families or responders. | Supports equity. |
| showerlaundryops.queue.no_show | no-show handling | METHOD | No-shows release slot and may move waitlist forward. | Keeps capacity used. |
| showerlaundryops.hygiene.cleaning | cleaning protocol | SAFETY_RULE | Stalls, machines and contact surfaces are cleaned on schedule. | Reduces infection risk. |
| showerlaundryops.hygiene.supplies | hygiene supplies | RECORD | Supplies include soap, towels, detergent, bags, gloves and disinfectant. | Keeps service functional. |
| showerlaundryops.hygiene.linen | towel and linen handling | METHOD | Used towels/linens are separated, washed or disposed under hygiene rule. | Prevents cross-contamination. |
| showerlaundryops.hygiene.personal_items | personal item control | METHOD | Laundry bags, tags or receipts keep clothing with correct person. | Prevents loss. |
| showerlaundryops.security.privacy | privacy rule | SAFETY_RULE | Gender, family, disability and trauma-informed privacy controls are considered. | Protects dignity. |
| showerlaundryops.security.access_control | access control | METHOD | Staff manage entry, staff-only areas and user flow. | Keeps site orderly. |
| showerlaundryops.security.incident | incident report | RECORD | Incidents record harassment, theft, injury, medical issue or conflict. | Supports safety review. |
| showerlaundryops.security.lost_found | lost and found | RECORD | Lost items are logged, stored and returned by proof. | Reduces disputes. |
| showerlaundryops.staffing.roster | staffing roster | RECORD | Roster tracks attendants, cleaners, security, interpreters and maintenance roles. | Maintains coverage. |
| showerlaundryops.staffing.briefing | shift briefing | METHOD | Briefing covers capacity, supplies, safety, complaints and equipment status. | Aligns staff. |
| showerlaundryops.staffing.volunteer | volunteer role | CONSTRAINT | Volunteers avoid sensitive tasks unless trained and supervised. | Protects privacy. |
| showerlaundryops.maintenance.equipment_check | equipment check | QUALITY_CHECK | Check covers leaks, pumps, heaters, machines, drains, power and ventilation. | Prevents outages. |
| showerlaundryops.maintenance.failure | failure response | METHOD | Failure triggers repair, backup unit, closure notice or rescheduling. | Maintains service. |
| showerlaundryops.maintenance.parts | parts and supplies | RECORD | Parts track hoses, filters, pumps, belts, fuses and detergents. | Supports repairs. |
| showerlaundryops.communication.public_notice | public notice | METHOD | Notice states location, hours, rules, supplies, appointments and accessibility. | Guides users. |
| showerlaundryops.communication.site_rules | site rules | METHOD | Rules cover time limits, children, belongings, conduct and cleaning. | Reduces conflict. |
| showerlaundryops.communication.language | language support | METHOD | Signs and staff support common languages and simple icons. | Improves access. |
| showerlaundryops.records.usage_log | usage log | MEASUREMENT | Usage tracks showers, laundry loads, no-shows, priority users and wait times. | Shows demand. |
| showerlaundryops.records.cost | cost record | RECORD | Costs track rental, water, waste, labor, supplies and repairs. | Supports reimbursement. |
| showerlaundryops.records.retention | retention rule | CONSTRAINT | Records follow emergency, privacy, procurement and finance schedules. | Preserves audit. |
| showerlaundryops.qa.site_inspection | site inspection | QUALITY_CHECK | Inspection checks cleanliness, privacy, safety, access and equipment. | Maintains quality. |
| showerlaundryops.demob.closeout | closeout | METHOD | Closeout cleans site, drains tanks, returns equipment and resolves lost items. | Ends service responsibly. |
| showerlaundryops.demob.final_usage | final usage summary | MEASUREMENT | Final summary reports showers, laundry loads, unmet demand and incidents. | Captures operational value. |
| showerlaundryops.review.after_action | after-action review | METHOD | Review captures capacity, privacy, maintenance, accessibility and staffing lessons. | Improves future support. |
