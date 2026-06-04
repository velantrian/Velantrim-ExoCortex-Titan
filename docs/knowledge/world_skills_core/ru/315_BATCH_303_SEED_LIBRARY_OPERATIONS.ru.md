# BATCH_303 — Seed Library Operations Detail
# world_skills_core · source: world_skills_core:batch_303:seed_library_operations
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| seedlibops.inventory.seed_lot | Seed library seed lot | invariant | Lot groups one crop, variety, source, year, quantity and storage condition. | trace seeds |
| seedlibops.inventory.variety_record | Seed variety record | invariant | Record stores crop, variety, traits, days, source, notes and local adaptation status. | catalog variety |
| seedlibops.inventory.accession_number | Seed accession number | invariant | Number uniquely identifies seed lot across donation, storage, borrowing and return records. | avoid mixups |
| seedlibops.inventory.packet_count | Seed packet count | variant | Count tracks packets prepared, borrowed, reserved, expired, returned and discarded. | manage stock |
| seedlibops.donations.donation_intake | Seed donation intake | invariant | Intake records donor, crop, variety, harvest year, growing method, quantity and condition. | accept seeds |
| seedlibops.donations.donor_declaration | Seed donor declaration | invariant | Declaration states seed source, isolation if known, treatment, GMO status if relevant and risks. | assess quality |
| seedlibops.donations.donation_screen | Seed donation screen | variant | Screen rejects moldy, unknown, treated, invasive, illegal or poorly labeled seeds. | protect library |
| seedlibops.cataloging.taxonomy_check | Seed taxonomy check | invariant | Check confirms crop species, common name, variety name and naming consistency. | improve catalog |
| seedlibops.cataloging.trait_notes | Seed trait notes | variant | Notes capture color, flavor, growth habit, disease tolerance, climate fit and user observations. | guide borrowers |
| seedlibops.cataloging.local_adaptation_tag | Local adaptation tag | variant | Tag marks seeds grown and saved locally for multiple seasons or climate conditions. | value resilience |
| seedlibops.storage.cool_dry_storage | Cool dry seed storage | invariant | Storage limits heat, humidity, light and pests to preserve viability. | extend life |
| seedlibops.storage.container_label | Seed container label | invariant | Label shows accession, crop, variety, year, quantity, source and handling notes. | identify stock |
| seedlibops.storage.humidity_control | Seed storage humidity control | invariant | Control uses sealed containers, desiccant, monitoring and dry handling to reduce moisture. | prevent mold |
| seedlibops.storage.pest_protection | Seed storage pest protection | variant | Protection prevents rodents, insects and pantry pests from damaging seed stock. | preserve inventory |
| seedlibops.viability.germination_test | Seed germination test | invariant | Test estimates viability by sprouting sample under controlled moisture and temperature. | check quality |
| seedlibops.viability.test_sample_size | Seed viability sample size | variant | Sample size balances accuracy with limited seed quantity. | conserve stock |
| seedlibops.viability.expiration_review | Seed expiration review | invariant | Review flags old lots by crop, year, storage history and germination result. | rotate seeds |
| seedlibops.borrowing.borrower_record | Seed borrower record | invariant | Record links patron, seed lot, packet count, date, expectations and education notes. | track loans |
| seedlibops.borrowing.checkout_limit | Seed checkout limit | variant | Limit caps packets per person, crop type or season to preserve shared stock. | fair access |
| seedlibops.borrowing.beginner_seed | Beginner seed category | variant | Category offers easy crops with clear instructions for new gardeners. | support success |
| seedlibops.returns.seed_return | Seed return | invariant | Return receives saved seed from borrower with crop, variety, harvest year and growing notes. | replenish stock |
| seedlibops.returns.return_quality_review | Seed return quality review | invariant | Review checks labeling, cleanliness, dryness, pest signs, off-types and donor information. | protect collection |
| seedlibops.returns.growout_feedback | Growout feedback | variant | Feedback records borrower experience, germination, yield, flavor, pests and adaptation notes. | improve knowledge |
| seedlibops.packets.packet_preparation | Seed packet preparation | invariant | Preparation divides seed into labeled packets with enough seed and basic planting guidance. | ready lending |
| seedlibops.packets.planting_instruction | Seed packet planting instruction | variant | Instruction gives sowing depth, spacing, season, days, seed-saving note and caution. | help growers |
| seedlibops.packets.language_access | Seed packet language access | variant | Access adds translated labels or icons for common crops and instructions. | broaden use |
| seedlibops.education.seed_saving_class | Seed saving class | invariant | Class teaches isolation, harvest timing, drying, cleaning, labeling and storage. | build skill |
| seedlibops.education.crop_isolation | Crop isolation education | invariant | Education explains cross-pollination risk and distance or timing controls for seed purity. | improve returns |
| seedlibops.education.seed_cleaning_demo | Seed cleaning demo | variant | Demo shows threshing, winnowing, wet processing, drying and safe handling. | practical learning |
| seedlibops.events.seed_swap_event | Seed swap event | variant | Event exchanges seeds with labeling rules, education table and unsuitable seed screening. | share diversity |
| seedlibops.events.planting_season_display | Planting season seed display | variant | Display highlights seeds appropriate for current local season and climate. | guide choices |
| seedlibops.records.catalog_database | Seed catalog database | invariant | Database stores lots, quantities, sources, tests, loans, returns and notes. | manage data |
| seedlibops.records.donor_log | Seed donor log | invariant | Log tracks donors, donations, accepted lots, rejected lots and follow-up. | acknowledge support |
| seedlibops.records.discard_log | Seed discard log | variant | Log records mold, pests, age, failed viability or policy reason for removal. | audit losses |
| seedlibops.safety.toxic_seed_warning | Toxic seed warning | invariant | Warning flags seeds or plants unsafe for ingestion, pets or children if relevant. | reduce risk |
| seedlibops.safety.invasive_species_check | Seed invasive species check | invariant | Check prevents distributing prohibited or locally invasive plants. | protect ecology |
| seedlibops.safety.treated_seed_exclusion | Treated seed exclusion | invariant | Exclusion avoids pesticide-treated or chemically coated seeds in shared library. | protect users |
| seedlibops.reporting.collection_report | Seed library collection report | invariant | Report summarizes lots, crop diversity, viability, loans, returns and gaps. | manage program |
| seedlibops.reporting.borrowing_report | Seed borrowing report | variant | Report tracks popular crops, seasonal demand, low stock and community reach. | plan supply |
| seedlibops.metrics.return_rate | Seed return rate KPI | invariant | KPI measures borrowed lots that produce usable returned seed. | evaluate cycle |
| seedlibops.metrics.viability_pass_rate | Seed viability pass rate KPI | variant | KPI tracks lots passing germination thresholds by crop, age and storage. | monitor quality |
| seedlibops.coordination.library_branch | Seed library branch coordination | variant | Coordination aligns displays, storage, staff training and local outreach across branches. | scale service |
| seedlibops.continuity.backup_collection | Seed library backup collection | variant | Backup protects important local lots through duplicate storage or partner exchange. | reduce loss |
| seedlibops.close.season_closeout | Seed library season closeout | invariant | Closeout reconciles inventory, returns, test needs, discards, reports and next season gaps. | finish season |
