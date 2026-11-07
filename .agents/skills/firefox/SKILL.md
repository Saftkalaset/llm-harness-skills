---
name: firefox
description: Inspect and operate local Firefox sessions, open windows/tabs, synced tabs from other devices, bookmarks/history databases, and CLI tab launching. Use when working with the user's Firefox browser or profile data.
---

# Firefox Local Operations & Profile Inspection

Keep instructions portable across agents. Do not restart a running Firefox instance or modify profile databases in place unless explicitly requested.

## 1. Locate the Active Profile

Check candidate profile roots in order and parse `profiles.ini` (or select the profile directory with the most recently modified `sessionstore-backups/recovery.jsonlz4` or `places.sqlite`):

1. **Snap (Ubuntu default):** `~/snap/firefox/common/.mozilla/firefox/`
2. **Native Linux:** `~/.mozilla/firefox/`
3. **Flatpak:** `~/.var/app/org.mozilla.firefox/.mozilla/firefox/`
4. **macOS:** `~/Library/Application Support/Firefox/Profiles/`

Use the bundled helper script (resolved relative to this skill directory) to locate the active profile or inspect tabs:

```bash
python3 <skill-directory>/scripts/firefox_inspect.py profile
```

## 2. Inspect SQLite Databases Safely (Live Browser)

While Firefox is running, databases use SQLite WAL mode. Never write to live profile databases. Copy the `.db` file together with its `-wal` and `-shm` files into a temporary directory before querying, and remove the temporary copies when finished:

- **`synced-tabs.db`** — Tabs synced from other Firefox Sync devices:
  - Table `tabs`: columns `guid`, `record` (JSON containing `clientName` and `tabs[]` with `title`, `urlHistory`, `lastUsed`), `last_modified`.
- **`places.sqlite`** — History (`moz_places`, `moz_historyvisits`) and bookmarks (`moz_bookmarks`).

List or filter synced tabs from other devices with the bundled script:

```bash
python3 <skill-directory>/scripts/firefox_inspect.py synced-tabs
python3 <skill-directory>/scripts/firefox_inspect.py synced-tabs --device "iPhone"
```

## 3. Read Open Windows & Tabs (`recovery.jsonlz4`)

Firefox writes live session state to `<profile>/sessionstore-backups/recovery.jsonlz4` (falling back to `previous.jsonlz4` when Firefox is closed).

- **Header format (`mozLz40`):** 8-byte magic header `b"mozLz40\x00"`, followed by a 4-byte little-endian unsigned integer (`struct.unpack('<I', f.read(4))[0]`) specifying the exact uncompressed byte size, followed by a raw LZ4 block.
- **Zero-dependency decompression on Linux:** Use `ctypes` with `liblz4.so.1` (`LZ4_decompress_safe`) rather than installing `pip` packages into an externally-managed system Python environment (PEP 668).

Inspect open windows and tabs directly:

```bash
python3 <skill-directory>/scripts/firefox_inspect.py open-tabs
```

## 4. Open URLs and Tab Batches Reliably

- **Single tab in existing window:** `firefox --new-tab "<url>"`
- **Multiple tabs / batches:**
  - Pass URLs as an argument list (e.g., `subprocess.run([...])`) rather than shell-interpolated strings so query parameters (`&`, `?`, `#`, quotes) are preserved verbatim.
  - When opening a batch in a new window, open the first URL with `firefox --new-window "<url0>"`, wait briefly (`~1s`) for the window to initialize, and pass explicit `--new-tab` flags for subsequent URLs:
    `firefox --new-tab "<url1>" --new-tab "<url2>" ...`
    *(Passing bare positional URLs without `--new-tab` can cause the first tab in the batch to be overwritten.)*
  - If opening many URLs targeting the same search engine (e.g., 10+ Google search tabs), stagger requests slightly (`--stagger 0.2`) or note that simultaneous requests may trigger a rate-limit CAPTCHA (`/sorry/index`).
  - Use the helper script to open a URL list or synced device tabs directly:
    ```bash
    python3 <skill-directory>/scripts/firefox_inspect.py open-urls --new-window "<url1>" "<url2>"
    python3 <skill-directory>/scripts/firefox_inspect.py open-urls --new-window --from-synced-device "iPhone"
    ```
  - **Built-in Firefox UI alternative:** **Firefox View** (top-left tab strip icon) > **Tabs from other devices**, or `☰` > **History** > **Synced tabs** > right-click device > **Open All in Tabs**.

## 5. Protocol Handlers & Scheme Dispatching (`handlers.json` & Private Browsing)

When dealing with external URL schemes (`magnet:`, `mailto:`, `zoommtg:`, `slack:`, `steam:`):

### A. The URI Dispatch Pipeline (`nsContentDispatchChooser`)
Firefox evaluates external scheme triggers in a three-step waterfall before opening an external application:
1. **Global Scheme Authorization:** Queries `network.protocol-handler.external.<scheme>` (default `false`).
2. **User Gesture Gate:** Checks if the load has transient user activation (`aHasValidUserGestureActivation`). If `network.protocol-handler.prompt-without-user-activation` is `true`, scripted/automatic triggers are gated.
3. **Double-Keyed Site Permission:** Checks `open-protocol-handler^<scheme>` stored per-origin in `permissions.sqlite`.

### B. The Private Browsing Isolation Trap
- In **Private Browsing Mode**, all site permissions carry origin attribute `privateBrowsingId = 1` and are stored strictly in ephemeral RAM. They are **never written to disk** (`permissions.sqlite`) and are purged immediately when the private window or session closes.
- Consequently, checking *"Always allow <site> to open <scheme> links"* inside a private window **always fails to persist** across sessions or when visiting different index domains.

### C. The Protocol-Level Exemption Pattern
To permanently bypass prompts for a protocol in **both normal and Private Browsing modes**:
- Set `network.protocol-handler.external.<scheme>` to `true`.
- Set `network.protocol-handler.warn-external.<scheme>` to `false`.
- Ensure `<profile>/handlers.json` maps the scheme to an action:
  - `action: 4` (`useSystemDefault`): Delegates to OS default handler (`xdg-mime query default x-scheme-handler/<scheme>`).
  - `action: 2` (`useHelperApp`): Delegates to a specific application executable or web template.
  - `ask: false` (or omit `"ask"`): Skips the application picker dialog.

Inspect registered handlers and system defaults with the helper script:
```bash
python3 <skill-directory>/scripts/firefox_inspect.py handlers
python3 <skill-directory>/scripts/firefox_inspect.py handlers --scheme magnet
```

---

## 6. Safe Profile Configuration (`user.js` vs. Live `prefs.js`)

**Golden Rule:** Never write directly to `prefs.js` while Firefox is running. Firefox maintains an in-memory preference tree and will silently overwrite `prefs.js` with its in-memory snapshot on shutdown.

### Non-Destructive Staging via `user.js`
- `<profile>/user.js` is Firefox's dedicated, persistent user override file.
- **Safety guarantee:** Firefox **never writes to or modifies `user.js`**. It only reads it during startup and merges its values into `prefs.js`.
- It is safe to create or append to `user.js` while Firefox is active. Preferences staged there will take effect on the next browser launch.
- If an immediate change is required without restarting the browser, instruct the user to toggle the preference via `about:config` in their live window.

List or stage preferences non-destructively with the helper script:
```bash
# View all preferences currently staged in user.js
python3 <skill-directory>/scripts/firefox_inspect.py user-prefs

# Stage a persistent boolean, integer, or string preference
python3 <skill-directory>/scripts/firefox_inspect.py set-user-pref --key "network.protocol-handler.external.magnet" --value true
python3 <skill-directory>/scripts/firefox_inspect.py set-user-pref --key "network.protocol-handler.warn-external.magnet" --value false
```

---

## 7. In-Page DOM Automation (Conditional)

When a task requires interacting with page DOM inside the user's logged-in Firefox session (clicking elements, filling forms, reading rendered state):

- Check whether `firefox-cli` (`command -v firefox-cli`) or a Firefox WebDriver BiDi MCP server is installed and active.
- If unavailable, do not restart the user's running Firefox session to add `--remote-debugging-port` without asking first; discuss installing `firefox-cli` or using read-only profile inspection.

## 8. Upstream Provenance & References

Consult [references/upstream.md](references/upstream.md) for provenance records, evaluated upstream projects (`firefox-cli`, Mozilla DevTools BiDi, Firefox Sync schema, `mozLz40` specifications), and re-evaluation triggers.
