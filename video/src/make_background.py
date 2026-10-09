"""Background + thumbnail for 'The Hunt for Bin Laden': dark map of Afghanistan/Pakistan with escape and raid routes."""
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, sys.argv[4])  # tools dir with owl.py
from owl import make_owl

W, H, SS = 1920, 1080, 2
LON0, LAT0 = 71.4, 33.2
SCALE = 260.0 * SS

BG = (12, 17, 28)
LAND = (38, 44, 58)
BORDER = (18, 22, 32)
AFG = (104, 62, 150)
PAK = (40, 112, 120)
FB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FBLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"

PLACES = {"TORA BORA": (70.22, 34.12), "JALALABAD": (70.45, 34.43), "ABBOTTABAD": (73.24, 34.17),
          "KABUL": (69.17, 34.53), "ISLAMABAD": (73.05, 33.69)}

def proj(lon, lat):
    k = math.cos(math.radians(LAT0))
    return W * SS / 2 + (lon - LON0) * k * SCALE, H * SS / 2 - (lat - LAT0) * SCALE

def polys(g): return [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]

def dashed(d, a, b, col, width, dash=26, gap=18, bend=0.0):
    (x0, y0), (x1, y1) = a, b
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    cx, cy = mx + nx * bend, my + ny * bend
    pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1)
           for t in np.linspace(0, 1, 400)]
    acc = 0; on = True; seg = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        acc += math.dist(p, q)
        if on: seg.append(q)
        if acc >= (dash if on else gap) * SS:
            if on: d.line(seg, fill=col, width=width, joint="curve")
            on = not on; acc = 0; seg = [q]
    if on and len(seg) > 1: d.line(seg, fill=col, width=width)
    # arrow head at end
    (px, py), (qx, qy) = pts[-12], pts[-1]
    ang = math.atan2(qy - py, qx - px); L = 34 * SS
    d.polygon([(qx, qy), (qx - L * math.cos(ang - 0.45), qy - L * math.sin(ang - 0.45)),
               (qx - L * math.cos(ang + 0.45), qy - L * math.sin(ang + 0.45))], fill=col)
    return pts[len(pts) // 2]

def label(d, xy, text, size, fill="white", anchor="lm"):
    d.text(xy, text, font=ImageFont.truetype(FB, size * SS), fill=fill, stroke_width=5 * SS, stroke_fill=(0, 0, 0), anchor=anchor)

def render(path, with_text):
    feats = json.load(open(sys.argv[1]))["features"]
    im = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(im)
    for lon in np.arange(60, 85, 0.5):
        d.line([proj(lon, 20), proj(lon, 45)], fill=(17, 24, 38), width=2 * SS)
    for lat in np.arange(25, 42, 0.5):
        d.line([proj(50, lat), proj(90, lat)], fill=(17, 24, 38), width=2 * SS)
    for f in feats:
        c = f["properties"]["ADM0_A3"]
        col = AFG if c == "AFG" else PAK if c == "PAK" else LAND
        for poly in polys(f["geometry"]):
            d.polygon([proj(*p) for p in poly[0]], fill=col, outline=BORDER, width=4 * SS)
    # target glow at Abbottabad
    ax, ay = proj(*PLACES["ABBOTTABAD"])
    glow = Image.new("L", im.size, 0)
    ImageDraw.Draw(glow).ellipse((ax - 150 * SS, ay - 150 * SS, ax + 150 * SS, ay + 150 * SS), fill=200)
    glow = glow.filter(ImageFilter.GaussianBlur(70 * SS))
    im = Image.composite(Image.new("RGB", im.size, (255, 60, 40)), im, glow)
    d = ImageDraw.Draw(im)
    # routes
    m1 = dashed(d, proj(*PLACES["TORA BORA"]), proj(*PLACES["ABBOTTABAD"]), (255, 90, 80), 9 * SS, bend=0.18)
    m2 = dashed(d, proj(*PLACES["JALALABAD"]), proj(*PLACES["ABBOTTABAD"]), (120, 200, 255), 9 * SS, bend=-0.22)
    # crosshair target
    for r in (70, 46):
        d.ellipse((ax - r * SS, ay - r * SS, ax + r * SS, ay + r * SS), outline=(255, 70, 60), width=6 * SS)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.line([(ax + dx * 30 * SS, ay + dy * 30 * SS), (ax + dx * 95 * SS, ay + dy * 95 * SS)], fill=(255, 70, 60), width=6 * SS)
    d.ellipse((ax - 11 * SS, ay - 11 * SS, ax + 11 * SS, ay + 11 * SS), fill="white", outline="black", width=3 * SS)
    # place dots + labels
    for name in ("TORA BORA", "JALALABAD", "KABUL", "ISLAMABAD"):
        x, y = proj(*PLACES[name])
        d.ellipse((x - 9 * SS, y - 9 * SS, x + 9 * SS, y + 9 * SS), fill="white", outline="black", width=3 * SS)
    x, y = proj(*PLACES["TORA BORA"]); label(d, (x - 20 * SS, y + 26 * SS), "TORA BORA", 30, anchor="rm")
    x, y = proj(*PLACES["JALALABAD"]); label(d, (x + 18 * SS, y - 30 * SS), "JALALABAD", 26, (210, 225, 240))
    x, y = proj(*PLACES["KABUL"]); label(d, (x - 20 * SS, y), "KABUL", 26, (210, 225, 240), "rm")
    x, y = proj(*PLACES["ISLAMABAD"]); label(d, (x + 20 * SS, y + 4 * SS), "ISLAMABAD", 24, (210, 225, 240))
    label(d, (ax + 110 * SS, ay - 6 * SS), "ABBOTTABAD", 38)
    # route captions
    label(d, (m1[0], m1[1] + 48 * SS), "ESCAPE 2001", 28, (255, 120, 110), "mm")
    label(d, (m2[0], m2[1] - 44 * SS), "RAID 2011", 28, (150, 215, 255), "mm")
    # country names
    x, y = proj(69.4, 33.25); d.text((x, y), "AFGHANISTAN", font=ImageFont.truetype(FBLACK, 46 * SS), fill=(150, 115, 195), anchor="mm")
    x, y = proj(73.0, 32.75); d.text((x, y), "PAKISTAN", font=ImageFont.truetype(FBLACK, 46 * SS), fill=(80, 160, 165), anchor="mm")
    img = im.resize((W, H), Image.LANCZOS)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = np.asarray(img).astype(np.float32) * (1 - np.clip((r - 0.55) / 0.9, 0, 1) ** 1.5 * 0.75)[..., None]
    a += np.random.default_rng(7).normal(0, 4, a.shape)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if with_text:
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((60, 56, 410, 146), 22, fill=(10, 10, 14))
        d.text((235, 101), "2001 - 2011", font=ImageFont.truetype(FBLACK, 58), fill="white", anchor="mm")
        d.text((60, 820), "THE HUNT FOR", font=ImageFont.truetype(FBLACK, 110), fill="white", stroke_width=11, stroke_fill=(0, 0, 0), anchor="ls")
        d.text((50, 1010), "BIN LADEN", font=ImageFont.truetype(FBLACK, 185), fill=(255, 92, 80), stroke_width=16, stroke_fill=(0, 0, 0), anchor="ls")
        owl = make_owl(0.6, 0, 0.6, -0.6)
        owl = owl.resize((int(owl.width * 0.55), int(owl.height * 0.55)), Image.LANCZOS)
        img = img.convert("RGBA"); img.alpha_composite(owl, (W - owl.width + 20, H - owl.height + 10)); img = img.convert("RGB")
    img.save(path, quality=93)

render(sys.argv[2], False)
render(sys.argv[3], True)
print("ok")
