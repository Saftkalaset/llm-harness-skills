# Iteration and acceptance gates

Before detailed geometry, record confirmed interfaces, material/assembly choices, clearance envelope, allowable bulk changes and print-time/material priorities. Compare simple concepts where their tradeoffs differ. Inspect existing work read-only; reuse measurements with valid provenance and investigate contradictory/stale data.

For new designs establish references/frames, build the connected primary body, then add features/refinement. Check the base before booleans requiring closed input. For existing parametric models, batch related parameter/cutter updates and audit together instead of many small calls.

Batching is not a transaction: checkpoint before destructive replacements and restore on failure. Keep one scene writer. Check the changed constraint first, then relevant complete checks on the frozen result. Repeat checks only when changed inputs, failures or unresolved concerns justify them.

| Gate | Evidence |
| --- | --- |
| Geometry | Evaluated integrity, expected printable components, references excluded from exports |
| Fit/motion | Common frame; separate contact/penetration checks; path resolution and release states |
| Printing | Orientation/removal access; effective settings; support/brim/skirt bounds including margin and extrusion width |
| Functional limits | Applicable load/thermal/creep assumptions; physical tests outstanding |
| Delivery | Matching frozen hashes; actual artifact units, instances, placement and settings |

Mesh integrity alone cannot satisfy other gates. A low beam stress, zero surface crossings or successful CLI exit is not overall readiness.

Preserve the previous milestone, current parameters and verification scope. Separate neutral geometry from configured projects. Use normal permission controls when publication is outside authorized locations; staging does not bypass that boundary.
