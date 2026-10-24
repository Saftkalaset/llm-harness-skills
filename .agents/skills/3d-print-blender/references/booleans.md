# Editable geometry, mating surfaces and motion

## Boolean architecture

Use watertight analytical cutters where practical. For compound features, a single closed profile often avoids overlapping-cutter ambiguities. `rect_2d`, `rounded_poly_2d`, `set_extruded_profile` and extrusion helpers retain profile metadata. Keep live booleans while revising parameters; freeze only at an intended milestone.

If the installed Blender offers the MANIFOLD solver, verify that both inputs meet its closure requirements. An unsupported solver or invalid input is not a successful cut; inspect evaluated bounds/geometry. Use a supported alternative such as EXACT where appropriate and recheck the result.

Prefer the context-independent `apply_modifiers()` helper over assuming selection-sensitive operator context. Before deleting a regional mesh section, split any shared large n-gon across the intended boundary; otherwise an entire cap can disappear. Recheck manifold integrity after local edits.

Use shared parameters or a Mirror modifier for genuinely symmetric features. Do not impose symmetry where hardware, printing or access differs. Keep a coherent functional coordinate frame and avoid silently rebaking offsets in existing meshes.

## Functional surfaces and structure

Fit the complete contact geometry, including shoulders, feet, ridges, cable plugs and insertion clearances. An outer silhouette or nominal bore diameter alone may miss interfering features. State per-side and total allowances, and separate CAD targets from measured printed dimensions. Preserve hardware elevations required for airflow.

Put material where relevant load paths require it; compare alternative structural layouts against available space, print direction, support removal, mass and thermal exposure. Do not thin/remove reinforcement solely because it crosses a keep-out without replacing its structural function.

`audit_cantilever(part, axis='X', root_pos=..., tip_pos=..., load_n=..., e_mpa=..., slices=...)` screens an ideal homogeneous solid beam with uniform load and fixed root. It derives sections from the evaluated mesh, but its stresses/sag are approximations for the actual printed structure. Disconnected truss sections, joint/shear compliance, sparse infill, layer anisotropy, foot point loads and warm creep are outside the model. Use relevant assembly loads and a justified effective modulus; there is no default universal allowable stress or lifetime inference.

## Fit and insertion

`check_fit(part, reference, tolerance=..., allow_contact=True)` samples strict interior points in world coordinates to distinguish contact, penetration/containment and unresolved cases. Open meshes, conflicting ray parity and sample-budget exhaustion remain unknown. Thin crossings may require finer geometry sampling or another solid-intersection method.

`check_insertion(part, reference, path_vec=..., max_step_mm=..., final_step_mm=..., final_distance_mm=...)` limits movement between samples, refines final engagement and checks the seated state separately. `steps` is only a compatibility hint and cannot silently override the distance limits. Paths exceeding the position budget require an explicit choice rather than a misleading pass.

Check the actual installation/removal route, not just a large vertical sweep. Mechanisms may require different released/locked states and should demonstrate both intended clearance and retention interference. A prescribed leaf deformation checks geometric space, not release force, strain life or manufacturability. Avoid assuming friction-based self-locking without measured material/contact behavior.
