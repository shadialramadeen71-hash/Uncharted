"""Cairo drawing helpers: shapes, the two heroes (Leo & Bruno), props and backgrounds.

Canvas is a vertical YouTube Shorts frame: 1080 x 1920.
"""
import math
import random

import cairo

W, H = 1080, 1920
GY = 1500  # ground line where characters' feet stand
PI = math.pi
OUT = (0.16, 0.11, 0.08)  # cartoon outline colour
FONT = "Inter Display"


# ---------------------------------------------------------------- utilities
def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t, k=1.70158):
    t = clamp(t) - 1
    return t * t * ((k + 1) * t + k) + 1


def ease_in(t):
    t = clamp(t)
    return t * t


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) * (1 - t)


def ellipse(ctx, x, y, rx, ry):
    ctx.new_sub_path()
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.arc(0, 0, 1, 0, 2 * PI)
    ctx.restore()


def circle(ctx, x, y, r):
    ellipse(ctx, x, y, r, r)


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -PI / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, PI / 2)
    ctx.arc(x + r, y + h - r, r, PI / 2, PI)
    ctx.arc(x + r, y + r, r, PI, 1.5 * PI)
    ctx.close_path()


def paint(ctx, color, lw=6, outline=True, a=1.0):
    """Fill the current path, optionally with a dark cartoon outline."""
    ctx.set_source_rgba(*hexc(color, a))
    if outline:
        ctx.fill_preserve()
        ctx.set_source_rgba(*OUT, a)
        ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
    else:
        ctx.fill()


def blob(ctx, color, lw=6):
    """Fill a path made of overlapping sub-shapes with a single outer outline."""
    ctx.set_source_rgba(*OUT, 1)
    ctx.set_line_width(lw * 2)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*hexc(color))
    ctx.fill()


def limb(ctx, pts, w, color, lw=6):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    if len(pts) == 4:
        ctx.curve_to(*pts[1], *pts[2], *pts[3])
    else:
        for p in pts[1:]:
            ctx.line_to(*p)
    ctx.set_source_rgba(*OUT, 1)
    ctx.set_line_width(w + 2 * lw)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*hexc(color))
    ctx.set_line_width(w)
    ctx.stroke()


def line(ctx, pts, w, color, a=1.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.set_source_rgba(*hexc(color, a))
    ctx.set_line_width(w)
    ctx.stroke()


def star_path(ctx, x, y, r_out, r_in, n=5, rot=-PI / 2):
    ctx.new_sub_path()
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * PI / n
        px, py = x + math.cos(a) * r, y + math.sin(a) * r
        if i == 0:
            ctx.move_to(px, py)
        else:
            ctx.line_to(px, py)
    ctx.close_path()


def text_size(ctx, s, size):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    return ctx.text_extents(s).x_advance


def text(ctx, s, x, y, size, color="#ffffff", stroke="#2a1a10", sw=12, align="center", a=1.0):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    adv = ctx.text_extents(s).x_advance
    x0 = x - adv / 2 if align == "center" else x
    ctx.move_to(x0, y)
    ctx.text_path(s)
    if stroke:
        ctx.set_source_rgba(*hexc(stroke, a))
        ctx.set_line_width(sw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    ctx.set_source_rgba(*hexc(color, a))
    ctx.fill()
    return adv


def pop_text(ctx, s, x, y, age, size=110, color="#FFE14D", rot=-0.12, life=0.9):
    """Comic onomatopoeia that pops in and fades out (age = seconds since start)."""
    if age < 0 or age > life:
        return
    k = ease_out_back(age / 0.25) if age < 0.25 else 1.0
    a = 1.0 if age < life - 0.25 else clamp((life - age) / 0.25)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(k, k)
    text(ctx, s, 0, size * 0.35, size, color=color, stroke="#2a1a10", sw=16, a=a)
    ctx.restore()


def sparkle(ctx, x, y, r, a=1.0, color="#FFF6B0"):
    star_path(ctx, x, y, r, r * 0.28, n=4, rot=0)
    ctx.set_source_rgba(*hexc(color, a))
    ctx.fill()


# ---------------------------------------------------------------- characters
SKIN = "#FFD1A8"
HAIR = "#6B3E1E"


def _eyes(ctx, ex, ey, rx, ry, pr, look, blink, expr, lw):
    for side in (-1, 1):
        x = side * ex
        if blink:
            ctx.move_to(x - rx, ey)
            ctx.curve_to(x - rx * 0.5, ey + ry * 0.45, x + rx * 0.5, ey + ry * 0.45, x + rx, ey)
            ctx.set_source_rgba(*OUT, 1)
            ctx.set_line_width(lw)
            ctx.stroke()
            continue
        sy = 1.15 if expr in ("surprised", "scared") else 1.0
        ellipse(ctx, x, ey, rx * sy, ry * sy)
        paint(ctx, "#ffffff", lw=lw * 0.8)
        px = x + look[0] * rx * 0.35
        py = ey + look[1] * ry * 0.3
        pr2 = pr * (0.8 if expr in ("surprised", "scared") else 1.0)
        circle(ctx, px, py, pr2)
        ctx.set_source_rgba(*OUT, 1)
        ctx.fill()
        circle(ctx, px + pr2 * 0.35, py - pr2 * 0.4, pr2 * 0.38)
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.fill()
        if expr == "laugh":  # happy closed-eye arcs over the top
            ellipse(ctx, x, ey, rx * 1.05, ry * 1.05)
            ctx.set_source_rgba(*hexc(SKIN))
            ctx.fill()
            ctx.move_to(x - rx * 0.8, ey + ry * 0.2)
            ctx.curve_to(x - rx * 0.4, ey - ry * 0.6, x + rx * 0.4, ey - ry * 0.6, x + rx * 0.8, ey + ry * 0.2)
            ctx.set_source_rgba(*OUT, 1)
            ctx.set_line_width(lw * 1.1)
            ctx.stroke()


def _brows(ctx, ex, by, w, expr, lw, color=None):
    col = color or OUT
    for side in (-1, 1):
        x = side * ex
        if expr in ("surprised",):
            y0 = y1 = by - 14
        elif expr == "scared":
            y0, y1 = by - 2, by - 16  # inner end raised
        elif expr == "angry":
            y0, y1 = by - 12, by + 6
        else:
            y0 = y1 = by
        inner = x - side * w * 0.5
        outer = x + side * w * 0.5
        ctx.move_to(inner, y1)
        ctx.curve_to(inner + side * w * 0.3, y1 - 8, outer - side * w * 0.3, y0 - 8, outer, y0)
        ctx.set_source_rgba(*col, 1) if isinstance(col, tuple) else ctx.set_source_rgba(*hexc(col))
        ctx.set_line_width(lw * 1.3)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


def _mouth(ctx, x, y, mouth, expr, scale, lw):
    if mouth > 0.06 or expr == "laugh":
        m = max(mouth, 0.55 if expr == "laugh" else 0)
        rx = (22 + 10 * m) * scale
        ry = (6 + 26 * m) * scale
        ctx.save()
        ellipse(ctx, x, y + ry * 0.3, rx, ry)
        paint(ctx, "#7A1E22", lw=lw * 0.8)
        ellipse(ctx, x, y + ry * 0.3, rx, ry)
        ctx.clip()
        ellipse(ctx, x, y + ry * 1.05, rx * 0.75, ry * 0.6)
        ctx.set_source_rgba(*hexc("#F07C8A"))
        ctx.fill()
        ctx.restore()
    elif expr == "surprised":
        ellipse(ctx, x, y + 6 * scale, 12 * scale, 15 * scale)
        paint(ctx, "#7A1E22", lw=lw * 0.8)
    elif expr == "scared":
        ctx.move_to(x - 26 * scale, y + 8 * scale)
        for i in range(1, 7):
            ctx.line_to(x - 26 * scale + i * 52 * scale / 6, y + (8 + (-7 if i % 2 else 0)) * scale)
        ctx.set_source_rgba(*OUT, 1)
        ctx.set_line_width(lw)
        ctx.stroke()
    else:
        ctx.arc(x, y - 14 * scale, 28 * scale, 0.2 * PI, 0.8 * PI)
        ctx.set_source_rgba(*OUT, 1)
        ctx.set_line_width(lw)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


def _arm_end(sx, sy, side, ang, length):
    a = math.radians(ang)
    return sx + side * math.sin(a) * length, sy + math.cos(a) * length


def draw_leo(ctx, x, y, s=1.0, face=1, mouth=0.0, blink=False, expr="happy", arms=(12, 12),
             look=(0.6, 0), walk=None, hop=0.0, rot=0.0, alpha=1.0):
    """Leo, the little boy. arms = (back-arm angle, front-arm angle) in degrees from hanging
    down (0) to straight up (180). Returns global positions of the hands."""
    lw = 6
    if alpha < 1:
        ctx.push_group()
    ctx.save()
    ctx.translate(x, y - hop)
    ctx.rotate(rot)
    ctx.scale(s * face, s)
    bob, swing = 0.0, 0.0
    if walk is not None:
        bob = -abs(math.sin(walk)) * 16
        swing = math.sin(walk) * 26
    ctx.translate(0, bob)

    # legs + shoes
    for lx, sw in ((-28, swing), (28, -swing)):
        limb(ctx, [(lx, -150), (lx + sw, -26)], 34, SKIN, lw)
        ellipse(ctx, lx + sw + 10, -16, 36, 21)
        paint(ctx, "#E8423F", lw)
        ellipse(ctx, lx + sw + 10, -6, 34, 8)
        ctx.set_source_rgba(1, 1, 1, 0.9)
        ctx.fill()
    # shorts
    rrect(ctx, -72, -218, 144, 88, 26)
    paint(ctx, "#2F74D8", lw)
    # shirt
    rrect(ctx, -80, -348, 160, 152, 52)
    paint(ctx, "#FFC531", lw)
    star_path(ctx, 0, -272, 30, 13)
    paint(ctx, "#FF8A1F", lw * 0.6)

    hands = {}
    for name, side, ang in (("back", -1, arms[0]), ("front", 1, arms[1])):
        sx, sy = side * 68, -326
        if walk is not None and ang < 40:
            ang = ang + (math.sin(walk) * 22 * side)
        ex, ey = _arm_end(sx, sy, side, ang, 118)
        limb(ctx, [(sx, sy), (ex, ey)], 30, SKIN, lw)
        circle(ctx, ex, ey, 21)
        paint(ctx, SKIN, lw)
        circle(ctx, sx, sy, 27)
        paint(ctx, "#FFC531", lw, outline=False)
        hands[name] = ctx.user_to_device(ex, ey)

    hy = -462
    # ears
    for side in (-1, 1):
        circle(ctx, side * 120, hy + 12, 25)
        paint(ctx, SKIN, lw)
    circle(ctx, 0, hy, 124)
    paint(ctx, SKIN, lw)
    # hair (one outlined blob of bumps + a cowlick)
    ctx.new_path()
    for cx, cy, r in ((-96, -520, 46), (-58, -562, 52), (-6, -580, 54), (48, -566, 52), (94, -528, 46),
                      (-112, -478, 30), (112, -482, 28)):
        circle(ctx, cx, cy, r)
    ctx.new_sub_path()
    ctx.move_to(-10, -620)
    ctx.curve_to(10, -690, 60, -680, 70, -650)
    ctx.curve_to(40, -660, 30, -630, 30, -600)
    ctx.close_path()
    blob(ctx, HAIR, lw * 0.75)
    # cheeks
    for side in (-1, 1):
        circle(ctx, side * 78, hy + 42, 20)
        ctx.set_source_rgba(*hexc("#FF8FA0", 0.45))
        ctx.fill()
    _eyes(ctx, 44, hy + 4, 25, 31, 14, look, blink, expr, lw)
    _brows(ctx, 46, hy - 46, 40, expr, lw, HAIR)
    _mouth(ctx, 0, hy + 64, mouth, expr, 1.0, lw)
    ctx.restore()
    if alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
    return hands


BR = "#9A5B2C"
BRL = "#E2AE72"


def draw_bruno(ctx, x, y, s=1.0, face=1, mouth=0.0, blink=False, expr="happy", arms=(18, 18),
               look=(0.6, 0), walk=None, hop=0.0, rot=0.0, snow=0.0, alpha=1.0):
    """Bruno, the big friendly bear. Same conventions as draw_leo."""
    lw = 7
    if alpha < 1:
        ctx.push_group()
    ctx.save()
    ctx.translate(x, y - hop)
    ctx.rotate(rot)
    ctx.scale(s * face, s)
    bob, swing = 0.0, 0.0
    if walk is not None:
        bob = -abs(math.sin(walk)) * 18
        swing = math.sin(walk) * 22
    ctx.translate(0, bob)

    for lx, sw in ((-78, swing), (78, -swing)):
        ellipse(ctx, lx + sw, -62, 64, 72)
        paint(ctx, BR, lw)
        ellipse(ctx, lx + sw, -22, 44, 20)
        paint(ctx, BRL, lw * 0.7)
    ellipse(ctx, 0, -290, 198, 236)
    paint(ctx, BR, lw)
    ellipse(ctx, 0, -262, 128, 160)
    paint(ctx, BRL, lw * 0.6, outline=False)

    hands = {}
    for name, side, ang in (("back", -1, arms[0]), ("front", 1, arms[1])):
        sx, sy = side * 150, -410
        if walk is not None and ang < 40:
            ang = ang + (math.sin(walk) * 18 * side)
        ex, ey = _arm_end(sx, sy, side, ang, 178)
        limb(ctx, [(sx, sy), (ex, ey)], 74, BR, lw)
        circle(ctx, ex, ey, 46)
        paint(ctx, BR, lw)
        ellipse(ctx, ex, ey + 8, 24, 18)
        ctx.set_source_rgba(*hexc(BRL))
        ctx.fill()
        hands[name] = ctx.user_to_device(ex, ey)

    # scarf
    rrect(ctx, -128, -520, 256, 54, 27)
    paint(ctx, "#E53935", lw)
    ctx.move_to(40, -480)
    ctx.line_to(96, -380)
    ctx.line_to(48, -372)
    ctx.line_to(20, -478)
    ctx.close_path()
    paint(ctx, "#E53935", lw)

    hy = -660
    for side in (-1, 1):
        circle(ctx, side * 122, hy - 118, 54)
        paint(ctx, BR, lw)
        circle(ctx, side * 122, hy - 116, 30)
        paint(ctx, BRL, lw, outline=False)
    circle(ctx, 0, hy, 168)
    paint(ctx, BR, lw)
    ellipse(ctx, 0, hy + 60, 88, 64)
    paint(ctx, BRL, lw * 0.7)
    for side in (-1, 1):
        circle(ctx, side * 104, hy + 40, 22)
        ctx.set_source_rgba(*hexc("#FF7F7F", 0.35))
        ctx.fill()
    _eyes(ctx, 60, hy - 30, 23, 27, 14, look, blink, expr, lw)
    _brows(ctx, 60, hy - 92, 34, expr, lw * 0.8)
    ellipse(ctx, 0, hy + 30, 32, 22)
    paint(ctx, "#2B1B12", lw * 0.5)
    ellipse(ctx, -9, hy + 22, 10, 6)
    ctx.set_source_rgba(1, 1, 1, 0.7)
    ctx.fill()
    if mouth > 0.06 or expr in ("laugh", "surprised", "scared"):
        m = max(mouth, {"laugh": 0.6, "surprised": 0.35, "scared": 0.45}.get(expr, 0))
        _mouth(ctx, 0, hy + 72, m, expr, 1.15, lw)
    else:
        ctx.move_to(0, hy + 52)
        ctx.line_to(0, hy + 70)
        ctx.arc(-18, hy + 70, 18, 0, PI)
        ctx.move_to(36, hy + 70)
        ctx.arc(18, hy + 70, 18, 0, PI)
        ctx.set_source_rgba(*OUT, 1)
        ctx.set_line_width(lw * 0.9)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()

    if snow > 0:
        # snow cap and patches after the giant snowball accident
        ctx.new_path()
        for cx, cy, r in ((-90, -790, 60), (-30, -830, 70), (40, -830, 70), (100, -790, 58), (0, -780, 80),
                          (-150, -800, 40), (150, -800, 40)):
            circle(ctx, cx, cy, r * snow)
        blob(ctx, "#FFFFFF", lw * 0.5)
        for cx, cy, r in ((-150, -440, 46), (150, -440, 46), (-60, -330, 30), (80, -160, 34), (-110, -120, 28)):
            circle(ctx, cx, cy, r * snow)
            paint(ctx, "#F4FAFF", lw * 0.5)
        for side in (-1, 1):
            ctx.move_to(side * 40, -812)
            ctx.line_to(side * 52, -740 + 20 * side)
            ctx.line_to(side * 64, -812)
            paint(ctx, "#DFF3FF", lw * 0.4)
    ctx.restore()
    if alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
    return hands


# ---------------------------------------------------------------- scenery
def sky(ctx, top, bottom, y1=H):
    g = cairo.LinearGradient(0, 0, 0, y1)
    g.add_color_stop_rgba(0, *hexc(top))
    g.add_color_stop_rgba(1, *hexc(bottom))
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(g)
    ctx.fill()


def cloud(ctx, x, y, s=1.0, a=1.0):
    parts = ((0, 0, 60), (-70, 18, 46), (70, 16, 50), (-30, -34, 48), (34, -30, 54), (120, 30, 34), (-118, 32, 32))
    for dx, dy, r in parts:
        circle(ctx, x + dx * s, y + dy * s + 10 * s, r * s)
    ctx.set_source_rgba(0.75, 0.86, 0.96, 0.8 * a)
    ctx.fill()
    for dx, dy, r in parts:
        circle(ctx, x + dx * s, y + dy * s, r * s)
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.fill()


def sun(ctx, x, y, r, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(t * 0.4)
    for i in range(12):
        ctx.rotate(PI / 6)
        ctx.move_to(r * 1.25, -10)
        ctx.line_to(r * 1.65, 0)
        ctx.line_to(r * 1.25, 10)
        ctx.close_path()
    ctx.set_source_rgba(*hexc("#FFD54A", 0.9))
    ctx.fill()
    ctx.restore()
    circle(ctx, x, y, r)
    paint(ctx, "#FFE066", 0, outline=False)
    circle(ctx, x - r * 0.3, y - r * 0.3, r * 0.35)
    ctx.set_source_rgba(1, 1, 1, 0.35)
    ctx.fill()


def hills(ctx, y, amp, freq, phase, color, outline=False):
    ctx.move_to(0, H)
    for i in range(0, W + 21, 20):
        ctx.line_to(i, y + math.sin(i * freq + phase) * amp + math.sin(i * freq * 2.3 + phase * 1.7) * amp * 0.35)
    ctx.line_to(W, H)
    ctx.close_path()
    paint(ctx, color, 5, outline=outline)


def tree(ctx, x, y, s=1.0, green="#4CAF50", dark="#3E8E41"):
    rrect(ctx, x - 28 * s, y - 230 * s, 56 * s, 240 * s, 18 * s)
    paint(ctx, "#8D5A33", 6 * s)
    ctx.new_path()
    for dx, dy, r in ((0, -330, 110), (-90, -260, 80), (90, -260, 84), (-50, -390, 80), (60, -380, 78)):
        circle(ctx, x + dx * s, y + dy * s, r * s)
    blob(ctx, green, 5 * s)
    for dx, dy, r in ((-40, -300, 22), (50, -340, 18), (10, -250, 16)):
        circle(ctx, x + dx * s, y + dy * s, r * s)
        ctx.set_source_rgba(*hexc(dark, 0.6))
        ctx.fill()


def pine(ctx, x, y, s=1.0, snow=False):
    rrect(ctx, x - 16 * s, y - 70 * s, 32 * s, 80 * s, 8 * s)
    paint(ctx, "#7A4B2A", 5 * s)
    for i, (w, top, bot) in enumerate(((130, -250, -50), (105, -350, -170), (80, -440, -270))):
        ctx.move_to(x, y + top * s)
        ctx.line_to(x + w * s, y + bot * s)
        ctx.line_to(x - w * s, y + bot * s)
        ctx.close_path()
        paint(ctx, "#2E7D4F", 5 * s)
        if snow:
            ctx.move_to(x, y + top * s)
            ctx.line_to(x + w * 0.45 * s, y + (top + (bot - top) * 0.45) * s)
            for k in range(4):
                ctx.line_to(x + w * (0.45 - 0.3 * k) * s, y + (top + (bot - top) * (0.52 if k % 2 == 0 else 0.42)) * s)
            ctx.line_to(x - w * 0.45 * s, y + (top + (bot - top) * 0.45) * s)
            ctx.close_path()
            paint(ctx, "#FFFFFF", 4 * s)


def flower(ctx, x, y, color, s=1.0):
    line(ctx, [(x, y), (x, y - 40 * s)], 5 * s, "#2E7D32")
    for i in range(5):
        a = i * 2 * PI / 5
        circle(ctx, x + math.cos(a) * 12 * s, y - 40 * s + math.sin(a) * 12 * s, 10 * s)
        paint(ctx, color, 3 * s)
    circle(ctx, x, y - 40 * s, 8 * s)
    paint(ctx, "#FFD54A", 3 * s)


def grass_ground(ctx, top, color="#69C24A", light="#8ED65F"):
    ctx.move_to(0, top)
    for i in range(0, W + 41, 40):
        ctx.line_to(i, top + math.sin(i * 0.013) * 14)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    paint(ctx, color, 6)
    rnd = random.Random(7)
    for _ in range(40):
        gx, gy = rnd.uniform(0, W), rnd.uniform(top + 40, H - 40)
        line(ctx, [(gx - 10, gy), (gx - 4, gy - 22), (gx, gy), (gx + 6, gy - 26), (gx + 10, gy)], 5, light)


def bg_forest(ctx, t):
    sky(ctx, "#7CCBFF", "#E4F7FF", 1400)
    sun(ctx, 170, 640, 70, t)
    for i, (bx, by, s, sp) in enumerate(((150, 820, 0.9, 18), (700, 700, 1.1, 12), (1100, 900, 0.7, 22))):
        cloud(ctx, (bx + t * sp) % 1400 - 160, by, s)
    hills(ctx, 1150, 40, 0.006, 1.0, "#A8DD86")
    for i, tx in enumerate((-30, 170, 380, 980, 1110)):
        tree(ctx, tx, 1330, 0.75 + 0.1 * (i % 2), "#5DBB63")
    grass_ground(ctx, 1330)
    for fx, fy, c in ((80, 1640, "#FF6F91"), (460, 1700, "#FFFFFF"), (760, 1660, "#B388FF"), (990, 1730, "#FF6F91"),
                      (230, 1790, "#FFFFFF")):
        flower(ctx, fx, fy, c)


def bg_beach(ctx, t):
    sky(ctx, "#6EC8FF", "#FFF0C8", 1200)
    sun(ctx, 860, 640, 80, t)
    cloud(ctx, (200 + t * 14) % 1400 - 160, 800, 0.9)
    cloud(ctx, (900 + t * 10) % 1400 - 160, 900, 0.7)
    ctx.rectangle(0, 1080, W, 300)
    g = cairo.LinearGradient(0, 1080, 0, 1340)
    g.add_color_stop_rgba(0, *hexc("#1E9BD7"))
    g.add_color_stop_rgba(1, *hexc("#56CCF2"))
    ctx.set_source(g)
    ctx.fill()
    for row in range(4):
        yy = 1120 + row * 55
        for i in range(-1, 9):
            xx = i * 150 + (t * (40 + row * 15)) % 150 + row * 40
            ctx.move_to(xx, yy)
            ctx.curve_to(xx + 25, yy - 14, xx + 50, yy - 14, xx + 75, yy)
        ctx.set_source_rgba(1, 1, 1, 0.55)
        ctx.set_line_width(5)
        ctx.stroke()
    # sand with a foamy edge
    edge = 1330 + math.sin(t * 1.6) * 8
    ctx.move_to(0, edge)
    for i in range(0, W + 41, 40):
        ctx.line_to(i, edge + math.sin(i * 0.02 + t * 2) * 10)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    paint(ctx, "#F6D58E", 6)
    ctx.move_to(0, edge + 2)
    for i in range(0, W + 41, 40):
        ctx.line_to(i, edge + 2 + math.sin(i * 0.02 + t * 2) * 10)
    ctx.set_source_rgba(1, 1, 1, 0.85)
    ctx.set_line_width(10)
    ctx.stroke()
    # palm tree on the left edge
    ctx.move_to(-20, 1520)
    ctx.curve_to(40, 1300, 60, 1100, 20, 900)
    ctx.line_to(70, 900)
    ctx.curve_to(110, 1100, 90, 1320, 50, 1520)
    ctx.close_path()
    paint(ctx, "#A8713F", 6)
    for a in (-2.7, -2.1, -1.5, -0.9, -0.3):
        sway = math.sin(t * 1.5 + a) * 0.05
        ctx.save()
        ctx.translate(45, 900)
        ctx.rotate(a + sway)
        ctx.move_to(0, 0)
        ctx.curve_to(80, -60, 170, -40, 240, 30)
        ctx.curve_to(160, 0, 80, 10, 0, 0)
        paint(ctx, "#3FA34D", 5)
        ctx.restore()
    for sx, sy in ((700, 1760), (260, 1820), (930, 1660)):
        star_path(ctx, sx, sy, 28, 13)
        paint(ctx, "#FF8A65", 4)


def bg_snow(ctx, t):
    sky(ctx, "#A9DCFF", "#F2FAFF", 1300)
    cloud(ctx, (300 + t * 10) % 1400 - 160, 760, 0.8, 0.9)
    for mx, mh, mw in ((120, 640, 360), (560, 520, 420), (980, 600, 360)):
        ctx.move_to(mx - mw, 1250)
        ctx.line_to(mx, 1250 - mh)
        ctx.line_to(mx + mw, 1250)
        ctx.close_path()
        paint(ctx, "#B8CDE6", 5)
        ctx.move_to(mx - mw * 0.3, 1250 - mh * 0.7)
        ctx.line_to(mx, 1250 - mh)
        ctx.line_to(mx + mw * 0.3, 1250 - mh * 0.7)
        ctx.line_to(mx + mw * 0.12, 1250 - mh * 0.62)
        ctx.line_to(mx, 1250 - mh * 0.72)
        ctx.line_to(mx - mw * 0.14, 1250 - mh * 0.6)
        ctx.close_path()
        paint(ctx, "#FFFFFF", 4)
    hills(ctx, 1240, 30, 0.007, 2.0, "#E6F2FF", outline=True)
    for i, px in enumerate((40, 200, 920, 1060)):
        pine(ctx, px, 1340 + (i % 2) * 20, 0.75, snow=True)
    ctx.move_to(0, 1350)
    for i in range(0, W + 41, 40):
        ctx.line_to(i, 1350 + math.sin(i * 0.01 + 1) * 16)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    paint(ctx, "#FBFDFF", 6)
    for ex, ey, rx in ((300, 1700, 160), (820, 1780, 200)):
        ellipse(ctx, ex, ey, rx, 22)
        ctx.set_source_rgba(*hexc("#CFE3F7", 0.6))
        ctx.fill()


def snowfall(ctx, t, n=70):
    rnd = random.Random(3)
    for i in range(n):
        x0, y0, sp, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(60, 140), rnd.uniform(4, 10)
        x = (x0 + math.sin(t * 1.3 + i) * 30) % W
        y = (y0 + t * sp) % H
        circle(ctx, x, y, r)
        ctx.set_source_rgba(1, 1, 1, 0.9)
        ctx.fill()


def bg_night(ctx, t, star_shift=0.0):
    sky(ctx, "#0A1240", "#3A4B92", 1400)
    rnd = random.Random(11)
    for i in range(90):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, 1300), rnd.uniform(2, 6)
        y = (y + star_shift) % 1400
        tw = 0.5 + 0.5 * math.sin(t * 3 + i)
        if r > 4.5:
            sparkle(ctx, x, y, r * 2.2, 0.5 + 0.5 * tw)
        else:
            circle(ctx, x, y, r)
            ctx.set_source_rgba(1, 1, 0.9, 0.4 + 0.6 * tw)
            ctx.fill()


def moon(ctx, x, y, r):
    circle(ctx, x, y, r * 1.5)
    ctx.set_source_rgba(1, 1, 0.8, 0.12)
    ctx.fill()
    circle(ctx, x, y, r)
    paint(ctx, "#FFF3B0", 5)
    for dx, dy, cr in ((-0.3, -0.2, 0.18), (0.25, 0.25, 0.22), (0.3, -0.35, 0.1)):
        circle(ctx, x + dx * r, y + dy * r, cr * r)
        ctx.set_source_rgba(*hexc("#E8D98A"))
        ctx.fill()


def night_ground(ctx, t):
    hills(ctx, 1230, 35, 0.006, 0.4, "#1B3A4B")
    # little house with a lit window
    rrect(ctx, 840, 1080, 220, 200, 6)
    paint(ctx, "#5B4B8A", 5)
    ctx.move_to(820, 1090)
    ctx.line_to(950, 970)
    ctx.line_to(1080, 1090)
    ctx.close_path()
    paint(ctx, "#C0504D", 5)
    rrect(ctx, 880, 1130, 70, 70, 6)
    paint(ctx, "#FFD86B", 4)
    ctx.move_to(0, 1330)
    for i in range(0, W + 41, 40):
        ctx.line_to(i, 1330 + math.sin(i * 0.013) * 12)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    paint(ctx, "#2F6B4F", 6)
    for i in range(12):  # fireflies
        fx = (i * 97 + math.sin(t * 0.9 + i) * 60) % W
        fy = 1400 + (i * 53) % 400 + math.cos(t * 1.2 + i) * 30
        a = 0.5 + 0.5 * math.sin(t * 4 + i * 2)
        circle(ctx, fx, fy, 12)
        ctx.set_source_rgba(1, 1, 0.5, 0.25 * a)
        ctx.fill()
        circle(ctx, fx, fy, 5)
        ctx.set_source_rgba(1, 1, 0.6, a)
        ctx.fill()


def bg_river(ctx, t):
    sky(ctx, "#86D0FF", "#E9F8FF", 1200)
    sun(ctx, 900, 620, 66, t)
    cloud(ctx, (120 + t * 16) % 1400 - 160, 760, 0.85)
    cloud(ctx, (760 + t * 11) % 1400 - 160, 880, 0.65)
    hills(ctx, 1080, 50, 0.005, 0.2, "#8FD27A")
    for tx in (60, 260, 860, 1040):
        tree(ctx, tx, 1170, 0.55, "#4CAF50")
    ctx.move_to(0, 1160)
    for i in range(0, W + 41, 40):
        ctx.line_to(i, 1160 + math.sin(i * 0.01) * 8)
    ctx.line_to(W, 1420)
    ctx.line_to(0, 1420)
    ctx.close_path()
    g = cairo.LinearGradient(0, 1160, 0, 1420)
    g.add_color_stop_rgba(0, *hexc("#2E9BDB"))
    g.add_color_stop_rgba(1, *hexc("#5CC6F0"))
    ctx.set_source(g)
    ctx.fill()
    for row in range(4):
        yy = 1200 + row * 50
        for i in range(-1, 8):
            xx = i * 170 + (t * (50 + row * 20)) % 170 + row * 60
            ctx.move_to(xx, yy)
            ctx.line_to(xx + 60, yy)
        ctx.set_source_rgba(1, 1, 1, 0.5)
        ctx.set_line_width(5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    grass_ground(ctx, 1400)
    for rx in (40, 80, 1000, 1040):
        sway = math.sin(t * 2 + rx) * 6
        line(ctx, [(rx, 1440), (rx + sway, 1300)], 7, "#3E8E41")
        ellipse(ctx, rx + sway, 1300, 10, 30)
        paint(ctx, "#8D5A33", 3)


# ---------------------------------------------------------------- props
def beehive(ctx, x, y, shake=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(shake * 0.02)
    line(ctx, [(0, -110), (0, -70)], 8, "#5D3A1A")
    for i, (w, yy) in enumerate(((48, -60), (72, -20), (80, 22), (64, 62))):
        ellipse(ctx, 0, yy, w, 26)
        paint(ctx, "#F2B33D" if i % 2 == 0 else "#E8A52A", 5)
    ellipse(ctx, 0, 30, 16, 14)
    paint(ctx, "#3A2412", 3)
    ellipse(ctx, 22, 84, 10, 16)  # honey drip
    paint(ctx, "#FFB300", 3)
    ctx.restore()


def honey_tree(ctx, x, y, hive, shake=0.0):
    rrect(ctx, x - 50, y - 520, 100, 540, 30)
    paint(ctx, "#8D5A33", 7)
    ctx.move_to(x - 30, y - 430)
    ctx.curve_to(x - 120, y - 470, x - 170, y - 560, x - 190, y - 600)
    ctx.set_source_rgba(*OUT, 1)
    ctx.set_line_width(40)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*hexc("#8D5A33"))
    ctx.set_line_width(28)
    ctx.stroke()
    ctx.new_path()
    for dx, dy, r in ((0, -700, 170), (-150, -630, 120), (130, -620, 120), (-80, -820, 120), (90, -810, 120)):
        circle(ctx, x + dx, y + dy, r)
    blob(ctx, "#4CAF50", 6)
    beehive(ctx, hive[0], hive[1], shake)


def bee(ctx, x, y, t, s=1.0, face=1):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * face, s)
    flap = math.sin(t * 60) * 0.5
    for dx in (-6, 10):
        ctx.save()
        ctx.translate(dx, -16)
        ctx.rotate(-0.4 + flap * (1 if dx > 0 else -1))
        ellipse(ctx, 0, -14, 12, 20)
        ctx.set_source_rgba(1, 1, 1, 0.8)
        ctx.fill_preserve()
        ctx.set_source_rgba(*OUT, 0.8)
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.restore()
    ellipse(ctx, 0, 0, 28, 20)
    paint(ctx, "#FFD028", 4)
    ctx.save()
    ellipse(ctx, 0, 0, 28, 20)
    ctx.clip()
    for sx in (-12, 4):
        ctx.rectangle(sx, -22, 8, 44)
    ctx.set_source_rgba(*OUT, 1)
    ctx.fill()
    ctx.restore()
    circle(ctx, 18, -4, 4)
    ctx.set_source_rgba(*OUT, 1)
    ctx.fill()
    ctx.move_to(-28, 0)
    ctx.line_to(-38, 4)
    ctx.line_to(-28, 6)
    ctx.set_source_rgba(*OUT, 1)
    ctx.fill()
    ctx.restore()


def treasure_map(ctx, x, y, s=1.0, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.move_to(-90, -60)
    ctx.line_to(-30, -70)
    ctx.line_to(30, -58)
    ctx.line_to(90, -68)
    ctx.line_to(90, 62)
    ctx.line_to(30, 72)
    ctx.line_to(-30, 60)
    ctx.line_to(-90, 70)
    ctx.close_path()
    paint(ctx, "#F5E0AE", 5)
    ctx.set_dash([10, 8])
    ctx.move_to(-60, 40)
    ctx.curve_to(-30, -20, 10, 40, 40, -20)
    ctx.set_source_rgba(*hexc("#8D5A33"))
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.set_dash([])
    line(ctx, [(30, -40), (58, -10)], 9, "#E53935")
    line(ctx, [(58, -40), (30, -10)], 9, "#E53935")
    ctx.restore()


def cookie(ctx, x, y, r):
    circle(ctx, x, y, r)
    paint(ctx, "#D9A05B", 4)
    for dx, dy in ((-0.4, -0.3), (0.3, -0.1), (-0.1, 0.4), (0.35, 0.4), (-0.45, 0.25)):
        circle(ctx, x + dx * r, y + dy * r, r * 0.13)
        ctx.set_source_rgba(*hexc("#5A3214"))
        ctx.fill()


def chest(ctx, x, y, s=1.0, lid=0.0, glow=0.0, t=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if glow > 0:
        ctx.save()
        ctx.translate(0, -120)
        ctx.rotate(t * 0.8)
        for i in range(10):
            ctx.rotate(PI / 5)
            ctx.move_to(0, 0)
            ctx.line_to(320, -40)
            ctx.line_to(320, 40)
            ctx.close_path()
        ctx.set_source_rgba(1, 0.92, 0.5, 0.35 * glow)
        ctx.fill()
        ctx.restore()
    rrect(ctx, -110, -120, 220, 120, 14)
    paint(ctx, "#A0602E", 6)
    for bx in (-70, 70):
        ctx.rectangle(bx - 10, -120, 20, 120)
        paint(ctx, "#F2C230", 4)
    if lid > 0.3:  # treasure inside
        for cx, cy in ((-50, -128), (0, -140), (50, -128), (-20, -112), (30, -112)):
            cookie(ctx, cx, cy, 30)
    ctx.save()
    ctx.translate(-110, -120)
    ctx.rotate(-lid * 1.9)
    ctx.move_to(0, 0)
    ctx.line_to(0, -40)
    ctx.curve_to(0, -100, 220, -100, 220, -40)
    ctx.line_to(220, 0)
    ctx.close_path()
    paint(ctx, "#B86F36", 6)
    for bx in (40, 180):
        ctx.rectangle(bx - 10, -78, 20, 78)
        paint(ctx, "#F2C230", 4)
    ctx.restore()
    rrect(ctx, -16, -112, 32, 36, 6)
    paint(ctx, "#F2C230", 4)
    ctx.restore()


def snowball(ctx, x, y, r, rot=0.0):
    circle(ctx, x, y, r)
    paint(ctx, "#FFFFFF", 6)
    ctx.save()
    circle(ctx, x, y, r)
    ctx.clip()
    circle(ctx, x + r * 0.35, y + r * 0.4, r * 0.95)
    ctx.set_source_rgba(*hexc("#D6E8FA", 0.7))
    ctx.fill()
    for i in range(3):
        a = rot + i * 2.1
        circle(ctx, x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55, r * 0.08)
        ctx.set_source_rgba(*hexc("#C5DCF2"))
        ctx.fill()
    ctx.restore()


def snowman_base(ctx, x, y):
    snowball(ctx, x, y - 110, 115)
    snowball(ctx, x, y - 280, 82)
    for by in (-250, -290, -330):
        circle(ctx, x, y + by, 9)
        ctx.set_source_rgba(*OUT, 1)
        ctx.fill()
    line(ctx, [(x - 70, y - 300), (x - 160, y - 370), (x - 185, y - 395)], 9, "#7A4B2A")
    line(ctx, [(x + 70, y - 300), (x + 160, y - 380), (x + 180, y - 410)], 9, "#7A4B2A")


def rocket(ctx, x, y, s=1.0, rot=0.0, flame=0.0, t=0.0, window_fn=None):
    """y = bottom of the rocket body. window_fn(ctx, wx, wy, r) draws who's inside."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    if flame > 0:
        f = flame * (1 + 0.15 * math.sin(t * 50))
        for col, k in (("#FF7A1A", 1.0), ("#FFD54A", 0.65), ("#FFFFFF", 0.3)):
            ctx.move_to(-60 * k, 0)
            ctx.curve_to(-60 * k, 120 * f * k, 0, 220 * f * k, 0, 260 * f * k)
            ctx.curve_to(0, 220 * f * k, 60 * k, 120 * f * k, 60 * k, 0)
            ctx.close_path()
            ctx.set_source_rgba(*hexc(col, 0.95))
            ctx.fill()
    for side in (-1, 1):  # fins
        ctx.move_to(side * 85, -160)
        ctx.line_to(side * 170, -10)
        ctx.line_to(side * 170, 30)
        ctx.line_to(side * 80, 0)
        ctx.close_path()
        paint(ctx, "#E53935", 6)
    ctx.move_to(-95, 0)
    ctx.line_to(-95, -380)
    ctx.curve_to(-95, -520, 0, -620, 0, -640)
    ctx.curve_to(0, -620, 95, -520, 95, -380)
    ctx.line_to(95, 0)
    ctx.close_path()
    paint(ctx, "#F4F4F8", 7)
    ctx.move_to(-62, -530)
    ctx.curve_to(-30, -590, 0, -630, 0, -640)
    ctx.curve_to(0, -630, 30, -590, 62, -530)
    ctx.close_path()
    paint(ctx, "#E53935", 6)
    rrect(ctx, -95, -60, 190, 60, 4)
    paint(ctx, "#E53935", 6)
    wx, wy, wr = 0, -360, 82
    circle(ctx, wx, wy, wr + 16)
    paint(ctx, "#9AA5B8", 6)
    circle(ctx, wx, wy, wr)
    paint(ctx, "#8FD3FF", 5)
    if window_fn:
        ctx.save()
        circle(ctx, wx, wy, wr)
        ctx.clip()
        window_fn(ctx, wx, wy, wr)
        ctx.restore()
        circle(ctx, wx, wy, wr)
        ctx.set_source_rgba(*OUT, 1)
        ctx.set_line_width(5)
        ctx.stroke()
    ctx.move_to(wx - wr * 0.6, wy - wr * 0.3)
    ctx.arc(wx, wy, wr * 0.7, PI * 1.1, PI * 1.45)
    ctx.set_source_rgba(1, 1, 1, 0.6)
    ctx.set_line_width(8)
    ctx.stroke()
    text(ctx, "L&B", 0, -150, 56, color="#2F74D8", stroke=None)
    ctx.restore()


def smoke(ctx, x, y, t0, age, n=10, spread=260):
    if age < 0:
        return
    rnd = random.Random(int(t0 * 100))
    for i in range(n):
        dx = rnd.uniform(-1, 1) * spread * min(1, age * 1.5)
        dy = -rnd.uniform(0, 80) * age
        r = 40 + age * 70 * rnd.uniform(0.6, 1.2)
        a = clamp(1 - age / 2.0) * 0.85
        circle(ctx, x + dx, y + dy, r)
        ctx.set_source_rgba(0.93, 0.93, 0.97, a)
        ctx.fill()


def fish(ctx, x, y, s=1.0, rot=0.0, wiggle=0.0, color="#FF8A1F"):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.save()
    ctx.translate(-40, 0)
    ctx.rotate(wiggle)
    ctx.move_to(0, 0)
    ctx.line_to(-38, -26)
    ctx.line_to(-38, 26)
    ctx.close_path()
    paint(ctx, color, 4)
    ctx.restore()
    ellipse(ctx, 0, 0, 48, 28)
    paint(ctx, color, 5)
    circle(ctx, 22, -6, 8)
    paint(ctx, "#FFFFFF", 3)
    circle(ctx, 24, -6, 4)
    ctx.set_source_rgba(*OUT, 1)
    ctx.fill()
    ctx.arc(34, 8, 7, 0, PI)
    ctx.set_source_rgba(*OUT, 1)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()


def drops(ctx, x, y, age, n=10, power=420, seed=1, color="#7FD4FF"):
    if age < 0 or age > 1.4:
        return
    rnd = random.Random(seed)
    for i in range(n):
        vx = rnd.uniform(-1, 1) * power * 0.7
        vy = -rnd.uniform(0.5, 1) * power
        px = x + vx * age
        py = y + vy * age + 900 * age * age
        r = rnd.uniform(8, 16)
        ellipse(ctx, px, py, r * 0.8, r)
        paint(ctx, color, 3, a=clamp(1.4 - age))
