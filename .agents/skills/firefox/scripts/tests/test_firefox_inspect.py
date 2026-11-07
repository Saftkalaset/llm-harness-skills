#!/usr/bin/env python3
"""Smoke tests for firefox_inspect.py"""

import ctypes
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = SKILL_DIR / "scripts" / "firefox_inspect.py"

sys.path.insert(0, str(SCRIPT_PATH.parent))
from firefox_inspect import find_active_profile, decompress_mozlz4


class TestFirefoxInspect(unittest.TestCase):
    def test_find_active_profile_or_skip(self):
        try:
            prof = find_active_profile()
            self.assertTrue(prof.is_dir())
        except SystemExit:
            # If running in environment without Firefox profile, skip gracefully
            self.skipTest("No local Firefox profile installed")

    def test_decompress_mozlz4_invalid_magic(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonlz4", delete=False) as f:
            f.write(b"invalid_header_here")
            tmp_path = Path(f.name)
        try:
            with self.assertRaises(SystemExit):
                decompress_mozlz4(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_decompress_mozlz4_synthetic_payload(self):
        # Create a valid mozLz40 file using ctypes liblz4 compress
        try:
            lz4 = ctypes.cdll.LoadLibrary("liblz4.so.1")
        except OSError:
            self.skipTest("liblz4.so.1 not available")

        payload = {"windows": [{"tabs": [{"index": 1, "entries": [{"url": "https://example.com"}]}]}]}
        raw_bytes = json.dumps(payload).encode("utf-8")
        uncompressed_size = len(raw_bytes)

        max_dest_size = lz4.LZ4_compressBound(uncompressed_size)
        comp_buf = ctypes.create_string_buffer(max_dest_size)
        comp_size = lz4.LZ4_compress_default(
            raw_bytes, comp_buf, uncompressed_size, max_dest_size
        )
        self.assertGreater(comp_size, 0)

        with tempfile.NamedTemporaryFile(suffix=".jsonlz4", delete=False) as f:
            f.write(b"mozLz40\x00")
            f.write(struct.pack("<I", uncompressed_size))
            f.write(comp_buf.raw[:comp_size])
            tmp_path = Path(f.name)

        try:
            decompressed = decompress_mozlz4(tmp_path)
            self.assertEqual(decompressed, payload)
        finally:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
