# Upstream Provenance: System Context Profiles

This document records the provenance, standards, and design rationale for the `system-context` skill.

## Provenance Ledger

| Source / Pattern | Specification / Reference | Version / Standard | Evaluation Date | Origin Classification | Borrowed Concepts | Local Divergence / Customizations | Re-evaluation Triggers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Shared Multi-Agent Context Architecture** | Internal Local Architecture Pattern | v1.0 (local design) | 2026-11-03 | **Original local design** | Clean architectural separation of machine-specific, private environment facts from public reusable skill code; lazy profile indexing (`INDEX.md`); structured verification logs. | Machine state is kept strictly under `.local/system-context/` (git-ignored and private), while `.agents/skills/system-context/` houses only reusable agent instructions and formatting schemas. | Adoption of formal cross-agent environment profile standards (e.g. unified agent context protocols across OpenAI/Google). |
| **POSIX Machine & OS Discovery Standards** | [freedesktop.org os-release Specification](https://www.freedesktop.org/software/systemd/man/os-release.html) & Linux sysfs / procfs | Standard POSIX / systemd | 2026-11-03 | Operating system standards | Structured host identification via standard system interfaces (`/etc/os-release`, `lspci`, `lscpu`, `free`, `df`, `ip`, and systemctl unit inspection). | Standardized markdown profile template ([references/profile-format.md](profile-format.md)) separating verified facts, user preferences, hardware specs, network topology, and verification timestamps. | Major Linux host changes (e.g. systemd system extension changes) or multi-OS expansion (macOS profile templates). |

---

## Technical Notes

### 1. Privacy Boundary
System profiles contain local IP addresses, partition layouts, hardware serials, and user configuration preferences. These are system-dependent and must never be committed to public git repositories or mixed into reusable skill source code. All machine state resides exclusively in `.local/system-context/`.

### 2. Verified Facts vs. Inferences
Agents must never confuse transient observations with permanent user preferences:
- **Verified Facts:** Directly observed via command outputs with explicit inspection dates (e.g., `Kernel: 6.17.0-14-generic`, verified 2026-11-07).
- **User Preferences:** Explicitly stated user instructions (e.g., "Always use Snap for Discord"). Inferences or guesses must never be recorded as preferences without explicit user confirmation.
