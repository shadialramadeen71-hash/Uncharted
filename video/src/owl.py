"""Professor Hoot: a cartoon owl drawn with PIL. make_owl(mouth 0..1, blink 0..1, wing -1..1) -> RGBA."""
from PIL import Image, ImageDraw, ImageFilter

SS = 2  # supersample
W, H = 900, 720

BROWN = (122, 78, 42)
DARK = (78, 48, 24)
BELLY = (232, 200, 150)
BELLY_DOTS = (205, 165, 110)
ORANGE = (247, 160, 40)
ORANGE_D = (200, 110, 20)
OUT = (35, 22, 12)

def _p(*v): return [x * SS for x in v]

def make_owl(mouth=0.0, blink=0.0, wing=0.0, look=0.0):
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    o = 6 * SS  # outline width
    cx = W // 2
    # feet
    for fx in (cx - 70, cx + 70):
        for k in (-22, 0, 22):
            d.ellipse(_p(fx + k - 16, 655, fx + k + 16, 700), fill=ORANGE, outline=OUT, width=o // 2)
    # wings (behind body), rotated by `wing`
    for side in (-1, 1):
        wl = Image.new("RGBA", (220 * SS, 360 * SS), (0, 0, 0, 0))
        wd = ImageDraw.Draw(wl)
        wd.ellipse(_p(10, 10, 210, 350), fill=DARK, outline=OUT, width=o)
        for k in range(3):
            wd.arc(_p(40, 120 + k * 60, 180, 260 + k * 60), 20, 160, fill=BROWN, width=5 * SS)
        wl = wl.rotate(side * (18 + wing * 22), resample=Image.BICUBIC, expand=True,
                       center=(110 * SS, 40 * SS))
        x = cx + side * 205 - wl.width // (2 * SS)
        im.alpha_composite(wl, (int(x * SS) if side < 0 else int(x * SS), 300 * SS))
    # ear tufts
    d.polygon(_p(cx - 200, 205, cx - 230, 70, cx - 110, 160), fill=BROWN, outline=OUT, width=o)
    d.polygon(_p(cx + 200, 205, cx + 230, 70, cx + 110, 160), fill=BROWN, outline=OUT, width=o)
    # body
    d.ellipse(_p(cx - 230, 120, cx + 230, 690), fill=BROWN, outline=OUT, width=o)
    # belly
    d.ellipse(_p(cx - 150, 360, cx + 150, 670), fill=BELLY)
    for r, row in enumerate(range(420, 640, 55)):
        for c in range(-2, 3):
            x = cx + c * 50 + (25 if r % 2 else 0)
            if abs(x - cx) < 120 - abs(row - 520) * 0.3:
                d.arc(_p(x - 16, row - 10, x + 16, row + 14), 20, 160, fill=BELLY_DOTS, width=4 * SS)
    # face disc
    d.ellipse(_p(cx - 200, 170, cx + 200, 420), fill=(176, 120, 70))
    # eyes
    for ex in (cx - 95, cx + 95):
        d.ellipse(_p(ex - 78, 200, ex + 78, 356), fill="white", outline=OUT, width=o // 2)
        px = ex + look * 22
        d.ellipse(_p(px - 34, 246, px + 34, 314), fill=(30, 20, 10))
        d.ellipse(_p(px - 22, 254, px - 6, 270), fill="white")
        if blink > 0.5:
            d.ellipse(_p(ex - 78, 200, ex + 78, 356), fill=(176, 120, 70), outline=OUT, width=o // 2)
            d.arc(_p(ex - 60, 240, ex + 60, 300), 10, 170, fill=OUT, width=7 * SS)
    # glasses
    for ex in (cx - 95, cx + 95):
        d.ellipse(_p(ex - 86, 192, ex + 86, 364), outline=(25, 25, 30), width=10 * SS)
    d.arc(_p(cx - 25, 255, cx + 25, 300), 200, 340, fill=(25, 25, 30), width=10 * SS)
    # brows
    d.line(_p(cx - 160, 178, cx - 40, 192), fill=OUT, width=9 * SS)
    d.line(_p(cx + 160, 178, cx + 40, 192), fill=OUT, width=9 * SS)
    # beak: upper fixed, lower drops with mouth
    m = max(0.0, min(1.0, mouth))
    drop = 8 + m * 46
    d.polygon(_p(cx - 34, 350, cx + 34, 350, cx + 26, 376 + drop, cx - 26, 376 + drop), fill=(90, 20, 20))
    d.polygon(_p(cx - 26, 372 + drop * 0.5, cx + 26, 372 + drop * 0.5, cx, 380 + drop), fill=(230, 90, 100)) if m > 0.2 else None
    d.polygon(_p(cx - 42, 340, cx + 42, 340, cx, 392), fill=ORANGE, outline=OUT, width=o // 2)
    d.polygon(_p(cx - 30, 368 + drop, cx + 30, 368 + drop, cx, 400 + drop), fill=ORANGE_D, outline=OUT, width=o // 2)
    # bow tie
    d.polygon(_p(cx, 440, cx - 70, 410, cx - 70, 470), fill=(200, 30, 40), outline=OUT, width=o // 2)
    d.polygon(_p(cx, 440, cx + 70, 410, cx + 70, 470), fill=(200, 30, 40), outline=OUT, width=o // 2)
    d.ellipse(_p(cx - 18, 424, cx + 18, 456), fill=(160, 20, 30), outline=OUT, width=o // 2)
    # mortarboard cap
    d.polygon(_p(cx - 190, 95, cx, 30, cx + 190, 95, cx, 160), fill=(30, 30, 38), outline=OUT, width=o // 2)
    d.rectangle(_p(cx - 95, 110, cx + 95, 168), fill=(30, 30, 38))
    d.polygon(_p(cx - 190, 95, cx, 30, cx + 190, 95, cx, 160), fill=(40, 40, 50), outline=OUT, width=o // 2)
    d.line(_p(cx, 95, cx + 160, 120, cx + 160, 200), fill=(250, 200, 40), width=6 * SS)
    d.ellipse(_p(cx + 148, 195, cx + 172, 225), fill=(250, 200, 40))
    d.ellipse(_p(cx - 12, 85, cx + 12, 105), fill=(250, 200, 40))
    im = im.resize((W, H), Image.LANCZOS)
    return im

if __name__ == "__main__":
    import sys
    sheet = Image.new("RGBA", (W * 4, H), (40, 60, 90, 255))
    for i, (m, b, w) in enumerate([(0, 0, 0), (0.6, 0, 0.5), (1, 0, -0.5), (0, 1, 0)]):
        sheet.alpha_composite(make_owl(m, b, w), (i * W, 0))
    sheet.convert("RGB").save(sys.argv[1])
