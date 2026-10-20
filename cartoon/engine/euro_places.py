"""More 'Paris winter' places (bakery, cafe, park, building hall) and their props."""
import math

import cairo
import numpy as np

from . import scene
from .character import OUTLINE, ellipse, fill_stroke, hexrgb, ink, limb, shade
from .euro import _poly, _rect, _vgrad, rooftops

W, H, GROUND = scene.W, scene.H, scene.GROUND
rgb = hexrgb


def _sign(ctx, x, y, w, h, words, bg="#24402f", fg=(0.92, 0.78, 0.4), size=56):
    _rect(ctx, x, y, w, h, bg)
    ctx.rectangle(x + 10, y + 10, w - 20, h - 20)
    ink(ctx, fg, 3)
    scene.text(ctx, words, x + w / 2, y + h / 2 + size * 0.36, size, fg, stroke=0)


def _hanging_lamp(ctx, x, y, color="#3f5b48"):
    limb(ctx, [(x, -200), (x, y)], 5, rgb("#2a2420"), ow=1.5)
    _poly(ctx, [(x - 50, y), (x + 50, y), (x + 100, y + 80), (x - 100, y + 80)], color)
    ellipse(ctx, x, y + 84, 22, 16)
    fill_stroke(ctx, rgb("#fff1b8"), ow=3)


def _corners(ctx, cx=560, cy=900, a=0.45):
    g = cairo.RadialGradient(cx, cy, 300, cx, cy, 1300)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.08, 0.04, 0.02, a)
    ctx.rectangle(-200, -200, W + 400, H + 400)
    ctx.set_source(g)
    ctx.fill()


# ------------------------------------------------------------------ props
def baguette(ctx, x, y, ang=0.0, length=300, color="#d9a352", fresh=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    c = rgb(color)
    c = tuple(a + (b - a) * fresh for a, b in zip(c, rgb("#c98a3a")))
    scene.rrect(ctx, -length / 2, -20, length, 40, 20)
    fill_stroke(ctx, c, ow=4.5)
    for k in range(5):
        sx = -length / 2 + 40 + k * (length - 80) / 4
        ctx.move_to(sx - 16, 8)
        ctx.curve_to(sx - 6, -4, sx + 6, -10, sx + 18, -12)
    ink(ctx, shade(c, 0.6), 3)
    ctx.restore()


def bread_basket(ctx, x, y):
    for k in range(4):
        baguette(ctx, x - 30 + k * 22, y - 70, -1.25 + k * 0.08, 200)
    _poly(ctx, [(x - 80, y - 40), (x + 80, y - 40), (x + 66, y + 20), (x - 66, y + 20)], "#9a6a3a", ow=4)
    for k in range(4):
        ctx.move_to(x - 76 + k * 4, y - 26 + k * 12)
        ctx.line_to(x + 76 - k * 4, y - 26 + k * 12)
    ink(ctx, rgb("#6b4524"), 2)


def boule(ctx, x, y, r=46):
    ctx.move_to(x - r, y)
    ctx.curve_to(x - r, y - r * 1.1, x + r, y - r * 1.1, x + r, y)
    ctx.close_path()
    fill_stroke(ctx, rgb("#c98a3a"), ow=4)
    ctx.move_to(x - r * 0.5, y - r * 0.5)
    ctx.line_to(x + r * 0.5, y - r * 0.5)
    ink(ctx, rgb("#f1d9a8"), 3)


def croissant(ctx, x, y, s=1.0):
    for k, (dx, r) in enumerate(((-34, 16), (-16, 22), (6, 25), (28, 22), (46, 16))):
        ellipse(ctx, x + dx * s, y - abs(dx) * 0.25 * s, r * s, r * 0.8 * s)
        fill_stroke(ctx, rgb("#d79a46"), ow=3.5)


def cup(ctx, x, y, tilt=0.0, steam_t=None):
    if steam_t is not None:
        scene.steam(ctx, x, y - 40, steam_t)
    ellipse(ctx, x, y + 8, 50, 10)
    fill_stroke(ctx, rgb("#f1ece2"), ow=3.5)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(tilt)
    ctx.move_to(-30, -44)
    ctx.line_to(30, -44)
    ctx.curve_to(30, -10, 22, 4, 0, 4)
    ctx.curve_to(-22, 4, -30, -10, -30, -44)
    ctx.close_path()
    fill_stroke(ctx, rgb("#f1ece2"), ow=3.5)
    ctx.arc(34, -26, 12, -1.6, 1.6)
    ink(ctx, OUTLINE, 4)
    ellipse(ctx, 0, -44, 30, 7)
    fill_stroke(ctx, rgb("#5a321c"), ow=3)
    ctx.restore()


def stain(ctx, x, y, r):
    if r <= 1:
        return
    ctx.save()
    ctx.translate(x, y)
    pts = 14
    for i in range(pts + 1):
        a = 2 * math.pi * i / pts
        rr = r * (0.8 + 0.25 * math.sin(i * 2.7) + 0.12 * math.cos(i * 5.1))
        (ctx.move_to if i == 0 else ctx.line_to)(math.cos(a) * rr, math.sin(a) * rr * 0.9)
    ctx.close_path()
    ctx.set_source_rgba(0.36, 0.2, 0.1, 0.85)
    ctx.fill()
    ctx.restore()


def napkin(ctx, x, y, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    _poly(ctx, [(-34, -30), (30, -36), (38, 26), (-30, 34)], "#f6f3ec", ow=3.5)
    ctx.move_to(-20, -10)
    ctx.line_to(20, 12)
    ink(ctx, rgb("#c9c2b4"), 2)
    ctx.restore()


def sack(ctx, x, y, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.move_to(-70, 40)
    ctx.curve_to(-84, -20, -70, -70, -40, -86)
    ctx.line_to(40, -86)
    ctx.curve_to(70, -70, 84, -20, 70, 40)
    ctx.curve_to(30, 52, -30, 52, -70, 40)
    ctx.close_path()
    fill_stroke(ctx, rgb("#e3d4b0"))
    ctx.move_to(-40, -86)
    ctx.curve_to(-20, -110, 20, -110, 40, -86)
    fill_stroke(ctx, rgb("#e3d4b0"), ow=4)
    limb(ctx, [(-30, -84), (30, -84)], 8, rgb("#8a6a3a"), ow=2.5)
    scene.text(ctx, "FARINE", 0, -6, 34, (0.5, 0.25, 0.2), stroke=0)
    scene.text(ctx, "25 kg", 0, 30, 26, (0.5, 0.25, 0.2), stroke=0)
    ctx.restore()


def duck(ctx, x, y, t, facing=1, mood="calm", s=1.0, swim=True):
    """Mallard duck. mood: calm | angry | happy | eat."""
    bob = math.sin(t * 3 + x * 0.01) * 4
    ctx.save()
    ctx.translate(x, y + bob)
    ctx.scale(facing * s, s)
    if mood == "angry":
        ctx.rotate(0.06 * math.sin(t * 30))
    ctx.move_to(-70, -10)
    ctx.curve_to(-60, -50, 40, -56, 60, -24)
    ctx.curve_to(70, 0, 40, 14, -20, 14)
    ctx.curve_to(-60, 14, -86, 0, -96, -30)
    ctx.close_path()
    fill_stroke(ctx, rgb("#8e7a68"))
    ctx.move_to(-40, -30)
    ctx.curve_to(-10, -40, 20, -38, 36, -26)
    ink(ctx, rgb("#5f5044"), 3)
    ellipse(ctx, -20, -24, 30, 12)
    ctx.set_source_rgba(0.3, 0.38, 0.6, 0.6)
    ctx.fill()
    head_dy = -8 if mood == "eat" and math.sin(t * 9) > 0 else 0
    limb(ctx, [(40, -30), (50, -62 + head_dy)], 22, rgb("#2f6b4a"), ow=4)
    ellipse(ctx, 54, -78 + head_dy, 26, 22)
    fill_stroke(ctx, rgb("#2f6b4a"))
    ctx.move_to(70, -80 + head_dy)
    ctx.curve_to(96, -82 + head_dy, 104, -72 + head_dy, 98, -66 + head_dy)
    ctx.line_to(72, -68 + head_dy)
    ctx.close_path()
    fill_stroke(ctx, rgb("#e3b63a"), ow=3.5)
    ellipse(ctx, 60, -84 + head_dy, 5, 5)
    ctx.set_source_rgb(0.05, 0.05, 0.05)
    ctx.fill()
    if mood == "angry":
        ctx.move_to(50, -96 + head_dy)
        ctx.line_to(68, -90 + head_dy)
        ink(ctx, OUTLINE, 4)
    limb(ctx, [(38, -46), (48, -48)], 8, (0.95, 0.95, 0.95), ow=1.5)
    if swim:
        for k in range(2):
            ctx.move_to(-110 - k * 20, 12 + k * 6)
            ctx.curve_to(-40, 20 + k * 6, 40, 20 + k * 6, 90 + k * 20, 10 + k * 6)
        ink(ctx, (0.85, 0.92, 1.0), 3)
    ctx.restore()


# ------------------------------------------------------------------ backgrounds
def boulangerie(ctx):
    _vgrad(ctx, -200, -200, W + 400, 1400, "#c7964f", "#e0bf86")
    # tiled lower wall
    ctx.rectangle(-200, 1150, W + 400, 420)
    ctx.set_source_rgb(0.93, 0.9, 0.82)
    ctx.fill()
    ctx.set_source_rgba(0.35, 0.45, 0.55, 0.45)
    ctx.set_line_width(2.5)
    for y in range(1150, 1560, 52):
        ctx.move_to(-200, y)
        ctx.line_to(W + 200, y)
    for x in range(-200, W + 200, 52):
        ctx.move_to(x, 1150)
        ctx.line_to(x, 1560)
    ctx.stroke()
    _rect(ctx, -200, 1136, W + 400, 22, "#3f6a89", ow=4)
    # terracotta floor
    _vgrad(ctx, -200, GROUND - 30, W + 400, 500, "#a85a3a", "#7a3e26")
    ctx.set_source_rgba(0.25, 0.1, 0.05, 0.4)
    ctx.set_line_width(3)
    for i, y in enumerate(range(GROUND - 30, H + 200, 60)):
        ctx.move_to(-200, y)
        ctx.line_to(W + 200, y)
        for x in range(-200 + (i % 2) * 60, W + 200, 120):
            ctx.move_to(x, y)
            ctx.line_to(x, y + 60)
    ctx.stroke()
    _sign(ctx, 140, 230, 800, 120, "BOULANGERIE", size=62)
    # shelves of bread
    for sy in (560, 780):
        _rect(ctx, 40, sy, 640, 22, "#7a5232")
        for k, bx in enumerate(range(90, 650, 140)):
            if (k + sy // 10) % 2:
                bread_basket(ctx, bx + 40, sy - 6)
            else:
                boule(ctx, bx + 20, sy - 2)
                boule(ctx, bx + 80, sy - 2, 38)
    for k in range(5):
        croissant(ctx, 120 + k * 120, 990, 0.9)
    _rect(ctx, 40, 1002, 640, 20, "#7a5232")
    # brick bread oven (right)
    for row, y in enumerate(range(760, 1240, 34)):
        for x in range(730 - (row % 2) * 30, 1100, 60):
            ctx.rectangle(x, y, 56, 30)
    ctx.set_source_rgb(0.62, 0.3, 0.2)
    ctx.fill_preserve()
    ink(ctx, rgb("#3e1c12"), 2)
    ctx.move_to(800, 1180)
    ctx.line_to(800, 960)
    ctx.curve_to(800, 860, 1000, 860, 1000, 960)
    ctx.line_to(1000, 1180)
    ctx.close_path()
    fill_stroke(ctx, rgb("#1e1612"))
    ctx.move_to(820, 1170)
    ctx.line_to(820, 966)
    ctx.curve_to(820, 884, 980, 884, 980, 966)
    ctx.line_to(980, 1170)
    ctx.close_path()
    g = cairo.RadialGradient(900, 1100, 10, 900, 1080, 200)
    g.add_color_stop_rgb(0, 1.0, 0.75, 0.3)
    g.add_color_stop_rgb(1, 0.6, 0.15, 0.05)
    ctx.set_source(g)
    ctx.fill()
    _rect(ctx, 780, 1180, 240, 26, "#4a3a32", ow=4)
    # glass pastry counter (left foreground-back)
    _rect(ctx, 60, 1220, 600, 340, "#6b4228")
    _rect(ctx, 80, 1236, 560, 120, "#d8e6ea", ow=4)
    for k in range(6):
        ellipse(ctx, 120 + k * 92, 1320, 34, 16)
        fill_stroke(ctx, rgb(["#7a3a2a", "#e6c46a", "#c95a7a"][k % 3]), ow=3)
    ctx.move_to(90, 1250)
    ctx.line_to(200, 1240)
    ink(ctx, (1, 1, 1), 4)
    _rect(ctx, 50, 1206, 620, 20, "#4a2c1a", ow=4)
    # door with snowy street on the far left
    _rect(ctx, -170, 700, 200, 860, "#24402f")
    ctx.save()
    ctx.rectangle(-150, 730, 160, 500)
    ctx.clip()
    rooftops(ctx, -150, 730, 160, 500, seed=4)
    ctx.restore()
    ctx.rectangle(-150, 730, 160, 500)
    ink(ctx, OUTLINE, 5)
    _hanging_lamp(ctx, 330, 110, "#7a2626")
    _hanging_lamp(ctx, 760, 130, "#7a2626")
    _corners(ctx)


def cafe(ctx):
    _vgrad(ctx, -200, -200, W + 400, 1300, "#6e2a26", "#8c3a2c")
    ctx.set_source_rgba(1, 0.85, 0.55, 0.05)
    for x in range(-200, W + 200, 90):
        ctx.rectangle(x, -200, 40, 1300)
    ctx.fill()
    _vgrad(ctx, -200, 1100, W + 400, 460, "#4a2c1a", "#2e1a10")
    for x in range(-180, W + 200, 200):
        ctx.rectangle(x, 1140, 170, 380)
        ink(ctx, rgb("#20120a"), 4)
    _rect(ctx, -200, 1090, W + 400, 26, "#c79a4a", ow=4)
    # big mirror with soft reflections
    _rect(ctx, 60, 360, 520, 600, "#b8913f")
    _vgrad(ctx, 84, 384, 472, 552, "#5d6a6e", "#8d9696")
    for k in range(3):
        ctx.move_to(120 + k * 120, 400)
        ctx.line_to(60 + k * 120, 920)
    ink(ctx, (1, 1, 1), 6)
    # chalkboard menu
    _rect(ctx, 650, 360, 360, 300, "#6b4a33")
    _rect(ctx, 670, 380, 320, 260, "#263027", ow=3)
    for i, line in enumerate(("Menu", "Cafe ...... 2", "Creme ..... 3", "Chocolat .. 3")):
        scene.text(ctx, line, 830, 440 + i * 56, 38 if i else 46, (0.93, 0.92, 0.86), stroke=0)
    # bar with espresso machine
    _rect(ctx, 640, 1060, 520, 500, "#5a3420")
    _rect(ctx, 630, 1040, 540, 28, "#c9c2b4")
    _rect(ctx, 760, 860, 220, 180, "#b8913f")
    ellipse(ctx, 870, 850, 110, 50)
    fill_stroke(ctx, rgb("#c9a44a"))
    ellipse(ctx, 870, 790, 26, 22)
    fill_stroke(ctx, rgb("#3a2a20"), ow=4)
    for bx in (800, 940):
        limb(ctx, [(bx, 1000), (bx, 1030)], 12, rgb("#2a2a2a"), ow=3)
    for k in range(6):  # bottles
        _rect(ctx, 680 + k * 70, 720, 30, 100, ["#2f5a3a", "#6b2a2a", "#c9a44a"][k % 3], ow=3)
        _rect(ctx, 688 + k * 70, 690, 14, 32, "#2a2a2a", ow=2.5)
    _rect(ctx, 650, 820, 460, 16, "#6b4a33", ow=3)
    # mosaic floor
    _vgrad(ctx, -200, GROUND - 30, W + 400, 500, "#e7dfcd", "#c9bea6")
    ctx.set_source_rgba(0.3, 0.2, 0.15, 0.25)
    for j, y in enumerate(range(GROUND - 20, H + 200, 30)):
        for x in range(-200 + (j % 2) * 15, W + 200, 30):
            ctx.rectangle(x, y, 26, 26)
    ctx.fill()
    _rect(ctx, -200, GROUND + 80, W + 400, 26, "#7a2a26", ow=3)
    _hanging_lamp(ctx, 300, 300, "#c9a44a")
    _hanging_lamp(ctx, 820, 260, "#c9a44a")
    _corners(ctx)


def bistro_table(ctx, x, top_y):
    limb(ctx, [(x, top_y + 10), (x, GROUND - 14)], 16, rgb("#2a2a2a"), ow=4)
    ellipse(ctx, x, GROUND - 6, 70, 14)
    fill_stroke(ctx, rgb("#2a2a2a"), ow=4)
    ellipse(ctx, x, top_y, 150, 26)
    fill_stroke(ctx, rgb("#e9e4dc"))
    ctx.move_to(x - 120, top_y - 6)
    ctx.curve_to(x - 60, top_y + 4, x + 20, top_y - 12, x + 100, top_y + 2)
    ink(ctx, rgb("#b9b2a6"), 2)


def eiffel(ctx, x, base, h, color=(0.5, 0.5, 0.62)):
    ctx.save()
    for d in (-1, 1):
        ctx.move_to(x + d * h * 0.28, base)
        ctx.curve_to(x + d * h * 0.14, base - h * 0.3, x + d * h * 0.06, base - h * 0.6, x + d * h * 0.012, base - h)
    ink(ctx, color, 5)
    for k, f in enumerate((0.28, 0.55, 0.8)):
        w = h * (0.2 - f * 0.17)
        ctx.move_to(x - w, base - h * f)
        ctx.line_to(x + w, base - h * f)
        ink(ctx, color, 6 - k)
    ctx.move_to(x - h * 0.12, base)
    ctx.curve_to(x - h * 0.06, base - h * 0.14, x + h * 0.06, base - h * 0.14, x + h * 0.12, base)
    ink(ctx, color, 4)
    for i in range(10):  # lattice hint
        f = 0.05 + i * 0.08
        w = h * (0.25 - f * 0.22)
        ctx.move_to(x - w, base - h * f)
        ctx.line_to(x + w * 0.6, base - h * (f + 0.08))
    ink(ctx, color, 1.5)
    ctx.restore()


def _tree(ctx, x, y, length, ang, depth, rng):
    if depth == 0 or length < 8:
        return
    x2 = x + math.sin(ang) * length
    y2 = y - math.cos(ang) * length
    ctx.move_to(x, y)
    ctx.line_to(x2, y2)
    ink(ctx, rgb("#3b2c26"), max(1.5, depth * 2.6))
    if depth <= 3:  # snow on the branch
        ctx.move_to(x, y - 3)
        ctx.line_to(x2, y2 - 3)
        ctx.set_source_rgba(0.96, 0.97, 1, 0.9)
        ctx.set_line_width(max(1.2, depth * 1.4))
        ctx.stroke()
    for d in (-1, 1):
        _tree(ctx, x2, y2, length * rng.uniform(0.62, 0.78), ang + d * rng.uniform(0.25, 0.6), depth - 1, rng)


def paris_park(ctx):
    _vgrad(ctx, -200, -200, W + 400, 1300, "#55617f", "#e0b9a6")  # late-afternoon winter sky
    eiffel(ctx, 820, 1120, 760)
    rooftops(ctx, -200, 900, W + 400, 300, seed=12)
    # snowy ground
    _vgrad(ctx, -200, 1150, W + 400, 1000, "#eef1f6", "#d9dfea")
    # pond: frozen edge, open water in the middle
    ellipse(ctx, 600, 1330, 560, 110)
    fill_stroke(ctx, rgb("#bcd6e6"))
    ellipse(ctx, 640, 1336, 420, 70)
    _g = cairo.LinearGradient(0, 1270, 0, 1400)
    _g.add_color_stop_rgb(0, 0.28, 0.4, 0.55)
    _g.add_color_stop_rgb(1, 0.4, 0.55, 0.68)
    ctx.set_source(_g)
    ctx.fill()
    for k in range(4):
        ctx.move_to(360 + k * 120, 1320 + (k % 2) * 20)
        ctx.line_to(420 + k * 120, 1320 + (k % 2) * 20)
    ink(ctx, (0.85, 0.92, 1.0), 3)
    rng = np.random.default_rng(3)
    for tx, ln in ((80, 220), (1000, 250), (-60, 180)):
        _tree(ctx, tx, 1200, ln, rng.uniform(-0.08, 0.08), 7, rng)
    # iron fence
    for x in range(-200, W + 200, 40):
        limb(ctx, [(x, 1480), (x, 1380)], 6, rgb("#1f2420"), ow=1.5)
        _poly(ctx, [(x - 8, 1384), (x, 1362), (x + 8, 1384)], "#1f2420", ow=1.5)
    limb(ctx, [(-200, 1400), (W + 200, 1400)], 7, rgb("#1f2420"), ow=1.5)
    limb(ctx, [(-200, 1470), (W + 200, 1470)], 7, rgb("#1f2420"), ow=1.5)
    # path in front
    _vgrad(ctx, -200, 1500, W + 400, 700, "#e6e8ee", "#cfd5e0")
    for x in range(-200, W + 200, 160):
        ellipse(ctx, x + 60, 1620 + (x % 3) * 40, 60, 8)
        ctx.set_source_rgba(0.7, 0.75, 0.85, 0.5)
        ctx.fill()
    # bench
    _rect(ctx, 80, 1430, 300, 22, "#3f6a4a", ow=4)
    _rect(ctx, 80, 1380, 300, 22, "#3f6a4a", ow=4)
    for lx in (100, 340):
        limb(ctx, [(lx, 1450), (lx, GROUND)], 10, rgb("#1f2420"), ow=3)
    ctx.rectangle(78, 1372, 304, 10)
    ctx.set_source_rgb(0.96, 0.97, 1)
    ctx.fill()
    # lamp post
    limb(ctx, [(1010, 1580), (1010, 980)], 18, rgb("#1f2a24"), ow=4)
    _poly(ctx, [(970, 980), (1050, 980), (1040, 890), (980, 890)], "#f3d98c")
    _poly(ctx, [(960, 890), (1060, 890), (1010, 850)], "#1f2a24")


def building_hall(ctx):
    _vgrad(ctx, -200, -200, W + 400, 1800, "#cdbf9f", "#e2d6bb")
    _vgrad(ctx, -200, 1100, W + 400, 500, "#7c5a3e", "#5a3e28")  # wood panelling
    for y in (300, 1080):  # mouldings
        _rect(ctx, -200, y, W + 400, 22, "#b9a884", ow=3)
    for x in range(-150, W + 200, 260):
        ctx.rectangle(x, 360, 220, 680)
        ink(ctx, rgb("#a8966f"), 3)
    # wooden letterboxes
    _rect(ctx, 40, 820, 320, 230, "#6b4a33")
    for r in range(3):
        for c in range(4):
            _rect(ctx, 54 + c * 76, 834 + r * 70, 66, 58, "#7c5a3e", ow=3)
            ctx.move_to(64 + c * 76, 850 + r * 70)
            ctx.line_to(110 + c * 76, 850 + r * 70)
            ink(ctx, rgb("#2a1a10"), 3)
    # old cage lift
    _rect(ctx, 430, 520, 260, 1040, "#2a2624")
    ctx.save()
    ctx.rectangle(450, 540, 220, 1000)
    ctx.clip()
    _vgrad(ctx, 450, 540, 220, 1000, "#6b5a3e", "#3a2e22")
    for k in range(-10, 20):
        ctx.move_to(450 + k * 40, 540)
        ctx.line_to(450 + k * 40 + 400, 1540)
        ctx.move_to(450 + k * 40, 540)
        ctx.line_to(450 + k * 40 - 400, 1540)
    ink(ctx, rgb("#1a1614"), 3)
    ctx.restore()
    _rect(ctx, 420, 500, 280, 30, "#b8913f", ow=4)
    # staircase with wrought-iron rail rising to the right
    steps = 12
    for i in range(steps):
        x = 740 + i * 46
        y = GROUND - (i + 1) * 52
        _rect(ctx, x, y, 500, 52, "#8a5a3a", ow=3)
    for i in range(steps + 1):
        bx = 760 + i * 46
        by = GROUND - i * 52 - 52
        limb(ctx, [(bx, by), (bx, by - 150)], 5, rgb("#1a1614"), ow=1.2)
        ctx.arc(bx, by - 75, 10, 0, 2 * math.pi)
        ink(ctx, rgb("#1a1614"), 2.5)
    limb(ctx, [(740, GROUND - 200), (760 + steps * 46, GROUND - steps * 52 - 200)], 16, rgb("#5a3420"), ow=3)
    # checkered marble floor
    ctx.rectangle(-200, GROUND - 30, W + 400, 600)
    ctx.set_source_rgb(0.93, 0.91, 0.86)
    ctx.fill()
    ctx.set_source_rgb(0.16, 0.15, 0.15)
    for j, y in enumerate(range(GROUND - 30, H + 200, 70)):
        for i, x in enumerate(range(-200, W + 200, 70)):
            if (i + j) % 2:
                ctx.rectangle(x, y, 70, 70)
    ctx.fill()
    # wall sconce
    _poly(ctx, [(260, 620), (330, 620), (318, 560), (272, 560)], "#f3d98c", ow=4)
    limb(ctx, [(296, 620), (296, 660)], 8, rgb("#b8913f"), ow=3)
    _hanging_lamp(ctx, 220, 360, "#b8913f")
    _corners(ctx, a=0.4)


scene.BACKGROUNDS.update(boulangerie=boulangerie, cafe=cafe, paris_park=paris_park, building_hall=building_hall)
