# Codex setup

This repository shares skill instructions with Codex. Machine-specific tool connections and access grants are configured separately because they depend on the local Codex environment.

## Skills and repository guidance

When you open this repository in Codex, it discovers skills under `.agents/skills/` and reads the root `AGENTS.md`. No Codex skill installation step is needed for repository work.

The Antigravity `config/permissions.json` file does not configure Codex. Keep that file scoped to Antigravity.

## Blender MCP

Codex supports the Blender MCP server using `mcp-for-blender` via `uvx`. In `~/.codex/config.toml`:

```toml
[mcp_servers.blender]
command = "uvx"
args = ["mcp-for-blender"]

[mcp_servers.blender.tools.get_scene_info]
approval_mode = "approve"

[mcp_servers.blender.tools.look]
approval_mode = "approve"

[mcp_servers.blender.tools.execute_blender_code]
approval_mode = "approve"
```

Codex stores MCP configuration in `~/.codex/config.toml`, shared by the Codex app, CLI, and IDE extension. Start with approval required for tool calls that can change the active Blender scene or write files.

## WoW: Forever MCP Servers (`everloot` & `wowdb`)

The [`wow-forever`](../.agents/skills/wow-forever/SKILL.md) skill queries two public, zero-auth Streamable HTTP MCP servers for *World of Warcraft: Forever* data:

```bash
codex mcp add everloot --url https://everloot.app/mcp/public
codex mcp add wowdb --url https://azeroth.wiki/api/mcp
```

In Antigravity (`~/.gemini/config/mcp_config.json`), these are registered under `mcpServers` with `"url": "https://everloot.app/mcp/public"` and `"url": "https://azeroth.wiki/api/mcp"`. When MCP tools are unavailable in a sandboxed session, use `.agents/skills/wow-forever/scripts/wow_forever_query.py`.

## Blender project file access

Codex's workspace sandbox does not automatically grant write access to the Blender project folders outside this repository. For a single project, launch Codex with that project folder as an additional writable directory:

```bash
codex --add-dir "$HOME/Documents/Blender files/<Project Name>"
```

This grants access for that Codex run. If you want persistent access to more folders, configure `sandbox_workspace_write.writable_roots` in your local Codex config after choosing the exact paths. Avoid adding the entire Blender files directory unless you want Codex to write to every project beneath it.

## Shell approvals and network

Do not translate Antigravity's broad command allow-list into blanket Codex approvals. Codex combines sandbox boundaries with approval policy. Keep the normal sandbox and approval behavior; grant extra directory access narrowly with `--add-dir` and handle commands that need more access through Codex's approval flow.

Codex sandboxed network access is off by default. The spec-extractor can still use available web research tools; shell downloads with `curl` may need additional network access or approval. Do not enable unrestricted network access globally just to download a reference image.

## What remains to configure

- The Blender MCP server command and arguments, or its remote URL and authentication requirements.
- Which Blender MCP tools Codex should expose, and which should require approval.
- Whether Codex should receive access per project with `--add-dir` or persistent access to selected Blender project directories.
