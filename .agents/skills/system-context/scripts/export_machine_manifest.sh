#!/usr/bin/env bash
# Export declarative software manifest for the current workstation to system-context
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SYS_CTX="$REPO_ROOT/.local/system-context"
HOSTNAME="$(hostname)"
OUT_FILE="${1:-$SYS_CTX/machines/${HOSTNAME}-software-manifest.md}"

mkdir -p "$(dirname "$OUT_FILE")"

echo "=== Exporting Machine Software Manifest for: $HOSTNAME ==="
echo "Output target: $OUT_FILE"

cat << EOF > "$OUT_FILE"
# Software Manifest: $HOSTNAME

Generated on: $(date -Iseconds)
Host: $HOSTNAME
OS: $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')
Kernel: $(uname -srm)

---

## 1. Snap Packages

\`\`\`text
$(command -v snap >/dev/null && snap list || echo "snap not installed")
\`\`\`

---

## 2. Upstream APT Sources & Keyrings

### Sources (\`/etc/apt/sources.list.d/\`)
\`\`\`text
$(ls -la /etc/apt/sources.list.d/ 2>/dev/null || echo "None")
\`\`\`

$(for src in /etc/apt/sources.list.d/*.sources; do
  if [ -f "$src" ]; then
    echo "#### File: \`$src\`"
    echo '```deb822'
    cat "$src"
    echo '```'
  fi
done)

### Keyrings (\`/etc/apt/keyrings/\`)
\`\`\`text
$(ls -la /etc/apt/keyrings/ 2>/dev/null || echo "None")
\`\`\`

---

## 3. Manually Installed APT Packages (\`apt-mark showmanual\`)

<details>
<summary>Click to expand $(apt-mark showmanual 2>/dev/null | wc -l) manually installed packages</summary>

\`\`\`text
$(apt-mark showmanual 2>/dev/null | sort || echo "apt-mark unavailable")
\`\`\`

</details>

---

## 4. Restoration Checklist for a New Desktop

To reproduce this software environment on a fresh Ubuntu installation:

1. **Install Base Snaps:**
   \`\`\`bash
   sudo snap install firefox
   sudo snap install discord
   sudo snap install rpi-imager
   sudo snap install blender --classic
   sudo snap install code --classic
   \`\`\`

2. **Re-establish Third-Party APT Sources:**
   - Review and copy DEB822 \`.sources\` files above into \`/etc/apt/sources.list.d/\`.
   - Ensure corresponding GPG signing keys are installed into \`/etc/apt/keyrings/\`.
   - Run \`sudo apt update\`.

3. **Install Core Development Tools:**
   \`\`\`bash
   sudo apt install -y python3-pil python3-numpy liblz4-1 git curl build-essential
   \`\`\`
EOF

echo "[✓] Manifest successfully exported to: $OUT_FILE"
