#!/usr/bin/env python3
"""
Two tomatoes -> 100 pieces — a vertical (1080x1920) English Short rendered in code.

Phase A: close-up, a chef's knife slices each tomato into 10 slices (20 pieces).
         Every slice tips over and shows the red flesh, seed chambers and seeds.
Phase B: the knife chops across the row of slices 4 times (left half, right
         half) — every chop adds 10 pieces — until the counter hits 100.

Tomatoes are ray-traced (sphere ∩ slab per piece) with numpy, then composited
on the same board / knife / oblique-projection engine as ../cucumber.

Usage:
    python3 make_tomato.py            # -> output/tomato_100_pieces_short_en.mp4
    python3 make_tomato.py --preview  # still frames -> output/preview
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cucumber"))
import make_cucumber as base  # noqa: E402  shared board / knife / text helpers
from make_cucumber import (FONT_LAT, FPS, H, KX, KY, CY, LIGHT, M, SR, VIEW, W, bandpass, clamp,  # noqa: E402
                           ease, ease_out, emoji, hstack, lerp, make_board, make_knife, norm,
                           paste_center, smooth_noise, text_img, warp)

OUT_DIR = os.path.join(HERE, "output")
HC = 1250
D_RAY = np.array([KX, KY / CY, 1.0])          # ray direction toward the camera
HV = norm(LIGHT + VIEW)

# ---------------------------------------------------------------- tomatoes
R = 165.0
TH = 2 * R / 10
CX = [0.0, 2 * R + 70]                         # tomato 0 (left), tomato 1 (right)
NCUT = 9
OFF = [0.35, 1.1]                              # rotation of the seed chambers

# ---------------------------------------------------------------- timeline
T_START = 1.0
_iv = list(np.geomspace(0.42, 0.26, NCUT - 1)) + [0.42] + list(np.geomspace(0.27, 0.20, NCUT - 1))
_times = [T_START]
for _v in _iv:
    _times.append(_times[-1] + _v)
EVENTS = []                                    # (time, tomato, k, world x of the cut)
_n = 0
for _j in (1, 0):
    for _k in range(1, NCUT + 1):
        EVENTS.append((_times[_n], _j, _k, CX[_j] + R - _k * TH))
        _n += 1
T_A_LAST = EVENTS[-1][0]
H_UP = 2 * R + 110
HOLD = 0.035

T_B0 = T_A_LAST + 1.45
CHOP_DT = 0.40
T_CHOPS = [T_B0 + i * CHOP_DT for i in range(8)]
Z_LINES = [-98.0, -33.0, 33.0, 98.0]
H_B = 250.0
KB_SCALE = 1.3
GAP = 22.0
T_PULL0 = T_CHOPS[-1] + 0.4
T_PULL1 = T_PULL0 + 0.8
T_BANNER = T_PULL1 - 0.25
DUR = T_PULL1 + 2.0
assert DUR <= 14.0, DUR

rng = np.random.default_rng(17)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def cuts_done(j, t):
    return sum(1 for ev in EVENTS if ev[1] == j and t >= ev[0])


def event_time(j, k):
    for ev in EVENTS:
        if ev[1] == j and ev[2] == k:
            return ev[0]


# ================================================================ pieces
class Piece:
    def __init__(self, j, a, b, k=None):
        self.j, self.a, self.b, self.k = j, a, b, k
        xs = list(np.linspace(a, b, 7)) + ([0.0] if a < 0 < b else [])
        pts = []
        for x in xs:
            rr = math.sqrt(max(R * R - x * x, 0.0))
            for q in range(40):
                u = q / 40 * 2 * math.pi
                pts.append((x, rr * math.cos(u), rr * math.sin(u)))
        self.bpts = np.array(pts)
        if k is None:
            return
        self.t_free = event_time(j, min(k + 1, NCUT))
        self.phi_f = math.radians(90 + rng.normal(0, 2.5))
        self.yaw = math.radians(rng.normal(0, 6))
        self.dz = rng.normal(0, 7)
        self.lift = 0.0 if k == 0 else rng.uniform(6, 13)
        Rm = self.orient(self.phi_f, 0.0)
        pf = self.bpts @ Rm.T
        self.dx_final = b - 0.2 * TH - pf[:, 0].min() + rng.uniform(-3, 6)

    @staticmethod
    def orient(phi, yaw):
        c, s = math.cos(phi), math.sin(phi)
        Rz = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1.0]])
        cy_, sy_ = math.cos(yaw), math.sin(yaw)
        Ry = np.array([[cy_, 0, sy_], [0, 1, 0], [-sy_, 0, cy_]])
        return Ry @ Rz

    def pose(self, t):
        tr = t - self.t_free - 0.02
        if tr < 0:
            return None
        df = 0.32
        if tr < df:
            e = (tr / df) ** 2
            phi, land = self.phi_f * e, 0.0
        else:
            kk = tr - df
            e = 1.0
            phi = self.phi_f - math.radians(6) * math.exp(-kk * 13) * abs(math.sin(kk * 28))
            land = ease_out(kk / 0.25)
        Rm = self.orient(phi, self.yaw * land)
        ymin = -(self.bpts @ Rm.T)[:, 1].min()
        Ty = max(lerp(R, ymin + self.lift, e), ymin)
        Tw = np.array([CX[self.j] + self.dx_final * e, Ty, self.dz * land])
        static = tr > df + 0.45
        return Rm, Tw, static


PIECES = []
for _j in (1, 0):
    for _k in range(NCUT + 1):
        _b = R - _k * TH
        _a = -R if _k == NCUT else R - (_k + 1) * TH
        PIECES.append(Piece(_j, _a, _b, _k))
PIECES.sort(key=lambda p: (p.t_free, -p.k))


# ================================================================ ray tracer
SS, OUTS = 3.2, 1.6                            # supersample px/unit, output px/unit
_skin_noise = smooth_noise(256, 512, 24, 48, 61)
_flesh_noise = smooth_noise(512, 512, 40, 40, 62)


def make_seed_tex(size=512):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    sector = 2 * math.pi / 5
    for loc in range(5):
        mid = (loc + 0.5) * sector
        for _ in range(8):
            a = mid + rng.uniform(-0.32, 0.32) * sector
            q = rng.uniform(0.34, 0.62)
            sx, sy = c + math.cos(a) * q * c, c + math.sin(a) * q * c
            ln, wd = 0.055 * c, 0.032 * c
            ori = a + rng.normal(0, 0.4)
            pts = []
            for s in range(14):
                u = s / 14 * 2 * math.pi
                lx, ly = math.cos(u) * ln, math.sin(u) * wd
                pts.append((sx + lx * math.cos(ori) - ly * math.sin(ori), sy + lx * math.sin(ori) + ly * math.cos(ori)))
            d.polygon(pts, fill=(246, 222, 150, 245), outline=(214, 160, 80, 255))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(1.2)), np.float32)


SEED_TEX = make_seed_tex()


def flesh_color(Pl, j, diff, spec):
    x, y, zz = Pl[:, 0], Pl[:, 1], Pl[:, 2]
    rmax = np.sqrt(np.maximum(R * R - x * x, 1.0))
    q = np.clip(np.sqrt(y * y + zz * zz) / rmax, 0, 1)
    ph = np.arctan2(zz, y) + OFF[j]
    locm = np.clip((0.68 - np.abs(x) / R) / 0.22, 0, 1)
    sector = 2 * math.pi / 5
    fr = np.mod(ph / sector, 1.0)
    dist = np.minimum(fr, 1 - fr) * sector
    lin = q * np.sin(np.minimum(dist, math.pi / 2))
    sw = 0.045 + 0.035 * q
    septum = smoothstep(sw + 0.018, sw, lin)
    locreg = smoothstep(0.17, 0.22, q) * smoothstep(0.77, 0.72, q) * (1 - septum)
    lw = (locreg * locm)[:, None]
    peri = np.array([224, 54, 38.0]) * (1 - smoothstep(0.72, 1.0, q))[:, None] + \
        np.array([200, 30, 22.0]) * smoothstep(0.72, 1.0, q)[:, None]
    jelly = np.array([240, 118, 62.0])
    col = peri * (1 - lw) + jelly * lw
    corew = (smoothstep(0.22, 0.16, q) * locm)[:, None]
    col = col * (1 - corew) + np.array([236, 96, 66.0]) * corew
    # seeds
    ang = ph - OFF[j]
    u = np.clip(((q * np.cos(ang) + 1) / 2 * 511).astype(int), 0, 511)
    v = np.clip(((q * np.sin(ang) + 1) / 2 * 511).astype(int), 0, 511)
    st = SEED_TEX[v, u]
    sa = st[:, 3:4] / 255 * lw
    col = col * (1 - sa) + st[:, :3] * sa
    rim = smoothstep(0.958, 0.985, q)[:, None]
    col = col * (1 - rim) + np.array([168, 20, 14.0]) * rim
    nu = np.clip(((y / R + 1) / 2 * 511).astype(int), 0, 511)
    nv = np.clip(((zz / R + 1) / 2 * 511).astype(int), 0, 511)
    col *= (0.92 + 0.14 * _flesh_noise[nv, nu])[:, None]
    col = col * (0.6 + 0.52 * diff)[:, None] + ((spec ** 40) * (60 + 110 * lw[:, 0]))[:, None]
    return col


def skin_color(nl, nw, j, diff, spec):
    th = np.arccos(np.clip(nl[:, 0], -1, 1))
    ps = np.arctan2(nl[:, 2], nl[:, 1])
    nu = np.clip(((ps + math.pi) / (2 * math.pi) * 511).astype(int), 0, 511)
    nv = np.clip((th / math.pi * 255).astype(int), 0, 255)
    nz = _skin_noise[nv, nu]
    col = np.array([200, 28, 18.0]) * (0.9 + 0.18 * nz)[:, None]
    sh = (smoothstep(0.75, 0.2, th) * 0.55)[:, None]
    col = col * (1 - sh) + np.array([206, 82, 28.0]) * sh
    lim = 0.09 + 0.33 * np.clip(np.cos(5 * (ps + OFF[j])), 0, 1) ** 3
    leaf = smoothstep(lim + 0.015, lim - 0.015, th)
    stem = smoothstep(0.065, 0.045, th)
    lf = leaf[:, None]
    leaf_col = np.array([52, 112, 38.0]) * (0.75 + 0.25 * smoothstep(lim, lim - 0.12, th))[:, None]
    col = col * (1 - lf) + leaf_col * lf
    col = col * (1 - stem[:, None]) + np.array([104, 142, 58.0]) * stem[:, None]
    ao = 1 - 0.32 * np.clip(-nw[:, 1], 0, 1) ** 2
    gloss = 1 - 0.85 * leaf
    col = col * ((0.3 + 0.82 * diff) * ao)[:, None] + ((spec ** 90 * 230 + spec ** 14 * 32) * gloss)[:, None]
    return col


def render_piece(p, Rm, Tw):
    pts = p.bpts @ Rm.T + Tw
    pr = pts @ M.T
    x0, y0 = pr.min(0) - 3
    x1, y1 = pr.max(0) + 3
    w = int(math.ceil((x1 - x0) * OUTS)) * 2
    h = int(math.ceil((y1 - y0) * OUTS)) * 2
    px = x0 + (np.arange(w) + 0.5) / SS
    py = y0 + (np.arange(h) + 0.5) / SS
    PX, PY = np.meshgrid(px, py)
    P0 = np.stack([PX, -PY / CY, np.zeros_like(PX)], -1)
    Pl0 = (P0 - Tw) @ Rm
    dl = Rm.T @ D_RAY
    A = dl @ dl
    B = 2 * (Pl0 @ dl)
    C = (Pl0 ** 2).sum(-1) - R * R
    disc = B * B - 4 * A * C
    sq = np.sqrt(np.maximum(disc, 0))
    t1, t2 = (-B - sq) / (2 * A), (-B + sq) / (2 * A)
    if abs(dl[0]) > 1e-9:
        ta, tb = (p.a - Pl0[..., 0]) / dl[0], (p.b - Pl0[..., 0]) / dl[0]
        lo, hi = np.minimum(ta, tb), np.maximum(ta, tb)
    else:
        ins = (Pl0[..., 0] >= p.a) & (Pl0[..., 0] <= p.b)
        lo = np.where(ins, -1e9, 1e9)
        hi = np.where(ins, 1e9, -1e9)
    lo2, hi2 = np.maximum(t1, lo), np.minimum(t2, hi)
    valid = (disc > 0) & (lo2 < hi2)
    img = np.zeros((h, w, 4), np.float32)
    if valid.any():
        tv = hi2[valid]
        Pl = Pl0[valid] + tv[:, None] * dl
        face = (hi < t2)[valid]
        nl = Pl / R
        fsign = 1.0 if dl[0] > 0 else -1.0
        nl_face = np.zeros_like(nl)
        nl_face[:, 0] = fsign
        nl_all = np.where(face[:, None], nl_face, nl)
        nw = nl_all @ Rm.T
        diff = np.clip(nw @ LIGHT, 0, 1)
        spec = np.clip(nw @ HV, 0, 1)
        col = np.zeros((len(tv), 3))
        if (~face).any():
            s = ~face
            col[s] = skin_color(nl[s], nw[s], p.j, diff[s], spec[s])
        if face.any():
            col[face] = flesh_color(Pl[face], p.j, diff[face], spec[face])
        img[valid, :3] = col
        img[valid, 3] = 255
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")
    im = im.resize((w // 2, h // 2), Image.BOX)
    return im, np.array([x0, y0])


# ================================================================ knife timing
def knife_a(t):
    xs = [ev[3] for ev in EVENTS]
    tc = [ev[0] for ev in EVENTS]
    n = len(xs)
    if t < tc[0] - 0.28:
        p = clamp(t / 0.7)
        return xs[0], H_UP + 900 * (1 - ease_out(p)) + 6 * math.sin(t * 6)
    x = xs[0]
    for i in range(n):
        prev_iv = tc[i] - tc[i - 1] if i else 0.5
        next_iv = tc[i + 1] - tc[i] if i + 1 < n else 0.6
        dd = 0.28 if i == 0 else min(0.14, 0.45 * prev_iv)
        du = min(0.2, 0.5 * next_iv)
        s, e = tc[i] - dd, tc[i] + HOLD + du
        nx = xs[i + 1] if i + 1 < n else xs[i]
        if t < s:
            return xs[i], H_UP
        if t < tc[i]:
            pp = (t - s) / dd
            return xs[i], H_UP * (1 - pp * pp)
        if t < tc[i] + HOLD:
            return xs[i], 0.0
        if t < e:
            pp = (t - tc[i] - HOLD) / du
            return lerp(xs[i], nx, ease(pp)), H_UP * ease_out(pp)
        x = nx
    pp = (t - (T_A_LAST + 0.3)) / 0.7
    return x, H_UP + 4500 * clamp(pp) ** 2


def knife_a_dd(i):
    tc = EVENTS[i][0]
    prev_iv = tc - EVENTS[i - 1][0] if i else 0.5
    return 0.28 if i == 0 else min(0.14, 0.45 * prev_iv)


class RowInfo:
    pass


ROW = RowInfo()


def chop_pos(c):
    return (ROW.xl if c % 2 == 0 else ROW.xr), Z_LINES[c // 2]


def knife_b(t):
    """-> (x, z, edge height) or None when the front-view knife is off screen."""
    if t < T_B0 - 0.6:
        return None
    if t < T_B0 - 0.12:
        x, zl = chop_pos(0)
        p = (t - (T_B0 - 0.6)) / 0.48
        return x, zl, H_B + 1600 * (1 - ease_out(p))
    for c, tc in enumerate(T_CHOPS):
        dd, du = 0.12, 0.2
        s, e = tc - dd, tc + HOLD + du
        x, zl = chop_pos(c)
        nx, nz = chop_pos(c + 1) if c + 1 < len(T_CHOPS) else (x, zl)
        if t < s:
            return x, zl, H_B
        if t < tc:
            pp = (t - s) / dd
            return x, zl, H_B * (1 - pp * pp)
        if t < tc + HOLD:
            return x, zl, 0.0
        if t < e:
            pp = (t - tc - HOLD) / du
            return lerp(x, nx, ease(pp)), lerp(zl, nz, ease(pp)), H_B * ease_out(pp)
    x, zl = chop_pos(len(T_CHOPS) - 1)
    pp = (t - (T_CHOPS[-1] + 0.3)) / 0.6
    if pp > 1:
        return None
    return x, zl, H_B + 2200 * clamp(pp) ** 2


def count_at(t):
    n = 0
    for j in (0, 1):
        c = cuts_done(j, t)
        n += 0 if c == 0 else c + 1
    return n + 10 * sum(1 for tc in T_CHOPS if t >= tc)


ALL_EVENT_T = sorted([ev[0] for ev in EVENTS] + T_CHOPS)


def last_event(t):
    past = [te for te in ALL_EVENT_T if te <= t]
    return past[-1] if past else None


# ================================================================ renderer
class Renderer:
    def __init__(self):
        print("building textures...", flush=True)
        self.board, self.bsc, self.bx0, self.by0 = make_board()
        self.board = self.board.convert("RGBA")
        self.knife, self.ksc, self.kz0, self.ky1, self.kout = make_knife()
        self.sprites = {}
        self.rem_pieces = {}
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        v = 1 - 0.42 * np.clip(np.hypot((xx - W / 2) / (W * 0.75), (yy - HC) / (H * 0.62)) - 0.35, 0, 1) ** 1.6
        self.vignette = v[..., None]
        self.yy = yy[:, :1]
        # final row extents -> phase B chop positions
        xs = []
        for p in PIECES:
            Rm, Tw, _ = p.pose(1e6)
            xs.append((p.bpts @ Rm.T + Tw)[:, 0])
        xs = np.concatenate(xs)
        ROW.x0, ROW.x1 = float(xs.min()), float(xs.max())
        span = ROW.x1 - ROW.x0
        ROW.xl, ROW.xr = ROW.x0 + span * 0.25, ROW.x0 + span * 0.75
        ROW.xc = (ROW.x0 + ROW.x1) / 2
        print(f"row {ROW.x0:.0f}..{ROW.x1:.0f}", flush=True)
        # text
        white, gold = (255, 255, 255), (255, 70, 50)
        f_lab = ImageFont.truetype(FONT_LAT, 74)
        f_hk = ImageFont.truetype(FONT_LAT, 60)
        f_num = ImageFont.truetype(FONT_LAT, 250)
        f_bn = ImageFont.truetype(FONT_LAT, 132)
        f_sb = ImageFont.truetype(FONT_LAT, 58)
        f_plus = ImageFont.truetype(FONT_LAT, 96)
        thin = dict(stroke=3, stroke_fill=(20, 20, 20))
        big = dict(stroke=7, stroke_fill=(30, 20, 20))
        self.f_num = f_num
        self.e_tom = emoji("🍅", 120)
        self.label = hstack([emoji("🔪", 70), text_img("PIECES", f_lab, white)], 10)
        self.hook = hstack([text_img("Can 2 tomatoes make 100 pieces?", f_hk, white, **thin), emoji("🤔", 64)], 12)
        self.banner = hstack([text_img("100 PIECES!", f_bn, (255, 228, 80), **big), self.e_tom], -18)
        self.sub = text_img("From just TWO tomatoes", f_sb, white, **thin)
        self.plus = text_img("+10", f_plus, (255, 228, 80), **big)
        self.num_cache = {}
        self.precompute_camera()

    # -------------------------------------------------- camera
    def precompute_camera(self):
        self.cam = []
        cx = None
        for f in range(int(DUR * FPS) + 2):
            t = f / FPS
            kx, _ = knife_a(min(t, T_A_LAST + 0.3))
            z = lerp(1.85, 1.5, ease(t / 0.9))
            target = kx + 0.10 * W / z
            cx = target if cx is None else cx + (target - cx) * 0.2
            pb = ease((t - (T_A_LAST + 0.35)) / 0.9)
            kb = knife_b(t)
            bx = lerp(ROW.xc, kb[0], 0.35) if kb else ROW.xc
            camx = lerp(cx, bx, pb)
            camy = lerp(-CY * R, -CY * 60, pb)
            z = lerp(z, 1.12, pb)
            pp = ease((t - T_PULL0) / (T_PULL1 - T_PULL0))
            camx = lerp(camx, ROW.xc, pp)
            z = lerp(z, 0.8, pp)
            self.cam.append((camx, camy, z))
        # smooth phase-B pan
        arr = np.array(self.cam)
        for i in range(1, len(arr)):
            if i / FPS > T_A_LAST + 0.35:
                arr[i, 0] = arr[i - 1, 0] + (arr[i, 0] - arr[i - 1, 0]) * 0.25
        self.cam = [tuple(r) for r in arr]

    def scr(self, p, cam, z, shake):
        return np.array([(p[0] - cam[0]) * z + W / 2 + shake[0], (p[1] - cam[1]) * z + HC + shake[1]])

    # -------------------------------------------------- pieces
    def sprite(self, key, piece, Rm, Tw):
        if key is not None and key in self.sprites:
            return self.sprites[key]
        sp = render_piece(piece, Rm, Tw)
        if key is not None:
            self.sprites[key] = sp
        return sp

    def rem_piece(self, j, a, b):
        key = (j, round(a, 3), round(b, 3))
        if key not in self.rem_pieces:
            self.rem_pieces[key] = Piece(j, a, b)
        return self.rem_pieces[key]

    def draw_sprite(self, dst, sp, cam, z, shake, offset=(0, 0)):
        im, origin = sp
        A = np.eye(2) * (z / OUTS)
        b = self.scr(origin, cam, z, shake) + np.array(offset)
        warp(dst, im, A, b)

    def draw_rem(self, dst, j, a, b, cam, z, shake):
        p = self.rem_piece(j, a, b)
        sp = self.sprite(("rem", j, round(a, 3), round(b, 3)), p, np.eye(3), np.array([CX[j], R, 0.0]))
        self.draw_sprite(dst, sp, cam, z, shake)

    def piece_sprite(self, p, t):
        pose = p.pose(t)
        if pose is None:
            return None
        Rm, Tw, static = pose
        key = ("final", p.j, p.k) if static else None
        return self.sprite(key, p, Rm, Tw), Rm, Tw

    # -------------------------------------------------- knives
    def draw_knife_a(self, dst, xk, yk, cam, z, shake):
        sc = self.ksc
        du = z * (M @ np.array([0, 0, 1.0])) / sc
        dv = z * (M @ np.array([0, -1.0, 0])) / sc
        origin = M @ np.array([xk, yk + self.ky1, self.kz0])
        warp(dst, self.knife, np.column_stack([du, dv]), self.scr(origin, cam, z, shake))

    def draw_knife_b(self, dst, xb, zb, yk, cam, z, shake):
        sc, s = self.ksc, KB_SCALE
        du = z * (M @ np.array([s, 0, 0])) / sc
        dv = z * (M @ np.array([0, -s, 0])) / sc
        mid = (178 - 352) / 2
        origin = M @ np.array([xb + (self.kz0 - mid) * s, yk + self.ky1 * s, zb])
        warp(dst, self.knife, np.column_stack([du, dv]), self.scr(origin, cam, z, shake))

    # -------------------------------------------------- frame
    def frame(self, t, f):
        cx, cy_, z = self.cam[min(f, len(self.cam) - 1)]
        cam = (cx, cy_)
        shake = np.zeros(2)
        le = last_event(t)
        if le is not None and t - le < 0.14:
            dt = t - le
            shake = np.array([math.sin(dt * 90) * 1.5, math.sin(dt * 70) * 5]) * math.exp(-dt * 25) * z

        frame = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        warp(frame, self.board, np.eye(2) * (z / self.bsc), self.scr(np.array([self.bx0, self.by0]), cam, z, shake))

        phase_b = t >= T_A_LAST + 0.6
        sprites = []                                  # (piece, sprite, Rm, Tw)
        for p in PIECES:
            r_ = self.piece_sprite(p, t)
            if r_ is not None:
                sprites.append((p,) + r_)

        # ---- contact shadows
        q = 4
        sh = Image.new("L", (W // q, H // q), 0)
        sd = ImageDraw.Draw(sh)

        def S(P):
            s_ = self.scr(M @ np.asarray(P, float), cam, z, shake) / q
            return (s_[0], s_[1])

        def footprint(pts_w, val):
            cxw, czw = pts_w[:, 0].mean(), pts_w[:, 2].mean()
            rx = (pts_w[:, 0].max() - pts_w[:, 0].min()) / 2 * 0.92
            rz = (pts_w[:, 2].max() - pts_w[:, 2].min()) / 2 * 0.92
            poly = [S((cxw + 14 + rx * math.cos(u), 0, czw - 12 + rz * math.sin(u))) for u in np.linspace(0, 6.283, 28)]
            sd.polygon(poly, fill=val)

        for p, sp, Rm, Tw in sprites:
            footprint(p.bpts @ Rm.T + Tw, 150)
        for j in (0, 1):
            c = cuts_done(j, t)
            if c < NCUT:
                footprint(np.array([[CX[j] - R * 0.8, 0, 0], [CX[j] + R * 0.8 - c * TH, 0, 0],
                                    [CX[j], 0, -R * 0.8], [CX[j], 0, R * 0.8]]), 185)
        if not phase_b:
            xk, yk = knife_a(t)
            fade = math.exp(-max(0.0, yk) / 420)
            kp = []
            for lz, ly in self.kout:
                P = np.array([xk, yk + ly, lz])
                kp.append(S(P - (P[1] / LIGHT[1]) * LIGHT))
            sd.polygon(kp, fill=int(140 * fade))
        sh = sh.filter(ImageFilter.GaussianBlur(float(2.5 * z + 1))).resize((W, H), Image.BILINEAR)
        arr = np.asarray(frame, np.float32)[..., :3] * (1 - np.asarray(sh, np.float32)[..., None] / 255 * 0.6)
        frame = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")

        if not phase_b:
            self.draw_phase_a(frame, t, sprites, cam, z, shake)
        else:
            self.draw_phase_b(frame, t, sprites, cam, z, shake)

        # ---- juice droplets
        dl = ImageDraw.Draw(frame, "RGBA")
        for idx, (te, j, k, xw) in enumerate(EVENTS):
            dt = t - te
            if 0 <= dt < 0.5:
                r_ = np.random.default_rng(300 + idx)
                for _ in range(10):
                    vx, vy = r_.uniform(-260, 340), r_.uniform(-640, -260)
                    sp_ = self.scr(np.array([xw + vx * dt, -CY * R * 1.6 + vy * dt + 1300 * dt * dt]), cam, z, shake)
                    rad = r_.uniform(2.0, 5.0) * z
                    al = int(210 * (1 - dt / 0.5))
                    dl.ellipse([sp_[0] - rad, sp_[1] - rad, sp_[0] + rad, sp_[1] + rad], fill=(235, 60, 40, al))
                    dl.ellipse([sp_[0] - rad * 0.45, sp_[1] - rad * 0.6, sp_[0], sp_[1] - rad * 0.2],
                               fill=(255, 220, 210, al))

        # ---- depth of field, vignette, grade
        img = np.asarray(frame, np.float32)[..., :3]
        small = frame.convert("RGB").resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2.2))
        blur = np.asarray(small.resize((W, H), Image.BILINEAR), np.float32)
        focus = 470 * z / 1.6 + 120
        dof = np.clip((np.abs(self.yy - HC) - focus) / 380, 0, 1) * clamp((z - 0.6) / 1.0)
        img = img * (1 - dof[..., None]) + blur * dof[..., None]
        img = img * self.vignette
        img = (img - 128) * 1.06 + 128 + np.array([4, 1, -3])
        frame = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
        self.draw_ui(frame, t)
        return frame.convert("RGB")

    def draw_phase_a(self, frame, t, sprites, cam, z, shake):
        xk, yk = knife_a(t)
        n_done = sum(1 for ev in EVENTS if t >= ev[0])
        nxt = EVENTS[n_done] if n_done < len(EVENTS) else None
        standing = []
        for p, sp, Rm, Tw in sprites:
            if t - p.t_free < 0.17:
                standing.append(sp)
            else:
                self.draw_sprite(frame, sp, cam, z, shake)
        split = None
        rems = []
        for j in (0, 1):
            c = cuts_done(j, t)
            if c >= NCUT:
                continue
            right = R - c * TH
            if nxt is not None and nxt[1] == j and abs(xk - nxt[3]) < 0.5:
                cut_local = nxt[3] - CX[j]
                rems.append((j, -R, cut_local))
                split = (j, cut_local, right)
            else:
                rems.append((j, -R, right))
        for j, a, b in rems:
            self.draw_rem(frame, j, a, b, cam, z, shake)
        self.draw_knife_a(frame, xk, yk, cam, z, shake)
        if split:
            self.draw_rem(frame, split[0], split[1], split[2], cam, z, shake)
        for sp in standing:
            self.draw_sprite(frame, sp, cam, z, shake)

    def draw_phase_b(self, frame, t, sprites, cam, z, shake):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for p, sp, Rm, Tw in sprites:
            self.draw_sprite(layer, sp, cam, z, shake)
        la = np.array(layer)
        yb = 22.0
        ys = [int(round(self.scr(np.array([0, -CY * yb + KY * zl]), cam, z, shake)[1])) for zl in Z_LINES]
        # cut marks for finished half-chops
        for c, tc in enumerate(T_CHOPS):
            if t < tc:
                break
            x, zl = chop_pos(c)
            xa = int(self.scr(np.array([x - 345 * KB_SCALE / 1.3 - KX * zl, 0]), cam, z, shake)[0])
            xb = int(self.scr(np.array([x + 345 * KB_SCALE / 1.3 - KX * zl, 0]), cam, z, shake)[0])
            y = ys[c // 2]
            xa, xb = max(xa, 0), min(xb, W)
            y0_, y1_ = max(y - 2, 0), min(y + 2, H)
            if xb > xa and y1_ > y0_:
                reg = la[y0_:y1_, xa:xb]
                m = reg[..., 3:4] > 0
                reg[..., :3] = np.where(m, (reg[..., :3] * 0.35 + np.array([120, 12, 8]) * 0.65).astype(np.uint8),
                                        reg[..., :3])
        layer = Image.fromarray(la, "RGBA")
        # strips and their offsets
        bounds = [0] + ys + [H]
        kb = knife_b(t)
        if kb is not None:
            kline = int(np.argmin([abs(kb[1] - zl) for zl in Z_LINES]))
        else:
            kline = 3
        strips = []
        for s in range(5):
            dz = 0.0
            for jl in range(4):
                e = ease_out((t - (T_CHOPS[2 * jl + 1] + 0.03)) / 0.3)
                dz += (-GAP if s <= jl else GAP) * e
            off = (-KX * dz * z, KY * dz * z)
            y0_, y1_ = bounds[s], bounds[s + 1]
            if y1_ <= y0_:
                continue
            strips.append((s, layer.crop((0, y0_, W, y1_)), (int(round(off[0])), int(round(y0_ + off[1])))))
        for s, im, (ox, oy) in strips:
            if s <= kline:
                frame.alpha_composite(im, (0, 0)) if False else self._paste(frame, im, ox, oy)
        if kb is not None:
            self.draw_knife_b(frame, kb[0], kb[1], kb[2], cam, z, shake)
        for s, im, (ox, oy) in strips:
            if s > kline:
                self._paste(frame, im, ox, oy)

    @staticmethod
    def _paste(dst, im, x, y):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + im.width, dst.width), min(y + im.height, dst.height)
        if x1 <= x0 or y1 <= y0:
            return
        dst.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

    # -------------------------------------------------- UI
    def num_img(self, n, color):
        key = (n, color)
        if key not in self.num_cache:
            self.num_cache[key] = text_img(str(n), self.f_num, color, stroke=5, stroke_fill=(25, 25, 25))
        return self.num_cache[key]

    def draw_ui(self, frame, t):
        if t < 2.2:
            paste_center(frame, self.hook, W / 2, 200, 1.0, clamp(t / 0.3) * clamp((2.2 - t) / 0.4))
        app = ease_out(t / 0.45)
        cy_ = 470 - (1 - app) * 80
        panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        pw, ph = 580, 400
        pd.rounded_rectangle([W / 2 - pw / 2, cy_ - ph / 2, W / 2 + pw / 2, cy_ + ph / 2], radius=60,
                             fill=(28, 12, 10, int(150 * app)), outline=(255, 95, 70, int(210 * app)), width=5)
        frame.alpha_composite(panel)
        paste_center(frame, self.label, W / 2, cy_ - 118, 1.0, app)
        n = count_at(t)
        le = last_event(t)
        pop = math.exp(-(t - le) * 11) if le is not None else 0.0
        col = (255, 150, 120) if pop > 0.35 else (255, 255, 255)
        paste_center(frame, self.num_img(n, col), W / 2, cy_ + 55, 1.0 + 0.32 * pop, app)
        for tc in T_CHOPS:
            dt = t - tc
            if 0 <= dt < 0.38:
                paste_center(frame, self.plus, W / 2 + 330, cy_ + 20 - dt * 160, 0.8 + 0.3 * ease_out(dt / 0.15),
                             clamp((0.38 - dt) / 0.15))
        if t > T_BANNER:
            p = (t - T_BANNER) / 0.45
            s = 0.4 + 0.6 * ease_out(p) + (0.08 * math.sin(p * math.pi) if p < 1 else 0)
            paste_center(frame, self.banner, W / 2, 890, s, clamp(p * 2))
            if t > T_BANNER + 0.35:
                paste_center(frame, self.sub, W / 2, 1030, 1.0, clamp((t - T_BANNER - 0.35) / 0.3))


# ================================================================ audio
def make_audio(path):
    n = int(DUR * SR) + SR
    out = np.zeros(n)
    r = np.random.default_rng(9)

    def add(sig, t, gain=1.0):
        i = int(t * SR)
        if 0 <= i < n:
            sig = sig[: n - i]
            out[i:i + len(sig)] += sig * gain

    def knock(pitch, ln=0.14):
        k = int(ln * SR)
        tt = np.arange(k) / SR
        return (np.sin(2 * np.pi * 150 * pitch * tt) * np.exp(-tt * 38) +
                0.6 * np.sin(2 * np.pi * 265 * pitch * tt) * np.exp(-tt * 55) +
                0.35 * np.sin(2 * np.pi * 430 * pitch * tt) * np.exp(-tt * 80)) * 0.75 + \
            r.normal(0, 1, k) * np.exp(-tt * 600) * 0.25

    def squish(ln):
        m = max(int(ln * SR), 200)
        nz = bandpass(r.normal(0, 1, m + 2000), 350, 3200)[:m]
        env = np.sin(np.linspace(0, np.pi, m)) ** 0.7 * (0.7 + 0.3 * np.sin(np.linspace(0, 40, m)))
        return nz / (np.abs(nz).max() + 1e-9) * env

    for i, (tc, j, k, xw) in enumerate(EVENTS):
        dd = knife_a_dd(i)
        te = tc - dd * (1 - math.sqrt(1 - 2 * R / H_UP))
        add(squish(tc - te + 0.02), te, 0.4)
        add(knock(r.uniform(0.92, 1.08)), tc, 0.8)
        kk = int(0.06 * SR)
        t2 = np.arange(kk) / SR
        add(np.sin(2 * np.pi * r.uniform(260, 360) * t2) * np.exp(-t2 * 60) + r.normal(0, 0.3, kk) * np.exp(-t2 * 200),
            tc + 0.34, 0.2)
    for c, tc in enumerate(T_CHOPS):
        add(squish(0.07), tc - 0.06, 0.45)
        add(knock(r.uniform(0.85, 0.95), 0.18), tc, 1.0)
        kk = int(0.05 * SR)
        t2 = np.arange(kk) / SR
        add(np.sin(2 * np.pi * (1200 + 90 * c) * t2) * np.exp(-t2 * 90), tc + 0.02, 0.12)
    for ta, tb in ((T_A_LAST + 0.35, T_A_LAST + 1.25), (T_PULL0, T_PULL1)):
        m = int((tb - ta) * SR)
        wn = bandpass(r.normal(0, 1, m), 300, 2500)
        add(wn / np.abs(wn).max() * np.sin(np.linspace(0, np.pi, m)) ** 2, ta, 0.18)
    m = int(1.8 * SR)
    t2 = np.arange(m) / SR
    chime = sum(np.sin(2 * np.pi * fq * t2) * np.exp(-t2 * d) * a
                for fq, d, a in ((1046.5, 3, 0.6), (1318.5, 3.5, 0.5), (1568, 4, 0.45), (2093, 6, 0.25)))
    add(chime, T_BANNER, 0.3)
    add(chime, T_BANNER + 0.12, 0.12)
    out += bandpass(r.normal(0, 1, n), 80, 1200) * 0.004
    out = out[: int(DUR * SR)]
    out = np.tanh(out / (np.abs(out).max() + 1e-9) * 1.4) * 0.9
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


# ================================================================ main
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rd = Renderer()
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT_DIR, "preview")
        os.makedirs(pdir, exist_ok=True)
        ts = [0.5, 0.95, 1.2, 2.5, 4.5, T_A_LAST + 0.5, T_B0 - 0.1, T_CHOPS[2] + 0.05, T_CHOPS[5] - 0.05,
              T_CHOPS[7] + 0.4, DUR - 0.4]
        for t in ts:
            rd.frame(t, int(t * FPS)).save(os.path.join(pdir, f"f_{t:05.2f}.png"))
            print("preview", round(t, 2), flush=True)
        return
    wav = os.path.join(OUT_DIR, "_audio.wav")
    make_audio(wav)
    out = os.path.join(OUT_DIR, "tomato_100_pieces_short_en.mp4")
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
    print("wrote", out, f"({DUR:.1f}s, {count_at(DUR)} pieces)")


if __name__ == "__main__":
    main()
