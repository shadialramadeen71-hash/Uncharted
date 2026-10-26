"""Late-90s 'dark deco' backgrounds: painted on black, blood-red skies, black deco towers, searchlights."""
import math

import cairo
import numpy as np

from . import scene
from .anim import EASE, clamp
from .character import OUTLINE, ellipse, fill_stroke, hexrgb, ink, limb, shade

W, H, GROUND = scene.W, scene.H, scene.GROUND
rgb = hexrgb
BLACK = (0.03, 0.02, 0.03)


def _fill(ctx, c, a=1.0):
    ctx.set_source_rgba(*(rgb(c) if isinstance(c, str) else c), a)
    ctx.fill()


def _poly(ctx, pts, c, a=1.0):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    _fill(ctx, c, a)


def _red_sky(ctx, y1=1300):
    g = cairo.LinearGradient(0, -200, 0, y1)
    g.add_color_stop_rgb(0, 0.12, 0.02, 0.03)
    g.add_color_stop_rgb(0.55, 0.5, 0.08, 0.06)
    g.add_color_stop_rgb(1, 0.85, 0.32, 0.12)
    ctx.rectangle(-200, -200, W + 400, y1 + 200)
    ctx.set_source(g)
    ctx.fill()


def bat_shape(ctx, x, y, s, color):
    pts = [(-60, 0), (-30, -14), (-14, -8), (-10, -22), (-4, -12), (4, -12), (10, -22), (14, -8), (30, -14),
           (60, 0), (40, 6), (30, 22), (14, 12), (0, 26), (-14, 12), (-30, 22), (-40, 6)]
    _poly(ctx, [(x + px * s, y + py * s) for px, py in pts], color)


def _skyline(ctx, base, seed, dark, lit_p=0.35, scale=1.0):
    rng = np.random.default_rng(seed)
    x = -220
    while x < W + 220:
        w = rng.uniform(110, 210) * scale
        h = rng.uniform(380, 900) * scale
        top = base - h
        steps = int(rng.integers(1, 4))
        pts = [(x, base), (x, top + 60 * steps)]
        for k in range(steps):  # art-deco set-backs
            inset = (k + 1) * w * 0.12
            pts += [(x + inset - w * 0.12, top + 60 * (steps - k)), (x + inset, top + 60 * (steps - k)),
                    (x + inset, top + 60 * (steps - k - 1))]
        pts += [(x + w - (steps) * w * 0.12, top), (x + w - (steps) * w * 0.12, top + 60 * steps), (x + w, top + 60 * steps), (x + w, base)]
        if rng.random() < 0.3:  # spire
            _poly(ctx, [(x + w / 2 - 8, top + 4), (x + w / 2, top - 120 * scale), (x + w / 2 + 8, top + 4)], dark)
        _poly(ctx, pts, dark)
        for wy in np.arange(top + 80 * scale, base - 20, 34 * scale):
            for wx in np.arange(x + 14, x + w - 14, 24 * scale):
                if rng.random() < lit_p:
                    ctx.rectangle(wx, wy, 8 * scale, 12 * scale)
        ctx.set_source_rgba(1.0, 0.82, 0.35, 0.85)
        ctx.fill()
        x += w + rng.uniform(-20, 10)


def gotham_rooftop(ctx):
    _red_sky(ctx)
    # searchlights
    for x0, ang in ((150, -0.35), (900, 0.3)):
        ctx.move_to(x0, 1300)
        ctx.line_to(x0 + math.sin(ang - 0.06) * 1600, 1300 - math.cos(ang - 0.06) * 1600)
        ctx.line_to(x0 + math.sin(ang + 0.06) * 1600, 1300 - math.cos(ang + 0.06) * 1600)
        ctx.close_path()
        _fill(ctx, (1.0, 0.95, 0.75), 0.12)
    # the signal in the clouds
    ellipse(ctx, 700, 330, 150, 110)
    _fill(ctx, (1.0, 0.93, 0.6), 0.75)
    bat_shape(ctx, 700, 330, 2.0, BLACK)
    # blimp
    ellipse(ctx, 250, 520, 150, 46)
    _fill(ctx, (0.18, 0.05, 0.05))
    _poly(ctx, [(110, 520), (70, 470), (80, 570)], (0.18, 0.05, 0.05))
    _skyline(ctx, 1320, 5, (0.16, 0.04, 0.05), 0.15, 0.8)
    _skyline(ctx, 1420, 7, (0.06, 0.02, 0.03), 0.28, 1.0)
    # rooftop
    ctx.rectangle(-200, 1380, W + 400, H)
    _fill(ctx, (0.13, 0.12, 0.15))
    ctx.rectangle(-200, 1380, W + 400, 60)
    _fill(ctx, (0.22, 0.2, 0.24))
    ctx.rectangle(-200, 1380, W + 400, 60)
    ink(ctx, OUTLINE, 5)
    # water tower (left) and gargoyle (right ledge)
    for lx in (-60, 90):
        limb(ctx, [(lx, 1380), (lx + 30, 1080)], 10, (0.08, 0.07, 0.09), ow=3)
    _poly(ctx, [(-90, 1090), (150, 1090), (140, 860), (-80, 860)], (0.1, 0.09, 0.11))
    _poly(ctx, [(-100, 870), (160, 870), (30, 780)], (0.08, 0.07, 0.09))
    gx = 930
    _poly(ctx, [(gx - 60, 1380), (gx + 70, 1380), (gx + 60, 1290), (gx + 90, 1240), (gx + 40, 1200), (gx + 10, 1230),
                (gx - 30, 1180), (gx - 20, 1250), (gx - 70, 1300)], (0.1, 0.09, 0.12))
    ellipse(ctx, gx + 46, 1222, 6, 4)
    _fill(ctx, (0.9, 0.3, 0.2))


def funhouse(ctx):
    g = cairo.LinearGradient(0, -200, 0, 1500)
    g.add_color_stop_rgb(0, 0.08, 0.03, 0.12)
    g.add_color_stop_rgb(1, 0.28, 0.1, 0.36)
    ctx.rectangle(-200, -200, W + 400, 1800)
    ctx.set_source(g)
    ctx.fill()
    # string lights
    for row, y0 in enumerate((260, 420)):
        for k in range(14):
            x = -150 + k * 100
            y = y0 + 40 * math.sin(k * 0.9 + row)
            ellipse(ctx, x, y, 14, 18)
            _fill(ctx, ["#ff4d6d", "#ffd23f", "#3ddc97", "#4cc9f0"][(k + row) % 4])
    # giant playing cards + painted "HA HA"
    for cx, rot in ((170, -0.15), (900, 0.12)):
        ctx.save()
        ctx.translate(cx, 820)
        ctx.rotate(rot)
        scene.rrect(ctx, -110, -160, 220, 320, 18)
        fill_stroke(ctx, (0.96, 0.94, 0.88))
        scene.text(ctx, "J", 0, 40, 140, (0.42, 0.17, 0.57), stroke=0)
        ctx.restore()
    for k, (x, y, s, r) in enumerate(((540, 620, 120, -0.1), (380, 1040, 80, 0.12), (720, 1080, 90, -0.08))):
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(r)
        scene.text(ctx, "HA HA", 0, 0, s, (0.18, 0.62, 0.27), stroke=10, stroke_color=BLACK)
        ctx.restore()
    # checker floor
    ctx.rectangle(-200, GROUND - 40, W + 400, H)
    _fill(ctx, (0.2, 0.55, 0.25))
    ctx.set_source_rgb(0.36, 0.13, 0.48)
    for j, y in enumerate(range(GROUND - 40, H + 200, 90)):
        for i, x in enumerate(range(-200, W + 200, 90)):
            if (i + j) % 2:
                ctx.rectangle(x, y, 90, 90)
    ctx.fill()
    ctx.rectangle(-200, GROUND - 40, W + 400, 14)
    _fill(ctx, BLACK)


def bank_vault(ctx):
    g = cairo.LinearGradient(0, -200, 0, 1500)
    g.add_color_stop_rgb(0, 0.04, 0.05, 0.06)
    g.add_color_stop_rgb(1, 0.16, 0.2, 0.2)
    ctx.rectangle(-200, -200, W + 400, 1800)
    ctx.set_source(g)
    ctx.fill()
    for x in (-60, 1000):  # dark marble columns
        ctx.rectangle(x - 60, 0, 120, GROUND)
        _fill(ctx, (0.22, 0.26, 0.26))
        ctx.rectangle(x - 60, 0, 30, GROUND)
        _fill(ctx, (0.1, 0.12, 0.12))
    # giant round vault door, swung open
    ellipse(ctx, 560, 820, 380, 380)
    _fill(ctx, (0.02, 0.02, 0.03))
    for r in (370, 300, 230):
        ellipse(ctx, 560, 820, r, r)
        ink(ctx, (0.45, 0.48, 0.5), 8)
    for k in range(8):
        a = k * math.pi / 4
        limb(ctx, [(560, 820), (560 + math.cos(a) * 200, 820 + math.sin(a) * 200)], 18, (0.5, 0.53, 0.55), ow=3)
    ellipse(ctx, 560, 820, 60, 60)
    fill_stroke(ctx, (0.62, 0.64, 0.66))
    # money bags and gold bars
    for x, y in ((180, 1430), (300, 1460), (820, 1440), (940, 1470)):
        ellipse(ctx, x, y, 70, 80)
        fill_stroke(ctx, (0.62, 0.55, 0.38))
        scene.text(ctx, "$", x, y + 26, 70, (0.25, 0.4, 0.2), stroke=0)
    for k in range(4):
        _poly(ctx, [(420 + k * 70, 1520), (480 + k * 70, 1520), (470 + k * 70, 1490), (430 + k * 70, 1490)], (0.95, 0.75, 0.2))
    ctx.rectangle(-200, GROUND - 40, W + 400, H)
    _fill(ctx, (0.1, 0.11, 0.12))
    ctx.rectangle(-200, GROUND - 40, W + 400, 14)
    _fill(ctx, BLACK)
    # green banker's lamps light pools
    for x in (180, 900):
        g2 = cairo.RadialGradient(x, 1250, 10, x, 1250, 420)
        g2.add_color_stop_rgba(0, 0.4, 0.9, 0.5, 0.25)
        g2.add_color_stop_rgba(1, 0.4, 0.9, 0.5, 0.0)
        ctx.rectangle(-200, -200, W + 400, H + 400)
        ctx.set_source(g2)
        ctx.fill()


scene.BACKGROUNDS.update(gotham_rooftop=gotham_rooftop, funhouse=funhouse, bank_vault=bank_vault)


# ------------------------------------------------------------------ props
def pie(ctx, x, y, rot=0.0, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ellipse(ctx, 0, 6, 70, 22)
    fill_stroke(ctx, (0.75, 0.52, 0.3), ow=4)
    for k in range(6):
        ellipse(ctx, -50 + k * 20, -8 - (k % 2) * 8, 22, 18)
        _fill(ctx, (0.98, 0.97, 0.94))
    ellipse(ctx, 0, -22, 10, 10)
    _fill(ctx, (0.85, 0.1, 0.15))
    ctx.restore()


def splat(ctx, x, y, u):
    if not 0 <= u <= 1:
        return
    a = 1 - EASE["in"](clamp((u - 0.6) / 0.4))
    for k in range(9):
        ang = k * 2 * math.pi / 9
        r = 40 + 50 * EASE["out"](clamp(u * 3))
        ellipse(ctx, x + math.cos(ang) * r * 0.8, y + math.sin(ang) * r * 0.6, 26, 22)
        _fill(ctx, (0.98, 0.97, 0.94), a)
    ellipse(ctx, x, y, 62, 50)
    _fill(ctx, (0.98, 0.97, 0.94), a)


def batarang(ctx, x, y, spin):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(spin)
    bat_shape(ctx, 0, 0, 0.8, (0.1, 0.1, 0.13))
    ctx.restore()


def green_rock(ctx, x, y, t, s=1.0, pickle=False):
    g = cairo.RadialGradient(x, y, 5, x, y, 160 * s)
    g.add_color_stop_rgba(0, 0.4, 1.0, 0.4, 0.55 + 0.15 * math.sin(t * 8))
    g.add_color_stop_rgba(1, 0.4, 1.0, 0.4, 0.0)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_SCREEN)
    ctx.arc(x, y, 160 * s, 0, 2 * math.pi)
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if pickle:
        ellipse(ctx, 0, 0, 70, 30)
        fill_stroke(ctx, (0.35, 0.62, 0.2), ow=4)
        for k in range(6):
            ellipse(ctx, -46 + k * 18, -10 + (k % 2) * 16, 4, 4)
            _fill(ctx, (0.22, 0.45, 0.12))
    else:
        _poly(ctx, [(-40, 20), (-50, -10), (-20, -50), (10, -30), (40, -56), (52, -6), (30, 26)], (0.3, 0.95, 0.35))
    ctx.restore()


def grapple(ctx, x0, y0, x1, y1, u):
    if u <= 0:
        return
    u = min(u, 1)
    ctx.move_to(x0, y0)
    ctx.line_to(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u)
    ctx.set_source_rgb(0.05, 0.05, 0.07)
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.save()
    ctx.translate(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u)
    _poly(ctx, [(-10, 6), (0, -14), (10, 6)], (0.4, 0.42, 0.45))
    ctx.restore()


def action_word(ctx, x, y, u, word, color=(1.0, 0.82, 0.1)):
    """Comic-style impact word (POW!, SPLAT!)."""
    sc = EASE["back"](clamp(u / 0.2)) * (1 - clamp((u - 0.85) / 0.15))
    if sc <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-0.15)
    ctx.scale(sc, sc)
    scene.starburst(ctx, 0, 0, 140, (0.85, 0.1, 0.1), 12)
    scene.text(ctx, word, 0, 26, 76, color, stroke=12, stroke_color=BLACK)
    ctx.restore()
