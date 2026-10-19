"""'Paris winter' look: painted backgrounds with watercolour texture, snow, warm lamp light,
paper + film grain, and a judgemental black cat.  Drawn with the same hand-drawn ink as the rig."""
import math

import cairo
import numpy as np
from scipy import ndimage

from . import scene
from .anim import clamp, smooth
from .character import OUTLINE, OW, STYLE, ellipse, fill_stroke, hexrgb, ink, limb, shade

W, H, GROUND = scene.W, scene.H, scene.GROUND
rgb = hexrgb


def _poly(ctx, pts, color, ow=OW):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    fill_stroke(ctx, rgb(color) if isinstance(color, str) else color, ow=ow)


def _rect(ctx, x, y, w, h, color, ow=OW):
    _poly(ctx, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], color, ow)


def _vgrad(ctx, x, y, w, h, top, bottom):
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgb(0, *rgb(top))
    g.add_color_stop_rgb(1, *rgb(bottom))
    ctx.rectangle(x, y, w, h)
    ctx.set_source(g)
    ctx.fill()


# ------------------------------------------------------------------ outside: Paris rooftops
def rooftops(ctx, x0, y0, w, h, seed=3):
    """Snowy zinc rooftops, chimneys, dormers and a far bell tower, inside (x0, y0, w, h)."""
    rng = np.random.default_rng(seed)
    _vgrad(ctx, x0, y0, w, h, "#2f3f5f", "#8f99ad")
    # far bell tower + dome
    tx = x0 + w * 0.72
    _poly(ctx, [(tx - 40, y0 + h * 0.62), (tx - 40, y0 + h * 0.2), (tx, y0 + h * 0.08), (tx + 40, y0 + h * 0.2),
                (tx + 40, y0 + h * 0.62)], "#a9b3c4", ow=3)
    for k in range(3):
        _rect(ctx, tx - 14, y0 + h * (0.24 + k * 0.11), 28, h * 0.06, "#8592a8", ow=2)
    ellipse(ctx, x0 + w * 0.2, y0 + h * 0.52, 70, 52)
    fill_stroke(ctx, rgb("#9ea9bc"), ow=3)
    # roof rows (back to front)
    for row in range(3):
        base = y0 + h * (0.5 + row * 0.18)
        col = shade(rgb("#7d8aa3"), 0.8 + row * 0.08)
        x = x0 - 40
        while x < x0 + w:
            rw = rng.uniform(110, 190)
            top = base - rng.uniform(40, 90)
            _poly(ctx, [(x, base + 120), (x, top + 30), (x + 30, top), (x + rw - 30, top), (x + rw, top + 30),
                        (x + rw, base + 120)], col, ow=3)
            ctx.rectangle(x + 4, top - 4, rw - 8, 14)
            ctx.set_source_rgb(0.93, 0.94, 0.97)
            ctx.fill()
            if rng.random() < 0.7:  # chimney with pots
                cx = x + rng.uniform(20, rw - 50)
                _rect(ctx, cx, top - 60, 34, 64, "#9a5b45", ow=3)
                _rect(ctx, cx - 4, top - 66, 42, 10, "#ecedf1", ow=2)
            if rng.random() < 0.6:  # lit dormer window
                dx = x + rng.uniform(25, rw - 55)
                _poly(ctx, [(dx, top + 70), (dx, top + 40), (dx + 15, top + 26), (dx + 30, top + 40), (dx + 30, top + 70)],
                      "#e6c27a" if rng.random() < 0.6 else "#4d5a75", ow=2.5)
            x += rw + rng.uniform(-10, 20)


# ------------------------------------------------------------------ backgrounds
def paris_apartment(ctx):
    # wallpaper: faded olive with stripes and little motifs
    _vgrad(ctx, -200, -200, W + 400, 1400, "#4f5a46", "#7b7a5c")
    ctx.set_source_rgba(1, 0.95, 0.75, 0.06)
    for x in range(-200, W + 200, 64):
        ctx.rectangle(x, -200, 22, 1400)
    ctx.fill()
    ctx.set_source_rgba(0.2, 0.18, 0.1, 0.12)
    for j, y in enumerate(range(-150, 1180, 90)):
        for x in range(-180 + (j % 2) * 32, W + 200, 64):
            ctx.new_sub_path()
            ctx.arc(x + 11, y, 6, 0, 2 * math.pi)
    ctx.fill()
    # wainscot
    _vgrad(ctx, -200, 1180, W + 400, 400, "#6b4a33", "#4a3222")
    for x in range(-160, W + 200, 230):
        ctx.rectangle(x, 1220, 190, 300)
        ink(ctx, rgb("#3a2618"), 4)
    _rect(ctx, -200, 1166, W + 400, 26, "#7c5a3e", ow=4)
    # floor
    _vgrad(ctx, -200, GROUND - 30, W + 400, 500, "#5b3c27", "#3e281a")
    ctx.set_source_rgba(0.1, 0.05, 0.02, 0.35)
    ctx.set_line_width(3)
    for i, y in enumerate(range(GROUND - 30, H + 200, 46)):
        ctx.move_to(-200, y)
        ctx.line_to(W + 200, y)
        for x in range(-200 + (i % 3) * 120, W + 200, 360):
            ctx.move_to(x, y)
            ctx.line_to(x, y + 46)
    ctx.stroke()
    ellipse(ctx, 560, GROUND + 150, 520, 80)
    fill_stroke(ctx, rgb("#7e2f2a"), ow=4)
    ellipse(ctx, 560, GROUND + 150, 430, 56)
    ink(ctx, rgb("#c99a5b"), 6)
    # window with rooftops
    wx, wy, ww, wh = 560, 400, 440, 640
    _rect(ctx, wx - 30, wy - 30, ww + 60, wh + 70, "#d9cdb3")
    ctx.save()
    ctx.rectangle(wx, wy, ww, wh)
    ctx.clip()
    rooftops(ctx, wx, wy, ww, wh)
    ctx.restore()
    for k in range(3):  # muntins
        _rect(ctx, wx + ww / 2 - 8, wy, 16, wh, "#d9cdb3", ow=3)
        _rect(ctx, wx, wy + wh * (k + 1) / 4 - 7, ww, 14, "#d9cdb3", ow=3)
    ctx.rectangle(wx, wy, ww, wh)
    ink(ctx, OUTLINE, 6)
    # snowy outer ledge + inner sill
    _poly(ctx, [(wx - 10, wy + wh - 10), (wx + ww + 10, wy + wh - 10), (wx + ww + 10, wy + wh + 6),
                (wx - 10, wy + wh + 6)], "#f1f2f5", ow=3)
    _rect(ctx, wx - 50, wy + wh + 30, ww + 100, 28, "#b9a98a")
    # velvet curtains
    for side in (0, 1):
        cx = wx - 60 if side == 0 else wx + ww + 60
        d = 1 if side == 0 else -1
        _poly(ctx, [(cx - 50 * d, wy - 70), (cx + 70 * d, wy - 70), (cx + 40 * d, wy + 260), (cx + 76 * d, wy + 330),
                    (cx + 30 * d, wy + wh + 120), (cx - 50 * d, wy + wh + 120)], "#7a2626")
        for k in range(3):
            ctx.move_to(cx - 30 * d + k * 22 * d, wy - 50)
            ctx.curve_to(cx - 20 * d + k * 20 * d, wy + 200, cx - 40 * d + k * 25 * d, wy + 400, cx - 30 * d + k * 22 * d, wy + wh + 110)
            ink(ctx, rgb("#4f1414"), 3)
    _rect(ctx, wx - 140, wy - 84, ww + 280, 18, "#8a6a3a", ow=4)
    # hanging lamp
    limb(ctx, [(330, -200), (330, 380)], 5, rgb("#2a2420"), ow=1.5)
    _poly(ctx, [(270, 380), (390, 380), (450, 470), (210, 470)], "#3f5b48")
    ellipse(ctx, 330, 472, 120, 14)
    fill_stroke(ctx, rgb("#2f4637"), ow=4)
    ellipse(ctx, 330, 482, 26, 20)
    fill_stroke(ctx, rgb("#fff1b8"), ow=3)
    # picture frames
    _rect(ctx, 60, 560, 210, 170, "#8a6a3a")
    _vgrad(ctx, 78, 578, 174, 134, "#b9a77f", "#7f8a6a")
    _poly(ctx, [(78, 712), (130, 640), (170, 690), (210, 650), (252, 712)], "#5d6b4c", ow=2)
    ellipse(ctx, 175, 870, 70, 90)
    fill_stroke(ctx, rgb("#8a6a3a"))
    ellipse(ctx, 175, 870, 54, 72)
    fill_stroke(ctx, rgb("#c9b48d"), ow=3)
    ellipse(ctx, 175, 850, 22, 26)
    ctx.set_source_rgb(0.42, 0.33, 0.25)
    ctx.fill()
    ellipse(ctx, 175, 912, 36, 26)
    ctx.fill()
    # cast iron stove with pipe and kettle
    limb(ctx, [(120, -200), (120, 980)], 46, rgb("#2b2b2c"), ow=4)
    _rect(ctx, 20, 980, 200, 270, "#2f3330")
    _rect(ctx, 50, 1060, 140, 110, "#1d1f1e", ow=4)
    ctx.rectangle(62, 1072, 116, 86)
    ctx.set_source_rgba(1, 0.45, 0.1, 0.55)
    ctx.fill()
    _rect(ctx, 10, 1250, 220, 20, "#2b2b2c", ow=4)
    for lx in (30, 190):
        _rect(ctx, lx, 1270, 20, GROUND - 1270, "#2b2b2c", ow=4)
    ellipse(ctx, 120, 958, 50, 30)
    fill_stroke(ctx, rgb("#9aa6a0"))
    limb(ctx, [(160, 950), (196, 924)], 10, rgb("#9aa6a0"), ow=3)
    # table with cloth and the old radio
    _rect(ctx, 650, 1290, 420, 26, "#6b4a33")
    for lx in (670, 1030):
        _rect(ctx, lx, 1316, 26, GROUND - 1316, "#5b3c27", ow=4)
    _poly(ctx, [(640, 1284), (1080, 1284), (1090, 1350), (630, 1350)], "#e7ddc6", ow=4)
    ctx.set_source_rgba(0.6, 0.2, 0.2, 0.35)
    for x in range(650, 1080, 40):
        ctx.rectangle(x, 1286, 18, 62)
    ctx.fill()
    scene.rrect(ctx, 880, 1170, 170, 116, 24)
    fill_stroke(ctx, rgb("#b5562c"))
    scene.rrect(ctx, 896, 1186, 100, 70, 12)
    fill_stroke(ctx, rgb("#e6d6a8"), ow=3)
    for k in range(4):
        ctx.move_to(904, 1198 + k * 15)
        ctx.line_to(988, 1198 + k * 15)
    ink(ctx, rgb("#7a5a3a"), 2)
    for kx in (1018, 1018):
        ellipse(ctx, kx, 1210, 12, 12)
        fill_stroke(ctx, rgb("#e6d6a8"), ow=3)
    ellipse(ctx, 1018, 1250, 12, 12)
    fill_stroke(ctx, rgb("#e6d6a8"), ow=3)
    # dark corners (painted light falloff)
    g = cairo.RadialGradient(560, 900, 300, 560, 900, 1300)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.08, 0.04, 0.02, 0.45)
    ctx.rectangle(-200, -200, W + 400, H + 400)
    ctx.set_source(g)
    ctx.fill()


def paris_street(ctx):
    _vgrad(ctx, -200, -200, W + 400, 1300, "#1f2b48", "#6f7a96")
    rooftops(ctx, -200, 380, W + 400, 700, seed=9)
    # foreground Haussmann facades
    for bx, bw_, lit in ((-200, 700, 0.5), (500, 780, 0.4)):
        _rect(ctx, bx, 200, bw_, GROUND, "#cdbf9f")
        ctx.set_source_rgba(0.35, 0.28, 0.2, 0.25)
        ctx.set_line_width(2.5)
        for y in range(240, 1100, 46):
            ctx.move_to(bx, y)
            ctx.line_to(bx + bw_, y)
        ctx.stroke()
        _poly(ctx, [(bx - 10, 210), (bx + 30, 120), (bx + bw_ - 30, 120), (bx + bw_ + 10, 210)], "#5c6577")
        ctx.rectangle(bx + 20, 112, bw_ - 40, 18)
        ctx.set_source_rgb(0.94, 0.95, 0.98)
        ctx.fill()
        rng = np.random.default_rng(int(bx) + 500)
        for fy in (290, 560, 830):
            for fx in range(bx + 50, bx + bw_ - 80, 170):
                warm = rng.random() < lit
                _rect(ctx, fx, fy, 86, 170, "#e8bf6a" if warm else "#3c4862", ow=4)
                ctx.move_to(fx + 43, fy)
                ctx.line_to(fx + 43, fy + 170)
                ctx.move_to(fx, fy + 70)
                ctx.line_to(fx + 86, fy + 70)
                ink(ctx, OUTLINE, 3)
                # wrought-iron balcony
                ctx.rectangle(fx - 14, fy + 150, 114, 40)
                for k in range(8):
                    ctx.move_to(fx - 10 + k * 15, fy + 152)
                    ctx.line_to(fx - 10 + k * 15, fy + 190)
                ink(ctx, rgb("#1d1a1a"), 3)
                ctx.rectangle(fx - 16, fy + 146, 118, 8)
                ctx.set_source_rgb(0.95, 0.96, 0.98)
                ctx.fill()
    # cafe with striped awning on the left
    _rect(ctx, -150, 1120, 560, 330, "#2e4a3c")
    _rect(ctx, -120, 1160, 480, 230, "#e7b866", ow=5)
    for k in range(4):
        ctx.move_to(-120 + k * 120, 1160)
        ctx.line_to(-120 + k * 120, 1390)
    ink(ctx, rgb("#2e4a3c"), 8)
    for k in range(9):
        _poly(ctx, [(-160 + k * 66, 1040), (-94 + k * 66, 1040), (-84 + k * 66, 1120), (-150 + k * 66, 1120)],
              "#9c2f2a" if k % 2 == 0 else "#efe6d3", ow=3)
    ctx.move_to(-160, 1040)
    ctx.line_to(440, 1040)
    ink(ctx, OUTLINE, 6)
    for k in range(9):
        ctx.rectangle(-160 + k * 66, 1036, 66, 10)
    ctx.set_source_rgb(0.95, 0.96, 0.98)
    ctx.fill()
    scene.text(ctx, "CAFE", 145, 1100, 44, (0.98, 0.94, 0.84), stroke=6, stroke_color=(0.3, 0.1, 0.08))
    # green door on the right
    _rect(ctx, 800, 1180, 170, 290, "#2f5a4a")
    ellipse(ctx, 940, 1330, 8, 8)
    fill_stroke(ctx, rgb("#c9a44a"), ow=2)
    # snowy sidewalk + curb + road
    _vgrad(ctx, -200, 1440, W + 400, 300, "#d9dfea", "#eef1f6")
    _rect(ctx, -200, 1730, W + 400, 30, "#a9b2c2", ow=4)
    _vgrad(ctx, -200, 1760, W + 400, 400, "#4b5160", "#2d313b")
    for x in range(-200, W + 200, 140):
        ellipse(ctx, x + 40, 1480 + (x % 3) * 30, 50, 8)
        ctx.set_source_rgba(0.75, 0.8, 0.9, 0.5)
        ctx.fill()
    # ice patch (glossy)
    ellipse(ctx, 640, GROUND + 18, 170, 26)
    fill_stroke(ctx, rgb("#a8d4ef"), ow=4)
    for dx in (-90, -20, 60):
        ctx.move_to(640 + dx, GROUND + 10)
        ctx.line_to(640 + dx + 50, GROUND + 4)
    ink(ctx, (1, 1, 1), 5)
    # cast iron street lamp
    limb(ctx, [(1010, 1700), (1010, 820)], 22, rgb("#1f2a24"), ow=4)
    _poly(ctx, [(960, 820), (1060, 820), (1046, 700), (974, 700)], "#f3d98c")
    _poly(ctx, [(950, 700), (1070, 700), (1010, 650)], "#1f2a24")
    # stone bench for the cat
    _rect(ctx, 60, 1380, 240, 40, "#9c968a")
    _rect(ctx, 80, 1420, 30, 120, "#8a8478", ow=4)
    _rect(ctx, 250, 1420, 30, 120, "#8a8478", ow=4)
    ctx.rectangle(56, 1372, 248, 12)
    ctx.set_source_rgb(0.95, 0.96, 0.98)
    ctx.fill()


scene.BACKGROUNDS.update(paris_apartment=paris_apartment, paris_street=paris_street)


# ------------------------------------------------------------------ paint texture
def _np_view(surf):
    surf.flush()
    return np.ndarray((surf.get_height(), surf.get_width(), 4), np.uint8, surf.get_data())


def watercolorize(surf, seed=5):
    """Watercolour look on a painted background: pigment blotches, wet edges, paper grain, muted grade."""
    a = _np_view(surf)
    img = a[:, :, :3].astype(np.float32) / 255.0  # BGR
    h, w = img.shape[:2]
    rng = np.random.default_rng(seed)
    blot = ndimage.zoom(ndimage.gaussian_filter(rng.standard_normal((h // 8, w // 8)), 3), 8, order=1)[:h, :w]
    blot = np.pad(blot, ((0, h - blot.shape[0]), (0, w - blot.shape[1])), mode="edge")
    blot /= np.abs(blot).max() + 1e-6
    lum = img.mean(2)
    edge = np.abs(lum - ndimage.gaussian_filter(lum, 4))
    edge = np.clip(edge * 6, 0, 1)
    grain = ndimage.gaussian_filter(rng.standard_normal((h, w)), 0.9)
    grain /= np.abs(grain).max() + 1e-6
    out = img * (1 + 0.09 * blot[..., None]) * (1 - 0.35 * edge[..., None]) + 0.025 * grain[..., None]
    gray = out.mean(2, keepdims=True)
    out = gray + (out - gray) * 0.82  # mute colours a little
    out[..., 2] *= 1.03  # warm (R in BGR)
    out[..., 0] *= 0.97
    a[:, :, :3] = np.clip(out * 255, 0, 255).astype(np.uint8)
    surf.mark_dirty()
    return surf


def paper_texture(seed=11):
    """Static paper/pigment texture multiplied over the whole frame so characters sit 'on paper'."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    a = _np_view(surf)
    rng = np.random.default_rng(seed)
    big = ndimage.zoom(ndimage.gaussian_filter(rng.standard_normal((H // 10, W // 10)), 2.5), 10, order=1)
    big = np.pad(big, ((0, max(0, H - big.shape[0])), (0, max(0, W - big.shape[1]))), mode="edge")[:H, :W]
    fine = ndimage.gaussian_filter(rng.standard_normal((H, W)), 0.7)
    v = 0.93 + 0.05 * big / (np.abs(big).max() + 1e-6) + 0.03 * fine / (np.abs(fine).max() + 1e-6)
    v = np.clip(v, 0, 1)
    a[:, :, 0] = (v * 0.94 * 255).astype(np.uint8)
    a[:, :, 1] = (v * 0.98 * 255).astype(np.uint8)
    a[:, :, 2] = (v * 255).astype(np.uint8)
    a[:, :, 3] = 255
    surf.mark_dirty()
    return surf


def grain_frames(n=6, seed=21):
    out = []
    rng = np.random.default_rng(seed)
    for _ in range(n):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        a = _np_view(surf)
        g = np.clip(128 + rng.standard_normal((H, W)) * 40, 0, 255).astype(np.uint8)
        a[:, :, 0] = a[:, :, 1] = a[:, :, 2] = g
        a[:, :, 3] = 255
        surf.mark_dirty()
        out.append(surf)
    return out


class Post:
    """Per-frame finishing pass for the euro look."""

    def __init__(self):
        self.paper = paper_texture()
        self.grain = grain_frames()

    def apply(self, ctx, fi):
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_MULTIPLY)
        ctx.set_source_surface(self.paper, 0, 0)
        ctx.paint_with_alpha(0.85)
        ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
        ctx.set_source_rgba(0.98, 0.78, 0.52, 0.22)  # warm grade
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVERLAY)
        ctx.set_source_surface(self.grain[(fi // 2) % len(self.grain)], 0, 0)
        ctx.paint_with_alpha(0.09)
        ctx.restore()


# ------------------------------------------------------------------ atmosphere
def _hash(i, k):
    return (math.sin(i * 127.1 + k * 311.7) * 43758.5453) % 1.0


def snow(ctx, t, rect=(-120, -120, W + 240, H + 240), n=140, size=1.0, speed=1.0, seed=0, alpha=0.9):
    x0, y0, w, h = rect
    ctx.save()
    ctx.rectangle(x0, y0, w, h)
    ctx.clip()
    ctx.set_source_rgba(1, 1, 1, alpha)
    for i in range(n):
        r = (2.0 + 4.5 * _hash(i, seed + 1)) * size
        v = (40 + 90 * _hash(i, seed + 2)) * speed * (r / 4)
        y = y0 + ((_hash(i, seed + 3) * h + t * v) % h)
        x = x0 + _hash(i, seed + 4) * w + 18 * math.sin(t * (0.6 + _hash(i, seed + 5)) + i)
        ctx.new_sub_path()
        ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def glow(ctx, x, y, r, color=(1.0, 0.82, 0.45), strength=0.55, t=0.0):
    f = 1 + 0.03 * math.sin(t * 13) + 0.02 * math.sin(t * 7.3)
    g = cairo.RadialGradient(x, y, 0, x, y, r * f)
    g.add_color_stop_rgba(0, *color, strength)
    g.add_color_stop_rgba(0.35, *color, strength * 0.4)
    g.add_color_stop_rgba(1, *color, 0)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_SCREEN)
    ctx.arc(x, y, r * f, 0, 2 * math.pi)
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()


# ------------------------------------------------------------------ Minou the cat
def cat(ctx, x, y, t, facing=1, mood="judge", s=1.0, look=0.0):
    """Sitting black cat. mood: judge | shock | happy | cry | laugh | sleep."""
    black = (0.11, 0.1, 0.13)
    rim = (0.32, 0.34, 0.44)
    ctx.save()
    ctx.translate(x, y)
    if mood == "laugh":
        ctx.translate(0, -abs(math.sin(t * 18)) * 6)
    ctx.scale(facing * s, s)
    # tail
    sway = math.sin(t * 2.2) * 14
    ctx.move_to(-30, -6)
    ctx.curve_to(-90, 0, -96, -40, -84 + sway, -86)
    ink(ctx, OUTLINE, 22)
    ctx.move_to(-30, -6)
    ctx.curve_to(-90, 0, -96, -40, -84 + sway, -86)
    ctx.set_source_rgb(*black)
    ctx.set_line_width(14)
    ctx.set_line_cap(1)
    ctx.stroke()
    # body
    ctx.move_to(-36, 0)
    ctx.curve_to(-50, -50, -40, -86, -4, -104)
    ctx.curve_to(26, -100, 40, -70, 42, -40)
    ctx.curve_to(46, -20, 44, -4, 40, 0)
    ctx.close_path()
    fill_stroke(ctx, black)
    ctx.move_to(-38, -20)
    ctx.curve_to(-44, -60, -30, -88, -6, -100)
    ink(ctx, rim, 3)
    for lx in (10, 30):
        limb(ctx, [(lx, -46), (lx + 2, -4)], 13, black, ow=3.5)
    # head
    hx, hy = 16 + look * 4, -120
    for ex_ in ((-12, -26, 0, -60, 12, -28), (16, -30, 32, -60, 40, -22)):
        _poly(ctx, [(hx + ex_[0], hy + ex_[1]), (hx + ex_[2], hy + ex_[3]), (hx + ex_[4], hy + ex_[5])], black, ow=4)
    ellipse(ctx, hx + 14, hy, 40, 34)
    fill_stroke(ctx, black)
    # eyes
    blink = ((t + 0.7) % 4.1) < 0.12
    for exx in (hx + 2, hx + 30):
        if mood in ("happy", "laugh", "sleep") or blink:
            ctx.arc(exx, hy - 2, 8, math.pi * (0.1 if mood == "sleep" else 1.1), math.pi * (0.9 if mood == "sleep" else 1.9))
            ink(ctx, (0.85, 0.8, 0.3), 3.5)
            continue
        ry = 10 if mood == "shock" else 8
        ellipse(ctx, exx, hy - 2, 9, ry)
        ctx.set_source_rgb(0.93, 0.82, 0.25)
        ctx.fill()
        ellipse(ctx, exx + 2 + look * 2, hy - 2, 2.2 if mood != "shock" else 4.5, ry - 1)
        ctx.set_source_rgb(0.05, 0.05, 0.05)
        ctx.fill()
        if mood in ("judge", "cry"):  # heavy unimpressed lids
            ctx.rectangle(exx - 11, hy - 14, 22, 9)
            ctx.set_source_rgb(*black)
            ctx.fill()
            ctx.move_to(exx - 10, hy - 5)
            ctx.line_to(exx + 10, hy - 5)
            ink(ctx, (0.85, 0.8, 0.3), 2)
    ctx.move_to(hx + 14, hy + 10)
    ctx.line_to(hx + 20, hy + 10)
    ctx.line_to(hx + 17, hy + 15)
    ctx.close_path()
    ctx.set_source_rgb(0.85, 0.5, 0.55)
    ctx.fill()
    for k in (-1, 1):
        ctx.move_to(hx + 4, hy + 14 + k * 3)
        ctx.line_to(hx - 26, hy + 10 + k * 8)
        ctx.move_to(hx + 28, hy + 14 + k * 3)
        ctx.line_to(hx + 58, hy + 10 + k * 8)
    ink(ctx, (0.7, 0.7, 0.75), 1.8)
    if mood == "cry":
        tears_from(ctx, [(hx + 2, hy + 4), (hx + 30, hy + 4)], t, 0.6, 1)
    ctx.restore()


# ------------------------------------------------------------------ props
def tears_from(ctx, eyes, t, amount=1.0, facing=1):
    """Cartoon tear fountains from each eye."""
    if amount <= 0.01:
        return
    for j, (ex_, ey_) in enumerate(eyes):
        d = (-1 if j == 0 else 1) * facing
        for i in range(9):
            p = (t * 1.8 + i / 9) % 1.0
            px = ex_ + d * (14 + 120 * p) * amount
            py = ey_ - 30 * p * amount + 320 * p * p
            ellipse(ctx, px, py, 6 * amount, 8 * amount)
            ctx.set_source_rgba(0.55, 0.78, 0.95, 0.9 * (1 - p))
            ctx.fill()


def bowl(ctx, x, y, t, steam=True):
    if steam:
        scene.steam(ctx, x, y - 16, t)
    ctx.move_to(x - 95, y)
    ctx.curve_to(x - 90, y + 80, x + 90, y + 80, x + 95, y)
    ctx.close_path()
    fill_stroke(ctx, rgb("#e9e4d8"))
    ctx.move_to(x - 88, y + 22)
    ctx.curve_to(x - 40, y + 34, x + 40, y + 34, x + 88, y + 22)
    ink(ctx, rgb("#3f6a89"), 5)
    ellipse(ctx, x, y, 95, 18)
    fill_stroke(ctx, rgb("#9fc6dc"))


def board(ctx, x, y, cut=0.0):
    """Cutting board with an onion that gets sliced as cut goes 0 -> 1."""
    scene.rrect(ctx, x - 130, y - 18, 260, 26, 8)
    fill_stroke(ctx, rgb("#b98a55"))
    ellipse(ctx, x - 40, y - 52, 46, 40)
    fill_stroke(ctx, rgb("#a1566b"))
    ctx.move_to(x - 40, y - 92)
    ctx.curve_to(x - 34, y - 104, x - 30, y - 112, x - 24, y - 118)
    ink(ctx, rgb("#6b7a3a"), 5)
    for k in range(3):
        ctx.move_to(x - 40, y - 90)
        ctx.curve_to(x - 70 + k * 30, y - 70, x - 70 + k * 30, y - 30, x - 40, y - 14)
    ink(ctx, rgb("#7a3a4c"), 2.5)
    n = int(cut * 7)
    for k in range(n):
        ellipse(ctx, x + 30 + k * 13, y - 22, 6, 18)
        fill_stroke(ctx, rgb("#efe3ee"), ow=2.5)


def knife(ctx, x, y, ang=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    _poly(ctx, [(0, -6), (110, -10), (126, 0), (0, 8)], "#d6dbe0", ow=3.5)
    scene.rrect(ctx, -56, -9, 58, 18, 7)
    fill_stroke(ctx, rgb("#4a2f22"), ow=3.5)
    ctx.restore()


def shiver(ctx, x, y, t):
    for k in (-1, 1):
        for j in range(3):
            xx = x + k * (70 + j * 16)
            ctx.move_to(xx, y - 40 + j * 10)
            for s_ in range(5):
                ctx.line_to(xx + (6 if s_ % 2 else -6) * math.sin(t * 40 + j), y - 40 + j * 10 + s_ * 18)
            ink(ctx, OUTLINE, 3)


def dizzy(ctx, x, y, t):
    for k in range(4):
        a = t * 5 + k * math.pi / 2
        px, py = x + math.cos(a) * 90, y + math.sin(a) * 26
        ctx.save()
        ctx.translate(px, py)
        ctx.move_to(0, -16)
        for i in range(1, 10):
            r = 16 if i % 2 == 0 else 6
            ang = -math.pi / 2 + i * math.pi / 5
            ctx.line_to(math.cos(ang) * r, math.sin(ang) * r)
        ctx.close_path()
        fill_stroke(ctx, rgb("#f1c94a"), ow=3)
        ctx.restore()


def later_card(ctx, t, t0, words="Fifteen minutes later...", dur=1.1):
    """Full-screen title card, like the old silent-film / cartoon time skips."""
    u = (t - t0) / dur
    if not 0 <= u <= 1:
        return
    a = smooth(u / 0.15) * (1 - smooth((u - 0.85) / 0.15))
    ctx.save()
    ctx.rectangle(0, 0, W, H)
    ctx.set_source_rgba(0.12, 0.08, 0.06, 0.92 * a)
    ctx.fill()
    ctx.translate(W / 2, H * 0.45)
    ctx.scale(0.9 + 0.1 * a, 0.9 + 0.1 * a)
    ctx.set_source_rgba(0.98, 0.94, 0.84, a)
    scene.set_font(ctx, 70)
    ext = ctx.text_extents(words)
    ctx.move_to(-ext.x_advance / 2, 0)
    ctx.show_text(words)
    ctx.restore()
