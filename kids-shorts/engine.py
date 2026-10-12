"""Kids' sing-along Shorts engine: original songs -> sung audio + vertical 1080x1920 video under 60 seconds."""
import json, math, os, random, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "nfl-short"))
from toon import Pen, S, OUT, GOLD, font, star, ease  # noqa: E402
import animals as A  # noqa: E402
from autotune import psola  # noqa: E402

SR, W, H, FPS = 44100, 1080, 1920, 30
CACHE = os.path.join(HERE, "build", "tts")
os.makedirs(CACHE, exist_ok=True)
rng = np.random.default_rng(5)


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- song structure
def song_timeline(cfg):
    beat = 60 / cfg["bpm"]; bar = 4 * beat
    intro = bar
    words, verses = [], []
    for vi, v in enumerate(cfg["verses"]):
        start = intro + vi * 8 * bar
        key = cfg["key"] + (1 if vi == len(cfg["verses"]) - 1 else 0)
        verses.append(dict(index=vi, who=v["who"], start=start, end=start + 8 * bar, key=key))
        hook = v.get("hook", cfg["hook"])
        hook = hook if isinstance(hook, (list, tuple)) else (hook,) * 3
        for li in range(3):
            b = li * 8
            ws = [v["lead"][0], v["lead"][1], hook[0], hook[1], hook[2], hook[0], hook[1], hook[2]]
            for wd, d, n in zip(ws, cfg["rhythm"], cfg["lines"][li]):
                words.append(dict(text=wd, start=start + b * beat, dur=d * beat * 0.95, midi=n + key, verse=vi, line=li, hook=wd in hook))
                b += d
        b = 24
        last = v["last"]
        seq = [(v["lead"][0], 1), (v["lead"][1], 1)]
        for i, wd in enumerate(last):
            seq.append((wd, 1 if i < len(last) - 1 else max(1, 5 - (len(last) - 1))))
        notes = [cfg["lines"][0][0], cfg["lines"][0][0]] + cfg["last_notes"][:len(last) - 1] + [cfg["last_notes"][-1]]
        for (wd, d), n in zip(seq, notes):
            words.append(dict(text=wd, start=start + b * beat, dur=d * beat * 0.95, midi=n + key, verse=vi, line=3, hook=False))
            b += d
    outro = intro + len(cfg["verses"]) * 8 * bar
    return dict(words=words, verses=verses, beat=beat, bar=bar, intro_end=intro, outro_start=outro, total=outro + bar + 0.6)


# ---------------------------------------------------------------- instruments
def env_ad(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def kick(heavy=False):
    n = int(0.4 * SR); t = np.arange(n) / SR
    return (1.1 if heavy else 0.9) * np.sin(2 * np.pi * (45 * t + 70 * (1 - np.exp(-t * 30)) / 30)) * np.exp(-t * (6 if heavy else 9))


def snare():
    n = int(0.2 * SR); t = np.arange(n) / SR
    return 0.42 * (rng.standard_normal(n) * np.exp(-t * 22) + 0.5 * np.sin(2 * np.pi * 200 * t) * np.exp(-t * 25))


def clap():
    n = int(0.18 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n) * (np.exp(-t * 30) + 0.6 * np.exp(-np.abs(t - 0.012) * 300))
    return 0.35 * np.convolve(x, np.ones(3) / 3, "same")


def hat():
    n = int(0.05 * SR); x = rng.standard_normal(n)
    return 0.16 * (x - np.convolve(x, np.ones(4) / 4, "same")) * np.exp(-np.arange(n) / SR * 70)


def lead_tone(kind, f, dur):
    n = int(max(dur, 0.2) * SR); t = np.arange(n) / SR
    if kind == "marimba":
        return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 18)) * env_ad(n, 0.003, 0.35)
    if kind == "glock":
        return (np.sin(2 * np.pi * f * 2 * t) + 0.3 * np.sin(2 * np.pi * f * 5.4 * t)) * env_ad(n, 0.002, 0.5) * 0.7
    if kind == "clarinet":
        x = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 3, 5, 7))
        return 0.7 * x * np.minimum(1, t / 0.03) * np.minimum(1, (dur - t) / 0.05).clip(0)
    if kind == "brass":
        x = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 8))
        return 0.55 * x * np.minimum(1, t / 0.02) * np.minimum(1, (dur - t) / 0.05).clip(0)
    x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t)
    return x * env_ad(n, 0.003, 0.3)


def bass(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return 0.55 * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.minimum(1, t / 0.01) * np.minimum(1, (dur - t) / 0.05)


def pluck(freqs, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * t) for f in freqs)
    return 0.11 * np.convolve(x, np.ones(6) / 6, "same") * env_ad(n, 0.003, 0.12)


def sfx(kind):
    if kind == "ribbit":
        n = int(0.45 * SR); t = np.arange(n) / SR
        return 0.3 * np.sign(np.sin(2 * np.pi * (180 - 60 * t) * t)) * (np.sin(2 * np.pi * 22 * t) > 0) * np.exp(-t * 5)
    if kind == "quack":
        n = int(0.3 * SR); t = np.arange(n) / SR
        f = 520 - 300 * t
        x = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 2, 3, 4, 5))
        return 0.35 * x * np.exp(-t * 7) * np.minimum(1, t / 0.01)
    if kind == "stomp":
        n = int(0.5 * SR); t = np.arange(n) / SR
        return 0.9 * np.sin(2 * np.pi * (38 * t + 40 * (1 - np.exp(-t * 20)) / 20)) * np.exp(-t * 6)
    if kind == "toot":
        n = int(0.5 * SR); t = np.arange(n) / SR
        f = 300 + 250 * np.minimum(1, t / 0.15)
        x = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in range(1, 9))
        return 0.25 * x * np.minimum(1, t / 0.03) * np.exp(-np.maximum(0, t - 0.3) * 12)
    if kind == "slide":
        n = int(0.5 * SR); t = np.arange(n) / SR
        f = 500 + 900 * t / 0.5
        return 0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / 0.02) * np.minimum(1, (0.5 - t) / 0.05)
    return np.zeros(10)


def add(buf, x, t):
    i = int(t * SR)
    if 0 <= i < len(buf):
        buf[i:i + len(x)] += x[: len(buf) - i]


# ---------------------------------------------------------------- vocals
def tts(word, tld):
    from gtts import gTTS
    key = "".join(c for c in word.lower() if c.isalnum())
    wav = os.path.join(CACHE, f"{key}_{tld}.wav")
    if not os.path.exists(wav):
        mp3 = wav[:-4] + ".mp3"
        gTTS(word.strip(",!?"), lang="en", tld=tld).save(mp3)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-af",
                        "silenceremove=start_periods=1:start_threshold=-40dB,areverse,silenceremove=start_periods=1:start_threshold=-40dB,areverse",
                        "-ac", "1", "-ar", "24000", wav], check=True)
    with wave.open(wav) as f:
        return np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(float) / 32768


_SUNG = {}


def sung(word, midi, dur, tld):
    k = (word, midi, round(dur, 3), tld)
    if k not in _SUNG:
        y = psola(tts(word, tld), 24000, midi_hz(midi), dur)
        idx = np.linspace(0, len(y) - 1, int(len(y) * SR / 24000))
        _SUNG[k] = np.interp(idx, np.arange(len(y)), y)
    return _SUNG[k]


def build_audio(cfg, T, path):
    n = int(T["total"] * SR)
    drums, bassb, chords, lead, vox, fx = (np.zeros(n) for _ in range(6))
    beat, bar = T["beat"], T["bar"]
    nbars = int(round(T["outro_start"] / bar)) + 1
    heavy = cfg.get("heavy", False)
    for b in range(nbars):
        t = b * bar
        vi = int((t - T["intro_end"]) // (8 * bar)) if t >= T["intro_end"] else -1
        key = T["verses"][vi]["key"] if 0 <= vi < len(T["verses"]) else cfg["key"]
        root, q = cfg["chords"][b % len(cfg["chords"])]
        root += key
        tones = [midi_hz(root + 12), midi_hz(root + 12 + (3 if q == "min" else 4)), midi_hz(root + 19)]
        for k in range(4):
            if k in (0, 2):
                add(drums, kick(heavy), t + k * beat)
            else:
                add(drums, clap(), t + k * beat); add(drums, snare() * 0.6, t + k * beat)
            add(drums, hat(), t + k * beat + beat / 2)
            add(bassb, bass(midi_hz(root - 12 + (7 if k == 2 else 0)), beat * 0.9), t + k * beat)
            add(chords, pluck(tones, beat * 0.45), t + k * beat + beat / 2)
    # intro + outro hooks on the lead instrument
    for start in (0.0, T["outro_start"]):
        bb = 0
        for d, m in zip(cfg["rhythm"], cfg["lines"][0]):
            add(lead, lead_tone(cfg["lead"], midi_hz(m + cfg["key"]), d * beat) * 0.5, start + bb * beat); bb += d
    add(fx, sfx(cfg["sfx"]), 0.05)
    for wd in T["words"]:
        add(lead, lead_tone(cfg["lead"], midi_hz(wd["midi"]), wd["dur"]) * 0.3, wd["start"])
        add(vox, sung(wd["text"], wd["midi"], wd["dur"], "us") * 0.65, wd["start"])
        add(vox, sung(wd["text"], wd["midi"], wd["dur"], "com.au") * 0.4, wd["start"] + 0.015)
    for v in T["verses"]:
        for li in range(3):
            add(fx, sfx(cfg["sfx"]), v["start"] + (li * 8 + 6) * beat + 0.05)
    yay = psola(tts("Yay!", "us"), 24000, midi_hz(72 + cfg["key"]), 0.9)
    yay = np.interp(np.linspace(0, len(yay) - 1, int(len(yay) * SR / 24000)), np.arange(len(yay)), yay)
    add(vox, yay * 0.7, T["outro_start"] + beat * 2)
    d = int(0.16 * SR)
    vox[d:] += vox[:-d] * 0.15
    mix = drums * 0.5 + bassb * 0.5 + chords * 0.6 + lead * 0.55 + vox * 0.95 + fx * 0.6
    fade = int(0.6 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix * 1.15) * 0.9
    st = np.stack([mix, np.roll(mix, 25)], 1)
    with wave.open(path, "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((st * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- scenes (vertical)
GROUND_Y = 1000


def _grad(img, y0, y1, c0, c1):
    d = ImageDraw.Draw(img)
    for y in range(y0 * S, y1 * S, 4):
        k = (y - y0 * S) / max(1, (y1 - y0) * S)
        d.rectangle([0, y, img.width, y + 4], fill=tuple(int(a + (b - a) * k) for a, b in zip(c0, c1)))


def scene_bg(name):
    img = Image.new("RGB", (W * S, H * S))
    pen = Pen(img)
    r = random.Random(3)
    if name == "pond":
        _grad(img, 0, GROUND_Y, (110, 200, 255), (200, 240, 255))
        for x, rr in ((100, 380), (650, 460)):
            pen.ell(x, GROUND_Y + 40, rr, 220, (120, 200, 110), 0)
        pen.rect(-10, GROUND_Y, W + 10, H, (80, 160, 220), 0)
        for i in range(10):
            y = GROUND_Y + 60 + i * 85
            pen.line([((i * 173) % W, y), ((i * 173) % W + 90, y)], (130, 195, 240), 5)
        for x in (40, 1040):
            pen.line([(x, H), (x + 15, GROUND_Y - 160)], (70, 130, 60), 10)
            pen.ell(x + 15, GROUND_Y - 190, 14, 45, (130, 80, 40), 4)
        for x, y, rr in ((200, 1300, 150), (540, 1255, 230), (880, 1300, 150)):
            pen.ell(x, y, rr, rr * 0.3, (60, 150, 70), 6)
            pen.poly([(x, y), (x + rr * 0.9, y - rr * 0.1), (x + rr * 0.9, y + rr * 0.1)], (80, 160, 220), 0)
    elif name == "farm":
        _grad(img, 0, GROUND_Y, (120, 205, 255), (210, 240, 255))
        pen.rect(-10, GROUND_Y, W + 10, H, (120, 200, 90), 0)
        pen.rect(60, 640, 360, GROUND_Y + 20, (210, 60, 50), 7, 4)  # barn
        pen.poly([(40, 650), (210, 500), (380, 650)], (170, 40, 40), 7)
        pen.rect(160, 800, 260, GROUND_Y + 20, (250, 240, 230), 6, 4)
        pen.line([(160, 800), (260, GROUND_Y + 20)], (210, 60, 50), 6); pen.line([(260, 800), (160, GROUND_Y + 20)], (210, 60, 50), 6)
        for x in range(380, W + 40, 90):  # fence
            pen.rect(x, 880, x + 20, GROUND_Y + 30, (250, 245, 235), 4, 3)
        pen.rect(380, 910, W + 10, 930, (250, 245, 235), 4); pen.rect(380, 960, W + 10, 980, (250, 245, 235), 4)
        pen.ell(540, 1330, 470, 150, (90, 170, 230), 7)
        for _ in range(30):
            x, y = r.uniform(0, W), r.uniform(GROUND_Y + 30, H)
            pen.ell(x, y, 8, 8, r.choice([(255, 255, 255), (255, 220, 80), (250, 150, 190)]), 0)
    elif name == "jungle":
        _grad(img, 0, GROUND_Y, (130, 210, 250), (215, 245, 230))
        pen.poly([(380, GROUND_Y), (560, 560), (700, 560), (880, GROUND_Y)], (150, 110, 90), 7)  # friendly volcano
        pen.poly([(560, 560), (700, 560), (680, 610), (580, 610)], (255, 140, 60), 0)
        for sx in (-1, 1):
            pen.ell(630 + sx * 50, 760, 14, 18, OUT, 0)
        pen.d.arc([pen.p(570, 760), pen.p(690, 840)], 20, 160, fill=OUT, width=7 * S)
        pen.rect(-10, GROUND_Y, W + 10, H, (140, 200, 100), 0)
        for x in (90, 990):
            pen.line([(x, GROUND_Y + 40), (x + 30, 520)], (150, 100, 60), 26)
            for a in range(6):
                ang = math.pi * (1.05 + a * 0.18)
                pen.poly([(x + 30, 520), (x + 30 + math.cos(ang) * 200, 520 + math.sin(ang) * 80 + 60),
                          (x + 30 + math.cos(ang + 0.15) * 180, 520 + math.sin(ang + 0.15) * 80 + 80)], (60, 160, 70), 5)
        for _ in range(16):
            x, y = r.uniform(0, W), r.uniform(GROUND_Y + 60, H)
            pen.ell(x, y, 60, 20, (100, 170, 80), 0)
    elif name == "savanna":
        _grad(img, 0, GROUND_Y, (255, 170, 90), (255, 230, 160))
        pen.ell(780, 360, 150, 150, (255, 240, 170), 0)
        for x, s in ((180, 1.0), (930, 0.8)):
            pen.line([(x, GROUND_Y + 20), (x, GROUND_Y - 260 * s)], (110, 70, 40), 24 * s)
            pen.ell(x, GROUND_Y - 290 * s, 220 * s, 60 * s, (90, 130, 50), 6)
        pen.rect(-10, GROUND_Y, W + 10, H, (230, 200, 110), 0)
        pen.ell(540, 1330, 470, 150, (100, 170, 220), 7)
        for _ in range(60):
            x, y = r.uniform(0, W), r.uniform(GROUND_Y + 20, H)
            pen.line([(x, y), (x + 6, y - 26)], (200, 170, 80), 4)
    elif name == "snow":
        _grad(img, 0, GROUND_Y, (150, 205, 245), (225, 240, 255))
        for x, h, c in ((150, 420, (235, 245, 255)), (600, 520, (220, 235, 250)), (1000, 380, (235, 245, 255))):
            pen.poly([(x - 330, GROUND_Y), (x, GROUND_Y - h), (x + 330, GROUND_Y)], c, 6)
        pen.d.chord([pen.p(720, 760), pen.p(1040, GROUND_Y + 140)], 180, 360, fill=(250, 252, 255), outline=OUT, width=6 * S)  # igloo
        pen.d.chord([pen.p(830, 880), pen.p(930, GROUND_Y + 60)], 180, 360, fill=(70, 90, 130), outline=OUT, width=5 * S)
        pen.rect(-10, GROUND_Y, W + 10, H, (235, 245, 255), 0)
        pen.ell(540, 1330, 470, 150, (190, 225, 245), 6)
        pen.line([(200, 1290), (420, 1300)], "white", 8)
    return img


def scene_dynamic(frame, name, t, pulse):
    pen = Pen(frame)
    if name in ("pond", "farm", "jungle"):
        x, y = 900, 170
        for i in range(12):
            a = i * math.pi / 6 + t * 0.4
            pen.line([(x + math.cos(a) * 100, y + math.sin(a) * 100), (x + math.cos(a) * 135, y + math.sin(a) * 135)], (255, 200, 40), 11)
        r = 80 + 6 * pulse
        pen.ell(x, y, r, r, (255, 220, 60), 7)
        for sx in (-1, 1):
            pen.ell(x + sx * 26, y - 12, 8, 12, OUT, 0)
        pen.d.arc([pen.p(x - 34, y - 16), pen.p(x + 34, y + 34)], 20, 160, fill=OUT, width=6 * S)
    for i, (x0, y, s) in enumerate(((100, 140, 0.9), (500, 90, 1.1))):
        if name == "savanna":
            break
        x = (x0 + t * 25 * (i + 1)) % (W + 300) - 150
        for dx, dy, rr in ((0, 0, 55), (60, 12, 45), (-60, 14, 40), (22, -28, 48)):
            pen.ell(x + dx * s, y + dy * s, rr * 1.2 * s, rr * s, "white", 0)
    if name == "jungle":
        for i in range(3):
            u = (t * 0.3 + i / 3) % 1
            pen.ell(630 + 30 * math.sin(t + i), 540 - u * 300, 40 + u * 50, 30 + u * 40, (235, 235, 240), 0)
    if name == "snow":
        r = random.Random(2)
        for i in range(60):
            x0, sp = r.uniform(0, W), r.uniform(80, 160)
            y = (r.uniform(0, H) + t * sp) % H
            pen.ell((x0 + 25 * math.sin(t + i)) % W, y, 7, 7, "white", 0)
    if name in ("farm", "pond", "jungle"):
        for i in range(2):  # butterflies
            bx = 540 + 400 * math.sin(t * 0.5 + i * 3)
            by = 620 + 80 * math.sin(t * 1.3 + i)
            f = abs(math.sin(t * 12 + i))
            for sx in (-1, 1):
                pen.ell(bx + sx * 18 * f, by, 18 * f + 3, 22, [(250, 150, 200), (150, 200, 255)][i], 3)


# ---------------------------------------------------------------- video
KIND_SCALE = {"baby": 0.78, "mommy": 0.95, "daddy": 1.05}
SIDE = {"baby": ("mommy", "daddy"), "mommy": ("baby", "daddy"), "daddy": ("baby", "mommy")}
STAGE_Y = 1255
G = {}


def lyric_rows(words):
    if len(words) > 5:
        return [words[:5], words[5:]] if words[0]["line"] < 3 else [words[:2], words[2:]]
    return [words]


def draw_lyrics(frame, t, T):
    cur = None
    for w in T["words"]:
        if w["start"] - 0.35 <= t:
            cur = (w["verse"], w["line"])
    if cur is None or t >= T["outro_start"]:
        return
    words = [w for w in T["words"] if (w["verse"], w["line"]) == cur]
    rows = lyric_rows(words)
    pen = Pen(frame)
    size = 68
    widths = [[font(size).getlength(w["text"]) / S for w in row] for row in rows]
    maxw = max(sum(ws) + 20 * (len(ws) - 1) for ws in widths)
    while maxw > 820 and size > 44:
        size -= 4
        widths = [[font(size).getlength(w["text"]) / S for w in row] for row in rows]
        maxw = max(sum(ws) + 20 * (len(ws) - 1) for ws in widths)
    cx, top = 500, 1395
    rowh = size * 1.35
    pen.rect(cx - maxw / 2 - 40, top - 20, cx + maxw / 2 + 40, top + rowh * len(rows) + 20, "white", 7, 36)
    for r, (row, ws) in enumerate(zip(rows, widths)):
        x = cx - (sum(ws) + 20 * (len(ws) - 1)) / 2
        y = top + rowh * r + rowh / 2
        for w, wd in zip(row, ws):
            on = w["start"] <= t < w["start"] + w["dur"] / 0.95
            done = t >= w["start"] + w["dur"] / 0.95
            if on:
                pen.rect(x - 8, y - size * 0.55, x + wd + 8, y + size * 0.55, (255, 225, 90), 0, 16)
            col = (230, 70, 40) if on else ((60, 150, 70) if done else (90, 90, 110))
            Pen(frame, x + wd / 2, y).text(0, 0, w["text"], size, col, 0)
            x += wd + 20


def hearts(pen, x, y, t):
    for i in range(4):
        u = (t * 0.6 + i / 4) % 1
        hx, hy = x - 120 + i * 80, y - u * 220
        pen.ell(hx - 12, hy, 16, 16, (240, 80, 120), 0); pen.ell(hx + 12, hy, 16, 16, (240, 80, 120), 0)
        pen.poly([(hx - 27, hy + 4), (hx + 27, hy + 4), (hx, hy + 32)], (240, 80, 120), 0)


def confetti(frame, t, t0, n=50):
    pen = Pen(frame)
    for i in range(n):
        x = (i * 137 + (t - t0) * 80 * (1 + i % 3)) % W
        y = ((t - t0) * 420 * (1 + i % 4) + i * 77) % 1350
        pen.rect(x, y, x + 16, y + 26, [(240, 90, 60), GOLD, (90, 200, 90), (70, 140, 240), (240, 80, 160)][i % 5], 0, 3)


def render(fi):
    cfg, T = G["cfg"], G["T"]
    t = fi / FPS
    if "bg" not in G:
        G["bg"] = scene_bg(cfg["scene"])
    frame = G["bg"].convert("RGBA")
    pulse = math.exp(-((t / T["beat"]) % 1) * 5)
    scene_dynamic(frame, cfg["scene"], t, pulse)
    draw = A.DRAW[cfg["animal"]]
    vi = next((v["index"] for v in T["verses"] if v["start"] <= t < v["end"]), None)
    who = cfg["verses"][vi]["who"] if vi is not None else "family"
    active = next((w for w in T["words"] if w["start"] <= t < w["start"] + w["dur"]), None)
    phase = min(1, (t - active["start"]) / active["dur"]) if active else 0
    sing_amt = math.sin(math.pi * phase) if active else 0
    hook_on = active is not None and active["hook"]
    last_line = active is not None and active["line"] == 3
    vstart = T["verses"][vi]["start"] if vi is not None else 0
    shake = 0
    if cfg["animal"] == "dino" and hook_on:
        shake = 8 * math.sin(t * 60) * (1 - phase)
    if who in KIND_SCALE:
        for side, x in zip(SIDE[who], (190, 890)):
            sc = KIND_SCALE[side] * 1.0
            bob = 14 * pulse
            draw(Pen(frame, x + shake, STAGE_Y + 45 - bob, sc), side, t, 0, blink=(t + x) % 3.7 < 0.12,
                 look=((540 - x) / 400, 0), arms="down")
        sc = KIND_SCALE[who] * 1.85
        enter = ease((t - vstart) / 0.5)
        hop = 150 * sing_amt if hook_on else 0
        arms = "up" if hook_on or (last_line and who == "daddy") else "down"
        action = sing_amt if hook_on else 0
        if last_line and who == "daddy" and active["text"] == cfg["verses"][vi]["last"][-1]:
            hop = 360 * sing_amt
        x = 540 + shake
        draw(Pen(frame, x, STAGE_Y - hop + 300 * (1 - enter), sc), who, t, sing_amt, blink=False, look=(0, -0.2),
             arms=arms, action=action)
        pen = Pen(frame)
        if last_line and who == "mommy":
            hearts(pen, 540, 760, t)
        if last_line and who == "baby":
            for i in range(6):
                a = t * 3 + i * math.pi / 3
                star(pen, 540 + math.cos(a) * 260, 980 + math.sin(a) * 120, 22, GOLD)
        for i in range(4):
            a = t * 2 + i * math.pi / 2
            star(pen, 540 + math.cos(a) * 300, STAGE_Y - 220 + math.sin(a) * 70, 14, (255, 240, 150))
    else:  # whole family together
        for kind, x in (("mommy", 210), ("daddy", 870), ("baby", 540)):
            sc = KIND_SCALE[kind] * (1.35 if kind != "baby" else 1.5) * cfg.get("family_scale", 1.0)
            hop = 80 * sing_amt if hook_on else 18 * pulse
            if kind == "baby":
                hop *= 1.3
            draw(Pen(frame, x + shake, STAGE_Y + (20 if kind != "baby" else 40) - hop, sc), kind, t, sing_amt,
                 blink=(t + x) % 3.7 < 0.12, look=(0, -0.2), arms="up" if hook_on or last_line else "down",
                 action=sing_amt if hook_on else 0)
        if last_line:
            confetti(frame, t, T["verses"][-1]["start"] + 24 * T["beat"])
    # titles
    pen = Pen(frame)
    if t < T["intro_end"] + 1.0:
        k = max(0.05, ease(t / 0.4))
        parts = cfg["title"].upper().split()
        rows = [" ".join(parts[:-1]), parts[-1]] if len(parts) > 1 else parts
        cols = [(250, 90, 60), GOLD, (90, 200, 90), (70, 140, 240), (240, 80, 160)]
        ci = 0
        for r, row in enumerate(rows):
            size = 170
            while font(size).getlength(row) / S > 980:
                size -= 6
            fw = [font(size).getlength(ch) / S for ch in row]
            x = 540 - sum(fw) / 2
            for ch, cw in zip(row, fw):
                if ch != " ":
                    Pen(frame, x + cw / 2, 250 + r * 175 - abs(math.sin(t * 6 + ci * 0.5)) * 22, k).text(0, 0, ch, size, cols[ci % 5], 14)
                    ci += 1
                x += cw
    elif t >= T["outro_start"]:
        u = t - T["outro_start"]
        k = max(0.05, ease(u / 0.4))
        Pen(frame, 540, 330 - abs(math.sin(t * 6)) * 20, k).text(0, 0, "YAY!", 160, GOLD, 14)
        Pen(frame, 540, 480, k).text(0, 0, "Sing it again!", 72, "white", 10)
        confetti(frame, t, T["outro_start"], 60)
    elif vi is not None:
        label = cfg["verse_titles"][vi]
        k = max(0.05, ease((t - vstart) / 0.35))
        p = Pen(frame, 540, 300, 0.6 + 0.4 * k)
        wd = font(66).getlength(label) / S + 70
        p.rect(-wd / 2, -55, wd / 2, 55, "white", 7, 55)
        p.text(0, 0, label, 66, cfg["accent"], 0)
    draw_lyrics(frame, t, T)
    return frame.convert("RGB").reduce(S).tobytes()


def init_worker(cfg, T):
    G["cfg"], G["T"] = cfg, T


def make(cfg, out_path, preview=None):
    T = song_timeline(cfg)
    assert T["total"] < 60, f"{cfg['title']} is {T['total']:.1f}s"
    wav = os.path.join(HERE, "build", cfg["id"] + ".wav")
    if preview is None or not os.path.exists(wav):
        build_audio(cfg, T, wav)
    print(f"{cfg['title']}: {T['total']:.1f}s", flush=True)
    if preview:
        init_worker(cfg, T)
        for ts in preview:
            Image.frombytes("RGB", (W, H), render(int(ts * FPS))).save(os.path.join(HERE, "build", f"{cfg['id']}_{ts:05.1f}.png"))
        return T
    n = int(T["total"] * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], stdin=subprocess.PIPE)
    with Pool(4, initializer=init_worker, initargs=(cfg, T)) as pool:
        for buf in pool.imap(render, range(n), chunksize=6):
            ff.stdin.write(buf)
    ff.stdin.close(); ff.wait()
    print("done", out_path, flush=True)
    return T
