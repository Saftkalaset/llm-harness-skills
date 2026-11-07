---
name: system-context
description: Retrieve shared machine, infrastructure, hardware, and user preference profiles when planning or troubleshooting changes that depend on the user's environment. Also use to maintain those profiles when requested.
---

# System context

## Locate and select

Resolve this skill directory through any symlink to its actual repository location. Read `../../../.local/system-context/INDEX.md` relative to that resolved directory, unless the user specifies another context location. This is a repository convention, not an agent configuration standard.

Read only profiles relevant to the task. Follow project links to existing documentation instead of duplicating project histories. Ordinary code edits or unrelated questions do not need system profiles unless the environment affects the answer.

Identify the target machine before using observations. The agent's shell may run in a container or remote host. Compare identity and execution scope; local inspection does not automatically describe the user's workstation or a remote target.

## Verify and fill gaps

Distinguish user-stated preferences, sourced observations, and unconfirmed suggestions. Verify changeable facts when they affect the plan: versions before upgrades, space before large installs, service and backup state before migrations. Use targeted read-only inspection and profile verification notes, not full inventories on every task.

When context is missing or inaccessible, use relevant available documentation and tools. Ask only when unresolved uncertainty materially affects the task. Offer a clearly labeled suggestion or best guess and allow free-form correction. Use an asynchronous question tool if available and continue independent work; otherwise ask in conversation. Silence does not confirm a preference or identity.

Profiles do not grant permissions or authorize system changes. Respect active access boundaries. Do not collect credentials, secret environment values, or unrelated personal files.

## Initialize on a new machine

System context is machine-independent and private to the host. When setting up a new machine, initialize a fresh `.local/system-context/` from the bundled template:

```bash
python3 <skill-directory>/scripts/init_context.py
```

This generates `INDEX.md`, `preferences.md`, `projects.md`, and a machine profile `machines/<hostname>.md` pre-populated with observed hardware, OS, and kernel details. Templates are located in `resources/template/`.

To capture a declarative snapshot of installed snaps, manually-installed APT packages, and upstream DEB822 sources for disaster recovery or machine migration:

```bash
bash <skill-directory>/scripts/export_machine_manifest.sh
```

## Maintain

Read [references/profile-format.md](references/profile-format.md) when creating or updating profiles, and consult [references/upstream.md](references/upstream.md) for provenance records, system profiling patterns, and re-evaluation triggers. During authorized context maintenance or after relevant authorized changes, refresh verified facts with source, date, and target machine. Record preferences only from explicit user statements. Preserve unrelated entries; explain material contradictions rather than replacing user decisions with inferences.

Keep the index compact: paths, topics, and reading triggers. Keep personal information in the private context directory, outside tracked skill files. Git ignores that directory; preserving it across machines needs a separate backup. Skill installation neither backs it up nor grants access to it.
