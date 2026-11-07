# <Project Name>
Revision: <revision> | Date: <date> | Units/frame: <declared units and assembly frame>

## Goal and constraints
- Function/hardware: <purpose and source references>
- Frozen confirmed interfaces: <user-tested fit and evidence>
- Printer/nozzle/HF/filament: <actual hardware and resolved profile source>
- Assembly/space: <piece count, tools allowed, above/below/rear clearance>
- Priorities: <print time, material, aesthetics, bulk; unresolved constraints>

## Dimensions and evidence
| Feature | Nominal | Per-side / total allowance | CAD target | Source, method, uncertainty |
| --- | ---: | --- | ---: | --- |
| <feature> | <value> | <allowance> | <target> | <measurement/CAD/estimate/user confirmation> |

- Cache validity: <source fingerprint/revision, frame, method, date where relevant>
- Envelope versus functional geometry: <actual openings/contacts versus approximations>

## Editable scene
- Printable parts: <names and expected component count>
- References/cutters/keep-outs: <names, common-frame parameters>
- Recipe: <stored function, explicit load/rebuild steps; no top-level execution>

## Current decisions and verification
- Active geometry and saved print default: <adopted revision/process and files>
- Recommended test candidates: <separate files and unperformed checks; not automatically adopted>
- Design tradeoffs: <chosen concept, alternatives and physical limitations>
- Mesh integrity: <scoped result and revision/hash>
- Fit/motion: <tolerance, sampling resolution, seated/released/locked results>
- Supports/toolpaths: <orientation, removal access, effective settings, verified bounds/margin>
- Mechanics/thermals: <model assumptions and remaining physical tests>

## Artifacts and next action
- Active `.blend`; neutral `.geometry.3mf`; configured project `.3mf` if verified.
- Comparison ledger, when variants are evaluated: <one current record with proposed/evaluated/rejected/adopted status and evidence links>
- Frozen geometry/configuration hashes: <values or manifest path>
- Reproducible checks/logs: <retained paths and tool versions>
- Historical notes/profiles and log archives: <revision-labeled locations; superseded guidance excluded from current recommendations>
- Next step: <specific remaining task; do not imply unperformed checks passed>
