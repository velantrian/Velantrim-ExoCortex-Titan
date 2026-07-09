# BATCH_220 — Pet Grooming Operations Detail
# world_skills_core · source: world_skills_core:batch_220:pet_grooming_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| petgroom.booking.groom_booking | Pet grooming booking | invariant | Booking records pet, owner, service, coat, temperament, time, add-ons and contact. | reserve groomer time |
| petgroom.booking.service_menu | Grooming service menu | invariant | Menu defines bath, brush, clip, trim, nails, ears, de-shed, sanitary trim or add-ons. | sell clear service |
| petgroom.booking.duration_estimate | Grooming duration estimate | variant | Estimate considers breed, coat, size, matting, behavior and service scope. | schedule realistically |
| petgroom.booking.vaccine_policy | Grooming vaccine policy | variant | Policy defines proof or screening needed before appointment. | reduce disease risk |
| petgroom.booking.no_show_policy | Grooming no-show policy | invariant | Policy manages late arrivals, cancellations, deposits and rebooking. | protect capacity |
| petgroom.intake.pet_identity | Grooming pet identity | invariant | Identity check confirms pet name, species, breed, color, owner and photo if used. | avoid mix-up |
| petgroom.intake.health_note | Grooming health note | invariant | Note records visible lumps, skin, ears, mobility, age, medical warnings and owner disclosures. | handle carefully |
| petgroom.intake.coat_assessment | Coat assessment | invariant | Assessment checks length, matting, shedding, fleas, moisture, skin and desired result. | choose workflow |
| petgroom.intake.behavior_assessment | Grooming behavior assessment | invariant | Assessment notes fear, biting, handling limits, leash manners and stress signals. | staff safety |
| petgroom.intake.owner_instruction | Owner grooming instruction | invariant | Instruction captures haircut preference, restrictions, allergies, products and pickup timing. | expectation control |
| petgroom.bath.prebrush | Pre-bath brushing | invariant | Brushing removes loose hair, tangles and debris before wetting where appropriate. | easier bath |
| petgroom.bath.shampoo_selection | Pet shampoo selection | variant | Selection considers coat, skin sensitivity, odor, parasite policy and owner request. | product fit |
| petgroom.bath.bathing | Pet bathing | invariant | Bathing wets, shampoos, rinses and checks skin while managing stress and temperature. | core clean |
| petgroom.bath.drying | Pet drying | invariant | Drying uses towel, air, cage dryer or hand dryer according to safety and coat. | finish safely |
| petgroom.bath.ear_protection | Grooming ear protection | variant | Protection avoids excess water, pressure or product entering ear canal. | reduce irritation |
| petgroom.clip.clip_style | Grooming clip style | invariant | Style defines blade, guard, length, breed pattern, owner preference and practical limits. | haircut target |
| petgroom.clip.blade_selection | Clipper blade selection | invariant | Selection matches coat, length, matting, skin risk and finish. | avoid injury |
| petgroom.clip.scissor_work | Grooming scissor work | variant | Work shapes face, feet, tail, furnishings or detail areas with controlled handling. | detail finish |
| petgroom.clip.sanitary_trim | Sanitary trim | variant | Trim shortens hair around hygiene areas under service policy and pet tolerance. | cleanliness |
| petgroom.clip.mat_removal | Mat removal | invariant | Removal chooses brushing, clipping, dematting limit or shave-down based on welfare and safety. | mats hurt |
| petgroom.nails.nail_trim | Pet nail trim | invariant | Trim shortens nails while avoiding quick and stress escalation. | paw comfort |
| petgroom.nails.nail_grind | Nail grinding | variant | Grinding smooths nail edges after or instead of clipping if pet tolerates it. | smoother finish |
| petgroom.nails.quick_incident | Quick incident | invariant | Incident records accidental quick nick, control action, owner notice and monitoring. | transparency |
| petgroom.nails.paw_pad_trim | Paw pad trim | variant | Trim removes excess hair between pads where safe and requested. | traction and hygiene |
| petgroom.nails.paw_condition_note | Paw condition note | invariant | Note records cracks, swelling, foreign object, overgrown nail or sensitivity. | alert owner |
| petgroom.safety.restraint_method | Grooming restraint method | invariant | Method uses loop, table, helper or low-stress handling appropriate to pet and task. | prevent falls |
| petgroom.safety.table_safety | Grooming table safety | invariant | Safety checks height, loop, surface, weight limit, pet position and supervision. | fall prevention |
| petgroom.safety.heat_stress | Grooming heat stress risk | invariant | Risk comes from dryers, stress, age, breed, coat, humidity or health condition. | watch closely |
| petgroom.safety.bite_prevention | Grooming bite prevention | invariant | Prevention uses signals, muzzles if allowed, breaks, owner notice or stop-work decision. | protect staff |
| petgroom.safety.stop_groom | Stop-groom decision | invariant | Decision pauses or ends service when pet welfare, behavior, injury or health risk rises. | welfare first |
| petgroom.cleaning.tub_sanitation | Grooming tub sanitation | invariant | Sanitation cleans hair, residue, drains, surfaces and contact areas between pets. | infection control |
| petgroom.cleaning.tool_disinfection | Grooming tool disinfection | invariant | Disinfection covers blades, combs, brushes, nail tools and table contact surfaces. | prevent spread |
| petgroom.cleaning.hair_disposal | Grooming hair disposal | invariant | Disposal manages hair, mats, waste, bags, drains and pests. | keep shop clean |
| petgroom.cleaning.laundry_flow | Grooming laundry flow | variant | Flow separates clean and soiled towels, loops, smocks and bedding. | hygiene |
| petgroom.cleaning.flea_protocol | Flea protocol | variant | Protocol isolates, treats environment per policy, notifies owner and cleans area. | limit infestation |
| petgroom.checkout.final_review | Grooming final review | invariant | Review checks haircut, nails, ears, cleanliness, notes, bows or accessories. | quality gate |
| petgroom.checkout.owner_handoff | Grooming owner handoff | invariant | Handoff explains completed service, concerns, incidents, recommendations and next booking. | close communication |
| petgroom.checkout.payment | Grooming payment | invariant | Payment records service, add-ons, discounts, tips, refunds and receipt. | close money |
| petgroom.checkout.rebook_prompt | Grooming rebook prompt | variant | Prompt suggests interval based on coat, service and owner preference. | continuity |
| petgroom.checkout.late_pickup | Grooming late pickup | invariant | Process manages pet care, fees, staff time and owner communication after agreed pickup. | handle delay |
| petgroom.records.grooming_card | Grooming record card | invariant | Card stores coat notes, blades, behavior, products, incidents and owner preferences. | next visit memory |
| petgroom.records.incident_report | Grooming incident report | invariant | Report documents injury, bite, stress event, escape, product reaction or customer complaint. | safety learning |
| petgroom.metrics.grooming_kpi | Pet grooming KPI | variant | KPI tracks appointments, rebooks, incidents, duration, complaints, revenue and groomer utilization. | manage shop |
| petgroom.continuity.power_water_outage | Grooming power or water outage | invariant | Outage plan pauses baths, protects pets, informs owners and reschedules. | keep pets safe |
