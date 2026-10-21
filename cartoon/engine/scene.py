"""Backgrounds, props, comic effects and on-screen text (hook, captions, tip card)."""
import math

import cairo

from .anim import EASE, clamp, smooth
from .character import OUTLINE, OW, ellipse, fill_stroke, hexrgb, limb, shade

W, H = 1080, 1920
GROUND = 1560
FONT = "Inter Black"
THEMES = {
    "cartoon": dict(font="Inter Black", text=(1, 1, 1), hi=(1, 0.86, 0.1), stroke=(0.16, 0.12, 0.19),
                    banner=(0.98, 0.3, 0.33), banner_text=(1, 1, 1), card=(1, 1, 1), card_text=(0.16, 0.12, 0.19),
                    head=(0.18, 0.72, 0.4), ok=(0.2, 0.75, 0.35), bad=(0.9, 0.18, 0.2), upper=True, size=68, cap_y=640, hook_y=300,
                    follow="FOLLOW FOR DAILY LIFE HACKS!"),
    "flat": dict(font="Inter Black", text=(1, 1, 1), hi=(1.0, 0.82, 0.4), stroke=(0.17, 0.16, 0.27),
                 banner=(0.94, 0.28, 0.44), banner_text=(1, 1, 1), card=(1, 1, 1), card_text=(0.17, 0.16, 0.27),
                 head=(0.02, 0.84, 0.63), ok=(0.02, 0.75, 0.55), bad=(0.94, 0.28, 0.44), upper=True, size=64,
                 cap_y=480, hook_y=190, follow="FOLLOW STRETCH & BRUNO!"),
    "euro": dict(font="DejaVu Serif", text=(0.98, 0.94, 0.84), hi=(1.0, 0.76, 0.34), stroke=(0.15, 0.09, 0.06),
                 banner=(0.48, 0.13, 0.11), banner_text=(0.98, 0.94, 0.84), card=(0.95, 0.9, 0.78),
                 card_text=(0.2, 0.13, 0.09), head=(0.22, 0.33, 0.47), ok=(0.3, 0.52, 0.3), bad=(0.68, 0.2, 0.15),
                 upper=False, size=64, cap_y=560, hook_y=250, follow="Follow for more Albert & Mimi"),
}
THEME = dict(THEMES["cartoon"])


def set_theme(name):
    THEME.clear()
    THEME.update(THEMES[name])


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def box(ctx, x, y, w, h, color, r=10, ow=OW):
    rrect(ctx, x, y, w, h, r)
    fill_stroke(ctx, hexrgb(color) if isinstance(color, str) else color, ow=ow)


# ------------------------------------------------------------------ backgrounds
def _wall_and_floor(ctx, wall, wall2, floor, floor2):
    g = cairo.LinearGradient(0, 0, 0, GROUND)
    g.add_color_stop_rgb(0, *hexrgb(wall2))
    g.add_color_stop_rgb(1, *hexrgb(wall))
    ctx.rectangle(-200, -200, W + 400, GROUND + 200)
    ctx.set_source(g)
    ctx.fill()
    ctx.rectangle(-200, GROUND - 40, W + 400, H - GROUND + 300)
    ctx.set_source_rgb(*hexrgb(floor))
    ctx.fill()
    # wooden planks
    ctx.set_source_rgb(*hexrgb(floor2))
    ctx.set_line_width(4)
    for i, y in enumerate(range(GROUND, H + 200, 70)):
        ctx.move_to(-200, y)
        ctx.line_to(W + 200, y)
        ctx.stroke()
        for x in range(-200 + (i % 3) * 140, W + 200, 420):
            ctx.move_to(x, y)
            ctx.line_to(x, y + 70)
            ctx.stroke()
    # skirting board
    ctx.rectangle(-200, GROUND - 70, W + 400, 34)
    fill_stroke(ctx, (0.98, 0.96, 0.92), ow=5)


def _window(ctx, x, y, w, h, curtain="#e86f6f"):
    box(ctx, x - 14, y - 14, w + 28, h + 28, "#fbf6ee", 8)
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgb(0, 0.45, 0.75, 0.98)
    g.add_color_stop_rgb(1, 0.78, 0.92, 1.0)
    ctx.rectangle(x, y, w, h)
    ctx.set_source(g)
    ctx.fill()
    for cx, cy, s in ((x + w * 0.3, y + h * 0.3, 1.0), (x + w * 0.75, y + h * 0.55, 0.7)):
        for dx, dy, r in ((0, 0, 34), (34, 8, 26), (-32, 10, 24), (10, 16, 28)):
            ctx.new_sub_path()
            ctx.arc(cx + dx * s, cy + dy * s, r * s, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
    ctx.rectangle(x, y, w, h)
    ctx.set_source_rgb(*OUTLINE)
    ctx.set_line_width(OW)
    ctx.stroke()
    ctx.move_to(x + w / 2, y)
    ctx.line_to(x + w / 2, y + h)
    ctx.move_to(x, y + h / 2)
    ctx.line_to(x + w, y + h / 2)
    ctx.set_line_width(10)
    ctx.set_source_rgb(0.98, 0.96, 0.92)
    ctx.stroke()
    c = hexrgb(curtain)
    for side in (0, 1):
        cx = x - 40 if side == 0 else x + w + 40
        d = 1 if side == 0 else -1
        ctx.move_to(cx - 30 * d, y - 40)
        ctx.line_to(cx + 70 * d, y - 40)
        ctx.curve_to(cx + 40 * d, y + h * 0.5, cx + 90 * d, y + h * 0.8, cx + 60 * d, y + h + 60)
        ctx.line_to(cx - 30 * d, y + h + 60)
        ctx.close_path()
        fill_stroke(ctx, c)
    box(ctx, x - 90, y - 52, w + 180, 18, "#8a5a3c", 9, ow=5)


def living_room(ctx):
    _wall_and_floor(ctx, "#f6dcb4", "#fbe9cd", "#c98c5a", "#b07648")
    # wallpaper dots
    ctx.set_source_rgba(1, 1, 1, 0.35)
    for j, y in enumerate(range(80, GROUND - 100, 110)):
        for x in range(-100 + (j % 2) * 60, W + 100, 120):
            ctx.new_sub_path()
            ctx.arc(x, y, 7, 0, 2 * math.pi)
    ctx.fill()
    _window(ctx, 600, 520, 330, 400)
    # picture frame
    box(ctx, 120, 620, 270, 200, "#8a5a3c", 8)
    ctx.rectangle(140, 640, 230, 160)
    ctx.set_source_rgb(0.62, 0.86, 0.75)
    ctx.fill()
    ctx.move_to(140, 800)
    ctx.line_to(220, 690)
    ctx.line_to(280, 760)
    ctx.line_to(320, 720)
    ctx.line_to(370, 800)
    ctx.close_path()
    ctx.set_source_rgb(0.3, 0.6, 0.45)
    ctx.fill()
    ctx.new_sub_path()
    ctx.arc(320, 680, 20, 0, 2 * math.pi)
    ctx.set_source_rgb(1, 0.85, 0.3)
    ctx.fill()
    # couch
    box(ctx, -60, 1200, 700, 210, "#6c7fd8", 50)
    box(ctx, -60, 1340, 700, 160, "#5a6cc4", 30)
    box(ctx, -90, 1290, 90, 230, "#5a6cc4", 40)
    box(ctx, 600, 1290, 90, 230, "#5a6cc4", 40)
    for x in (20, 330):
        box(ctx, x, 1250, 290, 120, "#7d8fe3", 36, ow=5)
    for x in (0, 560):
        ctx.rectangle(x + 20, 1500, 22, 60)
        fill_stroke(ctx, (0.35, 0.22, 0.15), ow=4)
    # floor lamp
    limb(ctx, [(1000, GROUND - 4), (1000, 1000)], 14, hexrgb("#444055"), ow=5)
    ctx.move_to(930, 1000)
    ctx.line_to(1070, 1000)
    ctx.line_to(1040, 880)
    ctx.line_to(960, 880)
    ctx.close_path()
    fill_stroke(ctx, hexrgb("#ffd66b"))
    box(ctx, 950, GROUND - 24, 100, 24, "#444055", 10, ow=5)
    # rug
    ellipse(ctx, 560, GROUND + 140, 470, 70)
    fill_stroke(ctx, hexrgb("#e2675f"), ow=5)
    ellipse(ctx, 560, GROUND + 140, 380, 46)
    ctx.set_source_rgba(1, 1, 1, 0.25)
    ctx.set_line_width(8)
    ctx.stroke()


def kitchen(ctx):
    _wall_and_floor(ctx, "#cfeee6", "#e6f7f2", "#d9a066", "#c08852")
    # backsplash tiles
    ctx.rectangle(-200, 820, W + 400, 380)
    ctx.set_source_rgb(0.98, 0.98, 0.96)
    ctx.fill()
    ctx.set_source_rgba(0.55, 0.7, 0.72, 0.6)
    ctx.set_line_width(3)
    for y in range(820, 1200, 60):
        ctx.move_to(-200, y)
        ctx.line_to(W + 200, y)
    for j, y in enumerate(range(820, 1200, 60)):
        for x in range(-200 + (j % 2) * 45, W + 200, 90):
            ctx.move_to(x, y)
            ctx.line_to(x, y + 60)
    ctx.stroke()
    # upper cabinets + window
    for x in (290, 860):
        box(ctx, x, 470, 260 if x == 290 else 330, 300, "#ffffff", 10)
        box(ctx, x + 18, 490, (260 if x == 290 else 330) / 2 - 27, 260, "#f1f1ee", 8, ow=4)
        box(ctx, x + (260 if x == 290 else 330) / 2 + 9, 490, (260 if x == 290 else 330) / 2 - 27, 260, "#f1f1ee", 8, ow=4)
    _window(ctx, 600, 520, 210, 230, curtain="#ffb547")
    # counter
    box(ctx, 250, 1240, 1100, 330, "#ffffff", 4)
    for x in range(270, 1250, 200):
        box(ctx, x, 1265, 180, 260, "#eef2f1", 8, ow=4)
        box(ctx, x + 70, 1290, 40, 12, "#99aaaa", 6, ow=3)
    box(ctx, 230, 1190, 1150, 54, "#5d6b78", 10)
    # sink
    ellipse(ctx, 490, 1206, 120, 16)
    fill_stroke(ctx, (0.68, 0.74, 0.78), ow=5)
    limb(ctx, [(470, 1192), (470, 1030), (500, 1000), (540, 1010), (548, 1060)], 22, (0.78, 0.82, 0.86))
    box(ctx, 430, 1180, 30, 14, "#b9c2c9", 5, ow=4)
    # stove + pan
    box(ctx, 820, 1176, 250, 18, "#33363d", 6, ow=4)
    ellipse(ctx, 945, 1176, 80, 10)
    ctx.set_source_rgb(0.95, 0.35, 0.15)
    ctx.fill()
    # fridge
    box(ctx, 10, 700, 230, 862, "#e9eef2", 22)
    box(ctx, 10, 700, 230, 300, "#f6f9fb", 22)
    limb(ctx, [(205, 780), (205, 920)], 12, (0.6, 0.65, 0.7), ow=4)
    limb(ctx, [(205, 1080), (205, 1260)], 12, (0.6, 0.65, 0.7), ow=4)
    for i, c in enumerate(("#ff6b6b", "#ffd93d", "#6bcb77")):
        ctx.new_sub_path()
        ctx.arc(60 + i * 45, 1100 + (i % 2) * 30, 14, 0, 2 * math.pi)
        fill_stroke(ctx, hexrgb(c), ow=4)


BACKGROUNDS = {"living_room": living_room, "kitchen": kitchen}


def make_background(name):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W + 400, H + 400)
    ctx = cairo.Context(surf)
    ctx.translate(200, 200)
    BACKGROUNDS[name](ctx)
    return surf


def vignette():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    g = cairo.RadialGradient(W / 2, H * 0.55, H * 0.3, W / 2, H * 0.55, H * 0.75)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.08, 0.02, 0.12, 0.35)
    ctx.set_source(g)
    ctx.paint()
    return surf


# ------------------------------------------------------------------ props
def phone(ctx, x, y, rot=0.0, scale=1.0, lit=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(scale, scale)
    box(ctx, -26, -46, 52, 92, "#25232d", 10, ow=5)
    rrect(ctx, -20, -38, 40, 74, 5)
    ctx.set_source_rgb(0.3 + 0.3 * lit, 0.55 + 0.3 * lit, 0.9)
    ctx.fill()
    ctx.restore()


def fishbowl(ctx, x, y, t, water_level=1.0, phone_in=0.0, fish_mood="happy"):
    # table
    box(ctx, x - 130, y + 80, 260, 26, "#9b6a45", 8)
    for dx in (-100, 84):
        ctx.rectangle(x + dx, y + 106, 18, GROUND - y - 106)
        fill_stroke(ctx, hexrgb("#7e5434"), ow=5)
    # bowl
    ctx.save()
    ctx.new_sub_path()
    ctx.arc(x, y, 92, math.radians(-60), math.radians(240))
    ctx.close_path()
    path = ctx.copy_path()
    ctx.set_source_rgba(0.85, 0.95, 1, 0.55)
    ctx.fill()
    ctx.append_path(path)
    ctx.clip()
    wl = y - 50 + 6 * math.sin(t * 3)
    ctx.rectangle(x - 100, wl, 200, 200)
    ctx.set_source_rgba(0.3, 0.65, 0.95, 0.7)
    ctx.fill()
    fx = x - 30 + 30 * math.sin(t * 1.3)
    fy = y + 20 + 6 * math.sin(t * 2.1)
    d = 1 if math.cos(t * 1.3) > 0 else -1
    ellipse(ctx, fx, fy, 30, 20)
    fill_stroke(ctx, hexrgb("#ff8a2a"), ow=4)
    ctx.move_to(fx - 26 * d, fy)
    ctx.line_to(fx - 48 * d, fy - 16)
    ctx.line_to(fx - 48 * d, fy + 16)
    ctx.close_path()
    fill_stroke(ctx, hexrgb("#ff8a2a"), ow=4)
    ellipse(ctx, fx + 14 * d, fy - 5, 6, 6)
    fill_stroke(ctx, (1, 1, 1), ow=2.5)
    if fish_mood == "angry":
        ctx.move_to(fx + 8 * d, fy - 16)
        ctx.line_to(fx + 22 * d, fy - 10)
        ctx.set_source_rgb(*OUTLINE)
        ctx.set_line_width(4)
        ctx.stroke()
    if phone_in > 0:
        phone(ctx, x + 30, y + 40 - 10 * phone_in, 0.5, 0.8, lit=0.0)
    ctx.restore()
    ctx.append_path(path)
    ctx.set_source_rgb(*OUTLINE)
    ctx.set_line_width(OW)
    ctx.stroke()
    ctx.move_to(x - 60, y - 40)
    ctx.curve_to(x - 75, y - 10, x - 75, y + 20, x - 60, y + 45)
    ctx.set_source_rgba(1, 1, 1, 0.7)
    ctx.set_line_width(8)
    ctx.stroke()


def rice_bag(ctx, x, y, rot=0.0, scale=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(scale, scale)
    ctx.move_to(-70, -90)
    ctx.line_to(70, -90)
    ctx.curve_to(90, 0, 90, 60, 70, 100)
    ctx.line_to(-70, 100)
    ctx.curve_to(-90, 60, -90, 0, -70, -90)
    ctx.close_path()
    fill_stroke(ctx, hexrgb("#f4ead2"))
    box(ctx, -55, -20, 110, 60, "#d94a3d", 10, ow=4)
    text(ctx, "RICE", 0, 22, 40, (1, 1, 1), stroke=0)
    ctx.restore()


def pan(ctx, x, y, rot=0.0, hot=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    limb(ctx, [(70, -8), (190, -16)], 18, hexrgb("#2b2b30"))
    ellipse(ctx, 0, 0, 90, 22)
    fill_stroke(ctx, hexrgb("#3a3b42"))
    ellipse(ctx, 0, -4, 74, 14)
    ctx.set_source_rgb(0.2, 0.2, 0.23)
    ctx.fill()
    ctx.restore()


def water_stream(ctx, x, y0, y1, t, on=1.0):
    if on <= 0.01:
        return
    w = 16 * on
    ctx.rectangle(x - w / 2, y0, w, (y1 - y0) * on)
    ctx.set_source_rgba(0.45, 0.75, 1, 0.85)
    ctx.fill()
    for k in range(4):
        yy = y0 + ((t * 600 + k * 40) % max(1, (y1 - y0)))
        ctx.rectangle(x - w / 4, yy, 3, 18)
        ctx.set_source_rgba(1, 1, 1, 0.8)
        ctx.fill()


# ------------------------------------------------------------------ effects
def starburst(ctx, x, y, r, color, spikes=12, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    for i in range(spikes * 2):
        a = math.pi * i / spikes
        rr = r if i % 2 == 0 else r * 0.68
        (ctx.move_to if i == 0 else ctx.line_to)(math.cos(a) * rr, math.sin(a) * rr)
    ctx.close_path()
    fill_stroke(ctx, color, ow=7)
    ctx.restore()


def burst(ctx, x, y, u, word, color="#ffdd33", size=1.0, rot=-0.12):
    """Comic 'OUCH!' bubble. u is 0..1 life progress."""
    sc = EASE["back"](clamp(u / 0.25)) * (1 - smooth((u - 0.85) / 0.15)) * size
    if sc <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    starburst(ctx, 0, 0, 150, hexrgb(color), 13, rot + u * 0.2)
    ctx.rotate(rot)
    text(ctx, word, 0, 26, 74, (0.85, 0.1, 0.15), stroke=10)
    ctx.restore()


def sweat(ctx, x, y, t):
    for k, (dx, dy) in enumerate(((0, 0), (40, 30))):
        p = (t * 1.4 + k * 0.5) % 1.0
        yy = y + dy + p * 40
        ctx.save()
        ctx.translate(x + dx, yy)
        ctx.move_to(0, -22)
        ctx.curve_to(12, -4, 14, 10, 0, 14)
        ctx.curve_to(-14, 10, -12, -4, 0, -22)
        ctx.close_path()
        ctx.set_source_rgba(0.55, 0.85, 1, 1 - p)
        ctx.fill_preserve()
        ctx.set_source_rgba(*OUTLINE, 1 - p)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.restore()


def speed_lines(ctx, x, y, t, d=1):
    ctx.set_source_rgba(*OUTLINE, 0.55)
    ctx.set_line_width(6)
    ctx.set_line_cap(1)
    for k in range(5):
        yy = y - 200 + k * 90 + 10 * math.sin(t * 20 + k)
        L = 80 + 60 * ((k * 37) % 3)
        ctx.move_to(x - d * 40, yy)
        ctx.line_to(x - d * (40 + L), yy)
        ctx.stroke()


def steam(ctx, x, y, t):
    for k in range(3):
        p = (t * 0.8 + k / 3) % 1.0
        ctx.move_to(x + k * 30 - 30, y)
        for s in range(8):
            yy = y - s * 18 - p * 60
            ctx.line_to(x + k * 30 - 30 + 12 * math.sin(s * 0.9 + t * 4 + k), yy)
        ctx.set_source_rgba(1, 1, 1, 0.75 * (1 - p))
        ctx.set_line_width(9)
        ctx.set_line_cap(1)
        ctx.stroke()


def splash(ctx, x, y, u):
    if u <= 0 or u >= 1:
        return
    for k in range(10):
        a = math.pi * (1.1 + 0.8 * k / 9)
        v = 380 + 90 * ((k * 7) % 3)
        px = x + math.cos(a) * v * u
        py = y + math.sin(a) * v * u + 900 * u * u
        ellipse(ctx, px, py, 11 * (1 - u * 0.5), 14 * (1 - u * 0.5))
        ctx.set_source_rgba(0.4, 0.7, 1, 1 - u)
        ctx.fill()


def sparkles(ctx, x, y, t, r=110):
    for k in range(5):
        a = k * 2 * math.pi / 5 + t * 1.5
        s = 0.6 + 0.4 * math.sin(t * 8 + k)
        px, py = x + math.cos(a) * r, y + math.sin(a) * r * 0.6
        ctx.save()
        ctx.translate(px, py)
        ctx.scale(s, s)
        ctx.move_to(0, -24)
        for i in range(1, 8):
            rr = 24 if i % 2 == 0 else 7
            ang = -math.pi / 2 + i * math.pi / 4
            ctx.line_to(math.cos(ang) * rr, math.sin(ang) * rr)
        ctx.close_path()
        ctx.set_source_rgb(1, 0.88, 0.25)
        ctx.fill_preserve()
        ctx.set_source_rgb(*OUTLINE)
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.restore()


def stamp(ctx, x, y, u, good):
    """Big ✓ or ✗ stamp."""
    sc = EASE["back"](clamp(u / 0.2)) * (1 - smooth((u - 0.85) / 0.15))
    if sc <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    c = (0.2, 0.75, 0.35) if good else (0.9, 0.18, 0.2)
    ctx.arc(0, 0, 90, 0, 2 * math.pi)
    fill_stroke(ctx, c, ow=8)
    ctx.set_source_rgb(1, 1, 1)
    ctx.set_line_width(24)
    ctx.set_line_cap(1)
    if good:
        ctx.move_to(-42, 2)
        ctx.line_to(-12, 34)
        ctx.line_to(46, -32)
    else:
        ctx.move_to(-36, -36)
        ctx.line_to(36, 36)
        ctx.move_to(36, -36)
        ctx.line_to(-36, 36)
    ctx.stroke()
    ctx.restore()


# ------------------------------------------------------------------ text / UI
def set_font(ctx, size):
    ctx.select_font_face(THEME["font"], cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)


def text(ctx, s, x, y, size, color, stroke=12, align="center", stroke_color=OUTLINE):
    set_font(ctx, size)
    ext = ctx.text_extents(s)
    if align == "center":
        x -= ext.x_advance / 2
    ctx.move_to(x, y)
    ctx.text_path(s)
    if stroke:
        ctx.set_source_rgb(*stroke_color)
        ctx.set_line_width(stroke)
        ctx.set_line_join(1)
        ctx.stroke_preserve()
    ctx.set_source_rgb(*color)
    ctx.fill()
    return ext.x_advance


def wrap_words(ctx, words, size, maxw):
    set_font(ctx, size)
    space = size * 0.3
    lines, cur, w = [], [], 0
    for i, wd in enumerate(words):
        ww = ctx.text_extents(wd).x_advance
        if cur and w + space + ww > maxw:
            lines.append((cur, w))
            cur, w = [], 0
        w = w + (space if cur else 0) + ww
        cur.append((i, wd, ww))
    if cur:
        lines.append((cur, w))
    return lines, space


def captions(ctx, line, t, y=640):
    """Word-by-word karaoke captions, paged two lines at a time."""
    words = [w[2].upper() if THEME["upper"] else w[2] for w in line["words"]]
    if not words:
        return
    size = THEME["size"]
    lines, space = wrap_words(ctx, words, size, 880)
    cur = 0
    for i, (s, e, _) in enumerate(line["words"]):
        if t >= line["start"] + s:
            cur = i
    pages = [lines[i:i + 2] for i in range(0, len(lines), 2)]
    page_i = next(pi for pi, pg in enumerate(pages) if any(cur <= w[0] for ws, _ in pg for w in ws) or pi == len(pages) - 1)
    page = pages[page_i]
    first_word = page[0][0][0][0]
    page_start = line["start"] + (line["words"][first_word][0] if page_i else 0)
    k = clamp((t - page_start) / 0.16)
    pop = 0.8 + 0.2 * EASE["back"](k)
    lh = size * 1.18
    total = lh * len(page)
    ctx.save()
    ctx.translate(W / 2, y)
    ctx.scale(pop, pop)
    tag = line["who_label"]
    set_font(ctx, 34)
    tw = ctx.text_extents(tag).x_advance
    box(ctx, -tw / 2 - 20, -total / 2 - 70, tw + 40, 52, line["color"], 26, ow=5)
    text(ctx, tag, 0, -total / 2 - 32, 34, THEME["banner_text"], stroke=0)
    for li, (ws, lw) in enumerate(page):
        x = -lw / 2
        yy = -total / 2 + lh * (li + 0.8)
        for (i, wd, ww) in ws:
            active = i == cur
            col = THEME["hi"] if active else THEME["text"]
            ctx.save()
            if active:
                ctx.translate(x + ww / 2, yy - size * 0.35)
                ctx.scale(1.12, 1.12)
                ctx.translate(-(x + ww / 2), -(yy - size * 0.35))
            text(ctx, wd, x, yy, size, col, stroke=16, align="left", stroke_color=THEME["stroke"])
            ctx.restore()
            x += ww + space
    ctx.restore()


def hook_title(ctx, t, lines, t_end):
    """Big attention-grabbing hook for the first seconds, then a small banner."""
    if t < t_end:
        for i, (s, color) in enumerate(lines):
            u = clamp((t - 0.05 - i * 0.22) / 0.35)
            if u <= 0:
                continue
            sc = EASE["back"](u)
            wob = math.sin(t * 9 + i) * 0.03
            ctx.save()
            ctx.translate(W / 2, THEME["hook_y"] + i * 115)
            ctx.rotate(-0.04 + wob)
            set_font(ctx, 92 if i == 0 else 80)
            fit = min(1.0, 960 / max(1.0, ctx.text_extents(s).x_advance + 40))  # never run off screen
            ctx.scale(sc * fit, sc * fit)
            text(ctx, s, 0, 0, 92 if i == 0 else 80, hexrgb(color), stroke=20, stroke_color=THEME["stroke"])
            ctx.restore()
    else:
        u = clamp((t - t_end) / 0.3)
        s = " ".join(x[0] for x in lines)
        set_font(ctx, 40)
        tw = ctx.text_extents(s).x_advance
        ctx.save()
        ctx.translate(W / 2, 230)
        ctx.scale(EASE["back"](u), EASE["back"](u))
        box(ctx, -tw / 2 - 26, -44, tw + 52, 66, THEME["banner"], 33, ow=6)
        text(ctx, s, 0, 2, 40, THEME["banner_text"], stroke=0)
        ctx.restore()


def tip_card(ctx, t, tip):
    u = clamp((t - tip["t0"]) / 0.4)
    if u <= 0:
        return
    sc = EASE["back"](u)
    cw = 940
    rows = tip["items"]
    ch = 120 + 86 * len(rows)
    ctx.save()
    ctx.translate(W / 2, 330 + ch / 2)
    ctx.scale(sc, sc)
    ctx.translate(-cw / 2, -ch / 2)
    rrect(ctx, 10, 14, cw, ch, 36)
    ctx.set_source_rgba(0, 0, 0, 0.25)
    ctx.fill()
    box(ctx, 0, 0, cw, ch, THEME["card"], 36, ow=8)
    box(ctx, 0, 0, cw, 96, tip.get("color", THEME["head"]), 36, ow=8)
    text(ctx, tip["title"], cw / 2, 68, 56, THEME["banner_text"], stroke=0)
    for i, (ok, s) in enumerate(rows):
        ru = clamp((t - tip["t0"] - 0.3 - i * 0.25) / 0.3)
        if ru <= 0:
            continue
        y = 150 + i * 86
        ctx.save()
        ctx.translate(70, y)
        ctx.scale(EASE["back"](ru), EASE["back"](ru))
        ctx.arc(0, 0, 30, 0, 2 * math.pi)
        fill_stroke(ctx, THEME["ok"] if ok else THEME["bad"], ow=5)
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_line_width(9)
        ctx.set_line_cap(1)
        if ok:
            ctx.move_to(-13, 1)
            ctx.line_to(-3, 12)
            ctx.line_to(15, -11)
        else:
            ctx.move_to(-11, -11)
            ctx.line_to(11, 11)
            ctx.move_to(11, -11)
            ctx.line_to(-11, 11)
        ctx.stroke()
        ctx.restore()
        text(ctx, s, 125, y + 17, 46, THEME["card_text"], stroke=0, align="left")
    ctx.restore()


def follow_card(ctx, t, t0):
    u = clamp((t - t0) / 0.35)
    if u <= 0:
        return
    sc = EASE["back"](u)
    ctx.save()
    ctx.translate(W / 2, 1450)
    ctx.scale(sc, sc)
    s = THEME["follow"]
    set_font(ctx, 46)
    tw = ctx.text_extents(s).x_advance
    box(ctx, -tw / 2 - 30, -50, tw + 60, 80, THEME["banner"], 40, ow=7)
    text(ctx, s, 0, 6, 46, THEME["banner_text"], stroke=0)
    ctx.restore()
