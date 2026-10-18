"""Render the Waikīkī and Oʻahu basemaps for the hotel map (Esri street tiles), plus their bounds, so pins can be placed on them."""
import json, math, os, time, urllib.request
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..")
TILES = os.path.join(HERE, "tiles"); os.makedirs(TILES, exist_ok=True)
UA = {"User-Agent": "hawaii-trip-map/1.0 (personal trip planning, low volume)"}
URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"

def ll2px(lat, lon, z):
    n = 256 * 2**z
    s = math.sin(math.radians(lat))
    return (lon + 180) / 360 * n, (0.5 - math.log((1+s)/(1-s)) / (4*math.pi)) * n

def tile(z, x, y):
    fn = os.path.join(TILES, f"estreet_{z}_{x}_{y}.jpg")
    if not os.path.exists(fn):
        data = urllib.request.urlopen(urllib.request.Request(URL.format(z=z, x=x, y=y), headers=UA), timeout=30).read()
        open(fn, "wb").write(data); time.sleep(0.15)
    return Image.open(fn).convert("RGB")

def render(name, north, south, west, east, z):
    x0, y0 = ll2px(north, west, z); x1, y1 = ll2px(south, east, z)
    W, H = int(x1 - x0), int(y1 - y0)
    img = Image.new("RGB", (W, H))
    for tx in range(int(x0 // 256), int(x1 // 256) + 1):
        for ty in range(int(y0 // 256), int(y1 // 256) + 1):
            img.paste(tile(z, tx, ty), (int(tx*256 - x0), int(ty*256 - y0)))
    img = ImageEnhance.Color(img).enhance(0.55)  # mute the basemap so the pins carry the color
    img.save(os.path.join(OUT, name + ".jpg"), quality=80, optimize=True)
    json.dump({"z": z, "x0": x0, "y0": y0, "w": W, "h": H, "north": north, "south": south, "west": west, "east": east},
              open(os.path.join(HERE, name + ".json"), "w"), indent=1)
    print("saved", name, W, H)

if __name__ == "__main__":
    render("map_waikiki", 21.2885, 21.2605, -157.8425, -157.8180, 16)
    render("map_oahu", 21.72, 21.24, -158.30, -157.64, 11)
