# Registration, project state and useful arithmetic

## Keep one durable model

Store the originals unchanged. A small project directory can contain `sources/`, `project.json`, a generator, `report.html` and SVG/PDF exports. It need not use this exact structure; the requirement is that the next iteration can reproduce the output without relying on session memory or `/tmp` scripts.

Record:

- Source file/URL and fingerprint, discipline, building/floor, revision, current-vs-historic status and evidence confidence.
- Native image size, original printed scale, DPI metadata, crop box and every subsequent resize/rotation/reflection. Separate the source frame from presentation size.
- Chosen scale, calibration feature(s), physical units, method and uncertainty. Keep alternative/contradictory measurements visible.
- Shared existing geometry and stable feature IDs. Variants reference that geometry rather than maintaining separately drawn shells.
- User constraints and their origins, anchors, accepted compromises, retained alternatives and outstanding measurements. Do not put private project details in the shared skill.

Use explicit fields such as `kind: user-preference`, `value: 0.85`, `units: m`, `surface: finished-front`, `state: closed`, `source: user-message` instead of an unexplained numeric constant. An applicable requirement needs its actual source, scope and date.

## Calibrate without manufacturing certainty

Known span: `pixels_per_metre = measured_pixels / physical_metres`.

Candidate scale from an unchanged drawing reproduced at its stated DPI:

`pixels_per_metre = DPI / 25.4 × 1000 / scale_denominator`.

Multiply by the image resize factor to express it in the displayed frame. Cropping changes the origin but not scale. Rotation/reflection changes axes and anchor locations. For a drawing reduced onto microfilm, copied or reprinted, metadata alone may not preserve the original paper scale. A graphic scale or physical dimension usually survives uniform resizing better than the printed ratio.

Area conversion: `area_m2 = polygon_area_pixels / pixels_per_metre²`.

If explicitly using a reference total for uniform area normalization:

- Keep raw area `A_raw` and target `A_target`.
- Coordinate dimensions effectively multiply by `sqrt(A_target / A_raw)`.
- Equivalently, effective pixels/metre becomes `old_pixels_per_metre × sqrt(A_raw / A_target)`.
- Do not stretch the building shell or different rooms independently. State that the target is assumed; agreement of the normalized total cannot validate itself.

Compare area definitions: internal measured area versus gross footprint, walls, cupboards, balconies, shared stairs, low ceiling/headroom and exclusions. Investigate a material discrepancy before drawing exact fit conclusions. Never force a marketing area by omitting a room or counting circulation twice.

For an L-shaped room, its maximum X and Y spans are not two sides of an equal-area rectangle. State the polygon area separately. Island footprint, working zone and living circulation can overlap in function; area allocations should still form a non-overlapping ledger when reporting a total.

## Geometry must agree with the picture

Make a registered existing-geometry overlay first, then inspect it over the original at useful zoom. Confirm opening counts/types and IDs against current photos. Historical plans can show an opening now converted into a balcony door; document that difference rather than adding another opening.

Render every requested alternative using that same underlay and fixed geometry. If the drawing underlay is masked for readability, mask only fittings, labels or proposed changed geometry; do not white out unreviewed fixed walls or openings. Keep the raw source view available.

For a clean redraw, support it with an opacity/overlay comparison so misregistration is visible. Productive visual inspection includes walls meeting at corners, doors swinging into fixtures, labels hiding dimensions, counters spanning shafts and scale/area labels matching the rendered geometry.

Compare clearance between the actual relevant faces. A cabinet front aligned above a bathroom step may be unreachable despite fitting within a rectangle. In an offset island, an X gap can be a side passage but not an opposed cooking aisle. Keep that semantic distinction in labels and tables.

## Minimal optional audit model

Run the dependency-free helper from the skill directory:

```bash
python3 scripts/plan_math.py calibrate --pixel-span 1000 --length-m 5
python3 scripts/plan_math.py calibrate --dpi 300 --denominator 20 --image-factor 0.5
python3 scripts/plan_math.py audit project.json
```

The second command returns a **candidate** scale; it does not establish that the scan preserves the print size. `audit --strict` exits 1 for drift, unresolved/insufficient gaps or boundary crossings, including intentional crossings; ordinary `audit` reports them without failing. Invalid inputs exit 2. A strict failure is a review flag, not a request for user permission or a reason to discard a knowingly accepted alternative.

Example `project.json` (arbitrary teaching geometry, not a real apartment):

```json
{
  "source": {
    "pixels_per_metre": 100,
    "scale_status": "dimension-derived",
    "reference_area_m2": 20
  },
  "zones": [
    {"id": "room", "polygon": [[0, 0], [500, 0], [500, 400], [0, 400]]}
  ],
  "fixed_geometry": {"W2": [[400, 0], [400, 200]]},
  "variants": [{
    "id": "island-option",
    "geometry": {"W2": [[400, 0], [400, 200]]},
    "rectangles": {
      "run": {"x": 100, "y": 100, "width": 300, "height": 60},
      "island": {"x": 215, "y": 245, "width": 185, "height": 80}
    },
    "clearances": [{
      "id": "working-aisle",
      "a": "run", "b": "island", "axis": "y",
      "minimum_m": 0.85, "uncertainty_m": 0.02,
      "constraint_source": "user-preference",
      "state": "closed"
    }],
    "boundaries": [{
      "id": "old-W3", "rect": "island",
      "axis": "y", "edge": "max", "limit": 300,
      "relation": "<=", "constraint_source": "user-preference"
    }]
  }]
}
```

This should report 20 m², unchanged W2, an 85 cm nominal aisle (83 cm lower bound under the supplied uncertainty), and a 25 cm W3 crossing. The helper does not automatically resize the model to the reference area or choose which preference to change.

### Audit limits

The zone sum assumes valid non-overlapping polygons without holes; independently check coverage/overlap with a geometry library or CAD tool when it matters. The helper explicitly does not compute polygon unions, validate self-intersections or prove room containment.

Its gap calculation is only for axis-aligned rectangles with overlapping perpendicular projections. It returns `not_opposed` for a diagonal/offset pair. It does not calculate a person's route, handles, door sweeps, curved walls or rotated furnishings. Supply separate open-state envelopes and checks where useful, or use a capable geometric tool.

Compare pinned geometry in the **source frame**, not coordinates rounded for display. Exact equality is deliberate: if an input's precision or source geometry changes, update the shared geometry with a recorded reason rather than tolerating silent drift.

## Translate the request before solving the layout

Keep positional anchors, orientation and opening behaviour as separate data. Record which edge/surface aligns to which reference and the front direction in the declared axes. A feature can keep its maximum-Y edge on a boundary while its door faces +X. “Start at the old wall” does not establish which face is anchored. Resolve that distinction early if it changes fit; do not turn an uncertain reading into an impossible-layout verdict and then shift the user's feature to repair it. A compact source overlay with a reference line, anchor mark and facing arrow is more useful than a long verbal interpretation.

For a rotation, distinguish the appliance body, reserved bay, finished fronts and opening envelope. Swap width/depth along the axes where appropriate; do not resize unrelated rooms when the existing bay can accommodate the rotated body. Label any leftover space as reserved allowance, not automatically usable storage or a manufacturer-approved filler. Recalculate access perpendicular to the new front and remove the old-direction access annotation. A removed wall remains a planning reference, not an opposing physical obstruction.

For an L/U run, write the ordered chain before sizing it: appliance → intermediate bay → corner/turn → next leg. State whether “two more sections” includes the turn and distinguish width along a run from depth across it. Count shared corners once; budget panels, fillers and actual appliance envelopes separately. Clarify only counts that materially change the result.

A shared circulation area can supply appliance access without becoming additional kitchen floor area. Keep the area ledger unchanged unless the room boundary itself moves; show open-door effects on that shared route. For stepped rooms, report the main usable rectangle and narrow storage pocket separately alongside total area.

## Efficient iteration

1. Translate a request into a small constraint change: e.g. storage width 40→60 cm, keeping the finished right edge fixed.
2. Derive the new geometry and affected passages from the model. Recompute every retained option to which the request applies.
3. Show the consequence, not just the new size: left passage, boundary crossing, lost office area or changed appliance format.
4. Update drawing, table and export from the same data. Preserve the old alternative only if useful or requested; label it as superseded.
5. Check that final summaries reference the actual visible variant and that all controls still work after adding/removing views. Verify unrelated states stayed unchanged using model comparisons or geometry/export fingerprints where useful; scope validation to affected geometry and interactions.

For an explicitly fresh reevaluation, previous assistant drawings and conclusions are derived outputs, not independent evidence. Recheck their decision-critical assumptions against the supplied sources, retain user clarifications, and keep uncertain interpretations separate from confirmed measurements.

No universal island size or aisle minimum follows from the example. If a user accepts a narrower nominal gap, do not silently claim that all appliances open comfortably or that the layout meets applicable accessibility/building requirements.
