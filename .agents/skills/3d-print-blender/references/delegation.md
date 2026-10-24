# Delegation and context boundaries

Delegate independent work when available and authorized; otherwise use the same boundaries sequentially. Scripts handle deterministic checks. Extra agents do not automatically reduce total token use.

| Task | Owner and boundary |
| --- | --- |
| Requirements, concept choice, modeling, publication | Primary agent; sole writer to live Blender scene |
| Manufacturer research | Research worker; sources, dimensions, uncertainty, thermal/load caveats |
| Slicer preflight | Slicer worker; isolated probes, no preference/permission changes or printer connection |
| Slicing and print checks | Slicer worker; frozen mesh/configuration and separate output directory |
| Independent review when complexity warrants | Reviewer; inspect artifacts/assumptions without changing the reviewed design |

Start discovery/research while the scene owner inspects requirements. Actual slicing starts from a frozen export. Never run competing headless processes against the live `.blend`; factory-startup regression fixtures are independent.

## Bounded assignments

Pass a self-contained brief: artifact paths/hashes, units, printer/nozzle/HF status, filament/configuration, constraints, output directory, acceptance criteria and authorized tools. Avoid inheriting an entire conversation where a short brief suffices.

Example slicer task:

> Verify this frozen geometry and resolved INI using the slicing reference. Write only to the new output directory. Do not edit the live scene, install software, print, or select alternate hardware profiles. Return effective settings, estimates, support/build-volume findings, hashes/paths and unresolved issues. Stop and report permission or unsupported-format failures.

Research returns a compact specification table plus caveats affecting the design; table-only formatting must not suppress uncertainty.

## Integration

- Return short results; raw CLI help, presets, coordinates and toolpaths remain in files.
- Match returned input/configuration hashes to the active revision. Changed inputs invalidate affected downstream checks; mark older results stale.
- Primary agent reviews effective settings and unresolved findings before publication. Worker completion is not design approval or physical validation.
- After a failed attempt, classify launcher, access, configuration or artifact failure before retrying; do not add flags or broaden permissions on an untested hypothesis.
- Cache installation discoveries locally, separate from measurements and shared instructions; invalidate on executable/version/access changes.
