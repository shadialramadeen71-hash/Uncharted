#!/usr/bin/env python3
"""
POPEYE BUILDS A HOUSE — a <= 15 s vertical YouTube Short (1080x1920), in English.

The sailor and his wife, drawn with real human proportions on the skeleton/IK
rig from ../rico_and_nina (2-bone IK limbs, cel shading, moving camera,
word-by-word captions, Piper TTS voices).  Based on the 1929 comic-strip
designs (public domain in the US since 2025): sailor cap, corncob pipe,
squint, huge anchor-tattooed forearms; his wife tall and slim with a black
bun, red top, long black skirt and big boots.

Story (hook first): "Build me a house by sunset!" -> spinach -> a 3-second
super-speed build with a live progress bar -> payoff line.

Usage:
    python3 make_popeye.py            # render output/popeye_builds_a_house_short.mp4
    python3 make_popeye.py --preview  # a few still frames -> output/preview
"""
import math
import os
import random
import subprocess
import sys
import wave

from PIL import ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rico_and_nina"))
sys.path.insert(0, os.path.join(HERE, "..", "cartoon"))
import make_series as S  # noqa: E402  rig, camera, captions, audio mix
import make_episodes as base  # noqa: E402  Pen/Cam, TTS, sfx

S.set_format(True)                      # 1080x1920 Shorts
FPS, SR = base.FPS, base.SR
INK = base.INK
GROUND = S.GROUND
OUT_DIR = os.path.join(HERE, "output")
lerp, ease, lp = base.lerp, base.ease, S.lp

# --------------------------------------------------------------------------
# Cast
# --------------------------------------------------------------------------
POPEYE = dict(key="p", s=1.0, face=1, phase=0.3, skin=(238, 192, 152), hair=(46, 34, 26), iris=(70, 110, 160),
              top=(34, 36, 46), pattern=None, bottoms=(48, 86, 164), long=True, shoes=(44, 34, 28),
              female=False, style="popeye", sleeves="short", bulk=1.22, lean=0.0)
WIFE = dict(key="w", s=1.03, face=-1, phase=1.2, skin=(246, 208, 184), hair=(22, 20, 24), iris=(70, 46, 30),
            top=(212, 40, 48), pattern=None, bottoms=(26, 24, 30), long=True, shoes=(112, 66, 40),
            female=True, style="olive", sleeves="long", bulk=0.82, lean=0.0)
S.SPECS.update(p=POPEYE, w=WIFE)
S.DEFAULT_X.update(p=520, w=300)
S.NAMES.update(p="POPEYE", w="HIS WIFE")
S.NAME_COL.update(p=(120, 200, 255), w=(255, 120, 130))
base.VOICES["p"] = ("en/en_US/joe/medium/en_US-joe-medium", 0.80, 1.10, 0.95)      # gravelly sailor
base.VOICES["w"] = ("en/en_US/amy/medium/en_US-amy-medium", 1.12, 1.05, 0.92)      # bright, a bit nasal

HOUSE_X0, HOUSE_X1 = 700.0, 1100.0
WALL_TOP = 300.0
UI = {}                                  # screen overlays requested by the fx of the current frame


# --------------------------------------------------------------------------
# Props
# --------------------------------------------------------------------------
def hand_pos(J, i, s):
    sh, el, wr = J["arm%d" % i]
    dx, dy = wr[0] - el[0], wr[1] - el[1]
    L = math.hypot(dx, dy) or 1
    return (wr[0] + dx / L * 8 * s, wr[1] + dy / L * 8 * s), (dx / L, dy / L)


def draw_hammer(rig, hc, f, s, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    top = (hc[0] + (f * 12 * ca - 58 * sa) * s, hc[1] + (f * 12 * sa - 58 * ca) * s)
    rig.line([hc, top], (150, 98, 52), 7 * s)
    nx, ny = ca, sa
    rig.poly([(top[0] - nx * 22 * s - sa * 9 * s, top[1] - ny * 22 * s + ca * 9 * s),
              (top[0] + nx * 22 * s - sa * 9 * s, top[1] + ny * 22 * s + ca * 9 * s),
              (top[0] + nx * 22 * s + sa * 9 * s, top[1] + ny * 22 * s - ca * 9 * s),
              (top[0] - nx * 22 * s + sa * 9 * s, top[1] - ny * 22 * s - ca * 9 * s)], (120, 124, 134), 3)


def draw_plank(rig, hc, s):
    rig.poly([(hc[0] - 120 * s, hc[1] - 16 * s), (hc[0] + 120 * s, hc[1] - 26 * s),
              (hc[0] + 120 * s, hc[1] - 6 * s), (hc[0] - 120 * s, hc[1] + 4 * s)], (214, 170, 110), 3)


def draw_can(rig, hc, s, f):
    x, y = hc[0] + f * 4 * s, hc[1] - 26 * s
    rig.poly([(x - 17 * s, y - 26 * s), (x + 17 * s, y - 26 * s), (x + 17 * s, y + 24 * s), (x - 17 * s, y + 24 * s)],
             (60, 150, 60), 3)
    rig.poly([(x - 17 * s, y - 8 * s), (x + 17 * s, y - 8 * s), (x + 17 * s, y + 10 * s), (x - 17 * s, y + 10 * s)],
             (245, 240, 220), 0)
    rig.ell(x, y - 1 * s, 7 * s, 6 * s, (40, 130, 50), 0)
    rig.ell(x, y - 26 * s, 17 * s, 5 * s, (190, 196, 200), 2)


def anchor(rig, cx, cy, s, ang):
    ca, sa = math.cos(ang), math.sin(ang)

    def P(x, y):
        return (cx + (x * ca - y * sa) * s, cy + (x * sa + y * ca) * s)

    col = (40, 64, 130)
    rig.line([P(0, -9), P(0, 9)], col, 2.2 * s)
    rig.line([P(-5, -5), P(5, -5)], col, 2.2 * s)
    rig.line([P(-7, 4), P(-4, 9), P(0, 10), P(4, 9), P(7, 4)], col, 2.2 * s)


# --------------------------------------------------------------------------
# Character drawing (wraps the shared rig with each character's look)
# --------------------------------------------------------------------------
def draw_wife(pn, spec, x, y, st, t):
    J = S.pose(spec, x, y, st, t)
    rig = S.make_rig(pn, spec, x, y, st)
    s, f, P = J["s"], J["f"], J["P"]
    # stockings + big boots, then the long skirt, then the rest of the body
    knees = []
    for i in (0, 1):
        hip, knee, ankle = J["leg%d" % i]
        knees.append(knee)
        rig.chain([lp(knee, ankle, 0.35), ankle], [8 * s, 7 * s], (40, 36, 44))
        rig.blob([(ankle[0] + f * 8 * s, ankle[1] + 7 * s, 22 * s, 12 * s),
                  (ankle[0] + f * 26 * s, ankle[1] + 10 * s, 14 * s, 9 * s),
                  (ankle[0], ankle[1] - 6 * s, 11 * s, 13 * s)], spec["shoes"], 3)
    hem_y = max(lp(J["leg0"][1], J["leg0"][2], 0.55)[1], lp(J["leg1"][1], J["leg1"][2], 0.55)[1])
    kx = [k[0] for k in knees]
    rig.poly([(P[0] - 34 * s, P[1] - 40 * s), (P[0] + 34 * s, P[1] - 40 * s),
              (max(kx) + 40 * s, hem_y), (min(kx) - 40 * s, hem_y)], spec["bottoms"], 3)
    rig.line([(min(kx) - 30 * s, hem_y - 14 * s), (max(kx) + 30 * s, hem_y - 14 * s)], (54, 50, 60), 2)
    S.draw_human(pn, spec, x, y, st, t, seated=True)
    H = J["H"]
    rig.blob([(H[0] - f * 34 * s, H[1] - 14 * s, 17 * s, 17 * s)], spec["hair"], 3)        # bun
    rig.blob([(H[0] - 2 * s, H[1] - 33 * s, 31 * s, 10 * s)], spec["hair"], 0)
    return J


def draw_popeye(pn, spec, x, y, st, t):
    S.draw_human(pn, spec, x, y, st, t)
    J = S.pose(spec, x, y, st, t)
    rig = S.make_rig(pn, spec, x, y, st)
    s, f, C, H = J["s"], J["f"], J["C"], J["H"]
    power = st.get("p_power", 0.0)
    # red collar
    for sx in (-1, 1):
        rig.poly([(C[0] + sx * 6 * s, C[1] - 2 * s), (C[0] + sx * 40 * s, C[1] - 2 * s), (C[0] + sx * 10 * s, C[1] + 30 * s)],
                 (206, 44, 44), 2.5)
    # sailor cap with rolled brim
    rig.blob([(H[0] - f * 2 * s, H[1] - 40 * s, 30 * s, 15 * s)], (250, 250, 248), 3)
    rig.ell(H[0], H[1] - 27 * s, 37 * s, 8 * s, (250, 250, 248), 3)
    rig.line([(H[0] - 33 * s, H[1] - 30 * s), (H[0] + 33 * s, H[1] - 30 * s)], (210, 214, 222), 2)
    # corncob pipe from the mouth corner
    m0 = (H[0] + f * 15 * s, H[1] + 26 * s)
    m1 = (H[0] + f * 46 * s, H[1] + 31 * s)
    rig.line([m0, m1], (96, 64, 34), 3.2 * s)
    rig.poly([(m1[0] - 5 * s, m1[1] + 3 * s), (m1[0] + 5 * s, m1[1] + 3 * s), (m1[0] + 6 * s, m1[1] - 13 * s),
              (m1[0] - 6 * s, m1[1] - 13 * s)], (206, 160, 78), 2)
    for k in range(3):
        rig.line([(m1[0] - 5 * s, m1[1] - (1 + 4 * k) * s), (m1[0] + 5 * s, m1[1] - (1 + 4 * k) * s)], (160, 118, 52), 1)
    rig.ell(m1[0], m1[1] - 13 * s, 6 * s, 2.4 * s, (60, 40, 22), 1.2)
    if st.get("p_smoke"):
        for k in range(3):
            ph = (t * 1.3 + k / 3) % 1
            px, py = rig.T((m1[0] + math.sin(ph * 6 + k) * 8 * s, m1[1] - (20 + ph * 70) * s))
            r = (5 + ph * 10) * s
            pn.ellipse(px, py, r, r, (235, 235, 240), 0)
    # the forearms: huge, with anchor tattoos
    fat = 1.0 + 0.35 * power
    for i in (0, 1):
        sh, el, wr = J["arm%d" % i]
        mid = lp(el, wr, 0.5)
        rig.chain([lp(el, wr, 0.05), mid, wr], [12 * s, 20 * s * fat, 11 * s], spec["skin"])
        ang = math.atan2(wr[1] - el[1], wr[0] - el[0]) - math.pi / 2
        anchor(rig, mid[0], mid[1], 1.25 * s * fat, ang)
        hc, (dx, dy) = hand_pos(J, i, s)
        sx = (-1, 1)[i]
        rig.ell(hc[0], hc[1], 10 * s, 11.5 * s, spec["skin"], 3)
        rig.ell(hc[0] - dy * 8 * s * sx, hc[1] + dx * 8 * s * sx, 4 * s, 5.5 * s, spec["skin"], 2)
        front = (sx == f)
        hold = st.get("p_hold")
        if front and hold == "hammer":
            draw_hammer(rig, hc, f, s, f * (0.4 + 0.9 * abs(math.sin(t * 22))))
        elif front and hold == "can":
            draw_can(rig, hc, s, f)
        elif hold == "plank" and front:
            draw_plank(rig, hc, s)
        if power > 0.05:
            px, py = rig.T(mid)
            base.sparkles(pn, px, py, t + i, 4, 46 * s)
    return J


def draw_cast(pn, st, t, seated=False):
    for k in st["cast"]:
        spec = S.SPECS[k]
        if k == "p":
            draw_popeye(pn, spec, st["p_x"], st["p_y"], st, t)
        elif k == "w":
            draw_wife(pn, spec, st["w_x"], st["w_y"], st, t)
        else:
            S.draw_human(pn, spec, st[k + "_x"], st[k + "_y"], st, t)


S.draw_cast = draw_cast


# --------------------------------------------------------------------------
# The building site
# --------------------------------------------------------------------------
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def draw_house(pn, b, t):
    x0, x1, gy = HOUSE_X0, HOUSE_X1, GROUND
    pn.rect(x0 - 16, gy - 10, x1 + 16, gy + 14, (176, 176, 182), 4)                 # foundation
    sp = clamp(b / 0.22)                                                          # frame studs
    n = int(sp * 9 + 0.999) if sp > 0 else 0
    for i in range(n):
        sx = x0 + 6 + i * (x1 - x0 - 12) / 8
        pn.rect(sx - 7, gy - 10 - (gy - 10 - WALL_TOP) * clamp(sp * 9 - i), sx + 7, gy - 10, (196, 150, 96), 3)
    if sp >= 1:
        pn.rect(x0, WALL_TOP - 8, x1, WALL_TOP + 8, (196, 150, 96), 3)
    wp = clamp((b - 0.2) / 0.2)                                                   # siding
    wood, paint = (220, 182, 126), (150, 202, 236)
    if wp > 0:
        top = gy - 10 - (gy - 10 - WALL_TOP) * wp
        pn.rect(x0, top, x1, gy - 10, wood, 4)
        pp = clamp((b - 0.78) / 0.14)
        if pp > 0:
            pn.rect(x0, top, x0 + (x1 - x0) * pp, gy - 10, paint, 0)
            pn.line([(x0 + (x1 - x0) * pp, top), (x0 + (x1 - x0) * pp, gy - 10)], (120, 180, 220), 6, caps=False)
        yy = gy - 40
        while yy > top + 6:
            pn.line([(x0 + 4, yy), (x1 - 4, yy)], (190, 150, 100) if pp < 1 else (120, 176, 214), 2, caps=False)
            yy -= 34
        pn.line([(x0, top), (x0, gy - 10), (x1, gy - 10), (x1, top), (x0, top)], INK, 4, caps=False)
    rp = clamp((b - 0.4) / 0.2)                                                   # roof
    if rp > 0:
        peak = WALL_TOP - 230 * ease(rp)
        pn.poly([(x0 - 50, WALL_TOP + 4), (x1 + 50, WALL_TOP + 4), ((x0 + x1) / 2, peak)], (176, 58, 50), 4)
        for r in range(1, 5):
            k = r / 5
            yy = lerp(WALL_TOP, peak, k)
            half = lerp((x1 - x0) / 2 + 50, 0, k)
            if rp > k:
                pn.line([((x0 + x1) / 2 - half + 6, yy), ((x0 + x1) / 2 + half - 6, yy)], (140, 40, 36), 3, caps=False)
    op = clamp((b - 0.6) / 0.15)                                                  # windows, door, chimney
    if op > 0:
        sc = ease(op)
        for wx in (x0 + 80, x1 - 80):
            w2, h2 = 45 * sc, 45 * sc
            pn.rect(wx - w2, 420 - h2, wx + w2, 420 + h2, (190, 228, 250), 4)
            pn.line([(wx, 420 - h2), (wx, 420 + h2)], INK, 3, caps=False)
            pn.line([(wx - w2, 420), (wx + w2, 420)], INK, 3, caps=False)
            if b > 0.92:
                pn.rect(wx - 52, 470, wx + 52, 490, (150, 96, 60), 3)
                for k in range(5):
                    pn.ellipse(wx - 40 + k * 20, 466, 9, 9, [(250, 90, 120), (255, 220, 80), (250, 140, 200)][k % 3], 2)
        dh = 140 * sc
        cx = (x0 + x1) / 2
        pn.rect(cx - 38, GROUND - 10 - dh, cx + 38, GROUND - 10, (200, 60, 56), 4)
        pn.ellipse(cx + 24, GROUND - 10 - dh * 0.45, 5, 5, (250, 210, 70), 2)
        pn.rect(x1 - 110, WALL_TOP - 40 - 110 * sc, x1 - 70, WALL_TOP - 40, (150, 90, 70), 4)
    if b >= 1.0:
        for k in range(3):
            ph = (t * 0.8 + k / 3) % 1
            r = 14 + ph * 26
            pn.ellipse(x1 - 90 + math.sin(ph * 5 + k) * 12, WALL_TOP - 160 - ph * 160, r, r, (240, 240, 244), 0)


def bg_site(layer, t, st):
    b = st.get("build", 0.0)
    pn = layer(0.1)
    sky = [(118, 196, 248), (146, 210, 250), (176, 222, 250), (210, 230, 240)]
    for i, c in enumerate(sky):
        pn.rect(-3000, -1600 + i * 500, 5000, -1100 + i * 500 + 600, c, 0)
    sun_y = 40 + 120 * b
    pn.ellipse(1100, sun_y, 70, 70, (255, 214, 90), 0)
    pn.ellipse(1100, sun_y, 54, 54, (255, 236, 150), 0)
    for i, (cx, cy) in enumerate(((150, 60), (560, 20), (900, 110), (-250, 90), (1500, 40))):
        cx += (t * 14) % 240
        pn.blob([(cx, cy, 64, 26), (cx + 52, cy - 14, 44, 26), (cx - 52, cy + 4, 40, 20)], (255, 255, 255), 3)
    pn = layer(0.45)
    for i in range(-6, 10):
        pn.ellipse(i * 330, 600, 300, 160, (126, 190, 110) if i % 2 else (110, 176, 100), 3)
    pn = layer(0.75)
    for i in range(-6, 12):
        tx = i * 260 + 40
        pn.rect(tx - 9, 470, tx + 9, 610, (120, 80, 50), 3)
        pn.blob([(tx, 430, 50, 50), (tx - 36, 470, 38, 34), (tx + 36, 470, 38, 34)], (70, 150, 80), 3)
    pn = layer(1.0)
    pn.rect(-3000, GROUND - 6, 5000, 2600, (122, 186, 92), 0)
    pn.line([(-3000, GROUND - 6), (5000, GROUND - 6)], INK, 4, caps=False)
    pn.rect(HOUSE_X0 - 140, GROUND - 2, HOUSE_X1 + 140, GROUND + 60, (170, 130, 86), 0)
    rnd = random.Random(4)
    for _ in range(140):
        gx, gy = rnd.uniform(-1200, 2600), rnd.uniform(GROUND + 10, GROUND + 900)
        pn.line([(gx, gy), (gx + 4, gy - 14)], (96, 160, 74), 3)
    # lumber pile (shrinks as the house grows) + sawhorse
    rows = max(0, int(round(5 * (1 - clamp(b / 0.6)))))
    for r in range(rows):
        pn.rect(560 - r * 2, GROUND - 14 - r * 16, 690 - r * 2, GROUND - r * 16, (214, 170, 110), 3)
    draw_house(pn, b, t)
    if b >= 1.0:                                                      # finished: little fence + sparkle
        for i in range(8):
            fx = HOUSE_X1 + 30 + i * 26
            pn.poly([(fx - 9, GROUND), (fx + 9, GROUND), (fx + 9, GROUND - 60), (fx, GROUND - 72), (fx - 9, GROUND - 60)],
                    (252, 252, 250), 3)
        pn.rect(HOUSE_X1 + 20, GROUND - 46, HOUSE_X1 + 230, GROUND - 36, (252, 252, 250), 3)
        if st.get("sparkle"):
            base.sparkles(pn, (HOUSE_X0 + HOUSE_X1) / 2, 200, t, 7, 260)


S.BACKGROUNDS["site"] = bg_site


# --------------------------------------------------------------------------
# Gags
# --------------------------------------------------------------------------
def fx_spinach(st, lt, dur, ov):
    t_pop = 0.95
    J = S.pose(POPEYE, st["p_x"], st["p_y"], st, lt)
    if lt < t_pop:
        st.update(p_hold="can", p_arms="hold")
        return
    k = lt - t_pop
    st.update(p_hold=None, p_arms="up", p_power=ease(k / 0.35), p_bounce=k < 0.6, p_mood="")
    mouth = (J["H"][0] + 18, J["H"][1] + 26)
    if k < 0.45:
        for i in range(7):
            a = i * 0.9
            fx_, fy_ = lerp(st["p_x"] + 80, mouth[0], k / 0.45) + math.cos(a) * 26 * (1 - k / 0.45), \
                lerp(GROUND - 300, mouth[1], k / 0.45) + math.sin(a) * 20 * (1 - k / 0.45)
            ov.append(lambda pn, x=fx_, y=fy_, a=a: pn.blob([(x, y, 13, 8), (x + 8, y - 5, 9, 6)], (40, 140, 50), 2))
    if k < 0.5:
        ov.append(lambda pn: base.poof(pn, st["p_x"] + 60, GROUND - 330, k / 0.5, (150, 230, 120), 0.8))


def fx_build(st, lt, dur, ov):
    prog = clamp(lt / (dur - 0.35))
    st["build"] = prog
    UI["build"] = prog
    cyc = lt * 2.4
    phase = cyc % 1
    xa, xb = 600, 960
    px = lerp(xa, xb, 0.5 - 0.5 * math.cos(2 * math.pi * phase))
    vel = math.sin(2 * math.pi * phase)
    st.update(p_x=px, p_legs="run" if abs(vel) > 0.25 else "stand", p_face=1 if vel >= 0 else -1, p_power=1.0)
    at_house = px > 880
    st["p_hold"] = "hammer" if at_house else "plank"
    st["p_arms"] = "up" if at_house else "hold"
    st.update(w_shock=True, w_arms="up" if prog > 0.5 else "rest", w_look=(1, -0.3))
    if prog >= 1:
        st.update(p_legs="stand", p_face=-1, p_hold="hammer", p_arms="rest", sparkle=True)
    # dust at his feet + BANG bursts at the wall
    if abs(vel) > 0.25:
        ov.append(lambda pn: base.poof(pn, px - st["p_face"] * 90, GROUND - 20, (lt * 3) % 1, (226, 206, 170), 0.45))
    if at_house and prog < 1:
        word = ["BANG!", "WHAM!", "BAM!"][int(lt * 4) % 3]
        k = (lt * 4) % 1

        def burst(pn, word=word, k=k):
            cx, cy = HOUSE_X0 + 160 + 60 * math.sin(lt * 7), 360 + 40 * math.cos(lt * 5)
            pn.star(cx, cy, 90 * (0.7 + 0.5 * k), (255, 230, 70), 4, rot=lt * 3, points=9)
            S.wtext(pn, cx, cy, word, 44, (230, 40, 40), 4, (255, 255, 255))
        ov.append(burst)


S.FX.update(spinach=fx_spinach, build=fx_build)


def sound(name, dur=1.0):
    import numpy as np
    t = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(3)
    if name == "hammer":
        tt = t[: int(0.12 * SR)]
        return (np.sin(2 * np.pi * 900 * tt) * 0.5 + rng.standard_normal(len(tt)) * 0.5) * np.exp(-tt * 45) * 0.8
    if name == "saw":
        tt = t[: int(0.35 * SR)]
        n = rng.standard_normal(len(tt)) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 14 * tt)))
        return np.convolve(n, np.ones(6) / 6, mode="same") * 0.35 * np.sin(np.pi * tt / tt[-1])
    if name == "powerup":
        tt = t[: int(0.7 * SR)]
        f = 300 + 900 * tt / tt[-1]
        ph = np.cumsum(f) / SR
        return np.sign(np.sin(2 * np.pi * ph)) * 0.18 * np.exp(-tt * 1.5)
    if name == "pop":
        tt = t[: int(0.1 * SR)]
        return np.sin(2 * np.pi * (500 - 3000 * tt) * tt) * np.exp(-tt * 40) * 0.6
    if name == "toot":
        out = []
        for f, d in ((880, 0.12), (0, 0.06), (880, 0.22)):
            tt = np.arange(int(d * SR)) / SR
            out.append(np.sin(2 * np.pi * f * tt) * 0.3 * np.minimum(1, tt * 60) * np.minimum(1, (d - tt) * 60)
                       + rng.standard_normal(len(tt)) * 0.03 * (f > 0))
        return np.concatenate(out)
    return S.sfx(name, dur)


S.sound = sound


# --------------------------------------------------------------------------
# Screen overlays
# --------------------------------------------------------------------------
def badge(img, ep, t):
    d = ImageDraw.Draw(img)
    if t < 2.6:                                          # hook title
        k = ease(min(1, t / 0.25)) * (1 - ease(max(0, (t - 2.3) / 0.3)))
        y = -140 + 330 * k
        d.rounded_rectangle([90, y - 70, 990, y + 70], radius=36, fill=(206, 40, 46), outline=INK, width=6)
        d.text((540, y), "A HOUSE IN 3 SECONDS?!", font=base.font(62), fill=(255, 240, 120), anchor="mm",
               stroke_width=4, stroke_fill=INK)
    b = UI.pop("build", None)
    if b is not None:                                    # live progress bar during the build
        y = 300
        d.rounded_rectangle([110, y - 52, 970, y + 52], radius=52, fill=(30, 30, 40), outline=INK, width=6)
        d.rounded_rectangle([122, y - 40, 122 + max(80, 836 * b), y + 40], radius=40,
                            fill=(90, 210, 90) if b < 1 else (255, 214, 60))
        d.text((540, y), f"BUILDING... {int(b * 100)}%" if b < 1 else "DONE! 100%", font=base.font(54),
               fill=(255, 255, 255), anchor="mm", stroke_width=4, stroke_fill=INK)


def follow_card(img, ep, lt):
    d = ImageDraw.Draw(img)
    k = ease(min(1, lt / 0.25))
    s = k * (1 + 0.06 * math.sin(lt * 16))
    cy, bw, bh = 1250, 600 * s, 130 * s
    d.rounded_rectangle([540 - bw / 2, cy - bh / 2, 540 + bw / 2, cy + bh / 2], radius=max(1, bh / 2),
                        fill=(230, 30, 50), outline=INK, width=5)
    if s > 0.2:
        d.text((540, cy), "SUBSCRIBE for more!", font=base.font(int(52 * s)), fill=(255, 255, 255), anchor="mm",
               stroke_width=3, stroke_fill=INK)


S.badge = badge
S.follow_card = follow_card

# --------------------------------------------------------------------------
# The episode
# --------------------------------------------------------------------------
SITE = dict(scene="site", cast=["w", "p"], p_x=590, w_x=410, pair=("w", "p"), wide_keys=["w", "p"],
            cam_c=(775, 360), cam_zk=0.57, p_wink=True, p_smoke=True, w_face=1, p_face=-1, build=0.0)
DONE = dict(SITE, build=1.0, sparkle=True, p_power=1.0, p_hold="hammer", p_x=600)

EPISODE = dict(num=1, title="Popeye Builds a House", beats=[
    S.L("w", "Popeye! Build me a house by sunset!", ["fixed", "ms_w"],
        dict(SITE, w_arms="point", w_brow=1, w_mood="angry", p_brow=1), flash=[0.0]),
    S.L("p", "Spinach time!", ["ms_p", "cu_p"], dict(SITE, p_face=1, p_smoke=False), fx="spinach",
        sfx=[(0.95, "pop"), (1.0, "powerup")], shake=[(1.0, 12)], flash=[1.0]),
    S.A(3.4, "fixed", dict(SITE, w_face=1, p_smoke=False, cam_zk=0.59), fx="build", whip=1,
        sfx=[(0, "whoosh")] + [(0.25 + i * 0.25, "hammer") for i in range(11)] + [(0.5, "saw"), (1.6, "saw"),
                                                                                    (3.05, "ding")],
        shake=[(0.3 + i * 0.5, 6) for i in range(6)] + [(3.05, 14)], flash=[3.05]),
    S.L("w", "A whole house in three seconds?!", ["fixed", "ms2"],
        dict(DONE, w_shock=True, w_arms="up", w_face=1, p_face=-1, w_look=(1, -0.4)), punch=1.2),
    S.L("p", "Built with love... and spinach!", ["ms_p", "cu_p"],
        dict(DONE, p_face=-1, p_arms="up", w_face=1, w_arms="hips", p_smoke=True), punch=1.3,
        sfx=[(1.6, "toot")]),
])


def render(preview=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    segs, total = S.build_timeline(EPISODE)
    print(f"length {total:.2f}s")
    if preview:
        pdir = os.path.join(OUT_DIR, "preview")
        os.makedirs(pdir, exist_ok=True)
        for s in segs:
            for frac in (0.3, 0.85):
                fi = int((s["start"] + s["dur"] * frac) * FPS)
                S.render_frame(EPISODE, segs, fi).save(os.path.join(pdir, f"f_{fi:04d}.png"))
        print("previews ->", pdir)
        return
    wav_path = os.path.join(base.CACHE, "popeye_house.wav")
    os.makedirs(base.CACHE, exist_ok=True)
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(S.mix_audio(segs, total).tobytes())
    out = os.path.join(OUT_DIR, "popeye_builds_a_house_short.mp4")
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{base.W}x{base.H}",
         "-r", str(FPS), "-i", "-", "-i", wav_path, "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    for fi in range(int(total * FPS)):
        proc.stdin.write(S.render_frame(EPISODE, segs, fi).tobytes())
    proc.stdin.close()
    proc.wait()
    print("->", out)


if __name__ == "__main__":
    render("--preview" in sys.argv)
