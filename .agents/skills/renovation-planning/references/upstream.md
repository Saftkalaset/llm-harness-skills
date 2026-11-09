# Provenance and re-evaluation

This skill was developed from the user's drawing-based apartment planning session on 2026-11-08–09. It does not adopt that apartment's dimensions, wall classifications, 85 cm aisle preference or regulatory assumptions as general defaults. Session artifacts remain in their project; private addresses, photographs and ownership information are not bundled in the skill.

No external skill implementation or source code was copied. The math helper is a local implementation of elementary planar geometry.

| Source | Version / date evaluated | Borrowed concept | Local divergence / limit | Re-evaluate when |
| --- | --- | --- | --- | --- |
| [Boverket: Förundersökning vid ändring](https://www.boverket.se/sv/PBL-kunskapsbanken/regler-om-byggande/barformaga-stadga-bestandighet/andring-av-byggnad/forundersokning/) | Live web guidance accessed 2026-11-09; no pinned revision | Investigate the existing structure and actual condition before relying on alteration assumptions. | Used as a research/uncertainty principle, not a comprehensive legal procedure or wall-removal method. | Guidance changes, a different jurisdiction, or moving from concept to regulated design. |
| [Stockholms stad: Hitta ritningar och detaljplaner](https://bygglov.stockholm/kontakta-oss/hitta-ritningar-och-detaljplaner/) | Search/page evidence evaluated 2026-11-08–09; later direct fetch timed out | Distinguish architectural, structural and services records; request the missing discipline. | No Stockholm-only workflow, contact details or availability guarantees embedded. | Archive service/location/process changes, or working outside Stockholm. |
| [IKEA METOD 40 cm base frame](https://www.ikea.com/se/sv/p/metod-baenkskap-vit-80213432/) and [60 cm appliance frame](https://www.ikea.com/se/sv/p/metod-baenkskap-f-inbyggda-vitvaror-diskho-vit-70213569/) | Product pages evaluated 2026-11-09 | Budget nominal modules separately from finishes, fillers, services and appliance bays. | No standard island size, module combination or procurement recommendation prescribed. Confirm actual current products/manuals for each project. | Product/range changes, a different market or selecting an exact appliance. |
| [IKEA island installation guide](https://www.ikea.com/se/sv/files/pdf/b5/50/b5507aa4/se_enhet_installation_guide_april22.pdf) | April 2022 guide, evaluated via indexed primary-source content 2026-11-09 | Trace a clearance recommendation to its source and distinguish it from a user preference or applicable requirement. | The guide's 120 cm planning dimension is not a universal mandatory minimum. This skill makes no substitute clearance rule. | Updated guidance, an exact installation specification, accessibility obligations or changed user priorities. |

## Session-derived corrections

- Research construction dates and current photographs before forming era-dependent hypotheses or redrawing openings.
- Register the original drawing first. Repeated freehand reconstructions introduced erroneous windows and shifted boundaries.
- Calibrate and allocate room polygons before claiming fit. An area-normalized total is a stated assumption, not an independent measurement.
- Keep manufacturer's recommendations, user choices and verified requirements distinct. Relaxing a preferred aisle can substantially change the feasible design.
- Show boundary crossings and trade-offs rather than silently moving an island into another room.
- Check transparent uploads, dark-theme table contrast and all requested alternatives, not just the newest drawing.

- Later layout iterations exposed a coupled-anchor error: an assumed appliance position was treated as fixed, producing an unnecessary conflict and offset. Separate position, facing direction and opening behaviour; clarify the decisive anchor before redesigning.
- Record ordered cabinet chains, option-specific exceptions and shared access zones. A rotation can change the access direction without changing room boundaries or the reserved bay; a removed wall is still a reference, not a physical aisle limit.
