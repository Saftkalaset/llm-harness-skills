---
name: sync-harness-access
description: Synchronize persistent folder access between Codex, Antigravity, and this repository when the user requests shared grants or reconciliation of saved settings.
---

# Synchronize harness access

Resolve this repository from the skill's location, not the current working directory. Read `config/folder-access.json` for shared intent. It is a record, not a file the harnesses load directly. Each grant has `path`, `access` (`read` or `write`), and `scope` (`global` or `project`); project grants also require `project_root`. Store home-relative paths when possible and expand them for local settings. An empty record does not revoke existing local grants.

## Workflow

1. Establish the user's intended folder, access level, and persistence/scope. Requests to grant access to both harnesses authorize those corresponding changes and the repository record. A temporary approval, session-only folder, or grant to one harness does not alone authorize shared global defaults. Do not ask again when the session already authorizes the intended changes.
2. Read only relevant filesystem settings from both installed harnesses. Compare with the shared record and the requested change. Do not blindly union lists: a missing grant might be a revocation. Resolve ambiguous direction with the user while completing independent inspection.
3. Describe the concrete edits. Save authorized shared intent to `config/folder-access.json` and update each verified target through supported settings tools or narrow file edits. Back up local settings, preserve unrelated fields/comments, parse before and after, avoid duplicate TOML tables, and re-read before writing to detect concurrent changes. Use the environment's approval mechanism for protected writes.
4. Read back persisted settings, inspect the repository diff, and report each target as applied, already consistent, unsupported, or pending. Saved settings do not prove an active session gained access; report when a restart or fresh session is needed.

Preserve exact scope. Do not broaden child paths to parents, read to write, or project grants to global defaults. Check symlink targets. Preserve deny/ask rules and report conflicts instead of removing them. Folder access does not authorize network access, blanket shell approvals, disabling sandboxes, or unrestricted filesystem access. For revocations remove only the matching grant and identify broader overlapping grants before claiming access is revoked.

## Codex adapter

Global defaults normally use `${CODEX_HOME:-~/.codex}/config.toml`; trusted projects can use `.codex/config.toml`. Check active settings, launch overrides, and managed requirements.

For legacy `sandbox_mode = "workspace-write"`, merge authorized absolute write folders into `sandbox_workspace_write.writable_roots`, preserving the remaining settings. `--add-dir` is a launch option, not proof of saved defaults. This array cannot express a read-only restriction.

Newer versions may use `default_permissions` and named `permissions.<name>.filesystem` profiles with `read`, `write`, or `deny` values. If those are active, verify the installed schema and update the selected profile; do not add ignored legacy settings or silently migrate models. Unsupported mappings remain pending. Upstream specification details are tracked in [references/upstream.md](references/upstream.md).

## Antigravity adapter

CLI global settings use `~/.gemini/antigravity-cli/settings.json`. Merge `read_file(/absolute/folder)` or `write_file(/absolute/folder)` into `permissions.allow`. Write implies read; Deny and Ask take precedence over Allow. Preserve other entries and fields.

App/IDE surfaces and project overrides may have different storage. Prefer a supported settings interface. If no verified schema or tool is available, give the exact folder permission to enter in that surface and mark it pending; do not claim CLI changes also changed the App. Never substitute Turbo or `allowNonWorkspaceAccess` for a folder grant.

Keep `config/permissions.json` scoped to the existing optional Antigravity command/MCP setup. Do not duplicate shared folder records there or run the broad setup just to grant a folder. Upstream permission schemas and configuration references are recorded in [references/upstream.md](references/upstream.md).

## Discovery and automation

Skills act during agent tasks; they do not watch settings panels or receive every approval event. Use this workflow when asked to sync changes. Unattended synchronization requires a separately installed watcher or supported hook with explicit direction, revocation, and scope handling.

The single source belongs in `.agents/skills/`. For use outside this repository, link it into each harness's documented global skill location, preserving existing destinations. If global discovery or file tools are unavailable, load the skill by path or provide exact proposed edits and mark application pending. Do not create checked-in platform-specific copies.
