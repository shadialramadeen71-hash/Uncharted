"""Fairy-tale palace (storybook look) for 'The Count & Pip': ballroom, throne room, portrait gallery + props."""
import math

import cairo

from . import scene
from .anim import EASE, clamp
from .character import OUTLINE, ellipse, fill_stroke, hexrgb, ink, limb, shade
from .euro import _poly, _rect, _vgrad

W, H, GROUND = scene.W, scene.H, scene.GROUND
rgb = hexrgb
GOLD = "#d9b24a"


def _arch_window(ctx, x, y, w, h, t_seed=0):
    ctx.move_to(x, y + h)
    ctx.line_to(x, y + w / 2)
    ctx.arc(x + w / 2, y + w / 2, w / 2, math.pi, 2 * math.pi)
    ctx.line_to(x + w, y + h)
    ctx.close_path()
    path = ctx.copy_path()
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgb(0, 0.12, 0.14, 0.36)
    g.add_color_stop_rgb(1, 0.36, 0.3, 0.6)
    ctx.set_source(g)
    ctx.fill()
    ctx.save()
    ctx.append_path(path)
    ctx.clip()
    for i in range(14):  # stars
        sx = x + ((i * 73 + t_seed * 31) % int(w))
        sy = y + ((i * 131 + t_seed * 17) % int(h * 0.7))
        ellipse(ctx, sx, sy, 3, 3)
        ctx.set_source_rgba(1, 1, 0.9, 0.9)
        ctx.fill()
    ctx.restore()
    ctx.append_path(path)
    ink(ctx, rgb(GOLD), 10)
    ctx.move_to(x + w / 2, y)
    ctx.line_to(x + w / 2, y + h)
    ctx.move_to(x, y + h * 0.55)
    ctx.line_to(x + w, y + h * 0.55)
    ink(ctx, rgb(GOLD), 6)


def _column(ctx, x, top, bottom, w=90):
    _rect(ctx, x, top + 40, w, bottom - top - 80, "#f4eee6")
    for k in range(4):
        ctx.move_to(x + 18 + k * 18, top + 50)
        ctx.line_to(x + 18 + k * 18, bottom - 50)
    ink(ctx, rgb("#d8cfc2"), 3)
    _rect(ctx, x - 16, top, w + 32, 44, GOLD)
    _rect(ctx, x - 16, bottom - 44, w + 32, 44, GOLD)


def _curtain(ctx, x, y, h, d, color="#e58fb0"):
    _poly(ctx, [(x, y), (x + 120 * d, y), (x + 60 * d, y + h * 0.45), (x + 110 * d, y + h), (x, y + h)], color)
    for k in range(3):
        ctx.move_to(x + 20 * d + k * 26 * d, y + 10)
        ctx.curve_to(x + 30 * d + k * 20 * d, y + h * 0.4, x + 10 * d + k * 26 * d, y + h * 0.7, x + 30 * d + k * 24 * d, y + h)
    ink(ctx, shade(rgb(color), 0.75), 3)
    ellipse(ctx, x + 66 * d, y + h * 0.46, 16, 16)
    fill_stroke(ctx, rgb(GOLD), ow=3)


def _marble_floor(ctx, a="#f6e6ee", b="#e3c9d6"):
    ctx.rectangle(-200, GROUND - 40, W + 400, H)
    ctx.set_source_rgb(*rgb(a))
    ctx.fill()
    ctx.set_source_rgb(*rgb(b))
    for j, y in enumerate(range(GROUND - 40, H + 200, 90)):
        for i, x in enumerate(range(-200, W + 200, 90)):
            if (i + j) % 2:
                ctx.rectangle(x, y, 90, 90)
    ctx.fill()
    g = cairo.LinearGradient(0, GROUND - 40, 0, GROUND + 260)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.45)
    g.add_color_stop_rgba(1, 1, 1, 1, 0.0)
    ctx.rectangle(-200, GROUND - 40, W + 400, 300)
    ctx.set_source(g)
    ctx.fill()
    _rect(ctx, -200, GROUND - 70, W + 400, 34, GOLD, ow=4)


def chandelier(ctx, x, y, t=0.0):
    limb(ctx, [(x, -200), (x, y - 60)], 6, rgb(GOLD), ow=2)
    for r, yy in ((170, y), (110, y - 50)):
        ellipse(ctx, x, yy, r, 22)
        ink(ctx, rgb(GOLD), 10)
        for k in range(7):
            cx = x + r * math.cos(math.pi * (0.1 + 0.8 * k / 6)) * (1 if k % 2 else -1)
            cx = x - r + 2 * r * k / 6
            _rect(ctx, cx - 6, yy - 46, 12, 36, "#fbf6ea", ow=2.5)
            ellipse(ctx, cx, yy - 56 + math.sin(t * 9 + k) * 1.5, 6, 10)
            ctx.set_source_rgb(1, 0.82, 0.3)
            ctx.fill()
    for k in range(9):  # crystal drops
        cx = x - 150 + k * 37
        ctx.move_to(cx, y + 20)
        ctx.line_to(cx - 8, y + 50 + (k % 3) * 14)
        ctx.line_to(cx, y + 64 + (k % 3) * 14)
        ctx.line_to(cx + 8, y + 50 + (k % 3) * 14)
        ctx.close_path()
        fill_stroke(ctx, (0.85, 0.93, 1.0), ow=2)


def ballroom(ctx):
    _vgrad(ctx, -200, -200, W + 400, 1800, "#bcd2ef", "#e9f0fb")
    for x in range(-200, W + 200, 100):  # soft wall panels
        ctx.rectangle(x + 10, 120, 80, 1300)
        ink(ctx, rgb("#a9c0e2"), 2)
    _rect(ctx, -200, 70, W + 400, 40, GOLD, ow=4)
    _arch_window(ctx, 40, 360, 240, 560, 1)
    _arch_window(ctx, 800, 360, 240, 560, 2)
    _curtain(ctx, 10, 330, 640, 1)
    _curtain(ctx, 1070, 330, 640, -1)
    # grand staircase with red carpet, curving down from the back
    for i in range(10):
        y = 700 + i * 72
        w = 300 + i * 26
        _rect(ctx, 540 - w / 2, y, w, 72, "#f4eee6", ow=3)
        _rect(ctx, 540 - w / 4, y, w / 2, 72, "#b3283e", ow=2.5)
    for d in (-1, 1):
        for i in range(11):
            y = 700 + i * 72
            bx = 540 + d * (150 + i * 13)
            limb(ctx, [(bx, y), (bx, y - 90)], 10, rgb("#fbf6ea"), ow=2.5)
        limb(ctx, [(540 + d * 150, 610), (540 + d * 280, 1402)], 18, rgb(GOLD), ow=3)
    _column(ctx, 300, 300, GROUND - 60)
    _column(ctx, 690, 300, GROUND - 60)
    _marble_floor(ctx)
    chandelier(ctx, 540, 200)


def throne_room(ctx):
    _vgrad(ctx, -200, -200, W + 400, 1800, "#e6c7e0", "#f6e8f1")
    _rect(ctx, -200, 70, W + 400, 40, GOLD, ow=4)
    # rose window
    cx, cy, r = 540, 470, 210
    ellipse(ctx, cx, cy, r + 26, r + 26)
    fill_stroke(ctx, rgb(GOLD))
    cols = ["#5b8ee6", "#e65b7a", "#f2c14e", "#62c39b", "#9b6ee6", "#e6955b"]
    for k in range(12):
        a0, a1 = k * math.pi / 6, (k + 1) * math.pi / 6
        ctx.move_to(cx, cy)
        ctx.arc(cx, cy, r, a0, a1)
        ctx.close_path()
        fill_stroke(ctx, rgb(cols[k % 6]), ow=4)
    ellipse(ctx, cx, cy, 60, 60)
    fill_stroke(ctx, rgb("#f6e8f1"))
    # banners with a crown
    for bx in (90, 850):
        _poly(ctx, [(bx, 200), (bx + 140, 200), (bx + 140, 800), (bx + 70, 740), (bx, 800)], "#3f5fae")
        _poly(ctx, [(bx + 30, 420), (bx + 50, 360), (bx + 70, 400), (bx + 90, 360), (bx + 110, 420)], GOLD, ow=3)
    # dais, red carpet and the golden throne
    _poly(ctx, [(300, 1180), (780, 1180), (840, 1260), (240, 1260)], "#f4eee6")
    _poly(ctx, [(240, 1260), (840, 1260), (880, 1330), (200, 1330)], "#e9e1d6")
    ctx.move_to(420, 640)
    ctx.curve_to(410, 520, 670, 520, 660, 640)
    ctx.line_to(680, 1180)
    ctx.line_to(400, 1180)
    ctx.close_path()
    fill_stroke(ctx, rgb(GOLD))
    _rect(ctx, 450, 680, 180, 380, "#a8213a")
    _poly(ctx, [(500, 600), (520, 550), (540, 590), (560, 550), (580, 600)], "#f2c14e", ow=3)
    _rect(ctx, 400, 1060, 280, 70, "#a8213a")
    _marble_floor(ctx, "#f7efe2", "#e9d9bf")
    _poly(ctx, [(430, GROUND - 60), (650, GROUND - 60), (900, H + 200), (180, H + 200)], "#b3283e")
    for x in (40, 1000):  # candelabras
        limb(ctx, [(x, GROUND - 60), (x, 1100)], 14, rgb(GOLD), ow=3)
        for dx in (-40, 0, 40):
            _rect(ctx, x + dx - 7, 1040, 14, 50, "#fbf6ea", ow=2.5)
        limb(ctx, [(x - 40, 1100), (x + 40, 1100)], 10, rgb(GOLD), ow=3)


def portrait(ctx, x, y, w, h, kind):
    _rect(ctx, x - 22, y - 22, w + 44, h + 44, GOLD)
    _vgrad(ctx, x, y, w, h, "#6e5a7a", "#3e3248")
    hx, hy = x + w / 2, y + h * 0.42
    ellipse(ctx, hx, hy + h * 0.45, w * 0.42, h * 0.3)
    fill_stroke(ctx, rgb("#7a2a3a" if kind == "king" else "#3f5fae"), ow=3)
    ellipse(ctx, hx, hy, w * 0.2, h * 0.17)
    fill_stroke(ctx, rgb("#f0c9a8"), ow=3)
    if kind == "king":
        _poly(ctx, [(hx - 30, hy - h * 0.15), (hx - 20, hy - h * 0.25), (hx, hy - h * 0.18), (hx + 20, hy - h * 0.25),
                    (hx + 30, hy - h * 0.15)], GOLD, ow=2.5)
        ellipse(ctx, hx, hy + h * 0.12, w * 0.14, h * 0.08)
        ctx.set_source_rgb(0.95, 0.95, 0.95)
        ctx.fill()
    else:
        ellipse(ctx, hx, hy - h * 0.12, w * 0.24, h * 0.12)
        fill_stroke(ctx, rgb("#e8c35a"), ow=2.5)
    for ex_ in (hx - 12, hx + 12):
        ellipse(ctx, ex_, hy - 4, 3, 3)
        ctx.set_source_rgb(0.1, 0.1, 0.1)
        ctx.fill()


def gallery(ctx):
    _vgrad(ctx, -200, -200, W + 400, 1800, "#e7c6c9", "#f3e1df")
    ctx.set_source_rgba(0.6, 0.3, 0.35, 0.12)  # damask dots
    for j, y in enumerate(range(150, 1150, 80)):
        for x in range(-180 + (j % 2) * 40, W + 200, 80):
            ctx.new_sub_path()
            ctx.arc(x, y, 9, 0, 2 * math.pi)
    ctx.fill()
    _vgrad(ctx, -200, 1150, W + 400, 450, "#7a4b3a", "#5b3529")
    for x in range(-180, W + 200, 220):
        ctx.rectangle(x, 1190, 180, 300)
        ink(ctx, rgb("#3e2219"), 3)
    _rect(ctx, -200, 1136, W + 400, 26, GOLD, ow=4)
    _rect(ctx, -200, 70, W + 400, 40, GOLD, ow=4)
    portrait(ctx, 40, 420, 230, 300, "king")
    portrait(ctx, 820, 420, 230, 300, "queen")
    # suit of armour
    ax = 950
    for y0, w_, c in ((1520, 60, "#9aa3ad"), (1400, 70, "#b4bcc6"), (1250, 120, "#c3cad3"), (1130, 140, "#b4bcc6")):
        _rect(ctx, ax - w_ / 2, y0 - 120, w_, 130, c, ow=4)
    ellipse(ctx, ax, 990, 62, 70)
    fill_stroke(ctx, rgb("#c3cad3"))
    for k in range(3):
        _rect(ctx, ax - 40, 970 + k * 14, 80, 6, "#3a3f46", ow=1.5)
    _poly(ctx, [(ax - 6, 920), (ax + 6, 920), (ax + 20, 860), (ax - 20, 860)], "#a8213a", ow=3)
    limb(ctx, [(ax + 90, GROUND - 40), (ax + 90, 900)], 10, rgb("#6b5a4a"), ow=3)
    _poly(ctx, [(ax + 80, 900), (ax + 100, 900), (ax + 90, 840)], "#c3cad3", ow=3)
    # wall sconces
    for sx in (360, 720):
        limb(ctx, [(sx, 760), (sx, 820)], 10, rgb(GOLD), ow=3)
        _rect(ctx, sx - 7, 708, 14, 52, "#fbf6ea", ow=2.5)
    _marble_floor(ctx, "#f3e9dc", "#e3d3bd")
    _poly(ctx, [(-200, GROUND - 10), (W + 200, GROUND - 10), (W + 200, GROUND + 120), (-200, GROUND + 120)], "#a8213a")


scene.BACKGROUNDS.update(ballroom=ballroom, throne_room=throne_room, gallery=gallery)


# ------------------------------------------------------------------ props
def pedestal(ctx, x, y):
    """Velvet cushion on a gold pedestal; y = cushion top."""
    _rect(ctx, x - 40, y + 30, 80, GROUND - y - 60, "#f4eee6")
    _rect(ctx, x - 70, y + 20, 140, 26, GOLD, ow=4)
    _rect(ctx, x - 70, GROUND - 50, 140, 30, GOLD, ow=4)
    ctx.move_to(x - 90, y + 22)
    ctx.curve_to(x - 100, y - 20, x + 100, y - 20, x + 90, y + 22)
    ctx.close_path()
    fill_stroke(ctx, rgb("#5b2a6e"))
    for d in (-1, 1):
        ellipse(ctx, x + d * 90, y + 22, 9, 12)
        fill_stroke(ctx, rgb(GOLD), ow=2.5)


def glass_slipper(ctx, x, y, t=0.0, s=1.0, rot=0.0, shine=True):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.move_to(-56, 0)
    ctx.curve_to(-60, -30, -40, -44, -20, -36)
    ctx.curve_to(0, -20, 30, -22, 54, -10)
    ctx.curve_to(66, -4, 60, 4, 50, 4)
    ctx.line_to(-30, 4)
    ctx.close_path()
    ctx.set_source_rgba(0.8, 0.93, 1.0, 0.75)
    ctx.fill_preserve()
    ink(ctx, rgb("#6aa7d6"), 3.5)
    _poly(ctx, [(-52, 4), (-44, 4), (-46, 30), (-50, 30)], (0.8, 0.93, 1.0), ow=2.5)
    ctx.move_to(-20, -28)
    ctx.curve_to(0, -18, 20, -18, 40, -10)
    ink(ctx, (1, 1, 1), 3)
    ctx.restore()
    if shine:
        scene.sparkles(ctx, x, y - 30, t, r=70 * s)


def shards(ctx, x, y, u):
    if not 0 <= u <= 1:
        return
    for k in range(14):
        a = math.pi * (1.05 + 0.9 * k / 13)
        v = 300 + 120 * ((k * 7) % 3)
        px = x + math.cos(a) * v * u
        py = y + math.sin(a) * v * u + 800 * u * u
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(k + u * 10)
        _poly(ctx, [(-10, -6), (12, -2), (0, 10)], (0.8, 0.93, 1.0), ow=2)
        ctx.restore()


def wand(ctx, x, y, ang=-0.6, glow=0.0, t=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    limb(ctx, [(0, 0), (150, 0)], 9, rgb("#2a1f2e"), ow=2.5)
    limb(ctx, [(130, 0), (150, 0)], 9, (0.97, 0.95, 0.9), ow=2.5)
    ctx.restore()
    tip = (x + 160 * math.cos(ang), y + 160 * math.sin(ang))
    if glow > 0:
        scene.sparkles(ctx, tip[0], tip[1], t, r=40 + 40 * glow)
    return tip


def pumpkin(ctx, x, y, s=1.0, pip=False, t=0.0):
    """y = bottom. pip=True: Pip turned into a pumpkin (horns, eyes, tail)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if pip:
        sw = 18 * math.sin(t * 4)
        ctx.move_to(-110, -40)
        ctx.curve_to(-170, -30, -190, -90 + sw, -170, -130 + sw)
        ink(ctx, OUTLINE, 18)
        ctx.move_to(-110, -40)
        ctx.curve_to(-170, -30, -190, -90 + sw, -170, -130 + sw)
        ctx.set_source_rgb(*rgb("#d64933"))
        ctx.set_line_width(12)
        ctx.stroke()
    for dx, w_ in ((-70, 80), (70, 80), (-30, 80), (30, 80), (0, 70)):
        ellipse(ctx, dx, -100, w_, 100)
        fill_stroke(ctx, rgb("#f28c28"), ow=4)
    _rect(ctx, -10, -230, 20, 40, "#5b7a2e", ow=3)
    if pip:
        for d in (-1, 1):
            _poly(ctx, [(d * 40 - 16, -190), (d * 60, -270), (d * 40 + 16, -190)], "#f1e3c6", ow=3)
        for ex_ in (-34, 34):
            ellipse(ctx, ex_, -120, 16, 18)
            fill_stroke(ctx, (1, 1, 1), ow=3)
            ellipse(ctx, ex_ + 4, -118, 8, 10)
            ctx.set_source_rgb(*rgb("#e0a800"))
            ctx.fill()
        ctx.move_to(-30, -70)
        ctx.curve_to(-10, -60, 10, -60, 30, -72)
        ink(ctx, OUTLINE, 5)
    ctx.restore()


def poof(ctx, x, y, u, color=(0.92, 0.88, 1.0)):
    if not 0 <= u <= 1:
        return
    a = 1 - EASE["in"](u)
    for k in range(9):
        ang = k * 2 * math.pi / 9
        r = 40 + 160 * EASE["out"](u)
        ellipse(ctx, x + math.cos(ang) * r, y + math.sin(ang) * r * 0.7, 70 * (1 - 0.4 * u), 60 * (1 - 0.4 * u))
        ctx.set_source_rgba(*color, a * 0.9)
        ctx.fill()
    scene.sparkles(ctx, x, y, u * 6, r=120 + 80 * u)


def big_frame(ctx, x, y, w, h):
    """Empty gold picture frame (the Count hides 'inside' it)."""
    ctx.rectangle(x - 46, y - 46, w + 92, h + 92)
    ctx.rectangle(x + w, y, -w, h)  # hole (reverse winding)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgb(*rgb(GOLD))
    ctx.fill_preserve()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ink(ctx, OUTLINE, 5)
    for k in range(4):
        cx = x - 23 if k % 2 == 0 else x + w + 23
        cy = y - 23 if k < 2 else y + h + 23
        ellipse(ctx, cx, cy, 30, 30)
        fill_stroke(ctx, shade(rgb(GOLD), 0.85), ow=3)
    ctx.rectangle(x - 16, y - 16, w + 32, h + 32)
    ink(ctx, shade(rgb(GOLD), 0.7), 3)


def dust(ctx, x, y, u):
    if not 0 <= u <= 1:
        return
    for k in range(7):
        ang = math.pi * (0.8 + 0.4 * k / 6)
        r = 30 + 160 * u
        ellipse(ctx, x + math.cos(ang) * r * -1, y + math.sin(ang) * r * 0.5, 30 + 20 * u, 24 + 16 * u)
        ctx.set_source_rgba(0.85, 0.8, 0.72, 0.8 * (1 - u))
        ctx.fill()
