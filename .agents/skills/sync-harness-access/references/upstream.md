# Upstream Provenance: Synchronize Harness Access

This document records the upstream platform specifications, schema documentation, and configuration models evaluated for the `sync-harness-access` skill. Refer to these references when updating configuration adapters or synchronizing permission schemas across harnesses.

## Provenance Ledger

| Platform / Specification | Documentation / Reference | Version / Spec | Evaluation Date | Origin Classification | Borrowed Concepts | Local Divergence / Customizations | Re-evaluation Triggers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenAI Codex Configuration** | [Codex Config Basics](https://learn.chatgpt.com/docs/config-file/config-basic) & [Reference](https://learn.chatgpt.com/docs/config-file/config-reference) | Codex CLI / Config v1/v2 | 2026-11-02 (initial) / 2026-11-07 | External platform specification | TOML configuration structure (`~/.codex/config.toml`), `sandbox_workspace_write.writable_roots` array, modern `permissions.<name>.filesystem` profiles. | Path normalization to shared format, validation against existing settings before merging, preservation of unrelated TOML tables and comments, detection of concurrent modifications. | Schema changes or deprecation of `sandbox_workspace_write` in Codex, or new declarative permission profile formats. |
| **Google Antigravity Permissions & Settings** | [Antigravity Permissions](https://antigravity.google/docs/permissions/) & [Settings](https://antigravity.google/docs/settings) | Antigravity 2.x CLI / IDE | 2026-11-02 (initial) / 2026-11-07 | External platform specification | Global settings (`~/.gemini/antigravity-cli/settings.json`), `permissions.allow`, `read_file(<path>)` / `write_file(<path>)` patterns, precedence rules (Deny > Ask > Allow). | Reconciled against single shared intent record (`config/folder-access.json`), home-relative path persistence, strict scope enforcement avoiding blanket filesystem access. | Changes in Antigravity workspace permission schemas, fine-grained folder scoping features, or policy inheritance rules. |

---

## Technical Notes

### 1. Codex Adapter Scope & Nuances
- Legacy `sandbox_mode = "workspace-write"` relies on `sandbox_workspace_write.writable_roots = ["/path/one", "/path/two"]`. This array controls write permissions; read-only folder grants cannot be expressed through this legacy mechanism alone.
- Newer Codex versions introduce named permission profiles (`permissions.<name>.filesystem`) with explicit `read`, `write`, and `deny` rules. The skill detects which schema is active rather than forcing legacy fields into newer configs.

### 2. Antigravity Adapter Scope & Nuances
- CLI global settings live in `~/.gemini/antigravity-cli/settings.json`.
- Permissions in `permissions.allow` take the format `read_file(/path)` or `write_file(/path)`. A `write_file` permission implies `read_file`.
- Precedence: `deny` rules override `ask` rules, which in turn override `allow` rules.
- Local repository setup (`config/permissions.json`) is reserved for tool/MCP execution and must not be conflated with user folder access grants.
