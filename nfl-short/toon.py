"""Tank & Zippy cartoon engine: shared characters, sets, audio and rendering for every episode.

Each episode module defines NAME, LINES, build_timeline(dur) and render_scene(t, ctx),
then calls toon.main(module, output_path)."""
import math, os, random, subprocess, sys, wave
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC = os.path.join(HERE, "music", "14._i_am_not_clumsy.mp3")
CFG = {"out_dir": os.path.join(HERE, "build"), "lines": {}}

W, H, S, FPS, SR = 1080, 1920, 2, 30, 44100
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
OUT = (25, 20, 30)
PURPLE, GOLD, RED = (92, 45, 145), (255, 200, 40), (200, 40, 45)
GROUND = 1480

VOICE = {  # gTTS accent, pitch factor, tempo after pitch
    "narrator": ("co.uk", 0.95, 1.12),
    "tank": ("us", 0.72, 1.18),
    "zippy": ("com.au", 1.45, 0.88),
    "coach": ("ca", 0.8, 1.2),
    "spicy": ("co.in", 1.2, 1.0),
}
NAMES = {"narrator": ("NARRATOR", (40, 40, 50)), "tank": ("TANK", PURPLE), "zippy": ("ZIPPY", (235, 110, 20)),
         "coach": ("COACH PANCAKE", (30, 110, 180)), "spicy": ("MR. SPICY", RED)}


def run(*cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, stdout=subprocess.PIPE).stdout
    return np.frombuffer(raw, np.float32).copy()


def make_voices():
    LINES, OUT_DIR = CFG["lines"], CFG["out_dir"]
    from gtts import gTTS
    clips = {}
    for key, (who, text) in LINES.items():
        mp3, wav = os.path.join(OUT_DIR, key + ".mp3"), os.path.join(OUT_DIR, key + ".wav")
        if not os.path.exists(wav):
            tld, pitch, tempo = VOICE[who]
            gTTS(text, lang="en", tld=tld).save(mp3)
            af = (f"silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                  f"silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                  f"asetrate={int(24000 * pitch)},aresample={SR},atempo={tempo}")
            run("ffmpeg", "-y", "-i", mp3, "-af", af, "-ac", "1", wav)
        a = load_audio(wav)
        clips[key] = a / (np.abs(a).max() + 1e-6) * 0.9
    return clips


# ---------------------------------------------------------------- sfx
rng = np.random.default_rng(7)


def env(n, a=0.01, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.minimum(1, (n / SR - t) / max(r, 1e-4))
    return np.clip(e, 0, 1)


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def sfx_whistle(d=0.9):
    n = int(d * SR); t = np.arange(n) / SR
    f = 2900 + 120 * np.sign(np.sin(2 * np.pi * 28 * t))
    return 0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.02, 0.1)


def sfx_whoosh(d=1.2):
    n = int(d * SR)
    x = lowpass(rng.standard_normal(n), 12) - lowpass(rng.standard_normal(n), 60)
    return 0.6 * x * np.sin(np.linspace(0, np.pi, n)) ** 2


def sfx_crash(d=1.0):
    n = int(d * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n) * np.exp(-t * 6) + 0.8 * np.sin(2 * np.pi * 70 * t) * np.exp(-t * 9)
    clank = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 12) for f in (1250, 1830, 2610)) * 0.2
    return 0.7 * (lowpass(x, 3) + clank)


def sfx_boing(d=0.6):
    n = int(d * SR); t = np.arange(n) / SR
    f = 180 + 260 * t / d + 40 * np.sin(2 * np.pi * 14 * t)
    return 0.45 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3)


def sfx_crowd(d=2.0, amt=0.25):
    n = int(d * SR)
    x = lowpass(rng.standard_normal(n), 8) - lowpass(rng.standard_normal(n), 40)
    return amt * x * env(n, 0.4, 0.6)


def sfx_thud(d=0.25):
    n = int(d * SR); t = np.arange(n) / SR
    return 0.8 * (np.sin(2 * np.pi * (90 - 120 * t) * t) + 0.3 * lowpass(rng.standard_normal(n), 6)) * np.exp(-t * 18)


def sfx_pop(d=0.15):
    n = int(d * SR); t = np.arange(n) / SR
    return 0.4 * np.sin(2 * np.pi * (600 + 2400 * t / d) * t) * np.exp(-t * 25)




def mix_audio(clips, ev, sfx, total):
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32); fx = np.zeros(n, np.float32)
    for key, t in ev:
        i = int(t * SR); a = clips[key]; voice[i:i + len(a)] += a[: n - i]
    for a, t in sfx:
        i = int(t * SR); fx[i:i + len(a)] += a[: n - i].astype(np.float32)
    music = load_audio(MUSIC)
    music = np.tile(music, int(np.ceil(n / len(music))))[:n]
    vol_env = lowpass((np.abs(voice) > 0.02).astype(np.float32), 8000)
    music *= 0.32 - 0.18 * np.clip(vol_env * 3, 0, 1)
    fade = int(1.5 * SR); music[-fade:] *= np.linspace(1, 0, fade)
    mix = voice * 0.95 + fx * 0.7 + music
    mix = np.tanh(mix * 1.1) * 0.9
    path = os.path.join(CFG["out_dir"], "mix.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix[: int(total * SR)] * 32767).astype(np.int16).tobytes())
    return path


def mouth_envelopes(clips):
    out = {}
    hop = SR // FPS
    for k, a in clips.items():
        frames = len(a) // hop + 1
        rms = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(frames)])
        out[k] = np.clip(rms / (rms.max() + 1e-6) * 1.4, 0, 1)
    return out


# ---------------------------------------------------------------- drawing helpers
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, int(size * S))
    return _fonts[size]


class Pen:
    """Draws in logical 1080x1920 coordinates on a 2x canvas, offset by (ox, oy) and scaled by sc."""

    def __init__(self, img, ox=0, oy=0, sc=1.0):
        self.d = ImageDraw.Draw(img); self.ox, self.oy, self.sc = ox, oy, sc

    def p(self, x, y):
        return ((self.ox + x * self.sc) * S, (self.oy + y * self.sc) * S)

    def ell(self, cx, cy, rx, ry, fill, ow=6):
        x0, y0 = self.p(cx - rx, cy - ry); x1, y1 = self.p(cx + rx, cy + ry)
        self.d.ellipse([x0, y0, x1, y1], fill=fill, outline=OUT if ow else None, width=int(ow * S * self.sc) if ow else 0)

    def poly(self, pts, fill, ow=6):
        self.d.polygon([self.p(*q) for q in pts], fill=fill, outline=OUT if ow else None,
                       width=int(ow * S * self.sc) if ow else 0)

    def line(self, pts, fill, w):
        self.d.line([self.p(*q) for q in pts], fill=fill, width=max(1, int(w * S * self.sc)), joint="curve")

    def limb(self, pts, fill, w):
        self.line(pts, OUT, w + 12)
        for q in (pts[0], pts[-1]):
            self.ell(q[0], q[1], (w + 12) / 2, (w + 12) / 2, OUT, 0)
        self.line(pts, fill, w)

    def rect(self, x0, y0, x1, y1, fill, ow=6, r=0):
        a = self.p(x0, y0); b = self.p(x1, y1)
        self.d.rounded_rectangle([a, b], radius=r * S * self.sc, fill=fill, outline=OUT if ow else None,
                                 width=int(ow * S * self.sc) if ow else 0)

    def text(self, x, y, s, size, fill, stroke=6, anchor="mm"):
        self.d.text(self.p(x, y), s, font=font(size * self.sc), fill=fill, anchor=anchor,
                    stroke_width=int(stroke * S * self.sc), stroke_fill=OUT)


def football(pen, x, y, r=34, ang=0):
    pts = [(x + math.cos(a) * r * 1.5 * math.cos(ang) - math.sin(a) * r * math.sin(ang),
            y + math.cos(a) * r * 1.5 * math.sin(ang) + math.sin(a) * r * math.cos(ang))
           for a in np.linspace(0, 2 * math.pi, 28)]
    pen.poly(pts, (140, 70, 30), 5)
    c, s_ = math.cos(ang), math.sin(ang)
    pen.line([(x - c * r * .6, y - s_ * r * .6), (x + c * r * .6, y + s_ * r * .6)], "white", 5)
    for k in (-0.4, -0.13, 0.13, 0.4):
        cx, cy = x + c * r * k, y + s_ * r * k
        pen.line([(cx + s_ * 10, cy - c * 10), (cx - s_ * 10, cy + c * 10)], "white", 4)


SPR_W, SPR_H, AX, AY = 900, 1050, 450, 980  # sprite canvas (logical) and feet anchor


def character(kind, mouth=0.0, blink=False, look=(0, 0), arms="down", dizzy=False, messy=False,
              hotdog=False, ball=False, jersey=PURPLE, number=None, angry=False, t=0.0, wave_=False, tilt=0):
    img = Image.new("RGBA", (SPR_W * S, SPR_H * S), (0, 0, 0, 0))
    pen = Pen(img, AX, AY)
    big = kind in ("tank", "opp")
    bw, bh, hr, lh = (340, 350, 112, 120) if big else (175, 215, 108, 115)
    skin = {"tank": (150, 95, 60), "opp": (235, 185, 150), "zippy": (255, 214, 170)}[kind]
    number = number or {"tank": "77", "zippy": "1", "opp": "99"}[kind]
    top = -lh - bh + 25
    # legs + shoes
    for sx in (-1, 1):
        x = sx * bw * 0.2
        pen.limb([(x, -lh - 20), (x, -22)], (240, 240, 240), max(44, bw * 0.2))
        pen.ell(x + sx * 12, -16, bw * 0.13 + 24, 20, (30, 30, 35))
    # arms
    sh = top + 55
    if arms == "up":
        ah = [(-bw * 0.42, top - hr * 2.1), (bw * 0.42, top - hr * 2.1)]
    elif arms == "throw":
        ah = [(-bw * 0.62, -lh - bh * 0.25), (bw * 0.75, top - hr * 1.6)]
    elif arms == "wave":
        ah = [(-bw * 0.62, -lh - bh * 0.3), (bw * 0.85, top - hr * 1.2 + 25 * math.sin(t * 14))]
    elif arms == "flail":
        ah = [(-bw * 0.95, top - 40 + 50 * math.sin(t * 25)), (bw * 0.95, top - 40 - 50 * math.sin(t * 25))]
    elif arms == "hips":
        ah = [(-bw * 0.62, -lh - bh * 0.3), (bw * 0.62, -lh - bh * 0.3)]
    else:
        ah = [(-bw * 0.62, -lh - bh * 0.3 + 6 * math.sin(t * 3)), (bw * 0.62, -lh - bh * 0.3 + 6 * math.sin(t * 3 + 1))]
    aw = 46 if big else 32
    for sx, hand in zip((-1, 1), ah):
        elbow = ((sx * bw * 0.5 + hand[0]) / 2 + sx * 25, (sh + hand[1]) / 2 + 10)
        pen.limb([(sx * bw * 0.42, sh), elbow, hand], jersey, aw)
        pen.ell(hand[0], hand[1], aw * 0.75, aw * 0.75, skin)
    # body
    pen.ell(0, -lh - bh / 2 + 10, bw / 2, bh / 2, jersey)
    pen.ell(0, top + 30, bw * 0.6, bh * 0.17, jersey)
    pen.line([(-bw * 0.45, -lh - bh * 0.18), (bw * 0.45, -lh - bh * 0.18)], GOLD, 10)
    pen.text(0, -lh - bh * 0.5, number, bh * 0.32, GOLD, 5)
    if messy:
        for (mx, my, mr, c) in ((-0.2, 0.55, 0.12, RED), (0.18, 0.35, 0.09, (250, 210, 30)), (0.05, 0.75, 0.07, RED)):
            pen.ell(mx * bw, -lh - bh * my, mr * bw, mr * bw * 0.8, c, 0)
    if ball:
        football(pen, bw * 0.05, -lh - bh * 0.55, 30 if not big else 36, -0.5)
    # head
    hy = top - hr * 0.7
    hx = 0
    k = 1.32 if kind == "zippy" else 1.12
    pen.ell(hx, hy - 8, hr * k, hr * k * 0.98, jersey)  # helmet shell
    pen.poly([(hx - 14, hy - hr * k * 0.98 - 4), (hx + 14, hy - hr * k * 0.98 - 4), (hx + 12, hy - hr * 0.4),
              (hx - 12, hy - hr * 0.4)], GOLD, 0)
    for sx in (-1, 1):
        pen.ell(hx + sx * hr * k * 0.82, hy + 8, 13, 13, (40, 20, 60), 0)
    pen.ell(hx, hy + hr * 0.22, hr * 0.82, hr * 0.68, skin, 5)  # face
    # eyes
    ex, ey, erx, ery = hr * 0.33, hy + hr * 0.05, hr * (0.24 if kind == "zippy" else 0.19), hr * (0.3 if kind == "zippy" else 0.23)
    for sx in (-1, 1):
        cx = hx + sx * ex
        if dizzy:
            a = t * 9 * sx
            pts = [(cx + math.cos(a + i * 0.5) * erx * (i / 14), ey + math.sin(a + i * 0.5) * erx * (i / 14)) for i in range(15)]
            pen.ell(cx, ey, erx, ery, "white", 4); pen.line(pts, OUT, 5)
        elif blink:
            pen.line([(cx - erx, ey), (cx + erx, ey)], OUT, 7)
        else:
            pen.ell(cx, ey, erx, ery, "white", 4)
            pen.ell(cx + look[0] * erx * 0.45, ey + look[1] * ery * 0.45, erx * 0.45, erx * 0.45, OUT, 0)
            pen.ell(cx + look[0] * erx * 0.45 - erx * 0.15, ey + look[1] * ery * 0.45 - erx * 0.15, erx * 0.13, erx * 0.13, "white", 0)
        # brows
        by = ey - ery - 14
        if angry:
            pen.line([(cx - sx * erx * 1.1, by - 14), (cx + sx * erx * 0.9, by + 10)], OUT, 11)
        elif kind != "zippy":
            pen.line([(cx - erx, by + 2), (cx + erx, by - 4 * sx)], OUT, 12)
        else:
            pen.line([(cx - erx * 0.8, by - 6), (cx + erx * 0.8, by - 10)], OUT, 6)
    # mouth
    my = hy + hr * 0.5
    if hotdog:
        pen.ell(hx, my, hr * 0.62, hr * 0.17, (230, 170, 90), 5)
        pen.ell(hx, my - 2, hr * 0.72, hr * 0.09, (185, 75, 50), 4)
        pen.line([(hx - hr * 0.5 + i * hr * 0.1, my - 4 + (8 if i % 2 else -2)) for i in range(11)], (250, 210, 30), 5)
    elif mouth > 0.1:
        pen.ell(hx, my, hr * (0.22 + 0.1 * mouth), hr * (0.06 + 0.22 * mouth), (110, 20, 30), 5)
        pen.ell(hx, my + hr * 0.12 * mouth, hr * 0.14, hr * 0.07 * mouth + 1, (230, 90, 100), 0)
    else:
        pts = [(hx + math.cos(a) * hr * 0.25, my - hr * 0.08 + math.sin(a) * hr * 0.14) for a in np.linspace(0.3, math.pi - 0.3, 10)]
        pen.line(pts, OUT, 7)
    if messy:
        pen.ell(hx - hr * 0.5, hy - hr * 0.7, hr * 0.2, hr * 0.14, RED, 0)
        pen.ell(hx + hr * 0.6, hy - hr * 0.3, hr * 0.12, hr * 0.1, (250, 210, 30), 0)
    # facemask (chin bar)
    pen.line([(hx - hr * 0.8, hy + hr * 0.25), (hx - hr * 0.55, hy + hr * 0.82), (hx + hr * 0.55, hy + hr * 0.82),
              (hx + hr * 0.8, hy + hr * 0.25)], OUT, 14)
    pen.line([(hx - hr * 0.8, hy + hr * 0.25), (hx - hr * 0.55, hy + hr * 0.82), (hx + hr * 0.55, hy + hr * 0.82),
              (hx + hr * 0.8, hy + hr * 0.25)], (195, 195, 205), 7)
    if dizzy:
        for i in range(4):
            a = t * 4 + i * math.pi / 2
            star(pen, hx + math.cos(a) * hr * 1.4, hy - hr * 1.3 + math.sin(a) * hr * 0.35, 20, GOLD)
    if tilt:
        img = img.rotate(tilt, center=(AX * S, (AY - lh - bh) * S), resample=Image.BICUBIC)
    return img


def coach(mouth=0.0, blink=False, look=(0, 0), t=0.0, arms="clipboard", angry=False):
    """Coach Pancake: short, round, giant mustache, team cap, clipboard."""
    img = Image.new("RGBA", (SPR_W * S, SPR_H * S), (0, 0, 0, 0))
    pen = Pen(img, AX, AY)
    bw, bh, hr, lh = 270, 250, 108, 95
    skin = (240, 190, 150)
    for sx in (-1, 1):
        pen.limb([(sx * 55, -lh - 20), (sx * 55, -22)], (205, 185, 135), 52)
        pen.ell(sx * 67, -16, 58, 20, (70, 45, 30))
    top = -lh - bh + 15
    sh = top + 50
    if arms == "point":
        ah = [(-150, -lh - bh * 0.35), (175, top - 170 + 10 * math.sin(t * 12))]
    elif arms == "facepalm":
        ah = [(-150, -lh - bh * 0.35), (25, top - hr * 0.6)]
    else:
        ah = [(-150, -lh - bh * 0.35 + 5 * math.sin(t * 3)), (60, -lh - bh * 0.5)]
    for sx, hand in zip((-1, 1), ah):
        elbow = ((sx * 120 + hand[0]) / 2 + sx * 25, (sh + hand[1]) / 2 + 15)
        pen.limb([(sx * 115, sh), elbow, hand], (200, 200, 212), 40)
    pen.ell(0, -lh - bh / 2 + 10, bw / 2, bh / 2, (200, 200, 212))
    pen.poly([(-45, top + 5), (0, top + 55), (45, top + 5)], (240, 240, 245), 5)
    pen.line([(-40, top + 20), (0, -lh - bh * 0.45), (40, top + 20)], (40, 40, 50), 4)
    pen.rect(-14, -lh - bh * 0.45, 22, -lh - bh * 0.45 + 22, (220, 220, 230), 4, 6)
    pen.text(-60, -lh - bh * 0.6, "W", 40, PURPLE, 0)
    if arms == "clipboard":
        pen.rect(-10, -lh - bh * 0.75, 140, -lh - bh * 0.15, (150, 100, 60), 6, 8)
        pen.rect(5, -lh - bh * 0.7, 125, -lh - bh * 0.2, "white", 0, 4)
        for i in range(4):
            pen.line([(20, -lh - bh * (0.62 - i * 0.1)), (110, -lh - bh * (0.62 - i * 0.1))], (120, 120, 140), 4)
        pen.text(60, -lh - bh * 0.42, "X O", 28, RED, 0)
    for sx, hand in zip((-1, 1), ah):
        pen.ell(hand[0], hand[1], 30, 30, skin)
    hy = top - hr * 0.75
    pen.ell(0, hy, hr, hr * 0.97, skin)
    pen.ell(-hr * 0.98, hy + 10, 22, 30, skin)
    pen.ell(hr * 0.98, hy + 10, 22, 30, skin)
    pen.ell(-hr * 1.02, hy + 5, 26, 34, (40, 40, 50), 4)  # headset cup
    pen.line([(-hr * 1.02, hy + 30), (-hr * 0.5, hy + hr * 0.6)], (40, 40, 50), 7)
    pen.ell(-hr * 0.45, hy + hr * 0.6, 10, 10, (40, 40, 50), 0)
    # cap
    pen.d.chord([pen.p(-hr * 1.02, hy - hr * 1.05), pen.p(hr * 1.02, hy + hr * 0.45)], 180, 360,
                fill=PURPLE, outline=OUT, width=6 * S)
    pen.poly([(hr * 0.3, hy - hr * 0.33), (hr * 1.55, hy - hr * 0.25), (hr * 1.5, hy - hr * 0.1), (hr * 0.3, hy - hr * 0.2)], PURPLE, 6)
    pen.text(0, hy - hr * 0.65, "W", 50, GOLD, 4)
    ex, ey = hr * 0.35, hy + hr * 0.02
    for sx in (-1, 1):
        cx = sx * ex
        if blink:
            pen.line([(cx - 15, ey), (cx + 15, ey)], OUT, 7)
        else:
            pen.ell(cx, ey, 17, 20, "white", 4)
            pen.ell(cx + look[0] * 7, ey + look[1] * 7, 8, 8, OUT, 0)
        by = ey - 30
        if angry:
            pen.line([(cx - sx * 22, by - 10), (cx + sx * 18, by + 8)], (230, 230, 235), 12)
        else:
            pen.line([(cx - 22, by), (cx + 22, by - 5)], (230, 230, 235), 12)
    my = hy + hr * 0.62
    if mouth > 0.1:
        pen.ell(0, my, 26 + 8 * mouth, 6 + 26 * mouth, (110, 20, 30), 5)
    else:
        pen.line([(-22, my), (22, my)], OUT, 6)
    pen.ell(0, hy + hr * 0.3, 26, 22, (235, 150, 130), 5)  # nose
    for sx in (-1, 1):  # mustache
        pen.ell(sx * 42, hy + hr * 0.48 - mouth * 6, 52, 22, (235, 235, 240), 5)
    return img


def star(pen, x, y, r, c):
    pts = [(x + math.cos(-math.pi / 2 + i * math.pi / 5) * (r if i % 2 == 0 else r * 0.45),
            y + math.sin(-math.pi / 2 + i * math.pi / 5) * (r if i % 2 == 0 else r * 0.45)) for i in range(10)]
    pen.poly(pts, c, 4)


def place(frame, spr, x, y, sc=1.0, angle=0.0, pivot_up=0):
    """Paste sprite so its feet anchor lands at logical (x, y)."""
    if angle:
        spr = spr.rotate(angle, center=(AX * S, (AY - pivot_up) * S), resample=Image.BICUBIC)
    if sc != 1.0:
        spr = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
    frame.alpha_composite(spr, (int((x - AX * sc) * S), int((y - AY * sc) * S)))


# ---------------------------------------------------------------- backgrounds
PERIOD = 1080


def make_world():
    img = Image.new("RGB", (2 * PERIOD * S, H * S))
    d = ImageDraw.Draw(img)
    for y in range(0, 560 * S, 4):  # sky gradient
        k = y / (560 * S)
        d.rectangle([0, y, img.width, y + 4], fill=(int(90 + 90 * k), int(170 + 60 * k), int(250 - 10 * k)))
    pen = Pen(img)
    r = random.Random(3)
    for cx in range(0, 2 * PERIOD, 540):  # clouds
        for dx, dy, rr in ((0, 0, 60), (60, 10, 50), (-60, 12, 45), (25, -30, 50)):
            pen.ell(cx + 200 + dx, 180 + dy + (cx % 3) * 40, rr * 1.2, rr, "white", 0)
    # stands
    pen.rect(-20, 520, 2 * PERIOD + 20, 905, (60, 60, 75), 0)
    for i in range(8):
        pen.rect(-20, 540 + i * 45, 2 * PERIOD + 20, 544 + i * 45, (45, 45, 58), 0)
    cols = [(240, 80, 80), (250, 200, 60), (90, 160, 250), (255, 255, 255), (150, 90, 210), (255, 140, 60)]
    dots = [(r.uniform(0, PERIOD), 560 + row * 45 + r.uniform(-6, 6), r.choice(cols)) for row in range(8) for _ in range(34)]
    for x, y, c in dots:
        for off in (0, PERIOD):
            pen.ell(x + off, y, 13, 13, c, 0)
            pen.ell(x + off, y + 20, 15, 10, c, 0)
    pen.rect(-20, 860, 2 * PERIOD + 20, 905, PURPLE, 0)
    for off in (0, PERIOD):
        for x in range(60, PERIOD, 360):
            pen.text(x + off + 120, 883, "GO WAFFLES!", 30, GOLD, 0)
    # field
    for i, y in enumerate(range(905, H, 90)):
        pen.rect(-20, y, 2 * PERIOD + 20, y + 90, (70, 165, 70) if i % 2 else (80, 180, 78), 0)
    nums = ["30", "40", "50", "40", "30", "40"]
    for i in range(12):
        x = i * 180
        pen.poly([(x, 905), (x + 10, 905), (x - 250, H), (x - 262, H)], (245, 245, 245), 0)
        pen.text(x - 120, 1080, nums[i % 6], 54, (245, 245, 245), 0)
    return img


def world_view(world, offset):
    o = int((offset % PERIOD) * S)
    return world.crop((o, 0, o + W * S, H * S)).convert("RGBA")


# ---------------------------------------------------------------- frame composition
def ease(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def caption(frame, who, text):
    pen = Pen(frame)
    name, col = NAMES[who]
    words, lines, cur = text.split(), [], ""
    f = font(70)
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if f.getlength(trial) / S > 940 and cur:
            lines.append(cur); cur = w_
        else:
            cur = trial
    lines.append(cur)
    y0 = 1640
    nw = font(40).getlength(name) / S + 50
    pen.rect(540 - nw / 2, y0 - 70, 540 + nw / 2, y0 - 16, col, 5, 26)
    pen.text(540, y0 - 43, name, 40, "white", 0)
    for i, ln in enumerate(lines):
        pen.text(540, y0 + 45 + i * 88, ln, 70, "white", 9)


def burst(frame, x, y, text, sc, color=GOLD):
    pen = Pen(frame, x, y, sc)
    pts = [(math.cos(i * math.pi / 9) * (300 if i % 2 == 0 else 200), math.sin(i * math.pi / 9) * (180 if i % 2 == 0 else 120)) for i in range(18)]
    pen.poly(pts, color, 8)
    pen.text(0, 0, text, 110, "white", 10)


def yellow_flag(pen, x, y, ang):
    c, s_ = math.cos(ang), math.sin(ang)
    pts = [(-45, -35), (45, -35), (45, 35), (-45, 35)]
    pen.poly([(x + px * c - py * s_, y + px * s_ + py * c) for px, py in pts], (255, 220, 0), 6)
    pen.ell(x - 45 * c + 35 * s_, y - 45 * s_ - 35 * c, 14, 14, (255, 220, 0), 5)


def hotdog_stand(pen, x, messy):
    pen.rect(x, 1050, x + 470, 1480, (200, 60, 50), 7, 10)
    pen.rect(x + 20, 1030, x + 450, 1240, (90, 40, 35), 6, 8)
    for i in range(5):
        hx = x + 70 + i * 82
        pen.line([(hx, 1030), (hx, 1060)], OUT, 4)
        pen.ell(hx, 1095, 16, 36, (185, 75, 50), 4)
    pen.rect(x + 50, 770, x + 420, 870, (255, 245, 220), 7, 14)
    pen.text(x + 235, 820, "HOT DOGS", 62, RED, 0)
    pen.rect(x - 20, 1240, x + 490, 1280, (150, 95, 60), 6, 6)
    for i in range(6):  # awning
        c = RED if i % 2 == 0 else "white"
        pen.poly([(x - 30 + i * 88, 900), (x - 30 + (i + 1) * 88, 900), (x - 30 + (i + 1) * 88, 1000), (x - 30 + i * 88, 1000)], c, 5)
    for i in range(6):
        pen.ell(x + 14 + i * 88, 1000, 44, 26, RED if i % 2 == 0 else "white", 5)
    pen.rect(x - 30, 880, x + 500, 905, (120, 40, 40), 5)
    pen.rect(x + 120, 860, x + 140, 880, OUT, 0); pen.rect(x + 330, 860, x + 350, 880, OUT, 0)
    pen.rect(x + 60, 1265, x + 90, 1340, (250, 210, 30), 5, 8)  # mustard bottle
    if messy:
        pen.rect(x + 330, 1210, x + 400, 1240, RED, 5, 8)  # knocked-over ketchup
        for dx, dy, r in ((-40, 20, 40), (0, 60, 30), (60, 40, 50), (-90, 80, 26)):
            pen.ell(x + 330 + dx, 1280 + dy, r, r * 0.6, RED, 0)
        for dx, dy, r in ((-150, -200, 46), (-320, -300, 30), (-60, -330, 24)):
            pen.ell(x + 330 + dx, 1280 + dy, r, r * 0.7, (250, 210, 30), 0)


G = {}


def speaking(t):
    for key, st in G["ev"]:
        who = CFG["lines"][key][0]
        i = int((t - st) * FPS)
        e = G["mouth"][key]
        if 0 <= i < len(e):
            return who, key, e[i]
    return None, None, 0.0


def current_caption(t):
    for key, st in G["ev"]:
        if st - 0.05 <= t <= st + G["dur"][key] + 0.35:
            return CFG["lines"][key]
    return None


def blink_at(t, seed):
    return ((t + seed) % 3.3) < 0.12


def render(fi):
    t = fi / FPS
    who, key, amp = speaking(t)
    ctx = dict(who=who, key=key, amp=amp, m={k: (amp if who == k else 0.0) for k in NAMES}, world=G["world"],
               T=G["T"], dur=G["dur"], evt=G["evt"])
    frame = G["episode"].render_scene(t, ctx)
    if t < G["T"].get("captions_off", G["T"].get("E", 1e9)):
        cap = current_caption(t)
        if cap:
            caption(frame, *cap)
    return frame.convert("RGB").reduce(S).tobytes()


def init_worker(state, ep_name):
    import importlib
    G.update(state)
    G["episode"] = importlib.import_module(ep_name)
    CFG["lines"] = G["episode"].LINES
    G["world"] = make_world()


def main(ep, final):
    CFG["lines"] = ep.LINES
    CFG["out_dir"] = os.path.join(HERE, "build", ep.NAME)
    os.makedirs(CFG["out_dir"], exist_ok=True)
    clips = make_voices()
    dur = {k: len(v) / SR for k, v in clips.items()}
    ev, sfx, T = ep.build_timeline(dur)
    total = T["end"]
    wav = mix_audio(clips, ev, sfx, total)
    state = dict(ev=ev, T=T, dur=dur, mouth=mouth_envelopes(clips), evt={k: s for k, s in ev})
    nframes = int(total * FPS)
    print(f"duration {total:.1f}s, {nframes} frames", flush=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(ep.__file__)))
    if os.environ.get("PREVIEW"):
        init_worker(state, ep.__name__)
        for ts in map(float, os.environ["PREVIEW"].split(",")):
            Image.frombytes("RGB", (W, H), render(int(ts * FPS))).save(os.path.join(CFG["out_dir"], f"prev_{ts:05.1f}.png"))
        return
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                           final], stdin=subprocess.PIPE)
    with Pool(4, initializer=init_worker, initargs=(state, ep.__name__)) as pool:
        for i, buf in enumerate(pool.imap(render, range(nframes), chunksize=4)):
            ff.stdin.write(buf)
            if i % 150 == 0:
                print(f"frame {i}/{nframes}", flush=True)
    ff.stdin.close(); ff.wait()
    print("done", final)
