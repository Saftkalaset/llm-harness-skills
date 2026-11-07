---
name: 3d-print-blender
description: Design, modify, inspect, validate and export 3D-printable models in Blender, including fit to reference hardware and slicer verification.
---

# Blender 3D printing workflow

## Establish constraints and preserve the scene

Before detailed modeling, identify confirmed interfaces, material, printer/nozzle (including HF/non-HF), assembly constraints, clearances and priorities for bulk, material and print time. Respect user-confirmed fit. Compare simple concepts when their tradeoffs differ materially; continue independent work while resolving missing constraints.

Keep one owner of the live scene. If a Blender connector is available, use its code/viewport tools; with Blender MCP these are `execute_blender_code` and `look`. Otherwise use an authorized local Blender process on an isolated copy, never a competing writer to the active file. Without Blender execution, inspect supplied exports and label Blender-specific checks unverified.

Load [scripts/lib.py](scripts/lib.py) once in Blender, and reload after its source changes:

```python
exec(open('<skill-directory>/scripts/lib.py').read(), globals())
state = open_project('<project-dir>')
```

`open_project()` inspects without running stored recipes. Switching an existing file/populated scene requires an explicit `allow_switch=True` after preserving its state; a dirty scene separately requires saving or intentional `allow_discard`. These are data-preservation controls, not a requirement to ask the user about ordinary authorized checkpointing. Ambiguous project filenames are rejected.

`save_recipe(code)` stores text only. `load_recipe()` explicitly registers imports, literal constants and functions; call the intended rebuild function separately. Review/refactor legacy recipes containing top-level modeling statements before registration. Definition-only loading prevents accidental rebuilding, not hostile imports/code.

Preserve existing units and coordinate conventions; never silently rescale/recenter. New mm projects can use metric `scale_length=0.001`. Dimensional audit helpers require numerical world coordinates in mm; neutral export converts declared units. Drive related references, features and keep-outs from common assembly parameters rather than unrelated offsets.

## Model and measure deliberately

- Use evaluated geometry in a declared frame. `evaluated_world_mesh()` returns an owned BMesh; free it. `world_bbox()` and `mesh_fingerprint()` include modifiers/transforms.
- `get_specs()` returns cached data and prints a digest. `record_measurement(key, value, source, frame=..., method=..., uncertainty=...)` records provenance and source-mesh fingerprints. Reuse valid records; remeasure changed geometry/frames or contradictory evidence. Legacy cached values without provenance remain unverified.
- Distinguish direct measurements, manufacturer CAD, image estimates, envelopes and actual openings. Projected overlap is not measured airflow or thermal performance.
- Prefer editable parameters/live booleans for revisions. Read [references/booleans.md](references/booleans.md) for cutter integrity, beam-model limitations and insertion paths.
- Use the specification-extraction skill when available for external product fit research; otherwise record sources, uncertainty and per-side/total clearances directly. Printer/material compensation requires calibration, not universal shrinkage values.

New helper-based scenes use `1_Printable_Parts`, `2_Boolean_Cutters`, and `3_References`. Hidden cutters must keep `hide_viewport=False` so live boolean dependencies evaluate; hide them with `hide_set(True)`. Do not reorganize an existing scene just to review it. Exclude hardware/clearance references from exports.

## Validate the specific claim

Run `audit(part)` and optional `toolbox_check(part)` on evaluated geometry. Interpret scoped results; legacy `pass` means mesh integrity only:

- **Mesh:** expected shells, manifold/degenerate geometry and available Toolbox checks.
- **Fit:** `check_fit(part, reference, allow_contact=True)` separates intended contact from sampled penetration. Open/unresolved geometry is not proven clear.
- **Motion:** `check_insertion(..., max_step_mm=..., final_step_mm=...)` samples densely near seating and reports the seated state separately. It is not continuous collision proof. Check actual insertion/removal and release states.
- **Keep-outs/supports:** containment matters as well as surface crossings. Overhang area identifies candidates, not a verified support/removal plan.
- **Mechanics:** `audit_cantilever()` is an approximate ideal solid-beam screen where applicable. Include relevant device/mount/cable/handling loads; anisotropy, joints, creep and heat need other evidence. No universal stress threshold certifies the part.

Read [references/overhang-audit.md](references/overhang-audit.md) for support decisions and [references/staging-gates.md](references/staging-gates.md) for iteration/acceptance gates. Read [references/slicing.md](references/slicing.md) before slicer CLI work: installation discovery, effective settings, arc-aware bounds and configured projects.

## Delegate from frozen artifacts

Research, slicer preflight and independent checks may run outside the scene owner when delegation is available/authorized; otherwise perform them sequentially. Slicing receives an immutable export/hash, resolved configuration, constraints and a separate output directory. Assign one execution owner per batch and surface permission blockers immediately; workers can prepare job manifests for the primary agent to launch when approval access differs. Workers must not edit the live scene or substitute hardware profiles. Return compact results/paths; keep full logs in files. Read [references/delegation.md](references/delegation.md).

## Save reproducible deliverables

Use one active root `.blend`, concise `PROJECT.md`, append-only `LOG.md`, and immutable `history/` milestones where appropriate. Start notes from [resources/PROJECT_TEMPLATE.md](resources/PROJECT_TEMPLATE.md). Preserve the recipe, provenance and scripts/configuration needed to reproduce important checks, not just results in temporary storage.

Keep `PROJECT.md` authoritative for the active geometry, saved print defaults and recommended test candidates. For variant studies, maintain one linked comparison ledger with proposed/evaluated/rejected/adopted status. Archive superseded guidance at milestones and repair links; follow [references/documentation.md](references/documentation.md) when maintaining or consolidating project notes.

`snapshot_and_export()` saves a milestone and neutral **`.geometry.3mf`** via `export_geometry_3mf()`. It preserves a separately configured root `.3mf`. Neutral geometry has no printer settings. `slice_project.py` produces a separate configured project from verified effective settings. Reopen/check units, instances, placement and settings before claiming a ready-to-slice project. Existing callers expecting snapshot export to overwrite root `.3mf` must adopt this distinction.

Save viewport images through supported file output or streaming, not large base64 shell arguments. Inspect isolated parts and assembly, restoring visibility/selection. With Blender MCP, `look` frames targets but may draw other visible objects; temporarily hide occluding references or use x-ray. Do not add camera/lights just for inspection.

Stage and verify in authorized writable locations, then publish once with guarded copies when needed. Skills do not grant filesystem permissions. Keep machine-local caches and optional platform permissions separate from shared skill source. Consult [references/upstream.md](references/upstream.md) for provenance records and upstream tool specifications (Blender 3D-Print Toolbox, Blender MCP, PrusaSlicer CLI).
