"""Add route maps and area maps to oahu.md / maui.md.

Usage:  python3 island_maps.py <repo root>
- Top of each island guide: the hotel hub map (from gen_md.py).
- Each day of the final plan: that day's route from the hotel (images from gen_md.py).
- Each "everything else" area: a new area map (hotel = H, places numbered) + a distance table.
Blocks are marked <!-- map:ID --> and are skipped if already present, so re-running is safe.
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1]
sys.path.insert(0, HERE)
import gen_md as G  # noqa: E402  (also sets up render with the trip places)
RM = G.RM

EXTRA = json.load(open(os.path.join(HERE, "places_extra.json")))
for k, v in EXTRA.items():
    RM.C[k] = tuple(v["coords"]); RM.LABEL[k] = v["label"]
C, L = RM.C, RM.LABEL

MX_FILE = os.path.join(HERE, "matrix_extra.json")
MX = json.load(open(MX_FILE)) if os.path.exists(MX_FILE) else {}
def from_hotel(hub, keys):
    """Drive distance/time from the hotel to each place (OSRM table, cached)."""
    need = [k for k in keys if f"{hub}>{k}" not in MX]
    if need:
        pts = ";".join(f"{C[k][1]},{C[k][0]}" for k in [hub] + need)
        url = f"https://router.project-osrm.org/table/v1/driving/{pts}?sources=0&annotations=distance,duration"
        r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=RM.UA), timeout=30))
        for i, k in enumerate(need, 1):
            MX[f"{hub}>{k}"] = {"dist_m": r["distances"][0][i], "dur_s": r["durations"][0][i]}
        json.dump(MX, open(MX_FILE, "w"), indent=1); time.sleep(1)
    return {k: MX[f"{hub}>{k}"] for k in keys}

def imgs(name, alt):
    return (f'<a href="maps/{name}_street.jpg"><img src="maps/{name}_street.jpg" width="49%" alt="{alt} (map)"></a> '
            f'<a href="maps/{name}_sat.jpg"><img src="maps/{name}_sat.jpg" width="49%" alt="{alt} (satellite)"></a>')

# ------------------------------------------------------------ areas
AREAS = {
 "oahu.md": dict(hub="REEF", areas=[
   dict(id="area_oahu_honolulu", title="Waikīkī + Honolulu", anchor="| **Puʻu ʻUalakaʻa lookout (Tantalus)** |", zmax=14,
        keys=["KUHIO", "KAPIOLANI", "ALAMOANA", "IOLANI", "CHINATOWN", "FOSTER", "PUNCHBOWL", "BISHOP", "TANTALUS"], routes=[],
        lpos={"CHINATOWN": "left", "FOSTER": "above", "IOLANI": "below"},
        how="Walk (Waikīkī), or a short rideshare"),
   dict(id="area_oahu_east", title="East Oʻahu", anchor="| **Lanikai + Kailua** |", zmax=13,
        keys=["HANAUMA", "HALONA", "SANDY", "MAKAPUU", "LANIKAI", "KAILUA"], routes=[["REEF", "HANAUMA", "MAKAPUU", "KAILUA"]],
        lpos={"HALONA": "above", "KAILUA": "left", "LANIKAI": "below"},
        how="Rideshare or a tour; the coast road loops round to Kailua"),
   dict(id="area_oahu_windward", title="Windward side", anchor="| **Hoʻomaluhia Botanical Garden** |", zmax=12,
        keys=["PALI", "HOOMALUHIA", "BYODOIN", "MOKOLII", "KUALOA"], routes=[["REEF", "PALI", "BYODOIN", "KUALOA"]],
        lpos={"MOKOLII": "left", "KUALOA": "above"},
        how="Tour, or rideshare out (rides back are harder to find)"),
   dict(id="area_oahu_north", title="North Shore", anchor="| **Polynesian Cultural Center** |", zmax=11,
        keys=["DOLE", "HALEIWA", "LANIAKEA", "WAIMEABAY", "WAIMEAVALLEY", "PIPELINE", "PCC"], routes=[["REEF", "DOLE", "HALEIWA", "PIPELINE"]],
        lpos={"WAIMEABAY": "left", "LANIAKEA": "left"},
        how="Full-day tour (not in the plan)"),
 ]),
 "maui.md": dict(hub="MCH", areas=[
   dict(id="area_maui_south", title="South Maui", anchor="| **Maui Ocean Center** (Māʻalaea) |", zmax=13,
        keys=["KAMAOLE", "WAILEABEACH", "MALUAKA", "BIGBEACH", "OCEANCENTER"], routes=[["MCH", "BIGBEACH"]],
        how="Walk to Kamaʻole; rideshare elsewhere (prebook the ride back from Big Beach)"),
   dict(id="area_maui_central", title="Central Maui", anchor="| **Wailuku town** |", zmax=13,
        keys=["WAILUKU", "IAO"], routes=[["MCH", "IAO"]], how="Rideshare or a half-day tour"),
   dict(id="area_maui_upcountry", title="Upcountry", anchor="| **Haleakalā daytime** |", zmax=12,
        keys=["KULA", "MAKAWAO", "HALE"], routes=[["MCH", "KULA", "HALE"]], how="On the Haleakalā tour; otherwise a tour or rideshare"),
   dict(id="area_maui_north", title="North Shore", anchor="| **Mama's Fish House** |", zmax=13,
        keys=["PAIA", "MAMAS", "HOOKIPA"], routes=[["MCH", "PAIA", "HOOKIPA"]], how="Rideshare (the ride back is harder) or a tour that stops there"),
   dict(id="area_maui_west", title="West Maui", anchor="| **Lahaina** |", zmax=12,
        keys=["LAHAINA", "KAANAPALI", "NAPILI", "KAPALUA", "NAKALELE"], routes=[["MCH", "KAANAPALI", "NAKALELE"]],
        lpos={"NAPILI": "below", "KAPALUA": "left"},
        how="Tour or a lūʻau package with transport; rideshare ~$70–100 each way"),
 ]),
}

# ------------------------------------------------------------ day routes (images made by gen_md.py)
TRIPS = {t["id"]: t for t in G.OAHU["trips"] + G.MAUI["trips"]}
DAYS = {
 "oahu.md": [("- ⛔ Nothing time-sensitive today.", "oahu_airport"), ("- 🕐 NYC falls back today", "oahu_dh"),
             ("- Pack for tomorrow's island hop.", "oahu_ph")],
 "maui.md": [("- 🍽️ Casual dinner in Kīhei.", "maui_airport"), ("- **If cancelled:** move it to Nov 5", "maui_molokini"),
             ("- 🪫 **If the week feels too full", "maui_hana"), ("- ⛔ No Hāna, no summit, no early check-ins.", "maui_wailea"),
             ("- If clouds or wind close the summit", "maui_haleakala")],
}
HUB = {"oahu.md": ("**Hotel:**", "oahu_hub", "oahu"), "maui.md": ("**Hotel:**", "maui_hub", "maui")}

def day_block(tid):
    t = TRIPS[tid]; r = RM.route(t["keys"])
    return (f"<!-- map:{tid} -->\n**🗺️ Route from the hotel:** {G.mi(r['dist_m'])} · {t['plan']} · {t['how']} · "
            f"[▶ directions]({G.directions(t['keys'])}) · [more in map.md](map.md#{t['anchor']})\n\n{imgs(tid, t['title'])}\n")

def area_block(hub, a):
    keys = [hub] + a["keys"]
    for style in G.VIEWS:
        RM.render(f"{a['id']}_{style}", f"{a['title']}: where everything is from the hotel (H)", keys=keys, routes=a["routes"],
                  hub=hub, style=style, zmax=a["zmax"], pad=80, lpos=a.get("lpos"))
    d = from_hotel(hub, a["keys"])
    rows = ["| Pin | Place | From the hotel | Drive (no traffic) | Map |", "|:-:|---|---:|---:|---|"]
    for n, k in enumerate(a["keys"], 1):
        rows.append(f"| {n} | {L[k]} | {G.mi(d[k]['dist_m'])} | {G.mins(d[k]['dur_s'])} | "
                    f"[▶ directions]({G.directions([hub, k])}) · [pin]({G.gmap(k)}) |")
    return (f"<!-- map:{a['id']} -->\n**🗺️ {a['title']}: where these are from the hotel (H).** Getting there without a car: {a['how']}.\n\n"
            f"{imgs(a['id'], a['title'])}\n\n" + "\n".join(rows) + "\n")

def hub_block(name, anchor):
    return (f"<!-- map:{name} -->\n**🗺️ Everything from the hotel (H)** · numbered pins and distances in [map.md](map.md#{anchor}-hub)\n\n"
            f"{imgs(name, 'Everything from the hotel')}\n")

def insert_after(lines, prefix, block, table=False):
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(idx) == 1, (prefix, idx)
    i = idx[0]
    if table:
        while i + 1 < len(lines) and lines[i + 1].startswith("|"): i += 1
    lines.insert(i + 1, "\n" + block)

if __name__ == "__main__":
    for fn in ("oahu.md", "maui.md"):
        path = os.path.join(ROOT, fn); s = open(path).read(); lines = s.split("\n"); added = 0
        pre, name, anchor = HUB[fn]
        if f"<!-- map:{name} -->" not in s: insert_after(lines, pre, hub_block(name, anchor)); added += 1
        for prefix, tid in DAYS[fn]:
            if f"<!-- map:{tid} -->" not in s: insert_after(lines, prefix, day_block(tid)); added += 1
        spec = AREAS[fn]
        for a in spec["areas"]:
            if f"<!-- map:{a['id']} -->" not in s: insert_after(lines, a["anchor"], area_block(spec["hub"], a), table=True); added += 1
        open(path, "w").write("\n".join(lines)); print(fn, "map blocks added:", added)
