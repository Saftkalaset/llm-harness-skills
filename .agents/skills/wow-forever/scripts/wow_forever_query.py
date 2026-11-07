#!/usr/bin/env python3
"""Zero-dependency CLI helper for querying World of Warcraft: Forever MCP endpoints and Polestar tables."""

import argparse
import json
import sys
import urllib.request
from typing import Any, Dict, Optional

AZEROTH_MCP_URL = "https://azeroth.wiki/api/mcp"
EVERLOOT_MCP_URL = "https://everloot.app/mcp/public"

# Curated Alliance/Contested zone skinnable beasts & level brackets (from Polestar skinning.js / Forever 1.60.1)
ZONE_SKINNABLE_BEASTS: Dict[str, Dict[str, Any]] = {
    "teldrassil": {
        "levels": "1–11",
        "pvp_status": "Alliance Safe",
        "leather": "Ruined Leather Scraps / Light Leather (Skinning 1–50)",
        "beasts": [
            "Young Thistle Boar", "Thistle Boar", "Young Nightsaber",
            "Mangy Nightsaber", "Nightsaber", "Nightsaber Stalker", "Elder Nightsaber"
        ],
    },
    "darkshore": {
        "levels": "11–20",
        "pvp_status": "Alliance Safe (Zero PvP Gank Risk)",
        "leather": "Light Leather & Medium Leather + Light/Medium Hide (Skinning 30–100)",
        "beasts": [
            "Moonstalker Runt (10–11)", "Moonstalker (14–15)", "Thistle Bear (11–12)",
            "Rabid Thistle Bear (13–14, quest: Plagued Lands / Cleansing of the Infected)",
            "Moonstalker Sire (17–18)", "Moonstalker Matriarch (19–20, south Darkshore)",
            "Grizzled Thistle Bear (16–17, south Darkshore)", "Ghostpaw Runner (19–20, Ashenvale border)"
        ],
    },
    "loch_modan": {
        "levels": "12–20",
        "pvp_status": "Alliance Safe",
        "leather": "Light Leather & Medium Leather (Skinning 40–100)",
        "beasts": [
            "Mountain Boar", "Mangy Mountain Boar", "Elder Mountain Boar",
            "Elder Black Bear", "Grizzled Black Bear", "Black Bear Patriarch",
            "Loch Crocolisk (Crocolisk Meat + Medium Leather around The Loch)"
        ],
    },
    "westfall": {
        "levels": "12–19",
        "pvp_status": "Alliance Safe",
        "leather": "Light Leather & Medium Leather",
        "beasts": [
            "Young Goretusk", "Goretusk", "Great Goretusk (Goretusk Liver/Snout quests)",
            "Coyote", "Coyote Packleader"
        ],
    },
    "redridge": {
        "levels": "16–25",
        "pvp_status": "Contested (Medium PvP Risk — vendor Daniel Stitchsong at Three Corners sells Merchant's Favor LW patterns)",
        "leather": "Medium Leather & Medium Hide (Skinning 75–125)",
        "beasts": [
            "Great Goretusk (16–17)", "Redridge Thrasher (18–20)",
            "Dire Condor (not plain-beast skinnable; focus Goretusks/Thrashers)"
        ],
    },
    "ashenvale": {
        "levels": "19–30",
        "pvp_status": "Contested (Moderate-High PvP Risk along main road; safer in off-road beast pockets)",
        "leather": "Medium Leather & Heavy Leather (Skinning 90–150)",
        "beasts": [
            "Ghostpaw Runner (19–20)", "Ashenvale Bear (21–22)", "Ghostpaw Alpha (23–24)",
            "Elder Ashenvale Bear (25–26)", "Shadowhorn Stag (26–27)",
            "Ghostpaw Howler (27–28)", "Elder Shadowhorn Stag (28–29)", "Giant Ashenvale Bear (29–30)"
        ],
    },
    "wetlands": {
        "levels": "21–30",
        "pvp_status": "Contested (Low-Moderate PvP Risk in western marshes & raptor ridges)",
        "leather": "Medium Leather & Heavy Leather (Skinning 100–150)",
        "beasts": [
            "Young Wetlands Crocolisk (21–22, Young Crocolisk Skin quest)",
            "Mottled Raptor / Screecher (22–25)", "Wetlands Crocolisk (24–25)",
            "Mottled Scytheclaw / Razormaw (26–29, Raptor Mastery chain)",
            "Giant Wetlands Crocolisk (25–26, Ormer's Revenge / Apprentice's Duties)"
        ],
    },
    "duskwood": {
        "levels": "20–30",
        "pvp_status": "Contested (High PvP Risk near Darkshire/roads; northern wolf woods safer)",
        "leather": "Medium Leather & Heavy Leather (Skinning 95–150)",
        "beasts": [
            "Starving Dire Wolf (19–20)", "Rabid Dire Wolf (21–22, Wolves at Our Heels)",
            "Black Ravager (23–24)", "Black Ravager Mastiff (25–26)"
        ],
    },
    "hillsbrad": {
        "levels": "22–32",
        "pvp_status": "Contested (Very High PvP Risk near Tarren Mill/Southshore; Yeti cave contested)",
        "leather": "Medium Leather & Heavy Leather (Skinning 105–160)",
        "beasts": [
            "Gray Bear (21–22)", "Starving Mountain Lion (23–24)",
            "Feral Mountain Lion (27–28)", "Cave Yeti (30–31)", "Ferocious Yeti (32–33)"
        ],
    },
    "stranglethorn": {
        "levels": "30–45",
        "pvp_status": "Contested (Extreme PvP Risk at Nesingwary Camp; use Stealth/Prowl + Track Humanoids)",
        "leather": "Heavy Leather & Thick Leather (Skinning 150–225)",
        "beasts": [
            "Young Stranglethorn Tiger / Panther (30–32)", "Lashtail Raptor (33–35)",
            "Stranglethorn Tigress / Elder Panther (35–38)", "Snapjaw Crocolisk (35–36)",
            "Mistvale Gorilla / Elder Mistvale Gorilla (32–41)", " Bhag'thera / King Bangalash (Elite quests)"
        ],
    },
}


def call_mcp(url: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "Mozilla/5.0 (WoW-Forever-Skill/1.0)",
        },
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_text(mcp_response: Dict[str, Any]) -> str:
    content = mcp_response.get("result", {}).get("content", [])
    return "\n".join(c.get("text", "") for c in content if isinstance(c, dict))


def cmd_search(query: str, kind: Optional[str], limit: int) -> None:
    print(f"=== Azeroth DB (`wowdb`) Search: {query!r} ===")
    az_args: Dict[str, Any] = {"query": query, "limit": limit}
    if kind:
        az_args["kind"] = kind
    try:
        az_text = extract_text(call_mcp(AZEROTH_MCP_URL, "search", az_args))
        az_data = json.loads(az_text)
        for e in az_data.get("entries", [])[:limit]:
            facts = ", ".join(str(f) for f in e.get("facts", []) if f is not None)
            print(f"  [{e.get('kind')}] {e.get('name')} ({facts}) -> path: {e.get('path')}")
    except Exception as exc:
        print(f"  [!] Azeroth DB error: {exc}", file=sys.stderr)

    print(f"\n=== Everloot Knowledge Search: {query!r} ===")
    ev_args: Dict[str, Any] = {"query": query, "limit": min(limit, 25), "version": "forever"}
    if kind and kind in {
        "item", "npc", "object", "quest", "zone", "spell", "lore_page",
        "achievement", "faction", "title", "quest_chain", "mount", "legacy_perk", "race", "instance", "build"
    }:
        ev_args["kind"] = kind
    try:
        ev_text = extract_text(call_mcp(EVERLOOT_MCP_URL, "search_knowledge", ev_args))
        print(ev_text)
    except Exception as exc:
        print(f"  [!] Everloot error: {exc}", file=sys.stderr)


def cmd_entity(target: str, field: Optional[str]) -> None:
    if target.startswith("/") or target.startswith("http"):
        args: Dict[str, Any] = {"path": target}
        if field:
            args["field"] = field
        text = extract_text(call_mcp(AZEROTH_MCP_URL, "get_entity", args))
        print(text)
    elif target.isdigit():
        args = {"id": int(target)}
        if field:
            args["field"] = field
        text = extract_text(call_mcp(EVERLOOT_MCP_URL, "get_entity", args))
        print(text)
    else:
        print("Target must be an Azeroth DB path (starting with '/') or an Everloot numeric ID.", file=sys.stderr)
        sys.exit(1)


def cmd_talents(cls: str, tree: Optional[str]) -> None:
    args: Dict[str, Any] = {"class": cls.lower(), "builds": True}
    if tree:
        args["tree"] = tree
    print(extract_text(call_mcp(EVERLOOT_MCP_URL, "talent_tree", args)))


def cmd_beasts(zone: Optional[str]) -> None:
    if zone:
        key = zone.lower().replace(" ", "_")
        matches = {k: v for k, v in ZONE_SKINNABLE_BEASTS.items() if key in k}
    else:
        matches = ZONE_SKINNABLE_BEASTS

    for k, info in matches.items():
        print(f"=== {k.upper().replace('_', ' ')} (Levels {info['levels']}) ===")
        print(f"  PvP Profile : {info['pvp_status']}")
        print(f"  Leather Tier: {info['leather']}")
        print("  Skinnable   : " + ", ".join(info["beasts"]))
        print()


def cmd_ecosystem() -> None:
    print("=== Everloot Community Ecosystem Registry ===")
    print(extract_text(call_mcp(EVERLOOT_MCP_URL, "ecosystem_projects", {"board": "all"})))
    print("\n=== Recent Official WoW: Forever Changes & Hotfixes ===")
    print(extract_text(call_mcp(EVERLOOT_MCP_URL, "recent_changes", {"game": "forever", "limit": 8})))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="Search Azeroth DB and Everloot in parallel")
    p_search.add_argument("query", help="Search query string")
    p_search.add_argument("--kind", help="Optional entity kind (e.g., item, recipe, ability, quest, camp)")
    p_search.add_argument("--limit", type=int, default=12)

    p_entity = sub.add_parser("entity", help="Get full record by Azeroth DB path (/forever/...) or Everloot numeric ID")
    p_entity.add_argument("target", help="Azeroth DB path or Everloot numeric ID")
    p_entity.add_argument("--field", help="Optional JSON pointer field")

    p_talents = sub.add_parser("talents", help="Fetch WoW Forever 1.60.1 talent trees from Everloot")
    p_talents.add_argument("cls", help="Class name (e.g., druid)")
    p_talents.add_argument("--tree", help="Optional tree name (e.g., 'Feral Combat')")

    p_beasts = sub.add_parser("beasts", help="List skinnable beasts and PvP risk per zone")
    p_beasts.add_argument("--zone", help="Filter by zone name (e.g., darkshore, ashenvale, wetlands)")

    sub.add_parser("ecosystem", help="Check WoW Forever community tools and recent official changes")

    args = parser.parse_args()
    if args.cmd == "search":
        cmd_search(args.query, args.kind, args.limit)
    elif args.cmd == "entity":
        cmd_entity(args.target, args.field)
    elif args.cmd == "talents":
        cmd_talents(args.cls, args.tree)
    elif args.cmd == "beasts":
        cmd_beasts(args.zone)
    elif args.cmd == "ecosystem":
        cmd_ecosystem()


if __name__ == "__main__":
    main()
