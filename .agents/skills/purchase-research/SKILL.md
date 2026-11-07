---
name: purchase-research
description: Conduct values-aware, multi-objective purchase and consumption research across physical goods, digital services, local services/trades, and restaurants/cultural events. Use whenever the user asks to research, compare, or recommend products, subscriptions, software, contractors, dining, or local activities.
---

# Purchase & Consumption Research

Use this skill whenever researching or comparing physical products, digital services/software, physical/local services, or dining and cultural activities.

## 1. Load Personal Consumption Profile

1. Resolve this skill directory through any symlink to its repository location and read `../../../.local/system-context/consumption-preferences.md` (following the [`system-context`](../system-context/SKILL.md) convention).
2. If `consumption-preferences.md` does not exist yet on the current machine, consult [references/rubric-template.md](references/rubric-template.md) and ask the user to confirm their preferences before recording them.
3. Treat `.local/system-context/consumption-preferences.md` as the authoritative source of user weights, geographic/energy hierarchies, dietary defaults, and trade-off rules.

## 2. Classify the Consumption Domain

Identify which of the four domains applies (or combine them for hybrid purchases like hardware + cloud service):

| Domain | Key Evaluation Signals |
| :--- | :--- |
| **A. Physical Goods** | Origin & HQ hierarchy, metric/ISO & EU compatibility, material hierarchy (metals/natural fibers > silicone > plastics), chemical disclosures (PFAS/BPA), ODM/white-label tracing, community/official repair docs & 3D-printable parts, second-hand prosumer availability, no post-purchase subscription lock-in. |
| **B. Digital Services & Software** | Hosting & HQ jurisdiction, historical grid decarbonization (early coal/hydrocarbon phase-out; nuclear & hydro baseload preference), agent-friendly data migration (API/CLI/export), Linux & standard web support, transparent recurring pricing vs. one-time/open-source local tools. |
| **C. Physical & Local Services** | Independent/cooperative local providers over gig-platform middlemen or PE roll-ups, genuine employee satisfaction/retention signals over formal certificates alone, repair transparency and standard parts usage. |
| **D. Dining, Cultural Events & Local Activities** | Independent chef/artist/community venues over corporate chains, substance & craft over social-media hype, personal dietary fit (e.g., flexitarian/pescetarian), direct venue/primary box-office booking (strictly avoiding ticket scalping platforms). |

## 3. Execute Multi-Tiered Source Research

When delegating broad web searches, use a `research` subagent if available; otherwise perform targeted web searches directly. Enforce the source hierarchy from the user's profile:

1. **Discovery Leads Only (Tier 4 / Aggregators):** You may scan SEO affiliate roundups ("Best X"), Google Maps, or TripAdvisor **solely to discover candidate names, model numbers, menus, or primary links**. Never cite their rankings or star averages as proof of quality.
2. **Primary Verification (Tier 1 & Tier 2):**
   - **Goods & Software:** Cross-check candidates against independent testing labs (*Råd & Rön*, *Stiftung Warentest*, *Testfakta*, *RTINGS*, *Project Farm*, *GamersNexus*, *iFixit*), enthusiast/trade forums, and multi-year Reddit ownership threads.
   - **Dining & Culture:** Cross-check against local Reddit communities, local newspaper critics (*DN*, *SvD*, *GP*), *White Guide*, *Michelin Guide*, and direct venue calendars.
3. **Failure-Mode & White-Label Audit (Tier 3):**
   - Systematically inspect 1-to-3 star reviews, warranty complaints, and repair forums for structural failures occurring after 6–24 months.
   - For physical goods, check whether a brand is rebadging an ODM/white-label catalog item; if so, disclose the underlying OEM and fair-market price.

## 4. Resolve Competing Goals Explicitly

Do not silently filter out a functionally superior product because it violates a soft preference, and do not hide compromises behind a single opaque recommendation:

- **Quality First, Explicit Warnings:** If the highest-performing or most durable option uses a flagged chemical (e.g., PFAS/PTFE), is white-labeled, or originates outside preferred regions, **include it** and attach a clear warning badge (`badge-warning` or `badge-danger`).
- **Archetype Recommendations:** Present 3–4 distinct archetypes tailored to the query:
  1. **Best Overall / Performance Pick** — Highest functional or craft quality, noting any origin/material trade-offs.
  2. **Principled / Local Pick** — Best alignment with geographic, clean-energy grid, independent ownership, and material preferences.
  3. **Second-Hand / Long-Term Value (TCO) Pick** — Best used prosumer/commercial model (for goods) or best direct-value alternative.
- **Trade-Off Tension Matrix:** Always include a structured table showing where the user's goals conflicted on the shortlisted candidates.

## 5. Deliverable Format

- **Conversational Output:** Present quick summaries, archetype picks, and the Trade-Off Tension Matrix in compact Markdown tables.
- **Comprehensive Reports:** For multi-candidate evaluations, compile a standalone, self-contained HTML report using [`html-presentation`](../html-presentation/SKILL.md) (`scripts/render_report.py`) and open it in Firefox (or provide a clickable `file:///` link).
- **Provenance & Maintenance:** Consult [references/upstream.md](references/upstream.md) when upgrading this skill's research methodology.
