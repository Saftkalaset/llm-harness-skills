---
name: html-presentation
description: Generate standalone, self-contained HTML presentations, analytical reviews, and audit reports for user review, and open them in Firefox. Use whenever preparing user-facing reports, comparison decks, or reviews that are not part of persistent codebase markdown.
---

# HTML Presentation & Review Generator

Use this skill when preparing ad-hoc analytical reports, audits, comparison decks, or presentations for the user. Do not deliver temporary reviews or presentations as raw Markdown files.

## 1. When to Use HTML vs. Markdown

- **HTML Deliverable:** Ad-hoc software reviews, system audits, design presentations, comparison tables, and any transient deliverables intended for user review. Always link with `file:///` and offer to open in Firefox.
- **Markdown Deliverable:** Persistent repository context (`README.md`, `PROJECT.md`), agent skills (`SKILL.md`), and tracked operational runbooks.
- **Terminal Output:** In direct conversational responses, separate items, options, and findings into structured Markdown tables for rapid scanning.

## 2. Report Compilation Workflow

Use the bundled zero-dependency helper to compile structured HTML and launch it in Firefox:

```bash
python3 <skill-directory>/scripts/render_report.py \
  --title "Software Inventory & Maintainability Review" \
  --scope "Workstation Package Audit" \
  --status "Completed" \
  --output "~/Documents/reviews/package_audit.html" \
  --open
```

Or pass content through stdin:

```bash
cat << 'EOF' | python3 <skill-directory>/scripts/render_report.py --title "Audit Summary" --output /tmp/audit.html --open
<div class="cards-grid">
  <div class="card"><div class="card-title">Packages Reviewed</div><div class="card-value">245</div></div>
  <div class="card"><div class="card-title">Pending Upgrades</div><div class="card-value">0</div></div>
</div>
<div class="section">
  <h2 class="section-title">Findings</h2>
  <table>
    <thead><tr><th>Item</th><th>Status</th><th>Notes</th></tr></thead>
    <tbody>
      <tr><td>Signal Desktop</td><td><span class="badge badge-success">Active</span></td><td>APT repository verified</td></tr>
    </tbody>
  </table>
</div>
EOF
```

## 3. Design Standards & References

- **Zero External Dependencies:** CSS and fonts must be inlined; do not link external CDNs (like unpkg or Google Fonts) so reports render instantly offline.
- **Typography & Theme:** Use native system font stacks (`-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, `Inter`) with automatic dark/light mode switching (`prefers-color-scheme`).
- **High Data Density:** Use structured tables with zebra-striping (`.badge-success`, `.badge-warning`, `.badge-danger`, `.badge-info`), metric cards (`.card`), and code blocks (`pre code`).
- **Upstream Inspiration & Evolution:** Consult [references/upstream.md](references/upstream.md) for provenance records, evaluated upstream repositories (`claude-report-skill`, `frontend-slides`, `html-presentation`), and re-evaluation triggers.
