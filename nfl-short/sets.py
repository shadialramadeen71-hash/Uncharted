"""Locations and props for Tank & Zippy (season 1, episodes 3-8)."""
import math, random
from PIL import Image, ImageDraw
from toon import Pen, S, W, H, PURPLE, GOLD, RED, OUT, PERIOD, football, star

FLOOR = 1150  # wall/floor line for indoor sets


def _canvas(w=W):
    return Image.new("RGB", (w * S, H * S))


def _gradient(img, y0, y1, c0, c1):
    d = ImageDraw.Draw(img)
    for y in range(y0 * S, y1 * S, 4):
        k = (y - y0 * S) / max(1, (y1 - y0) * S)
        d.rectangle([0, y, img.width, y + 4], fill=tuple(int(a + (b - a) * k) for a, b in zip(c0, c1)))


# ---------------------------------------------------------------- stadiums
THEMES = {
    "night": dict(sky=((8, 12, 40), (40, 50, 105)), stands=(32, 32, 48), rows=(24, 24, 36), banner=PURPLE,
                  banner_text="GO WAFFLES!", banner_fg=GOLD, field=((58, 140, 60), (66, 152, 66)), lights=True,
                  stars=True, crowd=[(200, 70, 70), (210, 170, 60), (80, 130, 210), (210, 210, 210), (130, 80, 180)]),
    "hotsauce": dict(sky=((255, 120, 50), (255, 205, 120)), stands=(95, 40, 35), rows=(75, 30, 28), banner=RED,
                     banner_text="GO HOT SAUCE!", banner_fg="white", field=((110, 165, 70), (122, 176, 78)),
                     lights=False, stars=False,
                     crowd=[(230, 50, 40), (250, 140, 30), (255, 210, 60), (240, 240, 240), (150, 30, 30)]),
    "snow": dict(sky=((15, 20, 50), (70, 80, 125)), stands=(40, 40, 58), rows=(30, 30, 44), banner=PURPLE,
                 banner_text="CHAMPIONSHIP!", banner_fg=GOLD, field=((70, 150, 72), (78, 160, 78)), lights=True,
                 stars=False, snow=True,
                 crowd=[(200, 70, 70), (210, 170, 60), (80, 130, 210), (230, 230, 230), (130, 80, 180)]),
}


def stadium(theme):
    th = THEMES[theme]
    img = Image.new("RGB", (2 * PERIOD * S, H * S))
    _gradient(img, 0, 560, *th["sky"])
    pen = Pen(img)
    r = random.Random(11)
    if th["stars"]:
        for _ in range(70):
            x, y = r.uniform(0, PERIOD), r.uniform(20, 500)
            for off in (0, PERIOD):
                pen.ell(x + off, y, 3, 3, (255, 255, 230), 0)
    if theme == "hotsauce":
        for off in (0, PERIOD):
            pen.ell(off + 800, 260, 110, 110, (255, 240, 170), 0)
            pen.poly([(off - 20, 520), (off + 120, 380), (off + 300, 380), (off + 420, 520)], (190, 90, 60), 0)
            pen.poly([(off + 500, 520), (off + 600, 430), (off + 720, 430), (off + 800, 520)], (170, 80, 55), 0)
    pen.rect(-20, 520, 2 * PERIOD + 20, 905, th["stands"], 0)
    for i in range(8):
        pen.rect(-20, 540 + i * 45, 2 * PERIOD + 20, 544 + i * 45, th["rows"], 0)
    dots = [(r.uniform(0, PERIOD), 560 + row * 45 + r.uniform(-6, 6), r.choice(th["crowd"])) for row in range(8) for _ in range(34)]
    for x, y, c in dots:
        for off in (0, PERIOD):
            pen.ell(x + off, y, 13, 13, c, 0)
            pen.ell(x + off, y + 20, 15, 10, c, 0)
    if th["lights"]:
        for off in (0, PERIOD):
            for x in (140, 760):
                pen.rect(off + x - 10, 160, off + x + 10, 560, (70, 70, 80), 0)
                pen.rect(off + x - 90, 90, off + x + 90, 170, (60, 60, 70), 5, 8)
                for i in range(3):
                    for j in range(2):
                        pen.ell(off + x - 60 + i * 60, 112 + j * 36, 22, 14, (255, 255, 220), 0)
    pen.rect(-20, 860, 2 * PERIOD + 20, 905, th["banner"], 0)
    for off in (0, PERIOD):
        for x in range(60, PERIOD, 360):
            pen.text(x + off + 120, 883, th["banner_text"], 28, th["banner_fg"], 0)
    f0, f1 = th["field"]
    for i, y in enumerate(range(905, H, 90)):
        pen.rect(-20, y, 2 * PERIOD + 20, y + 90, f0 if i % 2 else f1, 0)
    nums = ["30", "40", "50", "40", "30", "40"]
    for i in range(12):
        x = i * 180
        pen.poly([(x, 905), (x + 10, 905), (x - 250, H), (x - 262, H)], (245, 245, 245), 0)
        pen.text(x - 120, 1080, nums[i % 6], 54, (245, 245, 245), 0)
    if th.get("snow"):
        for _ in range(45):
            x, y = r.uniform(0, PERIOD), r.uniform(910, H)
            w_, h_ = r.uniform(25, 60), r.uniform(8, 18)
            for off in (0, PERIOD):
                pen.ell(x + off, y, w_, h_, (235, 242, 250), 0)
        for off in (0, PERIOD):
            for x in range(0, PERIOD, 120):
                pen.ell(off + x, 905, 90, 28, (240, 245, 252), 0)
    return img


def view(world, offset):
    o = int((offset % PERIOD) * S)
    return world.crop((o, 0, o + W * S, H * S)).convert("RGBA")


def snowfall(frame, t, n=70):
    pen = Pen(frame)
    r = random.Random(5)
    for i in range(n):
        x0, sp, sz = r.uniform(0, W), r.uniform(120, 260), r.uniform(5, 12)
        y = (r.uniform(0, H) + t * sp) % H
        x = (x0 + 30 * math.sin(t * 1.5 + i)) % W
        pen.ell(x, y, sz, sz, (255, 255, 255), 0)


# ---------------------------------------------------------------- indoor sets
def locker_room():
    img = _canvas()
    _gradient(img, 0, FLOOR, (70, 80, 105), (95, 105, 130))
    pen = Pen(img)
    pen.rect(-10, 120, W + 10, 230, PURPLE, 0)
    pen.text(540, 175, "WAFFLES LOCKER ROOM", 58, GOLD, 5)
    for i in range(7):
        x = 10 + i * 152
        pen.rect(x, 300, x + 140, FLOOR - 30, (110, 70, 160), 6, 6)
        for j in range(4):
            pen.line([(x + 30, 340 + j * 22), (x + 110, 340 + j * 22)], (60, 35, 95), 6)
        pen.rect(x + 110, 640, x + 122, 720, (220, 220, 230), 3, 4)
        pen.text(x + 70, 500, str([12, 77, 5, 1, 33, 8, 21][i]), 48, GOLD, 4)
    pen.rect(-10, FLOOR, W + 10, H, (150, 150, 160), 0)
    for y in range(FLOOR, H, 90):
        pen.line([(0, y), (W, y)], (130, 130, 142), 4)
    for x in range(-400, W + 400, 140):
        pen.line([(540 + (x - 540) * 0.4, FLOOR), (x, H)], (130, 130, 142), 4)
    pen.rect(60, FLOOR - 120, 1020, FLOOR - 85, (170, 115, 70), 5, 8)  # bench
    for x in (120, 960):
        pen.rect(x - 12, FLOOR - 85, x + 12, FLOOR + 10, (120, 80, 50), 4)
    return img


def gym():
    img = _canvas()
    _gradient(img, 0, FLOOR, (215, 225, 235), (190, 200, 215))
    pen = Pen(img)
    pen.rect(60, 180, 470, 470, "white", 7, 12)
    pen.text(265, 260, "EAT YOUR", 56, PURPLE, 0)
    pen.text(265, 340, "VEGGIES", 70, (60, 160, 60), 0)
    pen.text(265, 420, "- COACH", 36, (90, 90, 100), 0)
    pen.rect(620, 330, 1040, 360, (80, 80, 90), 5, 6)  # dumbbell rack
    for i in range(5):
        x = 660 + i * 80
        pen.rect(x - 28, 280, x + 28, 330, (50, 50, 60), 4, 10)
        pen.rect(x - 8, 255, x + 8, 285, (160, 160, 170), 3)
    pen.rect(-10, FLOOR, W + 10, H, (195, 145, 95), 0)
    for i, y in enumerate(range(FLOOR, H, 60)):
        pen.line([(0, y), (W, y)], (170, 120, 75), 4)
        for x in range(-200 + (i % 2) * 150, W, 300):
            pen.line([(x, y), (x, y + 60)], (170, 120, 75), 3)
    return img


def cafeteria():
    img = _canvas()
    _gradient(img, 0, FLOOR, (250, 240, 215), (240, 225, 195))
    pen = Pen(img)
    for x in range(0, W, 60):
        pen.line([(x, 700), (x, FLOOR)], (225, 210, 180), 3)
    pen.rect(-10, 690, W + 10, 705, (200, 120, 80), 0)
    pen.rect(140, 120, 940, 380, (40, 60, 50), 8, 12)  # menu chalkboard
    pen.text(540, 180, "TODAY'S MENU", 54, "white", 0)
    pen.text(540, 260, "Mon: Salad   Tue: Salad", 40, (180, 240, 180), 0)
    pen.text(540, 320, "Wed: Salad   Thu: Salad?", 40, (180, 240, 180), 0)
    pen.rect(-10, 830, W + 10, FLOOR - 40, (180, 180, 190), 6, 0)  # serving counter
    pen.rect(-10, 800, W + 10, 840, (220, 220, 230), 5, 0)
    for i in range(6):
        x = 80 + i * 180
        pen.ell(x, 790, 70, 26, [(90, 180, 70), (110, 200, 80), (230, 80, 60), (90, 180, 70), (250, 200, 80), (90, 180, 70)][i], 5)
    pen.line([(0, 600), (W, 600)], (200, 230, 250), 8)  # sneeze guard
    pen.rect(-10, FLOOR - 40, W + 10, H, (230, 230, 235), 0)
    for i, y in enumerate(range(FLOOR - 40, H, 100)):
        for j, x in enumerate(range(0, W, 100)):
            if (i + j) % 2:
                pen.rect(x, y, x + 100, y + 100, (60, 60, 75), 0)
    return img


def living_room():
    img = _canvas()
    _gradient(img, 0, FLOOR, (90, 160, 165), (70, 140, 150))
    pen = Pen(img)
    for x in range(0, W, 80):
        pen.rect(x, 0, x + 30, FLOOR, (100, 172, 176), 0)
    pen.rect(560, 160, 1000, 600, (20, 25, 60), 8, 6)  # window
    r = random.Random(4)
    for i in range(9):
        x = 570 + i * 48; h = r.uniform(100, 300)
        pen.rect(x, 590 - h, x + 44, 590, (45, 50, 90), 0)
        for j in range(int(h / 40)):
            if r.random() < 0.6:
                pen.rect(x + 10, 600 - h + j * 40, x + 20, 612 - h + j * 40, (255, 230, 120), 0)
    pen.ell(900, 240, 40, 40, (250, 250, 220), 0)
    pen.line([(780, 160), (780, 600)], (230, 230, 230), 8)
    pen.line([(560, 380), (1000, 380)], (230, 230, 230), 8)
    pen.rect(60, 250, 300, 520, (240, 200, 90), 7, 8)  # poster
    pen.text(180, 330, "TANK &", 44, PURPLE, 0)
    pen.text(180, 400, "ZIPPY", 54, PURPLE, 0)
    football(pen, 180, 470, 30, 0.3)
    pen.rect(-10, FLOOR, W + 10, H, (150, 105, 75), 0)
    pen.ell(540, 1600, 520, 140, (200, 80, 70), 0)  # rug
    pen.ell(540, 1600, 440, 100, (220, 120, 90), 0)
    # couch back
    pen.rect(90, 830, 990, 1180, (235, 120, 40), 8, 40)
    return img


def couch_front(frame):
    pen = Pen(frame)
    pen.rect(70, 1180, 1010, 1420, (225, 105, 30), 8, 30)
    pen.rect(40, 1000, 170, 1430, (215, 95, 25), 8, 40)
    pen.rect(910, 1000, 1040, 1430, (215, 95, 25), 8, 40)
    for x in (110, 970):
        pen.rect(x - 15, 1420, x + 15, 1470, (90, 60, 40), 4)


def backstage():
    img = _canvas()
    _gradient(img, 0, FLOOR, (45, 35, 45), (60, 45, 55))
    pen = Pen(img)
    for j, y in enumerate(range(0, FLOOR, 60)):
        for x in range(-60 + (j % 2) * 60, W, 120):
            pen.rect(x + 4, y + 4, x + 116, y + 56, (75, 50, 55), 0, 4)
    pen.rect(620, 320, 960, FLOOR, (130, 40, 60), 8, 6)  # dressing room door
    star(pen, 790, 470, 70, GOLD)
    pen.text(790, 600, "SINGER", 50, "white", 5)
    pen.ell(910, 760, 16, 16, GOLD)
    for i, x in enumerate((60, 260)):  # road cases
        pen.rect(x, 860, x + 190, FLOOR + 20, (40, 40, 45), 6, 8)
        pen.rect(x + 10, 870, x + 180, 900, (150, 150, 160), 0)
    pen.text(155, 1000, "FRAGILE", 30, (255, 220, 0), 0)
    pen.rect(-10, FLOOR, W + 10, H, (40, 38, 45), 0)
    pen.line([(0, 1300), (300, 1260), (600, 1320), (1080, 1280)], (20, 20, 20), 12)
    return img


def concert_stage():
    img = _canvas()
    _gradient(img, 0, 1300, (15, 5, 35), (60, 20, 80))
    pen = Pen(img)
    pen.rect(180, 220, 900, 660, (20, 20, 30), 10, 10)  # LED screen
    for side in (0, 1):  # speaker stacks
        x = 20 if side == 0 else 900
        for j in range(3):
            pen.rect(x, 560 + j * 200, x + 160, 750 + j * 200, (30, 30, 35), 6, 8)
            pen.ell(x + 80, 655 + j * 200, 55, 55, (60, 60, 70), 5)
            pen.ell(x + 80, 655 + j * 200, 22, 22, (20, 20, 25), 0)
    pen.rect(-10, 1300, W + 10, 1560, (70, 30, 110), 8, 0)  # stage deck
    pen.rect(-10, 1290, W + 10, 1320, GOLD, 0)
    pen.rect(-10, 1560, W + 10, H, (10, 5, 20), 0)
    return img


def stage_lights(frame, t, colors=((255, 230, 120), (120, 200, 255), (255, 120, 200))):
    over = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for i, c in enumerate(colors):
        x0 = 180 + i * 360
        a = math.sin(t * 1.6 + i * 2) * 260
        d.polygon([((x0 - 30) * S, 0), ((x0 + 30) * S, 0), ((540 + a + 220) * S, 1480 * S), ((540 + a - 220) * S, 1480 * S)],
                  fill=c + (55,))
    frame.alpha_composite(over)


def crowd_heads(frame, t, jump=0.0):
    pen = Pen(frame)
    r = random.Random(2)
    for i in range(16):
        x = i * 72 + r.uniform(-10, 10)
        y = 1870 - abs(math.sin(t * 8 + i)) * 30 * jump
        pen.ell(x, y, 50, 56, (55, 35, 85), 0)
        if jump > 0.5 and i % 3 == 0:
            pen.limb([(x + 20, y - 20), (x + 50, y - 130)], (55, 35, 85), 18)


def desert_road():
    img = Image.new("RGB", (2 * PERIOD * S, H * S))
    _gradient(img, 0, 900, (110, 180, 240), (255, 200, 140))
    pen = Pen(img)
    for off in (0, PERIOD):
        pen.ell(off + 820, 330, 100, 100, (255, 240, 170), 0)
        pen.poly([(off - 40, 900), (off + 80, 620), (off + 330, 620), (off + 450, 900)], (200, 100, 70), 6)
        pen.poly([(off + 560, 900), (off + 650, 720), (off + 820, 720), (off + 900, 900)], (185, 90, 65), 6)
    pen.rect(-20, 900, 2 * PERIOD + 20, H, (235, 195, 130), 0)
    r = random.Random(9)
    for _ in range(40):
        x, y = r.uniform(0, PERIOD), r.uniform(920, 1150)
        for off in (0, PERIOD):
            pen.ell(x + off, y, 18, 5, (215, 170, 105), 0)
    for off in (0, PERIOD):
        for x in (150, 700):
            cactus(pen, off + x, 1120, 0.8)
    pen.rect(-20, 1200, 2 * PERIOD + 20, 1560, (75, 75, 85), 0)
    pen.rect(-20, 1200, 2 * PERIOD + 20, 1215, (230, 230, 230), 0)
    pen.rect(-20, 1545, 2 * PERIOD + 20, 1560, (230, 230, 230), 0)
    for x in range(0, 2 * PERIOD, 180):
        pen.rect(x, 1372, x + 100, 1388, (255, 210, 50), 0)
    return img


# ---------------------------------------------------------------- props
def cactus(pen, x, y, sc=1.0):
    g = (70, 150, 70)
    pen.rect(x - 28 * sc, y - 260 * sc, x + 28 * sc, y, g, 6, 28 * sc)
    pen.rect(x - 95 * sc, y - 190 * sc, x - 55 * sc, y - 90 * sc, g, 6, 20 * sc)
    pen.rect(x - 95 * sc, y - 110 * sc, x - 20 * sc, y - 75 * sc, g, 6, 16 * sc)
    pen.rect(x + 55 * sc, y - 230 * sc, x + 95 * sc, y - 140 * sc, g, 6, 20 * sc)
    pen.rect(x + 20 * sc, y - 160 * sc, x + 95 * sc, y - 125 * sc, g, 6, 16 * sc)


def tumbleweed(pen, x, y, t, r=70):
    pen.ell(x, y, r, r * 0.9, (170, 120, 60), 6)
    for i in range(7):
        a = t * 6 + i * 0.9
        pen.line([(x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.7), (x - math.cos(a + 1.3) * r * 0.7, y - math.sin(a + 1.3) * r * 0.6)],
                 (120, 80, 35), 5)


def cooler(pen, x, y, sc=1.0, tilt=0.0):
    """Orange sports-drink cooler; (x, y) = bottom center."""
    c, s_ = math.cos(tilt), math.sin(tilt)

    def tp(px, py):
        return (x + (px * c - py * s_) * sc, y + (px * s_ + py * c) * sc)
    body = [tp(-90, 0), tp(90, 0), tp(100, -230), tp(-100, -230)]
    pen.poly(body, (255, 140, 30), 7)
    pen.poly([tp(-110, -230), tp(110, -230), tp(110, -270), tp(-110, -270)], "white", 7)
    pen.poly([tp(-20, -150), tp(25, -150), tp(0, -110), tp(30, -110), tp(-15, -50), tp(0, -95), tp(-30, -95)], "white", 4)
    for sx in (-1, 1):
        pen.poly([tp(sx * 100, -200), tp(sx * 125, -200), tp(sx * 125, -170), tp(sx * 100, -170)], (230, 230, 230), 4)
    return tp


def splash(pen, x, y, k, color=(255, 150, 40)):
    """Liquid burst, k from 0 to 1."""
    r = random.Random(3)
    for i in range(22):
        a = r.uniform(-math.pi, 0); sp = r.uniform(150, 420)
        px = x + math.cos(a) * sp * k
        py = y + math.sin(a) * sp * k + 900 * k * k
        rr = r.uniform(14, 34) * (1 - 0.5 * k)
        pen.ell(px, py, rr, rr * 1.2, color, 4)


def salad_bowl(pen, x, y, sc=1.0):
    pen.ell(x, y - 30 * sc, 110 * sc, 40 * sc, (90, 180, 70), 5)
    pen.ell(x - 30 * sc, y - 50 * sc, 30 * sc, 18 * sc, (120, 210, 90), 4)
    pen.ell(x + 40 * sc, y - 45 * sc, 16 * sc, 16 * sc, (230, 70, 60), 4)
    pen.poly([(x - 120 * sc, y - 30 * sc), (x + 120 * sc, y - 30 * sc), (x + 80 * sc, y + 30 * sc), (x - 80 * sc, y + 30 * sc)],
             (240, 240, 245), 6)


def single_leaf(pen, x, y):
    pen.ell(x, y, 34, 18, (110, 200, 80), 4)
    pen.line([(x - 30, y), (x + 30, y)], (70, 150, 50), 3)


def pizza(pen, x, y, r=150):
    pen.ell(x, y, r, r * 0.55, (225, 160, 70), 7)
    pen.ell(x, y, r * 0.85, r * 0.45, (255, 215, 90), 0)
    for i in range(8):
        a = i * math.pi / 4 + 0.3
        pen.ell(x + math.cos(a) * r * 0.5, y + math.sin(a) * r * 0.27, r * 0.13, r * 0.08, (200, 50, 45), 4)
    for i in range(4):
        a = i * math.pi / 2
        pen.line([(x, y), (x + math.cos(a) * r * 0.85, y + math.sin(a) * r * 0.45)], (210, 150, 60), 3)


def pizza_slice(pen, x, y, ang, sc=1.0):
    c, s_ = math.cos(ang), math.sin(ang)
    pts = [(0, -60), (45, 50), (-45, 50)]
    pen.poly([(x + (px * c - py * s_) * sc, y + (px * s_ + py * c) * sc) for px, py in pts], (255, 215, 90), 5)
    pen.ell(x + (8 * c) * sc, y + (8 * s_) * sc, 10 * sc, 8 * sc, (200, 50, 45), 3)


def scale_prop(pen, x, y, reading, blink):
    pen.rect(x - 170, y - 60, x + 170, y, (200, 200, 210), 7, 10)
    pen.rect(x - 20, y - 520, x + 20, y - 60, (150, 150, 160), 6)
    pen.rect(x - 140, y - 700, x + 140, y - 500, (60, 60, 70), 7, 14)
    pen.rect(x - 115, y - 670, x + 115, y - 530, (20, 40, 20), 0, 8)
    col = (255, 60, 60) if reading == "ERROR" and blink else (120, 255, 120)
    pen.text(x, y - 600, reading, 60 if len(reading) > 4 else 72, col, 0)


def table(pen, x0, x1, y):
    pen.rect(x0, y, x1, y + 40, (200, 160, 110), 7, 10)
    for x in (x0 + 50, x1 - 50):
        pen.rect(x - 15, y + 40, x + 15, y + 330, (150, 110, 70), 5)


def phone(pen, x, y, sc, lines, color=(40, 40, 60), screen=(245, 245, 255)):
    p = Pen(pen.d._image, x, y, sc)
    p.rect(-170, -300, 170, 300, color, 8, 40)
    p.rect(-145, -250, 145, 250, screen, 0, 18)
    p.rect(-40, -282, 40, -268, (90, 90, 110), 0, 6)
    yy = -170
    for text, size, col in lines:
        p.text(0, yy, text, size, col, 0)
        yy += size * 1.5


def drum(pen, x, y, t, hit):
    pen.rect(x - 110, y - 160, x + 110, y, (200, 50, 60), 7, 10)
    pen.ell(x, y - 160, 110, 32, (240, 240, 230), 6)
    for i in range(5):
        pen.line([(x - 110 + i * 55, y - 150), (x - 85 + i * 55, y - 10)], (240, 200, 60), 4)
    if hit:
        for i in range(6):
            a = -math.pi / 2 + (i - 2.5) * 0.4
            pen.line([(x + math.cos(a) * 140, y - 170 + math.sin(a) * 60), (x + math.cos(a) * 200, y - 170 + math.sin(a) * 100)], GOLD, 7)


def mic_stand(pen, x, y):
    pen.line([(x, y), (x, y - 520)], (60, 60, 70), 12)
    pen.ell(x, y, 80, 18, (60, 60, 70), 5)
    pen.ell(x, y - 545, 28, 38, (90, 90, 100), 6)


def music_notes(pen, x, y, t, n=5, color=GOLD):
    for i in range(n):
        u = (t * 0.8 + i / n) % 1
        px = x + math.sin(u * 6 + i) * 120 + (i - n / 2) * 60
        py = y - u * 500
        pen.ell(px, py, 22, 16, color, 4)
        pen.line([(px + 18, py), (px + 18, py - 70)], OUT, 7)
        pen.line([(px + 18, py - 70), (px + 50, py - 50)], OUT, 7)


def bus(pen, x, y, t, faces=True):
    """Team bus, side view; (x, y) = road contact point at rear wheel area."""
    pen.rect(x, y - 420, x + 820, y - 60, PURPLE, 8, 40)
    pen.rect(x, y - 140, x + 820, y - 110, GOLD, 0)
    pen.text(x + 420, y - 175, "WAFFLES", 70, GOLD, 6)
    for i in range(5):
        wx = x + 60 + i * 140
        pen.rect(wx, y - 380, wx + 110, y - 270, (170, 220, 250), 6, 12)
        if faces and i in (1, 3):
            big = i == 1
            hr = 46 if big else 34
            pen.ell(wx + 55, y - 300, hr, hr, PURPLE, 4)
            pen.ell(wx + 55, y - 292, hr * 0.7, hr * 0.55, (150, 95, 60) if big else (255, 214, 170), 3)
            for sx in (-1, 1):
                pen.ell(wx + 55 + sx * hr * 0.3, y - 296, 7, 8, "white", 2)
    pen.rect(x + 740, y - 380, x + 810, y - 220, (170, 220, 250), 6, 12)
    for wx in (x + 160, x + 660):
        pen.ell(wx, y - 50, 70, 70, (30, 30, 35), 6)
        pen.ell(wx, y - 50, 30, 30, (160, 160, 170), 0)
        a = -t * 10
        pen.line([(wx + math.cos(a) * 28, y - 50 + math.sin(a) * 28), (wx - math.cos(a) * 28, y - 50 - math.sin(a) * 28)], OUT, 6)


def trophy(pen, x, y, sc=1.0):
    p = Pen(pen.d._image, x, y, sc)
    p.rect(-90, -40, 90, 0, (120, 80, 40), 6, 6)
    p.rect(-60, -110, 60, -40, (120, 80, 40), 6, 6)
    p.rect(-15, -200, 15, -110, GOLD, 5)
    p.poly([(-110, -420), (110, -420), (70, -230), (0, -200), (-70, -230)], GOLD, 7)
    for sx in (-1, 1):
        p.line([(sx * 105, -400), (sx * 160, -380), (sx * 150, -300), (sx * 80, -280)], OUT, 14)
        p.line([(sx * 105, -400), (sx * 160, -380), (sx * 150, -300), (sx * 80, -280)], GOLD, 7)
    star(p, 0, -330, 40, (255, 240, 150))


def confetti(frame, t, t0, n=40):
    pen = Pen(frame)
    for i in range(n):
        x = (i * 137 + (t - t0) * 90 * (1 + i % 3)) % W
        y = ((t - t0) * 420 * (1 + i % 4) + i * 77) % 1500
        pen.rect(x, y, x + 18, y + 30, [GOLD, PURPLE, "white", RED, (90, 200, 255)][i % 5], 0, 3)


def scoreboard(pen, home, away, clock, y=170):
    pen.rect(140, y, 940, y + 230, (25, 25, 32), 8, 18)
    pen.text(340, y + 55, "WAFFLES", 44, GOLD, 0)
    pen.text(740, y + 55, "HOT SAUCE", 44, (255, 110, 90), 0)
    pen.text(340, y + 150, str(home), 100, "white", 0)
    pen.text(740, y + 150, str(away), 100, "white", 0)
    pen.rect(470, y + 100, 610, y + 200, (60, 15, 15), 4, 10)
    pen.text(540, y + 150, clock, 52, (255, 80, 60), 0)
