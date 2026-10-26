"""Render "Body Buddies" YouTube Shorts (1080x1920, < 20 s) with PIL + ffmpeg + gTTS.

Characters are drawn in a 2D cartoon style: thick ink outlines, cel shading,
rubber-hose arms and legs, and expressive faces with lip-sync.
The character layer is drawn at 2x and downsampled for smooth edges.

Usage: python3 make_video.py [slug ...]   (renders all episodes when no slug is given)
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from gtts import gTTS
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from episodes import EPISODES

W, H, FPS = 1080, 1920, 30
MAX_SECONDS = 19.5
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
FONT = os.path.join(HERE, "fonts", "Fredoka.ttf")
INTRO, GAP, OUTRO = 0.9, 0.2, 1.0
SR = 24000

# voice: (gTTS accent, pitch factor, tempo)
VOICES = {"kid": ("com", 1.28, 1.25), "organ": ("co.uk", 0.92, 1.25)}
NAMES = {"kid": "SAM"}

K = 2                              # supersampling factor of the character layer
STAGE_Y0, STAGE_Y1 = 280, 1400     # frame rows covered by the character layer
GROUND = 1300
KID_X, ORGAN_X = 230, 720
INK = (45, 30, 55)
OL = 6                             # outline width at 1x
SKIN = (255, 214, 175)
GLOVE = (255, 255, 255)

# Organ geometry lives on a 1400x1400 canvas. Faces: (x, y, scale) on that canvas.
FACES = {
    "heart": [(700, 600, 2.0)],
    "brain": [(700, 700, 2.0)],
    "lungs": [(410, 800, 1.35), (990, 800, 1.35)],
    "stomach": [(690, 720, 1.9)],
    "kidneys": [(400, 700, 1.25), (1000, 700, 1.25)],
}


def font(size, weight="Bold"):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_name(weight)
    return f


def darker(c, k=0.7):
    return tuple(int(v * k) for v in c[:3])


def blend(a, b, k):
    return tuple(int(x + (y - x) * k) for x, y in zip(a[:3], b[:3]))


def lighter(c, k=0.45):
    return tuple(int(v + (255 - v) * k) for v in c[:3])


# ---------------------------------------------------------------- audio
def synth(text, speaker, path):
    tld, pitch, tempo = VOICES[speaker]
    mp3 = path + ".mp3"
    gTTS(text, lang="en", tld=tld).save(mp3)
    # pitch shift via asetrate, then correct the speed with atempo
    tempo_fix = tempo / pitch
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af",
         f"asetrate={SR}*{pitch},aresample={SR},atempo={tempo_fix:.4f},"
         "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
         "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
         "-ac", "1", "-ar", str(SR), path], check=True)
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)


def build_audio(ep, tmp):
    clips = [synth(t, s, os.path.join(tmp, f"l{i}.wav")) for i, (s, t) in enumerate(ep["lines"])]
    total = INTRO + sum(len(c) / SR for c in clips) + GAP * (len(clips) - 1) + OUTRO
    if total > MAX_SECONDS:
        raise SystemExit(f"{ep['slug']}: {total:.1f}s is too long, shorten the dialogue")
    track = np.zeros(int(total * SR) + SR, dtype=np.float32)
    timeline, t = [], INTRO
    for (speaker, text), clip in zip(ep["lines"], clips):
        start = int(t * SR)
        track[start:start + len(clip)] += clip
        timeline.append((t, t + len(clip) / SR, speaker, text))
        t += len(clip) / SR + GAP
    track = track[: int(total * SR)]
    # "boing" for the organ landing at the end of the intro drop
    n, s0 = int(0.3 * SR), int(0.5 * SR)
    tt = np.arange(n) / SR
    track[s0:s0 + n] += 9000 * np.sin(2 * np.pi * (180 + 260 * np.sin(tt * 30) * np.exp(-tt * 8)) * tt) * np.exp(-tt * 10)
    track = np.clip(track / max(1, np.abs(track).max()) * 30000, -32767, 32767).astype(np.int16)
    wav = os.path.join(tmp, "mix.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(track.tobytes())
    hop = SR // FPS
    env = np.array([np.sqrt(np.mean(track[i:i + hop].astype(np.float32) ** 2))
                    for i in range(0, len(track), hop)])
    env = env / max(1, np.percentile(env, 95))
    return wav, total, timeline, np.clip(env, 0, 1)


# ---------------------------------------------------------------- 2x drawing helper
class Pen:
    """ImageDraw wrapper that takes 1x frame coordinates and draws on the 2x stage layer."""

    def __init__(self, img):
        self.img, self.d = img, ImageDraw.Draw(img, "RGBA")

    @staticmethod
    def p(x, y):
        return (x * K, (y - STAGE_Y0) * K)

    def box(self, b):
        return [*self.p(b[0], b[1]), *self.p(b[2], b[3])]

    def ellipse(self, b, fill=None, outline=None, width=OL):
        self.d.ellipse(self.box(b), fill=fill, outline=outline, width=int(width * K))

    def chord(self, b, a0, a1, fill=None, outline=None, width=OL):
        self.d.chord(self.box(b), a0, a1, fill=fill, outline=outline, width=int(width * K))

    def arc(self, b, a0, a1, fill, width=OL):
        self.d.arc(self.box(b), a0, a1, fill=fill, width=int(width * K))

    def rect(self, b, r, fill=None, outline=None, width=OL):
        self.d.rounded_rectangle(self.box(b), int(r * K), fill=fill, outline=outline, width=int(width * K))

    def line(self, pts, fill, width):
        pts = [self.p(*q) for q in pts]
        self.d.line(pts, fill=fill, width=int(width * K), joint="curve")
        r = width * K / 2
        for x, y in (pts[0], pts[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def paste(self, sprite, x, y):
        self.img.alpha_composite(sprite, (int(x * K), int((y - STAGE_Y0) * K)))


def circle(pen, x, y, r, fill, outline=INK, width=OL):
    pen.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline, width=width)


def hose(pen, p0, p1, bend, width, color):
    """Rubber-hose limb: a curved tube with an ink outline."""
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy) or 1
    cx, cy = mx - dy / ln * bend, my + dx / ln * bend
    pts = []
    for i in range(17):
        u = i / 16
        pts.append(((1 - u) ** 2 * p0[0] + 2 * u * (1 - u) * cx + u * u * p1[0],
                    (1 - u) ** 2 * p0[1] + 2 * u * (1 - u) * cy + u * u * p1[1]))
    pen.line(pts, INK, width + 2 * OL)
    pen.line(pts, color, width)


def arm(pen, shoulder, angle, length, color, side, hand=GLOVE, hand_r=28):
    a = math.radians(angle)
    hx, hy = shoulder[0] + length * math.cos(a), shoulder[1] + length * math.sin(a)
    hose(pen, shoulder, (hx, hy), 22 * side, 24, color)
    circle(pen, hx, hy, hand_r, hand)
    # thumb
    circle(pen, hx + 18 * math.cos(a - side * 1.6), hy + 18 * math.sin(a - side * 1.6), hand_r * 0.45, hand)
    return hx, hy


def shoe(pen, x, y, side, color):
    pen.ellipse([x - 38 + side * 18, y - 30, x + 38 + side * 18, y + 8], fill=color, outline=INK)
    pen.ellipse([x - 16 + side * 26, y - 22, x + 6 + side * 26, y - 12], fill=lighter(color, 0.6), width=0)


# ---------------------------------------------------------------- cel-shaded sprites
def cel(mask, color, highlights=(), shift=34):
    """Fill a mask with flat color, a hard shadow crescent, highlights and an ink outline."""
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    ring = mask.filter(ImageFilter.GaussianBlur(OL * K * 0.6)).point(lambda v: 255 if v > 6 else 0)
    out.paste(INK + (255,), (0, 0, *mask.size), ring)
    out.paste(tuple(color) + (255,), (0, 0, *mask.size), mask)
    moved = Image.new("L", mask.size, 0)
    moved.paste(mask, (-shift, -shift))
    shadow = ImageChops.subtract(mask, moved)
    out.paste(darker(color, 0.8) + (255,), (0, 0, *mask.size), shadow)
    if highlights:
        hl = Image.new("L", mask.size, 0)
        hd = ImageDraw.Draw(hl)
        for b in highlights:
            hd.ellipse(b, fill=255)
        out.paste(lighter(color, 0.6) + (255,), (0, 0, *mask.size), ImageChops.multiply(hl, mask))
    return out


def shape(draw_fn, size=1400):
    m = Image.new("L", (size, size), 0)
    draw_fn(ImageDraw.Draw(m))
    return m


def organ_parts(kind, color):
    """Return [(mask, color, highlights, is_main)] back-to-front plus a details painter."""
    S = 1400
    tube = lighter(color, 0.35)
    if kind == "heart":
        pts = []
        for i in range(400):
            a = 2 * math.pi * i / 400
            x = 16 * math.sin(a) ** 3
            y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
            pts.append((S / 2 + x * 34, S / 2 - y * 34 - 30))
        parts = [
            (shape(lambda d: d.rounded_rectangle([520, 110, 630, 420], 50, fill=255)), (90, 130, 230), [(540, 140, 580, 260)], False),
            (shape(lambda d: d.arc([660, 60, 1000, 420], 180, 360, fill=255, width=110)), color, [(700, 100, 780, 150)], False),
            (shape(lambda d: d.polygon(pts, fill=255)), color, [(330, 360, 520, 500), (300, 520, 360, 600)], True),
        ]
        details = lambda d: d.arc([560, 560, 1000, 1020], 200, 300, fill=darker(color, 0.78), width=14)
    elif kind == "brain":
        blobs = [(470, 520, 230), (700, 430, 250), (930, 520, 230), (420, 760, 210),
                 (700, 760, 280), (980, 760, 210), (560, 920, 180), (840, 920, 180)]
        parts = [
            (shape(lambda d: d.rounded_rectangle([630, 900, 770, 1230], 60, fill=255)), lighter(color, 0.2), [], False),
            (shape(lambda d: [d.ellipse([x - r, y - r, x + r, y + r], fill=255) for x, y, r in blobs]), color,
             [(400, 330, 560, 430), (620, 230, 720, 290)], True),
        ]

        def details(d):
            g = darker(color, 0.72)
            for x0, y0 in [(300, 560), (860, 470), (360, 880), (900, 900), (520, 320), (1000, 650)]:
                d.arc([x0, y0, x0 + 170, y0 + 110], 200, 340, fill=g, width=16)
            d.line([700, 200, 700, 340], fill=g, width=16)
    elif kind == "lungs":
        lobe_l = lambda d: d.rounded_rectangle([170, 420, 650, 1260], 230, fill=255)
        lobe_r = lambda d: d.rounded_rectangle([750, 420, 1230, 1260], 230, fill=255)
        parts = [
            (shape(lambda d: (d.rounded_rectangle([650, 90, 750, 540], 45, fill=255),
                              d.line([700, 520, 540, 640], fill=255, width=80),
                              d.line([700, 520, 860, 640], fill=255, width=80))), (235, 235, 245), [], False),
            (shape(lobe_l), color, [(270, 500, 400, 600)], True),
            (shape(lobe_r), color, [(850, 500, 980, 600)], True),
        ]

        def details(d):
            for y in range(150, 520, 70):
                d.line([660, y, 740, y], fill=(190, 190, 210), width=12)
    elif kind == "stomach":
        pts = []
        for i in range(400):
            a = 2 * math.pi * i / 400
            r = 1 + 0.18 * math.cos(2 * a + 0.6)
            pts.append((700 + 470 * r * math.cos(a), 760 + 380 * r * math.sin(a)))
        parts = [
            (shape(lambda d: d.rounded_rectangle([780, 80, 900, 460], 55, fill=255)), tube, [], False),
            (shape(lambda d: d.rounded_rectangle([200, 860, 340, 1230], 60, fill=255)), tube, [], False),
            (shape(lambda d: d.polygon(pts, fill=255)), color, [(380, 480, 560, 590)], True),
        ]

        def details(d):
            g = darker(color, 0.75)
            for y0 in (860, 950):
                d.arc([520, y0 - 140, 1000, y0], 20, 160, fill=g, width=14)
    elif kind == "kidneys":
        bean = []
        for i in range(400):
            a = 2 * math.pi * i / 400
            dent = 150 * math.exp(-(((a + math.pi) % (2 * math.pi)) - math.pi) ** 2 / 0.25)
            bean.append((420 + (230 - dent) * math.cos(a), 700 + 360 * math.sin(a)))
        mirror = [(S - x, y) for x, y in bean]
        parts = [
            (shape(lambda d: d.polygon(bean, fill=255)), color, [(290, 420, 400, 520)], True),
            (shape(lambda d: d.polygon(mirror, fill=255)), color, [(1000, 420, 1110, 520)], True),
        ]

        def details(d):
            pass
    return parts, details


def organ_sprite(kind, color):
    """Compose the cel-shaded organ once. Returns sprite, anchors and limb attachment points."""
    parts, details = organ_parts(kind, color)
    comp = Image.new("RGBA", (1400, 1400), (0, 0, 0, 0))
    main = Image.new("L", (1400, 1400), 0)
    for mask, col, hls, is_main in parts:
        comp.alpha_composite(cel(mask, col, hls))
        if is_main:
            main = ImageChops.lighter(main, mask)
    details(ImageDraw.Draw(comp))
    bb = comp.getbbox()
    mb = main.getbbox()
    # main body at most 480 px wide / 520 px tall on screen
    scale = min(520 * K / (mb[3] - mb[1]), 480 * K / (mb[2] - mb[0]))
    size = (int((bb[2] - bb[0]) * scale), int((bb[3] - bb[1]) * scale))
    sprite = comp.crop(bb).resize(size, Image.LANCZOS)
    m = np.array(main.crop(bb).resize(size, Image.BILINEAR)) > 128
    ys, xs = np.nonzero(m)
    top, bottom, left, right = ys.min(), ys.max(), xs.min(), xs.max()
    cx = (left + right) / 2
    row = int(top + 0.5 * (bottom - top))
    cols = np.nonzero(m[row])[0]
    shoulders = [(cols.min() + 14, row), (cols.max() - 14, row)]
    hips = []
    for hx in (cx - 0.17 * (right - left), cx + 0.17 * (right - left)):
        rows = np.nonzero(m[:, int(hx)])[0]
        hips.append((hx, (rows.max() if len(rows) else bottom) - 14))
    faces = [((x - bb[0]) * scale, (y - bb[1]) * scale, s * scale / K) for x, y, s in FACES[kind]]
    return {"img": sprite, "anchor": (cx, bottom), "shoulders": shoulders, "hips": hips,
            "faces": faces, "width": (right - left) / K}


def kid_sprites():
    """Cel-shaded body parts of Sam, drawn at 2x around a local origin (600, 600)."""
    S = 1200
    torso = cel(shape(lambda d: d.rounded_rectangle([400, 380, 800, 840], 120, fill=255), S),
                (255, 185, 60), [(440, 420, 520, 480)], shift=24)
    stripe = Image.new("L", (S, S), 0)
    ImageDraw.Draw(stripe).rectangle([0, 560, S, 620], fill=255)
    torso.paste((235, 90, 70, 255), (0, 0, S, S), ImageChops.multiply(stripe, torso.split()[3].point(lambda v: 255 if v > 250 else 0)))
    shorts = cel(shape(lambda d: d.rounded_rectangle([410, 760, 790, 900], 50, fill=255), S), (60, 90, 170), shift=20)

    def head_mask(d):
        d.ellipse([290, 180, 910, 760], fill=255)
        d.ellipse([240, 430, 360, 580], fill=255)
        d.ellipse([840, 430, 960, 580], fill=255)
    head = cel(shape(head_mask, S), SKIN, [(380, 240, 520, 320)], shift=26)

    def hair_mask(d):
        d.chord([270, 100, 930, 560], 180, 360, fill=255)
        for x in range(320, 900, 110):  # spiky top
            d.polygon([(x - 70, 260), (x + 20, 40 + (x % 3) * 30), (x + 70, 260)], fill=255)
        for x in range(330, 880, 90):   # fringe
            d.polygon([(x, 320), (x + 90, 320), (x + 60, 400)], fill=255)
    hair = cel(shape(hair_mask, S), (110, 65, 40), [(420, 170, 560, 230)], shift=22)
    return {"torso": torso, "shorts": shorts, "head": head, "hair": hair, "origin": 600}


# ---------------------------------------------------------------- faces
def draw_face(pen, cx, cy, s, mouth, mode, look, brow, iris, body):
    """mode: 'open' | 'blink' | 'happy'."""
    ow = max(3, OL * s)
    for side in (-1, 1):
        ex = cx + side * 95 * s
        if mode == "open":
            pen.ellipse([ex - 36 * s, cy - 46 * s, ex + 36 * s, cy + 46 * s], fill="white", outline=INK, width=ow)
            ix, iy = ex + look * s, cy + 6 * s
            circle(pen, ix, iy, 24 * s, iris, outline=None, width=0)
            circle(pen, ix, iy, 13 * s, INK, outline=None, width=0)
            circle(pen, ix - 9 * s, iy - 11 * s, 8 * s, "white", outline=None, width=0)
            circle(pen, ix + 8 * s, iy + 9 * s, 4 * s, "white", outline=None, width=0)
        elif mode == "blink":
            pen.arc([ex - 34 * s, cy - 18 * s, ex + 34 * s, cy + 18 * s], 10, 170, INK, ow)
        else:  # happy ^ ^
            pen.arc([ex - 34 * s, cy - 10 * s, ex + 34 * s, cy + 40 * s], 200, 340, INK, ow * 1.2)
        by = cy - (66 + 14 * brow) * s
        pen.arc([ex - 34 * s, by, ex + 34 * s, by + 40 * s], 210 if side < 0 else 220, 320 if side < 0 else 330, INK, ow)
        pen.ellipse([ex - 34 * s + side * 20 * s, cy + 52 * s, ex + 34 * s + side * 20 * s, cy + 80 * s],
                    fill=blend(body, (255, 110, 140), 0.45), width=0)
    my = cy + 92 * s
    if mouth < 0.08 or mode == "happy":
        w = 44 * s if mode != "happy" else 56 * s
        pen.chord([cx - w, my - 30 * s, cx + w, my + 26 * s], 10, 170, fill=(120, 25, 45) if mode == "happy" else None,
                  outline=INK, width=ow) if mode == "happy" else pen.arc([cx - w, my - 30 * s, cx + w, my + 22 * s], 15, 165, INK, ow)
        return
    w, h = (40 + 16 * mouth) * s, (18 + 74 * mouth) * s
    box = [cx - w, my - h, cx + w, my + h]
    pen.chord(box, 0, 180, fill=(120, 25, 45))
    pen.rect([cx - w * 0.7, my, cx + w * 0.7, my + min(14 * s, h * 0.3)], 4 * s, fill="white")
    if h > 30 * s:
        pen.chord([cx - w * 0.5, my + h * 0.55, cx + w * 0.5, my + h * 1.25], 180, 360, fill=(240, 110, 130))
    pen.chord(box, 0, 180, outline=INK, width=ow)


# ---------------------------------------------------------------- scene
def background(top, bottom, accent):
    t = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top)[None, None] * (1 - t) + np.array(bottom)[None, None] * t)
    img = Image.fromarray(np.repeat(arr, W, axis=1).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(7)
    for _ in range(11):  # floating blood-cell donuts on the wall
        x, y, r = rng.integers(0, W), rng.integers(280, 1150), rng.integers(28, 70)
        d.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=accent + (40,))
        d.ellipse([x - r * 0.45, y - r * 0.32, x + r * 0.45, y + r * 0.32], fill=accent + (30,))
    for _ in range(7):  # medical crosses
        x, y, r = rng.integers(40, W - 40), rng.integers(300, 1150), rng.integers(14, 26)
        d.rectangle([x - r, y - r / 3, x + r, y + r / 3], fill=(255, 255, 255, 110))
        d.rectangle([x - r / 3, y - r, x + r / 3, y + r], fill=(255, 255, 255, 110))
    floor_top = 1240
    d.rectangle([0, floor_top, W, H], fill=darker(top, 0.9) + (255,))
    d.rectangle([0, floor_top, W, floor_top + 10], fill=darker(top, 0.75) + (255,))
    for i in range(1, 5):
        d.line([0, floor_top + i * i * 22, W, floor_top + i * i * 22], fill=darker(top, 0.85) + (255,), width=4)
    d.ellipse([ORGAN_X - 330, GROUND - 60, ORGAN_X + 330, GROUND + 60], fill=(255, 255, 255, 70))
    return img


def wrap(text, f, width, d):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=f) <= width:
            cur = test
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines


def outlined(d, xy, text, f, fill, stroke=INK, sw=8, anchor="mm"):
    d.text(xy, text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)


def heartbeat(t):
    p = t % 0.85
    return math.exp(-(p / 0.05) ** 2) + 0.6 * math.exp(-((p - 0.2) / 0.05) ** 2)


# ---------------------------------------------------------------- render
def render(ep, idx):
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav, total, timeline, env = build_audio(ep, tmp)
        color = ep["color"]
        bg = background(*ep["bg"], darker(color, 0.95))
        organ = organ_sprite(ep["organ"], color)
        kid = kid_sprites()
        limb = darker(color, 0.85)
        organ_name = ep["title"].replace("The ", "").upper()
        nframes = int(total * FPS)
        out = os.path.join(OUT, f"body-buddies-{ep['slug']}.mp4")
        ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
            stdin=subprocess.PIPE)
        f_title, f_ep, f_sub, f_name = font(96), font(48), font(58, "SemiBold"), font(40)
        size = 54
        while ImageDraw.Draw(bg).textlength(ep["fact"], font=font(size)) > 820:
            size -= 2
        f_fact = font(size)
        smooth = 0.0
        for fi in range(nframes):
            t = fi / FPS
            cur = next((x for x in timeline if x[0] <= t < x[1]), None)
            speaker = cur[2] if cur else None
            amp = env[min(fi, len(env) - 1)]
            smooth += (amp - smooth) * 0.35
            outro = t > total - OUTRO
            stage = Image.new("RGBA", (W * K, (STAGE_Y1 - STAGE_Y0) * K), (0, 0, 0, 0))
            pen = Pen(stage)

            # ---------------- organ: drop in, squash on landing, idle/talk bounce
            drop = 0.0
            if t < 0.5:
                drop = -900 * (1 - t / 0.5) ** 2
                sy = 1.12
            elif t < 1.1:
                q = (t - 0.5) / 0.6
                sy = 1 - 0.22 * math.exp(-q * 4) * math.cos(q * 10)
            else:
                talk = smooth if speaker == "organ" else 0
                sy = 1 + 0.015 * math.sin(t * 3) + 0.05 * talk * math.sin(t * 14)
            sx = 2 - sy
            if ep["organ"] == "heart":
                b = 0.045 * heartbeat(t)
                sx, sy = sx + b, sy + b
            elif ep["organ"] == "lungs":
                b = 0.035 * math.sin(t * 2.4)
                sx += b
            ax, ay = organ["anchor"]
            hip_y = GROUND - 150 + drop
            img = organ["img"]
            sp = img.resize((int(img.width * sx), int(img.height * sy)), Image.BILINEAR)

            def to_screen(px, py):
                return ORGAN_X + (px - ax) * sx / K, hip_y + (py - ay) * sy / K

            # shadow + legs
            sh = 1 - min(1, -drop / 900)
            step = 8 * math.sin(t * 6) if speaker == "organ" else 0
            for i, (hx, hy) in enumerate(organ["hips"]):
                side = -1 if i == 0 else 1
                h0 = to_screen(hx, hy)
                foot = (h0[0] + side * 26, min(GROUND - 10, h0[1] + 150) - (abs(step) if i == 0 else 0))
                hose(pen, h0, foot, -12 * side, 22, limb)
                shoe(pen, foot[0], foot[1] + 8, side, (220, 60, 60))
            pen.paste(sp, ORGAN_X - ax * sx / K, hip_y - ay * sy / K)

            # arms: left arm gestures toward Sam while talking, right arm waves in the outro
            wob = math.sin(t * 2)
            la, ra = 120 - 6 * wob, 60 + 6 * wob
            if speaker == "organ":
                la = 195 + 28 * math.sin(t * 5)
                ra = 40 + 15 * math.sin(t * 3)
            if outro or 0.9 < t < 1.6:
                ra = -70 + 25 * math.sin(t * 14)
            (lx, ly), (rx, ry) = [to_screen(*s) for s in organ["shoulders"]]
            arm(pen, (lx, ly), la, 130, limb, -1)
            arm(pen, (rx, ry), ra, 130, limb, 1)

            # face(s)
            blink = (t % 3.1) < 0.12
            mode = "happy" if outro else ("blink" if blink else "open")
            look = -12 if speaker == "kid" else (-5 if speaker == "organ" else 0)
            for fx, fy, fs in organ["faces"]:
                x, y = to_screen(fx, fy)
                draw_face(pen, x, y, fs, amp if speaker == "organ" else 0, mode, look,
                          smooth if speaker == "organ" else 0, (90, 50, 40), color)

            # ---------------- Sam the kid
            bob = 6 * math.sin(t * 6) if speaker == "kid" else 2 * math.sin(t * 2.5)
            o = kid["origin"] / K
            base_y = GROUND - 260 + bob   # local origin of kid sprites
            for side in (-1, 1):
                hip = (KID_X + side * 45, GROUND - 120 + bob)
                foot = (KID_X + side * 52, GROUND - 14)
                hose(pen, hip, foot, 0, 40, SKIN)
                pen.line([(KID_X + side * 50, GROUND - 40), (KID_X + side * 52, GROUND - 24)], (255, 255, 255), 30)
                shoe(pen, foot[0], foot[1] + 6, side, (230, 70, 70))
            pen.paste(kid["shorts"], KID_X - o, base_y - o)
            pen.paste(kid["torso"], KID_X - o, base_y - o)
            la_k, ra_k = 115 + 5 * wob, 65 - 5 * wob
            if speaker == "kid":
                ra_k = -15 + 30 * math.sin(t * 5)
            if t < 1.3 or outro:
                ra_k = -75 + 25 * math.sin(t * 14)
            for side, ang in ((-1, la_k), (1, ra_k)):
                sh_pt = (KID_X + side * 88, base_y - o + 220)
                arm(pen, sh_pt, ang, 120, SKIN, side, hand=SKIN, hand_r=24)
                circle(pen, sh_pt[0], sh_pt[1] + 6, 30, (255, 185, 60))
            head_y = base_y - o
            pen.paste(kid["head"], KID_X - o, head_y - 100)
            pen.paste(kid["hair"], KID_X - o, head_y - 100)
            kid_blink = (t % 3.7) < 0.12
            kmode = "happy" if outro else ("blink" if kid_blink else "open")
            draw_face(pen, KID_X + 6, head_y + 150, 0.78, amp if speaker == "kid" else 0, kmode,
                      12 if speaker == "organ" else 5, smooth if speaker == "kid" else 0, (70, 130, 210), SKIN)

            frame = bg.copy()
            d = ImageDraw.Draw(frame, "RGBA")
            d.ellipse([ORGAN_X - 190 * sh, GROUND - 22 * sh, ORGAN_X + 190 * sh, GROUND + 22 * sh], fill=(0, 0, 0, 45))
            d.ellipse([KID_X - 120, GROUND - 18, KID_X + 120, GROUND + 18], fill=(0, 0, 0, 45))
            small = stage.reduce(K)
            frame.paste(small, (0, STAGE_Y0), small)

            # ---------------- title
            d.rounded_rectangle([W / 2 - 170, 70, W / 2 + 170, 130], 30, fill=INK + (255,))
            d.text((W / 2, 100), "BODY BUDDIES", font=f_ep, fill=(255, 220, 80), anchor="mm")
            outlined(d, (W / 2, 205), f"Ep {idx}: {ep['title']}", f_title, "white", sw=10)

            # ---------------- speech bubble
            if cur:
                pop = min(1, (t - cur[0]) / 0.12)
                bx0, by0, bx1 = 60, 1400 + 20 * (1 - pop), W - 60
                lines = wrap(cur[3], f_sub, bx1 - bx0 - 90, d)
                by1 = by0 + 80 + 72 * len(lines)
                col = color if speaker == "organ" else (60, 140, 240)
                tip_x = ORGAN_X if speaker == "organ" else KID_X + 40
                d.polygon([(tip_x - 45, by0 + 10), (tip_x + 45, by0 + 10), (tip_x + 10, by0 - 70)], fill=INK)
                d.rounded_rectangle([bx0, by0, bx1, by1], 46, fill=(255, 255, 255, 250), outline=INK, width=8)
                d.polygon([(tip_x - 34, by0 + 9), (tip_x + 34, by0 + 9), (tip_x + 9, by0 - 56)], fill="white")
                tag = NAMES.get(speaker, organ_name)
                tw = d.textlength(tag, font=f_name) + 56
                d.rounded_rectangle([bx0 + 50, by0 - 32, bx0 + 50 + tw, by0 + 30], 30, fill=col, outline=INK, width=6)
                d.text((bx0 + 50 + tw / 2, by0 - 1), tag, font=f_name, fill="white", anchor="mm")
                for li, line in enumerate(lines):
                    d.text((W / 2, by0 + 80 + 72 * li), line, font=f_sub, fill=INK, anchor="mm")
            elif outro:
                outlined(d, (W / 2, 1500), "Follow for the next organ!", font(64), (255, 220, 80), sw=9)

            # ---------------- fun fact card
            if t > timeline[3][0]:
                k = min(1, (t - timeline[3][0]) / 0.25)
                y0 = 1690 + 60 * (1 - k) ** 2
                d.rounded_rectangle([90, y0, W - 90, y0 + 150], 40, fill=(255, 255, 255, 235), outline=INK, width=7)
                d.rounded_rectangle([W / 2 - 130, y0 - 28, W / 2 + 130, y0 + 28], 28, fill=(255, 210, 60), outline=INK, width=6)
                d.text((W / 2, y0), "FUN FACT", font=f_name, fill=INK, anchor="mm")
                d.text((W / 2, y0 + 88), ep["fact"], font=f_fact, fill=darker(color, 0.8), anchor="mm")

            ff.stdin.write(frame.tobytes())
        ff.stdin.close()
        ff.wait()
        print(f"{out}  ({total:.1f}s)")


if __name__ == "__main__":
    wanted = set(sys.argv[1:])
    for i, ep in enumerate(EPISODES, 1):
        if not wanted or ep["slug"] in wanted:
            render(ep, i)
