# Current guidance, comparisons and history

## Current project guide

Keep one authoritative `PROJECT.md` with the active geometry/revision, confirmed interfaces, actual printer/process, current verification limits and links to deliverables. Distinguish the saved default print project from recommended test candidates. A successful slice or the fastest estimate does not itself adopt a candidate; promotion follows the user's authorized scope.

Update this guide when a revision or evaluation milestone is saved. Keep detailed measurements and raw reports in linked evidence files instead of accumulating competing current guides at the project root.

## Comparison ledger

When comparing variants, maintain one current ledger linked from `PROJECT.md`. Extend it rather than writing a new root summary for every experiment. Record:

- Variant ID and geometry/configuration revision or hashes.
- Changed parameters, effective process/orientation and comparison baseline.
- Time/material estimates, relevant mechanical/fit findings and their limitations.
- Status, decision reason and paths to reproducible evidence/deliverables.

Use **proposed** for an untested option, **evaluated** for an option with recorded results, **rejected** for an option not being pursued, and **adopted** for an active design/process choice. Keep validation outcomes separate from these statuses: an evaluated option can fail a check, and an adopted geometry can still await physical testing. Label failed checks, unavailable estimates and unperformed tests explicitly. Preserve rejected results so they are not rediscovered as recommendations.

## Archiving and cleanup

At a milestone, archive superseded design notes and legacy profiles under `history/`, retaining their revision and a clear historical-status label or index. Remove conflicting guidance from the active guide; preserve original records before consolidating or moving them. Follow the user's retention instructions rather than deleting recoverable evidence by default.

Keep `LOG.md` append-only. If a requested cleanup calls for a shorter active log, archive the complete old log unchanged and start a continuation that links to it. Historical estimates and validation claims must remain associated with their original revision.

Repair relative links after moves, link the archive from `PROJECT.md`, and check that current recommendations point to the intended files. If maintained documentation is covered by an artifact manifest, update its affected hashes while preserving the original provenance. Documentation-only cleanup must leave model, configured print-project and G-code files unchanged unless separately authorized.
