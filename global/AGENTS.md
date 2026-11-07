# Global Agent Guidelines & User Preferences

These guidelines apply across all projects, harnesses (Codex and Antigravity), and sessions.

## 1. Presentation & Delivery Standards

- **Ad-hoc Reviews, Reports & Presentations:** Do not deliver ad-hoc user reviews, analytical audits, comparison decks, or status presentations as raw Markdown files. Generate standalone, self-contained HTML reports with embedded CSS (no CDN dependencies) and open them in Firefox (or provide a clickable `file:///` link). Reserve Markdown strictly for persistent repository documentation, configuration, and agent skills.
- **Terminal & Conversational Output:** In direct responses, format concerns, options, packages, and multi-part findings into structured Markdown tables wherever possible for rapid scanning.
- **Clickable Links:** Always format file and directory paths as clickable Markdown links using the `file://` scheme.

## 2. System Operations & Maintenance

- **Installation Methods:** Prefer the system's established package managers (e.g. Snap for auto-updating desktop applications, APT with official DEB822 repositories for system tools). Keep changes reversible and easy to maintain.
- **Downtime & Daemons:** Consult the user before modifying running background services, scheduled tasks, or live databases.
- **Discovery Before Asking:** Inspect relevant system state via read-only commands (`/etc/os-release`, `uname`, `snap list`, `apt-cache policy`, `df -h`) before asking the user repeat configuration questions.
- **Interactive Inquiries:** When a question or clarification is necessary, state a recommended answer or best guess first and allow free-form user correction.
