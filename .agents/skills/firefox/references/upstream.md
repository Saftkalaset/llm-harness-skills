# Upstream Provenance: Firefox Local Operations & Profile Inspection

This document records the upstream tools, specifications, and community implementations evaluated for the `firefox` skill. Refer to these references when updating inspection helpers, session parsing, or automation interfaces.

## Provenance Ledger

| Source / Tool | Repository / Reference | Commit / Version / Spec | Evaluation Date | Origin Classification | Borrowed Concepts | Local Divergence / Customizations | Re-evaluation Triggers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **firefox-cli** | [respawn-llc/firefox-cli](https://github.com/respawn-llc/firefox-cli) | `c118396bcd` (v0.2.x) | 2026-11-07 | Inspiration & boundary model | CLI tab listing and manipulation, active window queries, session boundaries. | Does not require installing an external binary or attaching `--remote-debugging-port` to the user's running browser; implements direct zero-dependency Python inspection via SQLite WAL copies and `mozLz40` decompression. | `firefox-cli` adds stable read-only queries without requiring remote debugging ports or browser restarts. |
| **Firefox DevTools MCP / WebDriver BiDi** | [mozilla/firefox-devtools-mcp](https://github.com/mozilla/firefox-devtools-mcp) & [W3C WebDriver BiDi](https://w3c.github.io/webdriver-bidi/) | Working Draft / MCP v1.x | 2026-11-07 | Protocol standard | Standardized protocol for browser inspection and automation, distinguishing passive session queries from active DOM actions. | Read-only passive inspection is handled entirely out-of-process via disk artifacts (`places.sqlite`, `synced-tabs.db`, `recovery.jsonlz4`), reserving active DevTools/BiDi for explicit DOM automation tasks. | Official Mozilla MCP server becomes packaged and distributed through standard Ubuntu/Snap channels. |
| **Firefox Sync Engine (`synced-tabs.db`)** | [Firefox Source Docs: Services / Sync](https://firefox-source-docs.mozilla.org/services/sync/) | Firefox Sync Schema | 2026-11-07 | Application data specification | JSON schema structure of `record` column in `synced-tabs.db` (`clientName`, `tabs[]` with `title`, `urlHistory`, `lastUsed`). | Implemented safe SQLite WAL snapshotting (`synced-tabs.db` + `-wal` + `-shm` copied to temporary directories) to prevent locking live browser SQLite databases while reading. | Firefox Sync schema migrations or changes in SQLite storage structure for synced device records. |
| **Mozilla mozLz40 Compression Format** | [Firefox Source Docs: toolkit/components/lz4](https://firefox-source-docs.mozilla.org/) | `mozLz40` Header Spec | 2026-11-07 | File format specification | 8-byte magic header `b"mozLz40\x00"` + 4-byte little-endian uncompressed size integer followed by raw LZ4 block. | Decompression implemented in pure standard library Python via `ctypes` calling system `liblz4.so.1` (`LZ4_decompress_safe`), bypassing PEP 668 externally-managed environment restrictions without requiring `pip install`. | Mozilla changes sessionstore compression algorithms (e.g., Zstandard migration) or header format. |

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
