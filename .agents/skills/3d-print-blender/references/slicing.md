# Slicing a frozen revision

Use this reference for printer setup discovery, support/toolpath verification and configured 3MF delivery. The Python helpers use only the standard library and never install software, connect to a printer, change permissions, or change application preferences intentionally. CLI flags here target a PrusaSlicer-compatible CLI. If it is unavailable, export neutral geometry and report slicing as unverified; do not substitute an untested slicer or profile silently.

## Discover once, verify behavior

```bash
python3 <skill>/scripts/slicer_doctor.py --report <work>/slicer-discovery.json
```

Discovery checks native executable paths and, where available, installed Flatpak application branches without opening a GUI. It returns candidate argv arrays, preferring the installed stable Flatpak branch over beta. Choose the intended installation explicitly. Other packaging, operating systems or wrappers may require a caller-supplied argv array.

Probe a selected command in a writable work directory visible to the application sandbox:

```bash
python3 <skill>/scripts/slicer_doctor.py --probe \
  --command-json '["prusa-slicer"]' --work-dir <work> \
  --report <work>/slicer-probe.json
```

The probe runs help and a four-triangle STL export in an isolated directory, with an isolated application datadir. Successful exit alone is insufficient: a nonempty parseable output must exist when the process finishes. Native launchers that background children can return too early. A conditional Flatpak path uses the CLI binary directly, for example:

```text
["flatpak", "run", "--command=prusa-slicer", "com.prusa3d.PrusaSlicer/x86_64/stable"]
```

That is an example, not a universal installation path. Use actual discovery output. If temporary paths are hidden or launching requires approval, report the exact command and access failure through the host's normal permission mechanism. Do not add host mounts, broaden permissions, or fall back to different printer presets automatically. After one failed attempt, distinguish executable/launcher failure, filesystem visibility, configuration selection and artifact-format failure before retrying.

An optional `--cache <local-file>` reuses a successful probe only for the same command, executable signature, help/version output, platform and working parent. It is machine-local operational information, not shared skill content or permanent evidence that future filesystem access will succeed. Re-probe without the cache when access or installation behavior changes.

## Resolved configuration and explicit expectations

Use a resolved INI exported by the intended slicer, not a vendor preset bundle containing `inherits` or multiple profile sections. The runner requires declared `printer_settings_id`, `filament_type`, `nozzle_diameter` and `layer_height`; include the remaining real hardware/process settings as well. Select the actual printer model, nozzle diameter and HF/non-HF type, filament and process. The shared skill does not establish these from a default printer name or from the material named in an old 3MF.

The wrapper checks important present INI settings against the effective serialized G-code settings, including `nozzle_high_flow` when supplied. Add explicit expectations where hardware or project requirements make them important. Preset names in command arguments are not proof that those settings took effect. Temperatures, speeds and tolerances remain filament/process-specific.

## Slice, check and package

The primary modeler owns the live scene. A slicer worker receives a frozen STL or neutral 3MF, the resolved INI, constraints and a fresh output directory. It must not edit the live Blender file. The wrapper records input/configuration hashes and fails if either input changes while it runs.

```bash
python3 <skill>/scripts/slice_project.py <revision.geometry.3mf> \
  --config <resolved.ini> --output-dir <new-work-directory> \
  --command-json '["prusa-slicer"]' --bed 250,220,270 \
  --expect nozzle_diameter=0.4 --expect nozzle_high_flow=0 \
  --expect filament_type=PLA --center 125,110 \
  --margin 2 --bead-radius 0.225
```

The bed dimensions, placement, 2 mm margin and bead radius are illustrative caller choices. Use the real build volume and an appropriate extrusion-width allowance. Account for support feet, brim and skirt; the object fitting the bed does not mean the slice fits. If placement fails, adjust support strategy or placement explicitly and slice into a new directory. Do not reuse stale G-code to turn a failed run into a pass.

Outputs include:

- `slice.gcode`, logs and `report.json` with effective settings, estimates, validation scope, the slicer's generated-by header where present and SHA-256 hashes of the three helper scripts used.
- `geometry.3mf`, the CLI's geometry export, which may lack print configuration.
- `project.3mf`, a separate packaged project containing the effective serialized settings and inspected geometry.
- `effective-config.json` and artifact hashes for the worker's compact report.
- `roundtrip.ini`, `roundtrip.stl` and `roundtrip.log` from reopening the delivered project in a second isolated application datadir, without loading the original INI or recentering. Reopened settings must match the expectations, and the STL must be nonempty and parseable.

To obtain only verified G-code, use `--no-project`. Toolpath or configuration failures prevent a successful result. The wrapper does not publish files to the working project or issue print commands. Keep the scripts/configuration needed to reproduce important checks with the project's revision artifacts, outside ephemeral `/tmp` paths.

## Scope of toolpath checks

`validate_gcode.py` handles straight deposition and XY `G2`/`G3` arcs, including cardinal extrema rather than just endpoints. It tracks supported positioning, units, extrusion and arc-center modes. Unsupported motion formats return `unsupported`, not a pass. Binary G-code must be exported as text for this checker. Nozzle/bead bounds do not prove support removability, collision-free travel, machine kinematics, strength or thermal performance.

There is no blanket exemption for `Custom` G-code. If the manufacturer's startup purge legitimately lies outside the nominal print rectangle, provide an explicit exception box. Exceptions apply only to unclassified/Custom extrusion before the first layer or model deposition. For a machine whose known purge is at Y=-2.5 mm, a deliberately scoped example is:

```text
--startup-exception 0,250,-4,0,0,16
```

Use that box only after checking the actual startup routine and machine; never generalize it to every printer. Unknown coordinate modes or firmware macros that affect positions require a more capable verifier or an explicitly limited result.

## Verify the delivered format

```bash
python3 <skill>/scripts/verify_3mf.py inspect <project.3mf> --require-config
```

Use `--help` for the exact expected-setting and packaging options. The inspector checks mesh edge/winding integrity, instances, transforms, units and embedded settings; it does not prove self-intersection, fit or structural safety. `slice_project.py` additionally reopens the configured project with the actual CLI and checks resolved settings and parseable geometry before reporting success. That round trip does not re-slice the project or independently prove identical toolpaths/placement. Package from the effective G-code configuration rather than trusting a requested preset label.

The worker should return a short result: frozen revision/hash, effective printer/nozzle/filament/process, time/material estimates, support/build-volume findings, artifact paths and unresolved items. Full CLI help, presets and toolpaths belong in files, not the primary agent's context.
