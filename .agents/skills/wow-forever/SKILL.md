---
name: wow-forever
description: Research, optimize, and plan gameplay for World of Warcraft: Forever (1.60.1 / Classic+), including efficiency-first leveling routes, parallel profession progression (Skinning/Leatherworking), talent builds, datamined items/recipes/camps, and PvP realm survival. Use whenever the user asks about WoW Forever quests, leveling, professions, talents, gear, patterns, or economy.
---

# World of Warcraft: Forever Research & Optimization

Use this skill whenever researching or optimizing gameplay for **World of Warcraft: Forever** (Blizzard's standalone Classic+ branch, client build `1.60.1.*` / Interface `16001`, level 60 cap).

## 1. Load Character & Optimization Profile

1. Resolve this skill directory through any symlink to its repository location and read `../../../.local/system-context/wow-forever-profile.md` (following the [`system-context`](../system-context/SKILL.md) convention).
2. If `wow-forever-profile.md` does not exist yet on the current machine, consult [references/character-profile-template.md](references/character-profile-template.md) and ask the user to confirm their character class, race, level, server ruleset, professions, and optimization priorities.
3. Update `.local/system-context/wow-forever-profile.md` whenever the user reports a new character level, profession rank, talent respec, or gear milestone.

## 2. Query WoW: Forever Live Data (MCP + CLI Helper)

 Never rely purely on 2004/2019 Classic memory—**WoW: Forever modifies talent trees, lowers crafting skill requirements by ~25 points, adds the Camping system (`Camp Tent`, `Tanning Rack`), and introduces `Merchant's Favor` vendors and new zones/dungeons**. Always verify facts against live Forever sources:

### A. Native MCP Tools (Preferred When Registered)
- **`everloot` MCP (`https://everloot.app/mcp/public`)**:
  - `talent_tree(class, tree, builds)` — Inspect Forever's modified 1.60.1 talent trees (e.g., Druid *Feral Swiftness* moved to Row 2 at L15–16; *Leader of the Pack* at Row 5 / L30; *Primal Bite* and *Shifting Power* at Row 7 / L40).
  - `search_knowledge(query, kind, version="forever")` / `get_by_name(name, kind)` / `answer_sources(question)` — Search Forever reference data, game-file catalogs, and player-confirmed observations.
  - `item_page(itemId)`, `npc_page(npcId)`, `quest_page(questId)`, `vendor_page(vendorNpcId)`, `world_map_near(zone, x, y, radius)` — Check player-observed drops, vendor prices, and nearby map coordinates.
  - `profession_path(profession, fromSkill, toSkill)` & `recipe_thresholds(profession, recipe)` — Check yellow/green/grey skill ranges and leveling paths.
  - `market_value(realm, itemId)` & `auction_history(realm, itemId)` — Check realm auction prices for leather, hides, elixirs, and BoE patterns.
  - `recent_changes(filter, game="forever")` & `ecosystem_projects(board)` — Track latest Blizzard blue posts, hotfixes, client builds, and new community tools.
- **`wowdb` / Azeroth DB MCP (`https://azeroth.wiki/api/mcp`)**:
  - `search(query, kind, locale="enUS")` — Search datamined Forever DB2 records across `item`, `recipe`, `ability`, `spell`, `enchant`, `talent`, `legacy`, `race`, `quest`, `giver`, `camp`, `dungeon`, `achievement`, `faction`, and `guide`.
  - `get_entity(path, field)` — Read full item stats (`nativeDetails.stats`), recipe materials/minimumSkill/skillUps (`yellow`/`grey`), pattern item IDs (`taughtBy`), and camping station rules (`/forever/camping/camp-tent`, `/forever/camping/tanning-rack`).
  - `list_entities(kind, offset, limit)` — Browse all entities of a category sequentially.

### B. Bundled Zero-Dependency CLI Helper (Fallback & Batch Queries)
When MCP tools are unavailable in the current session, or when you want to run parallel compound queries across **Azeroth DB**, **Everloot**, and **Polestar** in a single command, run:

```bash
# Search both Azeroth DB and Everloot simultaneously
python3 <skill-directory>/scripts/wow_forever_query.py search "Deviate Scale" --kind recipe

# Fetch full entity details from Azeroth DB (by path) or Everloot (by ID)
python3 <skill-directory>/scripts/wow_forever_query.py entity "/forever/professions/leatherworking/deviate-scale-belt"

# Inspect WoW Forever 1.60.1 class talent trees
python3 <skill-directory>/scripts/wow_forever_query.py talents druid --tree "Feral Combat"

# List curated skinnable beasts per zone & Forever Leatherworking/Camping rules (from Polestar)
python3 <skill-directory>/scripts/wow_forever_query.py beasts --zone darkshore

# Check for new WoW Forever community tools, skills, and official hotfixes
python3 <skill-directory>/scripts/wow_forever_query.py ecosystem
```

## 3. Efficiency-First Leveling & Parallel Profession Methodology

When optimizing for **pure leveling speed to 60 with parallel Skinning & Leatherworking** (especially for a Feral Druid on a PvP server):

1. **Zero-Detour Beast Quest Loops:**
   - Prioritize quest clusters where the objective mobs are **skinnable beasts** (nightsabers, moonstalkers, thistle bears, boars, crocolisks, raptors, wolves, snapjaws, yetis). Every beast kill yields **Quest Progress + Combat XP + Skinning Skill + Leatherworking Material** in a single GCD cycle.
   - Avoid low-drop humanoids/mechanica/elementals unless they sit directly inside a high-density hub chain or reward a major weapon/feral upgrade.
2. **Exploit Forever's Camping System for XP/hr & Crafting:**
   - **Camp Tent (`/forever/camping/camp-tent`, LW 20):** Requires 5 Light Leather and a nearby Basic Campfire (1-hour shared camping cooldown). Sitting near a Camp Tent grants **up to 5% of a level in Rested XP** (+10% kill XP bonus) whenever current Rested XP is below 5%. Trigger this every 60 minutes on cooldown while out in the field.
   - **Tanning Rack (`/forever/camping/tanning-rack`, LW 140):** Replaces Camp Tent (providing the same 5% Rested XP bonus) and is **required in WoW: Forever** for many 125–225 recipes, *Cured Rugged Hide*, and specialization patterns. Its blueprint drops from **Razorclaw the Butcher** in *Shadowfang Keep*.
   - **Merchant's Favor Patterns:** Turn in supply crates at camps to earn *Merchant's Favor* (binds on pickup currency) and buy Forever-exclusive stat sets and *Forceful Thick Armor Kits* from **Daniel Stitchsong** (Three Corners, Redridge Mountains for Alliance) or **Pawani** (Crossroads for Horde).
3. **Account for Forever's -25 Leatherworking Skill Shift:**
   - In *WoW: Forever*, nearly every trainer Leatherworking recipe is taught **25 skill points earlier** and turns grey **25 points sooner** than in 2004 Classic (e.g., *Dark Leather Boots* at 35, *Embossed Leather Gloves* at 40, *Fine Leather Belt* at 55, *Heavy Leather* at 125).
   - Alliance **Expert Leatherworking (75–150)** is taught **only by Telonis in Darnassus** (and Artisan 150–300 by **Drakk Stonehand in Aerie Peak, Hinterlands**). Plan Darnassus/Aerie Peakhearth or flight transitions around hitting skill 50–75 and 125–150 so Skinning/LW never bottlenecks field grinding.
4. **Feral Druid Power Spikes & PvP Server Survival:**
   - **Level 15–16:** *2/2 Feral Swiftness* (+30% outdoor movement speed in Bear/Cat Form, moved to Row 2 in Forever!). Use Bear Form outdoors between pulls for +30% run speed even before Level 20 Cat Form!
   - **Level 20:** *Cat Form* (+40 + Agility AP, instant movement-impairment break, *Prowl* stealth).
   - **Level 30:** *Travel Form* + *Leader of the Pack* (moved to Row 5 / 20 points in Forever!).
   - **PvP Server Discipline:** In contested zones, grind beast pockets away from main road choke points, keep *Shadowmeld* + *Prowl* ready for drinking/ambush avoidance, and use shapeshifting to break roots/slows instantly.

## 4. Future Skill & Ecosystem Discovery Protocol

Because *World of Warcraft: Forever* is an actively evolving Classic+ branch:
1. Periodically run `python3 <skill-directory>/scripts/wow_forever_query.py ecosystem` (or call `everloot.ecosystem_projects` and `everloot.recent_changes`) and search GitHub/skill registries for new `SKILL.md` packages, MCP servers, or simulation repositories (`wowsims/forever`, `fitzforge/polestar`, `alcaras/forever-ref`).
2. Whenever a new community research skill, MCP server, or datamining tool for *WoW: Forever* is discovered:
   - Evaluate its capabilities and safety.
   - Record its source URL, version/commit, date, borrowed concepts, and re-evaluation triggers in [references/upstream.md](references/upstream.md).
   - Integrate its workflow or endpoint into this skill (`SKILL.md` and `scripts/wow_forever_query.py`) and register new verified MCP endpoints if requested.

## 5. Deliverable & Completion Workflow

- **Clarifying Questions First:** If critical context is missing (e.g., unknown current zone, current Leatherworking/Skinning skill rank, or dungeon group availability), ask concise clarifying questions (stating a recommended default first).
- **Mandatory HTML Guide & Interactive Form in Firefox Upon Completion:** Whenever research finishes and you have **no remaining questions to ask**, you **must** compile the actionable guide, route table, recipe/pattern targets, and an interactive progress/checklist form using [`html-presentation`](../html-presentation/SKILL.md) (`scripts/render_report.py --open`) so it opens directly in Firefox:
  ```bash
  cat << 'EOF' | python3 <html-presentation-skill-dir>/scripts/render_report.py \
    --title "WoW Forever Efficiency Guide: <Bracket / Topic>" \
    --scope "Night Elf Feral Druid (PvP) • Skinning & Leatherworking" \
    --status "Ready to Execute" \
    --open
  <!-- Metric Cards, Step-by-Step Beast/Quest Route Table, Craft & Pattern Targets, and Interactive Progress Form -->
  EOF
  ```
- **Conversational Output:** Keep chat output concise—provide a structured Markdown summary table and a clickable `file:///` link to the HTML report.
