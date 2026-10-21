"""Flat pastel look for 'Stretch & Bruno': outline-free shapes, soft colour blocks, no textures."""
import math

import cairo

from . import scene
from .anim import EASE, clamp
from .character import ellipse, hexrgb

W, H, GROUND = scene.W, scene.H, scene.GROUND
rgb = hexrgb


def _fill(ctx, color, a=1.0):
    ctx.set_source_rgba(*(rgb(color) if isinstance(color, str) else color), a)
    ctx.fill()


def _poly(ctx, pts, color, a=1.0):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    _fill(ctx, color, a)


def _rr(ctx, x, y, w, h, r, color, a=1.0):
    scene.rrect(ctx, x, y, w, h, r)
    _fill(ctx, color, a)


def _sky(ctx, top, bottom, y1=1300):
    g = cairo.LinearGradient(0, -200, 0, y1)
    g.add_color_stop_rgb(0, *rgb(top))
    g.add_color_stop_rgb(1, *rgb(bottom))
    ctx.rectangle(-200, -200, W + 400, y1 + 200)
    ctx.set_source(g)
    ctx.fill()


def _cloud(ctx, x, y, s=1.0, color="#ffffff", a=0.95):
    for dx, dy, r in ((0, 0, 60), (60, -20, 70), (130, 0, 55), (70, 20, 60)):
        ctx.new_sub_path()
        ctx.arc(x + dx * s, y + dy * s, r * s, 0, 2 * math.pi)
    _fill(ctx, color, a)


def _round_tree(ctx, x, base, s=1.0, leaf="#5bb98c", trunk="#8d6346"):
    _rr(ctx, x - 14 * s, base - 160 * s, 28 * s, 160 * s, 10 * s, trunk)
    for dx, dy, r in ((0, -230, 90), (-60, -180, 70), (60, -180, 70)):
        ellipse(ctx, x + dx * s, base + dy * s, r * s, r * s)
        _fill(ctx, leaf)
    ellipse(ctx, x + 30 * s, base - 250 * s, 34 * s, 30 * s)
    _fill(ctx, (1, 1, 1), 0.18)


def _pine(ctx, x, base, s=1.0, color="#3f8f6b"):
    _rr(ctx, x - 10 * s, base - 50 * s, 20 * s, 50 * s, 4, "#6b4a36")
    for k in range(3):
        y = base - 40 * s - k * 70 * s
        w = (110 - k * 25) * s
        _poly(ctx, [(x - w, y), (x + w, y), (x, y - 130 * s)], color)


# ------------------------------------------------------------------ backgrounds
HORIZON = 1060
VP = (880, HORIZON)  # vanishing point of the road


def road_x(y, side):
    """x of the road edge at screen height y (side -1 left, +1 right)."""
    u = (y - HORIZON) / (H + 200 - HORIZON)
    near = 560 if side < 0 else 1500
    far = 846 if side < 0 else 914
    return far + (near - far) * u


def city_crosswalk(ctx):
    _sky(ctx, "#9fd3e6", "#e8f4f0")
    _cloud(ctx, 120, 260, 1.0)
    _cloud(ctx, 700, 180, 0.8)
    # pastel buildings
    for x, w, h, c in ((-180, 260, 820, "#f2a7a1"), (90, 230, 700, "#f6d38b"), (330, 250, 880, "#9fc5e8"),
                       (590, 200, 640, "#c3b1e1"), (800, 240, 760, "#f2a7a1"), (1040, 240, 700, "#a8d8b9")):
        _rr(ctx, x, HORIZON - h, w, h + 40, 14, c)
        for r in range(int(h // 110) - 1):
            for k in range(int(w // 80)):
                _rr(ctx, x + 26 + k * 80, HORIZON - h + 50 + r * 110, 44, 62, 8, "#fffaf0", 0.85)
    # sidewalk (left) and road receding to the vanishing point
    ctx.rectangle(-200, HORIZON, W + 400, H)
    _fill(ctx, "#d9dde3")
    _poly(ctx, [(road_x(HORIZON, -1), HORIZON), (road_x(HORIZON, 1), HORIZON),
                (road_x(H + 200, 1), H + 200), (road_x(H + 200, -1), H + 200)], "#5d6474")
    for y0 in range(HORIZON + 30, H + 200, 140):  # dashed centre line
        y1 = y0 + 60
        xa = (road_x(y0, -1) + road_x(y0, 1)) / 2
        xb = (road_x(y1, -1) + road_x(y1, 1)) / 2
        _poly(ctx, [(xa - 3, y0), (xa + 3, y0), (xb + 8, y1), (xb - 8, y1)], "#ffd166")
    # zebra crossing across the road near the characters
    for k in range(5):
        y0 = GROUND - 40 + k * 44
        y1 = y0 + 26
        _poly(ctx, [(road_x(y0, -1) + 10, y0), (road_x(y0, 1) - 10, y0), (road_x(y1, 1) - 10, y1),
                    (road_x(y1, -1) + 10, y1)], "#f7f7f2")
    # curb
    _poly(ctx, [(road_x(HORIZON, -1) - 4, HORIZON), (road_x(HORIZON, -1), HORIZON),
                (road_x(H + 200, -1), H + 200), (road_x(H + 200, -1) - 30, H + 200)], "#b8bec8")
    # traffic light
    _rr(ctx, 596, 760, 18, GROUND - 760, 6, "#3d4250")
    _rr(ctx, 566, 640, 78, 160, 16, "#3d4250")
    _round_tree(ctx, 60, GROUND - 120, 0.9)


def traffic_light(ctx, red):
    ellipse(ctx, 605, 680, 24, 24)
    _fill(ctx, "#ef476f" if red else "#5b2330")
    ellipse(ctx, 605, 760, 24, 24)
    _fill(ctx, "#06d6a0" if not red else "#1f4a3f")


def forest_camp(ctx):
    _sky(ctx, "#ffd6a5", "#fdf3e1")
    ellipse(ctx, 820, 420, 110, 110)
    _fill(ctx, "#ffb26b")
    for pts, c in (([(-200, 1100), (200, 640), (560, 1100)], "#b8a3d6"), ([(300, 1100), (760, 580), (1280, 1100)], "#a48fc8")):
        _poly(ctx, pts, c)
    for x in range(-160, W + 200, 120):
        _pine(ctx, x, 1180, 0.9, "#2f7d6d")
    ctx.rectangle(-200, 1150, W + 400, H)
    _fill(ctx, "#8fd18e")
    for x in range(-100, W + 200, 190):
        _pine(ctx, x + 40, 1260, 1.25, "#3f9f6b")
    ctx.rectangle(-200, 1240, W + 400, H)
    _fill(ctx, "#a7dd96")
    # path
    _poly(ctx, [(380, 1240), (560, 1240), (900, H + 200), (60, H + 200)], "#e8d3a9")
    # tent
    _poly(ctx, [(760, 1430), (900, 1180), (1040, 1430)], "#f28c5a")
    _poly(ctx, [(880, 1430), (900, 1240), (920, 1430)], "#a24d2d")
    # recycling bin
    _rr(ctx, 930, 1380, 110, 180, 16, "#3a86ff")
    _rr(ctx, 920, 1366, 130, 30, 12, "#2f6fd6")
    ctx.arc(985, 1470, 28, 0, 2 * math.pi)
    ctx.set_source_rgb(1, 1, 1)
    ctx.set_line_width(7)
    ctx.stroke()
    # little flowers
    for x, y in ((120, 1600), (230, 1680), (980, 1640), (820, 1740), (60, 1780)):
        for k in range(5):
            a = k * 2 * math.pi / 5
            ellipse(ctx, x + math.cos(a) * 10, y + math.sin(a) * 10, 8, 8)
            _fill(ctx, "#ffffff")
        ellipse(ctx, x, y, 6, 6)
        _fill(ctx, "#ffd166")


def picnic_park(ctx):
    _sky(ctx, "#8ecae6", "#e9f5f9")
    _cloud(ctx, 80, 300, 1.1)
    _cloud(ctx, 640, 220, 0.9)
    ellipse(ctx, 300, 1260, 760, 260)
    _fill(ctx, "#9ad18b")
    ellipse(ctx, 980, 1290, 640, 230)
    _fill(ctx, "#86c47a")
    for x, s, c in ((140, 1.2, "#5bb98c"), (860, 1.4, "#4fa97e"), (1050, 0.9, "#6cc59a")):
        _round_tree(ctx, x, 1250, s, c)
    ctx.rectangle(-200, 1240, W + 400, H)
    _fill(ctx, "#a7dd96")
    # picnic blanket (flat, gingham)
    _poly(ctx, [(380, GROUND - 30), (1040, GROUND - 30), (1160, GROUND + 120), (300, GROUND + 120)], "#ef476f")
    for k in range(8):
        x0 = 380 + k * 82
        _poly(ctx, [(x0, GROUND - 30), (x0 + 40, GROUND - 30), (x0 + 50 - k * 4, GROUND + 120), (x0 + 6 - k * 4, GROUND + 120)],
              "#ffffff", 0.35)
    for k in range(3):
        y0 = GROUND - 30 + k * 52
        ctx.rectangle(300, y0, 860, 22)
        _fill(ctx, "#ffffff", 0.25)
    # basket
    _rr(ctx, 860, GROUND - 120, 150, 100, 18, "#c98b4f")
    ctx.arc(935, GROUND - 120, 60, math.pi, 2 * math.pi)
    ctx.set_source_rgb(*rgb("#a8703c"))
    ctx.set_line_width(12)
    ctx.stroke()
    for x, y in ((80, 1620), (200, 1720), (1000, 1760), (720, 1840)):
        ellipse(ctx, x, y, 9, 9)
        _fill(ctx, "#ffd166")


scene.BACKGROUNDS.update(city_crosswalk=city_crosswalk, forest_camp=forest_camp, picnic_park=picnic_park)


# ------------------------------------------------------------------ props
def car(ctx, u):
    """Car driving out of the vanishing point towards the camera; u: 0 (far) -> 1 (gone past)."""
    if not 0 <= u <= 1:
        return
    e = EASE["in"](u)
    y = HORIZON + 30 + (H + 500 - HORIZON) * e
    x = (road_x(y, -1) + road_x(y, 1)) / 2 + 120 * e
    s = 0.12 + 2.6 * e
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ellipse(ctx, 0, 10, 150, 22)
    _fill(ctx, (0, 0, 0), 0.18)
    _rr(ctx, -140, -150, 280, 150, 40, "#ef476f")
    _rr(ctx, -100, -230, 200, 110, 36, "#ef476f")
    _rr(ctx, -80, -215, 160, 80, 22, "#cfe8f5")
    for d in (-1, 1):
        ellipse(ctx, d * 100, -80, 26, 20)
        _fill(ctx, "#fff3b0")
        _rr(ctx, d * 120 - 22, -10, 44, 50, 12, "#2b2d42")
    _rr(ctx, -60, -60, 120, 26, 10, "#c43c5c")
    ctx.restore()


def can(ctx, x, y, rot=0.0, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    _rr(ctx, -20, -36, 40, 72, 10, "#f77f00")
    ctx.rectangle(-20, -10, 40, 18)
    _fill(ctx, "#fcbf49")
    _rr(ctx, -18, -40, 36, 8, 4, "#c9c9c9")
    ctx.restore()


def sandwich(ctx, x, y, half=False, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    w = 60 if half else 110
    _rr(ctx, -w / 2, -10, w, 22, 10, "#f2c27b")
    _rr(ctx, -w / 2 - 4, -16, w + 8, 10, 5, "#7ac142")
    _rr(ctx, -w / 2, -24, w, 10, 5, "#ef476f")
    _rr(ctx, -w / 2, -42, w, 22, 10, "#f2c27b")
    ctx.restore()


def lesson_card(ctx, t, t0, text, icon="heart"):
    """End card with the lesson of the episode."""
    u = clamp((t - t0) / 0.35)
    if u <= 0:
        return
    sc = EASE["back"](u)
    scene.set_font(ctx, 54)
    tw = ctx.text_extents(text).x_advance
    fit = min(1.15, 980 / (tw + 160))
    ctx.save()
    ctx.translate(W / 2, 500)
    ctx.scale(sc * fit, sc * fit)
    _rr(ctx, -tw / 2 - 90, -66, tw + 160, 120, 60, (0, 0, 0), 0.18)
    _rr(ctx, -tw / 2 - 96, -74, tw + 160, 120, 60, "#ffffff")
    cx = -tw / 2 - 40
    if icon == "heart":
        ctx.move_to(cx, -2)
        ctx.curve_to(cx - 36, -30, cx - 20, -56, cx, -38)
        ctx.curve_to(cx + 20, -56, cx + 36, -30, cx, -2)
        _fill(ctx, "#ef476f")
    else:
        ellipse(ctx, cx, -16, 26, 26)
        _fill(ctx, "#06d6a0")
    scene.text(ctx, text, cx + 44, 4, 54, scene.THEME["card_text"], stroke=0, align="left")
    ctx.restore()
