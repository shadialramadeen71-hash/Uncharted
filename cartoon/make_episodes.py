#!/usr/bin/env python3
"""
GORBO & PIP — a tiny cartoon series generated entirely from code.

* Gorbo: a very tall, green-skinned wizard.
* Pip:   his monkey sidekick.

Style: flat colours, thick black outlines, big round "touching" eyes,
static camera with hard cuts between a wide two-shot and close-ups,
snappy mouth flaps, and a cutaway gag — the classic adult-sitcom
animation look.

Every episode is <= 15 seconds. Voices are English, generated with the
Piper neural TTS engine (downloaded automatically on first run) and then
pitch-shifted per character with ffmpeg.

Usage:
    pip install piper-tts pillow numpy
    python3 make_episodes.py            # renders all episodes to ./output
    python3 make_episodes.py 2          # renders only episode 2
    python3 make_episodes.py --shorts   # vertical 1080x1920 YouTube Shorts versions
"""
import hashlib
import math
import os
import random
import subprocess
import sys
import urllib.request
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output")
CACHE = os.path.expanduser("~/.cache/gorbo_pip")
VOICE_DIR = os.path.join(CACHE, "voices")

W, H = 1280, 720          # output resolution
SS = 2                    # supersampling factor (smooth outlines)
FPS = 24
SR = 22050                # audio sample rate
MAX_LEN = 15.0            # seconds per episode (hard limit)
TITLE_DUR = 1.5

INK = (22, 18, 24)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# --------------------------------------------------------------------------
# Voices
# --------------------------------------------------------------------------
HF = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
VOICES = {
    # who: (model path on HF, pitch factor, tempo factor, length scale)
    "W": ("en/en_GB/alan/medium/en_GB-alan-medium", 0.86, 1.08, 1.05),   # deep, theatrical
    "M": ("en/en_US/joe/medium/en_US-joe-medium", 1.42, 0.80, 0.95),     # squeaky monkey
}


def ensure_voice(path):
    os.makedirs(VOICE_DIR, exist_ok=True)
    name = os.path.basename(path)
    local = os.path.join(VOICE_DIR, name + ".onnx")
    for ext in (".onnx", ".onnx.json"):
        dst = os.path.join(VOICE_DIR, name + ext)
        if not os.path.exists(dst):
            print("  downloading voice", name + ext)
            urllib.request.urlretrieve(HF + path + ext, dst)
    return local


def read_wav(path):
    with wave.open(path) as wf:
        data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
    return data.astype(np.float32) / 32768.0


def tts(who, text):
    """English speech for a character, cached on disk. Returns float32 mono @ SR."""
    model, pitch, tempo, length = VOICES[who]
    key = hashlib.md5(f"{who}|{text}|{VOICES[who]}".encode()).hexdigest()[:16]
    os.makedirs(os.path.join(CACHE, "lines"), exist_ok=True)
    raw = os.path.join(CACHE, "lines", key + "_raw.wav")
    fin = os.path.join(CACHE, "lines", key + ".wav")
    if not os.path.exists(fin):
        onnx = ensure_voice(model)
        subprocess.run([sys.executable, "-m", "piper", "-m", onnx, "-f", raw,
                        "--length-scale", str(length)],
                       input=text.encode(), check=True, capture_output=True)
        af = (f"asetrate={SR}*{pitch},aresample={SR},atempo={tempo},"
              "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
              "silenceremove=start_periods=1:start_threshold=-45dB,areverse")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", af,
                        "-ac", "1", "-ar", str(SR), fin], check=True)
    return read_wav(fin)


def mouth_envelope(clip):
    """Per-video-frame mouth openness (0, .55 or 1) — snappy cartoon flaps."""
    hop = SR // FPS
    n = int(math.ceil(len(clip) / hop))
    rms = np.array([np.sqrt(np.mean(clip[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    ref = np.percentile(rms, 90) + 1e-6
    lv = rms / ref
    return np.where(lv < 0.25, 0.0, np.where(lv < 0.7, 0.55, 1.0))


# --------------------------------------------------------------------------
# Sound effects (synthesised)
# --------------------------------------------------------------------------
def _t(d):
    return np.arange(int(d * SR)) / SR


def sfx(name):
    rng = np.random.default_rng(len(name))
    if name == "poof":
        t = _t(0.55)
        n = rng.standard_normal(len(t))
        n = np.convolve(n, np.ones(18) / 18, mode="same")
        return n * np.exp(-t * 7) * 1.6
    if name == "chime":
        out = np.zeros(int(0.9 * SR))
        for i, f in enumerate([1318, 1568, 1976, 2637]):
            s = int(i * 0.08 * SR)
            t = _t(0.9 - i * 0.08)
            out[s:s + len(t)] += np.sin(2 * np.pi * f * t) * np.exp(-t * 5) * 0.22
        return out
    if name == "zap":
        t = _t(0.55)
        f = 140 + 90 * np.sin(2 * np.pi * 23 * t) + rng.uniform(-30, 30, len(t))
        ph = np.cumsum(f) / SR
        saw = 2 * (ph % 1) - 1
        return saw * 0.35 * (0.6 + 0.4 * (rng.random(len(t)) > 0.5)) * np.exp(-t * 2)
    if name == "boom":
        t = _t(1.0)
        n = np.convolve(rng.standard_normal(len(t)), np.ones(40) / 40, mode="same") * 3
        return (n + np.sin(2 * np.pi * (60 - 25 * t) * t) * 0.8) * np.exp(-t * 4) * 0.9
    if name == "bonk":
        t = _t(0.3)
        return np.sin(2 * np.pi * (700 * np.exp(-t * 9) + 140) * t) * np.exp(-t * 12) * 0.8
    if name == "whoosh":
        t = _t(0.45)
        n = rng.standard_normal(len(t))
        k = np.convolve(n, np.ones(10) / 10, mode="same")
        return k * np.sin(np.pi * t / t[-1]) ** 2 * 1.1
    if name == "jingle":
        notes = [(523, .12), (659, .12), (784, .12), (1047, .3), (988, .1), (1047, .45)]
        out = []
        for f, d in notes:
            t = _t(d)
            sq = np.sign(np.sin(2 * np.pi * f * t)) * 0.12 + np.sin(2 * np.pi * f / 2 * t) * 0.15
            out.append(sq * np.minimum(1, t * 60) * np.exp(-t * 3))
        return np.concatenate(out)
    raise KeyError(name)


# --------------------------------------------------------------------------
# Drawing primitives
# --------------------------------------------------------------------------
class Cam:
    def __init__(self, cx, cy, z):
        self.cx, self.cy, self.z = cx, cy, z

    def p(self, x, y):
        return ((x - self.cx) * self.z + W / 2) * SS, ((y - self.cy) * self.z + H / 2) * SS

    def s(self, v):
        return v * self.z * SS


class Pen:
    def __init__(self, img, cam):
        self.d = ImageDraw.Draw(img)
        self.c = cam

    def _box(self, cx, cy, rx, ry):
        x0, y0 = self.c.p(cx - rx, cy - ry)
        x1, y1 = self.c.p(cx + rx, cy + ry)
        return [x0, y0, max(x0 + 1, x1), max(y0 + 1, y1)]

    def ellipse(self, cx, cy, rx, ry, fill, ow=4):
        if ow:
            self.d.ellipse(self._box(cx, cy, rx + ow, ry + ow), fill=INK)
        self.d.ellipse(self._box(cx, cy, rx, ry), fill=fill)

    def blob(self, parts, fill, ow=4):
        """Several ellipses merged into one outlined silhouette."""
        if ow:
            for cx, cy, rx, ry in parts:
                self.d.ellipse(self._box(cx, cy, rx + ow, ry + ow), fill=INK)
        for cx, cy, rx, ry in parts:
            self.d.ellipse(self._box(cx, cy, rx, ry), fill=fill)

    def line(self, pts, fill=INK, w=4, caps=True):
        P = [self.c.p(*q) for q in pts]
        ww = max(1, int(self.c.s(w)))
        self.d.line(P, fill=fill, width=ww, joint="curve")
        if caps:
            r = ww / 2
            for x, y in (P[0], P[-1]):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def stroke(self, pts, color, w, ow=4):
        """Thick coloured line with ink outline (tails, wands...)."""
        self.line(pts, INK, w + 2 * ow)
        self.line(pts, color, w)

    def limb(self, a, b, w, fill, ow=4):
        self.stroke([a, b], fill, w, ow)

    def poly(self, pts, fill, ow=4):
        P = [self.c.p(*q) for q in pts]
        self.d.polygon(P, fill=fill)
        if ow:
            ww = max(1, int(self.c.s(ow)))
            self.d.line(P + [P[0], P[1]], fill=INK, width=ww, joint="curve")

    def rect(self, x0, y0, x1, y1, fill, ow=4, r=0):
        a = self.c.p(x0, y0)
        b = self.c.p(x1, y1)
        rr = self.c.s(r)
        if ow:
            o = self.c.s(ow)
            self.d.rounded_rectangle([a[0] - o, a[1] - o, b[0] + o, b[1] + o], radius=rr + o, fill=INK)
        self.d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=rr, fill=fill)

    def star(self, cx, cy, r, fill, ow=3, rot=0.0, points=5):
        pts = []
        for i in range(points * 2):
            a = rot - math.pi / 2 + i * math.pi / points
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        self.poly(pts, fill, ow)


def lerp(a, b, k):
    return a + (b - a) * k


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


# --------------------------------------------------------------------------
# Props & effects
# --------------------------------------------------------------------------
YELLOW = (252, 214, 64)


def banana(pn, cx, cy, L, ang=0.0):
    outer, inner = [], []
    ca, sa = math.cos(ang), math.sin(ang)
    for i in range(25):
        s = -1 + 2 * i / 24
        x, y = s * L / 2, L * 0.2 * s * s
        th = L * 0.12 * (1 - s * s) ** 0.6 + 2
        outer.append((x, y + th))
        inner.append((x, y - th))
    pts = outer + inner[::-1]
    pts = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]
    pn.poly(pts, (250, 222, 70), 4)
    for e in (pts[0], pts[24]):
        pn.ellipse(e[0], e[1], 5, 5, (110, 80, 30), 2)


def toast(pn, cx, cy, s=1.0):
    pn.rect(cx - 26 * s, cy - 24 * s, cx + 26 * s, cy + 22 * s, (196, 128, 58), 4, 12 * s)
    pn.rect(cx - 19 * s, cy - 17 * s, cx + 19 * s, cy + 15 * s, (242, 205, 140), 0, 8 * s)


def poof(pn, cx, cy, k, color=(250, 250, 250), size=1.0):
    """Cartoon smoke cloud. k: 0 -> 1 progress."""
    if k <= 0 or k >= 1:
        return
    grow = ease(min(1, k * 2.2))
    shrink = 1 - ease((k - 0.55) / 0.45) if k > 0.55 else 1
    R = 95 * size * grow
    parts = []
    for i in range(9):
        a = i * 2 * math.pi / 9 + k * 0.8
        r = 45 * size * shrink * (0.8 + 0.25 * math.sin(i * 2.3))
        parts.append((cx + math.cos(a) * R * 0.75, cy + math.sin(a) * R * 0.6, r, r * 0.9))
    parts.append((cx, cy, R * 0.8 * shrink + 1, R * 0.65 * shrink + 1))
    pn.blob(parts, color, 4)


def sparkles(pn, cx, cy, t, n=6, spread=45):
    for i in range(n):
        a = t * 3 + i * 2 * math.pi / n
        r = spread * (0.6 + 0.4 * math.sin(t * 7 + i))
        pn.star(cx + math.cos(a) * r, cy + math.sin(a) * r, 9 + 4 * math.sin(t * 11 + i),
                YELLOW, 2, rot=t * 4, points=4)


def lightning(pn, a, b, seed):
    rnd = random.Random(seed)
    pts = [a]
    for i in range(1, 8):
        k = i / 8
        pts.append((lerp(a[0], b[0], k) + rnd.uniform(-22, 22), lerp(a[1], b[1], k) + rnd.uniform(-22, 22)))
    pts.append(b)
    pn.line(pts, INK, 16)
    pn.line(pts, (255, 245, 120), 8)
    pn.line(pts, (255, 255, 255), 3)


def smoke(pn, x, y, t, n=3):
    for i in range(n):
        k = ((t * 0.8 + i / n) % 1)
        pn.ellipse(x + math.sin(k * 6 + i) * 10, y - k * 70, 10 + k * 14, 9 + k * 12, (110, 110, 115), 3)


# --------------------------------------------------------------------------
# Characters
# --------------------------------------------------------------------------
SKIN_W = (128, 198, 92)
ROBE = (104, 60, 164)
SOOT = (74, 74, 78)
EYE = (252, 252, 250)

WIZ_POSES = {  # hand offset from feet, wand direction
    "rest": ((92, -185), (0.70, 0.72)),
    "up": ((130, -440), (0.30, -0.95)),
    "point": ((150, -330), (1.0, -0.18)),
}


def eyes(pn, pts, rx, ry, look, blink, skin, brows=0.0, shock=False, dizzy=False, t=0, ow=4):
    for (ex, ey) in pts:
        pn.ellipse(ex, ey, rx, ry, EYE, ow)
    for i, (ex, ey) in enumerate(pts):
        if blink:
            pn.ellipse(ex, ey, rx, ry, skin, ow)
            pn.line([(ex - rx * 0.8, ey + 2), (ex + rx * 0.8, ey + 2)], INK, 3)
            continue
        if dizzy:
            a = t * 12 + i * math.pi
            px, py = ex + math.cos(a) * rx * 0.45, ey + math.sin(a) * ry * 0.45
        else:
            px, py = ex + look[0] * rx * 0.42, ey + look[1] * ry * 0.3
        r = 2.5 if shock else 4.2
        pn.ellipse(px, py, r, r, INK, 0)
    if brows:
        for (ex, ey), sgn in zip(pts, (-1, 1)):
            lift = ry + 10 + brows * 8
            pn.line([(ex - rx * 0.7, ey - lift + sgn * 3 * brows), (ex + rx * 0.7, ey - lift - sgn * 3 * brows)], INK, 5)


def mouth(pn, x, y, m, w=17, smile=True):
    if m < 0.15:
        if smile:
            pn.line([(x - w, y - 3), (x - w * 0.4, y + 3), (x + w * 0.4, y + 3), (x + w, y - 3)], INK, 4)
        else:
            pn.line([(x - w * 0.8, y + 1), (x + w * 0.8, y)], INK, 4)
    else:
        h = 4 + 13 * m
        pn.ellipse(x, y + h * 0.4, w, h, (96, 22, 34), 4)
        pn.ellipse(x + 2, y + h * 0.9, w * 0.55, h * 0.35, (236, 110, 120), 0)


def draw_wizard(pn, x, y, st, t):
    inv = st.get("invisible", False)
    soot = st.get("soot", False)
    skin = SOOT if soot else SKIN_W
    robe = (70, 62, 78) if soot else ROBE
    yb = y + math.sin(t * 2.2) * 2.5
    if inv:
        yb += math.sin(t * 3.1) * 8          # floating
    hy = yb - 410

    if not inv:
        for sx in (-1, 1):
            pn.blob([(x + sx * 46, y - 12, 38, 14), (x + sx * 72, y - 18, 10, 8)], (64, 40, 28), 4)
        pn.poly([(x - 58, yb - 332), (x + 58, yb - 332), (x + 102, y - 16), (x - 102, y - 16)], robe, 4)
        for sx, sy in ((-55, -90), (40, -150), (-20, -250), (62, -60)):
            pn.star(x + sx, yb + sy, 11, (232, 200, 255) if not soot else (120, 120, 120), 2)
        pn.line([(x - 76, yb - 192), (x + 76, yb - 192)], INK, 12, caps=False)
        pn.line([(x - 74, yb - 192), (x + 74, yb - 192)], YELLOW if not soot else (110, 110, 100), 6, caps=False)
        pn.limb((x - 56, yb - 318), (x - 94, yb - 186), 36, robe)
        pn.ellipse(x - 96, yb - 178, 15, 15, skin, 4)

    # right (wand) arm, blended from rest to the requested pose
    k = ease(st.get("w_arm", 0.0))
    (hx0, hy0), (dx0, dy0) = WIZ_POSES["rest"]
    (hx1, hy1), (dx1, dy1) = WIZ_POSES[st.get("w_pose", "up")]
    hand = (x + lerp(hx0, hx1, k), yb + lerp(hy0, hy1, k))
    dx, dy = lerp(dx0, dx1, k), lerp(dy0, dy1, k)
    dn = math.hypot(dx, dy)
    tip = (hand[0] + dx / dn * 100, hand[1] + dy / dn * 100)
    st["_wand_tip"] = tip
    if not inv:
        pn.limb((x + 56, yb - 318), hand, 36, robe)
    pn.stroke([hand, tip], (130, 82, 40), 7, 3)
    pn.star(tip[0], tip[1], 15, YELLOW, 3, rot=t * 2)
    if not inv:
        pn.ellipse(hand[0], hand[1], 15, 15, skin, 4)

        # head: big jaw + ears, one merged silhouette
        pn.rect(x - 22, hy + 60, x + 22, hy + 90, skin, 4)
        pn.blob([(x, hy, 62, 72), (x + 5, hy + 46, 47, 34), (x - 63, hy + 6, 13, 19), (x + 63, hy + 6, 13, 19)], skin)
        beard = (238, 238, 240) if not soot else (120, 120, 120)
        pn.poly([(x - 42, hy + 66), (x + 48, hy + 66), (x + 34, hy + 118), (x + 10, hy + 168), (x - 14, hy + 116)], beard, 4)
        pn.blob([(x - 18, hy + 64, 26, 9), (x + 26, hy + 64, 26, 9)], beard, 3)

    eyes(pn, [(x - 19, hy - 22), (x + 19, hy - 22)], 19, 24, st.get("w_look", (1, 0)),
         st.get("w_blink", False) and not inv, skin, st.get("w_brow", 0.0),
         st.get("w_shock", False), st.get("dizzy", False), t)

    m = st.get("w_talk", 0.0)
    if not inv:
        pn.ellipse(x + 4, hy + 8, 11, 14, skin, 4)        # nose
        mouth(pn, x + 4, hy + 40, m, 18, smile=not soot)
    elif m > 0.15:
        mouth(pn, x + 4, hy + 40, m, 18)                    # floating mouth!

    # pointy hat
    sq = st.get("hat_squash", 0.0)
    if sq:
        sq = sq * (1 + 0.15 * math.sin(t * 25) * math.exp(-st.get("_squash_t", 9) * 5))
    hh = 160 * (1 - 0.62 * sq)
    hc = (60, 58, 66) if soot else ROBE
    y0 = hy - 56
    pn.poly([(x - 56, y0), (x + 56, y0), (x + 30, y0 - hh * 0.58), (x + 74, y0 - hh), (x + 4, y0 - hh * 0.66)], hc, 4)
    pn.poly([(x - 52, y0 - 6), (x + 52, y0 - 6), (x + 46, y0 - 24), (x - 46, y0 - 24)], YELLOW if not soot else (110, 110, 100), 3)
    pn.star(x + 2, y0 - hh * 0.38, 12, YELLOW if not soot else (150, 150, 150), 3, rot=0.2)
    pn.ellipse(x, y0 + 3, 90, 16, hc, 4)
    top = (x + 10, y0 - hh * 0.8)
    if st.get("banana_hat"):
        banana(pn, top[0] - 4, top[1] - 6, 150, -0.12)
    if st.get("toast_hat"):
        toast(pn, x + 8, y0 - hh * 0.62 - 26, 1.0)
    if soot:
        smoke(pn, x + 60, y0 - hh, t)
    if st.get("dizzy"):
        for i in range(3):
            a = t * 5 + i * 2 * math.pi / 3
            pn.star(x + math.cos(a) * 80, y0 - 10 + math.sin(a) * 16, 11, YELLOW, 2)


FUR = (126, 80, 44)
FACE = (234, 198, 152)


def draw_monkey(pn, x, y, st, t):
    bounce = st.get("m_bounce", False)
    yb = y - (abs(math.sin(t * 9)) * 16 if bounce else 2 + math.sin(t * 2.6 + 1) * 2)
    sway = math.sin(t * 2.0) * 9
    tail = [(x + 40, yb - 70), (x + 92, yb - 88), (x + 116, yb - 136), (x + 106 + sway * 0.6, yb - 182),
            (x + 82 + sway, yb - 196), (x + 70 + sway, yb - 176), (x + 84 + sway, yb - 164)]
    pn.stroke(tail, FUR, 11)
    for sx in (-1, 1):
        pn.limb((x + sx * 24, yb - 62), (x + sx * 32, y - 14), 24, FUR)
        pn.ellipse(x + sx * 38, y - 9, 23, 10, FACE, 4)
    pn.ellipse(x, yb - 100, 52, 62, FUR)
    pn.ellipse(x, yb - 90, 34, 42, FACE, 3)
    k = ease(st.get("m_arms", 0.0))
    if bounce:
        k = 0.7 + 0.3 * math.sin(t * 18)
    for sx in (-1, 1):
        hand = (x + sx * lerp(62, 84, k), yb + lerp(-72, -250, k))
        pn.limb((x + sx * 42, yb - 140), hand, 20, FUR)
        pn.ellipse(hand[0], hand[1], 12, 12, FACE, 3)
        if sx == 1 and st.get("m_banana"):
            banana(pn, hand[0] + 6, hand[1] - 18, 70, -1.2)
    hy = yb - 215
    pn.blob([(x, hy, 60, 55), (x - 64, hy - 6, 22, 22), (x + 64, hy - 6, 22, 22)], FUR)
    for sx in (-1, 1):
        pn.ellipse(x + sx * 64, hy - 6, 11, 12, FACE, 2)
    pn.line([(x - 6, hy - 52), (x - 2, hy - 70), (x + 8, hy - 56), (x + 14, hy - 68)], INK, 4)
    pn.blob([(x - 20, hy - 11, 25, 27), (x + 20, hy - 11, 25, 27), (x, hy + 24, 40, 27)], FACE, 3)
    eyes(pn, [(x - 16, hy - 15), (x + 16, hy - 15)], 15, 19, st.get("m_look", (-1, 0)),
         st.get("m_blink", False), FACE, st.get("m_brow", 0.0), st.get("m_shock", False), False, t, ow=3)
    for sx in (-1, 1):
        pn.ellipse(x + sx * 6, hy + 12, 2.6, 2.6, INK, 0)
    mouth(pn, x, hy + 30, st.get("m_talk", 0.0), 15, smile=not st.get("m_flat", False))


# --------------------------------------------------------------------------
# Backgrounds
# --------------------------------------------------------------------------
def bg_tower(pn, t, st):
    pn.rect(-600, -600, 1900, 600, (196, 176, 218), 0)
    for i in range(-3, 14):                                  # wallpaper stripes
        pn.rect(i * 110, -600, i * 110 + 46, 580, (186, 165, 210), 0)
    # arched window with night sky
    pn.rect(548, 128, 752, 372, (120, 78, 46), 4)
    pn.ellipse(650, 128, 102, 66, (120, 78, 46), 4)
    pn.rect(562, 140, 738, 360, (34, 40, 92), 0)
    pn.ellipse(650, 140, 88, 54, (34, 40, 92), 0)
    pn.ellipse(700, 165, 26, 26, (250, 246, 210), 3)
    pn.ellipse(712, 158, 22, 22, (34, 40, 92), 0)
    for sx, sy in ((600, 200), (640, 250), (690, 300), (610, 320), (720, 230)):
        pn.star(sx, sy, 5 + 2 * math.sin(t * 4 + sx), (250, 246, 210), 0, points=4)
    pn.line([(650, 76), (650, 360)], (120, 78, 46), 10, caps=False)
    pn.line([(562, 250), (738, 250)], (120, 78, 46), 10, caps=False)
    pn.rect(530, 368, 770, 384, (140, 92, 54), 4)
    # bookshelf
    pn.rect(1010, 170, 1236, 586, (128, 82, 48), 4)
    cols = [(200, 60, 60), (60, 120, 200), (230, 180, 60), (80, 160, 90), (150, 80, 170), (220, 120, 60)]
    for row, sy in enumerate((260, 352, 444, 536)):
        xx = 1026
        rnd = random.Random(row)
        while xx < 1210:
            bw = rnd.randint(16, 26)
            bh = rnd.randint(56, 74)
            pn.rect(xx, sy - bh, xx + bw, sy, cols[rnd.randrange(len(cols))], 2)
            xx += bw + 4
        pn.rect(1018, sy, 1228, sy + 10, (98, 60, 34), 3)
    # potion table
    pn.rect(40, 470, 290, 488, (128, 82, 48), 4)
    for lx in (60, 262):
        pn.rect(lx, 488, lx + 14, 590, (110, 70, 40), 3)
    for i, (bx, c) in enumerate(((90, (90, 210, 120)), (150, (230, 80, 120)), (215, (90, 170, 240)))):
        h = 38 + 10 * i
        pn.ellipse(bx, 470 - h * 0.5, 22, h * 0.5, c, 3)
        pn.rect(bx - 6, 470 - h - 22, bx + 6, 470 - h + 2, c, 3)
        pn.rect(bx - 8, 470 - h - 30, bx + 8, 470 - h - 20, (150, 100, 60), 2)
    # baseboard + floor + rug
    pn.rect(-600, 580, 1900, 602, (96, 60, 36), 4)
    pn.rect(-600, 602, 1900, 1400, (164, 112, 70), 0)
    for i in range(-6, 26):
        pn.line([(i * 70, 602), (i * 70 - 140, 760)], (146, 98, 60), 3, caps=False)
    pn.ellipse(655, 664, 360, 42, (180, 52, 60), 4)
    pn.ellipse(655, 664, 300, 30, (210, 168, 70), 0)
    pn.ellipse(655, 664, 280, 24, (180, 52, 60), 0)


def bg_kitchen(pn, t, st):
    pn.rect(-600, -600, 1900, 610, (248, 228, 150), 0)
    for i in range(-3, 22):                                  # tiles
        for j in range(4):
            pn.rect(560 + i * 40 - 600 * 0, 340 + j * 38, 560 + i * 40 + 36, 340 + j * 38 + 34, (236, 240, 244), 0)
    pn.rect(560, 60, 1300, 240, (170, 210, 220), 4)              # upper cabinets
    for cx in (650, 840, 1030, 1220):
        pn.line([(cx, 60), (cx, 240)], INK, 4, caps=False)
        pn.ellipse(cx - 12, 200, 5, 5, (200, 200, 205), 2)
    pn.rect(560, 505, 1300, 640, (170, 210, 220), 4)             # lower cabinets
    pn.rect(548, 486, 1300, 506, (150, 150, 160), 4)              # counter top
    for cx in (750, 950, 1150):
        pn.line([(cx, 506), (cx, 640)], INK, 4, caps=False)
    # fridge on the left
    pn.rect(70, 150, 290, 640, (238, 238, 240), 4, 14)
    pn.line([(70, 330), (290, 330)], INK, 4, caps=False)
    pn.rect(260, 210, 272, 300, (180, 180, 190), 2)
    pn.rect(260, 360, 272, 460, (180, 180, 190), 2)
    pn.rect(-600, 640, 1900, 1400, (220, 220, 228), 0)
    for i in range(-10, 40):
        for j in range(3):
            if (i + j) % 2 == 0:
                pn.poly([(i * 70 + j * 40, 640 + j * 40), (i * 70 + 70 + j * 40, 640 + j * 40),
                         (i * 70 + 110 + j * 40, 680 + j * 40), (i * 70 + 40 + j * 40, 680 + j * 40)], (90, 96, 120), 0)
    pn.line([(-600, 640), (1900, 640)], INK, 4, caps=False)
    # toaster
    burnt = st.get("toaster_burnt", False)
    body = (58, 56, 60) if burnt else (196, 202, 214)
    pn.rect(764, 410, 896, 486, body, 4, 22)
    pn.rect(790, 404, 846, 414, INK, 0, 3)
    pn.rect(820, 404, 876, 414, INK, 0, 3)
    pn.rect(896, 430, 910, 446, (40, 40, 40), 3, 3)
    if not burnt:
        pn.line([(784, 430), (784, 470)], (250, 250, 255), 6)
    else:
        smoke(pn, 830, 400, t, 4)


BACKGROUNDS = {"tower": bg_tower, "kitchen": bg_kitchen}

SHOTS_LANDSCAPE = {
    "wide": (640, 360, 1.0),
    "cu_w": (420, 300, 1.8),
    "cu_m": (880, 470, 1.9),
    "k_wide": (640, 360, 1.0),
    "k_cu_w": (420, 255, 1.6),
}
# YouTube Shorts: vertical 9:16, 1080x1920, framed for a phone screen
SHOTS_SHORTS = {
    "wide": (655, 470, 1.5),
    "cu_w": (440, 380, 2.6),
    "cu_m": (880, 540, 3.0),
    "k_wide": (620, 470, 1.7),
    "k_cu_w": (430, 330, 2.4),
}
SHOTS = SHOTS_LANDSCAPE
SHORTS = False


def set_shorts():
    global W, H, SHOTS, SHORTS, OUT_DIR
    W, H, SHOTS, SHORTS = 1080, 1920, SHOTS_SHORTS, True
    OUT_DIR = os.path.join(HERE, "output", "shorts")

# --------------------------------------------------------------------------
# Gag effects. Each gets (state, local_t, duration, overlays) and may mutate
# the state and/or append overlay draw callbacks (drawn above characters).
# --------------------------------------------------------------------------


def fx_sparkle_wand(st, lt, dur, ov):
    ov.append(lambda pn: sparkles(pn, *st["_wand_tip"], lt))


def fx_banana_drop(st, lt, dur, ov):
    st["w_arm"] = 1 - ease((lt - 0.45) * 4)
    st["w_look"] = (0, -1)
    ov.append(lambda pn: poof(pn, 440, 20, lt / 0.7, (255, 255, 255), 0.9))
    t0, tc, land = 0.22, 0.62, 132.0
    if t0 <= lt < tc:
        g = 2 * (land + 140) / (tc - t0) ** 2
        yy = -140 + 0.5 * g * (lt - t0) ** 2
        ov.append(lambda pn: banana(pn, 446, yy, 150, -0.12 + lt * 2))
    elif lt >= tc:
        st.update(banana_hat=True, hat_squash=1.0, dizzy=True, _squash_t=lt - tc, w_shock=True)


def fx_toaster(st, lt, dur, ov):
    st["w_pose"] = "point"
    st["w_arm"] = min(1.0, lt / 0.3) if lt < 1.0 else max(0.0, 1 - (lt - 1.0) * 3)
    st["w_brow"] = 1.0
    target = (830, 440)
    if 0.35 <= lt < 0.95:
        ov.append(lambda pn: lightning(pn, st["_wand_tip"], target, int(lt * 30)))
    if lt >= 0.95:
        st.update(soot=True, toaster_burnt=True, w_shock=True, w_brow=0)
        ov.append(lambda pn: poof(pn, 830, 430, (lt - 0.95) / 0.75, (255, 170, 60), 1.3))
        if lt < 1.1:
            ov.append(lambda pn: pn.star(830, 440, 190, (255, 240, 120), 5, rot=lt, points=9))
    t0, t1 = 1.0, 1.85
    if t0 <= lt < t1:
        k = (lt - t0) / (t1 - t0)
        tx = lerp(830, 428, k)
        ty = lerp(420, 70, k) - 420 * math.sin(math.pi * k) * 0.9
        ov.append(lambda pn: toast(pn, tx, ty, 1.0))
    elif lt >= t1:
        st["toast_hat"] = True


def fx_invis(st, lt, dur, ov):
    st.update(w_pose="point", w_arm=1.0, m_shock=lt < 0.5)
    face = (880, 440)
    if 0.0 <= lt < 0.25:
        ov.append(lambda pn: lightning(pn, st["_wand_tip"], face, int(lt * 40)))
    elif 0.25 <= lt < 0.45:   # bounces back off the monkey!
        ov.append(lambda pn: lightning(pn, face, (430, 300), int(lt * 40)))
    if lt >= 0.4:
        ov.append(lambda pn: poof(pn, 430, 330, (lt - 0.4) / 0.9, (240, 240, 255), 2.0))
    if lt >= 0.8:
        st["invisible"] = True
        st["m_shock"] = True


FX = {"sparkle_wand": fx_sparkle_wand, "banana_drop": fx_banana_drop,
      "toaster": fx_toaster, "invis": fx_invis}

# --------------------------------------------------------------------------
# Episodes (dialogue is in English)
# --------------------------------------------------------------------------
EPISODES = [
    dict(num=1, title="The Banana Spell", beats=[
        dict(type="line", who="W", text="Behold, Pip! The most powerful spell in the universe!",
             shot="cu_w", state=dict(w_arm=1, w_brow=1), fx="sparkle_wand", sfx=[(0, "chime")]),
        dict(type="line", who="M", text="Is it a banana? Please be a banana.",
             shot="cu_m", state=dict(m_bounce=True)),
        dict(type="line", who="W", text="Banana... kazam!", shot="wide",
             state=dict(w_arm=1, w_brow=1), fx="sparkle_wand"),
        dict(type="act", dur=1.6, shot="wide", fx="banana_drop", sfx=[(0, "poof"), (0.62, "bonk")]),
        dict(type="line", who="M", text="Eh. I'll allow it.", shot="cu_m", state=dict(m_look=(-1, -0.6))),
        dict(type="line", who="W", text="Ow.", shot="wide",
             state=dict(banana_hat=True, hat_squash=1.0, dizzy=True)),
    ]),
    dict(num=2, title="The Toaster Incident", beats=[
        dict(type="line", who="M", text="Gorbo, can you fix the coffee machine?", shot="wide",
             state=dict(m_arms=0.5)),
        dict(type="line", who="W", text="Ha! Easier than the time I fixed the toaster.",
             shot="cu_w", state=dict(w_arm=0.5, w_brow=1), fx="sparkle_wand"),
        dict(type="act", dur=2.2, shot="k_wide", bg="kitchen", fx="toaster",
             state=dict(show_m=False), sfx=[(0, "whoosh"), (0.35, "zap"), (0.95, "boom"), (1.85, "bonk")]),
        dict(type="line", who="W", text="Toast is ready.", shot="k_cu_w", bg="kitchen",
             state=dict(show_m=False, soot=True, toast_hat=True, toaster_burnt=True)),
        dict(type="line", who="M", text="We don't have a kitchen anymore.", shot="wide",
             state=dict(m_flat=True), sfx=[(0, "whoosh")]),
    ]),
    dict(num=3, title="Now You See Me", beats=[
        dict(type="line", who="M", text="Make me invisible! Please, please, please!", shot="cu_m",
             state=dict(m_bounce=True)),
        dict(type="line", who="W", text="Fine. Invisibilus!", shot="wide",
             state=dict(w_pose="point", w_arm=1, w_brow=1), fx="sparkle_wand", sfx=[(0, "chime")]),
        dict(type="act", dur=1.4, shot="wide", fx="invis", sfx=[(0.0, "zap"), (0.4, "poof")]),
        dict(type="line", who="M", text="Uh, boss? You're the invisible one.", shot="wide",
             state=dict(invisible=True, m_flat=True)),
        dict(type="line", who="W", text="I meant to do that.", shot="cu_w",
             state=dict(invisible=True, w_brow=1)),
    ]),
]

GAP = 0.18      # silence after each line
LEAD = 0.06     # mouth starts slightly before... audio


def build_timeline(ep):
    t = TITLE_DUR
    segs = []
    for b in ep["beats"]:
        s = dict(b, start=t)
        if b["type"] == "line":
            clip = tts(b["who"], b["text"])
            s.update(clip=clip, env=mouth_envelope(clip), dur=len(clip) / SR + GAP + LEAD)
        segs.append(s)
        t += s["dur"]
    total = t + 0.35
    if total > MAX_LEN:
        raise SystemExit(f"Episode {ep['num']} is {total:.2f}s — over the {MAX_LEN}s limit")
    return segs, total


def mix_audio(segs, total):
    out = np.zeros(int(total * SR) + SR)

    def place(sig, at, gain=1.0):
        i = int(at * SR)
        out[i:i + len(sig)] += sig[: len(out) - i] * gain

    place(sfx("jingle"), 0.05, 0.9)
    for s in segs:
        if s["type"] == "line":
            place(s["clip"], s["start"] + LEAD, 1.0)
        for off, name in s.get("sfx", []):
            place(sfx(name), s["start"] + off, 0.55)
    out = out[: int(total * SR)]
    out = out / max(1e-6, np.abs(out).max()) * 0.9
    return (out * 32767).astype(np.int16)


_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT_BOLD, size)
    return _fonts[size]


def title_card(ep, t):
    img = Image.new("RGB", (W * SS, H * SS), (30, 26, 70))
    pn = Pen(img, Cam(640, 360, 1.0))
    pn.ellipse(640, 360 + H * 0.56, 900, 260 + H * 0.2, (52, 40, 110), 0)
    rnd = random.Random(7)
    for i in range(40 if not SHORTS else 90):
        sx, sy = rnd.uniform(640 - W / 2, 640 + W / 2), rnd.uniform(360 - H / 2, 360 + H / 2)
        pn.star(sx, sy, 3 + 3 * abs(math.sin(t * 5 + i)), (250, 240, 200), 0, points=4)
    pn2 = Pen(img, Cam(655, 210, 1.2) if SHORTS else Cam(655, 175, 0.5))
    st = dict(w_arm=1, w_pose="up", w_brow=1, w_look=(0.4, 0.3), m_arms=1, m_look=(-0.4, 0.3),
              w_talk=0, m_talk=0.6)
    draw_wizard(pn2, 430, 660, st, t)
    draw_monkey(pn2, 880, 660, st, t)
    sparkles(pn2, *st["_wand_tip"], t)
    img = img.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    pop = min(1.0, t / 0.25)
    if SHORTS:
        f = font(int(120 * (0.6 + 0.4 * pop)))
        d.text((W / 2, 300), "GORBO & PIP", font=f, fill=YELLOW, anchor="mm",
               stroke_width=9, stroke_fill=INK)
        d.text((W / 2, 430), f"Episode {ep['num']}", font=font(54), fill=(255, 255, 255),
               anchor="mm", stroke_width=5, stroke_fill=INK)
        d.text((W / 2, 510), ep["title"], font=font(62), fill=(255, 255, 255),
               anchor="mm", stroke_width=5, stroke_fill=INK)
        return img
    f = font(int(96 * (0.6 + 0.4 * pop)))
    d.text((W / 2, 120), "GORBO & PIP", font=f, fill=YELLOW, anchor="mm",
           stroke_width=7, stroke_fill=INK)
    d.text((W / 2, 205), f"Episode {ep['num']}:  {ep['title']}", font=font(40), fill=(255, 255, 255),
           anchor="mm", stroke_width=4, stroke_fill=INK)
    return img


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
    st = dict(show_w=True, show_m=True)
    st.update(seg.get("state", {}))
    st["w_blink"] = (t * 1000) % 3300 < 120
    st["m_blink"] = (t * 1000 + 1700) % 2900 < 120
    if seg["type"] == "line":
        idx = int((lt - LEAD) * FPS)
        level = seg["env"][idx] if 0 <= idx < len(seg["env"]) else 0.0
        if seg["who"] == "W":
            st["w_talk"] = level
            st.setdefault("m_look", (-1, 0))
        else:
            st["m_talk"] = level
    overlays = []
    if seg.get("fx"):
        FX[seg["fx"]](st, lt, seg["dur"], overlays)

    cx, cy, z = SHOTS[seg["shot"]]
    z *= 1 + 0.035 * (lt / seg["dur"])            # slow push-in
    img = Image.new("RGB", (W * SS, H * SS))
    pn = Pen(img, Cam(cx, cy, z))
    BACKGROUNDS[seg.get("bg", "tower")](pn, t, st)
    if st["show_w"]:
        draw_wizard(pn, 430, 660, st, t)
    if st["show_m"]:
        draw_monkey(pn, 880, 660, st, t)
    for o in overlays:
        o(pn)
    img = img.resize((W, H), Image.LANCZOS)

    if seg["type"] == "line":                     # English captions
        d = ImageDraw.Draw(img)
        name = "GORBO" if seg["who"] == "W" else "PIP"
        if SHORTS:   # big, wrapped, above the Shorts UI at the bottom
            words, lines, cur = seg["text"].split(), [], ""
            for wd in words:
                trial = (cur + " " + wd).strip()
                if d.textlength(trial, font=font(58)) > W - 140 and cur:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = trial
            lines.append(cur)
            y0 = 1360
            d.text((W / 2, y0), name, font=font(46), fill=YELLOW, anchor="mm",
                   stroke_width=5, stroke_fill=INK)
            for i, ln in enumerate(lines):
                d.text((W / 2, y0 + 70 + i * 70), ln, font=font(58), fill=(255, 255, 255),
                       anchor="mm", stroke_width=6, stroke_fill=INK)
        else:
            d.text((W / 2, H - 46), f"{name}: {seg['text']}", font=font(30), fill=(255, 255, 255),
                   anchor="mm", stroke_width=4, stroke_fill=INK)
    return img


def render_episode(ep):
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Episode {ep['num']}: {ep['title']}")
    segs, total = build_timeline(ep)
    print(f"  length {total:.2f}s")
    wav_path = os.path.join(CACHE, f"ep{ep['num']}.wav")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(mix_audio(segs, total).tobytes())
    slug = ep["title"].lower().replace(" ", "_")
    suffix = "_short" if SHORTS else ""
    out = os.path.join(OUT_DIR, f"gorbo_and_pip_ep{ep['num']}_{slug}{suffix}.mp4")
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav_path,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    n = int(total * FPS)
    for fi in range(n):
        proc.stdin.write(render_frame(ep, segs, fi).tobytes())
    proc.stdin.close()
    proc.wait()
    print("  ->", out)
    return out


def main():
    args = sys.argv[1:]
    if "--shorts" in args:
        set_shorts()
        args.remove("--shorts")
    want = {int(a) for a in args}
    outs = [render_episode(ep) for ep in EPISODES if not want or ep["num"] in want]
    if len(outs) > 1:
        lst = os.path.join(CACHE, "concat.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{o}'\n" for o in outs)
        full = os.path.join(OUT_DIR, "gorbo_and_pip_all_episodes" + ("_short" if SHORTS else "") + ".mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", lst, "-c", "copy", full], check=True)
        print("All episodes ->", full)


if __name__ == "__main__":
    main()
