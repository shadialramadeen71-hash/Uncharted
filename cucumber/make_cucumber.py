#!/usr/bin/env python3
"""
Cucumber slicing — a vertical (1080x1920) Short rendered entirely in code.

* Macro close-up of a cucumber on a wooden board (shallow depth of field).
* A chef's knife chops it into slices, speeding up as it goes.
* Every slice tips over and shows its seeded cross-section.
* A live counter above the cucumber shows how many pieces have been cut.
* Synthesised ASMR audio: crunch + board knock per cut, slice taps, final chime.

Scene is modelled in 3D (X right, Y up, Z toward camera) and drawn with an
oblique projection, so circles become ellipses through plain affine maps.

Usage:
    python3 make_cucumber.py            # Arabic  -> output/cucumber_slicing_short_ar.mp4
    python3 make_cucumber.py --en       # English -> output/cucumber_slicing_short_en.mp4
    python3 make_cucumber.py --preview  # write a few still frames to output/preview
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output")
FONT_AR = os.path.join(HERE, "fonts", "tajawal-arabic-800-normal.woff")
FONT_LAT = os.path.join(HERE, "fonts", "tajawal-latin-800-normal.woff")
FONT_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

W, H, FPS, SR = 1080, 1920, 30, 44100
HC = 1230                      # screen y of the cucumber axis

# ---------------------------------------------------------------- projection
KX, CY, KY = 0.42, 0.86, 0.38  # screen = (X - KX*Z, -CY*Y + KY*Z)
NRM = math.hypot(CY, KY)
M = np.array([[1.0, 0.0, -KX], [0.0, -CY, KY]])


def norm(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


LIGHT = norm((-0.45, 0.8, 0.45))
VIEW = norm((KX, KY / CY, 1.0))           # direction toward the camera

# ---------------------------------------------------------------- the cucumber
R = 190.0                      # radius (world units)
LEN = 1750.0
TH = 40.0                      # slice thickness
N_CUTS = 24
CUT0 = LEN - 120
CUTS = [CUT0 - i * TH for i in range(N_CUTS)]
TAPER = 210.0
AXIS_SY = -CY * R
RH = R * NRM                   # half height of the cucumber band on screen
DXT = KX * KY * R / NRM        # x shift of the cut-ellipse top point

# ---------------------------------------------------------------- timing
T_FIRST = 1.2
_iv = np.geomspace(0.55, 0.22, N_CUTS - 1)
T_CUT = [T_FIRST] + list(T_FIRST + np.cumsum(_iv))
T_LAST = T_CUT[-1]
T_PULL0, T_PULL1 = T_LAST + 0.45, T_LAST + 1.45
T_BANNER = T_PULL1 - 0.25
DUR = T_PULL1 + 2.1
assert DUR <= 14.0, DUR
LANG = "en" if "--en" in sys.argv else "ar"
H_UP = 2 * R + 115             # knife edge height between chops
HOLD = 0.035

rng = np.random.default_rng(11)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


def ease_out(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


def lerp(a, b, p):
    return a + (b - a) * p


def radius_at(x):
    d = min(x, LEN - x)
    u = clamp(d / TAPER)
    return R * math.sqrt(max(0.0, 1 - (1 - u) ** 2)) ** 0.85 if u < 1 else R


# ============================================================== textures
def smooth_noise(h, w, sh, sw, seed):
    r = np.random.default_rng(seed)
    small = (r.random((max(2, sh), max(2, sw))) * 255).astype(np.uint8)
    return np.asarray(Image.fromarray(small).resize((w, h), Image.BICUBIC), np.float32) / 255.0


def make_board():
    sc = 0.7                                   # pixels per world unit
    x0, x1, y0, y1 = -1700.0, 4200.0, -3100.0, 2700.0
    bw, bh = int((x1 - x0) * sc), int((y1 - y0) * sc)
    yy = np.arange(bh, dtype=np.float32)[:, None] / sc
    warp = smooth_noise(bh, bw, 18, 10, 1) * 90 + smooth_noise(bh, bw, 70, 40, 2) * 18
    v = yy + warp
    rings = 0.5 + 0.5 * np.sin(v * 0.075 + smooth_noise(bh, bw, 12, 6, 3) * 6)
    rings = rings ** 3
    fine = smooth_noise(bh, bw, bh // 3, bw // 90, 4)
    broad = smooth_noise(bh, bw, 6, 5, 5)
    base = np.array([201, 156, 108], np.float32)
    dark = np.array([150, 102, 62], np.float32)
    k = (0.55 * rings + 0.25 * (1 - fine) + 0.2 * broad)[..., None]
    img = base * (1 - 0.55 * k) + dark * 0.55 * k
    img *= (0.94 + 0.08 * fine)[..., None]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    # knife marks
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(260):
        cx, cy_ = rng.uniform(0, bw), rng.uniform(0, bh)
        ln = rng.uniform(15, 70)
        a = rng.normal(math.pi / 2, 0.35)
        d.line([(cx, cy_), (cx + math.cos(a) * ln, cy_ + math.sin(a) * ln)],
               fill=(235, 205, 165, int(rng.uniform(25, 70))), width=1)
    return im, sc, x0, y0


def make_skin():
    """Cucumber body texture in projected space (2 px per unit)."""
    sc, padx, pady = 2.0, 120.0, 12.0
    tw, th = int((LEN + 2 * padx) * sc), int((2 * RH + 2 * pady) * sc)
    X = np.arange(tw, dtype=np.float32) / sc - padx
    S = np.arange(th, dtype=np.float32)[:, None] / sc - RH - pady
    rr = np.array([radius_at(float(x)) / R if 0 <= x <= LEN else 0.0 for x in X], np.float32)
    half = RH * rr
    alpha = np.clip((half[None, :] - np.abs(S)) * sc + 0.5, 0, 1)
    vn = np.clip(S / np.maximum(half[None, :], 1e-3), -1, 1)

    # lighting profile across the band
    th_s = np.linspace(-math.pi, math.pi, 4000)
    n = np.stack([np.zeros_like(th_s), np.sin(th_s), np.cos(th_s)], 1)
    vis = n @ VIEW > 0
    n = n[vis]
    sy = (-CY * n[:, 1] + KY * n[:, 2]) / NRM
    order = np.argsort(sy)
    sy, n = sy[order], n[order]
    diff = np.clip(n @ LIGHT, 0, 1)
    hv = norm(LIGHT + VIEW)
    spec = np.clip(n @ hv, 0, 1) ** 60
    D = np.interp(vn, sy, diff).astype(np.float32)
    SP = np.interp(vn, sy, spec).astype(np.float32)

    # longitudinal stripes, indexed by angle around the cylinder
    ang = np.arcsin(vn)
    stripe_src = smooth_noise(360, tw, 14, tw // 260, 21)
    rows = np.clip(((ang + math.pi / 2) / math.pi * 359).astype(int), 0, 359)
    stripes = stripe_src[rows, np.arange(tw)[None, :]]
    stripes = np.clip((stripes - 0.45) / 0.35, 0, 1) ** 1.5
    speck = smooth_noise(th, tw, th // 2, tw // 3, 22)
    dark = np.array([30, 74, 30], np.float32)
    light = np.array([112, 152, 66], np.float32)
    alb = dark + (light - dark) * (0.15 + 0.85 * stripes)[..., None]
    alb *= (0.9 + 0.2 * speck)[..., None]
    shade = 0.28 + 0.9 * D
    ao = 1 - 0.38 * np.clip((vn - 0.55) / 0.45, 0, 1) ** 2
    tip = (0.55 + 0.45 * rr ** 0.6)[None, :]
    gloss = 0.6 + 0.8 * smooth_noise(th, tw, 30, tw // 40, 23)
    col = alb * (shade * ao * tip)[..., None] + (SP * gloss * 150 * tip)[..., None]
    img = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    im = Image.fromarray(img, "RGBA")

    # bumps / warts
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(1500):
        x = rng.uniform(20, LEN - 20)
        a = rng.uniform(-1.35, 1.35)
        hr = RH * radius_at(x) / R
        cxp = (x + padx) * sc
        cyp = (hr * math.sin(a) + RH + pady) * sc
        rad = rng.uniform(2.2, 4.5) * sc
        sq = max(0.25, math.cos(a))
        d.ellipse([cxp - rad, cyp - rad * sq, cxp + rad, cyp + rad * sq], fill=(18, 48, 18, 120))
        hrad = rad * 0.45
        d.ellipse([cxp - rad * 0.5 - hrad, cyp - rad * sq * 0.6 - hrad * sq,
                   cxp - rad * 0.5 + hrad, cyp - rad * sq * 0.6 + hrad * sq], fill=(200, 225, 150, 110))
    for _ in range(900):        # pale speckles
        x = rng.uniform(10, LEN - 10)
        a = rng.uniform(-1.4, 1.4)
        hr = RH * radius_at(x) / R
        cxp = (x + padx) * sc
        cyp = (hr * math.sin(a) + RH + pady) * sc
        rad = rng.uniform(0.6, 1.4) * sc
        d.ellipse([cxp - rad, cyp - rad, cxp + rad, cyp + rad], fill=(185, 205, 120, 90))
    ov.putalpha(Image.fromarray(np.minimum(np.asarray(ov)[..., 3], (alpha * 255).astype(np.uint8))))
    im = Image.alpha_composite(im, ov)
    return im, sc, padx, pady


def make_face(size=640):
    """Cross-section of a cucumber slice (unit disc mapped to size x size)."""
    c = size / 2
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    dx, dy = (xx - c) / c, (yy - c) / c
    rho = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    n1 = smooth_noise(size, size, 60, 60, 31)
    flesh_out = np.array([150, 200, 95], np.float32)
    flesh_in = np.array([214, 234, 168], np.float32)
    t = np.clip((0.93 - rho) / 0.33, 0, 1)[..., None]
    col = flesh_out * (1 - t) + flesh_in * t
    # seed cavity: three lobes
    lobe = 0.58 + 0.04 * np.cos(3 * th)
    cav = np.clip((lobe - rho) * 40, 0, 1)[..., None]
    cav_col = np.array([196, 222, 150], np.float32)
    col = col * (1 - cav * 0.85) + cav_col * cav * 0.85
    # placenta lines
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.5
        dist = np.abs(np.sin(th - a)) * rho
        m = (np.cos(th - a) > 0) & (dist < 0.025) & (rho < lobe)
        col[m] = col[m] * 0.6 + np.array([232, 240, 205]) * 0.4
    centre = np.clip((0.07 - rho) * 30, 0, 1)[..., None]
    col = col * (1 - centre * 0.5) + np.array([235, 242, 210]) * centre * 0.5
    # skin ring
    ring = np.clip((rho - 0.955) * 60, 0, 1)[..., None]
    col = col * (1 - ring) + np.array([34, 82, 34], np.float32) * ring
    sub = np.clip(1 - np.abs(rho - 0.93) * 45, 0, 1)[..., None]
    col = col * (1 - sub * 0.5) + np.array([110, 170, 70]) * sub * 0.5
    col *= (0.93 + 0.12 * n1)[..., None]
    # moist sheen
    sheen = np.clip(1 - np.hypot(dx + 0.35, dy + 0.35) / 0.55, 0, 1) ** 2
    col += (sheen * 45)[..., None]
    alpha = np.clip((1 - rho) * c + 0.5, 0, 1) * 255
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), alpha]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im)
    # seeds
    for k in range(3):
        base = k * 2 * math.pi / 3 + 0.5 + math.pi / 3
        for j in range(9):
            a = base + (j % 3 - 1) * 0.33 + rng.normal(0, 0.05)
            rr_ = 0.26 + (j // 3) * 0.1 + rng.normal(0, 0.015)
            sx, sy = c + math.cos(a) * rr_ * c, c + math.sin(a) * rr_ * c
            ln, wd = 0.075 * c, 0.035 * c
            pts = []
            for q in range(16):
                u = q / 16 * 2 * math.pi
                lx, ly = math.cos(u) * ln, math.sin(u) * wd
                pts.append((sx + lx * math.cos(a) - ly * math.sin(a), sy + lx * math.sin(a) + ly * math.cos(a)))
            d.polygon(pts, fill=(240, 242, 214, 235), outline=(190, 210, 150, 200))
    return im.filter(ImageFilter.GaussianBlur(0.8))


def make_knife():
    """Chef's knife side view in its own (lz, ly) plane, 2 px per unit."""
    sc = 2.0
    z0, z1, y0, y1 = -370.0, 490.0, -12.0, 172.0
    w, h = int((z1 - z0) * sc), int((y1 - y0) * sc)

    def P(lz, ly):
        return ((lz - z0) * sc, (y1 - ly) * sc)

    big = 3
    mask = Image.new("L", (w * big, h * big), 0)
    md = ImageDraw.Draw(mask)
    blade = []
    for i in range(41):                        # edge: heel -> tip
        u = i / 40
        lz = lerp(178, -352, u)
        ly = 0 if u < 0.68 else 52 * ((u - 0.68) / 0.32) ** 2.2
        blade.append(P(lz, ly))
    for i in range(31):                        # spine: tip -> heel
        u = i / 30
        lz = lerp(-352, 182, u)
        ly = 52 + (146 - 52) * (1 - (1 - u) ** 2.4) if u < 0.6 else 146 - 4 * (1 - u)
        blade.append(P(lz, ly))
    md.polygon([(x * big, y * big) for x, y in blade], fill=255)
    mask = mask.resize((w, h), Image.LANCZOS)

    yy = np.arange(h, dtype=np.float32)[:, None] / sc
    ly = y1 - yy
    t = np.clip(ly / 146, 0, 1)
    steel = np.array([150, 158, 168], np.float32) * (1 - t)[..., None] + np.array([212, 217, 224], np.float32) * t[..., None]
    steel = np.broadcast_to(steel, (h, w, 3)).copy()
    brushed = smooth_noise(h, w, h // 2, w // 70, 41)
    steel *= (0.93 + 0.1 * brushed)[..., None]
    xx = np.arange(w, dtype=np.float32)[None, :] / sc
    diag = np.exp(-(((xx * 0.55 + ly * 1.0) - 330) / 55) ** 2)
    steel += (diag * 40)[..., None]
    bevel = (ly < 16)
    steel[np.broadcast_to(bevel, (h, w))] = steel[np.broadcast_to(bevel, (h, w))] * 0.55 + np.array([236, 240, 245]) * 0.45
    line = (np.abs(ly - 16) < 0.8)
    steel[np.broadcast_to(line, (h, w))] *= 0.78
    im = Image.fromarray(np.dstack([np.clip(steel, 0, 255), np.asarray(mask)]).astype(np.uint8), "RGBA")

    # bolster + handle
    hd = Image.new("RGBA", (w * big, h * big), (0, 0, 0, 0))
    d = ImageDraw.Draw(hd)

    def Pb(lz, ly_):
        x, y = P(lz, ly_)
        return x * big, y * big

    d.polygon([Pb(176, 146), Pb(205, 138), Pb(205, 50), Pb(176, 44)], fill=(120, 124, 130, 255))
    d.rounded_rectangle([*Pb(203, 132), *Pb(482, 54)], radius=26 * big * sc / 2, fill=(38, 32, 30, 255))
    d.rounded_rectangle([*Pb(206, 128), *Pb(476, 112)], radius=8 * big, fill=(66, 58, 54, 255))
    for rz in (265, 345, 425):
        cx, cy_ = Pb(rz, 93)
        rr_ = 7 * big * sc
        d.ellipse([cx - rr_, cy_ - rr_, cx + rr_, cy_ + rr_], fill=(196, 200, 206, 255))
        d.ellipse([cx - rr_ * 0.5 - rr_ * 0.3, cy_ - rr_ * 0.5 - rr_ * 0.3, cx - rr_ * 0.5 + rr_ * 0.3,
                   cy_ - rr_ * 0.5 + rr_ * 0.3], fill=(250, 250, 252, 255))
    hd = hd.resize((w, h), Image.LANCZOS)
    im = Image.alpha_composite(im, hd)
    outline = [((x / sc) + z0, y1 - (y / sc)) for x, y in blade]
    return im, sc, z0, y1, outline


# ============================================================== drawing helpers
def warp(dst, src, A, b):
    """Composite src onto dst where screen = A @ (u, v) + b (u, v = src pixels)."""
    sw, sh = src.size
    corners = np.array([[0, 0], [sw, 0], [0, sh], [sw, sh]], float)
    scr = corners @ A.T + b
    x0, y0 = np.floor(scr.min(0)).astype(int)
    x1, y1 = np.ceil(scr.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, dst.size[0]), min(y1, dst.size[1])
    if x1 <= x0 or y1 <= y0:
        return
    Ai = np.linalg.inv(A)
    off = Ai @ (np.array([x0 + 0.5, y0 + 0.5]) - b) - 0.5
    coeffs = (Ai[0, 0], Ai[0, 1], off[0] + 0.5 * (Ai[0, 0] + Ai[0, 1]) * 0,
              Ai[1, 0], Ai[1, 1], off[1])
    coeffs = (Ai[0, 0], Ai[0, 1], off[0], Ai[1, 0], Ai[1, 1], off[1])
    out = src.transform((x1 - x0, y1 - y0), Image.AFFINE, coeffs, resample=Image.BILINEAR)
    dst.alpha_composite(out, (x0, y0))


def aa_polygon(dst, pts, color, ss=3):
    pts = np.asarray(pts, float)
    x0, y0 = np.floor(pts.min(0)).astype(int) - 1
    x1, y1 = np.ceil(pts.max(0)).astype(int) + 1
    cx0, cy0 = max(x0, 0), max(y0, 0)
    cx1, cy1 = min(x1, dst.size[0]), min(y1, dst.size[1])
    if cx1 <= cx0 or cy1 <= cy0:
        return
    w, h = cx1 - cx0, cy1 - cy0
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).polygon([((x - cx0) * ss, (y - cy0) * ss) for x, y in pts], fill=255)
    m = m.resize((w, h), Image.BOX)
    if len(color) == 4:
        m = m.point(lambda v: v * color[3] // 255)
    layer = Image.new("RGBA", (w, h), tuple(color[:3]) + (255,))
    layer.putalpha(m)
    dst.alpha_composite(layer, (cx0, cy0))


def convex_hull(points):
    pts = sorted(set(map(tuple, np.round(points, 2))))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


# ============================================================== text / UI
def emoji(ch, size):
    f = ImageFont.truetype(FONT_EMOJI, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox())
    s = size / max(im.size)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def text_img(txt, font, fill, stroke=0, stroke_fill=(0, 0, 0), shadow=True):
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = d0.textbbox((0, 0), txt, font=font, stroke_width=stroke)
    pad = 30
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - bb[0] + 4, pad - bb[1] + 7), txt, font=font, fill=(0, 0, 0, 150),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 150))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).text((pad - bb[0], pad - bb[1]), txt, font=font, fill=fill,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def hstack(parts, gap=18):
    w = sum(p.width for p in parts) + gap * (len(parts) - 1)
    h = max(p.height for p in parts)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for p in parts:
        im.alpha_composite(p, (x, (h - p.height) // 2))
        x += p.width + gap
    return im


def paste_center(dst, im, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    dst.alpha_composite(im, (x, y)) if x >= 0 and y >= 0 and x + im.width <= dst.width and y + im.height <= dst.height \
        else _paste_clip(dst, im, x, y)


def _paste_clip(dst, im, x, y):
    layer = Image.new("RGBA", dst.size, (0, 0, 0, 0))
    layer.paste(im, (x, y))
    dst.alpha_composite(layer)


# ============================================================== scene state
def knife_state(t):
    x = CUTS[0]
    if t < T_CUT[0] - 0.3:
        p = clamp(t / 0.85)
        y = H_UP + 900 * (1 - ease_out(p)) + 8 * math.sin(t * 5)
        return CUTS[0], y
    for i, tc in enumerate(T_CUT):
        prev_iv = T_CUT[i] - T_CUT[i - 1] if i else 0.6
        next_iv = T_CUT[i + 1] - T_CUT[i] if i + 1 < N_CUTS else 0.7
        dd = 0.3 if i == 0 else min(0.15, 0.45 * prev_iv)
        du = min(0.22, 0.5 * next_iv)
        s = tc - dd
        e = tc + HOLD + du
        nx = CUTS[i + 1] if i + 1 < N_CUTS else CUTS[i]
        if t < s:
            return CUTS[i], H_UP + 6 * math.sin(t * 7)
        if t < tc:
            p = (t - s) / dd
            return CUTS[i], H_UP * (1 - p * p)
        if t < tc + HOLD:
            return CUTS[i], 0.0
        if t < e:
            p = (t - tc - HOLD) / du
            return lerp(CUTS[i], nx, ease(p)), H_UP * ease_out(p)
        x = nx
    p = (t - (T_LAST + HOLD + 0.35)) / 0.9
    return x, H_UP + 4500 * clamp(p) ** 2


def knife_enter_time(i):
    prev_iv = T_CUT[i] - T_CUT[i - 1] if i else 0.6
    dd = 0.3 if i == 0 else min(0.15, 0.45 * prev_iv)
    return T_CUT[i] - dd * (1 - math.sqrt(1 - 2 * R / H_UP))


def cuts_done(t):
    return sum(1 for tc in T_CUT if t >= tc)


SLICE_PARAMS = []
for i in range(N_CUTS):
    SLICE_PARAMS.append(dict(
        phi_f=math.radians(90 if i == 1 else rng.uniform(78, 86)),
        yaw=math.radians(rng.normal(0, 4)),
        dx=rng.uniform(-4, 10),
        dz=rng.normal(0, 6),
        rot=rng.uniform(0, 2 * math.pi),
        lift=0 if i == 1 else rng.uniform(10, 18),
    ))


def slice_pose(i, t):
    """Return (center, axis, e1, e2, r, h) for slice i (i >= 1) or None."""
    tr = t - T_CUT[i] - 0.02
    if tr < 0:
        return None
    a, b = CUTS[i], CUTS[i - 1]
    h = (b - a) / 2
    r = radius_at((a + b) / 2)
    pr = SLICE_PARAMS[i]
    df = 0.30
    if tr < df:
        phi = pr["phi_f"] * (tr / df) ** 2
        land = 0.0
    else:
        k = tr - df
        phi = pr["phi_f"] - math.radians(7) * math.exp(-k * 13) * abs(math.sin(k * 28))
        land = ease_out(k / 0.25)
    c = np.array([b - h * math.cos(phi) + r * math.sin(phi), h * math.sin(phi) + r * math.cos(phi), 0.0])
    ax = np.array([math.cos(phi), -math.sin(phi), 0.0])
    e1 = np.array([math.sin(phi), math.cos(phi), 0.0])
    e2 = np.array([0.0, 0.0, 1.0])
    p = clamp(tr / df)
    yaw = pr["yaw"] * land
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    Ry = np.array([[cy_, 0, sy_], [0, 1, 0], [-sy_, 0, cy_]])
    ax, e1, e2 = Ry @ ax, Ry @ e1, Ry @ e2
    c = c + np.array([pr["dx"] * land, pr["lift"] * p, pr["dz"] * land])
    return c, ax, e1, e2, r, h


# ============================================================== renderer
class Renderer:
    def __init__(self):
        print("building textures...", flush=True)
        self.board, self.bsc, self.bx0, self.by0 = make_board()
        self.skin, self.ssc, self.spx, self.spy = make_skin()
        face = make_face()
        self.faces = {}
        self.face_base = face
        self.knife, self.ksc, self.kz0, self.ky1, self.kout = make_knife()
        self.mask_cache = {}
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        v = 1 - 0.42 * np.clip(np.hypot((xx - W / 2) / (W * 0.75), (yy - HC) / (H * 0.62)) - 0.35, 0, 1) ** 1.6
        self.vignette = v[..., None]
        self.yy = yy[:, :1]
        self.f_label = ImageFont.truetype(FONT_AR, 74)
        self.f_hook = ImageFont.truetype(FONT_AR, 66)
        self.f_num = ImageFont.truetype(FONT_LAT, 250)
        self.f_ban = ImageFont.truetype(FONT_AR, 120)
        self.f_ban_num = ImageFont.truetype(FONT_LAT, 150)
        self.f_sub = ImageFont.truetype(FONT_AR, 58)
        self.e_cuc = emoji("🥒", 78)
        self.e_knife = emoji("🔪", 70)
        self.e_think = emoji("🤔", 66)
        white, gold = (255, 255, 255), (255, 226, 70)
        big = dict(stroke=6, stroke_fill=(30, 30, 30))
        thin = dict(stroke=3, stroke_fill=(20, 20, 20))
        cuc = self.e_cuc.resize((130, 130), Image.LANCZOS)
        if LANG == "en":
            f_lab = ImageFont.truetype(FONT_LAT, 70)
            f_hk = ImageFont.truetype(FONT_LAT, 60)
            f_bn = ImageFont.truetype(FONT_LAT, 130)
            f_sb = ImageFont.truetype(FONT_LAT, 58)
            self.label = hstack([self.e_knife, text_img("PIECES CUT", f_lab, white)], 10)
            self.hook = hstack([text_img("How many slices in one cucumber?", f_hk, white, **thin), self.e_think], 12)
            self.banner = hstack([text_img(f"{N_CUTS} SLICES!", f_bn, gold, **big), cuc], -20)
            self.sub = text_img("From just ONE cucumber", f_sb, white, **thin)
        else:
            self.label = hstack([text_img("عدد القطع", self.f_label, white), self.e_knife], 10)
            self.hook = hstack([self.e_think, text_img("كم قطعة بتطلع من خيارة وحدة؟", self.f_hook, white, **thin)], 12)
            self.banner = hstack([cuc, text_img("!", self.f_ban_num, gold, **big),
                                  text_img("قطعة", self.f_ban, gold, **big),
                                  text_img(str(N_CUTS), self.f_ban_num, gold, **big)], -36)
            self.sub = text_img("من خيارة وحدة بس", self.f_sub, white, **thin)
        self.num_cache = {}
        self.precompute_camera()

    # -------------------------------------------------- camera
    def precompute_camera(self):
        n = int(DUR * FPS) + 2
        self.cam = []
        cx = None
        for f in range(n):
            t = f / FPS
            kx, _ = knife_state(min(t, T_LAST + 0.3))
            if t < T_CUT[0] - 0.3:
                z = lerp(1.95, 1.6, ease(t / 0.9))
            else:
                z = 1.6
            pz = ease((t - T_PULL0) / (T_PULL1 - T_PULL0))
            z = lerp(z, 0.56, pz)
            target = kx + 0.10 * W / z
            cx = target if cx is None else cx + (target - cx) * 0.18
            final_cx = 1180.0
            self.cam.append((lerp(cx, final_cx, pz), z))

    def to_screen(self, p, cam, z, shake):
        return np.array([(p[0] - cam[0]) * z + W / 2 + shake[0], (p[1] - cam[1]) * z + HC + shake[1]])

    def face_img(self, level):
        level = int(clamp(level, 0.3, 1.2) * 20)
        if level not in self.faces:
            k = level / 20
            f = self.face_base
            rgb = f.convert("RGB").point(lambda v: min(255, int(v * k)))
            im = rgb.convert("RGBA")
            im.putalpha(f.getchannel("A"))
            self.faces[level] = im
        return self.faces[level]

    def draw_face(self, frame, centre, e1, e2, r, normal, rot, cam, z, shake):
        lvl = 0.72 + 0.42 * max(0.0, float(normal @ LIGHT))
        img = self.face_img(lvl)
        s = img.size[0] / 2
        cr, sr = math.cos(rot), math.sin(rot)
        u = cr * e1 + sr * e2
        v = -sr * e1 + cr * e2
        A = z * np.column_stack([M @ u, M @ v]) * (r / s)
        b = self.to_screen(M @ centre, cam, z, shake) - A @ np.array([s, s])
        warp(frame, img, A, b)

    def body_mask(self, a, b):
        key = (round(a, 2), round(b, 2))
        if key in self.mask_cache:
            return self.mask_cache[key]
        sc, px, py = self.ssc, self.spx, self.spy
        x0 = int(max(0, (a + px - 100) * sc))
        x1 = int(min(self.skin.size[0], (b + px + 100) * sc))
        hgt = self.skin.size[1]
        ss = 2
        m = Image.new("L", ((x1 - x0) * ss, hgt * ss), 0)
        d = ImageDraw.Draw(m)

        def T(x, sy):
            return (((x + px) * sc - x0) * ss, (sy + RH + py) * sc * ss)

        ra, rb = radius_at(a) / R, radius_at(b) / R
        d.polygon([T(a + DXT * ra, -RH - 20), T(b + DXT * rb, -RH - 20),
                   T(b - DXT * rb, RH + 20), T(a - DXT * ra, RH + 20)], fill=255)
        for x, rr in ((a, ra), (b, rb)):
            if 0 < x < LEN:
                pts = []
                for q in range(64):
                    tq = q / 64 * 2 * math.pi
                    Yo, Zo = R * rr * math.sin(tq), R * rr * math.cos(tq)
                    pts.append(T(x - KX * Zo, -CY * Yo + KY * Zo))
                d.polygon(pts, fill=255)
        m = m.resize((x1 - x0, hgt), Image.BOX)
        piece = self.skin.crop((x0, 0, x1, hgt))
        al = np.minimum(np.asarray(piece.getchannel("A")), np.asarray(m))
        piece.putalpha(Image.fromarray(al))
        self.mask_cache[key] = (piece, x0)
        return piece, x0

    def draw_body(self, frame, a, b, shift, cam, z, shake):
        piece, x0 = self.body_mask(a, b)
        sc = self.ssc
        A = np.eye(2) * (z / sc)
        origin = np.array([x0 / sc - self.spx + shift, -RH - self.spy + AXIS_SY])
        bvec = self.to_screen(origin, cam, z, shake)
        warp(frame, piece, A, bvec)

    def draw_slice(self, frame, pose, rot, cam, z, shake):
        c, ax, e1, e2, r, h = pose
        rims = []
        for sgn in (-1, 1):
            cc = c + sgn * h * ax
            for q in range(48):
                tq = q / 48 * 2 * math.pi
                P = cc + r * (math.cos(tq) * e1 + math.sin(tq) * e2)
                rims.append(self.to_screen(M @ P, cam, z, shake))
        hull = convex_hull(np.array(rims))
        if len(hull) >= 3:
            aa_polygon(frame, hull, (44, 92, 40))
        nf = ax if ax @ VIEW > 0 else -ax
        fc = c + h * nf
        # thin lighter rim just under the face
        rim = [self.to_screen(M @ (fc - nf * 3 + (r + 1.5) * (math.cos(q / 40 * 6.283) * e1 + math.sin(q / 40 * 6.283) * e2)),
                              cam, z, shake) for q in range(40)]
        aa_polygon(frame, rim, (70, 125, 55))
        self.draw_face(frame, fc, e1, e2, r, nf, rot, cam, z, shake)

    def knife_points(self, xk, yk):
        return [np.array([xk, yk + ly, lz]) for lz, ly in self.kout]

    def draw_knife(self, frame, xk, yk, cam, z, shake):
        sc = self.ksc
        du = z * (M @ np.array([0, 0, 1.0])) / sc      # per texture px along lz
        dv = z * (M @ np.array([0, -1.0, 0])) / sc     # per texture px down
        A = np.column_stack([du, dv])
        origin = M @ np.array([xk, yk + self.ky1, self.kz0])
        warp(frame, self.knife, A, self.to_screen(origin, cam, z, shake))

    # -------------------------------------------------- frame
    def frame(self, t, f_idx):
        cam_x, z = self.cam[min(f_idx, len(self.cam) - 1)]
        cam = (cam_x, AXIS_SY)
        k = cuts_done(t)
        shake = np.zeros(2)
        if k:
            dt = t - T_CUT[k - 1]
            if dt < 0.14:
                shake = np.array([math.sin(dt * 90) * 1.5, math.sin(dt * 70) * 5]) * math.exp(-dt * 25) * z

        frame = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        # board
        A = np.eye(2) * (z / self.bsc)
        bvec = self.to_screen(np.array([self.bx0, self.by0]), cam, z, shake)
        warp(frame, self.board.convert("RGBA") if not hasattr(self, "_brgba") else self._brgba, A, bvec)

        xk, yk = knife_state(t)
        poses = [(i, slice_pose(i, t)) for i in range(1, k)]
        end_shift = 0.0
        if k:
            end_shift = 470 * ease_out((t - T_CUT[0] - 0.03) / 0.6)

        # shadows (quarter res)
        q = 4
        sh = Image.new("L", (W // q, H // q), 0)
        sd = ImageDraw.Draw(sh)

        def S(P):
            s_ = self.to_screen(M @ np.asarray(P, float), cam, z, shake) / q
            return (s_[0], s_[1])

        right = CUTS[k - 1] if k else LEN
        segs = [(0, right, 0.0)] + ([(CUT0, LEN, end_shift)] if k else [])
        for a, b, sft in segs:
            pts = [S((a + sft + 40, 0, 40)), S((b + sft - 20, 0, 40)), S((b + sft - 20, 40, -260)),
                   S((a + sft + 60, 40, -260))]
            sd.polygon(pts, fill=170)
        for i, pose in poses:
            if pose is None:
                continue
            c, ax, e1, e2, r, h = pose
            g = [S((c[0] + 20 + r * 0.95 * math.cos(u), 0, c[2] - 15 + r * 0.95 * math.sin(u)))
                 for u in np.linspace(0, 6.283, 24)]
            sd.polygon(g, fill=150)
        fade = math.exp(-max(0.0, yk) / 420)
        kp = []
        for P in self.knife_points(xk, yk):
            Ps = P - (P[1] / LIGHT[1]) * LIGHT
            kp.append(S(Ps))
        sd.polygon(kp, fill=int(140 * fade))
        sh = sh.filter(ImageFilter.GaussianBlur(float(2.5 * z + 1))).resize((W, H), Image.BILINEAR)
        arr = np.asarray(frame, np.float32)[..., :3]
        arr *= (1 - np.asarray(sh, np.float32)[..., None] / 255 * 0.6)
        frame = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")

        # end piece and fallen slices
        if k:
            self.draw_body(frame, CUT0, LEN, end_shift, cam, z, shake)
        standing = []
        for i, pose in poses:
            if pose is None:
                continue
            tr = t - T_CUT[i]
            if tr < 0.17:
                standing.append((i, pose))
            else:
                self.draw_slice(frame, pose, SLICE_PARAMS[i]["rot"], cam, z, shake)
        # remaining body (split at the next cut while the blade is inside it,
        # so the part right of the blade hides the steel)
        split = k < N_CUTS and abs(xk - CUTS[k]) < 0.5
        self.draw_body(frame, 0, CUTS[k] if split else right, 0.0, cam, z, shake)
        def cut_face():
            fc = np.array([right, R, 0.0])
            self.draw_face(frame, fc, np.array([0, 1.0, 0]), np.array([0, 0, 1.0]), radius_at(right),
                           np.array([1.0, 0, 0]), 0.3 * k, cam, z, shake)

        if k and not split:
            cut_face()
        # knife then slices still standing next to the blade
        self.draw_knife(frame, xk, yk, cam, z, shake)
        if split:
            self.draw_body(frame, CUTS[k], right, 0.0, cam, z, shake)
            if k:
                cut_face()
        for i, pose in standing:
            self.draw_slice(frame, pose, SLICE_PARAMS[i]["rot"], cam, z, shake)

        # juice droplets
        if k:
            dl = ImageDraw.Draw(frame, "RGBA")
            for j in range(max(0, k - 3), k):
                dt = t - T_CUT[j]
                if dt > 0.55:
                    continue
                r_ = np.random.default_rng(100 + j)
                for _ in range(9):
                    vx, vy = r_.uniform(-260, 340), r_.uniform(-620, -260)
                    px = CUTS[j] + vx * dt
                    py = AXIS_SY - RH * 0.6 + vy * dt + 0.5 * 2600 * dt * dt
                    sp = self.to_screen(np.array([px, py]), cam, z, shake)
                    rad = r_.uniform(2.0, 4.5) * z
                    al = int(200 * (1 - dt / 0.55))
                    dl.ellipse([sp[0] - rad, sp[1] - rad, sp[0] + rad, sp[1] + rad], fill=(215, 240, 180, al))
                    dl.ellipse([sp[0] - rad * 0.4, sp[1] - rad * 0.6, sp[0], sp[1] - rad * 0.2],
                               fill=(255, 255, 255, al))

        # depth of field + vignette + grade
        img = np.asarray(frame, np.float32)[..., :3]
        small = frame.convert("RGB").resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2.2))
        blur = np.asarray(small.resize((W, H), Image.BILINEAR), np.float32)
        focus = 470 * z / 1.6 + 120
        dof = np.clip((np.abs(self.yy - HC) - focus) / 380, 0, 1) * clamp((z - 0.5) / 1.1)
        img = img * (1 - dof[..., None]) + blur * dof[..., None]
        img = img * self.vignette
        img = (img - 128) * 1.06 + 128 + np.array([4, 2, -3])
        frame = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")

        self.draw_ui(frame, t, k)
        return frame.convert("RGB")

    def num_img(self, n, color):
        key = (n, color)
        if key not in self.num_cache:
            self.num_cache[key] = text_img(str(n), self.f_num, color, stroke=5, stroke_fill=(25, 25, 25))
        return self.num_cache[key]

    def draw_ui(self, frame, t, k):
        # hook line
        if t < 2.2:
            a = clamp(t / 0.3) * clamp((2.2 - t) / 0.4)
            paste_center(frame, self.hook, W / 2, 200, 1.0, a)
        # counter panel above the cucumber
        app = ease_out(t / 0.45)
        cy_ = 470 - (1 - app) * 80
        panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        pw, ph = 560, 400
        pd.rounded_rectangle([W / 2 - pw / 2, cy_ - ph / 2, W / 2 + pw / 2, cy_ + ph / 2], radius=60,
                             fill=(15, 22, 15, int(150 * app)), outline=(140, 210, 100, int(200 * app)), width=5)
        frame.alpha_composite(panel)
        paste_center(frame, self.label, W / 2, cy_ - 118, 1.0, app)
        pop = 0.0
        if k:
            dt = t - T_CUT[k - 1]
            pop = math.exp(-dt * 11)
        col = (175, 255, 120) if pop > 0.35 else (255, 255, 255)
        paste_center(frame, self.num_img(k, col), W / 2, cy_ + 55, 1.0 + 0.32 * pop, app)
        # final banner
        if t > T_BANNER:
            p = (t - T_BANNER) / 0.45
            s = 0.4 + 0.6 * ease_out(p) + 0.08 * math.sin(clamp(p, 0, 2) * math.pi) * (p < 2)
            paste_center(frame, self.banner, W / 2, 890, s, clamp(p * 2))
            if t > T_BANNER + 0.35:
                paste_center(frame, self.sub, W / 2, 1030, 1.0, clamp((t - T_BANNER - 0.35) / 0.3))


# ============================================================== audio
def bandpass(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def make_audio(path):
    n = int(DUR * SR) + SR
    out = np.zeros(n)
    r = np.random.default_rng(5)

    def add(sig, t, gain=1.0):
        i = int(t * SR)
        if i >= n:
            return
        sig = sig[: n - i]
        out[i:i + len(sig)] += sig * gain

    for i, tc in enumerate(T_CUT):
        te = knife_enter_time(i)
        ln = max(0.03, tc - te + 0.012)
        m = int(ln * SR)
        noise = bandpass(r.normal(0, 1, m + 2000), 1300, 7500)[:m]
        env = np.linspace(0.3, 1, m) ** 0.6 * (0.6 + 0.4 * r.random(m) ** 6)
        crack = np.zeros(m)
        for _ in range(int(ln * 380)):
            p = r.integers(0, m - 40)
            crack[p:p + 40] += r.normal(0, 1, 40) * np.exp(-np.arange(40) / 6)
        add((noise / (np.abs(noise).max() + 1e-9) * env + crack * 0.6), te, 0.42)
        k = int(0.14 * SR)
        tt = np.arange(k) / SR
        pitch = r.uniform(0.92, 1.08)
        thock = (np.sin(2 * np.pi * 150 * pitch * tt) * np.exp(-tt * 38) +
                 0.6 * np.sin(2 * np.pi * 265 * pitch * tt) * np.exp(-tt * 55) +
                 0.35 * np.sin(2 * np.pi * 430 * pitch * tt) * np.exp(-tt * 80))
        click = r.normal(0, 1, k) * np.exp(-tt * 600)
        add(thock * 0.75 + click * 0.25, tc, 0.85)
        if i >= 1:                         # slice landing tap
            kk = int(0.05 * SR)
            t2 = np.arange(kk) / SR
            tap = np.sin(2 * np.pi * r.uniform(700, 1000) * t2) * np.exp(-t2 * 120) + r.normal(0, 0.4, kk) * np.exp(-t2 * 300)
            add(tap, tc + 0.32, 0.16)
        kk = int(0.03 * SR)                # counter pop
        t2 = np.arange(kk) / SR
        add(np.sin(2 * np.pi * (1500 + 30 * i) * t2) * np.exp(-t2 * 160), tc + 0.01, 0.07)
    # end piece slide
    m = int(0.5 * SR)
    sl = bandpass(r.normal(0, 1, m), 400, 3000) * np.exp(-np.arange(m) / SR * 7)
    add(sl / np.abs(sl).max(), T_CUT[0] + 0.05, 0.12)
    # whoosh on pull back
    m = int((T_PULL1 - T_PULL0) * SR)
    wn = bandpass(r.normal(0, 1, m), 300, 2500)
    env = np.sin(np.linspace(0, np.pi, m)) ** 2
    add(wn / np.abs(wn).max() * env, T_PULL0, 0.18)
    # final chime
    m = int(1.8 * SR)
    t2 = np.arange(m) / SR
    chime = sum(np.sin(2 * np.pi * f * t2) * np.exp(-t2 * d) * a
                for f, d, a in ((1046.5, 3, 0.6), (1318.5, 3.5, 0.5), (1568, 4, 0.45), (2093, 6, 0.25)))
    add(chime, T_BANNER, 0.28)
    add(chime, T_BANNER + 0.12, 0.12)
    # room tone
    out += bandpass(r.normal(0, 1, n), 80, 1200) * 0.004
    out = out[: int(DUR * SR)]
    out = np.tanh(out / (np.abs(out).max() + 1e-9) * 1.4) * 0.9
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ============================================================== main
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rd = Renderer()
    rd._brgba = rd.board.convert("RGBA")
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT_DIR, "preview")
        os.makedirs(pdir, exist_ok=True)
        for t in (0.3, 1.40, 1.45, 1.62, 2.2, 3.05, 6.0, 9.0, T_LAST + 0.2, DUR - 0.5):
            rd.frame(t, int(t * FPS)).save(os.path.join(pdir, f"f_{t:05.2f}.png"))
            print("preview", t, flush=True)
        return
    wav = os.path.join(OUT_DIR, f"_audio_{LANG}.wav")
    make_audio(wav)
    out = os.path.join(OUT_DIR, f"cucumber_slicing_short_{LANG}.mp4")
    nframes = int(DUR * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(nframes):
        proc.stdin.write(rd.frame(f / FPS, f).tobytes())
        if f % 30 == 0:
            print(f"frame {f}/{nframes}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    print("wrote", out, f"({DUR:.1f}s, {N_CUTS} pieces)")


if __name__ == "__main__":
    main()
