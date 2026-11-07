#!/usr/bin/env python3
"""Compile, hot-reload, and optionally serve the interactive 16-60 WoW: Forever Dynamic Progression Dashboard."""

import argparse
import html
import http.server
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
HTML_SKILL_RENDERER = SKILL_DIR.parent / "html-presentation" / "scripts" / "render_report.py"
DEFAULT_OUTPUT = Path.home() / "Documents" / "reviews" / "saftis_wow_forever_dashboard.html"
STATE_JSON_PATH = REPO_ROOT / ".local" / "system-context" / "wow-forever-state.json"
PROFILE_MD_PATH = REPO_ROOT / ".local" / "system-context" / "wow-forever-profile.md"
SYNC_PORT = 18765

WIKI = "https://azeroth.wiki/forever"


def ilink(slug_or_id: str, label: str, q: str = "uncommon") -> str:
    return f'<a class="wlink q-{q}" href="{WIKI}/items/{slug_or_id}" target="_blank" rel="noopener">{label}</a>'


def qlink(slug_or_id: str, label: str) -> str:
    return f'<a class="wlink q-quest" href="{WIKI}/quests/{slug_or_id}" target="_blank" rel="noopener">{label}</a>'


def dlink(slug: str, label: str) -> str:
    return f'<a class="wlink q-rare" href="{WIKI}/dungeons/{slug}" target="_blank" rel="noopener">{label}</a>'


ZONE_LEGS: List[Dict[str, Any]] = [
    {
        "id": "leg_wf",
        "min": 16,
        "max": 16,
        "name": "02-Westfall (Exit)",
        "beasts": "Great Goretusk, Coyote (Light/Med)",
        "notes": (
            f"Click Burned Remains <span class='coord'>Westfall 37.3, 50.6</span> ({qlink('79008', '...and that note you found')}) + "
            f"loot {ilink('15882', 'Half Pendant of Aquatic Endurance', 'quest')} <span class='coord'>17.9, 33.2</span> + "
            f"take Stormwind Boat <span class='coord'>22.7, 56.7</span>."
        ),
    },
    {
        "id": "leg_ds",
        "min": 16,
        "max": 20,
        "name": "03-Darkshore (Safe)",
        "beasts": "Thistle Bears (13–17), Moonstalkers (14–20) (Light/Med)",
        "notes": (
            f"<strong>Priority Sets:</strong> {qlink('983', 'Buzzbox 827')} &rarr; {qlink('1001', '411')} &rarr; {qlink('1002', '323')} &rarr; {qlink('1003', '525')} + "
            f"{qlink('2118', 'Plagued Lands')} &rarr; {qlink('2138', 'Cleansing of the Infected')} + "
            f"{qlink('4722', 'Beached Sea Turtle')} + South {qlink('944', 'The Master&#39;s Glaive')}. "
            f"Claim {ilink('idol-of-shifting-tides', 'Idol of Shifting Tides', 'uncommon')} &amp; L20 {qlink('98393', 'The Great Cat Spirit')}."
        ),
    },
    {
        "id": "leg_rr",
        "min": 20,
        "max": 22,
        "name": "04-Redridge",
        "beasts": "Great Goretusk (16–17), Thrasher (18–20) (Med)",
        "notes": (
            f"<strong>Priority Sets:</strong> Turn in {qlink('98247', 'Shipping Label (Q98247)')} at <span class='coord'>Redridge 15.3, 71.5</span> "
            f"(+2k ACA Rep, buy {ilink('pattern-brawler-s-leather-boots', 'Pattern: Brawler&#39;s Boots', 'rare')} &amp; "
            f"{ilink('pattern-brawler-s-leather-hood', 'Pattern: Brawler&#39;s Hood', 'rare')}) + {qlink('92', 'Redridge Goulash')}."
        ),
    },
    {
        "id": "leg_dw",
        "min": 22,
        "max": 25,
        "name": "05-Duskwood &amp; Wetlands",
        "beasts": "Dire Wolves (20–26), Crocolisks &amp; Mottled Raptors (21–26) (Med/Heavy)",
        "notes": (
            f"<strong>Priority Sets:</strong> Duskwood {qlink('56', 'The Night Watch')} ({ilink('gunnysack-of-the-night-watch', 'Free 10-Slot Bag', 'uncommon')}) + "
            f"{qlink('226', 'Wolves at Our Heels')}; Wetlands {qlink('484', 'Young Crocolisk Skins')} &rarr; {qlink('471', 'Apprentice&#39;s Duties')} + "
            f"{qlink('294', 'Ormer&#39;s Revenge')} + {qlink('98824', 'Prehistoric Prism')} ({ilink('heavehammer', 'Heavehammer +32 AP!', 'rare')})."
        ),
    },
    {
        "id": "leg_ash1",
        "min": 25,
        "max": 28,
        "name": "06-Ashenvale",
        "beasts": "Ashenvale Bears, Ghostpaw Alphas, Stags (21–28) (Heavy)",
        "notes": (
            f"<strong>Priority Sets:</strong> {qlink('991', 'Raene&#39;s Cleansing')} + {qlink('1054', 'Culling the Threat')} + "
            f"{qlink('1012', 'Insane Druids')} ({ilink('mavoris-s-warstaff', 'Mavoris&#39;s Warstaff +11 Str', 'uncommon')}) + "
            f"Stonetalon Sleeping Bag <span class='coord'>40.8, 52.6</span> ({qlink('79980', 'Scramble')})."
        ),
    },
    {
        "id": "leg_1k",
        "min": 28,
        "max": 30,
        "name": "07-Thousand Needles",
        "beasts": "Tortoises, Basilisks, Wyverns, Scorpids (28–34) (Heavy)",
        "notes": (
            f"Grab S. Barrens Sleeping Bag <span class='coord'>46.3, 73.9</span> ({qlink('79192', 'Stepping Stones')}). "
            f"Hit L30 for <strong>Travel Form</strong> + <strong>1/1 Leader of the Pack</strong>."
        ),
    },
    {
        "id": "leg_hb",
        "min": 30,
        "max": 32,
        "name": "30–32 Hillsbrad / Loch Modan",
        "beasts": "Elder Razormaw, Mountain Lions, Yetis (26–32) (Heavy)",
        "notes": (
            f"Finish {ilink('cozy-sleeping-bag', 'Cozy Sleeping Bag (+3–9% XP)', 'rare')} + {ilink('215365', '12-Slot Old Toolbox', 'uncommon')} "
            f"at <span class='coord'>Hillsbrad 87.2, 49.0</span> ({qlink('79975', 'This Must Be the Place')}) &rarr; <span class='coord'>Loch Modan 49.4, 13.0</span>."
        ),
    },
    {
        "id": "leg_des",
        "min": 32,
        "max": 35,
        "name": "32–35 Desolace &amp; E. Ashenvale",
        "beasts": "Scorpashi Scorpids, Bonepaw Hyenas (30–37) (Heavy/Thick)",
        "notes": "Train <strong>Ferocious Bite &amp; Ravage (L32)</strong>. Use <em>Track Humanoids</em> in Cat Form.",
    },
    {
        "id": "leg_stv1",
        "min": 35,
        "max": 37,
        "name": "35–37 STV North",
        "beasts": "Tigers, Panthers, Lashtail Raptors (30–35) (Heavy/Thick)",
        "notes": (
            f"<strong>Priority Set:</strong> {qlink('185', 'Tiger Mastery')} / {qlink('190', 'Panther Mastery')} / {qlink('194', 'Raptor Mastery')} "
            f"(100% skinnable beast kills). At LW 200/L35+, train <strong>Artisan LW</strong> at Aerie Peak."
        ),
    },
    {
        "id": "leg_bad1",
        "min": 37,
        "max": 40,
        "name": "37–40 Arathi &amp; Badlands",
        "beasts": "Crag Coyotes, Ridge Stalkers (35–42) (Thick Leather)",
        "notes": (
            f"<strong>Priority Quest:</strong> {qlink('739', 'Murdaloc (Q739)')} in Badlands for "
            f"{ilink('rock-pulverizer', 'Rock Pulverizer (+34 AP 2H Mace)', 'uncommon')}! Hit L40 for <strong>Dire Bear, Mount &amp; Row 7 Capstone</strong>."
        ),
    },
    {
        "id": "leg_fer",
        "min": 40,
        "max": 47,
        "name": "40–47 STV South, Feralas &amp; Tanaris",
        "beasts": "Elder Panthers, Ironfur Bears, Blisterpaw Hyenas (38–46) (Thick)",
        "notes": (
            f"Unlock <strong>Tribal LW (LW 235, L40)</strong> in Feralas &amp; craft "
            f"{ilink('wolfshead-helm', 'Wolfshead Helm', 'rare')}."
        ),
    },
    {
        "id": "leg_ung",
        "min": 47,
        "max": 52,
        "name": "47–52 Hinterlands &amp; Un'Goro",
        "beasts": "Silvermane Wolves, Ravasaurs, Devilsaurs (43–55) (Rugged &amp; Devilsaur)",
        "notes": (
            f"Complete L50 Druid quest ({qlink('9052', 'Blood of Morphaz')}) for "
            f"{ilink('feral-staff', 'Feral Staff (+17 Str, +16 Agi, +110 Armor)', 'rare')} &amp; farm {ilink('15417', 'Devilsaur Leather', 'uncommon')}."
        ),
    },
    {
        "id": "leg_60",
        "min": 52,
        "max": 60,
        "name": "52–60 Felwood, Winterspring, WPL &amp; Silithus",
        "beasts": "Angerclaw/Shardtooth Bears, Plagued Bears (48–60) (Rugged)",
        "notes": (
            f"Craft {ilink('warbear-woolies', 'Warbear Woolies', 'rare')} + "
            f"{ilink('devilsaur-gauntlets', 'Devilsaur Gauntlets', 'rare')} &amp; {ilink('devilsaur-leggings', 'Devilsaur Leggings', 'rare')} &rarr; Level 60!"
        ),
    },
]

WEAPON_PROGRESSION: List[Dict[str, Any]] = [
    {
        "id": "wpn_dm",
        "min": 16,
        "max": 19,
        "lvl": "16–18",
        "name_plain": "Smite's Mighty Hammer / Staff of Westfall",
        "name": f"{ilink('smite-s-mighty-hammer', 'Smite&#39;s Mighty Hammer', 'rare')} / {ilink('staff-of-westfall', 'Staff of Westfall', 'rare')}",
        "stats": "Hammer: +11 Str, +4 Agi (+26 Cat AP) | Staff: +11 Sta, +5 Spi",
        "src": f"{dlink('the-deadmines', 'The Deadmines')} (Mr. Smite drop / {qlink('214', 'The Defias Brotherhood')})—optional if running DM once.",
        "span": "Lvls 18–24",
    },
    {
        "id": "wpn_orc",
        "min": 20,
        "max": 23,
        "lvl": "20–23",
        "name_plain": "Orc Crusher / Bronze Warhammer (AH)",
        "name": f"{ilink('orc-crusher', 'Orc Crusher', 'uncommon')} / {ilink('bronze-warhammer', 'Bronze Warhammer (AH BoE)', 'uncommon')}",
        "stats": "Orc Crusher: +8 Str, +4 Sta (+16 AP) | Bronze Warhammer: +6 Str, +6 Sta (+12 AP, +60 HP)",
        "src": f"Quest: {qlink('19', 'Tharil&#39;zun (Q19)')} / {qlink('90', 'Seasoned Wolf Kabobs')} — OR buy {ilink('bronze-warhammer', 'Bronze Warhammer', 'uncommon')} cheap on AH (Blacksmithing dump).",
        "span": "Lvls 20–24",
    },
    {
        "id": "wpn_heave",
        "min": 24,
        "max": 35,
        "lvl": "24 (HUGE)",
        "name_plain": "Heavehammer / Slaghammer (AH)",
        "name": f"⭐ {ilink('heavehammer', 'Heavehammer (Quest Rare)', 'rare')} / {ilink('slaghammer', 'Slaghammer (AH BoE)', 'rare')}",
        "stats": "Heavehammer: +32 AP, +60 Armor (+168 Bear Armor!) | Slaghammer: +11 Str, +10 Sta (+22 AP)",
        "src": (
            f"Wetlands: Loot {ilink('titan-relic', 'Titan Relic', 'quest')} &rarr; {qlink('95810', 'Lost Relic Carry (Q95810)')} "
            f"<span class='coord'>38.8, 52.3</span> &rarr; {qlink('98824', 'Prehistoric Prism (Q98824)')} (or buy {ilink('slaghammer', 'Slaghammer', 'rare')} on AH)."
        ),
        "span": "BiS for 14+ Levels (24–38)!",
    },
    {
        "id": "wpn_mavoris",
        "min": 26,
        "max": 35,
        "lvl": "28–32 (Backup / AH)",
        "name_plain": "Mavoris's Warstaff / Golden Iron Destroyer (AH) / Big Stick (AH)",
        "name": f"{ilink('mavoris-s-warstaff', 'Mavoris&#39;s Warstaff', 'uncommon')} / {ilink('golden-iron-destroyer', 'Golden Iron Destroyer (L29 AH)', 'uncommon')} / {ilink('big-stick', 'Big Stick (L32 AH)', 'uncommon')}",
        "stats": "Warstaff/Destroyer: +11 Str (+22 AP) | Big Stick (L32 BoE): +15 Str (+30 AP!)",
        "src": f"Ashenvale {qlink('1012', 'Insane Druids (Q1012)')} <span class='coord'>75.3, 74.2</span> — OR buy {ilink('golden-iron-destroyer', 'Golden Iron Destroyer', 'uncommon')} / {ilink('big-stick', 'Big Stick', 'uncommon')} on AH.",
        "span": "Lvls 28–38 (if no Heavehammer)",
    },
    {
        "id": "wpn_rock",
        "min": 36,
        "max": 47,
        "lvl": "38 (HUGE)",
        "name_plain": "Rock Pulverizer / Mithril Warhammer (AH)",
        "name": f"⭐ {ilink('rock-pulverizer', 'Rock Pulverizer (Quest)', 'uncommon')} / ⭐ {ilink('mithril-warhammer', 'Mithril Warhammer (AH BoE)', 'uncommon')}",
        "stats": "Rock Pulverizer: +34 AP | Mithril Warhammer (Forever BS BoE): +9 Str, +14 Agi (+32 AP &amp; +0.7% Crit/Dodge!)",
        "src": f"Badlands {qlink('739', 'Murdaloc (Q739)')} <span class='coord'>50.9, 62.4</span> — OR buy custom Forever BS craft {ilink('mithril-warhammer', 'Mithril Warhammer', 'uncommon')} on AH!",
        "span": "BiS for 12 Levels (38–50)",
    },
    {
        "id": "wpn_feral",
        "min": 48,
        "max": 57,
        "lvl": "49–50 (HUGE)",
        "name_plain": "Feral Staff / Inlaid Thorium Hammer (L49 AH)",
        "name": f"⭐ {ilink('feral-staff', 'Feral Staff (L50 Class Staff)', 'rare')} / {ilink('inlaid-thorium-hammer', 'Inlaid Thorium Hammer (L49 AH)', 'uncommon')}",
        "stats": "Feral Staff: +17 Str, +16 Agi, +110 Armor (+50 Cat AP, +506 Bear Armor!) | Thorium Hammer: +23 Str (+46 AP)",
        "src": f"L50 Druid Class Chain: {qlink('9052', 'Blood of Morphaz')} (or bridge at L49 with {ilink('inlaid-thorium-hammer', 'Inlaid Thorium Hammer', 'uncommon')} from AH).",
        "span": "BiS from 50 to 60 Pre-Raid",
    },
    {
        "id": "wpn_60",
        "min": 55,
        "max": 60,
        "lvl": "55–60",
        "name_plain": "The Unstoppable Force",
        "name": f"{ilink('the-unstoppable-force', 'The Unstoppable Force (Epic 2H)', 'epic')}",
        "stats": "+18 Str, +17 Sta, +2% Crit (+28 Crit Rating)",
        "src": f"Alterac Valley Exalted or Dire Maul {qlink('5518', 'The Gordok Ogre Suit')}.",
        "span": "Level 60 Endgame",
    },
]

CRAFT_BIS: List[Dict[str, Any]] = [
    {
        "id": "cr_fine_tunic",
        "rl": 12,
        "lw": 40,
        "name_plain": "Fine Leather Tunic",
        "name": f"{ilink('fine-leather-tunic', 'Fine Leather Tunic (Chest)', 'uncommon')}",
        "stats": "+4 Agi, +3 Sta",
        "mats": "6x Light Leather, 3x Cured Light Hide (Trainer)",
    },
    {
        "id": "cr_force_med",
        "rl": 15,
        "lw": 80,
        "name_plain": "Forceful Medium Armor Kit (x4)",
        "name": f"⭐ {ilink('forceful-medium-armor-kit', 'Forceful Medium Armor Kit (x4)', 'uncommon')}",
        "stats": "+4 Attack Power & +16 Armor per slot (+16 AP total on Chest/Legs/Hands/Feet!)",
        "mats": f"1x Med Armor Kit, 2x Strange Dust, 2x Elixir of Minor Str ({ilink('pattern-forceful-medium-armor-kit', 'Pattern 252784 (BoE / AH)', 'uncommon')})",
    },
    {
        "id": "cr_brawler_17",
        "rl": 17,
        "lw": 85,
        "name_plain": "Brawler's Leather Boots",
        "name": f"⭐ {ilink('brawler-s-leather-boots', 'Brawler&#39;s Leather Boots (Rare Feet)', 'rare')}",
        "stats": "61 Armor, +5 Str, +5 Agi, +4 Sta (+15 Cat AP!)",
        "mats": f"14x Light Leather, 4x Cured Light Hide, 3x Pristine Leather, 3x Shadowgem ({ilink('pattern-brawler-s-leather-boots', 'Pattern 252786: #1 Favor Buy!', 'rare')})",
    },
    {
        "id": "cr_dark_pants",
        "rl": 18,
        "lw": 90,
        "name_plain": "Dark Leather Pants & Deviate Scale Belt",
        "name": f"{ilink('dark-leather-pants', 'Dark Leather Pants', 'uncommon')} &amp; {ilink('deviate-scale-belt', 'Deviate Scale Belt', 'rare')}",
        "stats": "Pants: +8 Agi | Belt (Rare): +5 Agi, +3 Str, +6 Sta",
        "mats": f"Pants: 12x Med Leather, 1x Gray Dye (Trainer) | Belt: {ilink('pattern-deviate-scale-belt', 'Pattern: Deviate Scale Belt', 'uncommon')}",
    },
    {
        "id": "cr_brawler_20",
        "rl": 20,
        "lw": 100,
        "name_plain": "Brawler's Leather Hood & Fletcher's Gloves",
        "name": f"⭐ {ilink('brawler-s-leather-hood', 'Brawler&#39;s Leather Hood (Rare)', 'rare')} &amp; {ilink('fletcher-s-gloves', 'Fletcher&#39;s Gloves', 'uncommon')}",
        "stats": "Hood: 76 Armor, +8 Agi, +10 Sta (+100 HP!) | Gloves: +1% Crit",
        "mats": f"Hood: 8x Med Leather, 4x Pristine Leather, 4x Shadowgem ({ilink('pattern-brawler-s-leather-hood', 'Pattern 252798: #2 Favor Buy!', 'rare')})",
    },
    {
        "id": "cr_toughened_22",
        "rl": 22,
        "lw": 110,
        "name_plain": "Toughened Leather Gloves",
        "name": f"⭐ {ilink('toughened-leather-gloves', 'Toughened Leather Gloves (Rare)', 'rare')}",
        "stats": "+6 Str, +6 Agi, +3 Sta (+18 Cat AP)",
        "mats": "4x Med Leather, 2x Cured Med Hide, 2x Elixir of Lesser Def, 2x Spider's Silk (Trainer)",
    },
    {
        "id": "cr_dark_shld",
        "rl": 23,
        "lw": 115,
        "name_plain": "Dark Leather Shoulders",
        "name": f"⭐ {ilink('dark-leather-shoulders', 'Dark Leather Shoulders (Shoulder)', 'uncommon')}",
        "stats": "+7 Agi (Huge—Shoulder slot is otherwise empty until L27+!)",
        "mats": f"12x Med Leather, 1x Elixir of Lesser Agi, 1x Gray Dye ({ilink('pattern-dark-leather-shoulders', 'Pattern 4294', 'uncommon')})",
    },
    {
        "id": "cr_earthen_24",
        "rl": 24,
        "lw": 120,
        "name_plain": "Heavy Earthen Gloves",
        "name": f"{ilink('heavy-earthen-gloves', 'Heavy Earthen Gloves (Hands)', 'uncommon')}",
        "stats": "+16 Attack Power",
        "mats": "12x Med Leather, 2x Elemental Earth, 2x Bolt of Woolen Cloth (Trainer)",
    },
    {
        "id": "cr_barb_legs",
        "rl": 29,
        "lw": 145,
        "name_plain": "Barbaric Leggings",
        "name": f"⭐ {ilink('barbaric-leggings', 'Barbaric Leggings (Legs)', 'uncommon')}",
        "stats": "+7 Str, +7 Agi, +7 Sta (+21 Cat AP!)",
        "mats": "10x Heavy Leather, 1x Moss Agate, 2x Fine Thread (Cheap & lasts 10 levels!)",
    },
    {
        "id": "cr_force_hvy",
        "rl": 30,
        "lw": 135,
        "name_plain": "Forceful Heavy Armor Kit (x4)",
        "name": f"⭐ {ilink('forceful-heavy-armor-kit', 'Forceful Heavy Armor Kit (x4)', 'uncommon')}",
        "stats": "Adds Attack Power & Armor to Chest, Legs, Hands & Feet",
        "mats": f"1x Heavy Armor Kit, 2x Soul Dust, 2x Elixir of Giant Growth ({ilink('pattern-forceful-heavy-armor-kit', 'Pattern 252812 (BoE)', 'uncommon')})",
    },
    {
        "id": "cr_barb_33",
        "rl": 33,
        "lw": 165,
        "name_plain": "Barbaric Harness & Barbaric Belt",
        "name": f"⭐ {ilink('barbaric-harness', 'Barbaric Harness (L33)', 'uncommon')} &amp; {ilink('barbaric-belt', 'Barbaric Belt (L35)', 'uncommon')}",
        "stats": "Harness: +7 Str, +8 Agi, +8 Sta | Belt: +11 Str + On-Use +30 Rage!",
        "mats": "14x Heavy Leather, 1x Iron Buckle (Trainer)",
    },
    {
        "id": "cr_nightscape",
        "rl": 36,
        "lw": 180,
        "name_plain": "Nightscape Tunic, Headband & Pants",
        "name": f"⭐ {ilink('nightscape-tunic', 'Nightscape Tunic', 'uncommon')} / {ilink('nightscape-headband', 'Headband (L36)', 'uncommon')} / {ilink('nightscape-pants', 'Pants (L41)', 'uncommon')}",
        "stats": "Tunic: +15 Agi, +6 Sta | Head: +12 Agi, +11 Sta | Pants: +16 Agi, +7 Sta",
        "mats": "5–14x Thick Leather, Silken Thread (Expert LW Trainer Telonis)",
    },
    {
        "id": "cr_wolfshead",
        "rl": 40,
        "lw": 225,
        "name_plain": "Wolfshead Helm",
        "name": f"⭐ {ilink('wolfshead-helm', 'Wolfshead Helm (Rare Head)', 'rare')} + {ilink('forceful-thick-armor-kit', 'Forceful Thick Kits', 'uncommon')}",
        "stats": "+10 Spi + Gain +5 Rage on Enrage & +5 Energy on Shifting Power",
        "mats": "18x Thick Leather, 2x Thick Wolfhide, 8x Wicked Claw (Tribal LW Trainer Caryssia Moonhunter)",
    },
    {
        "id": "cr_warbear",
        "rl": 50,
        "lw": 270,
        "name_plain": "Warbear Harness & Warbear Woolies",
        "name": f"⭐ {ilink('warbear-harness', 'Warbear Harness (L50)', 'rare')} &amp; {ilink('warbear-woolies', 'Warbear Woolies (L52)', 'rare')}",
        "stats": "Woolies: +28 Str, +18 Agi, +12 Sta (+74 Cat AP!)",
        "mats": "24–28x Rugged Leather, 12–14x Warbear Leather (Timbermaw Hold Friendly)",
    },
    {
        "id": "cr_devilsaur",
        "rl": 53,
        "lw": 265,
        "name_plain": "Devilsaur Gauntlets & Leggings",
        "name": f"⭐ {ilink('devilsaur-gauntlets', 'Devilsaur Gauntlets (L53)', 'rare')} &amp; {ilink('devilsaur-leggings', 'Devilsaur Leggings (L55)', 'rare')}",
        "stats": "+74 AP, +2% Crit, +21 Sta, +2% Hit (2pc Set Bonus)",
        "mats": "60x Rugged Leather, 22x Devilsaur Leather, 1x Cured Rugged Hide (Tribal LW)",
    },
]

LW_BRACKETS: List[Dict[str, Any]] = [
    {
        "min": 1,
        "max": 50,
        "recipe_plain": "Light Armor Kit + Camp Tent",
        "recipe": f"{ilink('light-armor-kit', 'Light Armor Kit', 'uncommon')} + {ilink('camp-tent', 'Camp Tent (at LW 20)', 'uncommon')}",
        "mats": f"1x {ilink('2318', 'Light Leather', 'uncommon')} (~64 crafts); 5x Light Leather for Tent",
        "notes": "Train Journeyman LW (75–150) at LW 50!",
    },
    {
        "min": 51,
        "max": 74,
        "recipe_plain": "Embossed Leather Gloves",
        "recipe": f"{ilink('embossed-leather-gloves', 'Embossed Leather Gloves (taught at 40)', 'uncommon')}",
        "mats": "3x Light Leather, 2x Coarse Thread (~25 crafts)",
        "notes": f"Also craft {ilink('fine-leather-tunic', 'Fine Leather Tunic (+4 Agi, +3 Sta)', 'uncommon')}.",
    },
    {
        "min": 75,
        "max": 101,
        "recipe_plain": "Fine Leather Belt",
        "recipe": f"{ilink('fine-leather-belt', 'Fine Leather Belt (taught at 55)', 'uncommon')}",
        "mats": "6x Light Leather, 2x Coarse Thread (~35 crafts to 102)",
        "notes": f"At LW 85, craft {ilink('brawler-s-leather-boots', 'Brawler&#39;s Leather Boots (Rare)', 'rare')}!",
    },
    {
        "min": 102,
        "max": 124,
        "recipe_plain": "Dark Leather Cloak / Nimble Gloves",
        "recipe": f"{ilink('dark-leather-cloak', 'Dark Leather Cloak (85)', 'uncommon')} OR {ilink('nimble-leather-gloves', 'Nimble Leather Gloves (95)', 'uncommon')}",
        "mats": f"8x {ilink('2319', 'Medium Leather', 'uncommon')}, 1x Gray Dye (~28 crafts)",
        "notes": f"Craft {ilink('brawler-s-leather-hood', 'Brawler&#39;s Hood (100)', 'rare')} &amp; {ilink('dark-leather-shoulders', 'Dark Leather Shoulders (115)', 'uncommon')}. Train Expert LW at Telonis (Darnassus) at 125!",
    },
    {
        "min": 125,
        "max": 154,
        "recipe_plain": "Heavy Armor Kit",
        "recipe": f"{ilink('heavy-armor-kit', 'Heavy Armor Kit (taught at 125)', 'uncommon')}",
        "mats": f"5x {ilink('4234', 'Heavy Leather', 'uncommon')}, 1x Fine Thread (~34 crafts)",
        "notes": f"Get {ilink('blueprint-tanning-rack', 'Blueprint: Tanning Rack (140)', 'uncommon')}. Craft {ilink('barbaric-leggings', 'Barbaric Leggings (145)', 'uncommon')}!",
    },
    {
        "min": 155,
        "max": 176,
        "recipe_plain": "Thick Leather",
        "recipe": f"{ilink('4304', 'Thick Leather (taught at 155 by Telonis)', 'uncommon')}",
        "mats": "6x Heavy Leather -> 1x Thick Leather (~23 crafts)",
        "notes": "Save all 23 Thick Leather for 177–204.",
    },
    {
        "min": 177,
        "max": 204,
        "recipe_plain": "Thick Armor Kit + Nightscape",
        "recipe": f"{ilink('thick-armor-kit', 'Thick Armor Kit (175)', 'uncommon')} + {ilink('nightscape-tunic', 'Nightscape Tunic (180)', 'uncommon')}",
        "mats": "5x Thick Leather, 1x Silken Thread (~32 crafts)",
        "notes": "Train Artisan LW at Drakk Stonehand (Aerie Peak, Hinterlands) at LW 200!",
    },
    {
        "min": 205,
        "max": 224,
        "recipe_plain": "Rugged Leather",
        "recipe": f"{ilink('8170', 'Rugged Leather (taught at 205 by Drakk)', 'uncommon')}",
        "mats": "6x Thick Leather -> 1x Rugged Leather (20 crafts)",
        "notes": "100% orange to 225. Save all 20 Rugged Leather.",
    },
    {
        "min": 225,
        "max": 238,
        "recipe_plain": "Rugged Armor Kit",
        "recipe": f"{ilink('rugged-armor-kit', 'Rugged Armor Kit (Drakk Stonehand)', 'uncommon')}",
        "mats": "5x Rugged Leather (~23 crafts)",
        "notes": f"At LW 235 (L40+), unlock Tribal LW in Feralas &amp; craft {ilink('wolfshead-helm', 'Wolfshead Helm', 'rare')}!",
    },
    {
        "min": 239,
        "max": 268,
        "recipe_plain": "Wicked Leather Gauntlets",
        "recipe": f"{ilink('wicked-leather-gauntlets', 'Wicked Leather Gauntlets', 'uncommon')} ({ilink('15725', 'Pattern: Chillwind WPL', 'uncommon')})",
        "mats": "8x Rugged Leather, 1x Black Dye (~39 crafts)",
        "notes": f"Craft {ilink('devilsaur-gauntlets', 'Devilsaur Gauntlets', 'rare')} at LW 265!",
    },
    {
        "min": 269,
        "max": 300,
        "recipe_plain": "Runic Leather Headband",
        "recipe": f"{ilink('runic-leather-headband', 'Runic Leather Headband', 'uncommon')} ({ilink('15756', 'Pattern: Light&#39;s Hope EPL', 'uncommon')})",
        "mats": "14x Rugged Leather, 10x Runecloth (~43 crafts)",
        "notes": f"Craft {ilink('devilsaur-leggings', 'Devilsaur Leggings', 'rare')} at LW 290 to complete 2/2 Devilsaur Set!",
    },
]


def load_saved_disk_state() -> Dict[str, Any]:
    if STATE_JSON_PATH.exists():
        try:
            return json.loads(STATE_JSON_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"char_level": 17, "skin_skill": 75, "lw_skill": 55, "ms_aca_label": True}


def save_disk_state(state: Dict[str, Any]) -> None:
    STATE_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_JSON_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

    lvl = state.get("char_level", 17)
    skin = state.get("skin_skill", 75)
    lw = state.get("lw_skill", 55)
    checked = [k for k, v in state.items() if isinstance(v, bool) and v]
    snapshot_block = (
        f"<!-- LIVE_DASHBOARD_STATE_START -->\n"
        f"## Live Dashboard Auto-Saved State (Updated {time.strftime('%Y-%m-%d %H:%M:%S')})\n"
        f"- **Current Level:** {lvl}\n"
        f"- **Skinning Skill:** {skin}/300\n"
        f"- **Leatherworking Skill:** {lw}/300\n"
        f"- **Completed Checkboxes:** {', '.join(checked) if checked else 'none yet'}\n"
        f"<!-- LIVE_DASHBOARD_STATE_END -->"
    )
    if PROFILE_MD_PATH.exists():
        content = PROFILE_MD_PATH.read_text(encoding="utf-8")
        if "<!-- LIVE_DASHBOARD_STATE_START -->" in content and "<!-- LIVE_DASHBOARD_STATE_END -->" in content:
            before = content.split("<!-- LIVE_DASHBOARD_STATE_START -->")[0]
            after = content.split("<!-- LIVE_DASHBOARD_STATE_END -->")[1]
            PROFILE_MD_PATH.write_text(before + snapshot_block + after, encoding="utf-8")
        else:
            PROFILE_MD_PATH.write_text(content.rstrip() + "\n\n" + snapshot_block + "\n", encoding="utf-8")


def build_dashboard_body(build_id: str, initial_state: Dict[str, Any]) -> str:
    lvl = int(initial_state.get("char_level", 17))
    skin = int(initial_state.get("skin_skill", 75))
    lw = int(initial_state.get("lw_skill", 55))

    zones_rows = []
    for leg in ZONE_LEGS:
        done = bool(initial_state.get(leg["id"]))
        active = not done and leg["min"] <= lvl <= leg["max"]
        cls = "done-row" if done else ("active-row" if active else "")
        lvl_str = str(leg["min"]) if leg["min"] == leg["max"] else f"{leg['min']}–{leg['max']}"
        chk = "checked" if done else ""
        zones_rows.append(
            f'<tr class="{cls}" id="row_{leg["id"]}">'
            f'<td><input type="checkbox" id="{leg["id"]}" {chk} onchange="toggleCheck(\'{leg["id"]}\')"></td>'
            f"<td><strong>{lvl_str}</strong></td>"
            f"<td><strong>{leg['name']}</strong></td>"
            f"<td>{leg['beasts']}</td>"
            f"<td>{leg['notes']}</td>"
            f"</tr>"
        )

    wpn_rows = []
    for w in WEAPON_PROGRESSION:
        done = bool(initial_state.get(w["id"]))
        active = not done and w["min"] <= lvl <= w["max"]
        cls = "done-row" if (done or lvl > w["max"]) else ("active-row" if active else "")
        chk = "checked" if done else ""
        wpn_rows.append(
            f'<tr class="{cls}" id="row_{w["id"]}">'
            f'<td><input type="checkbox" id="{w["id"]}" {chk} onchange="toggleCheck(\'{w["id"]}\')"></td>'
            f"<td><strong>{w['lvl']}</strong></td>"
            f"<td><strong>{w['name']}</strong></td>"
            f"<td>{w['stats']}</td>"
            f"<td>{w['src']}</td>"
            f"<td>{w['span']}</td>"
            f"</tr>"
        )

    craft_rows = []
    for c in CRAFT_BIS:
        done = bool(initial_state.get(c["id"]))
        active = not done and ((c["rl"] - 2 <= lvl <= c["rl"] + 5) or (c["lw"] - 15 <= lw <= c["lw"] + 25 and lvl >= c["rl"] - 3))
        cls = "done-row" if (done or lvl > c["rl"] + 9) else ("active-row" if active else "")
        chk = "checked" if done else ""
        craft_rows.append(
            f'<tr class="{cls}" id="row_{c["id"]}">'
            f'<td><input type="checkbox" id="{c["id"]}" {chk} onchange="toggleCheck(\'{c["id"]}\')"></td>'
            f"<td><strong>Lvl {c['rl']}</strong></td>"
            f"<td><strong>LW {c['lw']}</strong></td>"
            f"<td><strong>{c['name']}</strong></td>"
            f"<td>{c['stats']}</td>"
            f"<td>{c['mats']}</td>"
            f"</tr>"
        )

    lw_rows = []
    for i, b in enumerate(LW_BRACKETS):
        active = b["min"] <= lw <= b["max"]
        cls = "done-row" if lw > b["max"] else ("active-row" if active else "")
        lw_rows.append(
            f'<tr class="{cls}" id="row_lwb_{i}">'
            f"<td><strong>{b['min']}–{b['max']}</strong></td>"
            f"<td><strong>{b['recipe']}</strong></td>"
            f"<td>{b['mats']}</td>"
            f"<td>{b['notes']}</td>"
            f"</tr>"
        )

    data_json = json.dumps(
        {
            "build_id": build_id,
            "zones": ZONE_LEGS,
            "weapons": WEAPON_PROGRESSION,
            "crafts": CRAFT_BIS,
            "lw_brackets": LW_BRACKETS,
            "initial_state": initial_state,
            "sync_port": SYNC_PORT,
        }
    )

    return f"""
<style>
  .hero-banner {{
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.14), rgba(52, 211, 153, 0.10));
    border: 2px solid var(--accent);
    border-radius: var(--radius);
    padding: 1.25rem 1.4rem;
    margin-bottom: 1.25rem;
  }}
  .hero-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.3rem;
  }}
  .hero-kicker {{
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent);
  }}
  .sync-pill {{
    font-size: 0.78rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    background: rgba(52, 211, 153, 0.16);
    color: var(--success);
    border: 1px solid rgba(52, 211, 153, 0.35);
  }}
  .hero-headline {{
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.35rem;
  }}
  .hero-sub {{
    font-size: 0.92rem;
    color: var(--text);
    margin-bottom: 0.5rem;
  }}
  .alerts-stack {{
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    margin-top: 0.6rem;
  }}
  .alert-pill {{
    padding: 0.5rem 0.8rem;
    border-radius: 6px;
    font-size: 0.88rem;
    font-weight: 500;
    border-left: 4px solid var(--warning);
    background: rgba(251, 191, 36, 0.12);
  }}
  .alert-pill.danger {{
    border-left-color: var(--danger);
    background: rgba(248, 113, 113, 0.14);
  }}
  .alert-pill.success {{
    border-left-color: var(--success);
    background: rgba(52, 211, 153, 0.12);
  }}
  .stepper-row {{
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }}
  .stepper-btn {{
    padding: 0.35rem 0.65rem;
    font-size: 0.84rem;
    border-radius: 6px;
    background: var(--table-stripe);
    color: var(--text);
    border: 1px solid var(--card-border);
    cursor: pointer;
    font-weight: 600;
  }}
  .stepper-btn:hover {{
    background: var(--accent);
    color: #0f172a;
    border-color: var(--accent);
  }}
  .tab-bar {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 1.25rem;
    border-bottom: 2px solid var(--card-border);
    padding-bottom: 0.65rem;
  }}
  .tab-buttons {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }}
  .tab-btn {{
    padding: 0.55rem 1rem;
    border-radius: 8px;
    font-size: 0.92rem;
    font-weight: 600;
    border: 1px solid var(--card-border);
    background: var(--card-bg);
    color: var(--text);
    cursor: pointer;
  }}
  .tab-btn.active {{
    background: var(--accent);
    color: #0f172a;
    border-color: var(--accent);
  }}
  .tab-panel {{
    display: none;
  }}
  .tab-panel.active {{
    display: block;
  }}
  tr.active-row td {{
    background-color: rgba(56, 189, 248, 0.18) !important;
    border-top: 1px solid var(--accent);
    border-bottom: 1px solid var(--accent);
  }}
  tr.done-row td {{
    opacity: 0.42;
  }}
  tr.filtered-out {{
    display: none !important;
  }}
  .timer-box {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    background: var(--table-stripe);
    margin-top: 0.6rem;
  }}
  .timer-readout {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--success);
  }}
  .coord {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.82rem;
    padding: 0.12rem 0.38rem;
    border-radius: 4px;
    background: rgba(56, 189, 248, 0.14);
    color: var(--accent);
    white-space: nowrap;
  }}
  a.wlink {{
    text-decoration: underline;
    text-decoration-thickness: 1px;
    text-underline-offset: 2px;
    font-weight: 600;
  }}
  a.wlink:hover {{
    opacity: 0.85;
  }}
  a.q-rare {{
    color: #60a5fa;
  }}
  a.q-uncommon {{
    color: #34d399;
  }}
  a.q-quest {{
    color: #fbbf24;
  }}
  a.q-epic {{
    color: #c084fc;
  }}
  .lookup-bar {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.7rem 1rem;
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    background: var(--table-stripe);
    margin-top: 0.6rem;
  }}
  .lookup-links {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    font-size: 0.84rem;
  }}
</style>

<!-- 1. DYNAMIC HERO BANNER -->
<div class="hero-banner" id="next-step-banner">
  <div class="hero-top">
    <div class="hero-kicker">🎯 Next Priority &bull; Saftis (Night Elf Feral Druid &bull; Europe PvP)</div>
    <div class="sync-pill" id="sync-status-pill">✓ Auto-Save &amp; Hot-Reload Active</div>
  </div>
  <div class="hero-headline" id="ns-headline">Step 1: Pick Up 'A Lesson to Learn (Q26)' in Darnassus (35.4, 8.4) &rarr; Moonglade Upstairs (56.2, 30.6)</div>
  <div class="hero-sub" id="ns-detail">Starts the Aquatic Form chain for Idol of Shifting Tides (-40 shapeshift mana). Also click Westfall Burned Remains (37.3, 50.6) &amp; Westfall Pendant (17.9, 33.2) before taking the Stormwind Boat (22.7, 56.7) to Darkshore.</div>
  <div class="alerts-stack" id="ns-alerts"></div>
</div>

<!-- 2. COMPACT LIVE CONTROLS + 5 SUMMARY CARDS + WIKI LOOKUP BAR -->
<div class="section" style="padding: 1.1rem 1.35rem; margin-bottom: 1.1rem;">
  <div class="form-grid" style="margin-bottom: 0.65rem;">
    <div class="form-group">
      <label for="char_level">Character Level (16–60)</label>
      <div class="stepper-row">
        <button type="button" class="stepper-btn" onclick="stepVal('char_level', -1, 1, 60)">-1</button>
        <input type="number" id="char_level" value="{lvl}" min="1" max="60" oninput="updateDashboard()">
        <button type="button" class="stepper-btn" onclick="stepVal('char_level', 1, 1, 60)">+1</button>
      </div>
    </div>
    <div class="form-group">
      <label for="skin_skill">Skinning (1–300)</label>
      <div class="stepper-row">
        <button type="button" class="stepper-btn" onclick="stepVal('skin_skill', -5, 1, 300)">-5</button>
        <input type="number" id="skin_skill" value="{skin}" min="1" max="300" oninput="updateDashboard()">
        <button type="button" class="stepper-btn" onclick="stepVal('skin_skill', 1, 1, 300)">+1</button>
        <button type="button" class="stepper-btn" onclick="stepVal('skin_skill', 5, 1, 300)">+5</button>
      </div>
    </div>
    <div class="form-group">
      <label for="lw_skill">Leatherworking (1–300)</label>
      <div class="stepper-row">
        <button type="button" class="stepper-btn" onclick="stepVal('lw_skill', -5, 1, 300)">-5</button>
        <input type="number" id="lw_skill" value="{lw}" min="1" max="300" oninput="updateDashboard()">
        <button type="button" class="stepper-btn" onclick="stepVal('lw_skill', 1, 1, 300)">+1</button>
        <button type="button" class="stepper-btn" onclick="stepVal('lw_skill', 5, 1, 300)">+5</button>
      </div>
    </div>
  </div>

  <div class="cards-grid" style="margin-bottom: 0.6rem;">
    <div class="card">
      <div class="card-title">Current Zone</div>
      <div class="card-value" id="card-zone" style="font-size:1.15rem;">03-Darkshore (Safe)</div>
      <p id="card-zone-sub" style="margin-top:0.25rem;font-size:0.82rem;color:var(--text-muted);">Thistle Bears (13–17), Moonstalkers (14–20)</p>
    </div>
    <div class="card">
      <div class="card-title">LW Skill-Up Craft</div>
      <div class="card-value" id="card-lw" style="font-size:1.15rem;">Embossed Leather Gloves</div>
      <p id="card-lw-sub" style="margin-top:0.25rem;font-size:0.82rem;color:var(--text-muted);">LW 51–74: 3x Light Leather (~25 crafts)</p>
    </div>
    <div class="card">
      <div class="card-title">Craft ASAP Gear Upgrade</div>
      <div class="card-value" id="card-bis-craft" style="font-size:1.15rem;">Brawler's Leather Boots</div>
      <p id="card-bis-craft-sub" style="margin-top:0.25rem;font-size:0.82rem;color:var(--text-muted);">Req L17 / LW 85: +5 Str, +5 Agi, +4 Sta</p>
    </div>
    <div class="card">
      <div class="card-title">Target Weapon &amp; Idol</div>
      <div class="card-value" id="card-weapon" style="font-size:1.15rem;">Idol of Shifting Tides</div>
      <p id="card-weapon-sub" style="margin-top:0.25rem;font-size:0.82rem;color:var(--text-muted);">-40 Shift Mana (Darnassus &rarr; Moonglade &rarr; Darkshore)</p>
    </div>
    <div class="card">
      <div class="card-title">Talent &amp; Skinning Cap</div>
      <div class="card-value" id="card-talent" style="font-size:1.15rem;">1/3 Feral Instinct</div>
      <p id="card-skin-sub" style="margin-top:0.25rem;font-size:0.82rem;color:var(--text-muted);">Skinning {skin}: Max Beast Lvl 25</p>
    </div>
  </div>

  <div class="timer-box">
    <div style="font-size:0.88rem;">
      <strong>🏕️ {ilink('camp-tent', 'Camp Tent', 'uncommon')} Cooldown (60m &bull; +5% Rested XP):</strong> Place Basic Campfire + Camp Tent (5x Light Leather) whenever Rested &lt; 5%.
    </div>
    <div style="display:flex;align-items:center;gap:0.6rem;">
      <span class="timer-readout" id="tent-timer">READY</span>
      <button type="button" class="btn" style="padding:0.4rem 0.85rem;font-size:0.85rem;" onclick="startTentTimer()">Start 60m</button>
      <button type="button" class="stepper-btn" onclick="resetTentTimer()">Reset</button>
    </div>
  </div>

  <!-- QUICK DATABASE LOOKUP BAR & REFERENCE LINKS -->
  <div class="lookup-bar">
    <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;flex:1;">
      <strong style="font-size:0.88rem;">🔎 Quick Wiki Lookup:</strong>
      <input type="text" id="wiki-search-input" placeholder="Search any item, quest, pattern, or dungeon..." style="max-width:300px;padding:0.35rem 0.65rem;font-size:0.86rem;" onkeydown="if(event.key==='Enter')openWikiSearch()">
      <button type="button" class="stepper-btn" onclick="openWikiSearch()">Search Azeroth.wiki &#8599;</button>
    </div>
    <div class="lookup-links">
      <a class="wlink q-rare" href="https://azeroth.wiki/forever/professions/leatherworking" target="_blank" rel="noopener">📚 LW Recipes DB</a>
      <a class="wlink q-uncommon" href="https://azeroth.wiki/forever/professions/skinning" target="_blank" rel="noopener">🔪 Skinning DB</a>
      <a class="wlink q-quest" href="https://azeroth.wiki/forever/quests" target="_blank" rel="noopener">📜 Quests DB</a>
      <a class="wlink q-rare" href="https://azeroth.wiki/forever/dungeons" target="_blank" rel="noopener">🏰 Dungeons DB</a>
      <a class="wlink q-epic" href="https://github.com/fitzforge/polestar/tree/main/guides/forever" target="_blank" rel="noopener">🧭 Polestar Guides</a>
    </div>
  </div>
</div>

<!-- 3. TABBED NAVIGATION + FOCUS FILTER -->
<div class="tab-bar">
  <div class="tab-buttons">
    <button type="button" class="tab-btn active" onclick="switchTab('tab-route', this)">🗺️ 1. Route &amp; Priority Quests</button>
    <button type="button" class="tab-btn" onclick="switchTab('tab-gear', this)">⚔️ 2. Must-Get Weapons, Craftables &amp; Items</button>
    <button type="button" class="tab-btn" onclick="switchTab('tab-lw', this)">🔨 3. LW 1&rarr;300 &amp; Waylaid Crates</button>
    <button type="button" class="tab-btn" onclick="switchTab('tab-checks', this)">✅ 4. Checklists, Coordinates &amp; Sync</button>
  </div>
  <label style="display:flex;align-items:center;gap:0.4rem;font-size:0.86rem;cursor:pointer;">
    <input type="checkbox" id="focus_filter" onchange="updateDashboard()">
    <span>🔍 Focus Mode (Hide completed / far-future rows)</span>
  </label>
</div>

<!-- TAB 1: ROUTE & PRIORITY QUESTS -->
<div class="tab-panel active" id="tab-route">
  <div class="section">
    <h2 class="section-title">Simplified 16 &rarr; 60 Alliance Speedroute &amp; Beast Skinning Loops (Click Any Quest/Item to Open Wiki)</h2>
    <table id="zones-table">
      <thead>
        <tr>
          <th>Done</th>
          <th>Lvls</th>
          <th>Zone &amp; Hub</th>
          <th>Skinnable Beasts (Leather)</th>
          <th>Must-Do Quests &amp; Unlocks (Clickable Links)</th>
        </tr>
      </thead>
      <tbody id="zones-tbody">
        {"".join(zones_rows)}
      </tbody>
    </table>
  </div>
</div>

<!-- TAB 2: MUST-GET WEAPONS, CRAFTABLES & KEY ITEMS -->
<div class="tab-panel" id="tab-gear">
  <div class="section">
    <h2 class="section-title">1. Feral Weapon Rule, Chance-on-Hit Procs &amp; Best Weapons (16 &rarr; 60)</h2>
    <div class="alert-pill danger" style="margin-bottom:0.85rem;">
      <strong>⚠️ Critical Feral Weapon &amp; Proc Rules (Verified in Forever 1.60.1):</strong><br>
      1. <strong>Weapon DPS &amp; Speed Do Not Apply in Form:</strong> Bear Form (fixed <code>2.5s</code> speed) and Cat Form (fixed <code>1.0s</code> speed) replace your weapon with virtual animal paws (<code>0.85 &times; Level + AP/14</code>). Abilities like <em>Claw (110% normal damage)</em> and <em>Shred (155% damage)</em> scale off your <strong>paw damage</strong>, not weapon damage.<br>
      2. <strong>Weapon &ldquo;Chance on Hit&rdquo; Procs Do NOT Trigger in Bear/Cat Form:</strong> Weapon procs (like the Fire proc on {ilink('ironforge-greathammer', 'Ironforge Greathammer', 'rare')} from {qlink('96393', 'Old Ironforge Incursion')} in {dlink('hall-of-thanes', 'The Hall of Thanes')}, {ilink('5815', 'Glacial Stone', 'rare')}, or <em>Fiery Weapon</em>) require physical weapon swings and <strong>never proc on Bear/Cat paw attacks</strong>. Because {ilink('ironforge-greathammer', 'Ironforge Greathammer', 'rare')} has 0 Str/Agi/Sta, it gives <strong>+0 stats in Bear/Cat Form</strong>!<br>
      3. <strong>What DOES Work in Form:</strong> Equipped attributes (<strong>Strength = +2 AP, Agility = +1 AP &amp; Crit/Dodge, raw Attack Power, Crit, Hit, Haste, Armor, Stamina</strong>), Weapon <strong>On-Use buffs</strong> ({ilink('manual-crowd-pummeler', 'Manual Crowd Pummeler', 'rare')}), and <strong>Armor/Trinket procs</strong>.
    </div>
    <table id="weapons-table">
      <thead>
        <tr>
          <th>Got</th>
          <th>Lvl</th>
          <th>Weapon (Click to Inspect)</th>
          <th>Feral Stats (In-Form Value)</th>
          <th>Exact Quest / Source (Clickable Links)</th>
          <th>How Long It Lasts</th>
        </tr>
      </thead>
      <tbody id="weapons-tbody">
        {"".join(wpn_rows)}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2 class="section-title">2. Craft-ASAP Leatherworking Gear (BiS Power Spikes for 5&ndash;10 Levels)</h2>
    <p style="font-size:0.9rem;color:var(--text-muted);margin-bottom:0.85rem;">
      Check off items as you craft them. Click any item or pattern name to open its full <code>azeroth.wiki</code> reagent and stat page.
    </p>
    <table id="craft-bis-table">
      <thead>
        <tr>
          <th>Crafted</th>
          <th>Req Lvl</th>
          <th>LW Skill</th>
          <th>Craftable Item &amp; Slot (Click to Inspect)</th>
          <th>Stats / Effect</th>
          <th>Materials &amp; Pattern Source</th>
        </tr>
      </thead>
      <tbody id="craft-bis-tbody">
        {"".join(craft_rows)}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2 class="section-title">3. Other High-Impact Speed &amp; Power Items (Idols, Bags, Consumables)</h2>
    <table>
      <thead>
        <tr>
          <th>Lvl</th>
          <th>Item &amp; Slot (Click to Inspect)</th>
          <th>Effect</th>
          <th>Where to Get It</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>10</strong></td>
          <td>{ilink('mark-of-urs-endris', 'Mark of Urs&#39;endris', 'uncommon')} (Relic)</td>
          <td><strong>+4% Armor</strong> from all equipped items</td>
          <td>Level 10 Bear Form class quest reward ({qlink('6001', 'Body and Heart')}).</td>
        </tr>
        <tr>
          <td><strong>16</strong></td>
          <td>{ilink('idol-of-shifting-tides', 'Idol of Shifting Tides', 'uncommon')} + {ilink('aquarius-belt', 'Aquarius Belt', 'uncommon')}</td>
          <td><strong>-40 Mana cost</strong> on all shapeshift spells</td>
          <td>{qlink('5061', 'Aquatic Form (Q5061)')} at Mathrengyl Bearwalker <span class="coord">Darnassus 35.4, 8.4</span>.</td>
        </tr>
        <tr>
          <td><strong>16–31</strong></td>
          <td>{ilink('cozy-sleeping-bag', 'Cozy Sleeping Bag', 'rare')} + {ilink('215365', 'Old Toolbox (12-Slot)', 'uncommon')}</td>
          <td><strong>+3% to +9% XP buff</strong> + <strong>12-Slot Bag</strong></td>
          <td>{qlink('79008', 'Q79008')} <span class="coord">Westfall 37.3, 50.6</span> &rarr; {qlink('79192', 'Q79192')} <span class="coord">S. Barrens 46.3, 73.9</span> &rarr; {qlink('79980', 'Q79980')} <span class="coord">Stonetalon 40.8, 52.6</span> &rarr; {qlink('79975', 'Q79975')} <span class="coord">Hillsbrad 87.2, 49.0</span> &rarr; {qlink('79976', 'Q79976')} <span class="coord">Loch Modan 49.4, 13.0</span>.</td>
        </tr>
        <tr>
          <td><strong>Any</strong></td>
          <td>{ilink('camp-tent', 'Camp Tent', 'uncommon')} (LW 20 Consumable)</td>
          <td><strong>+5% Rested XP</strong> over ~30s (60m CD)</td>
          <td>Crafted with <code>5x Light Leather</code> next to a Basic Campfire.</td>
        </tr>
        <tr>
          <td><strong>23</strong></td>
          <td>{ilink('gunnysack-of-the-night-watch', 'Gunnysack of the Night Watch', 'uncommon')} (Bag)</td>
          <td><strong>Free 10-Slot Bag</strong></td>
          <td>Complete {qlink('56', 'The Night Watch (Q56)')} &rarr; {qlink('57', 'Q57')} &rarr; {qlink('58', 'Q58')} in Darkshire, Duskwood.</td>
        </tr>
        <tr>
          <td><strong>28</strong></td>
          <td>{ilink('blueprint-tanning-rack', 'Blueprint: Tanning Rack', 'uncommon')} (LW 140)</td>
          <td>Required nearby to craft 140+ Forever LW gear</td>
          <td>Drops from <em>Razorclaw the Butcher</em> ({dlink('shadowfang-keep', 'Shadowfang Keep')}) or buy on Auction House.</td>
        </tr>
        <tr>
          <td><strong>55</strong></td>
          <td>{ilink('idol-of-the-dream', 'Idol of the Dream', 'rare')} (Relic)</td>
          <td><strong>+2 sec duration</strong> on <em>Rip</em></td>
          <td>Crafted by Enchanters (BoE/Tradeable).</td>
        </tr>
        <tr>
          <td><strong>60</strong></td>
          <td>{ilink('howling-idol', 'Howling Idol', 'rare')} / {ilink('enraged-idol', 'Enraged Idol', 'rare')} / {ilink('idol-of-the-ursine-twins', 'Idol of the Ursine Twins', 'epic')}</td>
          <td><strong>-0.5s Shifting Power CD</strong> / <strong>+10 Rage Enrage</strong> / <strong>Lacerate resets Primal Bite</strong></td>
          <td>Level 60 endgame Relics ({ilink('idol-of-the-ursine-twins', 'Idol of the Ursine Twins', 'epic')} is BoE on AH!).</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2 class="section-title">4. Best Auction House (AH) Buys &mdash; BoE Armor, Patterns, Kits &amp; Consumables (15 &rarr; 60)</h2>
    <p style="font-size:0.9rem;color:var(--text-muted);margin-bottom:0.85rem;">
      Profession levelers and dungeon runners dump these Bind-on-Equip (BoE) items on the Auction House—often near vendor price. Check these before spending Merchant&#39;s Favor or entering a new bracket:
    </p>
    <table>
      <thead>
        <tr>
          <th>Lvl</th>
          <th>Slot / Category</th>
          <th>AH Item / Pattern (Click to Inspect)</th>
          <th>Feral Stats &amp; Value</th>
          <th>Why It&#39;s an AH Bargain</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>15</strong></td>
          <td><strong>Kit / Pattern</strong></td>
          <td>⭐ {ilink('pattern-forceful-medium-armor-kit', 'Pattern: Forceful Medium Armor Kit', 'uncommon')} / {ilink('forceful-medium-armor-kit', 'Forceful Medium Armor Kit (x4)', 'uncommon')}</td>
          <td><strong>+4 AP &amp; +16 Armor per slot</strong> (+16 AP &amp; +64 Armor across Chest/Legs/Hands/Feet!)</td>
          <td>Pattern is <strong>BoE</strong> on the AH—buy with silver to save <strong>30 Merchant&#39;s Favor</strong>!</td>
        </tr>
        <tr>
          <td><strong>18–19</strong></td>
          <td><strong>Waist / Legs / Feet / Back</strong></td>
          <td>{ilink('deviate-scale-belt', 'Deviate Scale Belt', 'rare')} / {ilink('dark-leather-pants', 'Dark Leather Pants', 'uncommon')} / {ilink('feet-of-the-lynx', 'Feet of the Lynx', 'rare')} / {ilink('sentry-cloak', 'Sentry Cloak', 'rare')}</td>
          <td>Belt: <strong>+3 Str, +5 Agi, +6 Sta</strong> | Pants: <strong>+8 Agi</strong> | Lynx: <strong>+3 Str, +8 Agi</strong> | Cloak: <strong>+4 Agi, +5 Sta</strong></td>
          <td>{ilink('dark-leather-pants', 'Dark Leather Pants', 'uncommon')} are mass-dumped by LW levelers for pennies; {ilink('deviate-scale-belt', 'Deviate Scale Belt', 'rare')} &amp; {ilink('sentry-cloak', 'Sentry Cloak', 'rare')} fill weak early slots.</td>
        </tr>
        <tr>
          <td><strong>20–24</strong></td>
          <td><strong>2H Mace (Weapon)</strong></td>
          <td>{ilink('bronze-warhammer', 'Bronze Warhammer (L20)', 'uncommon')} / {ilink('slaghammer', 'Slaghammer (L24 Rare)', 'rare')}</td>
          <td>Bronze: <strong>+6 Str, +6 Sta (+12 AP)</strong> | Slaghammer: <strong>+11 Str, +10 Sta (+22 AP)</strong></td>
          <td>{ilink('bronze-warhammer', 'Bronze Warhammer', 'uncommon')} is a Blacksmithing skill-up dump sold near vendor price until you get {ilink('heavehammer', 'Heavehammer', 'rare')} at L24.</td>
        </tr>
        <tr>
          <td><strong>22–27</strong></td>
          <td><strong>Hands / Shoulder / Wrist</strong></td>
          <td>⭐ {ilink('toughened-leather-gloves', 'Toughened Leather Gloves (L22)', 'rare')} / ⭐ {ilink('forest-tracker-epaulets', 'Forest Tracker Epaulets (L26)', 'rare')} / {ilink('barbaric-bracers', 'Barbaric Bracers (L27)', 'rare')}</td>
          <td>Gloves: <strong>+6 Str, +6 Agi (+18 AP)</strong> | Epaulets: <strong>+5 Str, +11 Agi (+21 AP!)</strong> | Bracers: <strong>+4 Str, +4 Agi, +6 Sta</strong></td>
          <td>Shoulder slot has almost zero quest rewards before L28—{ilink('forest-tracker-epaulets', 'Forest Tracker Epaulets', 'rare')} or {ilink('dark-leather-shoulders', 'Dark Leather Shoulders', 'uncommon')} is a massive spike.</td>
        </tr>
        <tr>
          <td><strong>28–33</strong></td>
          <td><strong>Legs / Chest / Shoulder / Back</strong></td>
          <td>⭐ {ilink('barbaric-leggings', 'Barbaric Leggings (L29)', 'uncommon')} / {ilink('dusky-leather-leggings', 'Dusky Leather Leggings (L28)', 'uncommon')} / {ilink('tigerstrike-mantle', 'Tigerstrike Mantle (L29)', 'rare')} / {ilink('barbaric-shoulders', 'Barbaric Shoulders (L30)', 'uncommon')} / {ilink('barbaric-harness', 'Barbaric Harness (L33)', 'uncommon')}</td>
          <td>Barbaric Legs: <strong>+7 Str, +7 Agi, +7 Sta (+21 AP)</strong> | Dusky Legs: <strong>+13 Agi</strong> | Tigerstrike: <strong>+8 Agi, +7 Sta</strong> | Harness: <strong>+7 Str, +8 Agi, +8 Sta (+22 AP)</strong></td>
          <td>LW levelers mass-craft Dusky &amp; Barbaric sets between 140–175 skill and dump them on the AH below material cost.</td>
        </tr>
        <tr>
          <td><strong>30</strong></td>
          <td><strong>Kit / Pattern</strong></td>
          <td>⭐ {ilink('pattern-forceful-heavy-armor-kit', 'Pattern: Forceful Heavy Armor Kit', 'uncommon')} / {ilink('forceful-heavy-armor-kit', 'Forceful Heavy Armor Kit (x4)', 'uncommon')}</td>
          <td><strong>Upgraded permanent AP + Armor</strong> on Chest, Legs, Hands &amp; Feet (Req Item Lvl 30+)</td>
          <td>Pattern is <strong>BoE</strong> on the AH—buy with silver instead of spending Favor!</td>
        </tr>
        <tr>
          <td><strong>36–41</strong></td>
          <td><strong>Head / Chest / Legs / Hands</strong></td>
          <td>⭐ {ilink('nightscape-tunic', 'Nightscape Tunic (L36)', 'uncommon')} / {ilink('nightscape-headband', 'Nightscape Headband (L36)', 'uncommon')} / {ilink('nightscape-pants', 'Nightscape Pants (L41)', 'uncommon')} / {ilink('gloves-of-holy-might', 'Gloves of Holy Might (L37 Epic)', 'epic')}</td>
          <td>Tunic: <strong>+15 Agi, +6 Sta</strong> | Head: <strong>+12 Agi, +11 Sta</strong> | Pants: <strong>+16 Agi, +7 Sta</strong> | Gloves: <strong>+20 AP, +14 Crit Rating, +30 Undead AP</strong></td>
          <td>Every Leatherworker crafts dozens of Nightscape pieces from 180–235 skill—always dirt-cheap on the AH.</td>
        </tr>
        <tr>
          <td><strong>38</strong></td>
          <td><strong>2H Mace (Weapon)</strong></td>
          <td>⭐ {ilink('mithril-warhammer', 'Mithril Warhammer (Custom Forever BS BoE)', 'uncommon')}</td>
          <td><strong>+9 Str, +14 Agi (+32 Cat AP &amp; +0.7% Crit/Dodge!)</strong></td>
          <td>Custom <em>WoW: Forever</em> Blacksmithing BoE—rivals {ilink('rock-pulverizer', 'Rock Pulverizer', 'uncommon')} without needing to travel to Badlands first!</td>
        </tr>
        <tr>
          <td><strong>40–50</strong></td>
          <td><strong>Head / Kits / 2H Mace</strong></td>
          <td>⭐ {ilink('wolfshead-helm', 'Wolfshead Helm (L40)', 'rare')} / {ilink('forceful-thick-armor-kit', 'Forceful Thick Armor Kit (L40)', 'uncommon')} / {ilink('inlaid-thorium-hammer', 'Inlaid Thorium Hammer (L49)', 'uncommon')} / {ilink('pattern-forceful-rugged-armor-kit', 'Pattern: Forceful Rugged Armor Kit (L50)', 'uncommon')}</td>
          <td>Wolfshead: <strong>+5 Rage on Enrage &amp; +5 Energy on Shifting Power</strong> | Thorium Hammer: <strong>+23 Str (+46 AP!)</strong></td>
          <td>{ilink('wolfshead-helm', 'Wolfshead Helm', 'rare')} and {ilink('forceful-thick-armor-kit', 'Forceful Thick Armor Kit', 'uncommon')} are craftable/buyable on AH; {ilink('pattern-forceful-rugged-armor-kit', 'Pattern: Forceful Rugged Armor Kit', 'uncommon')} is BoE.</td>
        </tr>
        <tr>
          <td><strong>47–56</strong></td>
          <td><strong>Forever &ldquo;Blue Suede&rdquo; &amp; Devilsaur BoEs</strong></td>
          <td>{ilink('blue-suede-shoes', 'Blue Suede Shoes (L47)', 'uncommon')} / {ilink('blue-suede-pants', 'Blue Suede Pants (L51)', 'uncommon')} / {ilink('blue-suede-armor', 'Blue Suede Armor (L53)', 'uncommon')} / {ilink('blue-suede-hat', 'Blue Suede Hat (L56)', 'uncommon')} / ⭐ {ilink('devilsaur-gauntlets', 'Devilsaur Gauntlets (L53)', 'rare')} &amp; {ilink('devilsaur-leggings', 'Leggings (L55)', 'rare')}</td>
          <td>Blue Suede: <strong>+25 to +50 Cat AP per piece!</strong> | Devilsaur 2-pc: <strong>+46 AP, +2% Crit, +2% Hit</strong></td>
          <td>Custom <em>Forever</em> BoE leather set with massive Str + Agi + Sta budgets; fills every slot before Pre-BiS.</td>
        </tr>
        <tr>
          <td><strong>15–50</strong></td>
          <td><strong>Elixirs &amp; Crate Shortcuts</strong></td>
          <td>{ilink('cured-light-hide', 'Cured Light Hide', 'common')} / {ilink('cured-medium-hide', 'Cured Medium Hide', 'common')} / {ilink('elixir-of-minor-strength', 'Elixir of Minor Strength', 'common')} / {ilink('elixir-of-lesser-agility', 'Elixir of Lesser Agility (L18)', 'common')} / {ilink('elixir-of-ogre-strength', 'Elixir of Ogre Strength (L20)', 'common')} / {ilink('elixir-of-agility', 'Elixir of Agility (L27)', 'common')} / {ilink('elixir-of-greater-agility', 'Elixir of Greater Agility (L38)', 'common')}</td>
          <td>Elixirs: <strong>+8 to +25 Str/Agi for 1 hr</strong> | Cured Hides: <strong>2 per Waylaid Fabrics Crate = +10–15 Favor</strong></td>
          <td>Alchemists dump leveling elixirs on the AH for a few silver; 2x {ilink('elixir-of-minor-strength', 'Elixir of Minor Strength', 'common')} is also the reagent for {ilink('forceful-medium-armor-kit', 'Forceful Medium Armor Kit', 'uncommon')}.</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<!-- TAB 3: LW 1-300 & WAYLAID CRATES -->
<div class="tab-panel" id="tab-lw">
  <div class="section">
    <h2 class="section-title">1. Simplified 1 &rarr; 300 Leatherworking Skill-Up Route (Click Any Recipe to Open Wiki)</h2>
    <table id="lw-table">
      <thead>
        <tr>
          <th>Skill</th>
          <th>Cheapest Skill-Up Craft</th>
          <th>Materials Needed</th>
          <th>Trainer / Rank Action</th>
        </tr>
      </thead>
      <tbody id="lw-tbody">
        {"".join(lw_rows)}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2 class="section-title">2. How to Spend Your 60 Merchant's Favor at Level 17 &amp; Get More Cheaply (<span class="coord">Redridge 15.3, 71.5</span>)</h2>
    <table>
      <thead>
        <tr>
          <th>Priority / Method</th>
          <th>Pattern or Crate (Click to Inspect)</th>
          <th>Exact Strategy &amp; Why</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>🥇 #1 Buy First (Lvl 17, LW 85)</strong></td>
          <td>{ilink('pattern-brawler-s-leather-boots', 'Pattern: Brawler&#39;s Leather Boots', 'rare')}<br>&rarr; Crafts {ilink('brawler-s-leather-boots', 'Brawler&#39;s Leather Boots', 'rare')}</td>
          <td><strong>Rare Feet: 61 Armor, +5 Str, +5 Agi, +4 Sta (+15 Cat AP!).</strong> You are Level 17 right now, there are almost zero good Feral quest boots from L17 to L30+, and it crafts with <strong>14x Light Leather + 4x Cured Light Hide + 3x Pristine Leather + 3x Shadowgem</strong> (saving your Medium Leather for LW 102–125!).</td>
        </tr>
        <tr>
          <td><strong>🥈 #2 Buy Second (Lvl 20, LW 100)</strong></td>
          <td>{ilink('pattern-brawler-s-leather-hood', 'Pattern: Brawler&#39;s Leather Hood', 'rare')}<br>&rarr; Crafts {ilink('brawler-s-leather-hood', 'Brawler&#39;s Leather Hood', 'rare')}</td>
          <td><strong>Rare Head: 76 Armor, +8 Agi, +10 Sta (+100 HP!).</strong> Head slot is otherwise completely empty until L28–32! Gives a huge survivability + Agi spike right when you unlock Cat Form at L20.</td>
        </tr>
        <tr>
          <td><strong>🛒 Buy on AH for Silver (0 Favor!)</strong></td>
          <td>{ilink('pattern-forceful-medium-armor-kit', 'Pattern: Forceful Medium Armor Kit (BoE)', 'uncommon')}<br>&rarr; Crafts {ilink('forceful-medium-armor-kit', 'Forceful Medium Armor Kit', 'uncommon')}</td>
          <td>Unlike the BoP <em>Brawler's</em> patterns, <code>Pattern: Forceful Medium Armor Kit</code> (<code>+4 AP &amp; +16 Armor</code> on Chest/Legs/Hands/Feet = <strong>+16 AP total</strong>) and {ilink('pattern-forceful-heavy-armor-kit', 'Pattern: Forceful Heavy Armor Kit', 'uncommon')} are <strong>Not Bound (BoE)</strong>! Check the Auction House first for silver so you save your Merchant's Favor for BoP patterns.</td>
        </tr>
        <tr>
          <td><strong>❌ Skip With Favor</strong></td>
          <td>{ilink('brawler-s-leather-belt', 'Brawler&#39;s Belt (L12)', 'rare')}, {ilink('brawler-s-leather-gloves', 'Gloves (L15)', 'rare')}, {ilink('brawler-s-leather-tunic', 'Tunic (L22)', 'rare')}, {ilink('brawler-s-leather-legguards', 'Legguards (L25)', 'rare')}</td>
          <td><strong>Why skip:</strong> {qlink('5061', 'Aquatic Form')} gives free {ilink('aquarius-belt', 'Aquarius Belt', 'uncommon')} (or craft {ilink('deviate-scale-belt', 'Deviate Scale Belt', 'rare')} at L18); Trainer/World gives {ilink('dark-leather-tunic', 'Dark Leather Tunic (+6 Agi)', 'uncommon')}, {ilink('dark-leather-pants', 'Dark Leather Pants (+8 Agi)', 'uncommon')}, {ilink('fletcher-s-gloves', 'Fletcher&#39;s Gloves (+1% Crit)', 'uncommon')}, and {ilink('barbaric-leggings', 'Barbaric Leggings (+7 Str/+7 Agi/+7 Sta)', 'uncommon')} without needing 6–8x Pristine Leather + 6–8x Shadowgems!</td>
        </tr>
        <tr>
          <td><strong>💰 Cheapest Favor Trick #1 (Skinning/LW Jackpot!)</strong></td>
          <td>{ilink('waylaid-crate-apprentice-fabrics', 'Waylaid Crate: Apprentice Fabrics (248702)', 'uncommon')} &amp; {ilink('waylaid-crate-journeyman-fabrics', 'Journeyman Fabrics (248705)', 'uncommon')}</td>
          <td><strong>Stock with <code>2x Cured Light Hide</code> (Apprentice) or <code>2x Cured Medium Hide</code> (Journeyman)!</strong> While Tailors must pay <code>20x Bolt of Linen</code> or <code>10x Bolt of Silk</code>, Leatherworkers can fill <em>Fabrics</em> crates with just <strong>2 surplus Hides + 10c of Salt</strong> (which also gives LW skill-ups!). Buy cheap empty <em>Fabrics</em> crates on the AH, stuff them with 2 Cured Hides, and turn in to Marcy Baker for <strong>Merchant's Favor + silver profit</strong>!</td>
        </tr>
        <tr>
          <td><strong>💰 Cheapest Favor Trick #2</strong></td>
          <td>{ilink('waylaid-crate-apprentice-textiles', 'Apprentice Textiles (248684)', 'uncommon')}, {ilink('waylaid-crate-journeyman-textiles', 'Journeyman Textiles (248688)', 'uncommon')} &amp; {ilink('waylaid-crate-apprentice-herbs', 'Apprentice Herbs (248682)', 'uncommon')}</td>
          <td>Stock <em>Textiles</em> crates ONLY with surplus <strong>40x Linen Cloth</strong> or <strong>20x Wool Cloth</strong> (put Leather in bank first!). Stock <em>Apprentice Herbs (248682)</em> with cheap <strong>10x Earthroot / 10x Mageroyal / 20x Peacebloom</strong> (~1–2s on AH; Marcy Baker's silver payout refunds the herbs!).</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<!-- TAB 4: CHECKLISTS, COORDINATES & SYNC -->
<div class="tab-panel" id="tab-checks">
  <div class="section">
    <h2 class="section-title">1. Milestone &amp; Trainer Checkboxes</h2>
    <div class="form-grid" id="milestones-grid">
      <label class="choice-label"><input type="checkbox" id="ms_westfall_note" onchange="updateDashboard()"> <span><strong>[L16 Westfall]</strong> Clicked Burned Campfire <span class="coord">37.3, 50.6</span> ({qlink('79008', 'Sleeping Bag #1')})</span></label>
      <label class="choice-label"><input type="checkbox" id="ms_lesson_darn" onchange="updateDashboard()"> <span><strong>[L16 Darnassus]</strong> Took {qlink('26', 'A Lesson to Learn (Q26)')} <span class="coord">35.4, 8.4</span> &amp; {qlink('29', 'Trial of the Lake')}</span></label>
      <label class="choice-label"><input type="checkbox" id="ms_pendant_wf" onchange="updateDashboard()"> <span><strong>[L16 Westfall]</strong> Looted {ilink('15882', 'Westfall Aquatic Pendant', 'quest')} <span class="coord">17.9, 33.2</span></span></label>
      <label class="choice-label"><input type="checkbox" id="ms_pendant_ds" onchange="updateDashboard()"> <span><strong>[L16–19 Darkshore]</strong> Looted {ilink('15883', 'Darkshore Pendant', 'quest')} <span class="coord">48.9, 11.3</span> &rarr; {ilink('idol-of-shifting-tides', 'Idol of Shifting Tides', 'uncommon')}</span></label>
      <label class="choice-label"><input type="checkbox" id="ms_aca_label" onchange="updateDashboard()"> <span><strong>[L16–22 Crate]</strong> Stocked 1st Crate with 40x Linen &amp; turned in {qlink('98247', 'Shipping Label')} <span class="coord">Redridge 15.3, 71.5</span></span></label>
      <label class="choice-label"><input type="checkbox" id="ms_lw_journeyman" onchange="updateDashboard()"> <span><strong>[LW 50+]</strong> Trained <strong>Journeyman LW (75–150)</strong></span></label>
      <label class="choice-label"><input type="checkbox" id="ms_skin_journeyman" onchange="updateDashboard()"> <span><strong>[Skin 50+]</strong> Trained <strong>Journeyman Skinning (75–150)</strong></span></label>
      <label class="choice-label"><input type="checkbox" id="ms_cat_spirit" onchange="updateDashboard()"> <span><strong>[L20 Class]</strong> Completed {qlink('98393', 'The Great Cat Spirit')} &rarr; <strong>Cat Form</strong></span></label>
      <label class="choice-label"><input type="checkbox" id="ms_lw_expert_telonis" onchange="updateDashboard()"> <span><strong>[LW 125 / L20+]</strong> Trained <strong>Expert LW (150–225)</strong> at Telonis (Darnassus)</span></label>
      <label class="choice-label"><input type="checkbox" id="ms_skin_expert" onchange="updateDashboard()"> <span><strong>[Skin 125+]</strong> Trained <strong>Expert Skinning (150–225)</strong></span></label>
      <label class="choice-label"><input type="checkbox" id="ms_heavehammer" onchange="updateDashboard()"> <span><strong>[L24 Wetlands]</strong> Got {ilink('heavehammer', 'Heavehammer (+32 AP, +60 Armor)', 'rare')} from {qlink('98824', 'Prehistoric Prism')}</span></label>
      <label class="choice-label"><input type="checkbox" id="ms_tanning_rack" onchange="updateDashboard()"> <span><strong>[LW 140]</strong> Obtained {ilink('blueprint-tanning-rack', 'Blueprint: Tanning Rack', 'uncommon')}</span></label>
      <label class="choice-label"><input type="checkbox" id="ms_sleeping_bag" onchange="updateDashboard()"> <span><strong>[L26–31]</strong> Finished {ilink('cozy-sleeping-bag', 'Cozy Sleeping Bag (+3–9% XP)', 'rare')}</span></label>
      <label class="choice-label"><input type="checkbox" id="ms_lw_artisan_drakk" onchange="updateDashboard()"> <span><strong>[LW 200 / L35+]</strong> Trained <strong>Artisan LW (225–300)</strong> at Drakk Stonehand (Hinterlands)</span></label>
      <label class="choice-label"><input type="checkbox" id="ms_skin_artisan" onchange="updateDashboard()"> <span><strong>[Skin 200+]</strong> Trained <strong>Artisan Skinning (225–300)</strong></span></label>
      <label class="choice-label"><input type="checkbox" id="ms_tribal_wolfshead" onchange="updateDashboard()"> <span><strong>[LW 235 / L40+]</strong> Unlocked <strong>Tribal LW</strong> &amp; crafted {ilink('wolfshead-helm', 'Wolfshead Helm', 'rare')}</span></label>
      <label class="choice-label"><input type="checkbox" id="ms_devilsaur" onchange="updateDashboard()"> <span><strong>[LW 265–290]</strong> Crafted {ilink('devilsaur-gauntlets', '2/2 Devilsaur Set', 'rare')}</span></label>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title">2. Quick Coordinate Cheat-Sheet (Simplified &amp; Linked)</h2>
    <table>
      <thead>
        <tr>
          <th>Chain</th>
          <th>Compact Step-by-Step Coordinates &amp; Quest Links</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>{ilink('idol-of-shifting-tides', 'Idol of Shifting Tides', 'uncommon')} (-40 Shift Mana)</strong></td>
          <td>
            1. Accept {qlink('26', 'A Lesson to Learn (Q26)')} at Mathrengyl <span class="coord">Darnassus 35.4, 8.4</span> &rarr;
            2. Teleport Moonglade, go <strong>upstairs</strong> to Dendrite <span class="coord">Moonglade 56.2, 30.6</span> for {qlink('29', 'Trial of the Lake (Q29)')} &rarr;
            3. Dive for {ilink('15877', 'Shrine Bauble', 'quest')} <span class="coord">Moonglade 54.7, 46.4</span> &rarr;
            4. Use at Shrine <span class="coord">36.0, 41.4</span> &amp; talk to Tajarri <span class="coord">36.5, 40.1</span> for {qlink('272', 'Trial of the Sea Lion (Q272)')} &rarr;
            5. Loot Pendants at <span class="coord">Westfall 17.9, 33.2</span> &amp; <span class="coord">Darkshore 48.9, 11.3</span> &rarr;
            6. Fuse at <span class="coord">Moonglade 36.0, 41.4</span> &rarr; Dendrite <span class="coord">56.2, 30.6</span> &rarr; Claim Idol at <span class="coord">Darnassus 35.4, 8.4</span> ({qlink('5061', 'Aquatic Form Q5061')}).
          </td>
        </tr>
        <tr>
          <td><strong>Level 20 Cat Form ({qlink('98393', 'The Great Cat Spirit')})</strong></td>
          <td>
            1. Mathrengyl <span class="coord">Darnassus 35.4, 8.4</span> ({qlink('98393', 'Q98393')}) &rarr;
            2. Dendrite <span class="coord">Moonglade 56.2, 30.6</span> &rarr;
            3. Loot 3 Relics in Moonglade Barrow Den <span class="coord">54.5, 75.0</span> ({qlink('98395', 'The Three Relics')}) &rarr;
            4. Return to <span class="coord">Darnassus 35.4, 8.4</span> ({qlink('98397', 'To Darnassus')} &mdash; Unlocks <strong>Cat Form, Claw, Prowl, Rip, Shred</strong>).
          </td>
        </tr>
        <tr>
          <td><strong>{ilink('cozy-sleeping-bag', 'Cozy Sleeping Bag', 'rare')} (+3–9% XP + 12-Slot Bag)</strong></td>
          <td>
            1. <span class="coord">Westfall 37.3, 50.6</span> ({qlink('79008', 'Q79008')}) &rarr;
            2. <span class="coord">S. Barrens 46.3, 73.9</span> ({qlink('79192', 'Q79192')}) &rarr;
            3. <span class="coord">Stonetalon 40.8, 52.6</span> ({qlink('79980', 'Q79980')} &rarr; Mound <span class="coord">39.6, 49.8</span> {qlink('79974', 'Wet Job')}) &rarr;
            4. <span class="coord">Hillsbrad 87.2, 49.0</span> ({qlink('79975', 'Thoradin&#39;s Wall')}) &rarr;
            5. <span class="coord">Loch Modan 49.4, 13.0</span> ({qlink('79976', 'Eagle Figurine')}).
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2 class="section-title">3. Sync State to Agent Profile</h2>
    <button type="button" class="btn" onclick="copyProfileSync()">📋 Copy Markdown Snapshot</button>
    <button type="button" class="stepper-btn" style="margin-left:0.5rem;" onclick="resetAllState()">Reset Saved State</button>
    <pre id="sync-output" style="margin-top:0.75rem;"></pre>
  </div>
</div>

<script>
const APP_DATA = {data_json};
const STORAGE_KEY = "saftis_wow_forever_state_v1";
const CURRENT_BUILD_ID = APP_DATA.build_id;
const ZONE_LEGS = APP_DATA.zones;
const WEAPON_PROGRESSION = APP_DATA.weapons;
const CRAFT_BIS = APP_DATA.crafts;
const LW_BRACKETS = APP_DATA.lw_brackets;
const SYNC_URL = "http://127.0.0.1:" + APP_DATA.sync_port + "/state";

const MILESTONE_IDS = [
  "ms_westfall_note", "ms_lesson_darn", "ms_pendant_wf", "ms_pendant_ds", "ms_aca_label",
  "ms_lw_journeyman", "ms_skin_journeyman", "ms_cat_spirit", "ms_lw_expert_telonis",
  "ms_skin_expert", "ms_heavehammer", "ms_tanning_rack", "ms_sleeping_bag",
  "ms_lw_artisan_drakk", "ms_skin_artisan", "ms_tribal_wolfshead", "ms_devilsaur"
];

function openWikiSearch() {{
  const q = (document.getElementById("wiki-search-input").value || "").trim();
  if (!q) {{
    window.open("https://azeroth.wiki/forever", "_blank", "noopener");
    return;
  }}
  const slug = q.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  window.open("https://azeroth.wiki/forever/items/" + encodeURIComponent(slug), "_blank", "noopener");
}}

function switchTab(tabId, btn) {{
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
  document.getElementById(tabId).classList.add("active");
  btn.classList.add("active");
  const state = loadState();
  state.active_tab = tabId;
  saveState(state, false);
}}

function getTalentForLevel(lvl) {{
  if (lvl <= 14) return `${{Math.max(1, lvl - 9)}}/5 Ferocity (Row 1)`;
  if (lvl <= 16) return `${{lvl - 14}}/2 Feral Swiftness (+30% Speed)`;
  if (lvl <= 19) return `${{lvl - 16}}/3 Feral Instinct (Stealth/Swipe)`;
  if (lvl === 20) return "1/1 Feral Charge (Row 3)";
  if (lvl <= 22) return `${{lvl - 20}}/2 Sharpened Claws (+Crit)`;
  if (lvl <= 24) return `${{lvl - 22}}/2 Savage Fury (+20% Claw/Maul)`;
  if (lvl <= 27) return `${{lvl - 24}}/3 Predatory Strikes (+AP)`;
  if (lvl <= 29) return `${{lvl - 27}}/2 Blood Frenzy (Extra CP)`;
  if (lvl === 30) return "1/1 Leader of the Pack (+3% Crit)";
  if (lvl <= 39) return "Row 5/6 -> 5/5 Rend and Tear";
  if (lvl === 40) return "1/1 Primal Bite / Shifting Power (Row 7)";
  if (lvl <= 45) return `Resto: ${{lvl - 40}}/5 Furor`;
  if (lvl <= 50) return `Balance: ${{lvl - 45}}/5 Natural Weapons`;
  if (lvl === 51) return "1/1 Omen of Clarity";
  return `Natural Shapeshifter (Lvl ${{lvl}})`;
}}

function getMaxSkinnableLevel(skin) {{
  return skin < 100 ? Math.floor(skin / 5) + 10 : Math.floor(skin / 5);
}}

function stepVal(id, delta, minV, maxV) {{
  const el = document.getElementById(id);
  el.value = Math.max(minV, Math.min(maxV, (parseInt(el.value, 10) || minV) + delta));
  updateDashboard();
}}

function toggleCheck(id) {{
  const state = loadState();
  const el = document.getElementById(id);
  if (el) state[id] = el.checked;
  saveState(state, true);
  updateDashboard(false);
}}

function loadState() {{
  try {{
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return Object.assign({{}}, APP_DATA.initial_state, JSON.parse(raw));
  }} catch (e) {{}}
  return Object.assign({{}}, APP_DATA.initial_state);
}}

function saveState(state, syncDisk = true) {{
  try {{
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }} catch (e) {{}}
  const pill = document.getElementById("sync-status-pill");
  const nowStr = new Date().toLocaleTimeString();
  if (pill) pill.textContent = `✓ Auto-Saved (${{nowStr}})`;
  if (syncDisk) {{
    fetch(SYNC_URL, {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify(state)
    }}).then((r) => {{
      if (r.ok && pill) pill.textContent = `✓ Synced to Disk & Browser (${{nowStr}})`;
    }}).catch(() => {{}});
  }}
}}

function updateDashboard(pushSave = true) {{
  const state = loadState();
  const lvl = Math.max(1, Math.min(60, parseInt(document.getElementById("char_level").value, 10) || 17));
  const skin = Math.max(1, Math.min(300, parseInt(document.getElementById("skin_skill").value, 10) || 75));
  const lw = Math.max(1, Math.min(300, parseInt(document.getElementById("lw_skill").value, 10) || 55));
  const focus = document.getElementById("focus_filter") ? document.getElementById("focus_filter").checked : false;

  state.char_level = lvl;
  state.skin_skill = skin;
  state.lw_skill = lw;
  state.focus_filter = focus;

  MILESTONE_IDS.forEach((id) => {{
    const el = document.getElementById(id);
    if (el) state[id] = el.checked;
  }});

  if (pushSave) saveState(state, true);

  // 1. Update Zones Table
  let activeZone = ZONE_LEGS[0];
  ZONE_LEGS.forEach((leg) => {{
    const chkEl = document.getElementById(leg.id);
    const done = chkEl ? chkEl.checked : !!state[leg.id];
    const isActive = !done && lvl >= leg.min && lvl <= leg.max;
    if (isActive) activeZone = leg;
    const row = document.getElementById("row_" + leg.id);
    if (row) {{
      row.className = done ? "done-row" : (isActive ? "active-row" : "");
      if (focus && (done || leg.min > lvl + 6)) row.classList.add("filtered-out");
    }}
  }});

  // 2. Update Weapons Table
  let activeWpn = WEAPON_PROGRESSION[0];
  WEAPON_PROGRESSION.forEach((w) => {{
    const chkEl = document.getElementById(w.id);
    const done = chkEl ? chkEl.checked : !!state[w.id];
    const isCur = !done && lvl >= w.min && lvl <= w.max;
    if (isCur) activeWpn = w;
    const row = document.getElementById("row_" + w.id);
    if (row) {{
      row.className = (done || lvl > w.max) ? "done-row" : (isCur ? "active-row" : "");
      if (focus && (done || lvl > w.max || w.min > lvl + 8)) row.classList.add("filtered-out");
    }}
  }});

  // 3. Update Craft BiS Table
  let activeBisCraft = CRAFT_BIS[0];
  CRAFT_BIS.forEach((c) => {{
    const chkEl = document.getElementById(c.id);
    const done = chkEl ? chkEl.checked : !!state[c.id];
    const isReady = !done && ((lvl >= c.rl - 2 && lvl <= c.rl + 5) || (lw >= c.lw - 15 && lw <= c.lw + 25 && lvl >= c.rl - 3));
    if (!done && lvl >= c.rl - 2 && lvl <= c.rl + 6) activeBisCraft = c;
    const row = document.getElementById("row_" + c.id);
    if (row) {{
      row.className = (done || lvl > c.rl + 9) ? "done-row" : (isReady ? "active-row" : "");
      if (focus && (done || lvl > c.rl + 9 || c.rl > lvl + 8)) row.classList.add("filtered-out");
    }}
  }});

  // 4. Update LW Skill-Up Table
  let activeLw = LW_BRACKETS[0];
  LW_BRACKETS.forEach((b, idx) => {{
    const isCur = lw >= b.min && lw <= b.max;
    const isDone = lw > b.max;
    if (isCur) activeLw = b;
    const row = document.getElementById("row_lwb_" + idx);
    if (row) {{
      row.className = isDone ? "done-row" : (isCur ? "active-row" : "");
      if (focus && (isDone || b.min > lw + 45)) row.classList.add("filtered-out");
    }}
  }});

  // 5. Update Top Summary Cards
  const maxMob = getMaxSkinnableLevel(skin);
  const talent = getTalentForLevel(lvl);
  document.getElementById("card-zone").textContent = activeZone.name.replace("&amp;", "&");
  document.getElementById("card-zone-sub").textContent = activeZone.beasts;
  document.getElementById("card-lw").textContent = activeLw.recipe_plain;
  document.getElementById("card-lw-sub").textContent = `LW ${{activeLw.min}}–${{activeLw.max}}`;
  document.getElementById("card-bis-craft").textContent = activeBisCraft.name_plain;
  document.getElementById("card-bis-craft-sub").textContent = `Req L${{activeBisCraft.rl}} / LW ${{activeBisCraft.lw}}: ${{activeBisCraft.stats.split("(")[0]}}`;
  document.getElementById("card-weapon").textContent = (!state.ms_pendant_ds && lvl < 20) ? "Idol of Shifting Tides" : activeWpn.name_plain;
  document.getElementById("card-weapon-sub").textContent = (!state.ms_pendant_ds && lvl < 20) ? "-40 Shift Mana (Darnassus -> Moonglade -> Darkshore)" : activeWpn.stats;
  document.getElementById("card-talent").textContent = talent;
  document.getElementById("card-skin-sub").textContent = `Skinning ${{skin}}: Max Beast Lvl ${{maxMob}}`;

  // 6. Alerts & Dynamic Next Priority
  const alerts = [];
  if (lvl <= 23 && !state.cr_brawler_17) {{
    alerts.push({{ type: "success", text: `🥇 60 Merchant's Favor Plan (Lvl ${{lvl}}): Buy Pattern: Brawler's Leather Boots (#1, Req L17 / LW 85: +5 Str, +5 Agi, +4 Sta) & Pattern: Brawler's Leather Hood (#2, Req L20 / LW 100: +8 Agi, +10 Sta) at Three Corners (Redridge 15.3, 71.5)!` }});
  }}
  if (lvl >= 23 && lvl <= 34 && !state.ms_heavehammer && !state.wpn_heave) {{
    alerts.push({{ type: "success", text: `⚔️ Huge Lvl 24 Weapon Spike: In Wetlands (Whelgar's Excavation 38.8, 52.3), do 'Lost Relic Carry (Q95810) -> Prehistoric Prism (Q98824)' for Heavehammer (Rare 2H Mace: +32 Attack Power & +60 Armor)!` }});
  }}
  if (lw >= 50 && !state.ms_lw_journeyman) {{
    alerts.push({{ type: "danger", text: `🚨 LW is ${{lw}}/75: Train Journeyman LW (75–150 cap, 5s) at your next capital stop!` }});
  }}
  if (skin >= 50 && !state.ms_skin_journeyman) {{
    alerts.push({{ type: "danger", text: `🚨 Skinning is ${{skin}}/75: Train Journeyman Skinning (75–150 cap) immediately!` }});
  }}
  if (lw >= 125 && lvl >= 20 && !state.ms_lw_expert_telonis) {{
    alerts.push({{ type: "danger", text: `🚨 LW is ${{lw}}/150: Teleport Moonglade -> fly to Darnassus to train Expert LW (150–225) at Telonis!` }});
  }}

  let headline = "";
  let detail = "";
  if (lvl <= 19 && !state.ms_lesson_darn) {{
    headline = "Next: Accept 'A Lesson to Learn (Q26)' in Darnassus (35.4, 8.4) -> Moonglade Upstairs (56.2, 30.6)";
    detail = "Starts the Aquatic Form chain for Idol of Shifting Tides (-40 shapeshift mana). Also click Westfall Burned Remains (37.3, 50.6) & Westfall Pendant (17.9, 33.2) before taking the Stormwind Boat (22.7, 56.7) to Darkshore.";
  }} else if (lvl <= 19 && !state.ms_pendant_ds) {{
    headline = `Next: Grind 03-Darkshore Beast Quests (Lvl ${{lvl}}->20) & Claim Idol of Shifting Tides`;
    detail = "Focus Wizbang's Buzzbox + Plagued Bears + Beached Creatures + South Onu hub. Dive at Darkshore (48.9, 11.3) for the 2nd Pendant -> fuse in Moonglade -> claim Idol in Darnassus (35.4, 8.4).";
  }} else if (lvl >= 20 && !state.ms_cat_spirit) {{
    headline = "🔥 Level 20 Unlock: Do 'The Great Cat Spirit' (Darnassus 35.4, 8.4 -> Moonglade 56.2, 30.6) for Cat Form!";
    detail = "Collect the 3 Barrow Den relics at Moonglade (54.5, 75.0) to unlock Cat Form, Claw, Prowl, Rip, and Shred!";
  }} else {{
    headline = `Active Zone (Lvl ${{lvl}}): ${{activeZone.name.replace("&amp;", "&")}} • Target Craft: ${{activeBisCraft.name_plain}}`;
    detail = `Skinnable Beasts: ${{activeZone.beasts}} | Target Weapon: ${{activeWpn.name_plain}} (${{activeWpn.stats}})`;
  }}

  document.getElementById("ns-headline").textContent = headline;
  document.getElementById("ns-detail").textContent = detail;

  const alertsEl = document.getElementById("ns-alerts");
  alertsEl.innerHTML = "";
  alerts.forEach((a) => {{
    const div = document.createElement("div");
    div.className = `alert-pill ${{a.type}}`;
    div.textContent = a.text;
    alertsEl.appendChild(div);
  }});

  const checkedList = Object.keys(state).filter((k) => state[k] === true);
  document.getElementById("sync-output").textContent =
`# Saftis Live Snapshot (Saftkalaset#1771 • Europe PvP)
- **Level:** ${{lvl}} (${{talent}})
- **Skinning:** ${{skin}}/300 (Max beast level: ${{maxMob}})
- **Leatherworking:** ${{lw}}/300 (Skill craft: ${{activeLw.recipe_plain}} | Gear target: ${{activeBisCraft.name_plain}})
- **Active Zone:** ${{activeZone.name.replace("&amp;", "&")}}
- **Target Weapon:** ${{activeWpn.name_plain}}
- **Completed Checkboxes:** ${{checkedList.length ? checkedList.join(", ") : "none yet"}}`;
}}

// Camp Tent Timer
let tentInterval = null;
function startTentTimer() {{
  const state = loadState();
  state.tent_end_ts = Date.now() + 60 * 60 * 1000;
  saveState(state, true);
  tickTentTimer();
}}
function resetTentTimer() {{
  const state = loadState();
  delete state.tent_end_ts;
  saveState(state, true);
  if (tentInterval) clearInterval(tentInterval);
  document.getElementById("tent-timer").textContent = "READY";
}}
function tickTentTimer() {{
  if (tentInterval) clearInterval(tentInterval);
  const update = () => {{
    const endTs = loadState().tent_end_ts;
    const el = document.getElementById("tent-timer");
    if (!endTs) {{ el.textContent = "READY"; return; }}
    const rem = Math.max(0, Math.floor((endTs - Date.now()) / 1000));
    if (rem === 0) {{ el.textContent = "🏕️ TENT READY!"; clearInterval(tentInterval); return; }}
    el.textContent = `${{String(Math.floor(rem / 60)).padStart(2, "0")}}:${{String(rem % 60).padStart(2, "0")}}`;
  }};
  update();
  tentInterval = setInterval(update, 1000);
}}

function copyProfileSync() {{
  navigator.clipboard.writeText(document.getElementById("sync-output").textContent);
  alert("Copied snapshot to clipboard!");
}}

function resetAllState() {{
  if (confirm("Reset saved browser progress back to Level 17 defaults?")) {{
    localStorage.removeItem(STORAGE_KEY);
    location.reload();
  }}
}}

// Hot-Reload Watcher (works natively on file:/// in Firefox via script-tag polling!)
function startHotReloadWatcher() {{
  setInterval(() => {{
    const oldScript = document.getElementById("hotload-probe");
    if (oldScript) oldScript.remove();
    const s = document.createElement("script");
    s.id = "hotload-probe";
    s.src = "saftis_wow_forever_hotload.js?t=" + Date.now();
    s.onload = () => {{
      if (window.SAFTIS_LATEST_BUILD_ID && window.SAFTIS_LATEST_BUILD_ID !== CURRENT_BUILD_ID) {{
        location.reload();
      }}
    }};
    document.body.appendChild(s);
  }}, 2500);
}}

window.addEventListener("DOMContentLoaded", () => {{
  const state = loadState();
  if (state.char_level) document.getElementById("char_level").value = state.char_level;
  if (state.skin_skill) document.getElementById("skin_skill").value = state.skin_skill;
  if (state.lw_skill) document.getElementById("lw_skill").value = state.lw_skill;
  if (state.focus_filter && document.getElementById("focus_filter")) {{
    document.getElementById("focus_filter").checked = !!state.focus_filter;
  }}
  const allCheckIds = [
    ...MILESTONE_IDS,
    ...ZONE_LEGS.map((x) => x.id),
    ...WEAPON_PROGRESSION.map((x) => x.id),
    ...CRAFT_BIS.map((x) => x.id)
  ];
  allCheckIds.forEach((id) => {{
    const el = document.getElementById(id);
    if (el && state[id] !== undefined) el.checked = !!state[id];
  }});
  if (state.active_tab) {{
    const targetBtn = document.querySelector(`.tab-btn[onclick*="${{state.active_tab}}"]`);
    if (targetBtn) switchTab(state.active_tab, targetBtn);
  }}
  updateDashboard(false);
  tickTentTimer();
  startHotReloadWatcher();
}});
</script>
"""


class StateSyncHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path.startswith("/state"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(load_saved_disk_state()).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        if self.path.startswith("/state"):
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(raw)
                save_disk_state(data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as exc:
                self.send_response(400)
                self._send_cors()
                self.end_headers()
                self.wfile.write(str(exc).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def compile_dashboard(output_path: Path, open_browser: bool) -> None:
    build_id = str(int(time.time() * 1000))
    initial_state = load_saved_disk_state()
    body = build_dashboard_body(build_id, initial_state)

    output_path = output_path.expanduser().resolve()
    cmd = [
        sys.executable,
        str(HTML_SKILL_RENDERER),
        "--title",
        "Saftis (16→60) WoW: Forever Dynamic Progression Dashboard",
        "--scope",
        "Night Elf Feral Druid • Saftkalaset#1771 • Europe PvP Megaserver • Linked & Hot-Reload Edition",
        "--status",
        "Interactive Live Tracker",
        "--output",
        str(output_path),
    ]
    if open_browser:
        cmd.append("--open")

    subprocess.run(cmd, input=body, text=True, check=True)

    hotload_js = output_path.parent / "saftis_wow_forever_hotload.js"
    hotload_js.write_text(
        f'window.SAFTIS_LATEST_BUILD_ID = "{build_id}";\n',
        encoding="utf-8",
    )
    print(f"Hot-reload probe updated: {hotload_js} (build {build_id})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output HTML file path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the compiled dashboard in Firefox",
    )
    parser.add_argument(
        "--serve-sync",
        action="store_true",
        help=f"Run the local disk auto-save sync listener on 127.0.0.1:{SYNC_PORT}",
    )
    args = parser.parse_args()

    compile_dashboard(args.output, args.open)
    if args.serve_sync:
        server = http.server.HTTPServer(("127.0.0.1", SYNC_PORT), StateSyncHandler)
        print(f"Listening for live dashboard state updates on http://127.0.0.1:{SYNC_PORT}/state ...")
        server.serve_forever()


if __name__ == "__main__":
    main()
