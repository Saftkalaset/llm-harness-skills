# Delegation and context boundaries

Delegate independent work when available and authorized; otherwise use the same boundaries sequentially. Prefer a tested script with concurrent jobs for deterministic comparisons; agents add value for independent interpretation, research and review. Extra agents do not automatically reduce total token use.

| Task | Owner and boundary |
| --- | --- |
| Requirements, concept choice, modeling, publication | Primary agent; sole writer to live Blender scene |
| Manufacturer research | Research worker; sources, dimensions, uncertainty, thermal/load caveats |
| Slicer preflight | Slicer worker; isolated probes, no preference/permission changes or printer connection |
| Slicing and print checks | Slicer worker; frozen mesh/configuration and separate output directory |
| Independent review when complexity warrants | Reviewer; inspect artifacts/assumptions without changing the reviewed design |

Start useful discovery/research while the scene owner inspects requirements. Assign actual slicing once a frozen export is ready; an already verified installation does not need an idle preflight worker. Never run competing headless processes against the live `.blend`; factory-startup regression fixtures are independent.

## Bounded assignments

Pass a self-contained brief: artifact paths/hashes, units, printer/nozzle/HF status, filament/configuration, constraints, output directory, acceptance criteria, execution owner and authorized tools. Avoid inheriting an entire conversation where a short brief suffices.

Example slicer task:

> Verify this frozen geometry and resolved INI using the slicing reference. Write only to the new output directory. Do not edit the live scene, install software, print, or select alternate hardware profiles. Return effective settings, estimates, support/build-volume findings, hashes/paths and unresolved issues. Stop and report permission or unsupported-format failures.

Research returns a compact specification table plus caveats affecting the design; table-only formatting must not suppress uncertainty.

## Execution ownership and permission blockers

Name one execution owner per job or batch, separately from the live-scene owner. The execution owner may be a worker with suitable authorized access or the primary agent. Other workers prepare inputs or review results without launching the same jobs.

Before handing off a launch, establish whether the worker can access the frozen files and surface any required approval to the user. If it cannot, return prepared jobs for the primary agent to launch through the normal approval mechanism. Report a known permission blocker or pending approval immediately, before entering a blocking wait where possible; include whether any process has actually started. Do not leave the coordinator assuming work is running.

For a batch, keep a compact manifest containing:

- Job ID and execution owner.
- Immutable input/configuration paths and hashes, units and expected hardware/process settings.
- Exact argument vector, output directory and log/report paths.
- State: prepared, running, blocked, completed or failed; include the blocker or outcome.

On a handoff, confirm whether pending launches were cancelled and whether any processes are still running before the new owner starts jobs. Distinguish coordinator cancellation from a user declining permission. A handoff does not authorize retrying a denied action or broadening permissions. Resume only jobs whose state and authorization allow it, using fresh output directories when retrying.

## Integration

- Return short results; raw CLI help, presets, coordinates and toolpaths remain in files.
- Match returned input/configuration hashes to the active revision. Changed inputs invalidate affected downstream checks; mark older results stale.
- Primary agent reviews effective settings and unresolved findings before publication. Worker completion is not design approval or physical validation.
- After a failed attempt, classify launcher, access, configuration or artifact failure before retrying; do not add flags or broaden permissions on an untested hypothesis.
- Cache installation discoveries locally, separate from measurements and shared instructions; invalidate on executable/version/access changes.
