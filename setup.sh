#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/.agents/skills"
GLOBAL_RULES="$SCRIPT_DIR/global/AGENTS.md"
PERMISSIONS_FILE="$SCRIPT_DIR/config/permissions.json"
SETTINGS_FILE="$HOME/.gemini/antigravity-cli/settings.json"

show_help() {
  cat << EOF
Usage: ./setup.sh [command] [options]

Commands:
  links          Symlink skills & global rules to Gemini and Codex, pruning dead links
  doctor         Validate system dependencies (Python, PIL, NumPy, LZ4, Firefox, Blender)
  init-context   Initialize local system-context from template for this machine
  permissions    Merge Antigravity permissions whitelist (opt-in; requires confirmation or --yes)
  all            Run links, doctor, and init-context (default if no command provided)
  help           Show this message

Options:
  --yes, -y      Skip confirmation prompts (for permissions command)
  --dry-run      Show actions without making changes
EOF
}

cmd_links() {
  echo "=== 1. Linking Skills & Global Rules ==="
  local gemini_skills="$HOME/.gemini/config/skills"
  local codex_skills="$HOME/.codex/skills"
  local dry_run="${1:-false}"

  mkdir -p "$gemini_skills" "$codex_skills"

  # Link skills into both harnesses
  for skill in "$SKILLS_DIR"/*; do
    if [ -d "$skill" ]; then
      local name="$(basename "$skill")"
      for dest_dir in "$gemini_skills" "$codex_skills"; do
        local target="$dest_dir/$name"
        if [ "$dry_run" = "true" ]; then
          echo "[dry-run] Link $name -> $target"
        else
          ln -sfn "$skill" "$target"
          echo "[✓] Linked: $name -> $target"
        fi
      done
    fi
  done

  # Link global rules if present
  if [ -f "$GLOBAL_RULES" ]; then
    for target in "$HOME/.gemini/config/AGENTS.md" "$HOME/.codex/AGENTS.md"; do
      if [ "$dry_run" = "true" ]; then
        echo "[dry-run] Link global rules -> $target"
      else
        ln -sfn "$GLOBAL_RULES" "$target"
        echo "[✓] Linked global rules -> $target"
      fi
    done
  fi

  # Prune broken/stale symlinks pointing to old or deleted skill locations
  echo "--- Checking for stale skill links ---"
  for dest_dir in "$gemini_skills" "$codex_skills"; do
    for link in "$dest_dir"/*; do
      if [ -L "$link" ] && [ ! -e "$link" ]; then
        if [ "$dry_run" = "true" ]; then
          echo "[dry-run] Would remove dead symlink: $link -> $(readlink "$link")"
        else
          echo "[!] Pruning dead symlink: $link -> $(readlink "$link")"
          rm -f "$link"
        fi
      fi
    done
  done
}

cmd_doctor() {
  echo "=== System & Dependency Diagnostics (Doctor) ==="
  python3 - << 'EOF'
import ctypes, os, shutil, subprocess, sys

def check(name, ok, note=""):
    status = "\033[32m[PASS]\033[0m" if ok else "\033[31m[FAIL]\033[0m"
    print(f"  {status} {name:20} {note}")
    return ok

print("Core Runtimes & Libraries:")
check("Python 3.10+", sys.version_info >= (3, 10), f"Found {sys.version.split()[0]}")

pil_ok = False
try:
    import PIL
    pil_ok = True
    note = f"Found v{getattr(PIL, '__version__', 'unknown')}"
except ImportError:
    note = "Missing (install python3-pil via apt)"
check("Pillow (PIL)", pil_ok, note)

numpy_ok = False
try:
    import numpy
    numpy_ok = True
    note = f"Found v{getattr(numpy, '__version__', 'unknown')}"
except ImportError:
    note = "Missing (install python3-numpy via apt)"
check("NumPy", numpy_ok, note)

lz4_ok = False
try:
    ctypes.CDLL("liblz4.so.1")
    lz4_ok = True
    note = "Available (liblz4.so.1)"
except Exception as e:
    note = f"Missing ({e}); install liblz4-1"
check("LZ4 C Library", lz4_ok, note)

print("\nApplications & Utilities:")
check("Firefox", bool(shutil.which("firefox") or os.path.exists("/snap/bin/firefox")), 
      shutil.which("firefox") or "/snap/bin/firefox" if os.path.exists("/snap/bin/firefox") else "Missing")

check("Blender", bool(shutil.which("blender") or os.path.exists("/snap/bin/blender")), 
      shutil.which("blender") or "/snap/bin/blender" if os.path.exists("/snap/bin/blender") else "Missing")

check("PrusaSlicer", bool(shutil.which("prusa-slicer")), 
      shutil.which("prusa-slicer") or "Missing / optional for slicing validation")

check("Git", bool(shutil.which("git")), shutil.which("git") or "Missing")

print("\nHarness Configuration:")
check("Gemini config", os.path.isdir(os.path.expanduser("~/.gemini/config")), "~/.gemini/config")
check("Codex config", os.path.isdir(os.path.expanduser("~/.codex")), "~/.codex")
check("Global rules", os.path.islink(os.path.expanduser("~/.gemini/config/AGENTS.md")), "~/.gemini/config/AGENTS.md")

print("\nTip: On Ubuntu 24.04+/26.10, install missing Python packages via apt to respect PEP 668:")
print("  sudo apt install python3-pil python3-numpy liblz4-1")
EOF
}

cmd_init_context() {
  echo "=== Initializing System Context ==="
  local init_script="$SKILLS_DIR/system-context/scripts/init_context.py"
  if [ -f "$init_script" ]; then
    python3 "$init_script"
  else
    echo "[!] Initialization script not found: $init_script" >&2
    exit 1
  fi
}

cmd_permissions() {
  local auto_yes="${1:-false}"
  echo "=== Antigravity Permissions Configuration ==="

  if [ ! -f "$PERMISSIONS_FILE" ]; then
    echo "[!] No permissions.json found at $PERMISSIONS_FILE."
    return
  fi

  local count=$(python3 -c "import json; print(len(json.load(open('$PERMISSIONS_FILE'))))")
  echo "Permissions file contains $count whitelist entries."
  echo "Target settings file: $SETTINGS_FILE"

  if [ "$auto_yes" != "true" ]; then
    read -r -p "Merge these permissions into Antigravity settings? [y/N]: " confirm
    case "$confirm" in
      [yY][eE][sS]|[yY]) ;;
      *) echo "Skipped permissions merge."; return ;;
    esac
  fi

  mkdir -p "$(dirname "$SETTINGS_FILE")"

  python3 - << EOF
import json, os, shutil, sys, tempfile, time

settings_path = "$SETTINGS_FILE"
permissions_path = "$PERMISSIONS_FILE"

with open(permissions_path, 'r') as f:
    allowed = json.load(f)

if os.path.exists(settings_path):
    with open(settings_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in {settings_path}; left unchanged: {exc}")
else:
    data = {}

permissions = data.setdefault("permissions", {})
current_perms = set(permissions.get("allow", []))
current_perms.update(allowed)
permissions["allow"] = sorted(current_perms)

backup = settings_path + ".bak." + time.strftime("%Y%m%d-%H%M%S")
if os.path.exists(settings_path):
    shutil.copy2(settings_path, backup)
    print(f"[i] Backup saved to: {backup}")

fd, temp_path = tempfile.mkstemp(prefix="settings.", suffix=".tmp", dir=os.path.dirname(settings_path))
try:
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, settings_path)
except Exception:
    try: os.unlink(temp_path)
    except FileNotFoundError: pass
    raise

print(f"[✓] Whitelist updated: {len(data['permissions']['allow'])} permissions active.")
EOF
}

# Main command dispatch
COMMAND="${1:-all}"
shift || true

case "$COMMAND" in
  links)
    cmd_links "$@"
    ;;
  doctor)
    cmd_doctor
    ;;
  init-context)
    cmd_init_context
    ;;
  permissions)
    auto_yes="false"
    for arg in "$@"; do
      if [ "$arg" = "--yes" ] || [ "$arg" = "-y" ]; then
        auto_yes="true"
      fi
    done
    cmd_permissions "$auto_yes"
    ;;
  all)
    cmd_links
    echo ""
    cmd_doctor
    echo ""
    cmd_init_context
    echo ""
    echo "Tip: Run './setup.sh permissions' if you wish to apply the Antigravity command allow-list."
    echo "=== All checks completed! ==="
    ;;
  help|--help|-h)
    show_help
    ;;
  *)
    echo "Unknown command: $COMMAND" >&2
    show_help >&2
    exit 1
    ;;
esac
