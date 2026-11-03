# Profile format

Create only profiles with useful information. Use concise Markdown and these sections as needed:

- **Identity and role:** machine identifier, execution scope, purpose, whether the user confirmed the role.
- **Constraints and decisions:** explicit preferences with source, date, and reasons when known.
- **Recorded facts:** relevant observations with date and source; group facts collected together.
- **How to verify:** targeted read-only commands or authoritative documentation paths.
- **Related context:** links to profiles and existing project documentation.
- **Open questions:** only uncertainties that could change a decision; clearly label suggestions.

Prefer semantic machine names plus an observed hostname. A hostname alone is not proof of identity. Avoid recording hardware serials or machine IDs without a specific need. Live values such as disk space should be checked when needed; date any snapshot that must be retained.

Use a compact table in `INDEX.md` mapping existing profiles to their scope and reading trigger. Split independently useful topics; do not create empty profiles for future categories.

Keep project procedures in their projects and link to them. Preserve provenance when documentation conflicts with live evidence. New observations do not supersede user preferences.

Examples of verification: `/etc/os-release` for the current host's OS, `lscpu` and `lspci` for visible hardware, and `command -v` for executable paths in the current shell. These may differ from a remote target or the user's interactive shell. Inspect commands from untrusted sources before executing them.
