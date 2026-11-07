# Shared Agent Skills & Antigravity Configuration

Personal skills and configuration shared by Codex and Google Antigravity.

## Skills

### `system-context`

Loads relevant machine and user preference profiles before environment-dependent planning or troubleshooting. Its shared instructions live in `.agents/skills/system-context/`; personal profiles live in the Git-ignored `.local/system-context/` directory, starting with `INDEX.md`. The skill resolves its real path through global symlinks, so both agents use the same private profiles. Read only relevant profiles; verify changeable facts when needed.

Global discovery can use a symlink to this skill directory from `~/.codex/skills/system-context` and `~/.gemini/config/skills/system-context`. These links do not grant folder permissions. A new session or skill refresh may be required to discover an installed skill. If global discovery is unavailable, load the repository's `SKILL.md` by path. Keep the repository in place while using these links.

Private profiles are not included in Git clones or skill installation; back them up separately if desired. On another machine, create profiles from that machine's observations rather than assuming the workstation profile applies.

Skills live in `.agents/skills/`, which Codex and Antigravity discover when this repository is open.

### `3d-print-blender`
Workflow for designing, validating, and iterating 3D printable parts in Blender, using MCP when available.
- **Hardware Profile:** Prusa Core One (0.4mm nozzle, PLA)
- **File Management:** Stores projects in `~/Documents/Blender files/<Project Name>/`
- **Versioning:** Sequential `.blend` files (`_v<N>[_<description>].blend`) and matched `.3mf` exports
- **Mesh Validation:** 3D-Print Toolbox extension and `MANIFOLD` solver verification

### `3d-print-spec-extractor`
Extracts physical dimensions, port heights, and clearances from manufacturer photos, datasheets, and web links for 3D modeling.
- **Role:** Typically delegated to a `research` subagent to prevent context bloat
- **Toolkit:** Bundled CLI tool `scripts/measure_reference.py` using Pillow & NumPy for pixel-to-millimeter scaling
- **Output:** Standardized mechanical spec sheets with 3D print fit tolerances

### `firefox`
Inspects and operates local Firefox profiles, open windows/tabs, synced tabs from other devices, and CLI tab launching.
- **Profile Discovery:** Automatically resolves Snap (`~/snap/firefox/common/.mozilla/firefox/`), native, Flatpak, and macOS profile paths
- **Toolkit:** Bundled zero-dependency CLI helper `scripts/firefox_inspect.py` for lock-safe WAL SQLite queries (`synced-tabs.db`) and `mozLz40` session decompression (`recovery.jsonlz4` via `liblz4`)
- **Tab Launching:** Opens batches of URLs or synced device tabs reliably with explicit `--new-tab` flags

### `html-presentation`
Generates standalone, self-contained HTML presentations, analytical reviews, and audit reports for user review, and opens them in Firefox.
- **Delivery Invariant:** Replaces raw Markdown review files with styled, zero-dependency HTML reports containing metrics, responsive tables, and dark/light mode themes
- **Toolkit:** Bundled CLI helper `scripts/render_report.py` and modular templates in `templates/report.html`
- **Inspiration References:** Tracks upstream ecosystem skills and provenance in `references/upstream.md` (`claude-report-skill`, `frontend-slides`, `html-presentation`, `ui-ux-pro-max-skill`)

## Quick Setup (New Machine)

### Shared folder access

The [sync-harness-access skill](.agents/skills/sync-harness-access/SKILL.md) records authorized shared folder access in `config/folder-access.json` and guides an agent through updating each harness's settings. For example: “Give both harnesses persistent write access to `~/Documents/Blender files` and save it to this project.” After changing a settings panel, ask: “Reconcile folder access between both harnesses and this project.”

Skills run during agent tasks. Automatic detection of settings-panel changes requires a separate watcher or hook; none is installed by this workflow. The shared record starts empty and does not import or revoke existing local grants. `setup.sh` does not apply this record. App/IDE targets are marked pending when only CLI settings can be verified.

The skill is available in this workspace. To use it in other projects, link the single repository source into each harness's documented global skill location or load it by path. Keep global installation separate from permission grants.

Prerequisites: Bash, Python 3.10+, and the standard Linux libraries. On Ubuntu 24.04+/26.10, install dependencies via `apt` to comply with PEP 668:
```bash
sudo apt install python3-pil python3-numpy liblz4-1
```

To link all skills, verify dependencies, and initialize context on a new machine:

```bash
git clone git@github.com:Saftkalaset/llm-harness-skills.git ~/Documents/llm-harness-skills
cd ~/Documents/llm-harness-skills
./setup.sh
```

### What `./setup.sh` does:
1. **`links`**: Symlinks all skills in `.agents/skills/` into both `~/.gemini/config/skills/` and `~/.codex/skills/`, links global rules `global/AGENTS.md` to both harnesses, and automatically prunes dead/broken symlinks.
2. **`doctor`**: Runs environment diagnostics checking Python, Pillow, NumPy, LZ4, Firefox, Blender, and PrusaSlicer.
3. **`init-context`**: Bootstraps machine-specific `.local/system-context/` from bundled templates if not already present.
4. **`permissions`** *(Opt-in)*: Merges the optional command allow-list in `config/permissions.json` into `~/.gemini/antigravity-cli/settings.json` with backup and explicit confirmation (`--yes` to skip prompt).

Codex discovers these skills and `AGENTS.md` from the repository without setup. Codex-specific Blender MCP and external project-folder access are documented in [docs/codex-setup.md](docs/codex-setup.md); they require local connection details and are not added to Antigravity's permissions file.

Setup refuses to replace a non-symlink at a skill destination and refuses malformed settings JSON. Existing settings are backed up before they are updated. Permissions are broad command/tool allow-list entries; review `config/permissions.json` against your CLI's permission semantics before applying it, especially shell, network, Docker, and write-capable Git commands.

## Workflow

For each model: capture requirements and sourced dimensions in `PROJECT.md`, model and inspect in Blender, run and report available mesh checks, export 3MF, confirm the file exists, and update the project log with validation results and remaining uncertainties. Image-based dimensions remain estimates unless independently verified.

## Undo Setup

Remove the skill symlinks created under `~/.gemini/config/skills/` to disable the global Antigravity IDE/App copies. The repository skills remain available to Codex and Antigravity while this repository is open. To revert the settings merge, restore the desired timestamped `settings.json.bak.*` file from `~/.gemini/antigravity-cli/`.
