#!/usr/bin/env python3
"""Initialize a new system-context directory for the current machine from templates."""

import argparse
import datetime
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_DIR.parent.parent
DEFAULT_DEST = REPO_ROOT / ".local" / "system-context"
TEMPLATE_DIR = SKILL_DIR / "resources" / "template"


def run_cmd(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def gather_facts() -> dict[str, str]:
    hostname = socket.gethostname() or "workstation"
    now_str = datetime.date.today().isoformat()

    # OS
    os_name = "Linux"
    if Path("/etc/os-release").exists():
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("PRETTY_NAME="):
                os_name = line.split("=", 1)[1].strip('"\'')
                break

    # Kernel & Arch
    kernel = run_cmd(["uname", "-r"]) or "unknown-kernel"
    arch = run_cmd(["uname", "-m"]) or "x86_64"

    # CPU
    cpu_model = "Unknown CPU"
    if Path("/proc/cpuinfo").exists():
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if "model name" in line:
                cpu_model = line.split(":", 1)[1].strip()
                break

    # RAM
    ram_total = "Unknown"
    swap_total = "Unknown"
    if Path("/proc/meminfo").exists():
        mem_text = Path("/proc/meminfo").read_text()
        m_ram = re.search(r"MemTotal:\s+(\d+)\s+kB", mem_text)
        if m_ram:
            ram_gib = round(int(m_ram.group(1)) / (1024 * 1024), 1)
            ram_total = f"~{ram_gib} GiB"
        m_swap = re.search(r"SwapTotal:\s+(\d+)\s+kB", mem_text)
        if m_swap:
            swap_gib = round(int(m_swap.group(1)) / (1024 * 1024), 1)
            swap_total = f"~{swap_gib} GiB"

    # GPU
    gpu_info = "Integrated / Unspecified GPU"
    lspci_out = run_cmd(["lspci"])
    if lspci_out:
        gpu_lines = [
            l.split(":", 2)[-1].strip()
            for l in lspci_out.splitlines()
            if any(term in l.lower() for term in ["vga", "3d controller", "display controller"])
        ]
        if gpu_lines:
            gpu_info = "; ".join(gpu_lines)

    # Root disk
    root_dev = "/dev/root"
    root_size = "unknown"
    df_out = run_cmd(["df", "-h", "/"])
    if df_out and len(df_out.splitlines()) > 1:
        parts = df_out.splitlines()[1].split()
        if len(parts) >= 2:
            root_dev = parts[0]
            root_size = parts[1]

    return {
        "HOSTNAME": hostname,
        "DATE": now_str,
        "OS_DESCRIPTION": os_name,
        "KERNEL": kernel,
        "ARCH": arch,
        "CPU_MODEL": cpu_model,
        "RAM_TOTAL": ram_total,
        "SWAP_TOTAL": swap_total,
        "GPU_INFO": gpu_info,
        "ROOT_DEV": root_dev,
        "ROOT_SIZE": root_size,
        "PYTHON_PATH": sys.executable or "/usr/bin/python3",
    }


def init_context(dest: Path, force: bool = False) -> None:
    if dest.exists() and not force:
        print(f"[!] System context already exists at: {dest}")
        print("    Use --force to re-initialize or edit existing files directly.")
        return

    dest.mkdir(parents=True, exist_ok=True)
    machines_dir = dest / "machines"
    machines_dir.mkdir(parents=True, exist_ok=True)

    facts = gather_facts()
    hostname = facts["HOSTNAME"]

    # 1. Copy preferences.md
    pref_tpl = (TEMPLATE_DIR / "preferences.md").read_text(encoding="utf-8")
    (dest / "preferences.md").write_text(pref_tpl, encoding="utf-8")

    # 2. Copy projects.md
    proj_tpl = (TEMPLATE_DIR / "projects.md").read_text(encoding="utf-8")
    (dest / "projects.md").write_text(proj_tpl, encoding="utf-8")

    # 3. Create machine profile
    mach_tpl = (TEMPLATE_DIR / "machines" / "template-machine.md").read_text(encoding="utf-8")
    for key, val in facts.items():
        mach_tpl = mach_tpl.replace(f"{{{{{key}}}}}", str(val))
    (machines_dir / f"{hostname}.md").write_text(mach_tpl, encoding="utf-8")

    # 4. Create INDEX.md referencing this machine
    index_tpl = (TEMPLATE_DIR / "INDEX.md").read_text(encoding="utf-8")
    index_content = index_tpl.replace(
        "[Host Machine](machines/template-machine.md)",
        f"[{hostname.capitalize()}](machines/{hostname}.md)",
    )
    (dest / "INDEX.md").write_text(index_content, encoding="utf-8")

    print(f"[✓] Initialized fresh system context at: {dest}")
    print(f"    - Index: {dest / 'INDEX.md'}")
    print(f"    - Preferences: {dest / 'preferences.md'}")
    print(f"    - Machine Profile: {machines_dir / f'{hostname}.md'}")
    print(f"    - Projects: {dest / 'projects.md'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DEST,
        help=f"Target directory for system context (default: {DEFAULT_DEST})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files in destination",
    )
    args = parser.parse_args()
    init_context(args.dest.expanduser().resolve(), force=args.force)


if __name__ == "__main__":
    main()
