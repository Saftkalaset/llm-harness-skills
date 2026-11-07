#!/usr/bin/env python3
"""Zero-dependency HTML report compiler and Firefox launcher."""

import argparse
import datetime
import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = SKILL_DIR / "templates" / "report.html"


def compile_report(
    title: str,
    content_html: str,
    output_path: Path,
    scope: str = "System Review",
    status: str = "Ready for Review",
) -> Path:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"Template not found at {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rendered = (
        template.replace("{{TITLE}}", html.escape(title))
        .replace("{{DATE}}", html.escape(now_str))
        .replace("{{SCOPE}}", html.escape(scope))
        .replace("{{STATUS}}", html.escape(status))
        .replace("{{CONTENT}}", content_html)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return output_path.resolve()


def open_in_firefox(file_path: Path) -> None:
    firefox_bin = shutil.which("firefox") or "/snap/bin/firefox"
    uri = file_path.resolve().as_uri()
    subprocess.run([firefox_bin, "--new-tab", uri], check=True)


def default_output_path(title: str) -> Path:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", title.lower()).strip("_") or "report"
    date_prefix = datetime.date.today().isoformat()
    reviews_dir = Path.home() / "Documents" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    return reviews_dir / f"{date_prefix}_{slug}.html"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", default="Analysis & Review Report")
    parser.add_argument("--scope", default="System Review")
    parser.add_argument("--status", default="Ready for Review")
    parser.add_argument(
        "--input", "-i", type=Path, help="Input HTML or snippet file"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output HTML file path (defaults to ~/Documents/reviews/YYYY-MM-DD_<slug>.html)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open in Firefox after compiling",
    )
    args = parser.parse_args()

    if args.input:
        resolved_input = args.input.expanduser()
        if not resolved_input.exists():
            raise SystemExit(f"Input file not found: {resolved_input}")
        body = resolved_input.read_text(encoding="utf-8")
    else:
        body = (
            sys.stdin.read()
            if not sys.stdin.isatty()
            else "<p>No content provided.</p>"
        )

    out_path = args.output.expanduser() if args.output else default_output_path(args.title)

    out = compile_report(
        title=args.title,
        content_html=body,
        output_path=out_path,
        scope=args.scope,
        status=args.status,
    )
    print(f"Report compiled: {out}")
    if args.open:
        open_in_firefox(out)
        print("Opened in Firefox.")


if __name__ == "__main__":
    main()
