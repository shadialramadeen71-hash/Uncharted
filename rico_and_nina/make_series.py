#!/usr/bin/env python3
"""
RICO & NINA — "Waiting for GTA VI"   (v2: human proportions + moving camera)

An original animated couple of GTA VI superfans, rendered entirely in code.

What's new compared with ../game_night:
  * Human proportions (~7.5 heads tall) built on a skeleton rig with
    2-bone IK for arms and legs, tapered limbs and cel shading.
  * Realistic-ish faces: almond eyes with irises, eyelids, eyebrows,
    nose line, lips, stubble / curls.
  * A moving camera: per-beat dolly / pan / zoom between shots, handheld
    drift, tracking shots, whip-pans with motion blur, impact shakes.
  * Parallax background layers (sky / far / mid / ground).
  * Walk, run, skate, sit, fall poses; props (donut, skateboard, seagull).
  * 6 episodes, each <= 15 s, English voices.

Usage:
    python3 make_series.py --shorts     # 1080x1920 YouTube Shorts
    python3 make_series.py              # 1280x720 landscape
    python3 make_series.py --shorts 4   # one episode
"""
import math
import os
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cartoon"))
import make_episodes as base  # noqa: E402  shared Pen / TTS / sfx engine
from make_episodes import INK, Cam, Pen, ease, lerp, poof, smoke  # noqa: E402

FPS, SR, SS = base.FPS, base.SR, base.SS
TITLE_DUR = 1.5
MAX_LEN = 15.0
GROUND = 660
SHORTS = False
OUT_DIR = os.path.join(HERE, "output")

base.VOICES["r"] = ("en/en_US/ryan/high/en_US-ryan-high", 0.97, 1.05, 0.95)          # Rico
base.VOICES["n"] = ("en/en_US/amy/medium/en_US-amy-medium", 1.04, 1.02, 0.95)          # Nina
base.VOICES["o"] = ("en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium", 0.88, 1.0, 1.08)  # Grandma Rosa
base.VOICES["d"] = ("en/en_US/joe/medium/en_US-joe-medium", 0.82, 1.12, 1.05)          # Officer Duke


def set_format(shorts):
    global SHORTS, OUT_DIR
    SHORTS = shorts
    base.W, base.H = (1080, 1920) if shorts else (1280, 720)
    OUT_DIR = os.path.join(HERE, "output", "shorts") if shorts else os.path.join(HERE, "output")


def darker(c, k=0.82):
    return tuple(int(v * k) for v in c)


def lp(a, b, k):
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))


def wtext(pn, x, y, text, size, fill, stroke=3, stroke_fill=INK):
    px, py = pn.c.p(x, y)
    pn.d.text((px, py), text, font=base.font(max(6, int(pn.c.s(size)))), fill=fill, anchor="mm",
              stroke_width=max(1, int(pn.c.s(stroke))), stroke_fill=stroke_fill)


# --------------------------------------------------------------------------
# Sound effects
# --------------------------------------------------------------------------
def sfx(name, dur=1.0):
    t = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(5)
    if name == "engine":
        ph = np.cumsum(48 + 6 * np.sin(2 * np.pi * 0.7 * t)) / SR
        return (2 * (ph % 1) - 1) * 0.18 * np.minimum(1, t * 8) * np.minimum(1, (dur - t) * 8)
    if name == "vroom":
        ph = np.cumsum(50 + 260 * (1 - np.exp(-t * 3))) / SR
        return (2 * (ph % 1) - 1) * 0.35 * np.minimum(1, t * 20) * np.exp(-np.maximum(0, t - dur + 0.3) * 8)
    if name == "tick":
        tt = t[: int(0.05 * SR)]
        return np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 90) * 0.6
    if name == "ding":
        tt = t[: int(0.6 * SR)]
        return (np.sin(2 * np.pi * 1760 * tt) + 0.5 * np.sin(2 * np.pi * 2640 * tt)) * np.exp(-tt * 7) * 0.35
    if name == "wind":
        n = np.convolve(rng.standard_normal(len(t)), np.ones(60) / 60, mode="same") * 6
        return n * np.sin(np.pi * t / dur) * 0.6
    if name == "squawk":
        tt = t[: int(0.45 * SR)]
        f = 900 + 500 * np.sin(2 * np.pi * 9 * tt)
        ph = np.cumsum(f) / SR
        return (2 * (ph % 1) - 1) * 0.3 * np.sin(np.pi * tt / tt[-1])
    if name == "thud":
        tt = t[: int(0.4 * SR)]
        n = np.convolve(rng.standard_normal(len(tt)), np.ones(30) / 30, mode="same") * 3
        return (np.sin(2 * np.pi * (70 - 30 * tt) * tt) + n) * np.exp(-tt * 12) * 0.9
    if name == "trombone":   # sad "wah wah wah waaah"
        out = []
        for f, d in [(392, .28), (370, .28), (349, .28), (330, .8)]:
            tt = np.arange(int(d * SR)) / SR
            vib = 1 + (0.012 * np.sin(2 * np.pi * 6 * tt) if d > .5 else 0)
            ph = np.cumsum(f * vib) / SR
            out.append((2 * (ph % 1) - 1) * 0.22 * np.minimum(1, tt * 25) * np.minimum(1, (d - tt) * 12))
        return np.concatenate(out)
    if name == "blip":
        tt = t[: int(0.12 * SR)]
        return np.sign(np.sin(2 * np.pi * 880 * tt)) * 0.15 * np.exp(-tt * 20)
    if name == "intro":
        out = np.zeros(int(1.4 * SR))
        for i, (f, d) in enumerate([(220, .35), (277, .35), (330, .35), (440, .5)]):
            s = int(i * 0.3 * SR)
            tt = np.arange(int(d * SR)) / SR
            ph = f * tt
            note = ((2 * (ph % 1) - 1) * 0.12 + (2 * ((ph * 1.005) % 1) - 1) * 0.12) * np.exp(-tt * 2.5)
            out[s:s + len(note)] += note
        tb = np.arange(len(out)) / SR
        out += np.sin(2 * np.pi * 55 * tb) * 0.25 * np.exp(-((tb * 3.3) % 1) * 6)
        return out
    return base.sfx(name)


# --------------------------------------------------------------------------
# Rig: skeleton + transform (lets a whole character rotate, e.g. falling)
# --------------------------------------------------------------------------
def capsule(pn, a, b, ra, rb, col):
    pn.ellipse(a[0], a[1], ra, ra, col, 0)
    pn.ellipse(b[0], b[1], rb, rb, col, 0)
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-3:
        return
    nx, ny = -dy / L, dx / L
    pn.poly([(a[0] + nx * ra, a[1] + ny * ra), (b[0] + nx * rb, b[1] + ny * rb),
             (b[0] - nx * rb, b[1] - ny * rb), (a[0] - nx * ra, a[1] - ny * ra)], col, 0)


class Rig:
    def __init__(self, pn, pivot=(0, 0), rot=0.0, off=(0, 0)):
        self.pn = pn
        self.px, self.py = pivot
        self.ox, self.oy = off
        self.c, self.s = math.cos(rot), math.sin(rot)
        self.swap = abs(self.s) > 0.5

    def T(self, p):
        x, y = p[0] - self.px, p[1] - self.py
        return (self.px + x * self.c - y * self.s + self.ox, self.py + x * self.s + y * self.c + self.oy)

    def _r(self, rx, ry):
        return (ry, rx) if self.swap else (rx, ry)

    def ell(self, cx, cy, rx, ry, fill, ow=3):
        x, y = self.T((cx, cy))
        rx, ry = self._r(rx, ry)
        self.pn.ellipse(x, y, rx, ry, fill, ow)

    def blob(self, parts, fill, ow=3):
        P = []
        for cx, cy, rx, ry in parts:
            x, y = self.T((cx, cy))
            P.append((x, y) + self._r(rx, ry))
        self.pn.blob(P, fill, ow)

    def poly(self, pts, fill, ow=3):
        self.pn.poly([self.T(p) for p in pts], fill, ow)

    def line(self, pts, fill=INK, w=3):
        self.pn.line([self.T(p) for p in pts], fill, w)

    def chain(self, pts, radii, fill, ow=3, shade=True):
        P = [self.T(p) for p in pts]
        segs = list(zip(P[:-1], P[1:], radii[:-1], radii[1:]))
        if ow:
            for a, b, ra, rb in segs:
                capsule(self.pn, a, b, ra + ow, rb + ow, INK)
        for a, b, ra, rb in segs:
            capsule(self.pn, a, b, ra, rb, fill)
        if shade:
            sc = darker(fill, 0.86)
            for a, b, ra, rb in segs:
                dx, dy = b[0] - a[0], b[1] - a[1]
                L = math.hypot(dx, dy) or 1
                nx, ny = -dy / L, dx / L
                if nx < 0 or (abs(nx) < 1e-6 and ny < 0):
                    nx, ny = -nx, -ny
                capsule(self.pn, (a[0] + nx * ra * 0.45, a[1] + ny * ra * 0.45),
                        (b[0] + nx * rb * 0.45, b[1] + ny * rb * 0.45), ra * 0.5, rb * 0.5, sc)


def ik(a, b, l1, l2, bend):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = max(abs(l1 - l2) + 1e-3, min(math.hypot(dx, dy), l1 + l2 - 1e-3))
    ang = math.atan2(dy, dx)
    k = max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))
    a1 = math.acos(k)
    mid = (a[0] + math.cos(ang) * d * 0.5, a[1] + math.sin(ang) * d * 0.5)
    best = None
    for c in (ang + a1, ang - a1):
        j = (a[0] + math.cos(c) * l1, a[1] + math.sin(c) * l1)
        score = (j[0] - mid[0]) * bend[0] + (j[1] - mid[1]) * bend[1]
        if best is None or score > best[0]:
            best = (score, j)
    j = best[1]
    ex, ey = b[0] - j[0], b[1] - j[1]
    e = math.hypot(ex, ey) or 1
    return j, (j[0] + ex / e * l2, j[1] + ey / e * l2)


RICO = dict(key="r", s=1.0, face=1, phase=0.0, skin=(232, 178, 138), hair=(62, 40, 26), iris=(96, 64, 32),
            top=(242, 106, 150), pattern=(255, 236, 120), bottoms=(204, 178, 124), long=False,
            shoes=(250, 250, 250), female=False, style="rico", sleeves="short", bulk=1.0, lean=0.0)
NINA = dict(key="n", s=0.93, face=-1, phase=1.7, skin=(168, 108, 76), hair=(204, 80, 44), iris=(70, 44, 24),
            top=(36, 182, 168), pattern=None, bottoms=(62, 100, 176), long=True,
            shoes=(226, 52, 60), female=True, style="nina", sleeves="none", bulk=1.0, lean=0.0)
# Grandma Rosa: retired, gray bun, round glasses, purple cardigan — secretly a pro gamer
ROSA = dict(key="o", s=0.86, face=-1, phase=0.7, skin=(240, 204, 178), hair=(214, 214, 222), iris=(70, 110, 150),
            top=(150, 92, 168), pattern=None, bottoms=(96, 74, 120), long=True,
            shoes=(120, 80, 50), female=True, style="rosa", sleeves="long", bulk=1.06, lean=0.07)
# Officer Duke: big mall security guard with a mustache and a cap
DUKE = dict(key="d", s=1.08, face=-1, phase=2.4, skin=(192, 136, 98), hair=(30, 26, 24), iris=(60, 40, 24),
            top=(44, 64, 116), pattern=None, bottoms=(36, 48, 86), long=True,
            shoes=(30, 30, 34), female=False, style="duke", sleeves="short", bulk=1.25, lean=0.0)
SPECS = {"r": RICO, "n": NINA, "o": ROSA, "d": DUKE}
DEFAULT_X = {"r": 520, "n": 770, "o": 960, "d": 1020}
NAMES = {"r": "RICO", "n": "NINA", "o": "GRANDMA ROSA", "d": "OFFICER DUKE"}
NAME_COL = {"r": (255, 140, 210), "n": (90, 230, 210), "o": (200, 170, 255), "d": (130, 180, 255)}


def arm_target(arms, legs, i, sx, f, ph, t, s, J):
    """Hand target relative to shoulder (scaled later) + elbow bend direction."""
    front = (sx == f)
    if arms == "rest" and legs == "walk":
        return (sx * 14 + f * math.sin(ph + (i + 1) * math.pi) * 42, 178), (-f * 0.3 + sx, 0.3)
    if arms == "rest" and legs == "run":
        return (sx * 6 + f * math.sin(ph + (i + 1) * math.pi) * 60, 105), (-f, 0.4)
    if arms == "up":
        return (sx * 70, -165 + math.sin(t * 16 + i) * 14), (sx, 0.2)
    if arms == "wave":
        if front:
            return (f * 62 + math.sin(t * 14) * 26, -150), (sx, 0.3)
        return (sx * 14, 184), (sx, 0.3)
    if arms == "shrug":
        return (sx * 85, 75), (sx, 0.6)
    if arms == "hips":
        return (sx * 30, 130), (sx, -0.2)
    if arms == "balance":
        return (sx * 175, 20 + math.sin(t * 6 + i) * 18), (0, -1)
    if arms == "flail":
        return (sx * 120 + math.sin(t * 22 + i) * 40, -110 + math.cos(t * 19 + i) * 50), (sx, 0)
    if arms == "drive":
        return (f * 125 + sx * 8, 72), (0, 1)
    if arms == "point" and front:
        return (f * 188, -12), (0, 1)
    if arms == "stop" and front:
        return (f * 150, -60), (0, 1)
    if arms == "hold" and front:
        return (f * 70, 105), (0, 1)
    if arms == "explain" and front:
        return (f * 62 + math.sin(t * 6) * 14, 88 + math.sin(t * 7.3) * 16), (sx, 0.5)
    if arms == "salute" and front:
        hx, hy = J["H"][0] - J["sh%d" % i][0], J["H"][1] - J["sh%d" % i][1]
        return ((hx + f * 18) / s, (hy - 16) / s), (sx, -0.6)
    return (sx * 14, 184), (sx, 0.3)


def pose(spec, x, y, st, t):
    k, s = spec["key"], spec["s"]
    f = st.get(k + "_face", spec["face"])
    legs = st.get(k + "_legs", "stand")
    arms = st.get(k + "_arms", "rest")
    talk = st.get(k + "_talk", 0.0)
    if arms == "rest" and legs == "stand" and st.get(k + "_speaking"):
        arms = "explain"                                   # talk with your hands
    ph = t * (15 if legs == "run" else 9 * st.get(k + "_wspd", 1.0)) + spec["phase"]
    jump = abs(math.sin(t * 9 + spec["phase"])) * 24 if st.get(k + "_bounce") else 0.0
    bob = {"walk": -abs(math.cos(ph)) * 6, "run": -abs(math.cos(ph)) * 14}.get(legs, math.sin(t * 2 + spec["phase"]) * 1.5)
    lean = {"run": 0.17, "walk": 0.04}.get(legs, 0.0) + spec["lean"]
    sway = math.sin(t * 1.3 + spec["phase"]) * 3 if legs == "stand" else 0.0
    gy = y - (30 if legs == "skate" else 0)
    crouch = 26 if legs == "skate" else 0
    P = (x + sway, gy - 280 * s + bob - jump + crouch)
    C = (P[0] + f * math.sin(lean) * 170 * s, P[1] - math.cos(lean) * 170 * s)
    J = dict(P=P, C=C, f=f, s=s, legs=legs, arms=arms)
    for i, sx in enumerate((-1, 1)):
        hip = (P[0] + sx * 22 * s * spec["bulk"], P[1] + 6 * s)
        q = ph + i * math.pi
        if legs == "walk":
            foot = (x + sx * 18 * s + f * math.sin(q) * 55 * s, gy - 16 * s - max(0, math.cos(q)) * 20 * s)
        elif legs == "run":
            foot = (x + sx * 12 * s + f * math.sin(q) * 95 * s, gy - 16 * s - max(0, math.cos(q)) * 60 * s)
        elif legs == "skate":
            foot = (x + sx * 50 * s, gy - 10)
        else:
            foot = (x + sx * 28 * s * spec["bulk"], gy - 16 * s - jump)
        knee, ankle = ik(hip, foot, 130 * s, 134 * s, (f, 0))
        J["leg%d" % i] = (hip, knee, ankle)
    nod = math.sin(t * 11) * talk * 3 * s
    J["H"] = (C[0] + f * 3 * s + f * talk * 2 * s, C[1] - 60 * s - talk * 2 * s + nod)
    J["N"] = (C[0], C[1] - 8 * s)
    for i, sx in enumerate((-1, 1)):
        sh = (C[0] + sx * 48 * s * spec["bulk"], C[1] + 8 * s)
        J["sh%d" % i] = sh
        (rx, ry), bend = arm_target(arms, legs, i, sx, f, ph, t, s, J)
        el, wr = ik(sh, (sh[0] + rx * s, sh[1] + ry * s), 100 * s, 94 * s, bend)
        J["arm%d" % i] = (sh, el, wr)
    return J


def make_rig(pn, spec, x, y, st):
    k = spec["key"]
    return Rig(pn, st.get(k + "_pivot", (x, y)), st.get(k + "_rot", 0.0), st.get(k + "_off", (0, 0)))


def head_world(spec, x, y, st, t):
    J = pose(spec, x, y, st, t)
    return make_rig(None, spec, x, y, st).T(J["H"])


# --------------------------------------------------------------------------
# Faces & bodies
# --------------------------------------------------------------------------
def eye(rig, ex, ey, s, look, blink, shock, tired, iris, skin, lash_side):
    rx, ry = 7.6 * s, (6.6 if shock else 4.7) * s
    rig.ell(ex, ey, rx, ry, (252, 252, 250), 2)
    if blink:
        rig.ell(ex, ey, rx, ry, skin, 2)
        rig.line([(ex - rx, ey + 1), (ex + rx, ey + 1)], INK, 2.5)
        return
    ir = (2.6 if shock else 3.8) * s
    ix, iy = ex + look[0] * 2.8 * s, ey + look[1] * 1.6 * s
    rig.ell(ix, iy, ir, ir, iris, 0)
    rig.ell(ix, iy, ir * 0.5, ir * 0.5, INK, 0)
    rig.ell(ix - ir * 0.35, iy - ir * 0.4, ir * 0.28, ir * 0.28, (255, 255, 255), 0)
    if tired:
        rig.poly([(ex - rx - 1, ey - ry - 2), (ex + rx + 1, ey - ry - 2), (ex + rx + 1, ey), (ex - rx - 1, ey)], skin, 0)
        rig.line([(ex - rx, ey), (ex + rx, ey)], INK, 2.5)
    else:
        lid = [(ex + math.cos(a) * rx, ey - abs(math.sin(a)) * ry) for a in np.linspace(math.pi, 2 * math.pi, 9)]
        rig.line(lid, INK, 2.8)
    if lash_side:
        rig.line([(ex + lash_side * rx, ey - 1 * s), (ex + lash_side * (rx + 4 * s), ey - 4 * s)], INK, 2.2)


def human_mouth(rig, mx, my, s, m, female, mood):
    lip = (186, 58, 82)
    if m < 0.15:
        if female:
            rig.blob([(mx - 4 * s, my - 0.5 * s, 5.5 * s, 2.4 * s), (mx + 4 * s, my - 0.5 * s, 5.5 * s, 2.4 * s),
                      (mx, my + 2 * s, 7.5 * s, 2.8 * s)], lip, 1.5)
            rig.line([(mx - 8 * s, my + 0.5 * s), (mx + 8 * s, my + 0.5 * s)], INK, 1.5)
        else:
            c = {"sad": -2.5, "flat": 0}.get(mood, 2.6) * s
            rig.line([(mx - 9 * s, my - c * 0.3), (mx, my + c), (mx + 9 * s, my - c * 0.3)], INK, 3)
        return
    h = (2.5 + 8 * m) * s
    w = (8 + 2.5 * m) * s
    if female:
        rig.ell(mx, my + h * 0.5, w + 2.4 * s, h + 2.4 * s, lip, 2)
        rig.ell(mx, my + h * 0.5, w, h, (78, 22, 34), 0)
    else:
        rig.ell(mx, my + h * 0.5, w, h, (78, 22, 34), 2.5)
    rig.ell(mx, my + h * 0.5 - h * 0.62, w * 0.75, 1.8 * s, (250, 250, 250), 0)
    rig.ell(mx, my + h * 0.5 + h * 0.55, w * 0.5, 2 * s, (220, 100, 112), 0)


def donut(pn, x, y, r=22):
    pn.ellipse(x, y, r, r * 0.75, (214, 160, 90), 3)
    pn.ellipse(x, y - 3, r * 0.85, r * 0.55, (248, 140, 196), 0)
    for k in range(6):
        a = k * 1.1
        pn.line([(x + math.cos(a) * r * 0.6, y - 3 + math.sin(a) * r * 0.35),
                 (x + math.cos(a) * r * 0.6 + 4, y - 3 + math.sin(a) * r * 0.35)],
                [(255, 255, 255), (90, 200, 255), (255, 230, 90)][k % 3], 2.5)
    pn.ellipse(x, y - 2, r * 0.28, r * 0.2, (214, 160, 90), 2)


def ring(rig, cx, cy, r, col=INK, w=2.5):
    rig.line([(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, 17)], col, w)


def draw_human(pn, spec, x, y, st, t, seated=False):
    k = spec["key"]
    J = pose(spec, x, y, st, t)
    rig = make_rig(pn, spec, x, y, st)
    s, f, P, C, H = J["s"], J["f"], J["P"], J["C"], J["H"]
    skin, hair, top = spec["skin"], spec["hair"], spec["top"]
    fem, style, b = spec["female"], spec["style"], spec["bulk"]
    wind = -14 * f if st.get(k + "_wind") else 0

    if style == "nina":  # big curls behind the head
        curls = []
        for i in range(13):
            a = math.pi * (0.85 + 1.3 * i / 12)
            curls.append((H[0] + wind + math.cos(a) * 42 * s, H[1] - 6 * s + math.sin(a) * 42 * s, 17 * s, 17 * s))
        curls += [(H[0] - 38 * s + wind, H[1] + 30 * s, 15 * s, 22 * s), (H[0] + 38 * s + wind, H[1] + 30 * s, 15 * s, 22 * s)]
        rig.blob(curls, hair, 3)
    if style == "rosa":  # bun
        rig.blob([(H[0] - f * 6 * s, H[1] - 42 * s, 17 * s, 15 * s)], hair, 3)

    if not seated:
        for i in (0, 1):
            hip, knee, ankle = J["leg%d" % i]
            if spec["long"]:
                rig.chain([hip, knee, ankle], [17 * s * b, 12.5 * s * b, 9 * s], spec["bottoms"])
            else:
                rig.chain([hip, knee, ankle], [15 * s, 11 * s, 8 * s], skin)
                rig.chain([hip, lp(hip, knee, 0.72)], [19 * s, 16 * s], spec["bottoms"])
            rig.blob([(ankle[0] + f * 10 * s, ankle[1] + 8 * s, 20 * s, 10 * s),
                      (ankle[0] + f * 25 * s, ankle[1] + 10 * s, 11 * s, 8 * s)], spec["shoes"], 3)
            xs = sorted([ankle[0] - f * 9 * s, ankle[0] + f * 34 * s])
            sole = (255, 255, 255) if style == "nina" else (200, 200, 205) if style == "rico" else darker(spec["shoes"], 0.6)
            rig.line([(xs[0], ankle[1] + 16 * s), (xs[1], ankle[1] + 16 * s)], sole, 2.5)

    # torso
    if style == "nina":
        if not seated:
            rig.poly([(P[0] - 40 * s, P[1] - 34 * s), (P[0] + 40 * s, P[1] - 34 * s),
                      (P[0] + 46 * s, P[1] + 24 * s), (P[0] - 46 * s, P[1] + 24 * s)], spec["bottoms"], 3)
        rig.poly([(C[0] - 30 * s, C[1] + 90 * s), (C[0] + 30 * s, C[1] + 90 * s),
                  (P[0] + 38 * s, P[1] - 30 * s), (P[0] - 38 * s, P[1] - 30 * s)], skin, 3)
        rig.ell(P[0] + f * 2 * s, P[1] - 48 * s, 1.8 * s, 2.4 * s, darker(skin, 0.7), 0)
        tp = [(C[0] - 44 * s, C[1]), (C[0] + 44 * s, C[1]), (C[0] + 38 * s, C[1] + 48 * s),
              (C[0] + 32 * s, C[1] + 94 * s), (C[0] - 32 * s, C[1] + 94 * s), (C[0] - 38 * s, C[1] + 48 * s)]
        rig.poly(tp, top, 3)
        rig.poly([(C[0] + 14 * s, C[1] + 3 * s), (C[0] + 41 * s, C[1] + 3 * s), (C[0] + 35 * s, C[1] + 48 * s),
                  (C[0] + 30 * s, C[1] + 91 * s), (C[0] + 12 * s, C[1] + 91 * s)], darker(top, 0.88), 0)
        rig.line([(C[0] - 30 * s, C[1] + 40 * s), (C[0] + 30 * s, C[1] + 40 * s)], (250, 236, 120), 3)
    else:
        if not seated:
            rig.poly([(P[0] - 44 * s * b, P[1] - 16 * s), (P[0] + 44 * s * b, P[1] - 16 * s),
                      (P[0] + 48 * s * b, P[1] + 30 * s), (P[0] - 48 * s * b, P[1] + 30 * s)], spec["bottoms"], 3)
        belly = 1.12 if style == "duke" else 1.0
        tp = [(C[0] - 56 * s * b, C[1] - 2 * s), (C[0] + 56 * s * b, C[1] - 2 * s), (C[0] + 50 * s * b, C[1] + 42 * s),
              (P[0] + 44 * s * b * belly, P[1] - 48 * s), (P[0] + 46 * s * b, P[1] + 8 * s), (P[0] - 46 * s * b, P[1] + 8 * s),
              (P[0] - 44 * s * b * belly, P[1] - 48 * s), (C[0] - 50 * s * b, C[1] + 42 * s)]
        rig.poly(tp, top, 3)
        rig.poly([(C[0] + 22 * s * b, C[1] + 2 * s), (C[0] + 53 * s * b, C[1] + 1 * s), (C[0] + 47 * s * b, C[1] + 42 * s),
                  (P[0] + 41 * s * b * belly, P[1] - 48 * s), (P[0] + 43 * s * b, P[1] + 5 * s), (P[0] + 18 * s * b, P[1] + 5 * s)],
                 darker(top, 0.88), 0)
        if spec["pattern"]:
            for fx, fy in ((-30, 30), (18, 62), (-12, 100), (34, 18), (-36, 130), (24, 140)):
                px, py = rig.T((C[0] + fx * s, C[1] + fy * s))
                pn.star(px, py, 7 * s, spec["pattern"], 2)
        rig.line([(C[0], C[1] + 8 * s), (P[0] + f * 2 * s, P[1] + 6 * s)], darker(top, 0.7), 2)
        if style == "rico":
            rig.poly([(C[0] - 16 * s, C[1] - 3 * s), (C[0] + 16 * s, C[1] - 3 * s), (C[0], C[1] + 24 * s)], skin, 2.5)
        if style == "rosa":
            for j in range(4):
                rig.ell(C[0] + 4 * s, C[1] + (30 + j * 34) * s, 3.5 * s, 3.5 * s, (250, 240, 200), 1.5)
            for j in range(9):
                a = math.pi * (0.15 + 0.7 * j / 8)
                rig.ell(C[0] + math.cos(a) * 22 * s, C[1] - 4 * s + math.sin(a) * 18 * s, 3 * s, 3 * s, (255, 255, 255), 1)
        if style == "duke":
            rig.poly([(C[0] - 14 * s, C[1] - 3 * s), (C[0] + 14 * s, C[1] - 3 * s), (C[0], C[1] + 20 * s)], (250, 250, 250), 2)
            px, py = rig.T((C[0] - f * 28 * s, C[1] + 34 * s))
            pn.star(px, py, 11 * s, (250, 210, 60), 2)
            rig.line([(P[0] - 46 * s * b, P[1] - 6 * s), (P[0] + 46 * s * b, P[1] - 6 * s)], (24, 24, 28), 9)
            rig.ell(P[0], P[1] - 6 * s, 8 * s, 6 * s, (220, 190, 80), 2)

    # neck & head
    rig.chain([J["N"], (H[0], H[1] + 30 * s)], [10 * s * (1.2 if style == "duke" else 1), 10 * s], skin, 3, shade=False)
    jaw = (24 * s, 27 * s) if fem else (26 * s, 29 * s) if style == "rico" else (30 * s, 30 * s)
    rig.blob([(H[0], H[1] - 6 * s, 31 * s, 33 * s), (H[0] + f * 2 * s, H[1] + 12 * s) + jaw,
              (H[0] - 31 * s, H[1] + 2 * s, 6 * s, 9 * s), (H[0] + 31 * s, H[1] + 2 * s, 6 * s, 9 * s)], skin, 3)
    rig.ell(H[0] - f * 19 * s, H[1] + 14 * s, 6 * s, 3.5 * s, darker(skin, 0.93), 0)
    if style == "rico" and not st.get("r_bigbeard"):
        rig.ell(H[0] + f * 3 * s, H[1] + 23 * s, 21 * s, 13 * s, darker(skin, 0.86), 0)

    mood = st.get(k + "_mood", "")
    shock = st.get(k + "_shock", False)
    look = st.get(k + "_look", (f, 0))
    wink = st.get(k + "_wink", False)
    ex0, ey = H[0] + f * 5 * s, H[1] - 1 * s
    for sx in (-1, 1):
        eye(rig, ex0 + sx * 12 * s, ey, s, look, st.get(k + "_blink") or (wink and sx == f), shock,
            st.get(k + "_tired") or style == "rosa" and not shock, spec["iris"], skin, sx if fem else 0)
        raise_ = (st.get(k + "_brow", 0.0) * 4 + (5 if shock else 0)) * s
        tilt = {"sad": -3, "angry": 3}.get(mood, 0) * s * sx
        bc = hair if style in ("rico", "duke") else (170, 170, 178) if style == "rosa" else INK
        rig.line([(ex0 + sx * 12 * s - 7 * s, ey - 9 * s - raise_ + tilt * 0.5),
                  (ex0 + sx * 12 * s + 7 * s, ey - 10 * s - raise_ - tilt * 0.5)], bc, 3.8 if style == "duke" else 3.2)
    if style == "rosa":
        for sx in (-1, 1):
            rig.line([(ex0 + sx * 21 * s, ey - 2 * s), (ex0 + sx * 25 * s, ey + 1 * s)], darker(skin, 0.7), 1.6)
    rig.line([(H[0] + f * 6 * s, H[1] + 1 * s), (H[0] + f * 10 * s, H[1] + 13 * s), (H[0] + f * 3 * s, H[1] + 15 * s)],
             darker(skin, 0.55), 2.4)
    if st.get("r_bigbeard") and style == "rico":
        rig.blob([(H[0] + f * 2 * s, H[1] + 30 * s, 29 * s, 20 * s), (H[0], H[1] + 58 * s, 27 * s, 30 * s),
                  (H[0], H[1] + 92 * s, 17 * s, 24 * s)], hair, 3)
    human_mouth(rig, H[0] + f * 5 * s, H[1] + 25 * s, s, st.get(k + "_talk", 0.0), fem, mood)
    if style == "duke":
        rig.blob([(H[0] + f * 5 * s - 7 * s, H[1] + 19 * s, 10 * s, 5 * s), (H[0] + f * 5 * s + 7 * s, H[1] + 19 * s, 10 * s, 5 * s)],
                 hair, 2)
    if style == "rosa":
        for sx in (-1, 1):
            ring(rig, ex0 + sx * 12 * s, ey, 10 * s, (120, 90, 60), 2.6)
        rig.line([(ex0 - 2 * s, ey - 1 * s), (ex0 + 2 * s, ey - 1 * s)], (120, 90, 60), 2.4)
        rig.blob([(H[0] - 4 * s, H[1] - 30 * s, 31 * s, 12 * s), (H[0] - 26 * s, H[1] - 14 * s, 9 * s, 14 * s),
                  (H[0] + 26 * s, H[1] - 14 * s, 9 * s, 14 * s)], hair, 3)
        if st.get("o_headset"):
            rig.line([(H[0] - 32 * s, H[1] - 2 * s), (H[0] - 26 * s, H[1] - 38 * s), (H[0], H[1] - 48 * s),
                      (H[0] + 26 * s, H[1] - 38 * s), (H[0] + 32 * s, H[1] - 2 * s)], (60, 220, 120), 5)
            for sx in (-1, 1):
                rig.ell(H[0] + sx * 33 * s, H[1] + 2 * s, 8 * s, 11 * s, (40, 40, 48), 3)
            rig.line([(H[0] + f * 34 * s, H[1] + 10 * s), (H[0] + f * 20 * s, H[1] + 28 * s)], (40, 40, 48), 3)
            rig.ell(H[0] + f * 18 * s, H[1] + 29 * s, 3.5 * s, 3.5 * s, (60, 220, 120), 2)
    elif style == "nina":
        rig.blob([(H[0] - 12 * s + wind, H[1] - 30 * s, 22 * s, 11 * s), (H[0] + 14 * s + wind, H[1] - 32 * s, 22 * s, 11 * s),
                  (H[0] + 30 * s + wind, H[1] - 20 * s, 9 * s, 12 * s)], hair, 3)
        for sx in (-1, 1):
            rig.ell(H[0] + sx * 12 * s + wind, H[1] - 38 * s, 11 * s, 6 * s, (250, 214, 60), 2.5)
            rig.ell(H[0] + sx * 33 * s, H[1] + 16 * s, 5.5 * s, 7 * s, (250, 200, 60), 2)
            rig.ell(H[0] + sx * 33 * s, H[1] + 16 * s, 2.5 * s, 4 * s, skin, 0)
    elif style == "duke":
        rig.blob([(H[0], H[1] - 28 * s, 34 * s, 16 * s), (H[0] - f * 4 * s, H[1] - 38 * s, 30 * s, 12 * s)], top, 3)
        rig.blob([(H[0] + f * 26 * s, H[1] - 18 * s, 22 * s, 6 * s)], (24, 30, 50), 3)
        px, py = rig.T((H[0] - f * 2 * s, H[1] - 34 * s))
        pn.star(px, py, 7 * s, (250, 210, 60), 2)
    else:
        rig.blob([(H[0] - 3 * s + wind, H[1] - 31 * s, 30 * s, 13 * s), (H[0] + f * 14 * s + wind * 2, H[1] - 39 * s, 19 * s, 11 * s),
                  (H[0] - 28 * s, H[1] - 15 * s, 6 * s, 13 * s), (H[0] + 28 * s, H[1] - 15 * s, 6 * s, 12 * s)], hair, 3)
    if st.get(k + "_shades"):
        for sx in (-1, 1):
            cx = ex0 + sx * 12 * s
            rig.poly([(cx - 10 * s, ey - 6 * s), (cx + 10 * s, ey - 6 * s), (cx + 9 * s, ey + 5 * s),
                      (cx - 9 * s, ey + 5 * s)], (24, 24, 32), 2.5)
        rig.line([(ex0 - 3 * s, ey - 4 * s), (ex0 + 3 * s, ey - 4 * s)], INK, 2.5)

    # arms (in front of the body)
    for i, sx in enumerate((-1, 1)):
        sh, el, wr = J["arm%d" % i]
        rig.chain([sh, el, wr], [12.5 * s, 10 * s, 7.5 * s], skin)
        if spec["sleeves"] == "short":
            rig.chain([sh, lp(sh, el, 0.42)], [15 * s * min(b, 1.1), 13.5 * s], top)
        elif spec["sleeves"] == "long":
            rig.chain([sh, el, lp(el, wr, 0.85)], [14.5 * s, 12 * s, 10 * s], top)
        else:
            rig.line([lp(sh, (C[0], C[1]), 0.15), (sh[0], sh[1] - 4 * s)], top, 4)
        dx, dy = wr[0] - el[0], wr[1] - el[1]
        L = math.hypot(dx, dy) or 1
        hc = (wr[0] + dx / L * 8 * s, wr[1] + dy / L * 8 * s)
        rig.ell(hc[0], hc[1], 8.5 * s, 10 * s, skin, 3)
        rig.ell(hc[0] - dy / L * 7 * s * sx, hc[1] + dx / L * 7 * s * sx, 3.5 * s, 5 * s, skin, 2)
        if st.get(k + "_hold") == "donut" and sx == f:
            px, py = rig.T((hc[0] + f * 6 * s, hc[1] - 14 * s))
            donut(pn, px, py, 20 * s)


def draw_cast(pn, st, t, seated=False):
    for k in st["cast"]:
        draw_human(pn, SPECS[k], st[k + "_x"], st[k + "_y"], st, t, seated and k in ("r", "n"))


# --------------------------------------------------------------------------
# Props
def draw_car_body(pn, cx, gy, t, speed):
    spin = -t * speed / 40
    pn.blob([(cx - 40, gy - 92, 220, 52), (cx + 150, gy - 80, 90, 40), (cx - 190, gy - 84, 60, 44)], (54, 196, 210), 4)
    pn.blob([(cx + 40, gy - 70, 180, 22)], darker((54, 196, 210), 0.88), 0)
    pn.line([(cx - 250, gy - 92), (cx + 230, gy - 92)], (246, 110, 152), 10, caps=False)
    pn.line([(cx - 30, gy - 130), (cx - 30, gy - 50)], INK, 3, caps=False)
    pn.rect(cx - 70, gy - 108, cx - 44, gy - 100, (230, 230, 235), 2, 3)
    pn.stroke([(cx + 110, gy - 140), (cx + 80, gy - 215)], (190, 236, 246), 8, 3)
    pn.ellipse(cx + 236, gy - 92, 12, 10, (255, 236, 120), 3)
    pn.ellipse(cx - 258, gy - 96, 9, 10, (230, 60, 60), 3)
    for wx in (cx - 150, cx + 140):
        pn.ellipse(wx, gy - 38, 40, 40, (34, 32, 38), 4)
        pn.ellipse(wx, gy - 38, 20, 20, (200, 200, 210), 3)
        for k in range(3):
            a = spin + k * 2 * math.pi / 3
            pn.line([(wx, gy - 38), (wx + math.cos(a) * 18, gy - 38 + math.sin(a) * 18)], INK, 4, caps=False)


def skateboard(pn, x, y, tilt=0.0):
    pts = [(x - 70, y - 22 - tilt), (x + 70, y - 22 + tilt)]
    pn.stroke([(x - 84, y - 30 - tilt * 1.2)] + pts + [(x + 84, y - 30 + tilt * 1.2)], (230, 80, 60), 7, 3)
    for wx in (x - 46, x + 46):
        pn.ellipse(wx, y - 9, 9, 9, (250, 230, 120), 3)


def seagull(pn, x, y, t, carrying=False, f=1):
    flap = math.sin(t * 22) * 30
    pn.poly([(x - 6, y), (x - 70, y - 20 - flap), (x - 40, y + 4)], (240, 240, 245), 3)
    pn.blob([(x, y, 34, 14), (x + f * 28, y - 10, 13, 12)], (250, 250, 252), 3)
    pn.poly([(x - f * 30, y - 4), (x - f * 50, y - 10), (x - f * 48, y + 6)], (150, 150, 160), 3)
    pn.poly([(x + f * 38, y - 12), (x + f * 56, y - 8), (x + f * 38, y - 4)], (250, 170, 40), 2)
    pn.ellipse(x + f * 31, y - 14, 2.5, 2.5, INK, 0)
    pn.poly([(x + 6, y), (x + 70, y - 20 + flap), (x + 40, y + 4)], (228, 228, 236), 3)
    if carrying:
        donut(pn, x + f * 58, y, 16)


def palm(pn, x, gy, h=300, sway=0.0, dark=None):
    trunk = (150, 104, 62) if dark is None else dark
    leaf = (60, 170, 90) if dark is None else dark
    ow = 0 if dark else 4
    top = (x + 40 + sway, gy - h)
    pn.stroke([(x, gy), (x + 18, gy - h * 0.5), top], trunk, 18, ow)
    for k in range(6):
        a = -math.pi * (0.05 + 0.9 * k / 5)
        tip = (top[0] + math.cos(a) * 110, top[1] + math.sin(a) * 50 + 40)
        mid = (top[0] + math.cos(a) * 60, top[1] + math.sin(a) * 50 - 6)
        pn.stroke([top, mid, tip], leaf, 14, ow)


# --------------------------------------------------------------------------
# Backgrounds — each takes L(parallax) -> Pen, so layers move at different speeds
# --------------------------------------------------------------------------
def bg_living(L, t, st):
    pn = L(1.0)
    pn.rect(-2000, -900, 4000, 600, (246, 200, 162), 0)
    for i in range(-20, 40):
        pn.rect(i * 120, -900, i * 120 + 50, 590, (240, 190, 150), 0)
    pn.rect(80, 140, 330, 380, (250, 250, 252), 4)
    pn.rect(92, 152, 318, 368, (176, 196, 220), 0)
    rnd = random.Random(4)
    for i in range(30):
        sx = 92 + (rnd.uniform(0, 226) + math.sin(t * 2 + i) * 6) % 226
        sy = 152 + (rnd.uniform(0, 216) + t * (40 + 30 * st.get("snow", 0))) % 216
        pn.ellipse(sx, sy, 3, 3, (255, 255, 255), 0)
    pn.rect(92, 350, 318, 368, (255, 255, 255), 0)
    pn.line([(205, 152), (205, 368)], (250, 250, 252), 8, caps=False)
    pn.rect(66, 376, 344, 392, (250, 250, 252), 4)
    pn.rect(470, 150, 670, 320, (255, 255, 255), 4)
    pn.rect(482, 162, 658, 308, (250, 120, 150), 0)
    pn.rect(482, 236, 658, 308, (255, 176, 110), 0)
    pn.ellipse(570, 236, 40, 40, (255, 226, 120), 0)
    pn.rect(482, 270, 658, 308, (90, 60, 140), 0)
    palm(pn, 520, 300, 110, 0, dark=(60, 30, 80))
    pn.rect(380, 430, 790, 560, (100, 120, 200), 4, 30)
    pn.rect(390, 440, 780, 470, (116, 136, 214), 0, 14)
    pn.rect(360, 480, 420, 590, (90, 108, 186), 4, 20)
    pn.rect(750, 480, 810, 590, (90, 108, 186), 4, 20)
    pn.rect(860, 470, 1150, 600, (130, 86, 54), 4, 6)
    pn.rect(960, 490, 1050, 520, (30, 30, 34), 3, 6)
    pn.ellipse(1032, 505, 4, 4, (90, 220, 255), 0)
    pn.rect(870, 290, 1140, 462, (30, 30, 34), 4, 8)
    sx0, sy0, sx1, sy1 = 884, 302, 1126, 450
    mode = st.get("tv_mode")
    if mode == "count":
        pn.rect(sx0, sy0, sx1, sy1, (20, 24, 60), 0)
        wtext(pn, 1005, 340, "GTA VI TRAILER", 22, (255, 140, 200))
        wtext(pn, 1005, 380, "watched:", 16, (255, 255, 255), 2)
        wtext(pn, 1005, 420, f"{st['tv_count']:,}", 34, (255, 230, 90))
    elif mode == "download":
        pn.rect(sx0, sy0, sx1, sy1, (16, 18, 30), 0)
        wtext(pn, 1005, 336, "DOWNLOADING GTA VI", 17, (255, 255, 255), 2)
        pn.rect(900, 368, 1110, 388, (60, 60, 80), 2, 6)
        pn.rect(902, 370, 902 + 2.1 * st.get("dl", 1), 386, (90, 230, 140), 0, 5)
        wtext(pn, 1005, 412, f"{st.get('dl', 1)}%   9h 12m left", 16, (255, 220, 120), 2)
    else:
        pn.rect(sx0, sy0, sx1, sy1, (250, 120, 150), 0)
        pn.rect(sx0, sy0 + 74, sx1, sy1, (255, 176, 110), 0)
        pn.ellipse(1005, sy0 + 76, 34, 34, (255, 226, 120), 0)
        pn.rect(sx0, sy0 + 100, sx1, sy1, (90, 60, 140), 0)
        palm(pn, 920, sy1, 120, math.sin(t) * 4, dark=(60, 30, 80))
        wtext(pn, 1005, 330, "GTA VI", 26, (255, 255, 255))
    pn.rect(-2000, 590, 4000, 606, (120, 80, 50), 4)
    pn.rect(-2000, 606, 4000, 1600, (196, 150, 120), 0)
    pn.ellipse(640, 690, 440, 50, (230, 120, 90), 4)


def bg_beach(L, t, st):
    pn = L(0.12)
    for y0, c in [(-1200, (250, 96, 150)), (120, (255, 130, 140)), (230, (255, 160, 120)), (330, (255, 196, 120))]:
        pn.rect(-3000, y0, 5000, 1600, c, 0)
    pn.ellipse(900, 400, 110, 110, (255, 226, 110), 0)
    for k in range(4):
        pn.rect(780, 380 + k * 16, 1020, 386 + k * 16, (255, 196, 120), 0)
    pn = L(0.45)
    pn.rect(-3000, 430, 5000, 1600, (60, 156, 206), 0)
    for i in range(-30, 50):
        xx = i * 140 + (t * 20) % 140
        pn.line([(xx, 470 + (i % 3) * 18), (xx + 50, 470 + (i % 3) * 18)], (150, 210, 240), 4)
    pn = L(1.0)
    pn.rect(-3000, 520, 5000, 1600, (246, 220, 160), 0)
    pn.line([(-3000, 522), (5000, 522)], INK, 4, caps=False)
    for i in range(-6, 12):
        palm(pn, -100 + i * 520, 560, 360, math.sin(t * 1.5 + i) * 8)
    for i in range(-20, 40):
        pn.rect(i * 120, 640, i * 120 + 112, 700, (176, 124, 80), 3)
        pn.rect(i * 120 + 4, 690, i * 120 + 108, 700, (150, 104, 66), 0)
    if st.get("rock_x") is not None:
        rx = st["rock_x"]
        pn.blob([(rx, 650, 34, 22), (rx + 18, 640, 20, 18)], (140, 140, 150), 4)


NEON = ["MOTEL", "DINER", "24/7", "ARCADE", "TACOS", "PAWN"]


def bg_street(L, t, st):
    sc = st.get("scroll", 0.0)
    pn = L(0.08)
    for y0, c in [(-1200, (24, 12, 52)), (140, (60, 26, 96)), (300, (110, 46, 118))]:
        pn.rect(-3000, y0, 5000, 1600, c, 0)
    rnd = random.Random(2)
    for i in range(60):
        pn.star(rnd.uniform(-600, 1900), rnd.uniform(-600, 260), 2 + abs(math.sin(t * 3 + i)) * 2, (255, 240, 220), 0,
                points=4)
    pn.ellipse(1050, 120, 40, 40, (250, 246, 210), 3)
    pn = L(0.3)
    off = (sc * 0.3) % 160
    for i in range(-20, 30):
        h = 120 + (i * 53) % 130
        pn.rect(i * 160 - off, 470 - h, i * 160 - off + 150, 1600, (64, 32, 96), 0)
    pn = L(0.65)
    P = 300
    off = (sc * 0.65) % P
    base_i = int(sc * 0.65 // P)
    cols = [(255, 170, 200), (130, 220, 230), (250, 220, 140), (190, 160, 255)]
    for i in range(-10, 20):
        bx = i * P - off
        k = (i + base_i) % 12
        bh = 180 + (k * 67) % 200
        c = cols[k % 4]
        pn.rect(bx, 590 - bh, bx + 250, 1600, c, 4)
        pn.rect(bx + 180, 590 - bh, bx + 250, 1600, darker(c, 0.88), 0)
        for wy in range(int(590 - bh + 24), 560, 46):
            for wx in range(int(bx + 20), int(bx + 230), 50):
                lit = (wx * 7 + wy * 3 + k) % 5 != 0
                pn.rect(wx, wy, wx + 26, wy + 26, (255, 236, 150) if lit else (60, 50, 90), 2)
        if k % 2 == 0:
            neon = (255, 80, 200) if k % 4 == 0 else (80, 240, 255)
            pn.rect(bx + 30, 590 - bh - 56, bx + 220, 590 - bh - 6, (30, 20, 50), 4, 10)
            wtext(pn, bx + 125, 590 - bh - 31, NEON[k // 2 % len(NEON)], 28, neon, 3, (255, 255, 255))
    pn = L(1.0)
    if st.get("store"):
        pn.rect(260, 150, 1120, 600, (88, 52, 70), 4)
        for yy in range(170, 600, 34):
            pn.line([(262, yy), (1118, yy)], (72, 42, 58), 3, caps=False)
        pn.rect(320, 110, 820, 190, (30, 20, 50), 4, 14)
        wtext(pn, 570, 150, "GAME HUT", 48, (80, 240, 255), 4, (255, 255, 255))
        pn.rect(320, 250, 800, 560, (40, 60, 110), 4)
        pn.rect(350, 280, 520, 520, (250, 120, 150), 3)
        wtext(pn, 435, 340, "COMING", 24, (255, 255, 255))
        wtext(pn, 435, 375, "SOON", 24, (255, 255, 255))
        palm(pn, 380, 520, 110, 0, dark=(80, 30, 90))
        pn.rect(560, 290, 770, 360, (255, 220, 90), 3)
        wtext(pn, 665, 325, "OPEN 24/7", 22, (40, 30, 60), 0)
        pn.rect(860, 260, 1020, 600, (70, 100, 140), 4)
        pn.ellipse(1000, 440, 7, 7, (230, 200, 90), 2)
        pn.rect(880, 330, 1000, 420, (255, 255, 255), 3)
        wtext(pn, 940, 352, "DIGITAL", 17, (220, 40, 60), 0)
        wtext(pn, 940, 376, "DOWNLOAD", 15, (220, 40, 60), 0)
        wtext(pn, 940, 400, "ONLY :)", 15, (40, 40, 40), 0)
    off2 = sc % 420
    if not st.get("store"):
        for i in range(-8, 16):
            palm(pn, i * 420 - off2 + 60, 600, 330, math.sin(t * 1.5 + i) * 6, dark=(28, 16, 50))
    pn.rect(-3000, 590, 5000, 630, (150, 140, 160), 4)
    pn.rect(-3000, 630, 5000, 1600, (54, 52, 66), 0)
    off3 = sc % 200
    for i in range(-20, 40):
        pn.rect(i * 200 - off3, 700, i * 200 - off3 + 110, 712, (250, 220, 90), 0)
    if st.get("speedlines"):
        rnd = random.Random(int(t * 30))
        for _ in range(18):
            yy, xx = rnd.uniform(-300, 760), rnd.uniform(-600, 1900)
            pn.line([(xx, yy), (xx + rnd.uniform(160, 400), yy)], (255, 255, 255), 4)


def bg_day(L, t, st):
    pn = L(0.1)
    pn.rect(-3000, -1200, 5000, 1600, (120, 200, 246), 0)
    pn.rect(-3000, 250, 5000, 1600, (170, 222, 250), 0)
    for i, (cx, cy) in enumerate(((200, 90), (700, 50), (1150, 120), (-300, 60), (1700, 80))):
        cx += (t * 12) % 200
        pn.blob([(cx, cy, 60, 26), (cx + 50, cy - 14, 42, 26), (cx - 50, cy + 4, 40, 20)], (255, 255, 255), 3)
    pn = L(0.65)
    cols = [(255, 200, 180), (190, 230, 210), (255, 236, 170), (210, 200, 250)]
    for i in range(-8, 14):
        bx = i * 280
        c = cols[i % 4]
        bh = 260 + (i * 41) % 120
        pn.rect(bx, 590 - bh, bx + 270, 1600, c, 4)
        for wy in range(int(590 - bh + 30), 470, 60):
            for wx in range(bx + 24, bx + 250, 62):
                pn.rect(wx, wy, wx + 36, wy + 40, (150, 210, 240), 3)
        if i == 2:  # the donut shop
            pn.rect(bx + 10, 470, bx + 260, 600, (255, 255, 255), 4)
            for k in range(6):
                pn.poly([(bx + 10 + k * 42, 462), (bx + 52 + k * 42, 462), (bx + 52 + k * 42, 500), (bx + 10 + k * 42, 500)],
                        (246, 110, 152) if k % 2 == 0 else (255, 255, 255), 2)
            pn.rect(bx + 40, 400, bx + 230, 450, (90, 50, 30), 4, 10)
            wtext(pn, bx + 135, 425, "DONUTS", 30, (255, 170, 210), 3)
            donut(pn, bx + 135, 360, 34)
    pn = L(1.0)
    for i in range(-8, 16):
        palm(pn, i * 480 + 120, 600, 340, math.sin(t * 1.5 + i) * 6)
    pn.rect(-3000, 590, 5000, 640, (210, 206, 214), 4)
    for i in range(-30, 50):
        pn.line([(i * 90, 592), (i * 90 - 20, 638)], (186, 182, 192), 3, caps=False)
    pn.rect(-3000, 640, 5000, 1600, (96, 96, 108), 0)
    pn.line([(-3000, 642), (5000, 642)], INK, 4, caps=False)
    for i in range(-20, 40):
        pn.rect(i * 200, 720, i * 200 + 110, 732, (255, 255, 255), 0)


BACKGROUNDS = {"living": bg_living, "beach": bg_beach, "street": bg_street, "day": bg_day}

# --------------------------------------------------------------------------
# Camera
# --------------------------------------------------------------------------
ZOOM = {"wide": (1.0, 1.9), "ms2": (1.4, 2.35), "ms": (1.75, 2.9), "cu": (3.0, 4.3), "car": (1.25, 1.85),
        "tv": (2.0, 2.4), "sign": (3.2, 3.8)}


def shot_cam(name, st, heads, t):
    zi = 1 if SHORTS else 0
    if name == "wide":
        xs = [st[k + "_x"] for k in st.get("wide_keys", st["cast"])]
        return sum(xs) / len(xs), (440 if SHORTS else 385), ZOOM["wide"][zi]
    if name.startswith("track_"):
        return st[name[-1] + "_x"] + 60, (440 if SHORTS else 385), ZOOM["wide"][zi]
    if name == "fixed":
        cx, cy = st["cam_c"]
        return cx, cy + (55 if SHORTS else 0), ZOOM["wide"][zi] * st.get("cam_zk", 1.0)
    if name == "ms2":
        a, b = st.get("pair", ("r", "n"))
        ha, hb = heads[a], heads[b]
        return (ha[0] + hb[0]) / 2, (ha[1] + hb[1]) / 2 + (120 if SHORTS else 105), ZOOM["ms2"][zi]
    if name.startswith("ms_"):
        h = heads[name[-1]]
        return h[0], h[1] + (85 if SHORTS else 100), ZOOM["ms"][zi]
    if name.startswith("cu_"):
        h = heads[name[-1]]
        return h[0], h[1] + (8 if SHORTS else 12), ZOOM["cu"][zi]
    if name == "car":
        return st["car_x"] - 10, st["gy"] - 200, ZOOM["car"][zi]
    if name == "tv":
        return 1005, 385, ZOOM["tv"][zi]
    if name == "sign":
        return 940, 375, ZOOM["sign"][zi]
    raise KeyError(name)


# --------------------------------------------------------------------------
# Gags
def fx_beard(st, lt, dur, ov):
    st["r_bigbeard"] = lt > 0.1
    if lt < 0.5:
        ov.append(lambda pn: poof(pn, st["r_x"], st["r_y"] - 470, lt / 0.5, (255, 255, 255), 0.5))


def fx_floor_it(st, lt, dur, ov):
    st.update(speedlines=lt > 0.2, r_shock=True, r_wind=True, n_wind=True, n_arms="up", n_mood="")
    st.setdefault("shake", 3.0)


def fx_counter(st, lt, dur, ov):
    st["tv_count"] = 4806 + min(6, int(lt / dur * 7))


def fx_gull(st, lt, dur, ov):
    hand = (st["n_x"] - 70, st["n_y"] - 360)
    tg = 0.6
    if lt < tg:
        k = ease(lt / tg)
        gx, gy = lerp(st["n_x"] - 700, hand[0], k), lerp(80, hand[1], k) - math.sin(math.pi * k) * 60
        ov.append(lambda pn: seagull(pn, gx, gy, lt, False, 1))
    else:
        k = (lt - tg) / (dur - tg)
        gx, gy = lerp(hand[0], st["n_x"] + 900, k), lerp(hand[1], -150, ease(k))
        st.update(n_hold=None, n_shock=True, n_arms="shrug", r_shock=True)
        ov.append(lambda pn: seagull(pn, gx, gy, lt, True, 1))
        if lt - tg < 0.4:
            ov.append(lambda pn: poof(pn, hand[0], hand[1], (lt - tg) / 0.4, (255, 255, 255), 0.35))


def fx_crash(st, lt, dur, ov):
    x0, rock = st["r_x0"], st["rock_x"]
    t_hit, t_land = 0.3, 0.85
    if lt < t_hit:
        st["r_x"] = lerp(x0, rock - 70, lt / t_hit)
        st["board_x"] = st["r_x"]
        return
    st["board_x"] = rock - 70
    st.update(r_legs="stand", r_arms="flail", r_shock=True, n_shock=True, n_arms="up")
    if lt < t_land:
        k = (lt - t_hit) / (t_land - t_hit)
        st["r_x"] = lerp(rock - 70, rock + 120, k)
        st["r_y"] = GROUND - math.sin(math.pi * k) * 170
        st["r_rot"] = ease(k) * math.pi / 2
        st["r_pivot"] = (st["r_x"], st["r_y"])
        st["r_off"] = (0, -24 * ease(k))
    else:
        st.update(r_x=rock + 120, r_rot=math.pi / 2, r_pivot=(rock + 120, GROUND), r_off=(0, -24),
                  r_arms="rest", shake_t=lt - t_land)
        if lt > t_land + 0.25:
            st["gray"] = True


def fx_download(st, lt, dur, ov):
    st["tv_mode"] = "download"
    st["dl"] = 0 if lt < 0.5 else 1


FX = {"beard": fx_beard, "floor_it": fx_floor_it, "counter": fx_counter, "gull": fx_gull,
      "crash": fx_crash, "download": fx_download}

# --------------------------------------------------------------------------
# Episodes
# --------------------------------------------------------------------------
LIVING = dict(scene="living")
BEACH_WALK = dict(scene="beach", r_x=380, n_x=620, r_legs="walk", n_legs="walk", r_vx=120, n_vx=120,
                  r_face=1, n_face=1)
CAR = dict(scene="street", car=True, car_x=640, gy=700, r_face=1, n_face=1)
STREET_WALK = dict(scene="street", r_x=420, n_x=680, r_legs="walk", n_legs="walk", r_vx=95, n_vx=95,
                   r_face=1, n_face=1, n_look=(-1, 0))
DAY = dict(scene="day", r_x=520, n_x=770)
LYING = dict(scene="beach", r_x=1000, r_rot=math.pi / 2, r_pivot=(1000, GROUND), r_off=(0, -24), rock_x=880,
             board_x=810, r_mood="sad", n_x=1330, n_face=-1, n_look=(-1, 0.6))
STORE = dict(scene="street", store=True, cast=["o", "n", "r"], r_x=380, n_x=580, o_x=780,
             wide_keys=["r", "n", "o"])
GRANNY = dict(scene="living", cast=["n", "o", "r"], r_x=430, o_x=700, n_x=960, o_headset=True, o_face=-1,
              pair=("r", "o"))
MALL = dict(scene="day", cast=["n", "d", "r"])


def L(who, text, cam, state, **kw):
    return dict(type="line", who=who, text=text, cam=cam, state=state, **kw)


def A(dur, cam, state, **kw):
    return dict(type="act", dur=dur, cam=cam, state=state, **kw)


EPISODES = [
    dict(num=1, title="Since Forever", beats=[
        L("r", "Nina! I've waited for GTA Six my whole life!", ["ms_r", "ms2"],
          dict(LIVING, r_arms="up", r_bounce=True, r_brow=1), flash=[0.0]),
        L("n", "I know. You grew a beard while waiting.", ["ms_n", "cu_n"], dict(LIVING, n_arms="hips", n_brow=1)),
        L("r", "Worth it.", "cu_r", dict(LIVING), fx="beard", sfx=[(0.05, "poof")], punch=0.12),
        L("r", "Vice City, here we come!", "wide",
          dict(BEACH_WALK, r_bigbeard=True, r_shades=True, r_arms="up"), whip=1, sfx=[(0, "whoosh")]),
        L("n", "Babe. We live in Ohio.", ["ms2", "ms_n"],
          dict(LIVING, r_bigbeard=True, r_mood="sad", snow=3), whip=-1, sfx=[(0, "whoosh"), (0.3, "wind")],
          punch=0.6),
        A(0.8, "cu_r", dict(LIVING, r_bigbeard=True, r_mood="sad", snow=3, r_look=(0, 1)), dutch=-5),
    ]),
    dict(num=2, title="Driving Lessons", beats=[
        L("r", "I'm practicing my driving for GTA Six.", ["car", "ms_r"],
          dict(CAR, speed=60, r_arms="drive", r_shades=True)),
        L("n", "Babe, we're going five miles an hour.", "ms_n",
          dict(CAR, speed=60, r_arms="drive", r_shades=True, n_mood="flat", n_tired=True, n_look=(1, 0))),
        L("r", "In real life, I follow the rules.", ["ms_r", "cu_r"],
          dict(CAR, speed=60, r_arms="drive", r_shades=True)),
        A(1.2, "car", dict(CAR, speed=1700, r_arms="drive", r_shades=True), fx="floor_it",
          sfx=[(0, "vroom")], shake=[(0.05, 14)], flash=[0.05], dutch=5),
        L("r", "Nina! The speed limit!", ["ms_r", "car"], dict(CAR, speed=1700, r_arms="drive", r_shades=True),
          fx="floor_it", dutch=-4),
        L("n", "Now THAT'S how you play GTA!", "ms_n", dict(CAR, speed=1700, r_arms="drive", r_shades=True),
          fx="floor_it", punch=0.9),
    ]),
    dict(num=3, title="The Trailer", beats=[
        L("n", "I've watched the GTA Six trailer a hundred times.", ["wide", "ms2"], dict(STREET_WALK)),
        L("r", "A hundred? Amateur.", ["ms2", "cu_r"], dict(scene="street", r_x=520, n_x=760, r_shades=True),
          punch=0.55),
        A(1.2, "tv", dict(LIVING, r_x=420, n_x=660, tv_mode="count", tv_count=4806), fx="counter", whip=1,
          sfx=[(0.1 + i * 0.16, "tick") for i in range(7)]),
        L("r", "I'm almost at five thousand.", ["ms_r", "cu_r"],
          dict(LIVING, r_x=420, n_x=660, tv_mode="count", tv_count=4812, r_look=(1, 0))),
        L("n", "Okay. We're going outside.", ["ms2", "ms_n"],
          dict(LIVING, r_x=420, n_x=660, tv_mode="count", tv_count=4812, n_arms="point", n_mood="angry",
               r_shock=True), punch=0.2),
        L("r", "Ahh! The sun! It burns!", "fixed",
          dict(scene="beach", cam_c=(700, 385), r_x=760, r_vx=-340, r_legs="run", r_face=-1, r_arms="up",
               r_shock=True, n_x=900, n_face=-1, n_arms="hips", n_mood="flat"), whip=1, sfx=[(0, "whoosh")],
          dutch=4),
    ]),
    dict(num=4, title="Wanted Level", beats=[
        L("n", "Mmm. The last donut.", "wide",
          dict(MALL, r_x=300, n_x=540, d_x=1500, r_legs="walk", n_legs="walk", r_vx=90, n_vx=90, r_face=1,
               n_face=1, n_hold="donut", n_arms="hold", wide_keys=["r", "n"])),
        L("r", "That was MY donut! That's a two-star crime!", ["ms2", "ms_r"],
          dict(MALL, d_x=1500, n_hold="donut", n_arms="hold", r_arms="point", r_mood="angry", r_brow=1, stars=2),
          sfx=[(0.35, "ding"), (0.5, "ding")]),
        L("d", "Did somebody say... crime?", ["wide", "ms_d"],
          dict(MALL, r_x=420, n_x=640, d_x=1160, d_vx=-180, d_vt=0.9, d_legs="walk", n_hold="donut",
               n_arms="hold", r_shock=True, n_shock=True, stars=2, d_shades=True), punch=1.3),
        A(1.5, "wide", dict(MALL, r_x=420, n_x=640, d_x=1000, n_hold="donut", n_arms="hold", stars=2,
                            d_shades=True, wide_keys=["r", "n"]),
          fx="gull", sfx=[(0.2, "whoosh"), (0.55, "squawk")], shake=[(0.6, 8)]),
        L("d", "That bird... is going DOWN.", ["ms_d", "cu_d"],
          dict(MALL, r_x=420, n_x=640, d_x=1000, stars=5, d_mood="angry", d_shades=True, d_arms="point",
               d_face=1, d_look=(1, -1)), sfx=[(0, "ding"), (0.15, "ding"), (0.3, "ding")], dutch=5),
    ]),
    dict(num=5, title="Wasted", beats=[
        L("r", "Watch this! Real life GTA stunt!", "track_r",
          dict(scene="beach", r_x=300, r_vx=170, r_legs="skate", r_arms="balance", r_face=1, skate=True,
               n_x=200, n_face=1, n_arms="hips", n_mood="flat")),
        A(1.5, "fixed", dict(scene="beach", cam_c=(830, 385), r_x0=680, rock_x=880, r_legs="skate",
                              r_arms="balance", r_face=1, skate=True, n_x=430, n_face=1), fx="crash",
          sfx=[(0.3, "bonk"), (0.85, "thud")], shake=[(0.85, 18)], flash=[0.85]),
        L("r", "Wasted.", ["ms_r", "cu_r"], dict(LYING, gray=True, skate=True), punch=0.1, dutch=-6),
        L("n", "Babe, you scraped your knee.", ["ms_n", "ms2"],
          dict(LYING, skate=True, n_x=1260, n_arms="hips", n_mood="flat")),
        L("r", "Respawn me at the hospital.", "cu_r", dict(LYING, skate=True)),
    ]),
    dict(num=6, title="Release Night", beats=[
        L("r", "First in line, all night long! We're ready!", ["wide", "ms2"],
          dict(STORE, r_arms="up", r_bounce=True, n_tired=True, n_face=1, o_face=-1), flash=[0.0]),
        L("o", "Sorry, sweetie. I've been here since Tuesday.", ["ms2", "ms_o"],
          dict(STORE, o_face=-1, r_shock=True, n_tired=True, n_face=1, r_look=(1, 0)), punch=1.6),
        L("n", "Grandma... read the sign.", ["ms_n", "ms2"],
          dict(STORE, n_face=1, n_arms="point", o_face=-1, pair=("n", "o"))),
        A(1.2, "sign", dict(STORE), sfx=[(0.05, "trombone")]),
        L("o", "Oh, I pre-loaded it at home.", "cu_o", dict(STORE, o_face=-1, o_wink=True, o_shades=False)),
        L("r", "Grandma... you're my hero.", "cu_r", dict(STORE, r_brow=1, r_look=(1, -0.3)), dutch=4),
    ]),
    dict(num=7, title="Pro Gamer Granny", beats=[
        L("r", "Grandma, GTA is way too hard for you.", ["wide", "ms2"], dict(GRANNY, r_arms="hips")),
        L("o", "Kid, I was doing getaways before you were born.", ["ms_o", "cu_o"],
          dict(GRANNY, o_mood="angry", o_brow=1), punch=2.0),
        L("n", "In the game... right, Grandma?", "ms_n", dict(GRANNY, n_face=-1, n_mood="flat", n_brow=1)),
        A(1.1, "cu_o", dict(GRANNY, o_shades=True, o_wink=False), sfx=[(0.0, "siren")], punch=0.0, dutch=6),
        L("r", "GRANDMA?!", "cu_r", dict(GRANNY, r_shock=True, r_arms="up"), flash=[0.0], shake=[(0.0, 10)]),
    ]),
    dict(num=8, title="Mall Cop", beats=[
        L("r", "Real life GTA mode: activated!", "track_r",
          dict(MALL, r_x=150, r_vx=320, r_legs="run", r_face=1, r_shades=True, n_x=-400, d_x=2000)),
        L("d", "Sir. Walking only.", ["ms2", "ms_d"],
          dict(MALL, r_x=820, d_x=1040, d_face=-1, d_arms="stop", d_shades=True, r_shock=True, r_face=1,
               n_x=-400, pair=("r", "d")), punch=0.4),
        A(1.6, "fixed", dict(MALL, cam_c=(960, 385), r_x=820, r_vx=60, r_legs="walk", r_wspd=0.35, r_face=1,
                             r_shades=True, d_x=1040, d_face=-1, d_shades=True, d_arms="hips", n_x=-400,
                             d_look=(1, 0)), sfx=[(0.2 + i * 0.4, "tick") for i in range(4)]),
        L("n", "Slowest getaway in history.", "ms_n", dict(MALL, n_x=560, n_face=1, n_mood="flat", r_x=960, d_x=1180)),
        L("d", "...I'll allow it.", "cu_d", dict(MALL, n_x=560, r_x=960, d_x=1180, d_face=-1, d_shades=True)),
    ]),
]

GAP, LEAD = 0.14, 0.06
OUTRO = 0.9


def build_timeline(ep):
    t = 0.0
    segs = []
    for b in ep["beats"]:
        s = dict(b, start=t)
        if b["type"] == "line":
            clip = base.tts(b["who"], b["text"])
            s.update(clip=clip, env=base.mouth_envelope(clip), dur=len(clip) / SR + GAP + LEAD)
        segs.append(s)
        t += s["dur"]
    last = segs[-1]
    cam = last["cam"] if isinstance(last["cam"], str) else last["cam"][1]
    ost = dict(last["state"])
    for k in ost.get("cast", ["n", "r"]):
        if not ost.get(k + "_rot"):
            ost[k + "_arms"] = "wave"
    for key in ("r_vx", "n_vx", "d_vx"):
        ost.pop(key, None)
    segs.append(dict(type="outro", dur=OUTRO, cam=cam, state=ost, start=t))
    total = t + OUTRO
    if total > MAX_LEN:
        raise SystemExit(f"Episode {ep['num']} is {total:.2f}s — over the {MAX_LEN}s limit")
    return segs, total


def sound(name, dur=1.0):
    t = np.arange(int(dur * SR)) / SR
    if name == "siren":
        tt = np.arange(int(1.1 * SR)) / SR
        f = np.where((tt * 3) % 1 < 0.5, 960, 720)
        ph = np.cumsum(f) / SR
        return np.sin(2 * np.pi * ph) * 0.25 * np.minimum(1, tt * 10)
    return sfx(name, dur)


def music(total):
    """Light synth beat (100 BPM) — background bed."""
    n = int(total * SR) + SR
    out = np.zeros(n)
    beat = 0.6
    chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (130.8, 164.8, 196.0), (196.0, 246.9, 293.7)]
    rng = np.random.default_rng(1)
    for b in range(int(total / beat) + 2):
        i = int(b * beat * SR)
        tt = np.arange(int(0.25 * SR)) / SR
        kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14) * 0.7
        out[i:i + len(kick)] += kick[: max(0, n - i)]
        j = int((b + 0.5) * beat * SR)
        th = np.arange(int(0.05 * SR)) / SR
        hat = rng.standard_normal(len(th)) * np.exp(-th * 70) * 0.12
        out[j:j + len(hat)] += hat[: max(0, n - j)]
        ch = chords[(b // 4) % 4]
        tb = np.arange(int(beat * SR)) / SR
        ph = ch[0] / 2 * tb
        bass = (2 * (ph % 1) - 1) * 0.16 * np.exp(-tb * 3)
        pad = sum(np.sin(2 * np.pi * f * tb) for f in ch) * 0.035
        seg = bass + pad
        out[i:i + len(seg)] += seg[: max(0, n - i)]
    return out[: int(total * SR)]


def mix_audio(segs, total):
    n = int(total * SR)
    speech = np.zeros(n + 3 * SR)
    fx = np.zeros(n + 3 * SR)

    def place(buf, sig, at, gain=1.0):
        i = int(at * SR)
        buf[i:i + len(sig)] += sig[: len(buf) - i] * gain

    for s in segs:
        if s["type"] == "line":
            place(speech, s["clip"], s["start"] + LEAD, 1.0)
        if s["state"].get("car") and s["type"] != "outro":
            place(fx, sfx("engine", s["dur"]), s["start"], 0.35)
        for off, name in s.get("sfx", []):
            place(fx, sound(name, 1.2 if name == "vroom" else 1.0), s["start"] + off, 0.5)
    place(fx, sfx("ding"), total - OUTRO + 0.05, 0.4)
    speech, fx = speech[:n], fx[:n]
    env = np.convolve(np.abs(speech), np.ones(2000) / 2000, mode="same")
    duck = np.where(env > 0.01, 0.35, 1.0)
    duck = np.convolve(duck, np.ones(1500) / 1500, mode="same")
    out = speech + fx + music(total) * 0.5 * duck
    out = out / max(1e-6, np.abs(out).max()) * 0.9
    return (out * 32767).astype(np.int16)


# --------------------------------------------------------------------------
# Frame rendering
# --------------------------------------------------------------------------
def wrap(d, words, fnt, maxw):
    lines, cur = [], []
    for i, wd in enumerate(words):
        trial = " ".join(w for _, w in cur + [(i, wd)])
        if cur and d.textlength(trial, font=fnt) > maxw:
            lines.append(cur)
            cur = []
        cur.append((i, wd))
    lines.append(cur)
    return lines


def caption(img, who, text, prog):
    """Big word-by-word captions (current word highlighted)."""
    d = ImageDraw.Draw(img)
    w, h = base.W, base.H
    words = text.split()
    weights = np.cumsum([len(x) + 2 for x in words])
    cur = int(np.searchsorted(weights / weights[-1], min(0.999, max(0.0, prog)), side="right"))
    size = 66 if SHORTS else 36
    fnt = base.font(size)
    lines = wrap(d, words, fnt, w - (120 if SHORTS else 200))
    y0 = 1330 if SHORTS else h - 40 - (len(lines) - 1) * 44
    lh = 82 if SHORTS else 44
    d.text((w / 2, y0 - (64 if SHORTS else 40)), NAMES[who], font=base.font(44 if SHORTS else 24),
           fill=NAME_COL[who], anchor="mm", stroke_width=5 if SHORTS else 3, stroke_fill=INK)
    for li, line in enumerate(lines):
        full = " ".join(wd for _, wd in line)
        x = w / 2 - d.textlength(full, font=fnt) / 2
        for i, wd in line:
            col = (255, 230, 60) if i == cur else (255, 255, 255)
            d.text((x, y0 + li * lh), wd, font=fnt, fill=col, anchor="lm", stroke_width=7 if SHORTS else 4,
                   stroke_fill=INK)
            x += d.textlength(wd + " ", font=fnt)


def badge(img, ep, t):
    if t > 2.4:
        return
    d = ImageDraw.Draw(img)
    k = ease(min(1, t / 0.3)) * (1 - ease(max(0, (t - 2.1) / 0.3)))
    x = -420 + 440 * k if SHORTS else -320 + 340 * k
    y = 150 if SHORTS else 22
    s = 1.0 if SHORTS else 0.62
    d.rounded_rectangle([x, y, x + 400 * s, y + 116 * s], radius=22 * s, fill=(40, 20, 70), outline=INK, width=4)
    d.text((x + 20 * s, y + 38 * s), "RICO & NINA", font=base.font(int(46 * s)), fill=(255, 236, 120), anchor="lm",
           stroke_width=3, stroke_fill=INK)
    d.text((x + 20 * s, y + 88 * s), f"EP.{ep['num']}  {ep['title'].upper()}", font=base.font(int(28 * s)),
           fill=(255, 140, 210), anchor="lm")


def follow_card(img, ep, lt):
    d = ImageDraw.Draw(img)
    w, h = base.W, base.H
    k = ease(min(1, lt / 0.25))
    pulse = 1 + 0.06 * math.sin(lt * 16)
    s = (1.0 if SHORTS else 0.65) * k * pulse
    cy = 1500 if SHORTS else h * 0.78
    bw, bh = 560 * s, 130 * s
    d.rounded_rectangle([w / 2 - bw / 2, cy - bh / 2, w / 2 + bw / 2, cy + bh / 2], radius=bh / 2,
                        fill=(230, 30, 50), outline=INK, width=5)
    if s > 0.2:
        d.text((w / 2, cy), "FOLLOW for more!", font=base.font(int(54 * s)), fill=(255, 255, 255), anchor="mm",
               stroke_width=3, stroke_fill=INK)
        nxt = "next: Ep." + str(ep["num"] % len(EPISODES) + 1)
        d.text((w / 2, cy + bh / 2 + 44 * s), nxt, font=base.font(int(40 * s)), fill=(255, 236, 120), anchor="mm",
               stroke_width=4, stroke_fill=INK)


def dutch(img, deg):
    w, h = img.size
    sc = math.cos(math.radians(abs(deg))) + max(w / h, h / w) * math.sin(math.radians(abs(deg))) + 0.01
    big = img.resize((int(w * sc), int(h * sc)), Image.BICUBIC).rotate(deg, resample=Image.BICUBIC)
    x0, y0 = (big.width - w) // 2, (big.height - h) // 2
    return big.crop((x0, y0, x0 + w, y0 + h))


def hud_stars(img, n, lt):
    d = ImageDraw.Draw(img)
    w = base.W
    r = 34 if SHORTS else 22
    y = 230 if SHORTS else 40
    for i in range(5):
        cx = w - (60 if SHORTS else 40) - i * r * 2.3
        filled = (4 - i) < n
        pop = 1 + (0.5 * max(0, 1 - lt * 4) if filled else 0)
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r * pop * (1 if k % 2 == 0 else 0.45)
            pts.append((cx + math.cos(a) * rr, y + math.sin(a) * rr))
        d.polygon(pts, fill=(255, 255, 255) if filled else (60, 60, 70), outline=INK, width=4)


def motion_blur(img, px):
    a = np.asarray(img).astype(np.float32)
    n = 7
    acc = np.zeros_like(a)
    for k in range(n):
        acc += np.roll(a, int((k - n // 2) * px / n), axis=1)
    return Image.fromarray((acc / n).astype(np.uint8))


def render_frame(ep, segs, fi):
    t = fi / FPS
    seg = segs[-1]
    for s in segs:
        if s["start"] <= t < s["start"] + s["dur"]:
            seg = s
            break
    lt = t - seg["start"]
    dur = seg["dur"]
    st = {}
    for k, x in DEFAULT_X.items():
        st[k + "_x"], st[k + "_y"] = x, GROUND
    st["cast"] = ["n", "r"]
    st.update(seg["state"])
    for k in st["cast"]:
        st[k + "_blink"] = (t * 1000 + ord(k) * 37) % (2900 + ord(k) * 5) < 110
        vt = st.get(k + "_vt", 99)
        st[k + "_x"] += st.get(k + "_vx", 0) * min(lt, vt)
        if lt > vt:
            st[k + "_legs"] = "stand"
    if st.get("car"):
        st["scroll"] = st.get("speed", 0) * t
        bump = math.sin(t * 22) * (1.5 if st.get("speed", 0) < 200 else 4)
        st["r_x"], st["n_x"] = st["car_x"] + 40, st["car_x"] - 110
        st["r_y"] = st["n_y"] = st["gy"] + 190 + bump
    prog = 0.0
    if seg["type"] == "line":
        idx = int((lt - LEAD) * FPS)
        level = seg["env"][idx] if 0 <= idx < len(seg["env"]) else 0.0
        st[seg["who"] + "_talk"] = level
        st[seg["who"] + "_speaking"] = True
        prog = (lt - LEAD) / (len(seg["clip"]) / SR)
    overlays = []
    if seg.get("fx"):
        FX[seg["fx"]](st, lt, dur, overlays)
    if st.get("skate") and "board_x" not in st:
        st["board_x"] = st["r_x"]

    # ---- camera: move between shots + handheld drift + shake + whip + crash zoom
    heads = {k: head_world(SPECS[k], st[k + "_x"], st[k + "_y"], st, t) for k in SPECS}
    cam = seg["cam"]
    a_name, b_name = (cam, cam) if isinstance(cam, str) else cam
    ca, cb = shot_cam(a_name, st, heads, t), shot_cam(b_name, st, heads, t)
    k = ease(lt / dur)
    cx, cy, z = lerp(ca[0], cb[0], k), lerp(ca[1], cb[1], k), lerp(ca[2], cb[2], k)
    if a_name == b_name:
        z *= 1 + 0.06 * (lt / dur)
    if seg.get("punch") is not None and lt >= seg["punch"]:
        z *= 1 + 0.3 * ease((lt - seg["punch"]) / 0.12)
    cx += (math.sin(t * 0.9) * 5 + math.sin(t * 2.3) * 2) / z
    cy += (math.cos(t * 1.1) * 4) / z
    shake = st.get("shake", 0.0)
    for ts, amp in seg.get("shake", []):
        if lt >= ts:
            shake += amp * math.exp(-(lt - ts) * 6)
    if shake:
        rnd = random.Random(fi)
        cx += rnd.uniform(-1, 1) * shake / z
        cy += rnd.uniform(-1, 1) * shake / z
    blur = 0
    if seg.get("whip") and lt < 0.22:
        kk = 1 - ease(lt / 0.22)
        cx += seg["whip"] * kk * 650 / z
        blur = kk * (180 if SHORTS else 140)

    img = Image.new("RGB", (base.W * SS, base.H * SS))

    def layer(par):
        return Pen(img, Cam(640 + (cx - 640) * par, 400 + (cy - 400) * par, 1 + (z - 1) * par))

    BACKGROUNDS[st["scene"]](layer, t, st)
    pn = Pen(img, Cam(cx, cy, z))
    seated = bool(st.get("car"))
    if st.get("skate"):
        skateboard(pn, st["board_x"], GROUND, 0)
    draw_cast(pn, st, t, seated)
    if seated:
        draw_car_body(pn, st["car_x"], st["r_y"] - 190, t, st.get("speed", 0))
    for o in overlays:
        o(pn)
    img = img.resize((base.W, base.H), Image.LANCZOS)
    if st.get("gray"):
        g = ImageOps.grayscale(img).convert("RGB")
        img = Image.blend(g, Image.new("RGB", img.size, (60, 50, 50)), 0.15)
    if seg.get("dutch"):
        img = dutch(img, seg["dutch"] * ease(min(1, lt / 0.2)))
    if blur:
        img = motion_blur(img, blur)
    for tf in seg.get("flash", []):
        if 0 <= lt - tf < 0.16:
            img = Image.blend(img, Image.new("RGB", img.size, (255, 255, 255)), 0.75 * (1 - (lt - tf) / 0.16))
    if st.get("stars"):
        hud_stars(img, st["stars"], lt)
    badge(img, ep, t)
    if seg["type"] == "line":
        caption(img, seg["who"], seg["text"], prog)
    if seg["type"] == "outro":
        follow_card(img, ep, lt)
    return img


def render_episode(ep):
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Episode {ep['num']}: {ep['title']}")
    segs, total = build_timeline(ep)
    print(f"  length {total:.2f}s")
    wav_path = os.path.join(base.CACHE, f"rn3_ep{ep['num']}.wav")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(mix_audio(segs, total).tobytes())
    slug = ep["title"].lower().replace(" ", "_")
    out = os.path.join(OUT_DIR, f"rico_and_nina_ep{ep['num']}_{slug}{'_short' if SHORTS else ''}.mp4")
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{base.W}x{base.H}", "-r", str(FPS), "-i", "-", "-i", wav_path,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    for fi in range(int(total * FPS)):
        proc.stdin.write(render_frame(ep, segs, fi).tobytes())
    proc.stdin.close()
    proc.wait()
    print("  ->", out)
    return out


def main():
    args = sys.argv[1:]
    set_format("--shorts" in args)
    want = {int(a) for a in args if a.isdigit()}
    outs = [render_episode(ep) for ep in EPISODES if not want or ep["num"] in want]
    if len(outs) > 1:
        lst = os.path.join(base.CACHE, "rn3_concat.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{o}'\n" for o in outs)
        full = os.path.join(OUT_DIR, "rico_and_nina_all_episodes" + ("_short" if SHORTS else "") + ".mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", lst, "-c", "copy", full], check=True)
        print("All episodes ->", full)


if __name__ == "__main__":
    main()
