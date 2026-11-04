#!/usr/bin/env python3
"""
RICO & NINA — "Waiting for GTA VI"
A tiny code-generated cartoon about an (original) couple of superfans who
can't stop talking about GTA VI.

Same engine and drawing style as ../cartoon (flat colours, thick outlines,
big touching eyes, hard cuts), plus: full bodies with legs and a walk
cycle, a car with scrolling streets, and several locations per episode.

Every episode is <= 15 s with English voices (Piper TTS).

Usage:
    python3 make_episodes.py              # 1280x720 landscape
    python3 make_episodes.py --shorts     # 1080x1920 YouTube Shorts
    python3 make_episodes.py --shorts 2   # just episode 2
"""
import math
import os
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cartoon"))
import make_episodes as base  # noqa: E402  (shared drawing / audio engine)
from make_episodes import INK, YELLOW, Cam, Pen, ease, lerp, eyes, mouth, poof, smoke  # noqa: E402

FPS, SR, SS = base.FPS, base.SR, base.SS
TITLE_DUR = 1.5
MAX_LEN = 15.0
SHORTS = False
OUT_DIR = os.path.join(HERE, "output")

# English voices: Rico (male US), Nina (female US)
base.VOICES["R"] = ("en/en_US/ryan/high/en_US-ryan-high", 0.97, 1.05, 0.95)
base.VOICES["N"] = ("en/en_US/amy/medium/en_US-amy-medium", 1.04, 1.02, 0.95)


def set_format(shorts):
    global SHORTS, OUT_DIR
    SHORTS = shorts
    base.W, base.H = (1080, 1920) if shorts else (1280, 720)
    OUT_DIR = os.path.join(HERE, "output", "shorts" if shorts else "")


def W():
    return base.W


def H():
    return base.H


def wtext(pn, x, y, text, size, fill, stroke=4, stroke_fill=INK):
    px, py = pn.c.p(x, y)
    pn.d.text((px, py), text, font=base.font(max(6, int(pn.c.s(size)))), fill=fill, anchor="mm",
              stroke_width=max(1, int(pn.c.s(stroke))), stroke_fill=stroke_fill)


# --------------------------------------------------------------------------
# Extra sound effects
# --------------------------------------------------------------------------
def sfx(name, dur=1.0):
    t = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(3)
    if name == "engine":
        f = 48 + 6 * np.sin(2 * np.pi * 0.7 * t)
        ph = np.cumsum(f) / SR
        return (2 * (ph % 1) - 1) * 0.18 * np.minimum(1, t * 8) * np.minimum(1, (dur - t) * 8)
    if name == "vroom":
        f = 50 + 260 * (1 - np.exp(-t * 3))
        ph = np.cumsum(f) / SR
        return (2 * (ph % 1) - 1) * 0.35 * np.minimum(1, t * 20) * np.exp(-np.maximum(0, t - dur + 0.3) * 8)
    if name == "tick":
        tt = t[: int(0.05 * SR)]
        return np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 90) * 0.6
    if name == "wind":
        n = np.convolve(rng.standard_normal(len(t)), np.ones(60) / 60, mode="same") * 6
        return n * np.sin(np.pi * t / dur) * 0.6
    if name == "intro":   # synth-wave sting
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
# Characters (original designs)
# --------------------------------------------------------------------------
R_SKIN = (234, 180, 136)
R_SKIN_D = (200, 146, 108)
R_HAIR = (72, 46, 30)
SHIRT = (246, 110, 152)
SHORTS_C = (206, 180, 126)

N_SKIN = (176, 116, 82)
N_HAIR = (216, 86, 48)
TOP = (38, 186, 172)
JEANS = (64, 104, 178)

ARM_POSES = {  # (dx, dy) of each hand from the feet point, for left / right hands
    "rest": ((-70, -190), (70, -190)),
    "up": ((-96, -430), (96, -430)),
    "drive": ((38, -300), (78, -296)),
    "shrug": ((-92, -300), (92, -300)),
    "point": ((-70, -190), (130, -330)),
}


def legs(pn, x, y, yb, walking, ph, face, leg_c, pants_c, pants_len, shoe_c, hip_w, hip_y):
    for i, sx in enumerate((-1, 1)):
        p = ph + i * math.pi
        sw = math.sin(p) if walking else 0.0
        lift = max(0.0, math.cos(p)) * 16 if walking else 0.0
        hip = (x + sx * hip_w, yb - hip_y)
        foot = (x + sx * hip_w * 0.8 + sw * 34 * face, y - 16 - lift)
        knee = ((hip[0] + foot[0]) / 2 + 10 * face * (lift > 4), (hip[1] + foot[1]) / 2)
        pn.stroke([hip, knee, foot], leg_c, 26)
        if pants_len >= 1:
            pn.stroke([hip, knee, foot], pants_c, 30)
        elif pants_len > 0:
            pn.stroke([hip, (lerp(hip[0], knee[0], 1.3 * pants_len * 2), lerp(hip[1], knee[1], 1.3 * pants_len * 2))],
                      pants_c, 34)
        pn.blob([(foot[0] + 8 * face, foot[1] + 4, 27, 12), (foot[0] + 22 * face, foot[1] + 6, 13, 9)], shoe_c)
        pn.line([(foot[0] - 14 + 8 * face, foot[1] + 9), (foot[0] + 30 + 8 * face, foot[1] + 9)], (250, 250, 250), 4)


def arms(pn, x, yb, st, key, t, skin, sleeve, sh_w, sh_y, walking, ph):
    pose = st.get(key + "_arms", "rest")
    hands = ARM_POSES[pose]
    out = []
    for i, sx in enumerate((-1, 1)):
        hx, hy = hands[i]
        if pose == "up":
            hy += math.sin(t * 16 + i) * 10
        if walking and pose == "rest":
            hx += math.sin(ph + (1 - i) * math.pi) * 22
        sh = (x + sx * sh_w, yb - sh_y)
        hand = (x + hx, yb + hy)
        pn.limb(sh, hand, 22, skin)
        pn.ellipse(sh[0] + sx * 2, sh[1] + 10, 21, 25, sleeve, 4)
        out.append(hand)
    return out


def draw_rico(pn, x, y, st, t, seated=False):
    walking = st.get("r_walk", False) and not seated
    face = st.get("r_face", 1)
    ph = t * 9
    yb = y - (abs(math.sin(ph)) * 7 if walking else 2 + math.sin(t * 2) * 2)
    if st.get("r_bounce"):
        yb -= abs(math.sin(t * 9)) * 18
    if not seated:
        legs(pn, x, y, yb, walking, ph, face, R_SKIN, SHORTS_C, 0.5, (250, 250, 250), 26, 196)
        pn.poly([(x - 56, yb - 212), (x + 56, yb - 212), (x + 60, yb - 140), (x + 4, yb - 150), (x - 60, yb - 140)],
                SHORTS_C, 4)
    # shirt (Hawaiian)
    pn.poly([(x - 62, yb - 336), (x + 62, yb - 336), (x + 56, yb - 196), (x - 56, yb - 196)], SHIRT, 4)
    for fx, fy in ((-34, -300), (20, -260), (-10, -222), (38, -318), (-40, -236)):
        pn.star(x + fx, yb + fy, 10, (255, 236, 120), 2)
    pn.poly([(x - 20, yb - 336), (x + 20, yb - 336), (x, yb - 300)], R_SKIN, 3)
    if st.get("r_arms") == "drive":
        pn.ellipse(x + 64, yb - 300, 32, 40, (40, 40, 44), 4)
        pn.ellipse(x + 64, yb - 300, 22, 30, (150, 220, 230), 0)
    hands = arms(pn, x, yb, st, "r", t, R_SKIN, SHIRT, 60, 324, walking, ph)
    for h in hands:
        pn.ellipse(h[0], h[1], 12, 12, R_SKIN, 4)
    # head
    hy = yb - 400
    pn.rect(x - 18, hy + 50, x + 18, hy + 70, R_SKIN, 4)
    pn.blob([(x, hy, 50, 58), (x + 4 * face, hy + 38, 45, 30), (x - 50, hy + 6, 10, 15), (x + 50, hy + 6, 10, 15)],
            R_SKIN)
    if st.get("r_bigbeard"):
        pn.blob([(x + 4, hy + 50, 52, 36), (x + 4, hy + 100, 46, 48), (x + 2, hy + 150, 32, 40),
                 (x, hy + 190, 18, 24)], R_HAIR, 4)
    else:
        pn.ellipse(x + 4 * face, hy + 46, 36, 18, R_SKIN_D, 0)             # stubble
    hair_off = -10 if st.get("r_wind") else 0
    pn.blob([(x - 8 + hair_off, hy - 48, 46, 22), (x + 22 + hair_off * 2, hy - 58, 36, 20),
             (x + 46 + hair_off * 3, hy - 44, 14, 16), (x - 44, hy - 30, 12, 22)], R_HAIR, 4)
    ex = x + 4 * face
    eyes(pn, [(ex - 17, hy - 12), (ex + 17, hy - 12)], 16, 20, st.get("r_look", (face, 0)),
         st.get("r_blink", False), R_SKIN, st.get("r_brow", 0.0), st.get("r_shock", False), False, t)
    if st.get("r_shades"):
        for sx in (-1, 1):
            pn.rect(ex + sx * 17 - 19, hy - 24, ex + sx * 17 + 19, hy - 2, (24, 24, 30), 3, 8)
        pn.line([(ex - 4, hy - 18), (ex + 4, hy - 18)], INK, 4)
    pn.ellipse(x + 8 * face, hy + 12, 9, 12, R_SKIN, 4)
    mouth(pn, x + 4 * face, hy + 36, st.get("r_talk", 0.0), 16, smile=not st.get("r_flat"))


def draw_nina(pn, x, y, st, t, seated=False):
    walking = st.get("n_walk", False) and not seated
    face = st.get("n_face", 1)
    ph = t * 9 + 1.3
    yb = y - (abs(math.sin(ph)) * 6 if walking else 2 + math.sin(t * 2.3 + 1) * 2)
    if st.get("n_bounce"):
        yb -= abs(math.sin(t * 9 + 1)) * 18
    hy = yb - 360
    wind = -14 if st.get("n_wind") else 0
    # big curly hair, behind the head
    curls = []
    for i in range(11):
        a = math.pi * (0.95 + 1.1 * i / 10)
        curls.append((x + math.cos(a) * 62 + wind, hy - 6 + math.sin(a) * 58, 30, 30))
    curls += [(x - 54 + wind, hy + 34, 26, 30), (x + 54 + wind, hy + 34, 26, 30), (x + wind, hy - 30, 60, 46)]
    pn.blob(curls, N_HAIR, 4)
    if not seated:
        legs(pn, x, y, yb, walking, ph, face, N_SKIN, JEANS, 1, (226, 52, 60), 20, 186)
        pn.poly([(x - 44, yb - 204), (x + 44, yb - 204), (x + 48, yb - 160), (x - 48, yb - 160)], JEANS, 4)
    pn.rect(x - 38, yb - 226, x + 38, yb - 200, N_SKIN, 4)               # midriff
    pn.poly([(x - 48, yb - 300), (x + 48, yb - 300), (x + 42, yb - 222), (x - 42, yb - 222)], TOP, 4)
    pn.line([(x - 40, yb - 262), (x + 40, yb - 262)], (250, 240, 120), 5, caps=False)
    hands = arms(pn, x, yb, st, "n", t, N_SKIN, TOP, 46, 290, walking, ph)
    for h in hands:
        pn.ellipse(h[0], h[1], 11, 11, N_SKIN, 4)
    pn.rect(x - 15, hy + 44, x + 15, hy + 64, N_SKIN, 4)
    pn.blob([(x, hy, 44, 50), (x + 3 * face, hy + 30, 36, 25), (x - 44, hy + 6, 9, 13), (x + 44, hy + 6, 9, 13)], N_SKIN)
    for sx in (-1, 1):                                                   # hoop earrings
        pn.ellipse(x + sx * 46, hy + 26, 9, 11, (250, 200, 60), 3)
        pn.ellipse(x + sx * 46, hy + 26, 4, 6, N_SKIN, 0)
    pn.blob([(x - 22 + wind, hy - 40, 30, 16), (x + 16 + wind, hy - 44, 32, 16), (x + 40 + wind, hy - 30, 14, 14)],
            N_HAIR, 4)
    for sx in (-1, 1):                                                   # sunglasses on her head
        pn.ellipse(x + sx * 17 + wind, hy - 56, 16, 10, (250, 216, 60), 3)
    ex = x + 3 * face
    eyes(pn, [(ex - 16, hy - 10), (ex + 16, hy - 10)], 15, 19, st.get("n_look", (-face, 0)),
         st.get("n_blink", False), N_SKIN, st.get("n_brow", 0.0), st.get("n_shock", False), False, t)
    for sx in (-1, 1):                                                   # lashes
        pn.line([(ex + sx * 30, hy - 22), (ex + sx * 38, hy - 30)], INK, 3)
    pn.ellipse(x + 6 * face, hy + 10, 8, 10, N_SKIN, 4)
    m = st.get("n_talk", 0.0)
    if m < 0.15:
        pn.blob([(x + 3 * face - 6, hy + 30, 9, 5), (x + 3 * face + 6, hy + 30, 9, 5)], (206, 52, 76), 3)
    else:
        mouth(pn, x + 3 * face, hy + 26, m, 14)


# --------------------------------------------------------------------------
# Car + backgrounds (all extend far in x so the camera can follow walkers)
# --------------------------------------------------------------------------
def draw_car_body(pn, cx, gy, t, speed):
    spin = -t * speed / 40
    pn.blob([(cx - 40, gy - 92, 220, 52), (cx + 150, gy - 80, 90, 40), (cx - 190, gy - 84, 60, 44)],
            (54, 196, 210), 4)
    pn.line([(cx - 250, gy - 92), (cx + 230, gy - 92)], (246, 110, 152), 10, caps=False)
    pn.line([(cx - 30, gy - 130), (cx - 30, gy - 50)], INK, 3, caps=False)
    pn.rect(cx - 70, gy - 108, cx - 44, gy - 100, (230, 230, 235), 2, 3)
    pn.stroke([(cx + 100, gy - 140), (cx + 70, gy - 210)], (190, 236, 246), 8, 3)
    pn.ellipse(cx + 236, gy - 92, 12, 10, (255, 236, 120), 3)
    pn.ellipse(cx - 258, gy - 96, 9, 10, (230, 60, 60), 3)
    for wx in (cx - 150, cx + 140):
        pn.ellipse(wx, gy - 38, 40, 40, (34, 32, 38), 4)
        pn.ellipse(wx, gy - 38, 20, 20, (200, 200, 210), 3)
        for k in range(3):
            a = spin + k * 2 * math.pi / 3
            pn.line([(wx, gy - 38), (wx + math.cos(a) * 18, gy - 38 + math.sin(a) * 18)], INK, 4, caps=False)


def palm(pn, x, gy, h=300, sway=0.0, dark=None):
    trunk = (150, 104, 62) if dark is None else dark
    leaf = (60, 170, 90) if dark is None else dark
    top = (x + 40 + sway, gy - h)
    pn.stroke([(x, gy), (x + 18, gy - h * 0.5), top], trunk, 18, 0 if dark else 4)
    for k in range(6):
        a = -math.pi * (0.05 + 0.9 * k / 5)
        tip = (top[0] + math.cos(a) * 110, top[1] + math.sin(a) * 50 + 40)
        mid = (top[0] + math.cos(a) * 60, top[1] + math.sin(a) * 50 - 6)
        pn.stroke([top, mid, tip], leaf, 14, 0 if dark else 4)


def bg_living(pn, t, st):
    pn.rect(-2000, -800, 4000, 600, (246, 200, 162), 0)
    for i in range(-20, 40):
        pn.rect(i * 120, -800, i * 120 + 50, 590, (240, 190, 150), 0)
    # window: it's snowing (they do NOT live in Vice City)
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
    # sunset poster
    pn.rect(470, 150, 670, 320, (255, 255, 255), 4)
    pn.rect(482, 162, 658, 308, (250, 120, 150), 0)
    pn.rect(482, 236, 658, 308, (255, 176, 110), 0)
    pn.ellipse(570, 236, 40, 40, (255, 226, 120), 0)
    pn.rect(482, 270, 658, 308, (90, 60, 140), 0)
    palm(pn, 520, 300, 110, 0, dark=(60, 30, 80))
    # couch
    pn.rect(360, 430, 780, 560, (100, 120, 200), 4, 30)
    pn.rect(340, 480, 400, 590, (90, 108, 186), 4, 20)
    pn.rect(740, 480, 800, 590, (90, 108, 186), 4, 20)
    # TV on a cabinet + console
    pn.rect(860, 470, 1150, 600, (130, 86, 54), 4, 6)
    pn.rect(960, 490, 1050, 520, (30, 30, 34), 3, 6)
    pn.ellipse(1032, 505, 4, 4, (90, 220, 255), 0)
    pn.rect(870, 290, 1140, 462, (30, 30, 34), 4, 8)
    sx0, sy0, sx1, sy1 = 884, 302, 1126, 450
    if st.get("tv_count") is not None:
        pn.rect(sx0, sy0, sx1, sy1, (20, 24, 60), 0)
        wtext(pn, 1005, 340, "GTA VI TRAILER", 22, (255, 140, 200), 3)
        wtext(pn, 1005, 380, "watched:", 16, (255, 255, 255), 2)
        wtext(pn, 1005, 420, f"{st['tv_count']:,}", 34, (255, 230, 90), 3)
    else:
        pn.rect(sx0, sy0, sx1, sy1, (250, 120, 150), 0)
        pn.rect(sx0, sy0 + 74, sx1, sy1, (255, 176, 110), 0)
        pn.ellipse(1005, sy0 + 76, 34, 34, (255, 226, 120), 0)
        pn.rect(sx0, sy0 + 100, sx1, sy1, (90, 60, 140), 0)
        palm(pn, 920, sy1, 120, math.sin(t) * 4, dark=(60, 30, 80))
        wtext(pn, 1005, 330, "GTA VI", 26, (255, 255, 255), 3)
    pn.rect(-2000, 590, 4000, 606, (120, 80, 50), 4)
    pn.rect(-2000, 606, 4000, 1500, (196, 150, 120), 0)
    pn.ellipse(640, 680, 420, 46, (230, 120, 90), 4)


def bg_beach(pn, t, st):
    bands = [(-800, (250, 96, 150)), (120, (255, 130, 140)), (230, (255, 160, 120)), (330, (255, 196, 120))]
    for y0, c in bands:
        pn.rect(-2000, y0, 4000, 440, c, 0)
    pn.ellipse(900, 400, 110, 110, (255, 226, 110), 0)
    for k in range(4):
        pn.rect(780, 380 + k * 16, 1020, 386 + k * 16, (255, 196, 120), 0)
    pn.rect(-2000, 430, 4000, 530, (60, 156, 206), 0)
    for i in range(-20, 40):
        xx = i * 140 + (t * 20) % 140
        pn.line([(xx, 470 + (i % 3) * 18), (xx + 50, 470 + (i % 3) * 18)], (150, 210, 240), 4)
    pn.rect(-2000, 520, 4000, 1500, (246, 220, 160), 0)
    pn.line([(-2000, 522), (4000, 522)], INK, 4, caps=False)
    for i in range(-4, 10):
        palm(pn, -100 + i * 520, 560, 360, math.sin(t * 1.5 + i) * 8)
    for i in range(-10, 30):                                             # boardwalk
        pn.rect(i * 120, 640, i * 120 + 112, 700, (176, 124, 80), 3)


NEON = ["MOTEL", "DINER", "24/7", "ARCADE", "TACOS", "PAWN"]


def bg_street(pn, t, st):
    sc = st.get("scroll", 0.0)
    for y0, c in [(-800, (34, 18, 66)), (140, (70, 30, 100)), (300, (120, 50, 120))]:
        pn.rect(-2000, y0, 4000, 600, c, 0)
    P = 300
    off = (sc * 0.4) % P
    rnd = random.Random(9)
    cols = [(255, 170, 200), (130, 220, 230), (250, 220, 140), (190, 160, 255)]
    for i in range(-8, 18):
        bx = i * P - off
        k = (i + int(sc * 0.4 // P)) % 12
        bh = 180 + (k * 67) % 200
        c = cols[k % 4]
        pn.rect(bx, 590 - bh, bx + 250, 590, c, 4)
        for wy in range(int(590 - bh + 24), 560, 46):
            for wx in range(int(bx + 20), int(bx + 230), 50):
                lit = (wx * 7 + wy * 3 + k) % 5 != 0
                pn.rect(wx, wy, wx + 26, wy + 26, (255, 236, 150) if lit else (60, 50, 90), 2)
        if k % 2 == 0:
            name = NEON[k // 2 % len(NEON)]
            neon = (255, 80, 200) if k % 4 == 0 else (80, 240, 255)
            pn.rect(bx + 30, 590 - bh - 56, bx + 220, 590 - bh - 6, (30, 20, 50), 4, 10)
            wtext(pn, bx + 125, 590 - bh - 31, name, 28, neon, 3, (255, 255, 255))
    off2 = sc % 420
    for i in range(-6, 14):
        palm(pn, i * 420 - off2 + 60, 600, 330, math.sin(t * 1.5 + i) * 6, dark=(28, 16, 50))
    pn.rect(-2000, 590, 4000, 630, (150, 140, 160), 4)
    pn.rect(-2000, 630, 4000, 1500, (54, 52, 66), 0)
    off3 = sc % 200
    for i in range(-12, 30):
        pn.rect(i * 200 - off3, 700, i * 200 - off3 + 110, 712, (250, 220, 90), 0)
    if st.get("speedlines"):
        rnd = random.Random(int(t * 30))
        for _ in range(16):
            yy = rnd.uniform(-200, 760)
            xx = rnd.uniform(-400, 1800)
            pn.line([(xx, yy), (xx + rnd.uniform(160, 400), yy)], (255, 255, 255), 4)


BACKGROUNDS = {"living": bg_living, "beach": bg_beach, "street": bg_street}

# --------------------------------------------------------------------------
# Camera
# --------------------------------------------------------------------------
ZOOM = {  # landscape, shorts
    "wide": (1.0, 1.65), "cu": (1.9, 2.6), "car": (1.25, 1.85), "tv": (2.0, 2.4),
}


def camera(shot, st):
    zi = 1 if SHORTS else 0
    if shot == "wide":
        return (st["r_x"] + st["n_x"]) / 2, 400 + 30 * SHORTS, ZOOM["wide"][zi]
    if shot == "car":
        return st["car_x"] - 10, st["gy"] - 200, ZOOM["car"][zi]
    if shot == "tv":
        return 940, 380, ZOOM["tv"][zi]
    who = shot[-1]  # cu_r / cu_n
    hx = st[who + "_x"]
    hy = st[who + "_y"] - (400 if who == "r" else 360)
    return hx, hy + (110 if SHORTS else 80), ZOOM["cu"][zi]


# --------------------------------------------------------------------------
# Gag effects
# --------------------------------------------------------------------------
def fx_beard(st, lt, dur, ov):
    st["r_bigbeard"] = lt > 0.1
    if lt < 0.5:
        ov.append(lambda pn: poof(pn, st["r_x"], st["r_y"] - 330, lt / 0.5, (255, 255, 255), 0.6))


def fx_floor_it(st, lt, dur, ov):
    st.update(speedlines=lt > 0.25, r_shock=True, r_wind=True, n_wind=True, n_arms="up")


def fx_counter(st, lt, dur, ov):
    st["tv_count"] = 4806 + min(6, int(lt / dur * 7))


FX = {"beard": fx_beard, "floor_it": fx_floor_it, "counter": fx_counter}

# --------------------------------------------------------------------------
# Episodes
# --------------------------------------------------------------------------
LIVING = dict(scene="living", r_x=470, n_x=780)
BEACH = dict(scene="beach", r_x=360, n_x=640, r_walk=True, n_walk=True, r_vx=110, n_vx=110)
CAR = dict(scene="street", car=True, car_x=640, gy=700)
STREET_WALK = dict(scene="street", r_x=420, n_x=700, r_walk=True, n_walk=True, r_vx=90, n_vx=90,
                   r_look=(1, 0), n_look=(-1, 0))

EPISODES = [
    dict(num=1, title="Since Forever", beats=[
        dict(type="line", who="R", text="Nina! I've waited for GTA Six my whole life!", shot="wide",
             state=dict(LIVING, r_arms="up", r_bounce=True, r_brow=1)),
        dict(type="line", who="N", text="I know. You grew a beard while waiting.", shot="cu_n",
             state=dict(LIVING, n_arms="shrug")),
        dict(type="line", who="R", text="Worth it.", shot="cu_r", fx="beard",
             state=dict(LIVING), sfx=[(0.05, "poof")]),
        dict(type="line", who="R", text="Vice City, here we come!", shot="wide",
             state=dict(BEACH, r_bigbeard=True, r_shades=True, r_look=(1, 0), n_look=(1, 0)),
             sfx=[(0, "whoosh")]),
        dict(type="line", who="N", text="Babe. We live in Ohio.", shot="wide",
             state=dict(LIVING, r_bigbeard=True, r_flat=True, snow=3), sfx=[(0, "whoosh"), (0.2, "wind")]),
        dict(type="act", dur=0.9, shot="cu_r", state=dict(LIVING, r_bigbeard=True, r_flat=True, snow=3,
                                                         r_look=(0, 1))),
    ]),
    dict(num=2, title="Driving Lessons", beats=[
        dict(type="line", who="R", text="I'm practicing my driving for GTA Six.", shot="car",
             state=dict(CAR, speed=60, r_arms="drive", r_shades=True)),
        dict(type="line", who="N", text="Babe, we're going five miles an hour.", shot="cu_n",
             state=dict(CAR, speed=60, r_arms="drive", r_shades=True, n_flat=True)),
        dict(type="line", who="R", text="In real life, I follow the rules.", shot="cu_r",
             state=dict(CAR, speed=60, r_arms="drive", r_shades=True)),
        dict(type="act", dur=1.3, shot="car", fx="floor_it",
             state=dict(CAR, speed=1700, r_arms="drive", r_shades=True), sfx=[(0, "vroom")]),
        dict(type="line", who="R", text="Nina! The speed limit!", shot="car", fx="floor_it",
             state=dict(CAR, speed=1700, r_arms="drive", r_shades=True)),
        dict(type="line", who="N", text="Now THAT'S how you play GTA!", shot="cu_n", fx="floor_it",
             state=dict(CAR, speed=1700, r_arms="drive", r_shades=True)),
    ]),
    dict(num=3, title="The Trailer", beats=[
        dict(type="line", who="N", text="I've watched the GTA Six trailer a hundred times.", shot="wide",
             state=dict(STREET_WALK)),
        dict(type="line", who="R", text="A hundred? Amateur.", shot="cu_r",
             state=dict(STREET_WALK, r_shades=True, r_walk=False, n_walk=False, r_vx=0, n_vx=0)),
        dict(type="act", dur=1.3, shot="tv", fx="counter", sfx=[(0.1 + i * 0.18, "tick") for i in range(7)],
             state=dict(LIVING, r_x=420, n_x=640, tv_count=4806)),
        dict(type="line", who="R", text="I'm almost at five thousand.", shot="cu_r",
             state=dict(LIVING, r_x=420, n_x=640, tv_count=4812, r_look=(0.6, 0))),
        dict(type="line", who="N", text="Okay. We're going outside.", shot="wide",
             state=dict(LIVING, r_x=420, n_x=640, tv_count=4812, n_arms="point", n_brow=1, r_shock=True)),
        dict(type="line", who="R", text="Ahh! The sun! It burns!", shot="wide",
             state=dict(BEACH, r_shock=True, r_arms="up", r_vx=60, n_vx=60, n_look=(-1, 0)),
             sfx=[(0, "whoosh")]),
    ]),
]

GAP, LEAD = 0.16, 0.06


def build_timeline(ep):
    t = TITLE_DUR
    segs = []
    for b in ep["beats"]:
        s = dict(b, start=t)
        if b["type"] == "line":
            clip = base.tts(b["who"], b["text"])
            s.update(clip=clip, env=base.mouth_envelope(clip), dur=len(clip) / SR + GAP + LEAD)
        segs.append(s)
        t += s["dur"]
    total = t + 0.3
    if total > MAX_LEN:
        raise SystemExit(f"Episode {ep['num']} is {total:.2f}s — over the {MAX_LEN}s limit")
    return segs, total


def mix_audio(segs, total):
    out = np.zeros(int((total + 2) * SR))

    def place(sig, at, gain=1.0):
        i = int(at * SR)
        out[i:i + len(sig)] += sig[: len(out) - i] * gain

    place(sfx("intro"), 0.0, 0.8)
    for s in segs:
        if s["type"] == "line":
            place(s["clip"], s["start"] + LEAD, 1.0)
        if s.get("state", {}).get("car"):
            place(sfx("engine", s["dur"]), s["start"], 0.35)
        for off, name in s.get("sfx", []):
            place(sfx(name, 1.2 if name == "vroom" else 1.0), s["start"] + off, 0.5)
    out = out[: int(total * SR)]
    out = out / max(1e-6, np.abs(out).max()) * 0.9
    return (out * 32767).astype(np.int16)


def title_card(ep, t):
    w, h = W(), H()
    img = Image.new("RGB", (w * SS, h * SS))
    pn = Pen(img, Cam(640, 360, 1.0))
    top = 360 - h / 2
    for i, c in enumerate([(40, 20, 80), (110, 40, 120), (230, 90, 150), (255, 150, 120)]):
        pn.rect(-1000, top + i * h * 0.17, 3000, 3000, c, 0)
    pn.ellipse(640, 360 + h * 0.18, 150, 150, (255, 226, 110), 0)
    for k in range(5):
        yy = 360 + h * 0.18 + 30 + k * 26
        pn.rect(400, yy, 880, yy + 9, (255, 150, 120), 0)
    pn.rect(-1000, 360 + h * 0.27, 3000, 3000, (40, 20, 70), 0)
    for i in range(-2, 5):
        palm(pn, 640 + i * 300 - 450, 360 + h * 0.28, 260 if not SHORTS else 380, math.sin(t * 2 + i) * 6,
             dark=(30, 14, 50))
    cam2 = Cam(645, 330, 1.7) if SHORTS else Cam(640, 160, 0.48)
    pn2 = Pen(img, cam2)
    st = dict(r_arms="up", n_arms="up", r_shades=True, r_talk=0.6, n_talk=0.6, r_look=(0.5, 0.3),
              n_look=(-0.5, 0.3))
    draw_rico(pn2, 500, 660, st, t)
    draw_nina(pn2, 790, 660, st, t)
    img = img.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    pop = 0.6 + 0.4 * min(1.0, t / 0.25)
    if SHORTS:
        d.text((w / 2, 250), "RICO & NINA", font=base.font(int(118 * pop)), fill=(255, 236, 120), anchor="mm",
               stroke_width=9, stroke_fill=INK)
        d.text((w / 2, 360), "waiting for GTA VI", font=base.font(56), fill=(255, 140, 210), anchor="mm",
               stroke_width=6, stroke_fill=INK)
        d.text((w / 2, 450), f"Ep.{ep['num']}  {ep['title']}", font=base.font(56), fill=(255, 255, 255),
               anchor="mm", stroke_width=5, stroke_fill=INK)
    else:
        d.text((w / 2, 100), "RICO & NINA", font=base.font(int(92 * pop)), fill=(255, 236, 120), anchor="mm",
               stroke_width=7, stroke_fill=INK)
        d.text((w / 2, 172), "waiting for GTA VI", font=base.font(36), fill=(255, 140, 210), anchor="mm",
               stroke_width=4, stroke_fill=INK)
        d.text((w / 2, 222), f"Episode {ep['num']}:  {ep['title']}", font=base.font(34), fill=(255, 255, 255),
               anchor="mm", stroke_width=4, stroke_fill=INK)
    return img


def caption(img, who, text):
    d = ImageDraw.Draw(img)
    name = "RICO" if who == "R" else "NINA"
    w, h = W(), H()
    if SHORTS:
        lines, cur = [], ""
        for wd in text.split():
            trial = (cur + " " + wd).strip()
            if d.textlength(trial, font=base.font(58)) > w - 140 and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = trial
        lines.append(cur)
        y0 = 1380
        d.text((w / 2, y0), name, font=base.font(46), fill=(255, 140, 210), anchor="mm",
               stroke_width=5, stroke_fill=INK)
        for i, ln in enumerate(lines):
            d.text((w / 2, y0 + 70 + i * 70), ln, font=base.font(58), fill=(255, 255, 255), anchor="mm",
                   stroke_width=6, stroke_fill=INK)
    else:
        d.text((w / 2, h - 46), f"{name}: {text}", font=base.font(30), fill=(255, 255, 255), anchor="mm",
               stroke_width=4, stroke_fill=INK)


def render_frame(ep, segs, fi):
    t = fi / FPS
    if t < TITLE_DUR:
        return title_card(ep, t)
    seg = segs[-1]
    for s in segs:
        if s["start"] <= t < s["start"] + s["dur"]:
            seg = s
            break
    lt = t - seg["start"]
    st = dict(r_x=470, n_x=780, r_y=660, n_y=660)
    st.update(seg.get("state", {}))
    st["r_blink"] = (t * 1000) % 3100 < 120
    st["n_blink"] = (t * 1000 + 1500) % 3700 < 120
    st["r_x"] += st.get("r_vx", 0) * lt
    st["n_x"] += st.get("n_vx", 0) * lt
    if st.get("car"):
        st["scroll"] = st.get("speed", 0) * t
        bump = math.sin(t * 22) * (1.5 if st.get("speed", 0) < 200 else 4)
        st["r_x"], st["n_x"] = st["car_x"] + 30, st["car_x"] - 110
        st["r_y"] = st["n_y"] = st["gy"] + 110 + bump
        st.setdefault("n_look", (1, 0))
        st.setdefault("r_look", (1, 0) if st.get("speed", 0) < 200 else (0, 0))
    if seg["type"] == "line":
        idx = int((lt - LEAD) * FPS)
        level = seg["env"][idx] if 0 <= idx < len(seg["env"]) else 0.0
        st["r_talk" if seg["who"] == "R" else "n_talk"] = level
    overlays = []
    if seg.get("fx"):
        FX[seg["fx"]](st, lt, seg["dur"], overlays)

    cx, cy, z = camera(seg["shot"], st)
    z *= 1 + 0.035 * (lt / seg["dur"])
    img = Image.new("RGB", (W() * SS, H() * SS))
    pn = Pen(img, Cam(cx, cy, z))
    BACKGROUNDS[st["scene"]](pn, t, st)
    seated = bool(st.get("car"))
    draw_nina(pn, st["n_x"], st["n_y"], st, t, seated)
    draw_rico(pn, st["r_x"], st["r_y"], st, t, seated)
    if seated:
        draw_car_body(pn, st["car_x"], st["gy"] + (st["r_y"] - st["gy"] - 110), t, st.get("speed", 0))
    for o in overlays:
        o(pn)
    img = img.resize((W(), H()), Image.LANCZOS)
    if seg["type"] == "line":
        caption(img, seg["who"], seg["text"])
    return img


def render_episode(ep):
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Episode {ep['num']}: {ep['title']}")
    segs, total = build_timeline(ep)
    print(f"  length {total:.2f}s")
    wav_path = os.path.join(base.CACHE, f"rn_ep{ep['num']}.wav")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(mix_audio(segs, total).tobytes())
    slug = ep["title"].lower().replace(" ", "_")
    out = os.path.join(OUT_DIR, f"rico_and_nina_ep{ep['num']}_{slug}{'_short' if SHORTS else ''}.mp4")
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W()}x{H()}", "-r", str(FPS), "-i", "-", "-i", wav_path,
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
        lst = os.path.join(base.CACHE, "rn_concat.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{o}'\n" for o in outs)
        full = os.path.join(OUT_DIR, "rico_and_nina_all_episodes" + ("_short" if SHORTS else "") + ".mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", lst, "-c", "copy", full], check=True)
        print("All episodes ->", full)


if __name__ == "__main__":
    main()
