# Machine Profile: {{HOSTNAME}}

## Identity and role

- **Role:** Main workstation / development machine.
- **Hostname:** `{{HOSTNAME}}` (observed via `hostname`).
- **Scope:** Local workstation shell.
- **Initialization Date:** {{DATE}}

## Recorded facts

Observed with `/etc/os-release`, `uname -srm`, `lscpu`, `free -h`, `lspci`, `df -h`, and `snap list`:

- **Operating System:** {{OS_DESCRIPTION}}
- **Kernel & Arch:** {{KERNEL}} ({{ARCH}})
- **CPU:** {{CPU_MODEL}}
- **Memory:** {{RAM_TOTAL}} RAM, {{SWAP_TOTAL}} swap
- **GPU / Display:** {{GPU_INFO}}
- **Filesystem / Storage:** Root on `{{ROOT_DEV}}` ({{ROOT_SIZE}} total).
- **Core Package Managers & Channels:**
  - Snaps in use: (e.g., `firefox`, `blender`, `code`, `discord`, `rpi-imager`)
  - Third-party APT repositories active: (e.g. `/etc/apt/sources.list.d/*.sources`)
- **Key Tool Paths:**
  - Python: `{{PYTHON_PATH}}`
  - Node / Bun: (run `command -v node bun`)
  - Docker / Container runtime: (run `command -v docker`)

## Constraints and decisions

Apply [working preferences](../preferences.md) when planning system changes. Tool paths above are observations, not instructions to install or upgrade packages with a particular manager.

## How to verify

1. Check `hostname` and execution scope first.
2. Query OS and Kernel: `/etc/os-release` and `uname -srm`.
3. Query hardware: `lscpu`, `free -h`, `lspci | grep -iE 'vga|3d|display'`.
4. Query disk space before installs: `df -h / /home`.
5. Check installed tool versions before upgrading: `command -v <tool>` and `<tool> --version`.
6. Inspect package ownership: `dpkg -S <path>` or `snap list <pkg>`.

## Related context

See [project index](../projects.md) for project-specific instructions.
