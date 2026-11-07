# Upstream Provenance: Blender 3D Printing Workflow

This document records the upstream tools, specifications, extensions, and community repositories evaluated for the `3d-print-blender` skill. Refer to these references when updating Blender geometry scripts, auditing algorithms, or slicer integration routines.

## Provenance Ledger

| Source / Tool | Repository / Documentation | Commit / Version / Tag | Evaluation Date | Origin Classification | Borrowed Concepts | Local Divergence / Customizations | Re-evaluation Triggers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Blender 3D-Print Toolbox** | [Blender Foundation Manual: 3D-Print Toolbox](https://docs.blender.org/manual/en/latest/addons/mesh/3d_print_toolbox.html) | Blender 4.2+ / 5.x bundled extension | 2026-10-16 (initial) / 2026-10-24 | Bundled extension API | Non-manifold edge detection, degenerate geometry checks, volume and surface area calculation, overhang angle thresholds. | Encapsulated into programmatic Python helpers (`lib.py`) via `audit()` and `toolbox_check()` for headless, non-interactive execution with structured digests rather than GUI panels. | Upstream BMesh inspection API updates or new geometric integrity checks added to the official toolbox. |
| **Blender MCP Server** | [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) (PyPI `mcp-for-blender`) | `2e4b0bc294` (v0.1.x) | 2026-10-16 (initial) / 2026-11-07 | External MCP tool bridge | Agent-to-Blender bridge using `execute_blender_code`, scene query via `get_scene_info`, and viewport rendering via `look`. | Supports dual-mode operation: leverages Blender MCP if active, but seamlessly falls back to headless background CLI execution (`blender --background`) on isolated working copies if MCP is unavailable. | Blender MCP adds native mesh diffing tools, real-time geometry streaming, or object transform APIs. |
| **PrusaSlicer CLI & Profiles** | [prusa3d/PrusaSlicer](https://github.com/prusa3d/PrusaSlicer) | `version_2.9.7` (`450d70dd81`) | 2026-10-24 | External CLI slicer | CLI headless slicing (`prusa-slicer --slice`), arc-fitting validation (`G2`/`G3`), nozzle flow presets (HF vs. standard), print time estimation. | Enforces strict separation between neutral geometry (`.geometry.3mf`) and machine-configured projects (`.3mf`); isolates slice execution and mandates hash validation before slicing. | Major CLI parameter changes in PrusaSlicer or new printer/filament profile bundle structures. |

---

## Technical Notes

### 1. Dual-Mode Scene Access
When the Blender MCP server is running (e.g. configured via `uvx mcp-for-blender`), the agent executes Python code directly in the user's live Blender session (`execute_blender_code`) and captures viewport previews (`look`). When MCP is absent, the skill runs an isolated headless Blender subprocess (`blender -b <file> -P <script>`) to prevent concurrency locks or uncommitted UI conflicts.

### 2. Geometry vs. Configured Project Separation
- **Neutral Geometry (`<model>.geometry.3mf`):** Contains only mesh geometry and world coordinates in mm. Completely free of printer, nozzle, or slicer parameters.
- **Configured Slicer Project (`<model>.3mf`):** Generated via `slice_project.py` or PrusaSlicer presets with verified infill, perimeters, layer heights, and nozzle diameters.
