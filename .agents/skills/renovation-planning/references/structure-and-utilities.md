# Structural-wall assessment and utility mapping

Read this reference by default once the correct apartment is identified, as well as for explicit wall or service questions. Produce an enlarged, annotated existing-conditions plan and perform the structural/service evaluation supported by the inputs without waiting for the user to request each layer. Both workflows depend on the same registered drawing and evidence inventory; they do not require a complete redesign first. Respect an explicit narrower user scope and reuse a valid existing baseline on later edits.

## Default baseline coverage

- Enlarge the correct apartment directly from the original drawing, preserving its aspect ratio and registered coordinate frame. Keep the original accessible and use a separate overlay for annotations.
- Annotate every identifiable internal/perimeter wall with a stable ID. Split a wall into labelled segments if its structure or evidence changes along its length. Do not confuse wardrobes, shafts, piers or columns with walls.
- Evaluate each wall to the extent supported by the actual records. Add its structural-role label and evidence-table entry even when the user only asked for layout work. Where the evidence is insufficient, explicitly mark the role unresolved and identify the discriminating input rather than leaving the wall unassessed without explanation.
- Annotate every supported water/drainage, electrical, ventilation, heating or other relevant service point, not only fixtures proposed to move. Add known physical routes and elevations; show topology-only evidence separately. If a system is not documented, record that gap, not a fictional route or assumed absence.
- Use stable feature IDs and readable callouts linked to source sheet/detail, evidence type and confidence. Structural-role and service-system toggles may reduce clutter while a summary view retains wall IDs and known service points. Do not use a structural colour as a promise that removal is safe.
- Evaluate both evidence quality and renovation implications: supported role/location, uncertainty, mapped or potential conflict, and the next useful check. A useful partial service map is preferable to omitting known fixture locations because concealed routes remain unknown.

## 1. Acquire and classify the right inputs

Ask for or discover only inputs relevant to the question. Useful sources include:

| Evidence | Can support | Does not establish by itself |
| --- | --- | --- |
| Current measured architectural plans, sections and elevations | Wall/opening locations, levels and room geometry | Bearing direction or the contents of a concealed shaft |
| Structural plans, sections, schedules, calculations and details | Floor/roof framing, spans, supports, bearings, beams, columns, stability and intended load paths | That the structure was built and remains exactly as designed |
| Floors immediately above/below, basement/foundation and attic/roof plans | Vertical continuity, transfer points and loads relevant to a target wall | A load path merely because rooms or partitions repeat |
| Demolition/alteration/as-built records | Previous openings, replacement beams, relocated walls/services and changed loads | Current condition when records are incomplete or contradictory |
| Water/drainage/heating, electrical and ventilation plans; riser/single-line diagrams and legends | Documented service topology, systems and sometimes physical routes | Exact routes, heights or wall positions when the sheet is only schematic |
| Site photographs, inspection records, measured survey and professional findings | Visible material, fixtures, outlets, vents, accessible routes, actual framing and deviations | Concealed pipe/cable direction from the fixture alone, or a safe route to cut |

For Sweden, search by the actual sheet discipline and title, for example K/konstruktion, A/arkitekt, VVS/VA, ventilation and EL, together with floor/wing/revision. Prefixes vary by project and era; read the legend/title rather than relying on a filename. A post-renovation record can supersede an original sheet for one system while other geometry remains historic.

Align sheets using stable common features and record any mirror/rotation, origin change or scale difference. Do not stretch one discipline's plan to hide a mismatch. If floors do not register, investigate the discrepancy before comparing continuity.

## 2. Assess a wall by tracing its load path

1. Identify every wall in the confirmed apartment baseline and its extent precisely: stable ID, floor and source wall face/centreline. For a proposed change, identify full removal versus a particular opening. Distinguish a wall from cupboards, flue/shaft boxing, a pier, column or beam enclosure. Prioritise detailed analysis of affected walls while keeping an evidence-based assessment or explicit unresolved status for the others.
2. Read the structural legend and relevant sections/details. Locate floor and roof members, direction, spans, continuity, joist ends/joints and actual supports. A line crossing a wall on a services plan is not a beam.
3. Trace downward and upward where relevant: what loads bear on the wall, how it reaches structure below, and whether an opening/transfer beam or roof post changes that path. Include stability/bracing roles, not just vertical gravity loads. Door openings do not prove the remaining wall is non-bearing.
4. Compare design evidence with current photos, surveys and alteration records. Note mismatches and whether the classification applies to the whole wall or only a segment. An explicitly designed partition can still require checks for later acquired load, changed framing or other functions.
5. State the strongest justified conclusion. With matching, applicable structural records, a wall can be documented as structural or as a partition. With incomplete evidence, state a supported provisional assessment or leave it unresolved. Neither false certainty nor automatic classification of every wall as unknowable is useful.

Suggested output:

| Wall / extent | Assessment | Evidence and applicability | Missing discriminating evidence | Design consequence |
| --- | --- | --- | --- | --- |
| W2, proposed opening | Documented structural / provisionally structural / documented partition / unresolved | Exact sheet, section/detail, revision and relevant support path; whether verified on site | Specific member bearing, concealed beam, current condition or conflicting revision | Conditional opening, potential beam/post/ceiling allowance or no structural change shown in the design record |

“Documented partition” means the applicable record identifies that role; it is not authorization to demolish. Keep distinctions between original design intent, as-built evidence, current observed state and a professional's alteration design. Independently check services, fire/acoustic separation and approvals even when the wall is non-bearing.

Thickness/material and construction era inform hypotheses and source selection. Do not turn a 12 cm brick wall, top-floor location, an apparent short span or a wall parallel to assumed joists into proof. Do not supply percentages unsupported by an actual evidential model. When uncertainty matters, explain which one or two observations would change the conclusion most.

If the next step requires intrusive inspection, identify its purpose and appropriate professional coordination; do not invent a safe drilling/cutting location from uncertain concealed geometry. Beam sizes, structural capacity, temporary support and demolition sequencing require a scoped engineering design, not this concept workflow.

## 3. Produce the supported service map by default

Create toggleable, labelled layers on the same original plan; colour alone must not encode system or confidence. Keep **existing**, **proposed** and **inferred/unlocated** separate. A one-line/riser diagram can be displayed alongside the plan without pretending that its line routing is physical.

For each feature/segment, record system, source sheet/detail/revision, from/to or served fixture, geometry if established, level/elevation if known, relevant dimensions and confidence. Allow unknown geometry: a documented connection may have known endpoints but an unlocated path.

| Layer | Useful fields and checks |
| --- | --- |
| Cold/hot water and circulation | Riser/branch, valves and isolation scope, fixture connection, pipe material/size if specified, access and whether concealed location is verified |
| Wastewater and soil/vent stacks | Drain/riser identifiers, diameter, flow direction, connection/invert elevation, fall and floor/ceiling zone. Do not confuse a plumbing vent with room ventilation. |
| Heating/cooling | Radiators, risers/loops, supply/return, valves and any documented underfloor heating or refrigeration routes. Check maintenance/thermal consequences before concealing or removing an emitter. |
| Electricity | Distribution board, circuits and protection where documented, sockets, switches, lighting, appliance points and traced conduits/cables. Circuit connectivity is not proof of physical cable routing; show an unknown route as unknown. |
| Ventilation/extraction | Supply/extract terminals, shafts, ducts, fan/shared-system connection, direction, dimensions/flows when specified, and access. Distinguish a cooker hood/recirculator from the dwelling's ventilation system. |
| Other applicable systems | Gas, telecom/data/fibre, fire alarm/sprinklers and other building-specific systems. Do not infer presence or absence without evidence. |

### Route evidence and verification

Keep evidence type and confidence separate: an as-built label is not a guarantee, and a directly observed point does not verify a concealed continuation. Assign confidence from applicability, registration, age, contradictions and actual verification, not from a source label alone.

- **Observed / surveyed:** identify the inspection or measurement and accessible extent; do not generalize beyond it.
- **As-built documented:** route is physically drawn in applicable as-built records, with current agreement or any verification limits noted.
- **Design documented:** route is shown in a design drawing; installed agreement remains unverified.
- **Inferred zone / topology only:** show a dashed band, unlocated link or question marker, not a precise solid centreline. Explain the inference.
- **Unknown / conflicting:** retain both conflicting sources and the question; no convenient invented route.

Only use an exact XY line where the source supports that precision. Carry Z/level and concealment information (floor void, wall, ceiling, shaft) when relevant to feasibility. A flat plan alone cannot establish drainage fall, duct clearance or whether two runs collide at different levels.

## 4. Use the layers to evaluate the renovation

Overlay proposed removed walls, new cabinets/fixtures, island anchors and new service demand against the source map. Identify intersections and uncertainty bands: hidden services in a wall, a proposed fixing near a conduit, drain route through a structural zone, inaccessible shut-offs, shared duct changes, or a penetration through a fire/acoustic boundary.

An apparently clear drawing is not proof that an area is free of concealed services. Separate **mapped conflict**, **potential conflict because location is uncertain**, and **no conflict shown in the available records**.

Show what new inputs would resolve the decision: a specific service/structural sheet, connection height, accessible shaft photograph, tracing/survey result or qualified inspection. Continue independent planning while those are obtained. Proposed routes remain concept options until dimensions, capacity, gradients, installation rules, access and permissions are verified.

## Deliverables

- A readable enlargement of the confirmed apartment's original plan with all identifiable walls annotated and registered across views.
- Structural-role annotations and a source-linked wall assessment table, making supported conclusions and unresolved roles explicit by default.
- Supported existing service points/routes, per-system layers, a legend, evidence/confidence and explicit coverage gaps by default; proposed layers when alterations are considered.
- A short list of the highest-impact next measurements/checks, rather than a generic demand for all possible documents.
- A concise statement of what the evidence now establishes and what still prevents a construction-ready conclusion.
