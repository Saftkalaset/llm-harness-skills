#!/usr/bin/env python3
"""Zero-dependency helper for inspecting and operating local Firefox profiles."""

import argparse
import configparser
import ctypes
import json
import os
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CANDIDATE_ROOTS = [
    Path.home() / "snap/firefox/common/.mozilla/firefox",
    Path.home() / ".mozilla/firefox",
    Path.home() / ".var/app/org.mozilla.firefox/.mozilla/firefox",
    Path.home() / "Library/Application Support/Firefox/Profiles",
]


def find_active_profile(explicit_profile: str | None = None) -> Path:
    if explicit_profile:
        p = Path(explicit_profile).expanduser().resolve()
        if not p.is_dir():
            raise SystemExit(f"Profile directory not found: {p}")
        return p

    candidates: list[Path] = []
    for root in CANDIDATE_ROOTS:
        if not root.is_dir():
            continue
        ini_path = root / "profiles.ini"
        if ini_path.is_file():
            cp = configparser.ConfigParser()
            cp.read(ini_path)
            for section in cp.sections():
                if cp.has_option(section, "Path"):
                    rel = cp.get(section, "Path")
                    is_rel = cp.get(section, "IsRelative", fallback="1") == "1"
                    prof_dir = (root / rel) if is_rel else Path(rel)
                    if prof_dir.is_dir():
                        candidates.append(prof_dir.resolve())
        for child in root.iterdir():
            if child.is_dir() and (
                ".default" in child.name or (child / "places.sqlite").exists()
            ):
                resolved = child.resolve()
                if resolved not in candidates:
                    candidates.append(resolved)

    if not candidates:
        raise SystemExit(
            "No Firefox profile found in standard Snap, native, Flatpak, or macOS locations."
        )

    def profile_freshness(prof: Path) -> float:
        markers = [
            prof / "sessionstore-backups/recovery.jsonlz4",
            prof / "synced-tabs.db-wal",
            prof / "synced-tabs.db",
            prof / "places.sqlite-wal",
            prof / "places.sqlite",
        ]
        mtimes = [m.stat().st_mtime for m in markers if m.exists()]
        return max(mtimes) if mtimes else prof.stat().st_mtime

    candidates.sort(key=profile_freshness, reverse=True)
    return candidates[0]


def decompress_mozlz4(path: Path) -> dict:
    with path.open("rb") as f:
        magic = f.read(8)
        if magic != b"mozLz40\x00":
            raise SystemExit(f"Unexpected header in {path}: {magic!r}")
        uncompressed_size = struct.unpack("<I", f.read(4))[0]
        compressed = f.read()

    for libname in ("liblz4.so.1", "liblz4.so", "liblz4.dylib"):
        try:
            lz4 = ctypes.cdll.LoadLibrary(libname)
            out_buf = ctypes.create_string_buffer(uncompressed_size)
            res = lz4.LZ4_decompress_safe(
                compressed, out_buf, len(compressed), uncompressed_size
            )
            if res < 0:
                raise RuntimeError(f"LZ4_decompress_safe returned {res}")
            return json.loads(out_buf.raw[:res].decode("utf-8"))
        except OSError:
            continue

    try:
        import lz4.block  # type: ignore

        raw = lz4.block.decompress(compressed, uncompressed_size=uncompressed_size)
        return json.loads(raw.decode("utf-8"))
    except ImportError as exc:
        raise SystemExit(
            "Could not load liblz4 shared library via ctypes or python lz4.block."
        ) from exc


def load_synced_tabs(profile: Path, device_filter: str | None = None) -> list[dict]:
    db_path = profile / "synced-tabs.db"
    if not db_path.exists():
        return []

    with tempfile.TemporaryDirectory(prefix="ff-sync-") as tmpdir:
        tmp_db = Path(tmpdir) / "synced-tabs.db"
        for suffix in ("", "-wal", "-shm"):
            src = Path(str(db_path) + suffix)
            if src.exists():
                shutil.copy2(src, Path(str(tmp_db) + suffix))

        conn = sqlite3.connect(str(tmp_db))
        try:
            rows = conn.execute(
                "SELECT guid, record, last_modified FROM tabs ORDER BY last_modified DESC"
            ).fetchall()
        finally:
            conn.close()

    devices = []
    for guid, record_json, last_mod in rows:
        data = json.loads(record_json)
        client_name = data.get("clientName", guid)
        if device_filter and device_filter.lower() not in client_name.lower():
            continue
        tabs_out = []
        for t in data.get("tabs", []):
            urls = t.get("urlHistory") or []
            tabs_out.append(
                {
                    "title": t.get("title") or "",
                    "url": urls[0] if urls else "",
                    "urlHistory": urls,
                    "lastUsed": t.get("lastUsed"),
                }
            )
        devices.append(
            {
                "guid": guid,
                "clientName": client_name,
                "lastModified": last_mod,
                "tabs": tabs_out,
            }
        )
    return devices


def load_open_tabs(profile: Path, window_num: int | None = None) -> list[dict]:
    candidates = [
        profile / "sessionstore-backups/recovery.jsonlz4",
        profile / "sessionstore.jsonlz4",
        profile / "sessionstore-backups/previous.jsonlz4",
    ]
    session_file = next((p for p in candidates if p.exists()), None)
    if not session_file:
        raise SystemExit(f"No sessionstore file found in {profile}")

    data = decompress_mozlz4(session_file)
    windows_out = []
    for idx, win in enumerate(data.get("windows", []), start=1):
        if window_num is not None and idx != window_num:
            continue
        tabs_out = []
        for t_idx, tab in enumerate(win.get("tabs", []), start=1):
            entries = tab.get("entries") or []
            current = entries[-1] if entries else {}
            tabs_out.append(
                {
                    "index": t_idx,
                    "title": current.get("title") or "",
                    "url": current.get("url") or "",
                    "lastAccessed": tab.get("lastAccessed"),
                }
            )
        windows_out.append({"window": idx, "tabs": tabs_out})
    return windows_out


def open_urls(
    urls: list[str],
    new_window: bool = False,
    window_delay: float = 1.0,
    stagger: float = 0.0,
) -> None:
    clean_urls = [u for u in urls if u]
    if not clean_urls:
        raise SystemExit("No URLs provided to open.")

    firefox_bin = shutil.which("firefox") or "/snap/bin/firefox"

    if new_window:
        subprocess.run([firefox_bin, "--new-window", clean_urls[0]], check=True)
        remaining = clean_urls[1:]
        if remaining:
            time.sleep(window_delay)
    else:
        remaining = clean_urls

    if not remaining:
        return

    if stagger > 0:
        for u in remaining:
            subprocess.run([firefox_bin, "--new-tab", u], check=True)
            time.sleep(stagger)
    else:
        cmd = [firefox_bin]
        for u in remaining:
            cmd.extend(["--new-tab", u])
        subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="Explicit Firefox profile directory path")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("profile", help="Print the active Firefox profile path")

    p_sync = sub.add_parser("synced-tabs", help="List tabs from Firefox Sync devices")
    p_sync.add_argument("--device", help="Filter by device clientName substring")
    p_sync.add_argument("--json", action="store_true", help="Output JSON")

    p_open = sub.add_parser("open-tabs", help="List currently open windows and tabs")
    p_open.add_argument("--window", type=int, help="Filter to 1-based window number")
    p_open.add_argument("--json", action="store_true", help="Output JSON")

    p_launch = sub.add_parser("open-urls", help="Reliably open URLs in Firefox")
    p_launch.add_argument(
        "--new-window",
        action="store_true",
        help="Open the first URL in a new window and the rest as tabs",
    )
    p_launch.add_argument(
        "--from-synced-device",
        help="Open all synced tabs from the matching device substring",
    )
    p_launch.add_argument(
        "--window-delay",
        type=float,
        default=1.0,
        help="Seconds to wait after --new-window before adding tabs (default: 1.0)",
    )
    p_launch.add_argument(
        "--stagger",
        type=float,
        default=0.0,
        help="Seconds between individual --new-tab calls (default: 0, batch mode)",
    )
    p_launch.add_argument("urls", nargs="*", help="URLs to open")

    args = parser.parse_args()
    profile = find_active_profile(args.profile)

    if args.cmd == "profile":
        print(profile)
        return

    if args.cmd == "synced-tabs":
        devices = load_synced_tabs(profile, args.device)
        if args.json:
            print(json.dumps(devices, indent=2, ensure_ascii=False))
            return
        for dev in devices:
            tabs = dev["tabs"]
            print(f"Device: {dev['clientName']} ({len(tabs)} tabs)")
            for idx, t in enumerate(tabs, start=1):
                print(f"  {idx:2d}. {t['title']} -> {t['url']}")
        return

    if args.cmd == "open-tabs":
        windows = load_open_tabs(profile, args.window)
        if args.json:
            print(json.dumps(windows, indent=2, ensure_ascii=False))
            return
        for win in windows:
            tabs = win["tabs"]
            print(f"Window {win['window']} ({len(tabs)} tabs):")
            for t in tabs:
                print(f"  {t['index']:2d}. {t['title']} -> {t['url']}")
        return

    if args.cmd == "open-urls":
        target_urls = list(args.urls)
        if args.from_synced_device:
            devices = load_synced_tabs(profile, args.from_synced_device)
            for dev in devices:
                target_urls.extend(t["url"] for t in dev["tabs"] if t.get("url"))
        open_urls(
            target_urls,
            new_window=args.new_window,
            window_delay=args.window_delay,
            stagger=args.stagger,
        )
        print(f"Opened {len(target_urls)} tab(s).")


if __name__ == "__main__":
    main()
