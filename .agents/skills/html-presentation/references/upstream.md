# Upstream Provenance: HTML Presentation & Review Generator

This document records the upstream community skills, repositories, and specifications evaluated for `html-presentation`. Refer to these sources when evaluating updates, expanding presentation features, or refactoring styling tokens.

## Provenance Ledger

| Source / Project | Repository / URL | Commit / Tag Evaluated | Evaluation Date | Origin Classification | Concepts Adopted vs. Future Backlog | Local Divergence & Customizations | Re-evaluation Triggers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **claude-report-skill** (`/report`) | [MarcinDudekDev/claude-report-skill](https://github.com/MarcinDudekDev/claude-report-skill) | `7fe4234286` (2025-10) | 2026-11-07 | Adapted synthesis | **Adopted:** Standalone single-file HTML reports, zero external CDN dependencies, dark-mode styling, badge indicators.<br>**Backlog:** Machine-readable JSON metadata block in footer. | Implemented via zero-dependency Python script (`render_report.py`) with CLI and stdin interfaces; added automated Firefox launching. | Upstream adds interactive client-side sorting, chart widgets, or collapsible trace blocks. |
| **frontend-slides** | [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) | `9906a34d64` (2025-08) | 2026-11-07 | Design inspiration | **Adopted:** None in current report template.<br>**Backlog:** 16:9 responsive slide decks, viewport auto-fit, minimal keyboard navigation (`ArrowLeft`, `ArrowRight`, `Space`, `f` for fullscreen). | Planned for future multi-slide comparison deck templates. | New responsive presentation layouts or accessibility enhancements upstream. |
| **html-presentation** | [wbohanw/html-presentation](https://github.com/wbohanw/html-presentation) | `3f811b781b` (2025-09) | 2026-11-07 | Design inspiration | **Adopted:** Assertion-Evidence design guideline (lead with conclusion in headings, support with tables/metrics in body).<br>**Backlog:** Viewport-fitted scroll-snap. | Applied to technical audits, software inventory reviews, and comparison tables rather than academic slides. | Updates to assertion-evidence layout patterns or multi-column responsive cards. |
| **html-ppt-skill** (HTML PPT Studio) | [lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill) | `fd16290679` (2025-09) | 2026-11-07 | Design inspiration | **Adopted:** Dark-mode color token palette.<br>**Backlog:** Multiple selectable themes (Nord, Tokyo Night, Neo-Brutalism). | Hardened into pure CSS custom properties with automatic `prefers-color-scheme` support. | Additional palette options or dynamic theme switcher components. |
| **ui-ux-pro-max-skill** | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | `b7d5353e01` (2025-10) | 2026-11-07 | Design inspiration | **Adopted:** Native system font stacks, accessible high-contrast tables with zebra-striping, compact metric cards. | Stripped of external utility CSS; inlined directly into `templates/report.html`. | New grid layouts or visual hierarchy recommendations. |

---

## Technical Notes

### 1. Zero External Dependencies
Reports must open cleanly from local disk (`file:///`) with no network connectivity. All styling is embedded in a `<style>` block without external CDN links (`fonts.googleapis.com`, `cdn.jsdelivr.net`, etc.).

### 2. Implemented Components
The current template (`templates/report.html`) implements:
- Responsive container with header metadata (`Title`, `Generated`, `Scope`, `Status`)
- Metric cards grid (`.cards-grid`, `.card`, `.card-title`, `.card-value`)
- Content sections with titles (`.section`, `.section-title`)
- Data tables with alternating row shading and status badges (`.badge-success`, `.badge-warning`, `.badge-danger`, `.badge-info`)
- Code and preformatted command blocks (`code`, `pre`)
- Light/dark mode switching via `@media (prefers-color-scheme: light)`
