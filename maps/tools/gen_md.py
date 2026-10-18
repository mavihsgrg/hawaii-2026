"""Generate hawaii/map.md from coords/routes/matrix produced by render.py."""
import json, os, sys, math
from urllib.parse import quote
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from places import PLACES
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
C = {k: tuple(v) for k, v in json.load(open(os.path.join(HERE, "coords.json"))).items()}
R = json.load(open(os.path.join(HERE, "routes.json")))
M = json.load(open(os.path.join(HERE, "matrix.json")))
L = {k: v[0] for k, v in PLACES.items()}

mi = lambda m: f"{m/1609.34:.1f} mi"
mins = lambda s: f"{round(s/60)} min" if s < 5400 else f"{int(s//3600)} h {round(s%3600/60):02d} min"
ll = lambda k: f"{C[k][0]:.5f},{C[k][1]:.5f}"
def terrain(k, z=15): return f"https://www.google.com/maps/@?api=1&map_action=map&center={ll(k)}&zoom={z}&basemap=terrain"
def sat(k, z=16): return f"https://www.google.com/maps/@?api=1&map_action=map&center={ll(k)}&zoom={z}&basemap=satellite"
def earth(k, d=2500): return f"https://earth.google.com/web/@{ll(k)},300a,{d}d,35y,0h,60t,0r"
def directions(keys):
    url = f"https://www.google.com/maps/dir/?api=1&origin={ll(keys[0])}&destination={ll(keys[-1])}&travelmode=driving"
    if len(keys) > 2: url += "&waypoints=" + quote("|".join(ll(k) for k in keys[1:-1]))
    return url

def leg_table(keys, plan):
    r = R[">".join(keys)]
    rows = ["| Leg | Distance | Drive (no traffic) | Plan for |", "|---|---:|---:|---|"]
    for i, leg in enumerate(r["legs"]):
        rows.append(f"| {L[keys[i]]} → {L[keys[i+1]]} | {mi(leg['dist_m'])} | {mins(leg['dur_s'])} | {plan[i] if i < len(plan) else ''} |")
    if len(r["legs"]) > 1:
        rows.append(f"| **Total** | **{mi(r['dist_m'])}** | **{mins(r['dur_s'])}** | |")
    return "\n".join(rows) + f"\n\n[▶ Open these directions in Google Maps]({directions(keys)})"

def geojson(keys, routes, lines=()):
    feats = []
    for k in keys:
        feats.append({"type": "Feature", "properties": {"title": L[k], "marker-color": "#d62828" if "hotel" in L[k] else "#111111"},
                      "geometry": {"type": "Point", "coordinates": [round(C[k][1], 5), round(C[k][0], 5)]}})
    for keysr in routes:
        co = R[">".join(keysr)]["coords"]; step = max(1, len(co)//160)
        co = co[::step] + [co[-1]]
        feats.append({"type": "Feature", "properties": {"title": " → ".join(L[k] for k in keysr), "stroke": "#1d4ed8", "stroke-width": 4},
                      "geometry": {"type": "LineString", "coordinates": [[round(x, 5), round(y, 5)] for x, y in co]}})
    for a, b, t in lines:
        feats.append({"type": "Feature", "properties": {"title": t, "stroke": "#0369a1"},
                      "geometry": {"type": "LineString", "coordinates": [[C[a][1], C[a][0]], [C[b][1], C[b][0]]]}})
    return "```geojson\n" + json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")) + "\n```"

def base_table(base, keys, notes):
    rows = [f"| Place | Drive from {L[base]} | Time (no traffic) | Live maps |", "|---|---:|---:|---|"]
    for k in keys:
        m = M[base][k]
        d, t = (mi(m["dist_m"]), mins(m["dur_s"])) if k not in notes else notes[k]
        rows.append(f"| [{L[k]}](#{k.lower()}) | {d} | {t} | [terrain]({terrain(k)}) · [satellite]({sat(k)}) · [3D]({earth(k)}) |")
    return "\n".join(rows)

def loc_section(k, extra=""):
    isl = "Oʻahu" if PLACES[k][4] == "oahu" else "Maui"
    return (f'<a id="{k.lower()}"></a>\n### {L[k]}\n\n![{L[k]}](maps/loc_{k.lower()}.jpg)\n\n'
            f"{isl} · `{ll(k)}` · [Google terrain]({terrain(k)}) · [satellite]({sat(k)}) · [Google Earth 3D]({earth(k)}){extra}\n")

OAHU_ALL = ["HNL", "REEF", "DH", "PH", "BISHOP"]
MAUI_ALL = ["OGG", "COSTCO", "MCH", "MAALAEA", "MOLOKINI", "PAIA", "HOOKIPA", "TWIN", "KEANAE", "WAI", "HANA", "WAILEA", "KULA", "HALE"]
hana = ["MCH", "PAIA", "HOOKIPA", "TWIN", "KEANAE", "WAI", "HANA"]

md = f"""# 🗺️ Trip map: every place, every drive

> Terrain snapshots of every place on the plan, from the airports onward, plus the drive between each stop.
> **Snapshots** (images) show the terrain: shaded relief, contour lines, forest, roads. **Live links** under each one open Google Maps terrain, satellite or Google Earth 3D.
> **Interactive maps** (the `geojson` blocks) render as zoomable maps on GitHub.
> Distances and no-traffic drive times come from OSRM (OpenStreetMap routing). **"Plan for"** is the realistic time from our research, with traffic, parking and the slow Hāna road. Generated 2026-10-18 for the decided plan (Oʻahu → Maui).

**Jump to:** [Big picture](#big) · [All distances](#all) · [Oʻahu](#oahu) · [Maui](#maui) · [Every location](#every) · [How to update](#update)

<a id="big"></a>
## Big picture

![Oʻahu to Maui](maps/00_islands_flight.jpg)

| Hop | Distance | Time |
|---|---:|---:|
| ✈️ JFK → HNL (Oct 31) | ~4,980 mi | ~11 h nonstop |
| ✈️ HNL → OGG (Nov 3) | ~100 mi (straight line) | ~40 min in the air; plan **4–6 h door to door** |
| ✈️ OGG → JFK (Nov 8 → 9) | ~4,950 mi | ~11–16 h with one stop |

<a id="all"></a>
## All distances at a glance

| Day | Route | Distance | Drive (no traffic) | Plan for | How |
|---|---|---:|---:|---|---|
| Sat Oct 31 | HNL → OUTRIGGER Reef | {mi(R['HNL>REEF']['dist_m'])} | {mins(R['HNL>REEF']['dur_s'])} | 30–45 min (traffic + bags) | Prebooked transfer |
| Sun Nov 1 | Hotel → Diamond Head | {mi(R['REEF>DH']['dist_m'])} | {mins(R['REEF>DH']['dur_s'])} | 15–20 min | Rideshare |
| Mon Nov 2 | Hotel → Pearl Harbor | {mi(R['REEF>PH>BISHOP>REEF']['legs'][0]['dist_m'])} | {mins(R['REEF>PH>BISHOP>REEF']['legs'][0]['dur_s'])} | 30–40 min (H-1 traffic) | Rideshare |
| Mon Nov 2 | Pearl Harbor → Bishop Museum → Hotel | {mi(R['REEF>PH>BISHOP>REEF']['legs'][1]['dist_m']+R['REEF>PH>BISHOP>REEF']['legs'][2]['dist_m'])} | {mins(R['REEF>PH>BISHOP>REEF']['legs'][1]['dur_s']+R['REEF>PH>BISHOP>REEF']['legs'][2]['dur_s'])} | 30–45 min | Rideshare |
| Tue Nov 3 | Hotel → HNL | {mi(R['REEF>HNL']['dist_m'])} | {mins(R['REEF>HNL']['dur_s'])} | leave ~2.5 h before the flight | Transfer |
| Tue Nov 3 | OGG → Costco → Maui Coast Hotel | {mi(R['OGG>COSTCO>MCH']['dist_m'])} | {mins(R['OGG>COSTCO>MCH']['dur_s'])} | 1–1.5 h incl. car pickup + shop | 🚗 Rental car |
| Wed Nov 4 | Hotel → Māʻalaea Harbor | {mi(R['MCH>MAALAEA']['dist_m'])} | {mins(R['MCH>MAALAEA']['dur_s'])} | 25–40 min; check in 45 min early | 🚗 |
| Wed Nov 4 | Māʻalaea → Molokini | ~11 mi by sea | — | ~1 h each way, ~5 h trip | 🚤 PacWhale |
| Thu Nov 5 | Hotel → Hāna (all stops) | {mi(R['>'.join(hana)]['dist_m'])} one way | {mins(R['>'.join(hana)]['dur_s'])} | **10–12 h round-trip day** | 🚐 Guided tour |
| Fri Nov 6 🎂 | Hotel → Hotel Wailea | {mi(R['MCH>WAILEA']['dist_m'])} | {mins(R['MCH>WAILEA']['dur_s'])} | 15 min (rideshare if drinking) | 🚗 / rideshare |
| Sat Nov 7 | Hotel → Kula → Haleakalā summit | {mi(R['MCH>KULA>HALE']['dist_m'])} | {mins(R['MCH>KULA>HALE']['dur_s'])} | **2.5–3 h + gate queue** (NPS) | 🚗 |
| Sun Nov 8 | Hotel → OGG | {mi(R['MCH>OGG']['dist_m'])} | {mins(R['MCH>OGG']['dur_s'])} | 30–45 min + car return | 🚗 |

---

<a id="oahu"></a>
## Oʻahu (Oct 31 – Nov 3)

No car: transfer + rideshares. Everything is within ~12 miles of the hotel.

![Oʻahu overview](maps/01_oahu_overview.jpg)

**Interactive map** (zoom and click the pins on GitHub):

{geojson(OAHU_ALL, [["HNL","REEF"], ["REEF","DH"], ["REEF","PH","BISHOP","REEF"]])}

### From the hotel to everything on Oʻahu

{base_table("REEF", ["HNL","DH","PH","BISHOP"], {})}

### Sat Oct 31: airport → hotel

![Oct 31](maps/d1_oct31.jpg)

{leg_table(["HNL","REEF"], ["30–45 min with bags and traffic; prebook the transfer"])}

### Sun Nov 1: Diamond Head

![Nov 1](maps/d2_nov01.jpg)

{leg_table(["REEF","DH"], ["15–20 min by rideshare; the trail climbs ~560 ft from the crater floor to the rim"])}

### Mon Nov 2: Pearl Harbor (+ optional Bishop Museum)

![Nov 2](maps/d3_nov02.jpg)

{leg_table(["REEF","PH","BISHOP","REEF"], ["30–40 min in morning traffic; be there an hour before the program", "15–20 min", "15–25 min"])}

### Tue Nov 3: hotel → HNL

![Nov 3 Oʻahu](maps/d4_nov03_oahu.jpg)

{leg_table(["REEF","HNL"], ["Leave ~2.5 h before the island hop"])}

---

<a id="maui"></a>
## Maui (Nov 3 – 8)

Rental car from OGG, based in Kīhei. Hāna is a guided tour; everything else is a self-drive.

![Maui overview](maps/02_maui_overview.jpg)

**Interactive map:**

{geojson(MAUI_ALL, [["OGG","COSTCO","MCH"], ["MCH","MAALAEA"], hana, ["MCH","WAILEA"], ["MCH","KULA","HALE"]], [("MAALAEA","MOLOKINI","Boat to Molokini")])}

### From the hotel to everything on Maui

{base_table("MCH", ["OGG","COSTCO","MAALAEA","MOLOKINI","WAILEA","KULA","HALE","PAIA","HOOKIPA","TWIN","KEANAE","WAI","HANA"], {"MOLOKINI": ("by boat from Māʻalaea", "~1 h by boat")})}

### Tue Nov 3: OGG → groceries → hotel

![Nov 3 Maui](maps/d4_nov03_maui.jpg)

{leg_table(["OGG","COSTCO","MCH"], ["Car pickup takes 30–45 min first", "Plus shopping time"])}

### Wed Nov 4: Molokini snorkel

![Nov 4](maps/d5_nov04.jpg)

{leg_table(["MCH","MAALAEA"], ["25–40 min; check in 45 min before departure"])}

Then about 11 miles by boat to Molokini, a sunken crater rim in the ʻAlalākeiki Channel. Around 5 hours in total, with Turtle Arches on the way back.

### Thu Nov 5: Road to Hāna (guided tour)

![Nov 5](maps/d6_nov05.jpg)

{leg_table(hana, ["~40 min", "5–10 min", "20–30 min: the winding section starts around here", "45–60 min", "60–75 min", "10 min"])}

The road has 59 bridges (many single-lane) and 600+ curves; the routing engine's no-traffic time badly understates it. With stops it's a **10–12 hour round trip**, which is why it's a guided tour. The tour route may differ from the one shown.

### Fri Nov 6 🎂: birthday dinner

![Nov 6](maps/d7_nov06.jpg)

{leg_table(["MCH","WAILEA"], ["15 min; take a rideshare if you're drinking"])}

### Sat Nov 7: Haleakalā sunset

![Nov 7](maps/d8_nov07.jpg)

{leg_table(["MCH","KULA","HALE"], ["~50 min to Upcountry", "60–75 min of switchbacks, sea level → 9,740 ft"])}

You climb from sea level to **~10,000 ft** in about 50 miles: dozens of switchbacks above Kula, ~35–45 °F with wind at sunset, then the drive down in the dark. NPS says to allow **~3 hours from Wailea** and to arrive 3 hours before sunset.

### Sun Nov 8: hotel → OGG

![Nov 8](maps/d9_nov08.jpg)

{leg_table(["MCH","OGG"], ["30–45 min; fill up the tank and allow time for the car return"])}

---

<a id="every"></a>
## Every location, close up

Terrain close-ups of each place, in trip order. Click through for live maps.

#### Oʻahu
""" + "\n".join(loc_section(k) for k in OAHU_ALL) + "\n#### Maui\n" + "\n".join(loc_section(k) for k in MAUI_ALL) + """
---

<a id="update"></a>
## How to update the maps

The map images and this file are generated by `maps/tools/`:

```bash
cd maps/tools
python3 render.py ..          # re-renders every image in maps/ (needs Pillow; tiles are cached in tiles/, not committed)
python3 gen_md.py ../..       # rewrites map.md
```

Add a place in `places.py` (+ its coordinates in `coords.json`), then add it to the lists in `render.py` / `gen_md.py`.

**Credits:** map tiles © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, SRTM | map style © [OpenTopoMap](https://opentopomap.org) (CC-BY-SA). Routing by [OSRM](https://project-osrm.org). Coordinates from OSM Nominatim. Twin Falls is placed approximately.
"""
open(os.path.join(OUT, "map.md"), "w").write(md)
print("wrote", len(md), "chars")
