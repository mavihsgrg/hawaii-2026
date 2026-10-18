"""Render the hotel-centred maps and write map.md.

Usage:  python3 gen_md.py <repo root>
Every island is organised around its hotel (the red H): a hub map with every destination,
then one section per trip out of the hotel, each with a street map and a terrain map.
"""
import json, os, sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1]
sys.path.insert(0, HERE)
import render as RM  # noqa: E402  (render reads sys.argv[1]; we point it at maps/ below)
from places import PLACES  # noqa: E402

RM.OUT = os.path.join(ROOT, "maps")
C, L, R = RM.C, RM.LABEL, RM.ROUTES
M = json.load(open(os.path.join(HERE, "matrix.json")))

mi = lambda m: f"{m/1609.34:.1f} mi"
mins = lambda s: f"{round(s/60)} min" if s < 5400 else f"{int(s//3600)} h {round(s%3600/60):02d} min"
ll = lambda k: f"{C[k][0]:.5f},{C[k][1]:.5f}"
def gmap(k, base="roadmap", z=15): return f"https://www.google.com/maps/@?api=1&map_action=map&center={ll(k)}&zoom={z}&basemap={base}"
def earth(k): return f"https://earth.google.com/web/@{ll(k)},300a,2500d,35y,0h,60t,0r"
def directions(keys):
    url = f"https://www.google.com/maps/dir/?api=1&origin={ll(keys[0])}&destination={ll(keys[-1])}&travelmode=driving"
    if len(keys) > 2: url += "&waypoints=" + quote("|".join(ll(k) for k in keys[1:-1]))
    return url
def links(k): return f"[map]({gmap(k)}) · [terrain]({gmap(k, 'terrain')}) · [satellite]({gmap(k, 'satellite', 16)}) · [3D]({earth(k)})"

OWN_TEXT = {  # (plan, how) for places that share a trip with another destination
    "BISHOP": ("15–20 min from Pearl Harbor; 2–3 h visit", "🚕 Rideshare (~$15–25)"),
    "MOLOKINI": ("~1 h by boat each way; ~5 h trip", "🚤 PacWhale boat from Māʻalaea (pin 2)"),
    "MAALAEA": ("25–40 min; check in 45 min early", "🚖 Prebooked dawn taxi there, rideshare back (~$55–80)"),
}

CLOSE_Z = {"MOLOKINI": 15, "HANA": 15, "KULA": 14, "HALE": 15, "HNL": 14, "OGG": 14, "DH": 15, "PH": 15}

VIEWS = ("street", "sat")  # left: normal map, right: satellite

def pair(name, title, **kw):
    """Render the same view as a normal map and a satellite map, side by side."""
    for style in VIEWS:
        RM.render(f"{name}_{style}", title, style=style, **kw)
    return (f'<a href="maps/{name}_street.jpg"><img src="maps/{name}_street.jpg" width="49%" alt="{title} (map)"></a> '
            f'<a href="maps/{name}_sat.jpg"><img src="maps/{name}_sat.jpg" width="49%" alt="{title} (satellite)"></a>')

def closeup(k, hub=False):
    la, lo = C[k]; dd = 0.0008
    for style in VIEWS:
        RM.render(f"c_{k.lower()}_{style}", L[k], keys=[k], extra_pts=[(la-dd, lo-dd), (la+dd, lo+dd)], W=900, H=560,
                  zmax=CLOSE_Z.get(k, 16), pad=40, style=style, hub=k if hub else None)
    return (f'<img src="maps/c_{k.lower()}_street.jpg" width="49%" alt="{L[k]} (map)"> '
            f'<img src="maps/c_{k.lower()}_sat.jpg" width="49%" alt="{L[k]} (satellite)">\n\n'
            f"<sub>`{ll(k)}` · open in Google: {links(k)}</sub>")

def trip_table(keys, plan, how):
    r = RM.route(list(keys))
    return (f"| Distance | Drive time (no traffic) | Plan for | How we get there |\n|---:|---:|---|---|\n"
            f"| **{mi(r['dist_m'])}** | {mins(r['dur_s'])} | {plan} | {how} |\n\n"
            f"[▶ Directions from the hotel in Google Maps]({directions(list(keys))})")

# ---------------------------------------------------------------- trips
OAHU = dict(hub="REEF", trips=[
    dict(id="oahu_airport", anchor="o-airport", icon="✈️", title="Hotel ↔ HNL airport", days="Sat Oct 31 (arrive) · Tue Nov 3 (leave)",
         keys=["REEF", "HNL"], dest=["HNL"], plan="30–45 min with bags; leave ~2.5 h before the Nov 3 flight",
         how="🚕 Rideshare or flat-rate taxi (~$30–50 each way); shuttle optional"),
    dict(id="oahu_dh", anchor="o-dh", icon="🥾", title="Hotel → Diamond Head", days="Sun Nov 1",
         keys=["REEF", "DH"], dest=["DH"], plan="15–20 min; hike 1.5–2 h (~560 ft climb)",
         how="🚕 Rideshare both ways (~$25–40 total)"),
    dict(id="oahu_ph", anchor="o-ph", icon="⚓", title="Hotel → Pearl Harbor → Bishop Museum → Hotel", days="Mon Nov 2",
         keys=["REEF", "PH", "BISHOP", "REEF"], dest=["PH", "BISHOP"], plan="30–40 min out in H-1 traffic; 3–4 h at Pearl Harbor",
         how="🚕 Rideshare each leg (~$60–100 total); no bags allowed at Pearl Harbor"),
])
MAUI = dict(hub="MCH", trips=[
    dict(id="maui_airport", anchor="m-airport", icon="✈️", title="Hotel ↔ OGG airport", days="Tue Nov 3 (arrive) · Sun Nov 8 (leave ~11:30 AM)",
         keys=["MCH", "OGG"], dest=["OGG"], plan="30–45 min (+ shuttle stops)",
         how="🚐 Prebooked shared shuttle or rideshare (~$40–70 each way)"),
    dict(id="maui_molokini", anchor="m-molokini", icon="🤿", title="Hotel → Māʻalaea Harbor → boat to Molokini", days="Wed Nov 4",
         keys=["MCH", "MAALAEA"], dest=["MAALAEA", "MOLOKINI"], lines=[("MAALAEA", "MOLOKINI", "boat ~1 h")],
         plan="25–40 min; check in 45 min early · then ~11 mi by boat (~5 h trip)",
         how="🚖 Prebooked dawn taxi there, rideshare back (~$55–80)"),
    dict(id="maui_hana", anchor="m-hana", icon="🌿", title="Hotel → Road to Hāna", days="Thu Nov 5",
         keys=["MCH", "PAIA", "HOOKIPA", "TWIN", "KEANAE", "WAI", "HANA"], dest=["HANA"], zmax=12,
         plan="**10–12 h round-trip day** with stops", how="🚐 Guided tour, hotel pickup ~6:30–7:00 AM"),
    dict(id="maui_wailea", anchor="m-wailea", icon="🎂", title="Hotel → Hotel Wailea (birthday dinner)", days="Fri Nov 6",
         keys=["MCH", "WAILEA"], dest=["WAILEA"], plan="~15 min", how="🚕 Rideshare there, prebooked taxi back (~$30–50)"),
    dict(id="maui_haleakala", anchor="m-haleakala", icon="🌋", title="Hotel → Haleakalā summit (sunset)", days="Sat Nov 7",
         keys=["MCH", "KULA", "HALE"], dest=["HALE"], zmax=12, plan="2.5–3 h up, sea level → ~10,000 ft; back ~8 PM",
         how="🚐 Guided sunset tour, hotel pickup ~1:30 PM (entry + dinner included)"),
])

def island(name, emoji, dates, anchor, spec, base_note, hub_map_kw):
    hub = spec["hub"]
    out = [f'<a id="{anchor}"></a>\n## {emoji} {name} · {dates}\n', f"> **Home base: {L[hub].replace(' (hotel)', '')}.** {base_note}\n",
           f"### 🏨 The hotel\n\n{closeup(hub, hub=True)}\n",
           f"### 🗺️ Everything from the hotel\n",
           pair(f"{anchor}_hub", f"{name}: everything from the hotel (H)", **hub_map_kw), ""]
    # numbered table matching the hub pins
    rows = ["| Pin | Where | Day | From the hotel | Drive (no traffic) | Plan for | How | Section |", "|:-:|---|---|---:|---:|---|---|---|"]
    n = 0
    for k in hub_map_kw["keys"]:
        if k == hub: continue
        n += 1
        t = next((t for t in spec["trips"] if k in t["dest"] or k in t["keys"][1:2]), None)
        if k == "MOLOKINI":
            d, tm = "by boat from Māʻalaea", "~1 h by boat"
        elif t and t["keys"][-1] == k:
            r = RM.route(t["keys"]); d, tm = mi(r["dist_m"]), mins(r["dur_s"])
        else:
            d, tm = mi(M[hub][k]["dist_m"]), mins(M[hub][k]["dur_s"])
        plan, how = OWN_TEXT.get(k, (t["plan"], t["how"])) if t else ("", "")
        rows.append(f"| {n} | **{L[k]}** | {t['days'] if t else ''} | {d} | {tm} | {plan} | {how} | "
                    f"[{t['icon']} go]({'#' + t['anchor']}) |" if t else f"| {n} | **{L[k]}** | | {d} | {tm} | | | |")
    out += ["\n".join(rows), ""]
    for t in spec["trips"]:
        out += [f'<a id="{t["anchor"]}"></a>\n### {t["icon"]} {t["title"]}\n', f"**{t['days']}**\n",
                pair(t["id"], f"{t['days'].split(' (')[0]} · {t['title']}", keys=t["keys"] if t["keys"][-1] != t["keys"][0] else t["keys"][:-1],
                     routes=[t["keys"]], lines=t.get("lines", ()), hub=hub, zmax=t.get("zmax", 15)), "",
                trip_table(t["keys"], t["plan"], t["how"]), ""]
        if t["id"] == "maui_hana":
            r = RM.route(t["keys"]); cum = 0; rows = ["| Stop | From the hotel | Leg |", "|---|---:|---:|"]
            for i, leg in enumerate(r["legs"]):
                cum += leg["dist_m"]; rows.append(f"| {i+1}. **{L[t['keys'][i+1]]}** | {mi(cum)} | +{mi(leg['dist_m'])} · {mins(leg['dur_s'])} |")
            for k in t["keys"][1:]:
                la, lo = C[k]; dd = 0.0008
                RM.render(f"c_{k.lower()}_sat", L[k], keys=[k], extra_pts=[(la-dd, lo-dd), (la+dd, lo+dd)], W=900, H=560,
                          zmax=CLOSE_Z.get(k, 16), pad=40, style="sat")
            out += ["**The stops, in order from the hotel** (the tour's exact stops may differ):\n", "\n".join(rows), "",
                    " ".join(f'<img src="maps/c_{k.lower()}_sat.jpg" width="32%" alt="{L[k]}">' for k in t["keys"][1:]), "",
                    "<sub>" + " · ".join(f"{i}. {L[k]}" for i, k in enumerate(t["keys"][1:], 1)) + " (satellite, left to right)</sub>", ""]
        for k in t["dest"]:
            out += [f"**📍 {L[k]}**\n", closeup(k), ""]
    return "\n".join(out)

if __name__ == "__main__":
    for style in VIEWS:
        RM.render(f"00_islands_{style}", "Big picture: Oʻahu → Maui island hop (HNL → OGG)", keys=["HNL", "REEF", "OGG", "MCH"],
                  lines=[("HNL", "OGG", "flight ~100 mi · ~40 min")], zmax=9, pad=120, style=style, lpos={"HNL": "above", "REEF": "below"})
    oahu_kw = dict(keys=["REEF", "HNL", "DH", "PH", "BISHOP"], routes=[["REEF", "HNL"], ["REEF", "DH"], ["REEF", "PH"], ["REEF", "BISHOP"]],
                   hub="REEF", zmax=13)
    maui_kw = dict(keys=["MCH", "OGG", "MAALAEA", "MOLOKINI", "HANA", "WAILEA", "HALE"],
                   routes=[["MCH", "OGG"], ["MCH", "MAALAEA"], MAUI["trips"][2]["keys"], ["MCH", "WAILEA"], ["MCH", "KULA", "HALE"]],
                   lines=[("MAALAEA", "MOLOKINI", "boat")], hub="MCH", zmax=11, pad=70, lpos={"OGG": "above", "MAALAEA": "left"})
    oahu = island("Oʻahu", "🌺", "Oct 31 – Nov 3", "oahu", OAHU,
                  "No car: rideshare, taxi, transfers. Everything is within ~12 miles. Every ride in detail: [`commute.md`](commute.md).",
                  oahu_kw)
    maui = island("Maui", "🌋", "Nov 3 – Nov 8", "maui", MAUI,
                  "No car: airport shuttle, tours with hotel pickup (Hāna, Haleakalā), a dawn taxi to the Molokini boat, rideshare to dinner. Every ride in detail: [`commute.md`](commute.md).",
                  maui_kw)
    toc = ["- [Big picture](#big)",
           "- [🌺 Oʻahu · from OUTRIGGER Reef](#oahu)"] + [f"  - [{t['icon']} {t['title']}](#{t['anchor']})" for t in OAHU["trips"]] + \
          ["- [🌋 Maui · from Maui Coast Hotel](#maui)"] + [f"  - [{t['icon']} {t['title']}](#{t['anchor']})" for t in MAUI["trips"]] + \
          ["- [How to update the maps](#update)"]
    md = f"""# 🗺️ Trip map: everything from the hotel

> Each island is laid out around **our hotel (the red H)**: one map with every place we go, then one section per trip out of the hotel, in day order.
> Every view comes as a **normal map** (left) and a **satellite view** (right). Pins are numbered to match the tables; click any map to enlarge it.
> Distances and no-traffic drive times: OSRM (OpenStreetMap routing). **"Plan for"** is the realistic time. **No car**: how we get there is in each table; details in [`commute.md`](commute.md).
> Generated 2026-10-18.

## 📑 Contents

{chr(10).join(toc)}

<a id="big"></a>
## ✈️ Big picture

<img src="maps/00_islands_street.jpg" width="49%" alt="Oʻahu to Maui (map)"> <img src="maps/00_islands_sat.jpg" width="49%" alt="Oʻahu to Maui (satellite)">

| Hop | Distance | Time |
|---|---:|---:|
| ✈️ JFK → HNL (Oct 31) | ~4,980 mi | ~11 h nonstop |
| ✈️ HNL → OGG (Nov 3) | ~100 mi | ~40 min in the air; **4–6 h hotel to hotel** |
| ✈️ OGG → JFK (Nov 8 → 9) | ~4,950 mi | ~11–16 h with one stop |

---

{oahu}

---

{maui}

---

<a id="update"></a>
## 🔧 How to update the maps

```bash
cd maps/tools
python3 gen_md.py ../..   # re-renders the hotel-centred maps and rewrites map.md (needs Pillow; tiles cache in tiles/)
```

Places live in `places.py` + `coords.json`; trips are the `OAHU` / `MAUI` lists in `gen_md.py`.

**Credits:** normal maps: Esri World Street Map (Esri, HERE, Garmin, © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors); satellite imagery © Esri, Maxar, Earthstar Geographics. Routing: [OSRM](https://project-osrm.org). Twin Falls is placed approximately.
"""
    open(os.path.join(ROOT, "map.md"), "w").write(md)
    print("wrote map.md", len(md))
