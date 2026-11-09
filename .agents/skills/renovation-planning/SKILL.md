---
name: renovation-planning
description: Assess renovation drawings and, by default, annotate the identified apartment's walls and available utilities, evaluate structural-wall evidence and compare layouts on registered original plans. Includes scale/area checks and service constraints; not structural certification or construction documents.
---

# Renovation Planning

Build an evidence-based concept that the user can inspect and iterate without the existing building drifting between drawings. Distinguish spatial fit, technical feasibility, approvals and construction readiness; proving one does not prove the others.

## 1. Establish the building before designing

Before prolonged research, check whether the intended outcome, property/apartment identity and usable evidence are sufficient for the next step. Inspect what the user already supplied before asking. If essential information is missing, bundle the highest-impact questions early (usually one to three), explain what each enables and state a recommended way forward. A listing link is optional when adequate drawings/measurements exist; do not require an address for an anonymized concept. Read the intake and research-stop guidance in [renovation-considerations.md](references/renovation-considerations.md).

- If neither a drawing nor a listing/photo reference is supplied, request a usable starting point: an existing plan, listing link, or measured sketch with openings and a few dimensions. First establish whether the user wants an evidence-based assessment or a rough concept; do not spend a long time searching an unidentified property or invent a registered plan.
- Where the property is identifiable and research is within the request, do a focused discovery pass to locate likely records. If it does not resolve a decision-critical gap, ask for the missing identifier/document or research direction before repeating speculative archive/gallery searches. This is clarification of missing inputs, not a new permission gate for ordinary read-only research.
- Pause only the dependent conclusion: an unidentified apartment blocks apartment-specific annotations, missing scale blocks reliable dimensional fit, and insufficient structural/service evidence blocks definitive claims about those features. Continue useful inventory, planning or clearly labelled concept work. Do not withhold supported partial assessments just because the entire document set is incomplete.

- Inspect the supplied drawing set, not only the attractive plan. Make a contact sheet and a compact inventory of sheet title/number, discipline, building/wing, floor, revision/date, scale and relevance. Enlarge title blocks and critical details from the original resolution. Convert one-bit scans to grayscale before downsampling so fine lines remain visible.
- Confirm the actual apartment and floor convention, including courtyard/street wings, mezzanines, attic levels, and mirrored or rotated layouts. A typical-floor plan, service riser and alteration to a different apartment are not interchangeable.
- Use supplied listing links, photographs, energy records and association/owner documents early. Establish the reported construction year and distinguish it from drawing, renovation and valuation dates. Review gallery images for window/door counts, radiators, cupboards, shafts, thresholds, ceiling drops and recent changes. Preserve source URLs and dates. Photo composition and marketing plans do not supply reliable centimetre measurements.
- Identify what evidence is missing: architectural plan/section, structural framing and roof supports, service routes, current survey or later alterations. Continue independent concept work while requesting only missing facts that affect a decision.
- Inspect image dimensions, orientation, alpha and visible content before using a user sketch. Composite transparency over white for inspection. If no visible pixels exist, state that clearly and request another image or a text description; do not claim to see marks. Let a legible rough sketch establish placement intent, not exact scale.

## 2. Register and calibrate once

Read [geometry-and-state.md](references/geometry-and-state.md) when measuring or changing a plan. Keep one source coordinate frame, registration transform and geometry model shared by every view.

- Preserve the original as a fixed underlay. Trace existing outlines and openings directly over it; use clean vector overlays or a source-registered redraw. Do not invent an exterior or distribute windows by eye. If a full clean redraw is requested, verify its overlay against the source first. Image generation is not a source of measured building geometry.
- Define axes and units visibly: for example X rightward and Y downward on the sheet. Resolve ambiguous words such as “lower” by describing the intended direction before moving geometry. Record cropping, resizing, rotation and reflection transforms.
- Prefer dimension lines, a graphic scale or direct measurements for calibration. A printed ratio plus scan DPI is a candidate scale only after checking the reproduction/crop history and an independent dimension or area. Check horizontal and vertical references; do not silently stretch one axis to make a plan fit.
- Use the stated total area as a consistency check, with its area convention. If the user wants area-normalized estimates, show the raw scaled area, reference area and single uniform adjustment explicitly. Matching a requested total is not independent proof of room dimensions or cabinet fit.
- Zone the separate rooms and reconcile their areas before layout calculations. Distinguish actual polygon area, bounding X/Y spans, usable area after cupboards, fixture footprint, and shared circulation. Do not double-count an island added to a living-room zone. Label estimates with practical precision and include their uncertainty.

### Default annotated existing-conditions baseline

Once the correct apartment is identified, automatically produce a readable enlargement of its original plan with a source-registered annotation overlay. Do this before proposing alterations unless the user explicitly narrows the task; do not wait for a separate request for wall or utility assessment.

- Identify **every distinguishable wall**, including internal and perimeter walls, using stable IDs. Preserve existing user-agreed IDs; use segment suffixes where evidence differs. Distinguish columns, shafts and cupboard outlines from walls. Add a structural assessment for each wall/segment wherever the available evidence supports one, with a source-linked assessment table; label unsupported cases unresolved rather than silently omitting them or inventing a verdict.
- Annotate **all supported utility locations**: water/drainage points and risers, electrical points/boards, ventilation terminals/shafts, heating and other relevant services. Include documented physical routes when available. Do not restrict the baseline to the proposed alteration area. Evaluate the evidence for each relevant system and record missing/uncertain coverage; a lack of exact routes must not suppress useful known fixture locations.
- Read [structure-and-utilities.md](references/structure-and-utilities.md) for this baseline. Make the load-bearing evaluation and service interpretation explicit when sufficient inputs exist, even if the immediate request is a room-layout change. Distinguish documented conclusions, provisional assessments and unknowns; wall labels are not demolition approval.
- Include a legend, readable feature labels, source references and per-feature confidence. Provide toggles for wall roles and utility systems where combined annotations would obscure the plan. Keep the original, enlargement and overlay registration intact; do not redraw the shell or add openings to make annotations easier.

Create this baseline once and carry it into subsequent alternatives. Reuse it on routine edits; revise affected evidence/annotations when new records, photographs or measurements arrive instead of repeating the whole investigation each turn.

## 3. Keep decisions and constraints explicit

Maintain a small project record beside the deliverable: source inventory, calibrated geometry, pinned features, current requirements, alternatives, unresolved questions and next measurements. Keep reusable generators and model data there rather than depending on temporary scripts or hard-coded edits to generated HTML.

- Give features stable IDs (e.g. W1–W5) anchored to source geometry. Preserve agreed fixed walls, shafts, windows, radiators and services across alternatives. A proposed removal does not erase the old boundary as a planning reference.
- Classify constraints as: **user requirement**, **user preference**, **manufacturer requirement**, **verified applicable rule**, or **design recommendation**. Cite and date externally sourced requirements. Do not silently promote a recommendation to a mandatory minimum, or turn this session's aisle choice into a universal default. A user preference cannot override an applicable legal or manufacturer requirement; explain a verified conflict.
- Record the reference surface: finished outer face, carcass, worktop edge, handle, wall face or centreline. “Fridge edge on W2” and “glass on W2” should become coordinate constraints, not visual approximations. Model position and facing direction independently: a lower edge on a Y boundary does not imply a downward-facing door. Before declaring a conflict or moving a feature, resolve any uncertain anchor that would materially change the result; use a small annotated source view and a focused question when needed.
- Name the anchor when resizing or rotating. Increasing storage may keep the hob centre, island centre or one outer edge fixed; rotating an appliance may preserve its bay while swapping the body’s width/depth axes. Recompute its front access and opening envelope in the new direction. See the request-to-geometry guidance in [geometry-and-state.md](references/geometry-and-state.md).
- Retain requested alternatives as separate states, with shared constraints and explicit option-specific overrides. A new no-island option does not remove islands from earlier alternatives or inherit their island requirement. Make targeted edits from the shared geometry; apply common changes to every affected state, including nested options. Update drawings, labels, tables and requested tab order together; remove superseded assumptions from the active view.

## 4. Test the spatial and technical fit

Read relevant rows of [renovation-considerations.md](references/renovation-considerations.md), not an indiscriminate checklist. Resolve service and access constraints before polishing furniture.

Use the relevant architectural/structural/services sheets to maintain the baseline wall assessment and source-registered service layers, then evaluate the proposed layout against them. With suitable inputs, make supported conclusions and useful maps; do not substitute either a speculative route or a blanket refusal for analysing the evidence.

- Use exact manufacturer formats and installation drawings when products matter. Separate nominal cabinet widths from panels, fillers, worktop overhangs, ventilation and service depth. An appliance bay is not automatically a standard cabinet carcass. Leave uncertain hardware as a labelled reservation, not an invented off-the-shelf mechanism.
- Budget the entire run. Check that every sink/appliance/drawer front can be approached; a unit can fit on paper while a bathroom step blocks its use. A blind corner has no front access. Side-access or pull-out storage requires a mechanism-specific check and supported worktop.
- Measure aisles between finished envelopes, with the relevant faces actually opposed. A horizontal gap between diagonally offset objects is not a working aisle. Show closed-front space separately from door/drawer/oven opening and the remaining route. Check pinch points, fridge drawer removal, seating and maintenance access.
- Overlay legacy boundaries and report crossings in centimetres. Do not push an island into the hall or living room without making the change visible. If requirements conflict, show the smallest useful trade-off: smaller office, shallower island, narrower appliance, alternate location, or accepted boundary crossing. Do not repeatedly declare a layout impossible because of an unaccepted preferred clearance.
- Thin walls, age, repeated layouts, area, doors and apparent joist direction are clues, not structural proof. Use qualitative evidence and uncertainty; avoid invented load-bearing probabilities or simplistic thickness rules. Verify actual bearings, concealed beams, roof/attic loads, stability and later alterations with the appropriate records/professional before treating removal as feasible.
- Overlay documented water, drainage, heating, electricity, ventilation and other relevant utilities separately from proposed routes. Keep source, location/elevation and confidence per segment; distinguish schematics from physical routes. Unknown hidden runs remain unknown, rather than being connected by convenient straight lines.
- Keep work reversible at concept stage. Do not prescribe demolition, temporary propping, beam sizes, electrical work or modifications to shared services from a layout sketch. Identify the specific survey, professional check or approval needed; do not block unrelated design work.

## 5. Deliver and verify the comparison

- Prefer a self-contained HTML comparison with an annotated **Current** underlay and clearly named proposal tabs. Use the `html-presentation` skill when available; otherwise generate portable HTML/SVG directly and use the available browser, reporting launch failures accurately. Keep model, generator and SVG exports with the project.
- The **Current** view defaults to the enlarged original with all wall IDs and supported utility-point annotations, plus accessible structural-role and per-system layers. Show the baseline assessment and evidence gaps even when no alteration has yet been proposed.
- Reuse the exact same registration and fixed geometry in every view. Show zones, approximate X/Y dimensions, usable/fixture areas, appliance widths, aisles, legacy boundaries and changed elements. Keep key constraints visible without burying the plan in engineering notes.
- Check registration, source opening counts, preserved geometry, total-area accounting, clearances, product budget, headings, file links, tab controls and exports. Inspect the rendered result; code/XML validation alone does not catch a misleading drawing. Check text/background pairs in dark and light themes, including nested tables, selected buttons and SVG labels.
- With uncertain source dimensions, test whether the clearance remains above its minimum under the stated uncertainty. Nominal equality to a minimum has no tolerance margin; describe it accordingly.
- Report the final change, its practical consequence and what still needs measuring. Do not repeatedly present superseded estimates as current. Do not claim that an unseen listing, failed image fetch or unrendered view was reviewed.

## Supporting tools

`scripts/plan_math.py` provides calibration arithmetic and a small model audit for area sums, pinned-geometry drift, opposed rectangular gaps and legacy-boundary crossings. It is a partial geometry check, not a renderer, polygon-union checker, collision solver or compliance assessment. See the model example and limitations in [geometry-and-state.md](references/geometry-and-state.md).

For origin and re-evaluation notes, see [upstream.md](references/upstream.md). No apartment-specific dimensions, construction assumptions or aisle minima are defaults of this skill.
