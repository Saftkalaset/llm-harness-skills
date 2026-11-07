#!/usr/bin/env python3
"""Smoke tests for render_report.py"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = SKILL_DIR / "scripts" / "render_report.py"

# Import helper functions directly
sys.path.insert(0, str(SCRIPT_PATH.parent))
from render_report import compile_report, default_output_path


class TestRenderReport(unittest.TestCase):
    def test_compile_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "sub" / "report.html"
            result = compile_report(
                title="Test Title",
                content_html="<p>Test Content</p>",
                output_path=out_file,
                scope="Unit Test",
                status="Verified",
            )
            self.assertTrue(result.exists())
            html = result.read_text(encoding="utf-8")
            self.assertIn("Test Title", html)
            self.assertIn("<p>Test Content</p>", html)
            self.assertIn("Unit Test", html)
            self.assertIn("Verified", html)

    def test_default_output_path(self):
        path = default_output_path("My Custom Audit 123!")
        self.assertTrue(path.name.endswith(".html"))
        self.assertIn("my_custom_audit_123", path.name)

    def test_cli_missing_input_exits_with_error(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--input", "/nonexistent/path/report.html"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Input file not found", proc.stderr + proc.stdout)

    def test_cli_stdin_compilation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "output.html"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--title",
                    "CLI Stdin Test",
                    "--output",
                    str(out_file),
                ],
                input="<div>Hello from stdin</div>",
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertTrue(out_file.exists())
            self.assertIn("Hello from stdin", out_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
