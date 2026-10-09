"""RISE/FALL-style split thumbnail for the bin Laden video: 2001 HIDING | 2011 FOUND."""
import sys, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

src = open(sys.argv[5]).read()
src = src[:src.index("render(sys.argv[2], False)")]
exec(src)  # brings proj, dashed, label, PLACES, colours, etc.

def base_map(mode):
    global LON0, LAT0, SCALE
    LON0, LAT0 = (74.15, 34.39) if mode == "left" else (69.3, 34.44)
    SCALE = 150.0 * SS
    feats = json.load(open(sys.argv[1]))["features"]
    im = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(im)
    for f in feats:
        c = f["properties"]["ADM0_A3"]
        col = AFG if c == "AFG" else PAK if c == "PAK" else LAND
        if mode == "right":  # cooler palette on the 'found' side
            col = (40, 100, 160) if c == "AFG" else (34, 80, 110) if c == "PAK" else LAND
        for poly in polys(f["geometry"]):
            d.polygon([proj(*p) for p in poly[0]], fill=col, outline=BORDER, width=4 * SS)
    key = "TORA BORA" if mode == "left" else "ABBOTTABAD"
    kx, ky = proj(*PLACES[key])
    glow = Image.new("L", im.size, 0)
    ImageDraw.Draw(glow).ellipse((kx - 170 * SS, ky - 170 * SS, kx + 170 * SS, ky + 170 * SS), fill=210)
    glow = glow.filter(ImageFilter.GaussianBlur(80 * SS))
    im = Image.composite(Image.new("RGB", im.size, (255, 70, 40) if mode == "left" else (90, 190, 255)), im, glow)
    d = ImageDraw.Draw(im)
    if mode == "left":
        dashed(d, proj(*PLACES["TORA BORA"]), proj(*PLACES["ABBOTTABAD"]), (255, 90, 80), 9 * SS, bend=0.18)
        # question marks: nobody knows where he went
        for (x, y) in ((760 * SS, 520 * SS), (300 * SS, 760 * SS), (640 * SS, 820 * SS)):
            d.text((x, y), "?", font=ImageFont.truetype(FBLACK, 90 * SS), fill=(255, 255, 255, 120), stroke_width=6 * SS, stroke_fill=(0, 0, 0), anchor="mm")
        x, y = proj(*PLACES["TORA BORA"])
        d.ellipse((x - 12 * SS, y - 12 * SS, x + 12 * SS, y + 12 * SS), fill="white", outline="black", width=3 * SS)
        label(d, (x - 22 * SS, y + 30 * SS), "TORA BORA", 34, anchor="rm")
    else:
        dashed(d, proj(*PLACES["JALALABAD"]), proj(*PLACES["ABBOTTABAD"]), (150, 215, 255), 9 * SS, bend=-0.22)
        ax, ay = proj(*PLACES["ABBOTTABAD"])
        for r in (80, 52):
            d.ellipse((ax - r * SS, ay - r * SS, ax + r * SS, ay + r * SS), outline=(255, 70, 60), width=7 * SS)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d.line([(ax + dx * 34 * SS, ay + dy * 34 * SS), (ax + dx * 108 * SS, ay + dy * 108 * SS)], fill=(255, 70, 60), width=7 * SS)
        d.ellipse((ax - 12 * SS, ay - 12 * SS, ax + 12 * SS, ay + 12 * SS), fill="white", outline="black", width=3 * SS)
        label(d, (ax + 120 * SS, ay), "ABBOTTABAD", 38)
    img = im.resize((W, H), Image.LANCZOS)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = np.asarray(img).astype(np.float32) * (1 - np.clip((r - 0.55) / 0.9, 0, 1) ** 1.5 * 0.75)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

left, right = base_map("left"), base_map("right")
# zig-zag split line (like the RISE/FALL reference)
pts = [(1040, -10), (900, 330), (1020, 330), (880, 700), (990, 700), (900, 1090)]
mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(mask).polygon(pts + [(W, H + 10), (W, -10)], fill=255)
img = Image.composite(right, left, mask)
# dim each side away from its focus slightly
glow = Image.new("L", (W, H), 0)
ImageDraw.Draw(glow).line(pts, fill=255, width=34, joint="curve")
glow = glow.filter(ImageFilter.GaussianBlur(22))
img = Image.composite(Image.new("RGB", (W, H), (255, 225, 140)), img, glow.point(lambda v: int(v * 0.85)))
d = ImageDraw.Draw(img)
d.line(pts, fill=(250, 250, 245), width=9, joint="curve")
img.save(sys.argv[3], quality=93)  # clean split background

fb = ImageFont.truetype(FBLACK, 200)
d.text((470, 175), "HIDING", font=fb, fill=(255, 92, 80), stroke_width=18, stroke_fill=(0, 0, 0), anchor="mm")
d.text((1450, 175), "FOUND", font=fb, fill=(110, 185, 255), stroke_width=18, stroke_fill=(0, 0, 0), anchor="mm")
for (cx, yr) in ((430, "2001"), (1480, "2011")):
    d.rounded_rectangle((cx - 165, 905, cx + 165, 1015), 26, fill=(12, 12, 16))
    d.text((cx, 960), yr, font=ImageFont.truetype(FBLACK, 86), fill="white", anchor="mm")
img.save(sys.argv[2], quality=93)
print("ok")
