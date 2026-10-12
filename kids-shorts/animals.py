"""Cute animal families for the kids' song shorts. Every draw function uses local coords:
origin = between the feet, y negative is up, about 330 units tall at scale 1."""
import math
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "nfl-short"))
from toon import Pen, S, OUT, GOLD, star  # noqa: E402

PINK, BLUE = (245, 95, 155), (60, 130, 230)


def w(pen, n):
    return max(1, int(n * S * pen.sc))


def eyes(pen, cx, cy, r, look, blink, gap):
    for sx in (-1, 1):
        x = cx + sx * gap
        if blink:
            pen.d.arc([pen.p(x - r * 0.8, cy - r * 0.6), pen.p(x + r * 0.8, cy + r * 0.6)], 20, 160, fill=OUT, width=w(pen, 6))
        else:
            pen.ell(x, cy, r, r * 1.1, "white", 5)
            pen.ell(x + look[0] * r * 0.3, cy + look[1] * r * 0.3, r * 0.5, r * 0.55, OUT, 0)
            pen.ell(x + look[0] * r * 0.3 - r * 0.18, cy + look[1] * r * 0.3 - r * 0.2, r * 0.17, r * 0.17, "white", 0)


def cheeks(pen, cx, cy, gap, r=18):
    for sx in (-1, 1):
        pen.ell(cx + sx * gap, cy, r, r * 0.6, (250, 150, 165), 0)


def smile_or_sing(pen, cx, cy, size, mouth):
    if mouth > 0.08:
        pen.ell(cx, cy, size * 0.55, size * (0.12 + 0.4 * mouth), (150, 30, 50), 5)
        pen.ell(cx, cy + size * 0.18 * mouth, size * 0.3, size * 0.12 * mouth + 1, (250, 120, 140), 0)
    else:
        pen.d.arc([pen.p(cx - size * 0.6, cy - size * 0.5), pen.p(cx + size * 0.6, cy + size * 0.3)], 25, 155, fill=OUT, width=w(pen, 6))


def bow(pen, x, y, s=1.0, col=PINK):
    pen.poly([(x - 40 * s, y - 24 * s), (x, y), (x - 40 * s, y + 24 * s)], col, 5)
    pen.poly([(x + 40 * s, y - 24 * s), (x, y), (x + 40 * s, y + 24 * s)], col, 5)
    pen.ell(x, y, 11 * s, 11 * s, tuple(min(255, c + 30) for c in col), 4)


def accessory(pen, kind, head_top, neck_y, head_x=0):
    if kind == "mommy":
        bow(pen, head_x - 40, head_top + 10)
    elif kind == "daddy":
        bow(pen, head_x, neck_y, 0.75, BLUE)
    elif kind == "baby":
        pen.d.arc([pen.p(head_x - 12, head_top - 40), pen.p(head_x + 28, head_top)], 180, 450, fill=OUT, width=w(pen, 6))


# ---------------------------------------------------------------- frog
FROG = {"baby": (150, 215, 90), "mommy": (110, 200, 100), "daddy": (70, 165, 80)}


def frog(pen, kind, t, mouth=0.0, blink=False, look=(0, 0), arms="down", action=0.0):
    col = FROG[kind]; dark = tuple(int(c * 0.75) for c in col)
    for sx in (-1, 1):
        pen.ell(sx * 95, -38, 62, 42, dark, 6)
        pen.ell(sx * 125, -8, 48, 15, dark, 5)
    pen.ell(0, -92, 115, 95, col, 7)
    pen.ell(0, -72, 76, 60, (215, 240, 170), 0)
    arm_y = -175 + 10 * math.sin(t * 10) if arms == "up" else -62
    for sx in (-1, 1):
        pen.ell(sx * (125 if arms == "up" else 82), arm_y, 22, 36, col, 6)
    pen.ell(0, -192, 122, 86, col, 7)
    for sx in (-1, 1):
        pen.ell(sx * 62, -262, 44, 44, col, 7)
    eyes(pen, 0, -264, 30, look, blink, 62)
    cheeks(pen, 0, -192, 88)
    smile_or_sing(pen, 0, -178, 80, mouth)
    accessory(pen, kind, -306, -112)


# ---------------------------------------------------------------- duck
DUCK = {"baby": (255, 220, 60), "mommy": (250, 250, 245), "daddy": (245, 245, 240)}


def duck(pen, kind, t, mouth=0.0, blink=False, look=(0, 0), arms="down", action=0.0):
    col = DUCK[kind]; shade = tuple(int(c * 0.85) for c in col)
    orange = (255, 150, 40)
    for sx in (-1, 1):
        pen.poly([(sx * 40 - 45, 0), (sx * 40 + 45, 0), (sx * 40, -40)], orange, 5)
        pen.line([(sx * 40, -40), (sx * 40, -70)], orange, 12)
    pen.poly([(90, -150), (165, -205), (140, -120)], col, 6)  # tail
    pen.ell(0, -130, 125, 90, col, 7)
    flap = 25 * math.sin(t * 18) if arms == "up" else 0
    for sx in (-1, 1):
        pen.ell(sx * 110, -140 - flap * (1 if sx > 0 else -1) - (40 if arms == "up" else 0), 40, 62, shade, 6)
    head_col = (60, 150, 80) if kind == "daddy" else col
    pen.ell(0, -265, 90, 85, head_col, 7)
    if kind == "daddy":
        pen.rect(-70, -195, 70, -180, "white", 0, 6)
    eyes(pen, 0, -285, 22, look, blink, 36)
    cheeks(pen, 0, -250, 60, 15)
    pen.ell(0, -232 + 6 * mouth, 52, 18, orange, 5)  # lower beak
    pen.ell(0, -246 - 8 * mouth, 56, 19, (255, 170, 60), 5)  # upper beak
    if kind == "baby":
        for i in range(3):
            pen.line([(-10 + i * 10, -345), (-20 + i * 16, -380)], (240, 190, 40), 6)
    else:
        accessory(pen, kind, -345, -185)


# ---------------------------------------------------------------- dino
DINO = {"baby": (140, 220, 120), "mommy": (240, 150, 190), "daddy": (100, 160, 230)}


def dino(pen, kind, t, mouth=0.0, blink=False, look=(0, 0), arms="down", action=0.0):
    col = DINO[kind]; dark = tuple(int(c * 0.78) for c in col)
    belly = (250, 235, 190)
    pen.poly([(70, -60), (230, -40 + 15 * math.sin(t * 4)), (90, -120)], col, 6)  # tail
    for sx in (-1, 1):
        pen.ell(sx * 55, -30, 45, 40, dark, 6)
        pen.ell(sx * 62, -6, 50, 16, dark, 5)
    pen.ell(0, -120, 105, 105, col, 7)
    pen.ell(0, -105, 68, 75, belly, 0)
    for i in range(5):  # back spikes
        a = math.pi * (0.62 + 0.11 * i)
        x, y = math.cos(a) * 120 + 20, -150 + math.sin(a) * -110
        pen.poly([(x - 22, y + 10), (x, y - 34), (x + 22, y + 10)], (255, 190, 70), 5)
    ay = -230 if arms == "up" else -130
    for sx in (-1, 1):
        pen.ell(sx * 92, ay + 6 * math.sin(t * 12), 20, 30, col, 5)
    pen.ell(-15, -275, 110, 92, col, 7)
    eyes(pen, -15, -300, 26, look, blink, 45)
    cheeks(pen, -15, -262, 75)
    smile_or_sing(pen, -15, -240, 85, mouth)
    for sx in (-1, 1):
        pen.ell(-15 + sx * 20, -270, 5, 4, dark, 0)
    accessory(pen, kind, -360, -185, -15)


# ---------------------------------------------------------------- elephant
ELE = {"baby": (175, 195, 225), "mommy": (190, 170, 215), "daddy": (140, 160, 195)}


def elephant(pen, kind, t, mouth=0.0, blink=False, look=(0, 0), arms="down", action=0.0):
    col = ELE[kind]; dark = tuple(int(c * 0.8) for c in col)
    for sx in (-1, 1):
        pen.rect(sx * 60 - 32, -90, sx * 60 + 32, 0, col, 6, 14)
        pen.ell(sx * 60, -8, 34, 12, (240, 235, 230), 0)
    pen.ell(0, -135, 120, 100, col, 7)
    flap = 0.15 * math.sin(t * 8) if arms == "up" else 0.03 * math.sin(t * 3)
    for sx in (-1, 1):
        pen.ell(sx * 125 * (1 + flap), -265, 85, 95, dark, 7)
        pen.ell(sx * 125 * (1 + flap), -265, 55, 65, (240, 180, 200), 0)
    pen.ell(0, -265, 100, 92, col, 7)
    trunk_up = action
    pts = [(0, -235), (0, -185), (10 + 70 * trunk_up, -150 - 60 * trunk_up), (40 + 150 * trunk_up, -150 - 170 * trunk_up)]
    pen.line(pts, OUT, 50); pen.line(pts, col, 36)
    pen.ell(pts[-1][0], pts[-1][1], 20, 16, dark, 4)
    eyes(pen, 0, -285, 22, look, blink, 42)
    cheeks(pen, 0, -255, 66)
    if mouth > 0.08:
        pen.ell(-42, -212, 20, 8 + 20 * mouth, (150, 30, 50), 4)
    accessory(pen, kind, -355, -175)


# ---------------------------------------------------------------- penguin
PEN = {"baby": (120, 130, 150), "mommy": (40, 45, 60), "daddy": (30, 35, 50)}


def penguin(pen, kind, t, mouth=0.0, blink=False, look=(0, 0), arms="down", action=0.0):
    col = PEN[kind]
    orange = (255, 160, 40)
    for sx in (-1, 1):
        pen.ell(sx * 45, -8, 45, 16, orange, 5)
    pen.ell(0, -150, 115, 150, col, 7)
    pen.ell(0, -130, 82, 118, (250, 250, 252) if kind != "baby" else (230, 235, 240), 0)
    ay = -230 if arms == "up" else -140
    for sx in (-1, 1):
        ang = (0.9 if arms == "up" else 0.25) + 0.15 * math.sin(t * 14)
        x0, y0 = sx * 100, -200
        pen.poly([(x0, y0), (x0 + sx * 70 * math.sin(ang), y0 + 140 * math.cos(ang) - (60 if arms == "up" else 0)),
                  (x0 + sx * 20, y0 + 60)], col, 6)
    pen.ell(0, -275, 95, 85, col, 7)
    pen.ell(0, -262, 70, 58, (250, 250, 252), 0)
    eyes(pen, 0, -285, 20, look, blink, 34)
    cheeks(pen, 0, -255, 52, 14)
    pen.poly([(-26, -255 - 6 * mouth), (26, -255 - 6 * mouth), (0, -225)], orange, 4)
    if mouth > 0.08:
        pen.poly([(-22, -250 + 4 * mouth), (22, -250 + 4 * mouth), (0, -225 + 20 * mouth)], (220, 120, 30), 3)
    if kind == "baby":
        for i in range(4):
            pen.line([(-15 + i * 10, -355), (-25 + i * 16, -385)], col, 6)
    else:
        accessory(pen, kind, -355, -190)


DRAW = {"frog": frog, "duck": duck, "dino": dino, "elephant": elephant, "penguin": penguin}
