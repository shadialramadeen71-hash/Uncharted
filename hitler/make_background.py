"""Background / thumbnail for a 'Fall of Hitler' video: dark Europe map, spring 1945."""
import json, math, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, SS = 1920, 1080, 2
LON0, LAT0 = 6.4, 51.1           # map centre (puts Berlin right of centre)
SCALE = 42.0 * SS                # px per degree of latitude
BERLIN = (13.40, 52.52)

BG = (12, 17, 28)
LAND = (38, 44, 58)
BORDER = (20, 24, 34)
RED = (176, 40, 34)
PURPLE = (104, 62, 150)
BLUE = (40, 112, 170)
NEUTRAL = (70, 76, 90)

GROUPS = {
    RED: {"DEU", "AUT"},
    PURPLE: {"RUS", "UKR", "BLR", "LTU", "LVA", "EST", "MDA", "POL", "ROU", "BGR", "HUN", "SVK", "CZE"},
    BLUE: {"GBR", "FRA", "BEL", "NLD", "LUX", "ITA", "DNK"},
    NEUTRAL: {"ESP", "PRT", "CHE", "SWE", "IRL", "TUR", "LIE"},
}

def proj(lon, lat):
    k = math.cos(math.radians(LAT0))
    x = W * SS / 2 + (lon - LON0) * k * SCALE
    y = H * SS / 2 - (lat - LAT0) * SCALE * 1.18  # mild stretch toward a conformal look
    return x, y

def polys(geom):
    if geom["type"] == "Polygon": return [geom["coordinates"]]
    return geom["coordinates"]

def render(path, with_text):
    feats = json.load(open(sys.argv[1]))["features"]
    base = Image.new("RGB", (W * SS, H * SS), BG)
    # faint grid lines
    d = ImageDraw.Draw(base)
    for lon in range(-40, 70, 5):
        d.line([proj(lon, 20), proj(lon, 75)], fill=(18, 25, 40), width=2 * SS)
    for lat in range(25, 75, 5):
        d.line([proj(-40, lat), proj(70, lat)], fill=(18, 25, 40), width=2 * SS)
    red_mask = Image.new("L", base.size, 0)
    rm = ImageDraw.Draw(red_mask)
    for f in feats:
        code = f["properties"]["ADM0_A3"]
        col = next((c for c, s in GROUPS.items() if code in s), LAND)
        for poly in polys(f["geometry"]):
            pts = [proj(*p) for p in poly[0]]
            d.polygon(pts, fill=col, outline=BORDER, width=3 * SS)
            if col == RED: rm.polygon(pts, fill=255)
    # glow around Germany
    glow = red_mask.filter(ImageFilter.GaussianBlur(40 * SS))
    glow_rgb = Image.new("RGB", base.size, (255, 70, 40))
    base = Image.composite(glow_rgb, base, glow.point(lambda v: int(v * 0.35)))
    # redraw germany crisp on top of glow
    for f in feats:
        if f["properties"]["ADM0_A3"] in GROUPS[RED]:
            for poly in polys(f["geometry"]):
                ImageDraw.Draw(base).polygon([proj(*p) for p in poly[0]], fill=RED, outline=(90, 15, 12), width=3 * SS)
    # cracks radiating from Berlin, clipped to the red area
    random.seed(1945)
    cracks = Image.new("L", base.size, 0)
    cd = ImageDraw.Draw(cracks)
    bx, by = proj(*BERLIN)
    def crack(x, y, ang, length, width, depth):
        steps = int(length / (14 * SS))
        pts = [(x, y)]
        for _ in range(steps):
            ang += random.uniform(-0.45, 0.45)
            x += math.cos(ang) * 14 * SS; y += math.sin(ang) * 14 * SS
            pts.append((x, y))
            if depth < 2 and random.random() < 0.07:
                crack(x, y, ang + random.choice([-1, 1]) * random.uniform(0.5, 1.1), length * 0.45, max(2, width * 0.6), depth + 1)
        cd.line(pts, fill=255, width=int(width), joint="curve")
    for a in np.linspace(0, 2 * math.pi, 11, endpoint=False):
        crack(bx, by, a + random.uniform(-0.25, 0.25), random.uniform(300, 650) * SS, 4 * SS, 0)
    cracks = Image.composite(cracks, Image.new("L", base.size, 0), red_mask.filter(ImageFilter.MinFilter(9)))
    cglow = cracks.filter(ImageFilter.GaussianBlur(10 * SS))
    base = Image.composite(Image.new("RGB", base.size, (255, 190, 120)), base, cglow.point(lambda v: min(255, v * 2)))
    base = Image.composite(Image.new("RGB", base.size, (255, 245, 225)), base, cracks)
    # Berlin marker
    d = ImageDraw.Draw(base)
    for r, a in ((60, 60), (40, 110), (22, 255)):
        ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse((bx - r * SS, by - r * SS, bx + r * SS, by + r * SS), outline=(255, 255, 255, a), width=4 * SS)
        base = Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(base)
    d.ellipse((bx - 10 * SS, by - 10 * SS, bx + 10 * SS, by + 10 * SS), fill="white", outline=(0, 0, 0), width=3 * SS)
    fb = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", 34 * SS)
    d.text((bx + 26 * SS, by - 4 * SS), "BERLIN", font=fb, fill="white", stroke_width=5 * SS, stroke_fill=(0, 0, 0), anchor="lm")
    img = base.resize((W, H), Image.LANCZOS)
    # vignette + grain
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    vig = 1 - np.clip((r - 0.55) / 0.9, 0, 1) ** 1.5 * 0.75
    a = np.asarray(img).astype(np.float32) * vig[..., None]
    a += np.random.default_rng(7).normal(0, 4, a.shape)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if with_text:
        d = ImageDraw.Draw(img)
        fblack = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
        d.rounded_rectangle((70, 70, 330, 160), 22, fill=(10, 10, 14))
        d.text((200, 115), "1945", font=ImageFont.truetype(fblack, 76), fill="white", anchor="mm")
        d.text((60, 820), "THE FALL", font=ImageFont.truetype(fblack, 170), fill=(255, 92, 80), stroke_width=15, stroke_fill=(0, 0, 0), anchor="ls")
        d.text((60, 990), "OF HITLER", font=ImageFont.truetype(fblack, 140), fill="white", stroke_width=13, stroke_fill=(0, 0, 0), anchor="ls")
    img.save(path, quality=93)

render(sys.argv[2], False)
render(sys.argv[3], True)
print("ok")
