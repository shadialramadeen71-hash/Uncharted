"""Tank & Zippy: Roommates — everyday-clothes characters, new locations and props."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "nfl-short"))
import toon  # noqa: E402
from toon import Pen, S, W, H, AX, AY, SPR_W, SPR_H, OUT, GOLD, RED, PURPLE, star, GROUND  # noqa: E402

FLOOR = 1150
SKIN = {"tank": (150, 95, 60), "zippy": (255, 214, 170)}
HAIR = {"tank": (30, 24, 22), "zippy": (235, 120, 40)}

OUTFITS = {
    "tank": dict(shirt=(60, 125, 95), pants=(60, 85, 140), shoes=(245, 245, 245), sleeves="long", pattern="hoodie"),
    "zippy": dict(shirt=(250, 200, 50), pants=(215, 70, 55), shoes=(60, 140, 230), sleeves="short", pattern="bolt", shorts=True),
    "tank_pj": dict(shirt=(110, 150, 220), pants=(110, 150, 220), shoes=(150, 100, 80), sleeves="long", pattern="stars"),
    "zippy_chef": dict(shirt=(250, 200, 50), pants=(215, 70, 55), shoes=(60, 140, 230), sleeves="short", pattern="apron",
                       shorts=True, hat="chef"),
    "tank_camp": dict(shirt=(190, 50, 45), pants=(90, 75, 60), shoes=(110, 75, 45), sleeves="long", pattern="plaid", hat="beanie"),
    "zippy_camp": dict(shirt=(60, 130, 80), pants=(110, 90, 60), shoes=(110, 75, 45), sleeves="long", pattern="plaid",
                       hat="beanie", hat_color=(240, 120, 40)),
    "zippy_suit": dict(shirt=(40, 45, 60), pants=(40, 45, 60), shoes=(30, 30, 30), sleeves="long", pattern="suit"),
    "zippy_party": dict(shirt=(250, 200, 50), pants=(215, 70, 55), shoes=(60, 140, 230), sleeves="short", pattern="bolt",
                        shorts=True, hat="party"),
    "tank_party": dict(shirt=(60, 125, 95), pants=(60, 85, 140), shoes=(245, 245, 245), sleeves="long", pattern="hoodie",
                       hat="party"),
}


def casual(kind, mouth=0.0, blink=False, look=(0, 0), arms="down", t=0.0, outfit=None, angry=False, sad=False,
           dizzy=False, hair="full", brow_gone=False, tilt=0, cheeks=False, hold=None):
    """Tank or Zippy in everyday clothes. hair: 'full' | 'half' | 'bald' (for The Haircut)."""
    o = dict(OUTFITS[outfit or kind])
    img = Image.new("RGBA", (SPR_W * S, SPR_H * S), (0, 0, 0, 0))
    pen = Pen(img, AX, AY)
    big = kind == "tank"
    bw, bh, hr, lh = (330, 330, 118, 135) if big else (170, 200, 112, 125)
    skin = SKIN[kind]
    top = -lh - bh + 25
    # legs
    for sx in (-1, 1):
        x = sx * bw * 0.2
        lw = max(46, bw * 0.21)
        if o.get("shorts"):
            pen.limb([(x, -lh - 20), (x, -22)], skin, lw - 8)
            pen.rect(x - lw / 2 - 4, -lh - 30, x + lw / 2 + 4, -lh * 0.45, o["pants"], 5, 8)
        else:
            pen.limb([(x, -lh - 20), (x, -22)], o["pants"], lw)
        pen.ell(x + sx * 14, -18, bw * 0.12 + 26, 22, o["shoes"])
        pen.line([(x + sx * 14 - 20, -14), (x + sx * 14 + 20, -14)], (220, 60, 60) if big else "white", 5)
    # arms
    sh = top + 55
    if arms == "up":
        ah = [(-bw * 0.42, top - hr * 2.0), (bw * 0.42, top - hr * 2.0)]
    elif arms == "wave":
        ah = [(-bw * 0.62, -lh - bh * 0.3), (bw * 0.85, top - hr * 1.2 + 25 * math.sin(t * 14))]
    elif arms == "flail":
        ah = [(-bw * 0.95, top - 40 + 50 * math.sin(t * 25)), (bw * 0.95, top - 40 - 50 * math.sin(t * 25))]
    elif arms == "hips":
        ah = [(-bw * 0.62, -lh - bh * 0.3), (bw * 0.62, -lh - bh * 0.3)]
    elif arms == "hold":  # both hands forward at chest height
        ah = [(-bw * 0.3, -lh - bh * 0.62), (bw * 0.3, -lh - bh * 0.62)]
    elif arms == "point":
        ah = [(-bw * 0.62, -lh - bh * 0.3), (bw * 1.0, top - 20)]
    elif arms == "facepalm":
        ah = [(-bw * 0.62, -lh - bh * 0.3), (bw * 0.1, top - hr * 0.6)]
    elif arms == "shrug":
        ah = [(-bw * 0.85, top - 30), (bw * 0.85, top - 30)]
    else:
        ah = [(-bw * 0.62, -lh - bh * 0.3 + 6 * math.sin(t * 3)), (bw * 0.62, -lh - bh * 0.3 + 6 * math.sin(t * 3 + 1))]
    aw = 44 if big else 30
    for sx, hand in zip((-1, 1), ah):
        elbow = ((sx * bw * 0.5 + hand[0]) / 2 + sx * 25, (sh + hand[1]) / 2 + 10)
        if o["sleeves"] == "long":
            pen.limb([(sx * bw * 0.42, sh), elbow, hand], o["shirt"], aw)
        else:
            pen.limb([(sx * bw * 0.42, sh), elbow, hand], skin, aw - 6)
            pen.limb([(sx * bw * 0.42, sh), ((sx * bw * 0.42 + elbow[0]) / 2, (sh + elbow[1]) / 2)], o["shirt"], aw + 6)
        pen.ell(hand[0], hand[1], aw * 0.72, aw * 0.72, skin)
    # body
    cy = -lh - bh / 2 + 10
    pen.ell(0, cy, bw / 2, bh / 2, o["shirt"])
    pat = o.get("pattern")
    if pat == "hoodie":
        pen.rect(-bw * 0.28, cy + bh * 0.05, bw * 0.28, cy + bh * 0.3, tuple(max(0, c - 25) for c in o["shirt"]), 5, 18)
        for sx in (-1, 1):
            pen.line([(sx * 22, top + 40), (sx * 26, top + 120)], (235, 235, 235), 6)
        pen.ell(0, top + 30, bw * 0.38, 40, tuple(max(0, c - 15) for c in o["shirt"]), 5)
    elif pat == "bolt":
        pen.poly([(-10, cy - 70), (40, cy - 70), (10, cy - 5), (45, cy - 5), (-25, cy + 75), (0, cy + 10), (-35, cy + 10)], (220, 60, 50), 4)
    elif pat == "stars":
        for i, (sx, sy) in enumerate(((-0.25, -0.2), (0.2, -0.05), (-0.1, 0.2), (0.25, 0.28), (-0.3, 0.35))):
            star(pen, sx * bw, cy + sy * bh, 18, (255, 245, 180))
    elif pat == "plaid":
        for i in range(-3, 4):
            pen.line([(i * bw * 0.13, cy - bh * 0.45), (i * bw * 0.13, cy + bh * 0.45)], (30, 30, 30), 4)
            pen.line([(-bw * 0.45, cy + i * bh * 0.13), (bw * 0.45, cy + i * bh * 0.13)], (30, 30, 30), 4)
    elif pat == "apron":
        pen.rect(-bw * 0.32, cy - bh * 0.3, bw * 0.32, cy + bh * 0.42, "white", 5, 16)
        pen.text(0, cy + bh * 0.05, "CHEF", 34 if not big else 46, RED, 0)
    elif pat == "suit":
        pen.poly([(-bw * 0.22, top + 20), (bw * 0.22, top + 20), (0, cy + bh * 0.2)], "white", 4)
        pen.poly([(-22, top + 40), (0, top + 55), (-22, top + 70)], RED, 3)
        pen.poly([(22, top + 40), (0, top + 55), (22, top + 70)], RED, 3)
        for i in range(3):
            pen.ell(0, cy + i * 40 - 10, 6, 6, (200, 200, 210), 0)
    # head
    hy = top - hr * 0.72
    pen.ell(0, top + 5, hr * 0.35, 30, skin, 0)
    for sx in (-1, 1):
        pen.ell(sx * hr * 0.97, hy + 8, 22, 30, skin)
    pen.ell(0, hy, hr, hr * 0.98, skin)
    hc = HAIR[kind]
    if kind == "tank":
        if hair == "full":
            pen.d.chord([pen.p(-hr * 1.02, hy - hr * 1.08), pen.p(hr * 1.02, hy + hr * 0.25)], 180, 360, fill=hc, outline=OUT, width=5 * S)
        elif hair == "half":
            pen.d.chord([pen.p(-hr * 1.02, hy - hr * 1.08), pen.p(hr * 1.02, hy + hr * 0.25)], 270, 360, fill=hc, outline=OUT, width=5 * S)
            pen.poly([(0, hy - hr * 1.05), (0, hy - hr * 0.42), (hr * 1.0, hy - hr * 0.42), (hr * 0.75, hy - hr * 0.88)], hc, 0)
        else:
            pen.ell(-hr * 0.4, hy - hr * 0.62, 26, 12, (230, 200, 170), 0)  # shine
        pen.d.chord([pen.p(-hr * 0.92, hy + hr * 0.02), pen.p(hr * 0.92, hy + hr * 1.02)], 20, 160, fill=hc, outline=OUT, width=4 * S)  # beard
    else:
        if hair != "bald":
            for i in range(7):
                a = math.pi + i * math.pi / 6
                px, py = math.cos(a) * hr * 0.95, hy + math.sin(a) * hr * 0.95
                pen.poly([(px - 34, py + 10), (px + math.cos(a) * 55, py + math.sin(a) * 55 - 10), (px + 34, py + 10)], hc, 4)
            pen.d.chord([pen.p(-hr * 1.0, hy - hr * 1.02), pen.p(hr * 1.0, hy + hr * 0.15)], 180, 360, fill=hc, outline=OUT, width=5 * S)
        for sx in (-1, 1):
            for j in range(3):
                pen.ell(sx * hr * (0.5 + 0.08 * j), hy + hr * 0.35 + (j % 2) * 10, 4, 4, (220, 140, 90), 0)
    # hats
    hat = o.get("hat")
    if hat == "chef":
        pen.rect(-hr * 0.7, hy - hr * 1.15, hr * 0.7, hy - hr * 0.7, "white", 5, 10)
        for dx in (-hr * 0.45, 0, hr * 0.45):
            pen.ell(dx, hy - hr * 1.35, hr * 0.42, hr * 0.38, "white", 5)
    elif hat == "beanie":
        hcol = o.get("hat_color", (40, 90, 160))
        pen.d.chord([pen.p(-hr * 1.05, hy - hr * 1.12), pen.p(hr * 1.05, hy + hr * 0.1)], 180, 360, fill=hcol, outline=OUT, width=5 * S)
        pen.rect(-hr * 1.05, hy - hr * 0.55, hr * 1.05, hy - hr * 0.38, tuple(max(0, c - 30) for c in hcol), 5, 8)
        pen.ell(0, hy - hr * 1.15, 22, 22, "white")
    elif hat == "party":
        pen.poly([(-hr * 0.45, hy - hr * 0.85), (hr * 0.45, hy - hr * 0.85), (hr * 0.1, hy - hr * 1.9)], (240, 80, 160), 5)
        for i in range(3):
            pen.ell(-hr * 0.1 + i * hr * 0.08, hy - hr * (1.1 + i * 0.25), 8, 8, GOLD, 0)
        star(pen, hr * 0.1, hy - hr * 1.95, 20, GOLD)
    # eyes
    ex, ey = hr * 0.34, hy - hr * 0.02
    erx, ery = hr * (0.22 if kind == "zippy" else 0.17), hr * (0.27 if kind == "zippy" else 0.21)
    for sx in (-1, 1):
        cx = sx * ex
        if dizzy:
            pts = [(cx + math.cos(t * 9 * sx + i * 0.5) * erx * i / 14, ey + math.sin(t * 9 * sx + i * 0.5) * erx * i / 14) for i in range(15)]
            pen.ell(cx, ey, erx, ery, "white", 4); pen.line(pts, OUT, 5)
        elif blink:
            pen.line([(cx - erx, ey), (cx + erx, ey)], OUT, 7)
        else:
            pen.ell(cx, ey, erx, ery, "white", 4)
            pen.ell(cx + look[0] * erx * 0.45, ey + look[1] * ery * 0.45, erx * 0.45, erx * 0.45, OUT, 0)
            pen.ell(cx + look[0] * erx * 0.45 - erx * 0.15, ey + look[1] * ery * 0.45 - erx * 0.15, erx * 0.13, erx * 0.13, "white", 0)
        if brow_gone and sx == 1:
            continue
        by = ey - ery - 14
        bc = HAIR[kind] if kind == "tank" else (190, 90, 30)
        if angry:
            pen.line([(cx - sx * erx * 1.1, by - 14), (cx + sx * erx * 0.9, by + 10)], bc, 11)
        elif sad:
            pen.line([(cx - sx * erx * 1.0, by + 8), (cx + sx * erx * 0.9, by - 12)], bc, 9)
        else:
            pen.line([(cx - erx, by + 2), (cx + erx, by - 4)], bc, 10 if big else 7)
    if sad and not blink:
        pen.ell(-ex, ey + ery + 18 + (t * 60) % 40, 9, 13, (120, 200, 255), 3)
    if cheeks:
        for sx in (-1, 1):
            pen.ell(sx * hr * 0.6, hy + hr * 0.32, 22, 13, (240, 130, 130), 0)
    # mouth
    my = hy + hr * (0.42 if big else 0.5)
    if mouth > 0.1:
        pen.ell(0, my, hr * (0.2 + 0.1 * mouth), hr * (0.06 + 0.22 * mouth), (110, 20, 30), 5)
        pen.ell(0, my + hr * 0.12 * mouth, hr * 0.13, hr * 0.06 * mouth + 1, (230, 90, 100), 0)
    elif angry or sad:
        pts = [(math.cos(a) * hr * 0.2, my + hr * 0.1 - math.sin(a) * hr * 0.1) for a in np.linspace(0.3, math.pi - 0.3, 10)]
        pen.line(pts, OUT, 7)
    else:
        pts = [(math.cos(a) * hr * 0.24, my - hr * 0.08 + math.sin(a) * hr * 0.14) for a in np.linspace(0.3, math.pi - 0.3, 10)]
        pen.line(pts, OUT, 7)
    if hold:
        hold(pen, (ah[0][0] + ah[1][0]) / 2, (ah[0][1] + ah[1][1]) / 2)
    if tilt:
        img = img.rotate(tilt, center=(AX * S, (AY - lh - bh) * S), resample=Image.BICUBIC)
    return img


def granny(mouth=0.0, blink=False, look=(0, 0), t=0.0, arms="cane", fur=False, hold=None):
    """Mrs. Pickles, the landlady: tiny, grey bun, round glasses, flowery dress, cane."""
    img = Image.new("RGBA", (SPR_W * S, SPR_H * S), (0, 0, 0, 0))
    pen = Pen(img, AX, AY)
    bw, bh, hr, lh = 220, 260, 100, 80
    skin = (245, 205, 180)
    dress = (120, 85, 60) if fur else (175, 120, 200)
    for sx in (-1, 1):
        pen.limb([(sx * 40, -lh - 10), (sx * 40, -22)], (230, 200, 180), 26)
        pen.ell(sx * 50, -16, 40, 17, (120, 40, 60))
    top = -lh - bh + 30
    sh = top + 45
    if arms == "wave":
        ah = [(-130, -lh - bh * 0.3), (150, top - 120 + 20 * math.sin(t * 12))]
    elif arms == "hold":
        ah = [(-70, -lh - bh * 0.6), (70, -lh - bh * 0.6)]
    else:
        ah = [(-130, -lh - bh * 0.3), (150, -lh - bh * 0.25)]
    if arms == "cane":
        pen.line([(150, -lh - bh * 0.25), (170, -5)], (120, 70, 40), 14)
        pen.d.arc([pen.p(110, -lh - bh * 0.25 - 40), pen.p(170, -lh - bh * 0.25 + 20)], 180, 360, fill=(120, 70, 40), width=14 * S)
    for sx, hand in zip((-1, 1), ah):
        elbow = ((sx * 100 + hand[0]) / 2 + sx * 20, (sh + hand[1]) / 2 + 10)
        pen.limb([(sx * 90, sh), elbow, hand], dress, 30)
        pen.ell(hand[0], hand[1], 22, 22, skin)
    pen.poly([(-bw * 0.35, top + 20), (bw * 0.35, top + 20), (bw * 0.6, -lh), (-bw * 0.6, -lh)], dress, 7)
    pen.ell(0, top + 40, bw * 0.42, 60, dress)
    if fur:
        for i in range(14):
            r = random.Random(i)
            pen.ell(r.uniform(-bw * 0.5, bw * 0.5), r.uniform(top + 20, -lh), 18, 12, (150, 110, 80), 0)
    else:
        for i in range(10):
            r = random.Random(i)
            fx, fy = r.uniform(-bw * 0.4, bw * 0.4), r.uniform(top + 60, -lh - 30)
            for k in range(5):
                a = k * 2 * math.pi / 5
                pen.ell(fx + math.cos(a) * 9, fy + math.sin(a) * 9, 7, 7, "white", 0)
            pen.ell(fx, fy, 5, 5, GOLD, 0)
    for i in range(7):  # pearls
        a = math.pi * (0.2 + 0.6 * i / 6)
        pen.ell(math.cos(a) * 50, top + 20 + math.sin(a) * 35, 9, 9, (250, 250, 245), 3)
    hy = top - hr * 0.8
    pen.ell(0, hy, hr, hr * 0.98, skin)
    pen.ell(0, hy - hr * 1.15, hr * 0.45, hr * 0.38, (205, 205, 215))  # bun
    pen.d.chord([pen.p(-hr * 1.05, hy - hr * 1.05), pen.p(hr * 1.05, hy + hr * 0.35)], 180, 360, fill=(205, 205, 215), outline=OUT, width=5 * S)
    for sx in (-1, 1):
        cx = sx * hr * 0.36
        pen.ell(cx, hy + 8, 32, 32, (245, 240, 230), 6)
        if blink:
            pen.line([(cx - 14, hy + 8), (cx + 14, hy + 8)], OUT, 6)
        else:
            pen.ell(cx + look[0] * 8, hy + 8 + look[1] * 8, 9, 9, OUT, 0)
        pen.ell(sx * hr * 0.62, hy + hr * 0.38, 18, 11, (240, 140, 140), 0)
    pen.line([(-hr * 0.1, hy + 8), (hr * 0.1, hy + 8)], OUT, 5)
    my = hy + hr * 0.55
    if mouth > 0.1:
        pen.ell(0, my, 20 + 6 * mouth, 4 + 18 * mouth, (120, 30, 50), 4)
    else:
        pen.line([(math.cos(a) * 22, my - 6 + math.sin(a) * 10) for a in np.linspace(0.3, math.pi - 0.3, 9)], OUT, 6)
    if hold:
        hold(pen, (ah[0][0] + ah[1][0]) / 2, (ah[0][1] + ah[1][1]) / 2)
    return img


# ---------------------------------------------------------------- hand-held props (pen, x, y = between the hands)
def mug(pen, x, y):
    pen.rect(x - 34, y - 50, x + 34, y + 30, (240, 240, 240), 5, 8)
    pen.d.arc([pen.p(x + 25, y - 30), pen.p(x + 60, y + 10)], 270, 90, fill=OUT, width=6 * S)
    for i in range(3):
        pen.line([(x - 18 + i * 18 + 6 * math.sin(i + y), y - 60 - j * 12) for j in range(4)], (200, 200, 210), 4)


def fishbowl(pen, x, y, t=0.0, sunglasses=False, sc=1.0):
    p = Pen(pen.d._image, pen.ox + x * pen.sc, pen.oy + y * pen.sc, sc * pen.sc)
    p.ell(0, 0, 95, 85, (190, 230, 250), 6)
    p.rect(-60, -92, 60, -72, (190, 230, 250), 5, 8)
    p.ell(0, 40, 80, 30, (150, 120, 90), 0)
    fx = 18 * math.sin(t * 2)
    p.poly([(fx + 25, 0), (fx + 55, -22), (fx + 55, 22)], (255, 140, 40), 4)
    p.ell(fx, 0, 34, 24, (255, 150, 40), 4)
    p.ell(fx - 14, -5, 8, 8, "white", 2)
    p.ell(fx - 16, -5, 4, 4, OUT, 0)
    if sunglasses:
        p.rect(fx - 30, -14, fx - 2, 2, OUT, 0, 5)
        p.line([(fx - 2, -8), (fx + 12, -8)], OUT, 4)
    for i in range(3):
        u = (t * 0.6 + i / 3) % 1
        p.ell(fx - 30 + i * 8, -20 - u * 50, 5 + i * 2, 5 + i * 2, (240, 250, 255), 3)


def clippers(pen, x, y, t=0.0):
    pen.rect(x - 24, y - 70, x + 24, y + 40, (60, 60, 70), 5, 12)
    pen.rect(x - 28, y - 86, x + 28, y - 66, (200, 200, 210), 4, 4)
    for i in range(3):
        pen.line([(x - 40 - i * 10, y - 80 + 6 * math.sin(t * 60 + i)), (x - 55 - i * 10, y - 80 - 6 * math.sin(t * 60 + i))], OUT, 3)


def gift(pen, x, y):
    pen.rect(x - 60, y - 60, x + 60, y + 50, (90, 180, 240), 6, 6)
    pen.rect(x - 12, y - 60, x + 12, y + 50, (240, 80, 120), 0)
    pen.rect(x - 60, y - 15, x + 60, y + 5, (240, 80, 120), 0)
    pen.ell(x - 25, y - 75, 28, 18, (240, 80, 120), 4)
    pen.ell(x + 25, y - 75, 28, 18, (240, 80, 120), 4)


def marshmallow_stick(pen, x, y, burning=False, t=0.0):
    pen.line([(x, y), (x + 170, y - 120)], (130, 85, 50), 8)
    pen.rect(x + 160, y - 150, x + 200, y - 110, (90, 60, 40) if burning else (250, 245, 235), 4, 10)
    if burning:
        for i in range(3):
            fh = 40 + 15 * math.sin(t * 14 + i)
            pen.poly([(x + 160 + i * 14, y - 150), (x + 167 + i * 14, y - 150 - fh), (x + 174 + i * 14, y - 150)], (255, 150, 30), 3)


def cone(pen, x, y, scoops=1, t=0.0):
    pen.poly([(x - 34, y - 20), (x + 34, y - 20), (x, y + 80)], (220, 170, 100), 5)
    cols = [(255, 190, 210), (250, 245, 230), (150, 90, 60), (180, 230, 180), (255, 220, 120), (200, 160, 230)]
    for i in range(scoops):
        wob = math.sin(t * 6 + i * 0.7) * i * 4
        pen.ell(x + wob, y - 40 - i * 52, 44, 36, cols[i % 6], 5)


# ---------------------------------------------------------------- locations
def _canvas():
    return Image.new("RGB", (W * S, H * S))


def _grad(img, y0, y1, c0, c1):
    d = ImageDraw.Draw(img)
    for y in range(y0 * S, y1 * S, 4):
        k = (y - y0 * S) / max(1, (y1 - y0) * S)
        d.rectangle([0, y, img.width, y + 4], fill=tuple(int(a + (b - a) * k) for a, b in zip(c0, c1)))


def street():
    img = _canvas()
    _grad(img, 0, 1200, (120, 190, 245), (200, 230, 250))
    pen = Pen(img)
    for cx, cy in ((180, 200), (800, 140)):
        for dx, dy, r in ((0, 0, 60), (60, 10, 50), (-60, 12, 45)):
            pen.ell(cx + dx, cy + dy, r * 1.2, r, "white", 0)
    pen.rect(120, 260, 960, 1200, (180, 90, 70), 8, 0)  # building
    for j in range(4):
        for i in range(4):
            x, y = 180 + i * 200, 320 + j * 200
            if j == 3 and i in (1, 2):
                continue
            pen.rect(x, y, x + 120, y + 130, (170, 215, 240), 6, 6)
            pen.line([(x + 60, y), (x + 60, y + 130)], "white", 5)
    pen.rect(400, 950, 680, 1200, (90, 55, 40), 7, 8)  # entrance
    pen.rect(420, 980, 660, 1200, (120, 75, 50), 0, 6)
    pen.text(540, 920, "PICKLES APARTMENTS", 40, "white", 5)
    pen.rect(-10, 1200, W + 10, 1330, (190, 190, 195), 0)
    pen.rect(-10, 1330, W + 10, H, (80, 80, 90), 0)
    for x in range(0, W, 200):
        pen.rect(x, 1600, x + 110, 1615, (240, 240, 240), 0)
    for i in range(4):
        pen.rect(380 - i * 20, 1200 + i * 30, 700 + i * 20, 1230 + i * 30, (170, 170, 175), 4)
    return img


def hallway():
    img = _canvas()
    _grad(img, 0, FLOOR, (235, 215, 170), (220, 195, 150))
    pen = Pen(img)
    for x in range(0, W, 90):
        pen.line([(x, 0), (x, FLOOR)], (225, 200, 155), 6)
    pen.rect(-10, 860, W + 10, 880, (150, 100, 70), 0)
    pen.rect(330, 340, 750, FLOOR, (110, 70, 45), 0, 0)  # door frame hole
    for x in (130, 950):
        pen.rect(x - 30, 380, x + 30, 440, (250, 230, 150), 5, 10)
        pen.ell(x, 470, 50, 18, (255, 245, 200), 0)
    pen.rect(-10, FLOOR, W + 10, H, (150, 50, 55), 0)
    for x in range(-200, W + 200, 160):
        pen.line([(540 + (x - 540) * 0.3, FLOOR), (x, H)], (130, 40, 45), 4)
    return img


def door(pen, open_k=0.0, fallen=False, number="4B"):
    """Apartment door in the hallway frame (330..750 x 340..FLOOR)."""
    if fallen:
        pen.poly([(300, FLOOR + 200), (780, FLOOR + 200), (840, FLOOR + 320), (240, FLOOR + 320)], (170, 110, 70), 7)
        pen.text(540, FLOOR + 260, number, 50, GOLD, 5)
        return
    w = 420 * (1 - open_k * 0.85)
    pen.rect(330, 340, 330 + w, FLOOR, (170, 110, 70), 7, 4)
    if w > 120:
        pen.rect(330 + w * 0.2, 400, 330 + w * 0.8, 640, (150, 95, 60), 5, 6)
        pen.text(330 + w / 2, 520, number, 60, GOLD, 5)
        pen.ell(330 + w - 50, 760, 16, 16, GOLD)


def kitchen():
    img = _canvas()
    _grad(img, 0, FLOOR, (250, 245, 225), (240, 230, 205))
    pen = Pen(img)
    for x in range(0, W, 80):
        for y in range(620, 900, 80):
            pen.rect(x + 3, y + 3, x + 77, y + 77, (200, 230, 230), 0, 4)
    pen.rect(-10, 140, 420, 520, (240, 175, 120), 7, 6)
    pen.rect(640, 140, 1090, 520, (240, 175, 120), 7, 6)
    for x0 in (20, 220, 660, 870):
        pen.rect(x0, 170, x0 + 170, 490, (230, 160, 105), 5, 6)
        pen.ell(x0 + 150, 330, 8, 8, (120, 80, 50), 0)
    pen.rect(450, 180, 610, 400, (170, 220, 250), 7, 6)
    pen.line([(530, 180), (530, 400)], "white", 6)
    pen.rect(-10, 900, W + 10, FLOOR, (240, 175, 120), 7, 0)  # counter base
    pen.rect(-10, 880, W + 10, 910, (200, 200, 205), 5, 0)
    pen.rect(380, 820, 700, 880, (60, 60, 65), 6, 6)  # stove top
    for x in (450, 630):
        pen.ell(x, 850, 50, 14, (40, 40, 45), 4)
    pen.rect(-10, FLOOR, W + 10, H, (230, 230, 235), 0)
    for i, y in enumerate(range(FLOOR, H, 110)):
        for j, x in enumerate(range(0, W, 110)):
            if (i + j) % 2:
                pen.rect(x, y, x + 110, y + 110, (200, 80, 80), 0)
    return img


def frying_pan(pen, x, y, smoke=0.0, t=0.0, pancake=True):
    pen.ell(x, y, 110, 30, (50, 50, 55), 6)
    pen.line([(x + 105, y), (x + 260, y + 10)], (50, 50, 55), 20)
    if pancake:
        pen.ell(x, y - 8, 75, 18, (225, 170, 90), 4)
    for i in range(int(smoke * 6)):
        u = (t * 0.5 + i / 6) % 1
        pen.ell(x - 40 + i * 16 + 30 * math.sin(t * 2 + i), y - 60 - u * 400, 40 + u * 50, 35 + u * 40, (120, 120, 125), 0)


def bathroom():
    img = _canvas()
    _grad(img, 0, FLOOR, (200, 235, 240), (185, 225, 232))
    pen = Pen(img)
    for x in range(0, W, 90):
        for y in range(0, FLOOR, 90):
            pen.rect(x + 2, y + 2, x + 88, y + 88, (215, 242, 246), 0, 6)
    pen.rect(330, 230, 750, 680, (180, 150, 110), 8, 20)  # mirror
    pen.rect(355, 255, 725, 655, (210, 235, 250), 0, 12)
    pen.line([(420, 300), (480, 260)], "white", 10)
    pen.line([(400, 360), (520, 270)], "white", 6)
    pen.rect(-10, FLOOR, W + 10, H, (245, 245, 250), 0)
    for x in range(0, W, 120):
        pen.line([(x, FLOOR), (x, H)], (220, 220, 230), 4)
    return img


def bathtub(pen, x0, x1, y, bubbles=True, t=0.0):
    pen.rect(x0, y - 220, x1, y - 20, "white", 8, 50)
    for x in (x0 + 60, x1 - 60):
        pen.ell(x, y - 10, 24, 18, GOLD)
    if bubbles:
        r = random.Random(4)
        for i in range(16):
            bx = r.uniform(x0 + 40, x1 - 40)
            pen.ell(bx, y - 230 + 8 * math.sin(t * 2 + i), r.uniform(26, 50), r.uniform(22, 40), (250, 250, 255), 4)


def forest():
    img = _canvas()
    _grad(img, 0, 1200, (10, 15, 45), (40, 50, 90))
    pen = Pen(img)
    r = random.Random(3)
    for _ in range(80):
        pen.ell(r.uniform(0, W), r.uniform(0, 800), 3, 3, (255, 255, 230), 0)
    pen.ell(860, 220, 80, 80, (250, 245, 210), 0)
    pen.ell(890, 200, 70, 70, (40, 50, 95), 0)
    for i, x in enumerate(range(-60, W + 120, 150)):
        h = 520 + (i * 97) % 180
        for k in range(3):
            pen.poly([(x - 110 + k * 15, 1200 - k * 150), (x, 1200 - h - k * 60), (x + 110 - k * 15, 1200 - k * 150)], (20, 50 + k * 8, 40), 0)
    pen.rect(-10, 1150, W + 10, H, (40, 75, 45), 0)
    for _ in range(60):
        x, y = r.uniform(0, W), r.uniform(1160, H)
        pen.line([(x, y), (x + 6, y - 22)], (60, 110, 60), 4)
    return img


def tent(pen, x, y, collapse=0.0, t=0.0):
    h = 380 * (1 - collapse) + 80 * collapse
    pen.poly([(x - 260, y), (x, y - h), (x + 260, y)], (240, 140, 40), 8)
    if collapse < 0.5:
        pen.poly([(x - 60, y), (x, y - h * 0.6), (x + 60, y)], (150, 80, 25), 5)
    else:
        pen.ell(x + 40 * math.sin(t * 6), y - 70, 70, 50, (240, 140, 40), 6)


def campfire(pen, x, y, t):
    for i in range(4):
        a = i * math.pi / 4
        pen.line([(x - math.cos(a) * 90, y - math.sin(a) * 20 + 10), (x + math.cos(a) * 90, y + math.sin(a) * 20 + 10)], (110, 70, 40), 18)
    for i, (dx, s) in enumerate(((-30, 1.0), (25, 0.9), (0, 1.3))):
        fh = 140 * s + 25 * math.sin(t * 12 + i * 2)
        pen.poly([(x + dx - 45, y), (x + dx, y - fh), (x + dx + 45, y)], (255, 130, 30), 0)
        pen.poly([(x + dx - 22, y), (x + dx, y - fh * 0.55), (x + dx + 22, y)], (255, 230, 90), 0)


def glow(frame, x, y, r, color=(255, 170, 60), alpha=70):
    over = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for k in range(6):
        rr = r * (1 - k / 7)
        d.ellipse([(x - rr) * S, (y - rr * 0.8) * S, (x + rr) * S, (y + rr * 0.8) * S], fill=color + (alpha // 6,))
    frame.alpha_composite(over)


def bush(pen, x, y, eyes=False, shake=0.0):
    for dx, dy, r in ((-90, 0, 90), (0, -40, 110), (90, 0, 90)):
        pen.ell(x + dx + shake, y + dy, r, r * 0.8, (30, 80, 40), 6)
    if eyes:
        for sx in (-1, 1):
            pen.ell(x + sx * 35 + shake, y - 40, 18, 14, (255, 240, 120), 3)
            pen.ell(x + sx * 35 + shake, y - 40, 6, 9, OUT, 0)


def ice_cream_shop():
    img = _canvas()
    _grad(img, 0, FLOOR, (255, 230, 240), (250, 215, 230))
    pen = Pen(img)
    for x in range(0, W, 120):
        pen.rect(x, 0, x + 60, 120, (240, 120, 160), 0)
    pen.rect(-10, 110, W + 10, 130, (200, 80, 120), 0)
    pen.rect(140, 200, 940, 470, (60, 40, 50), 8, 14)
    pen.text(540, 260, "PICKLES' ICE CREAM", 54, (255, 200, 220), 0)
    for i, (n, p) in enumerate((("Vanilla", "$2"), ("Pickle Swirl", "$3"), ("Chocolate", "$2"))):
        pen.text(400, 330 + i * 45, n, 36, "white", 0)
        pen.text(760, 330 + i * 45, p, 36, GOLD, 0)
    pen.rect(-10, 860, W + 10, FLOOR, (250, 250, 252), 7, 0)  # counter
    pen.rect(-10, 850, W + 10, 880, (240, 120, 160), 5, 0)
    cols = [(255, 190, 210), (250, 245, 230), (150, 90, 60), (180, 230, 180), (255, 220, 120)]
    for i in range(5):
        x = 110 + i * 215
        pen.rect(x - 85, 760, x + 85, 860, (200, 220, 235), 5, 6)
        pen.ell(x, 780, 70, 26, cols[i], 4)
    pen.rect(-10, FLOOR, W + 10, H, (250, 240, 245), 0)
    for i, y in enumerate(range(FLOOR, H, 100)):
        for j, x in enumerate(range(0, W, 100)):
            if (i + j) % 2:
                pen.rect(x, y, x + 100, y + 100, (240, 150, 180), 0)
    return img


def party_decor(frame, t, banner="HAPPY BIRTHDAY ZIPPY!"):
    pen = Pen(frame)
    pts = [(40 + i * 125, 120 + 40 * math.sin(i * 0.8)) for i in range(9)]
    pen.line(pts, OUT, 4)
    cols = [(240, 80, 120), GOLD, (90, 180, 240), (120, 220, 120)]
    for i, (x, y) in enumerate(pts[:-1]):
        pen.poly([(x + 10, y + 4), (x + 110, y + 4), (x + 60, y + 90)], cols[i % 4], 4)
    pen.rect(120, 190, 960, 290, "white", 6, 20)
    pen.text(540, 240, banner, 52, (240, 80, 120), 0)
    for i, x in enumerate((60, 190, 890, 1020)):
        y = 520 + 15 * math.sin(t * 2 + i)
        pen.line([(x, y + 80), (x + 10, y + 300)], (120, 120, 130), 3)
        pen.ell(x, y, 55, 70, cols[i % 4], 5)


def cake(pen, x, y, candles=True, lit=True, t=0.0):
    pen.rect(x - 130, y - 110, x + 130, y, (250, 230, 240), 6, 14)
    pen.rect(x - 130, y - 110, x + 130, y - 80, (240, 120, 160), 0, 14)
    for i in range(5):
        pen.ell(x - 100 + i * 50, y - 80, 18, 14, (240, 120, 160), 0)
    if candles:
        for i in range(3):
            cx = x - 60 + i * 60
            pen.rect(cx - 8, y - 170, cx + 8, y - 110, (90, 180, 240), 3)
            if lit:
                pen.poly([(cx - 10, y - 172), (cx, y - 205 - 5 * math.sin(t * 15 + i)), (cx + 10, y - 172)], (255, 180, 40), 3)


def boxes(pen, t=0.0):
    for x, y, w, h, label in ((60, 1480, 220, 180, "BOOKS"), (90, 1300, 160, 180, "STUFF"), (820, 1480, 240, 200, "FRAGILE"),
                              (860, 1280, 180, 200, "MISC"), (300, 1480, 170, 140, "")):
        pen.rect(x, y - h, x + w, y, (200, 150, 95), 6, 6)
        pen.line([(x + w / 2, y - h), (x + w / 2, y - h + 40)], (230, 200, 150), 10)
        if label:
            pen.text(x + w / 2, y - h / 2, label, 30, (120, 70, 40), 0)


def rooftop():
    img = _canvas()
    _grad(img, 0, 1100, (255, 150, 90), (255, 215, 150))
    pen = Pen(img)
    pen.ell(540, 900, 160, 160, (255, 240, 180), 0)
    r = random.Random(6)
    x = -20
    while x < W:
        w = r.uniform(80, 160); h = r.uniform(250, 600)
        pen.rect(x, 1100 - h, x + w, 1100, (110, 70, 110), 0)
        for j in range(int(h / 60)):
            for i in range(int(w / 40)):
                if r.random() < 0.35:
                    pen.rect(x + 12 + i * 40, 1100 - h + 20 + j * 60, x + 30 + i * 40, 1100 - h + 44 + j * 60, (255, 220, 140), 0)
        x += w + 10
    pen.rect(-10, 1100, W + 10, H, (130, 120, 125), 0)
    pen.rect(-10, 1090, W + 10, 1130, (100, 90, 95), 0)
    pts = [(i * 135, 160 + 50 * math.sin(i)) for i in range(9)]
    pen.line(pts, OUT, 3)
    for px, py in pts:
        pen.ell(px, py + 18, 12, 16, (255, 240, 170), 3)
    return img


def couch(pen, x, y, w=600, color=(235, 120, 40), sc=1.0):
    """Side-on couch; (x, y) = bottom center."""
    p = Pen(pen.d._image, pen.ox + x * pen.sc, pen.oy + y * pen.sc, sc * pen.sc)
    p.rect(-w / 2, -330, w / 2, -140, color, 8, 40)
    p.rect(-w / 2 - 20, -170, w / 2 + 20, -40, tuple(max(0, c - 15) for c in color), 8, 30)
    p.rect(-w / 2 - 40, -260, -w / 2 + 50, -40, tuple(max(0, c - 25) for c in color), 8, 30)
    p.rect(w / 2 - 50, -260, w / 2 + 40, -40, tuple(max(0, c - 25) for c in color), 8, 30)
    for dx in (-w / 2, w / 2 - 30):
        p.rect(dx, -40, dx + 30, 0, (90, 60, 40), 4)


# ---------------------------------------------------------------- series helpers
toon.VOICE["granny"] = ("ie", 1.18, 0.88)
toon.NAMES["granny"] = ("MRS. PICKLES", (150, 80, 170))
SERIES = "ROOMMATES"
WARM, WARM_RAYS = (235, 120, 60), (245, 145, 80)


def music(name):
    return os.path.join(HERE, "music", name)


def title_card(frame, t, ep_title, y=230, dur=2.8):
    if t >= dur:
        return
    a = toon.ease(t / 0.4) * (1 - toon.ease((t - dur + 0.4) / 0.4))
    p = Pen(frame, 540, y, 0.6 + 0.4 * a)
    p.rect(-480, -120, 480, 175, (60, 30, 20), 7, 30)
    p.text(0, -40, "TANK & ZIPPY", 104, GOLD, 12)
    p.text(0, 50, SERIES, 52, (255, 200, 160), 6)
    p.text(0, 125, ep_title, 46, "white", 6)


def life_end_card(t, u, ep_title, next_text, sprites=None, final=False):
    sprites = sprites or [
        (casual("tank", 0, toon.blink_at(t, 0), (0.4, 0), arms="wave", t=t), 300, 1380, 0.9),
        (casual("zippy", 0, toon.blink_at(t, 1.3), (-0.4, 0), arms="wave", t=t), 770, 1380 - abs(math.sin(t * 6)) * 40, 0.9)]
    frame = toon.end_card(t, u, f"{SERIES} · {ep_title}", None if final else next_text, sprites, bg=WARM, rays=WARM_RAYS)
    return frame


def say_all(tl, keys, t, gap=0.25):
    for k in keys:
        t = tl.say(k, t) + gap
    return t


def run(module, filename):
    toon.main(module, sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, filename))
