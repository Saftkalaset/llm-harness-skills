# Overhangs, supports and mesh checks

`audit(part)` evaluates modifiers/transforms without cleaning the source. `toolbox_check(part)` adds available 3D-Print Toolbox checks; report missing checks if unavailable. `cleanup_mesh()` changes geometry: use only for intended repair and audit afterwards.

## Result scopes

- Mesh: expected shells, nonmanifold/degenerate geometry, optional self-intersection checks. Legacy `pass` is mesh-only.
- Keep-outs: check closure/validity, containment and surface crossings. Open/unresolved geometry yields unknown, not proven clearance.
- Walls: opposing face-centre rays are samples and may miss small notches, bevel neighbors or local thin regions. Inspect critical details separately.
- Supports: downward area flags candidates; it does not qualify bridges or generate/verify supports.
- Fit: use `check_fit()` and a relevant motion path. Intended seated contact does not permit penetration elsewhere.

## Shape for the process

State angles relative to vertical or horizontal. Peaked roofs/teardrops around 40–43° from vertical are useful conservative starting geometry for 0.4 mm FFF processes; rounded arches may leave unsupported crowns. Span, layer height, cooling, extrusion width and material govern actual behavior. No angle threshold guarantees support-free printing.

A vertical landing band can reduce curling from an outward chamfer at the plate. Steeper chamfers (for example 30–35° from vertical) may help, but verify actual first-layer behavior.

Support horizontal tips/ledges rather than automatically filling peaked roofs. Paint/enforce support where automatic supports would enter mating seats or obstruct removal. Verify build-plate-only branches can reach each underside; allow model-start supports when appropriate and inspect their contact surfaces. Remove supports before hardware insertion.

Check generated support feet, brim/skirt and deposition paths against the build volume with an explicit margin and extrusion-width allowance. Include arc extrema; the object fitting the bed does not establish that its supports fit. See [slicing.md](slicing.md).
