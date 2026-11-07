# Repository guidance

This repository contains reusable agent skills and optional Antigravity configuration.

- Shared skills belong in `.agents/skills/<skill-name>/`; keep each skill's `SKILL.md`, scripts, and resources together.
- Keep skill instructions usable across agents. Name product-specific tools only when documenting a conditional tool path, and state what to do when that tool is unavailable.
- Keep Antigravity settings and permissions optional and separate from the shared skill content. Review permission changes for their actual scope before applying them.
- Keep `.agents/skills/` as the only checked-in skill source; do not add duplicate platform-specific copies.
- When planning or troubleshooting changes that depend on the user's machines, infrastructure, hardware, or operating preferences, use `.agents/skills/system-context/SKILL.md`. Load only the relevant profiles.
- For any skill adapted from or inspired by external tools, documentation, or community skills, maintain a provenance record in `.agents/skills/<skill-name>/references/upstream.md`. Record the upstream source URL, version/commit/tag evaluated, date, borrowed concepts, local divergence, and re-evaluation triggers to facilitate future skill upgrades.
- In conversational and terminal output, separate concerns, options, packages, and multi-part findings into Markdown tables wherever possible for fast review.
- Do not deliver ad-hoc user reviews, analytical audits, or presentations as raw Markdown files. Use self-contained, styled HTML for documents intended for user review and provide clickable links or open them in Firefox. Reserve Markdown strictly for persistent repository documentation, configuration, and agent skills.
