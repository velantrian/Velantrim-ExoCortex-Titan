# BATCH_182 — Facilities Energy Management Operations Detail
# world_skills_core · source: world_skills_core:batch_182:facilities_energy_management_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| energymgmt.meter.meter_register | Energy meter register | invariant | Register lists meters, utility accounts, locations, fuels, multipliers, owners and data source. | know what is measured |
| energymgmt.meter.manual_read | Manual meter read | invariant | Manual read records date, value, unit, reader and anomalies when automated data is unavailable. | basic evidence |
| energymgmt.meter.interval_data | Interval energy data | invariant | Interval data shows usage by time blocks and reveals peaks, schedules and equipment behavior. | see when energy is used |
| energymgmt.meter.submeter | Energy submeter | variant | Submeter separates building, tenant, system or process loads for more precise management. | isolate consumption |
| energymgmt.meter.meter_fault | Energy meter fault | invariant | Fault may show flatline, impossible spike, missing data or multiplier error needing investigation. | bad data misleads |
| energymgmt.meter.weather_normalization | Weather normalization | variant | Normalization adjusts energy use for heating or cooling weather differences. | fair comparison |
| energymgmt.baseline.energy_baseline | Energy baseline | invariant | Baseline represents expected energy use before project, operation change or performance period. | compare against reference |
| energymgmt.baseline.energy_use_intensity | Energy use intensity | invariant | EUI divides building energy by area or relevant activity metric. | compare buildings |
| energymgmt.baseline.load_profile | Load profile | invariant | Profile shows demand pattern over time and helps identify occupancy, equipment or control issues. | fingerprint of building |
| energymgmt.baseline.peak_demand | Peak demand | invariant | Peak demand is highest power draw over billing or measurement interval. | drives demand charges |
| energymgmt.baseline.degree_day | Degree day | variant | Degree days estimate heating or cooling need based on outdoor temperature. | weather context |
| energymgmt.baseline.operating_hours | Operating hours | invariant | Hours explain when building should be conditioned, lit or operating. | schedule drives usage |
| energymgmt.controls.setpoint | HVAC setpoint | invariant | Setpoint defines target temperature or control value for system operation. | small changes matter |
| energymgmt.controls.schedule_control | Building schedule control | invariant | Schedule control turns systems on or off based on occupancy and operational need. | stop running empty |
| energymgmt.controls.night_setback | Night setback | variant | Setback reduces heating or cooling intensity outside occupied hours where appropriate. | comfort versus savings |
| energymgmt.controls.optimum_start | Optimum start | variant | Control starts HVAC just early enough to meet comfort at occupancy time. | avoid excessive preheat |
| energymgmt.controls.simultaneous_heat_cool | Simultaneous heating and cooling | invariant | Simultaneous heat and cool wastes energy when zones or controls fight each other. | common building fault |
| energymgmt.controls.bms_alarm | BMS energy alarm | invariant | Alarm flags abnormal temperature, runtime, valve position, sensor or energy condition. | automation needs attention |
| energymgmt.utility.bill_audit | Utility bill audit | invariant | Audit checks rates, meter reads, demand, taxes, fees, dates, multipliers and anomalies. | bills can be wrong |
| energymgmt.utility.tariff_review | Tariff review | variant | Review compares rate options, demand structure, time-of-use and eligibility. | price structure matters |
| energymgmt.utility.demand_charge | Demand charge | invariant | Demand charge bills peak power capacity rather than total energy. | peaks cost money |
| energymgmt.utility.power_factor | Power factor charge | variant | Poor power factor can create charges or equipment inefficiency in some tariffs. | electrical quality cost |
| energymgmt.utility.tenant_rebill | Tenant energy rebilling | variant | Rebilling allocates utility cost by lease, submeter, formula or agreed method. | cost allocation |
| energymgmt.utility.budget_variance | Energy budget variance | invariant | Variance compares actual cost or use to budget and investigates weather, price or operation causes. | explain overspend |
| energymgmt.audit.walkthrough | Energy walkthrough audit | invariant | Walkthrough observes schedules, equipment, envelope, lighting, controls and obvious waste. | first-pass savings |
| energymgmt.audit.level_two_audit | Detailed energy audit | variant | Detailed audit quantifies measures, costs, savings, payback, risks and measurement plan. | investment basis |
| energymgmt.audit.ecm | Energy conservation measure | invariant | ECM is an action that reduces energy use, demand or cost while maintaining required service. | named improvement |
| energymgmt.audit.no_cost_measure | No-cost measure | variant | No-cost measure uses schedule, setpoint, behavior or control adjustment without capital project. | quick wins |
| energymgmt.audit.retrocommissioning | Retrocommissioning | variant | Retrocommissioning tunes existing systems back to intended or optimized operation. | fix drift |
| energymgmt.audit.opportunity_register | Energy opportunity register | invariant | Register tracks measures, owner, status, estimate, evidence and approval path. | manage pipeline |
| energymgmt.project.led_retrofit | LED retrofit | variant | Retrofit replaces lighting with efficient fixtures while checking levels, controls, compatibility and disposal. | common project |
| energymgmt.project.vfd | Variable frequency drive | variant | VFD saves energy when motors can reduce speed under variable load. | speed control |
| energymgmt.project.economizer | Air-side economizer | variant | Economizer uses outdoor air for cooling when conditions are suitable. | free cooling |
| energymgmt.project.insulation_upgrade | Insulation upgrade | variant | Upgrade reduces heat transfer where envelope or piping losses justify work. | reduce load |
| energymgmt.project.controls_tuning | Controls tuning | invariant | Tuning adjusts sequences, sensors, deadbands and schedules to reduce waste. | software savings |
| energymgmt.project.project_closeout | Energy project closeout | invariant | Closeout confirms installation, commissioning, documentation, training and baseline updates. | project becomes operation |
| energymgmt.mv.measurement_verification | Measurement and verification | invariant | M&V compares actual performance to baseline with agreed adjustments and method. | prove savings |
| energymgmt.mv.savings_calculation | Energy savings calculation | invariant | Calculation subtracts adjusted actual use from baseline use for same conditions. | quantify benefit |
| energymgmt.mv.persistence_check | Savings persistence check | variant | Check confirms savings continue after occupancy, weather, controls or maintenance changes. | savings can fade |
| energymgmt.mv.rebound_effect | Rebound effect | variant | Rebound occurs when efficiency gain is partly offset by higher use or comfort changes. | behavior matters |
| energymgmt.reporting.energy_dashboard | Energy dashboard | variant | Dashboard shows use, cost, demand, targets, anomalies and project savings. | visibility for action |
| energymgmt.reporting.carbon_factor | Carbon factor | invariant | Carbon factor converts energy consumption into emissions estimate by fuel or grid factor. | climate accounting |
| energymgmt.reporting.energy_kpi | Facilities energy KPI | invariant | KPI tracks intensity, demand, cost, emissions, savings or comfort complaints. | measure operations |
| energymgmt.reporting.management_review | Energy management review | invariant | Review evaluates performance, projects, budgets, risks, comfort, compliance and next actions. | governance rhythm |
