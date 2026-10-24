"""Hot, sunny flat-style places for 'Faris & Puff' (desert, car park, beach) and their props."""
import math

import cairo

from . import scene
from .anim import EASE, clamp
from .character import ellipse, hexrgb
from .flat_places import _cloud, _fill, _poly, _rr, _sky

W, H, GROUND = scene.W, scene.H, scene.GROUND
rgb = hexrgb


def _sun(ctx, x, y, r=110):
    for k in range(12):
        a = k * math.pi / 6
        _poly(ctx, [(x + math.cos(a - 0.09) * (r + 20), y + math.sin(a - 0.09) * (r + 20)),
                    (x + math.cos(a) * (r + 80), y + math.sin(a) * (r + 80)),
                    (x + math.cos(a + 0.09) * (r + 20), y + math.sin(a + 0.09) * (r + 20))], "#ffd166", 0.8)
    ellipse(ctx, x, y, r, r)
    _fill(ctx, "#ffbf3f")


def _palm(ctx, x, base, s=1.0):
    ctx.move_to(x, base)
    ctx.curve_to(x + 10 * s, base - 200 * s, x - 20 * s, base - 320 * s, x + 20 * s, base - 420 * s)
    ctx.set_source_rgb(*rgb("#9b6a43"))
    ctx.set_line_width(26 * s)
    ctx.set_line_cap(1)
    ctx.stroke()
    tx, ty = x + 20 * s, base - 420 * s
    for k in range(7):
        a = math.pi * (1.05 + 0.9 * k / 6)
        ctx.move_to(tx, ty)
        ctx.curve_to(tx + math.cos(a) * 80 * s, ty + math.sin(a) * 80 * s - 30 * s,
                     tx + math.cos(a) * 150 * s, ty + math.sin(a) * 120 * s, tx + math.cos(a) * 170 * s, ty + math.sin(a) * 150 * s + 60 * s)
        ctx.set_source_rgb(*rgb("#3fa36b" if k % 2 else "#4cb87a"))
        ctx.set_line_width(26 * s)
        ctx.stroke()


def desert(ctx):
    _sky(ctx, "#8fd3f4", "#fde9b8", 1250)
    _sun(ctx, 820, 330)
    for y0, c, amp in ((1080, "#f2c27b", 60), (1180, "#eab06a", 80), (1300, "#f6cf8f", 70)):
        ctx.move_to(-200, H + 200)
        ctx.line_to(-200, y0)
        for x in range(-200, W + 240, 40):
            ctx.line_to(x, y0 - amp * math.sin(x / 260 + y0))
        ctx.line_to(W + 200, H + 200)
        ctx.close_path()
        _fill(ctx, c)
    _palm(ctx, 120, 1260, 0.75)
    _palm(ctx, 220, 1240, 0.55)
    # far camel silhouette
    ctx.save()
    ctx.translate(900, 1090)
    ctx.scale(0.5, 0.5)
    ellipse(ctx, 0, 0, 90, 50)
    _fill(ctx, "#c9894d")
    ellipse(ctx, -10, -50, 40, 34)
    _fill(ctx, "#c9894d")
    _rr(ctx, 70, -110, 26, 110, 10, "#c9894d")
    ellipse(ctx, 100, -116, 30, 18)
    _fill(ctx, "#c9894d")
    for lx in (-60, -30, 30, 60):
        _rr(ctx, lx, 30, 14, 110, 6, "#c9894d")
    ctx.restore()
    ctx.rectangle(-200, GROUND - 30, W + 400, H)
    _fill(ctx, "#f7d79d")
    for x in range(-150, W + 200, 170):  # sand ripples
        ctx.move_to(x, GROUND + 80 + (x % 3) * 40)
        ctx.curve_to(x + 30, GROUND + 64 + (x % 3) * 40, x + 70, GROUND + 64 + (x % 3) * 40, x + 100, GROUND + 80 + (x % 3) * 40)
        ctx.set_source_rgba(0.85, 0.65, 0.35, 0.6)
        ctx.set_line_width(5)
        ctx.stroke()


def car_park(ctx):
    _sky(ctx, "#7cc6ee", "#e3f4fb", 1200)
    _sun(ctx, 160, 250, 90)
    for x, w, h, c in ((-150, 300, 560, "#e8d3b0"), (150, 260, 700, "#f1e2c6"), (410, 280, 520, "#e2c79c"),
                       (690, 300, 640, "#efdcb9"), (990, 260, 480, "#e8d3b0")):
        _rr(ctx, x, 1150 - h, w, h + 40, 10, c)
        for r in range(int(h // 120)):
            for k in range(int(w // 90)):
                _rr(ctx, x + 30 + k * 90, 1150 - h + 40 + r * 120, 50, 70, 8, "#8fc1de", 0.85)
    _palm(ctx, 60, 1250, 0.8)
    _palm(ctx, 1040, 1250, 0.7)
    ctx.rectangle(-200, 1150, W + 400, H)
    _fill(ctx, "#6b717e")
    for x in range(-200, W + 200, 260):  # parking lines
        _poly(ctx, [(x, 1180), (x + 12, 1180), (x - 60, H + 200), (x - 80, H + 200)], "#f2f2f2", 0.8)
    # shade canopy on the left
    _rr(ctx, -150, 980, 520, 40, 12, "#e9eef3")
    for lx in (-120, 300):
        _rr(ctx, lx, 1000, 18, GROUND - 1000, 6, "#b9c2cc")
    ctx.rectangle(-150, 1020, 520, GROUND - 1000)
    _fill(ctx, (0, 0, 0), 0.10)


def beach(ctx):
    _sky(ctx, "#6ec3ef", "#d9f1fb", 1150)
    _sun(ctx, 860, 280, 95)
    _cloud(ctx, 120, 330, 0.9)
    ctx.rectangle(-200, 1050, W + 400, 220)
    _fill(ctx, "#2bb3c0")
    for y in (1090, 1150, 1210):
        for x in range(-200, W + 200, 140):
            ctx.move_to(x, y)
            ctx.curve_to(x + 30, y - 12, x + 60, y - 12, x + 90, y)
        ctx.set_source_rgba(1, 1, 1, 0.6)
        ctx.set_line_width(5)
        ctx.stroke()
    ctx.move_to(-200, 1290)
    for x in range(-200, W + 240, 60):
        ctx.line_to(x, 1270 + 14 * math.sin(x / 70))
    ctx.line_to(W + 200, 1330)
    ctx.line_to(-200, 1330)
    ctx.close_path()
    _fill(ctx, "#ffffff", 0.8)
    ctx.rectangle(-200, 1300, W + 400, H)
    _fill(ctx, "#f7dda6")
    # umbrella + towel
    ctx.move_to(170, GROUND - 30)
    ctx.line_to(230, 980)
    ctx.set_source_rgb(*rgb("#7a5a3a"))
    ctx.set_line_width(12)
    ctx.stroke()
    for k in range(6):
        a0 = math.pi * (1 + k / 6)
        a1 = math.pi * (1 + (k + 1) / 6)
        ctx.move_to(230, 980)
        ctx.arc(230, 980, 230, a0, a1)
        ctx.close_path()
        _fill(ctx, "#ef476f" if k % 2 else "#ffffff")
    _poly(ctx, [(-60, GROUND + 40), (320, GROUND + 40), (360, GROUND + 140), (-100, GROUND + 140)], "#3a86ff")
    for k in range(4):
        ctx.rectangle(-80 + k * 110, GROUND + 40, 50, 100)
    _fill(ctx, "#ffffff", 0.35)
    ellipse(ctx, 900, GROUND + 120, 26, 16)
    _fill(ctx, "#f28c8c")


scene.BACKGROUNDS.update(desert=desert, car_park=car_park, beach=beach)


# ------------------------------------------------------------------ props & effects
def heat_waves(ctx, x, y, t, n=3, a=0.5):
    for k in range(n):
        xx = x + (k - n / 2) * 40
        ctx.move_to(xx, y)
        for s in range(8):
            ctx.line_to(xx + 10 * math.sin(s * 1.2 + t * 6 + k), y - s * 22)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.set_line_width(6)
        ctx.set_line_cap(1)
        ctx.stroke()


def bottle(ctx, x, y, rot=0.0, level=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    _rr(ctx, -20, -70, 40, 110, 12, (0.75, 0.9, 1.0), 0.85)
    if level > 0:
        _rr(ctx, -18, -68 + 106 * (1 - level), 36, 106 * level, 10, "#4cc9f0", 0.9)
    _rr(ctx, -10, -86, 20, 18, 4, "#3a86ff")
    ctx.rectangle(-20, -30, 40, 22)
    _fill(ctx, "#ffffff", 0.9)
    ctx.restore()


def parked_car(ctx, x, y, t, hot=1.0):
    """Side view car; y = ground. hot draws the heat shimmer."""
    ellipse(ctx, x, y + 6, 230, 18)
    _fill(ctx, (0, 0, 0), 0.18)
    _rr(ctx, x - 230, y - 150, 460, 120, 40, "#ef476f")
    ctx.move_to(x - 140, y - 150)
    ctx.curve_to(x - 110, y - 250, x + 90, y - 250, x + 140, y - 150)
    ctx.close_path()
    _fill(ctx, "#ef476f")
    ctx.move_to(x - 115, y - 155)
    ctx.curve_to(x - 90, y - 228, x - 10, y - 228, x - 10, y - 155)
    ctx.close_path()
    _fill(ctx, "#cfe8f5")
    ctx.move_to(x + 10, y - 155)
    ctx.curve_to(x + 10, y - 228, x + 80, y - 228, x + 118, y - 155)
    ctx.close_path()
    _fill(ctx, "#cfe8f5")
    for wx in (x - 140, x + 140):
        ellipse(ctx, wx, y - 30, 50, 50)
        _fill(ctx, "#2b2d42")
        ellipse(ctx, wx, y - 30, 22, 22)
        _fill(ctx, "#c9ced6")
    ellipse(ctx, x + 215, y - 110, 14, 10)
    _fill(ctx, "#fff3b0")
    if hot > 0:
        heat_waves(ctx, x - 40, y - 250, t, 4, 0.55 * hot)


def thermometer(ctx, x, y, u, temp="50°C"):
    sc = EASE["back"](clamp(u / 0.3))
    if sc <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    _rr(ctx, -30, -200, 60, 220, 30, "#ffffff")
    ellipse(ctx, 0, 30, 46, 46)
    _fill(ctx, "#ffffff")
    ellipse(ctx, 0, 30, 32, 32)
    _fill(ctx, "#ef476f")
    fill = min(1.0, u * 1.4)
    _rr(ctx, -12, 10 - 190 * fill, 24, 190 * fill + 10, 12, "#ef476f")
    scene.text(ctx, temp, 100, -80, 64, (1, 1, 1), stroke=14, stroke_color=rgb("#ef476f"))
    ctx.restore()


def flip_flop(ctx, x, y, s=1.0, color="#06d6a0"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ellipse(ctx, 0, 0, 44, 16)
    _fill(ctx, color)
    ctx.move_to(-10, -4)
    ctx.curve_to(0, -30, 20, -30, 26, -4)
    ctx.set_source_rgb(1, 1, 1)
    ctx.set_line_width(6)
    ctx.stroke()
    ctx.restore()


def puddle(ctx, x, y, r):
    if r <= 1:
        return
    ellipse(ctx, x, y, r, r * 0.22)
    _fill(ctx, "#bfe9ff", 0.85)
    ellipse(ctx, x - r * 0.3, y - r * 0.05, r * 0.3, r * 0.06)
    _fill(ctx, (1, 1, 1), 0.7)
