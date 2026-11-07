# Upstream Provenance: Firefox Local Operations & Profile Inspection

This document records the upstream tools, specifications, and community implementations evaluated for the `firefox` skill. Refer to these references when updating inspection helpers, session parsing, or automation interfaces.

## Provenance Ledger

| Source / Tool | Repository / Reference | Commit / Version / Spec | Evaluation Date | Origin Classification | Borrowed Concepts | Local Divergence / Customizations | Re-evaluation Triggers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **firefox-cli** | [respawn-llc/firefox-cli](https://github.com/respawn-llc/firefox-cli) | `c118396bcd` (v0.2.x) | 2026-11-07 | Inspiration & boundary model | CLI tab listing and manipulation, active window queries, session boundaries. | Does not require installing an external binary or attaching `--remote-debugging-port` to the user's running browser; implements direct zero-dependency Python inspection via SQLite WAL copies and `mozLz40` decompression. | `firefox-cli` adds stable read-only queries without requiring remote debugging ports or browser restarts. |
| **Firefox DevTools MCP / WebDriver BiDi** | [mozilla/firefox-devtools-mcp](https://github.com/mozilla/firefox-devtools-mcp) & [W3C WebDriver BiDi](https://w3c.github.io/webdriver-bidi/) | Working Draft / MCP v1.x | 2026-11-07 | Protocol standard | Standardized protocol for browser inspection and automation, distinguishing passive session queries from active DOM actions. | Read-only passive inspection is handled entirely out-of-process via disk artifacts (`places.sqlite`, `synced-tabs.db`, `recovery.jsonlz4`), reserving active DevTools/BiDi for explicit DOM automation tasks. | Official Mozilla MCP server becomes packaged and distributed through standard Ubuntu/Snap channels. |
| **Firefox Sync Engine (`synced-tabs.db`)** | [Firefox Source Docs: Services / Sync](https://firefox-source-docs.mozilla.org/services/sync/) | Firefox Sync Schema | 2026-11-07 | Application data specification | JSON schema structure of `record` column in `synced-tabs.db` (`clientName`, `tabs[]` with `title`, `urlHistory`, `lastUsed`). | Implemented safe SQLite WAL snapshotting (`synced-tabs.db` + `-wal` + `-shm` copied to temporary directories) to prevent locking live browser SQLite databases while reading. | Firefox Sync schema migrations or changes in SQLite storage structure for synced device records. |
| **Mozilla mozLz40 Compression Format** | [Firefox Source Docs: toolkit/components/lz4](https://firefox-source-docs.mozilla.org/) | `mozLz40` Header Spec | 2026-11-07 | File format specification | 8-byte magic header `b"mozLz40\x00"` + 4-byte little-endian uncompressed size integer followed by raw LZ4 block. | Decompression implemented in pure standard library Python via `ctypes` calling system `liblz4.so.1` (`LZ4_decompress_safe`), bypassing PEP 668 externally-managed environment restrictions without requiring `pip install`. | Mozilla changes sessionstore compression algorithms (e.g., Zstandard migration) or header format. |
| **Mozilla Scheme Dispatch (`nsContentDispatchChooser`)** | [mozilla-central: uriloader/exthandler](https://searchfox.org/mozilla-central/source/uriloader/exthandler/) | Gecko Dispatch Pipeline | 2026-11-07 | Browser subsystem architecture | Waterfall evaluation for custom/external URI schemes: global pref check (`network.protocol-handler.external.<scheme>`), transient user activation check, and double-keyed site permissions (`open-protocol-handler^<scheme>`). | Discovered and documented the Private Browsing isolation trap: `privateBrowsingId = 1` isolates site permissions strictly in memory, purging them on window close. Documented the protocol exemption pattern via `user.js`. | Mozilla alters permission gating or removes `network.protocol-handler.external.<scheme>` overrides. |
| **Firefox `user.js` Preference Architecture** | [Firefox Source Docs: modules/libpref](https://firefox-source-docs.mozilla.org/) | `libpref` Initialization Spec | 2026-11-07 | Configuration specification | `<profile>/user.js` startup precedence: values defined in `user.js` override and merge into `prefs.js` on every boot and are never modified or overwritten by browser runtime. | Implemented non-destructive preference staging in `firefox_inspect.py` (`stage-user-pref` / `user-prefs`), eliminating the risk of runtime `prefs.js` clobbering when modifying preferences while Firefox runs. | Mozilla changes preference file loading hierarchy or deprecates `user.js`. |

---

## Technical Notes

### 1. SQLite WAL Mode Safety
Firefox operates all profile databases in SQLite WAL (Write-Ahead Logging) mode. Live connections hold shared memory locks (`places.sqlite-shm`) and uncommitted transactions (`places.sqlite-wal`). Directly querying `places.sqlite` or `synced-tabs.db` while Firefox runs can cause database locked errors or read dirty state. The bundled helper `firefox_inspect.py` snapshots the main database file along with `-wal` and `-shm` to a temporary directory, runs read queries, and cleans up immediately.

### 2. mozLz40 Parsing Without External Wheels
Modern Linux distributions enforce PEP 668, blocking `pip install lz4` in system Python environments. The standard C library `liblz4.so.1` is natively available on Ubuntu:
```python
import ctypes, struct

lib = ctypes.CDLL("liblz4.so.1")
with open(path, "rb") as f:
    magic = f.read(8)  # b"mozLz40\x00"
    uncompressed_size = struct.unpack("<I", f.read(4))[0]
    compressed_data = f.read()
dest = ctypes.create_string_buffer(uncompressed_size)
ret = lib.LZ4_decompress_safe(compressed_data, dest, len(compressed_data), uncompressed_size)
```

### 3. Scheme Dispatch & Private Browsing Isolation Trap
In Firefox's `nsContentDispatchChooser`, permission checks for launching external applications via custom URI schemes (`open-protocol-handler^<scheme>`) are double-keyed by origin and protocol. In Private Browsing mode (`privateBrowsingId = 1`), permissions are partitioned into non-persistent in-memory tables. Because they are never written to `permissions.sqlite`, any user check on "Always allow <site> to open <scheme> links" is destroyed when the private window closes. Global scheme pre-approval via `network.protocol-handler.external.<scheme> = true` and `network.protocol-handler.warn-external.<scheme> = false` resolves this by bypassing the per-site permission check entirely.

### 4. Non-Destructive Live Preference Staging (`user.js`)
Firefox manages runtime preferences in an in-memory cache and periodically writes `prefs.js` to disk, including a full flush on shutdown. Editing `prefs.js` directly while Firefox is open will be overwritten on exit. In contrast, `user.js` in the profile directory is an override file that Firefox never writes to or deletes; it is only read during initialization to overwrite values in `prefs.js`. Using `firefox_inspect.py set-user-pref` safely stages preferences into `user.js` without browser conflicts.
