"""Fetch OSRM routes + OpenTopoMap tiles and render terrain maps for the Hawaii trip."""
import json, math, os, sys, time, urllib.request
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from places import PLACES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]  # output dir for images
os.makedirs(OUT, exist_ok=True)
TILES = os.path.join(HERE, "tiles"); os.makedirs(TILES, exist_ok=True)
UA = {"User-Agent": "hawaii-trip-map/1.0 (personal trip planning, low volume)"}
C = {k: tuple(v) for k, v in json.load(open(os.path.join(HERE, "coords.json"))).items()}
LABEL = {k: v[0] for k, v in PLACES.items()}

F = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
FB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
def font(sz, bold=False):
    return ImageFont.truetype(F, sz)

# ---------- routing ----------
ROUTES_FILE = os.path.join(HERE, "routes.json")
ROUTES = json.load(open(ROUTES_FILE)) if os.path.exists(ROUTES_FILE) else {}
def route(keys):
    rid = ">".join(keys)
    if rid not in ROUTES:
        pts = ";".join(f"{C[k][1]},{C[k][0]}" for k in keys)
        url = f"https://router.project-osrm.org/route/v1/driving/{pts}?overview=full&geometries=geojson"
        r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
        rt = r["routes"][0]
        ROUTES[rid] = {"keys": keys, "dist_m": rt["distance"], "dur_s": rt["duration"],
                       "legs": [{"dist_m": l["distance"], "dur_s": l["duration"]} for l in rt["legs"]],
                       "coords": rt["geometry"]["coordinates"]}
        json.dump(ROUTES, open(ROUTES_FILE, "w"))
        time.sleep(1)
    return ROUTES[rid]

def hav_km(a, b):
    R = 6371; p = math.radians
    x = math.sin(p(b[0]-a[0])/2)**2 + math.cos(p(a[0]))*math.cos(p(b[0]))*math.sin(p(b[1]-a[1])/2)**2
    return 2*R*math.asin(math.sqrt(x))

# ---------- tiles ----------
def ll2px(lat, lon, z):
    n = 256 * 2**z
    x = (lon + 180) / 360 * n
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1+s)/(1-s)) / (4*math.pi)) * n
    return x, y

def tile(z, x, y):
    fn = os.path.join(TILES, f"{z}_{x}_{y}.png")
    if not os.path.exists(fn):
        sub = "abc"[(x+y) % 3]
        url = f"https://{sub}.tile.opentopomap.org/{z}/{x}/{y}.png"
        for attempt in range(3):
            try:
                data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
                open(fn, "wb").write(data); break
            except Exception as e:
                print("tile retry", z, x, y, e); time.sleep(2)
        else:
            return Image.new("RGB", (256, 256), (220, 230, 240))
        time.sleep(0.15)
    return Image.open(fn).convert("RGB")

def fit_zoom(pts, W, H, pad, zmax):
    for z in range(zmax, 3, -1):
        xs, ys = zip(*[ll2px(la, lo, z) for la, lo in pts])
        if max(xs)-min(xs) <= W-2*pad and max(ys)-min(ys) <= H-2*pad:
            return z
    return 4

def basemap(center_px, z, W, H):
    cx, cy = center_px
    x0, y0 = cx - W/2, cy - H/2
    img = Image.new("RGB", (W, H))
    for tx in range(int(x0//256), int((x0+W)//256)+1):
        for ty in range(int(y0//256), int((y0+H)//256)+1):
            if 0 <= ty < 2**z:
                img.paste(tile(z, tx % 2**z, ty), (int(tx*256 - x0), int(ty*256 - y0)))
    return img, x0, y0

# ---------- drawing ----------
COL = ["#d62828", "#1d4ed8", "#7c3aed", "#ea580c", "#0f766e"]

def halo_text(d, xy, text, f, fill="#111", anchor="la"):
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=4, stroke_fill="white")

def dashed(d, pts, fill, width, dash=14):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        L = math.hypot(x2-x1, y2-y1); n = max(1, int(L // dash))
        for i in range(0, n, 2):
            a, b = i/n, min(1, (i+1)/n)
            d.line([(x1+(x2-x1)*a, y1+(y2-y1)*a), (x1+(x2-x1)*b, y1+(y2-y1)*b)], fill=fill, width=width)

def scale_bar(d, lat, z, W, H):
    mpp = 156543.03392 * math.cos(math.radians(lat)) / 2**z  # metres per pixel
    for miles in [0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 50, 100]:
        px = miles*1609.34/mpp
        if px > W*0.18: break
    x, y = 20, H - 46
    d.rectangle([x-8, y-26, x+px+70, y+14], fill=(255, 255, 255, 215))
    d.line([(x, y), (x+px, y)], fill="#111", width=4)
    for xx in (x, x+px): d.line([(xx, y-8), (xx, y+4)], fill="#111", width=3)
    d.text((x, y-24), f"{miles:g} mi  ({miles*1.609:.1f} km)", font=font(15), fill="#111")

def render(name, title, keys=(), routes=(), lines=(), W=1200, H=800, zmax=15, pad=90, extra_pts=(), lpos=None):
    lpos = lpos or {}
    """routes: list of key lists (driven); lines: list of (keyA, keyB, label) straight dashed (boat/flight)."""
    geoms = [route(list(r)) for r in routes]
    pts = [C[k] for k in keys] + [tuple(p) for p in extra_pts]
    for g in geoms: pts += [(la, lo) for lo, la in g["coords"][::5]]
    for a, b, _ in lines: pts += [C[a], C[b]]
    z = fit_zoom(pts, W, H, pad, zmax)
    xs, ys = zip(*[ll2px(la, lo, z) for la, lo in pts])
    img, x0, y0 = basemap(((max(xs)+min(xs))/2, (max(ys)+min(ys))/2), z, W, H)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    P = lambda la, lo: (ll2px(la, lo, z)[0]-x0, ll2px(la, lo, z)[1]-y0)
    for i, g in enumerate(geoms):
        line = [P(la, lo) for lo, la in g["coords"]]
        d.line(line, fill="white", width=10, joint="curve")
        d.line(line, fill=COL[i % len(COL)], width=6, joint="curve")
    for a, b, lab in lines:
        pa, pb = P(*C[a]), P(*C[b])
        dashed(d, [pa, pb], "white", 9); dashed(d, [pa, pb], "#0369a1", 5)
        mx, my = (pa[0]+pb[0])/2, (pa[1]+pb[1])/2
        halo_text(d, (mx+14, my+26), lab, font(18), fill="#0369a1", anchor="lm")
    for n, k in enumerate(keys, 1):
        x, y = P(*C[k])
        d.ellipse([x-15, y-15, x+15, y+15], fill="#111", outline="white", width=3)
        d.text((x, y), str(n), font=font(16), fill="white", anchor="mm")
        f19 = font(19); tw = d.textlength(LABEL[k], font=f19)
        pos = lpos.get(k, "right")
        if pos == "right" and x + 20 + tw > W - 10: pos = "left"
        if pos == "left" and x - 20 - tw < 10: pos = "below"
        xy, anc = {"right": ((x+20, y), "lm"), "left": ((x-20, y), "rm"),
                   "above": ((x, y-20), "mb"), "below": ((x, y+20), "mt")}[pos]
        if anc in ("mb", "mt"):  # keep centred labels inside the frame
            xy = (min(max(xy[0], tw/2 + 10), W - tw/2 - 10), xy[1])
        halo_text(d, xy, LABEL[k], f19, anchor=anc)
    # title + attribution
    d.rectangle([0, 0, W, 46], fill=(255, 255, 255, 225))
    d.text((16, 23), title, font=font(24), fill="#111", anchor="lm")
    scale_bar(d, (min(p[0] for p in pts)+max(p[0] for p in pts))/2, z, W, H)
    att = "Map: © OpenStreetMap contributors, SRTM | style © OpenTopoMap (CC-BY-SA) | routes: OSRM"
    d.rectangle([W-560, H-24, W, H], fill=(255, 255, 255, 200))
    d.text((W-8, H-12), att, font=font(13), fill="#333", anchor="rm")
    out = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    out.save(os.path.join(OUT, name + ".jpg"), quality=84, optimize=True)
    print("saved", name, "z", z)

# ---------- the trip ----------
OAHU_LEGS = [["HNL", "REEF"], ["REEF", "DH"], ["REEF", "PH", "BISHOP", "REEF"], ["REEF", "HNL"]]
MAUI_LEGS = [["OGG", "MCH"], ["MCH", "MAALAEA"], ["MCH", "PAIA", "HOOKIPA", "TWIN", "KEANAE", "WAI", "HANA"],
             ["MCH", "WAILEA"], ["MCH", "KULA", "HALE"], ["MCH", "OGG"]]

if __name__ == "__main__":
    render("00_islands_flight", "Big picture: Oʻahu → Maui island hop (HNL → OGG)",
           keys=["HNL", "REEF", "OGG", "MCH"], lines=[("HNL", "OGG", "flight ~100 mi · ~40 min")], zmax=9, pad=120,
           lpos={"HNL": "above", "REEF": "below"})
    render("01_oahu_overview", "Oʻahu overview: airport, Waikīkī hotel, Diamond Head, Pearl Harbor",
           keys=["HNL", "REEF", "DH", "PH", "BISHOP"], routes=[["HNL", "REEF"], ["REEF", "DH"], ["REEF", "PH"]], zmax=13)
    render("02_maui_overview", "Maui overview: every stop on the plan",
           keys=["OGG", "COSTCO", "MCH", "MAALAEA", "MOLOKINI", "PAIA", "HOOKIPA", "TWIN", "KEANAE", "WAI", "HANA", "WAILEA", "KULA", "HALE"],
           routes=[["OGG", "MCH"], ["MCH", "PAIA", "HOOKIPA", "TWIN", "KEANAE", "WAI", "HANA"], ["MCH", "KULA", "HALE"]],
           lines=[("MAALAEA", "MOLOKINI", "boat")], zmax=11, pad=70,
           lpos={"OGG": "above", "PAIA": "below", "COSTCO": "left", "MAALAEA": "below", "KULA": "right"})
    # per day
    render("d1_oct31", "Sat Oct 31 · HNL airport → OUTRIGGER Reef, Waikīkī", keys=["HNL", "REEF"], routes=[["HNL", "REEF"]])
    render("d2_nov01", "Sun Nov 1 · Hotel → Diamond Head", keys=["REEF", "DH"], routes=[["REEF", "DH"]])
    render("d3_nov02", "Mon Nov 2 · Hotel → Pearl Harbor → (Bishop Museum) → Hotel", keys=["REEF", "PH", "BISHOP"],
           routes=[["REEF", "PH", "BISHOP", "REEF"]])
    render("d4_nov03_oahu", "Tue Nov 3 · Hotel → HNL airport", keys=["REEF", "HNL"], routes=[["REEF", "HNL"]])
    render("d4_nov03_maui", "Tue Nov 3 · OGG airport → Maui Coast Hotel, Kīhei (shuttle / rideshare)", keys=["OGG", "MCH"],
           routes=[["OGG", "MCH"]])
    render("d5_nov04", "Wed Nov 4 · Taxi to Māʻalaea Harbor → boat to Molokini", keys=["MCH", "MAALAEA", "MOLOKINI"],
           routes=[["MCH", "MAALAEA"]], lines=[("MAALAEA", "MOLOKINI", "boat ~1 h each way")], zmax=13)
    render("d6_nov05", "Thu Nov 5 · Road to Hāna (tour route)", keys=["MCH", "PAIA", "HOOKIPA", "TWIN", "KEANAE", "WAI", "HANA"],
           routes=[["MCH", "PAIA", "HOOKIPA", "TWIN", "KEANAE", "WAI", "HANA"]], zmax=12, pad=70)
    render("d7_nov06", "Fri Nov 6 (birthday) · Rideshare to Hotel Wailea (birthday dinner)", keys=["MCH", "WAILEA"], routes=[["MCH", "WAILEA"]])
    render("d8_nov07", "Sat Nov 7 · Haleakalā sunset tour (hotel pickup) via Kula", keys=["MCH", "KULA", "HALE"],
           routes=[["MCH", "KULA", "HALE"]], zmax=12)
    render("d9_nov08", "Sun Nov 8 · Hotel → OGG airport (shuttle / rideshare)", keys=["MCH", "OGG"], routes=[["MCH", "OGG"]])
    # every location, close up
    CLOSE_Z = {"MOLOKINI": 15, "HANA": 15, "PAIA": 15, "KULA": 14, "KEANAE": 15, "HALE": 15, "HNL": 14, "OGG": 14, "DH": 15, "PH": 15}
    for k in PLACES:
        la, lo = C[k]; dd = 0.0008
        render(f"loc_{k.lower()}", LABEL[k], keys=[k], extra_pts=[(la-dd, lo-dd), (la+dd, lo+dd)],
               W=900, H=560, zmax=CLOSE_Z.get(k, 16), pad=40)
    # summary of every leg for the markdown
    summary = {}
    for legs in OAHU_LEGS + MAUI_LEGS:
        r = route(legs); summary[">".join(legs)] = {k: r[k] for k in ("keys", "dist_m", "dur_s", "legs")}
    json.dump({"summary": summary, "coords": C}, open(os.path.join(HERE, "summary.json"), "w"), indent=1)
    print("done")
