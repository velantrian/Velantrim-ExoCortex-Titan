# BATCH_173 — Print Shop Operations Detail
# world_skills_core · source: world_skills_core:batch_173:print_shop_operations_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| printops.intake.job_ticket | Print job ticket | invariant | Job ticket records customer, artwork, quantity, substrate, colors, finishing, due date and approvals. | one source for job |
| printops.intake.spec_review | Print specification review | invariant | Review checks size, paper, color, bleed, binding, variable data and delivery requirements. | clarify before production |
| printops.intake.artwork_receipt | Artwork receipt | invariant | Receipt logs file source, version, date, format and customer contact. | track supplied files |
| printops.intake.quote_basis | Print quote basis | variant | Quote basis estimates material, setup, run time, finishing, waste, outsourcing and delivery. | price from process |
| printops.intake.rush_job | Rush print job | variant | Rush job compresses planning and increases need for clear approvals, capacity check and risk note. | speed has tradeoffs |
| printops.intake.change_order | Print change order | invariant | Change order documents customer-approved changes to artwork, quantity, schedule, material or price. | prevent hidden scope creep |
| printops.prepress.preflight | Preflight check | invariant | Preflight checks fonts, links, resolution, bleed, color spaces, page size and file integrity. | catch file problems |
| printops.prepress.bleed | Bleed | invariant | Bleed extends artwork beyond trim edge to avoid white gaps after cutting. | design for cutting |
| printops.prepress.imposition | Imposition | invariant | Imposition arranges pages on sheet for printing, folding, binding and trimming sequence. | pages in production order |
| printops.prepress.color_profile | Color profile | invariant | Color profile defines how color values map to device or print condition. | color translation |
| printops.prepress.rip_processing | RIP processing | invariant | RIP converts artwork into printer-ready raster or plate instructions. | file becomes press data |
| printops.prepress.variable_data_merge | Variable data merge | variant | Merge combines template with data records for personalized print while controlling proof and privacy. | every copy may differ |
| printops.proofing.soft_proof | Soft proof | variant | Soft proof shows digital preview but cannot fully prove substrate, ink, finish or device output. | screen is approximate |
| printops.proofing.hard_proof | Hard proof | invariant | Hard proof physically demonstrates color, layout, paper or finishing before production approval. | approve tangible result |
| printops.proofing.proof_approval | Proof approval | invariant | Approval records customer or internal signoff before production proceeds. | no print without signoff |
| printops.proofing.proof_revision | Proof revision | invariant | Revision tracks changes between proof versions and prevents mixing old and new artwork. | version control |
| printops.proofing.contract_proof | Contract proof | variant | Contract proof becomes agreed visual reference for acceptable production output. | standard for dispute |
| printops.proofing.press_check | Press check | variant | Press check reviews live production sheet for color, registration and defects before full run. | approve at machine |
| printops.press.make_ready | Press make-ready | invariant | Make-ready sets plates, ink, registration, substrate feed, color and quality before saleable production. | setup before run |
| printops.press.registration | Print registration | invariant | Registration aligns colors or print passes so images and text fit correctly. | prevent color misalignment |
| printops.press.ink_density | Ink density | invariant | Ink density measures printed ink strength and helps control consistent color. | color control metric |
| printops.press.dot_gain | Dot gain | invariant | Dot gain is increase in printed dot size compared with file or plate and affects tone. | press changes image |
| printops.press.blanket_wash | Blanket wash | variant | Blanket wash removes ink, paper dust and debris from offset blanket to restore print quality. | maintain image transfer |
| printops.press.sheet_pull | Sheet pull | invariant | Sheet pull samples production output for inspection at defined intervals. | quality during run |
| printops.digital.toner_calibration | Digital press calibration | invariant | Calibration aligns digital output for density, color, registration and consistency. | keep machine stable |
| printops.digital.substrate_setting | Digital substrate setting | invariant | Substrate setting configures printer for paper weight, coating, size and feed behavior. | avoid jams and defects |
| printops.digital.click_charge | Click charge | variant | Click charge is per-impression cost used in digital print pricing and job costing. | cost per print |
| printops.digital.variable_data_qc | Variable data QC | invariant | QC verifies record count, sample personalization, sequence and data-field mapping. | avoid personalized errors |
| printops.finishing.cutting | Guillotine cutting | invariant | Cutting trims stacks to final size using guides, clamps, blade condition and safety procedure. | final size accuracy |
| printops.finishing.folding | Folding operation | invariant | Folding creates panels or signatures and requires correct grain, sequence, score and alignment. | mailers and brochures |
| printops.finishing.binding | Binding operation | variant | Binding joins pages by saddle stitch, perfect bind, coil, wire or other method. | turn sheets into product |
| printops.finishing.lamination | Lamination | variant | Lamination adds protective film and requires heat, pressure, adhesion and trim allowance control. | finish changes durability |
| printops.finishing.die_cut | Die cutting | variant | Die cutting shapes printed material using die, pressure, registration and waste stripping. | custom shape |
| printops.finishing.kitting | Print kitting | variant | Kitting groups multiple printed pieces into sets for fulfillment or distribution. | assemble deliverable |
| printops.quality.color_variation | Color variation | invariant | Variation arises from substrate, ink, machine, environment, profile or batch changes. | color not magic |
| printops.quality.hickey | Printing hickey | invariant | Hickey is a spot or defect caused by debris, dried ink or contamination. | small speck, visible defect |
| printops.quality.misfeed | Press misfeed | invariant | Misfeed disrupts sheet handling and may cause waste, damage or registration errors. | feed reliability |
| printops.quality.spoilage_count | Print spoilage count | invariant | Spoilage count tracks unusable sheets from setup, defects, damage or overrun. | waste control |
| printops.quality.retention_sample | Print retention sample | variant | Retention sample preserves representative output for reference, dispute or repeat job. | keep evidence |
| printops.material.paper_grain | Paper grain direction | invariant | Grain direction affects folding, cracking, stiffness and binding behavior. | paper has direction |
| printops.material.paper_conditioning | Paper conditioning | variant | Conditioning lets paper acclimate to shop humidity and temperature to reduce curl or misfeed. | environment matters |
| printops.delivery.packaging | Print delivery packaging | invariant | Packaging protects finished print from bending, moisture, scuffing and mixing during delivery. | product leaves safely |
| printops.delivery.delivery_manifest | Print delivery manifest | invariant | Manifest records boxes, quantities, destination, carrier, due date and proof of handoff. | close the job |
| printops.delivery.job_closeout | Print job closeout | invariant | Closeout confirms delivered quantity, spoilage, samples, invoice status, file archive and customer notes. | finish with records |
