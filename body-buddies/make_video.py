"""Render "Body Buddies" YouTube Shorts (1080x1920, < 20 s) with PIL + ffmpeg + gTTS.

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
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from episodes import EPISODES

W, H, FPS = 1080, 1920, 30
MAX_SECONDS = 19.5
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
INTRO, GAP, OUTRO = 0.9, 0.2, 1.0
SR = 24000

# voice: (gTTS accent, pitch factor, tempo)
VOICES = {"kid": ("com", 1.28, 1.25), "organ": ("co.uk", 0.92, 1.25)}
NAMES = {"kid": "SAM"}
# organs made of two parts get a face on each: (x offset, face scale)
FACES = {"lungs": [(-145, 0.55), (145, 0.55)], "kidneys": [(-160, 0.5), (160, 0.5)]}


def font(size):
    return ImageFont.truetype(FONT_BOLD, size)


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
    if total > MAX_SECONDS:  # squeeze the speech so the short stays < 20 s
        raise SystemExit(f"{ep['slug']}: {total:.1f}s is too long, shorten the dialogue")
    track = np.zeros(int(total * SR) + SR, dtype=np.float32)
    timeline, t = [], INTRO
    for (speaker, text), clip in zip(ep["lines"], clips):
        start = int(t * SR)
        track[start:start + len(clip)] += clip
        timeline.append((t, t + len(clip) / SR, speaker, text))
        t += len(clip) / SR + GAP
    track = track[: int(total * SR)]
    # "pop" sound for the intro
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    track[:n] += 9000 * np.sin(2 * np.pi * (400 + 900 * tt) * tt) * np.exp(-tt * 14)
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


# ---------------------------------------------------------------- drawing helpers
def gradient(top, bottom):
    t = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top)[None, None] * (1 - t) + np.array(bottom)[None, None] * t)
    arr = np.repeat(arr, W, axis=1).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(3)
    for _ in range(14):  # soft bubbles
        x, y, r = rng.integers(0, W), rng.integers(300, H), rng.integers(30, 110)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 60))
    return img


def darker(c, k=0.7):
    return tuple(int(v * k) for v in c)


def lighter(c, k=0.45):
    return tuple(int(v + (255 - v) * k) for v in c)


def organ_sprite(kind, color):
    """Draw the organ body once at 2x and downsample for smooth edges."""
    S = 1400
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    out, hi = darker(color, 0.55), lighter(color, 0.5)
    lw = 22
    if kind == "heart":
        pts = []
        for i in range(400):
            a = 2 * math.pi * i / 400
            x = 16 * math.sin(a) ** 3
            y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
            pts.append((S / 2 + x * 36, S / 2 - y * 36 - 40))
        d.rounded_rectangle([560, 120, 660, 360], 40, fill=(90, 120, 220), outline=out, width=lw)
        d.rounded_rectangle([720, 90, 820, 330], 40, fill=color, outline=out, width=lw)
        d.polygon(pts, fill=color, outline=out, width=lw)
        d.ellipse([360, 380, 520, 520], fill=hi)
    elif kind == "brain":
        blobs = [(470, 520, 230), (700, 430, 250), (930, 520, 230), (420, 760, 210),
                 (700, 760, 280), (980, 760, 210), (560, 920, 180), (840, 920, 180)]
        for x, y, r in blobs:
            d.ellipse([x - r - lw, y - r - lw, x + r + lw, y + r + lw], fill=out)
        for x, y, r in blobs:
            d.ellipse([x - r, y - r, x + r, y + r], fill=color)
        for x0, y0 in [(360, 520), (820, 480), (420, 880), (920, 900), (560, 330)]:
            d.arc([x0, y0, x0 + 160, y0 + 110], 200, 340, fill=out, width=14)
        d.line([700, 230, 700, 330], fill=out, width=14)
        d.ellipse([430, 380, 560, 470], fill=hi)
    elif kind == "lungs":
        d.rounded_rectangle([650, 80, 750, 520], 40, fill=(235, 235, 245), outline=out, width=lw)
        d.line([700, 500, 520, 620], fill=(235, 235, 245), width=90)
        d.line([700, 500, 880, 620], fill=(235, 235, 245), width=90)
        for x0, x1 in [(170, 650), (750, 1230)]:
            d.rounded_rectangle([x0, 420, x1, 1260], 230, fill=color, outline=out, width=lw)
        for x in (320, 900):
            d.ellipse([x, 520, x + 120, 620], fill=hi)
    elif kind == "stomach":
        d.rounded_rectangle([760, 80, 880, 420], 50, fill=lighter(color, 0.2), outline=out, width=lw)
        pts = []
        for i in range(400):
            a = 2 * math.pi * i / 400
            r = 1 + 0.18 * math.cos(2 * a + 0.6)
            pts.append((700 + 470 * r * math.cos(a), 760 + 380 * r * math.sin(a)))
        d.polygon(pts, fill=color, outline=out, width=lw)
        d.rounded_rectangle([200, 900, 360, 1240], 60, fill=lighter(color, 0.2), outline=out, width=lw)
        d.ellipse([420, 500, 560, 600], fill=hi)
    elif kind == "kidneys":
        bean = []
        for i in range(400):
            a = 2 * math.pi * i / 400
            dent = 150 * math.exp(-(((a + math.pi) % (2 * math.pi)) - math.pi) ** 2 / 0.25)
            bean.append((420 + (230 - dent) * math.cos(a), 700 + 360 * math.sin(a)))
        for pts in (bean, [(S - x, y) for x, y in bean]):  # right kidney mirrors the left
            d.polygon(pts, fill=color, outline=out, width=lw)
        for x in (300, S - 400):
            d.ellipse([x, 450, x + 100, 530], fill=hi)
    return img.resize((S // 2, S // 2), Image.LANCZOS)


def draw_face(d, cx, cy, s, mouth, blink, look=0):
    ew, eh = 62 * s, (70 if not blink else 8) * s
    for dx in (-95, 95):
        x = cx + dx * s
        d.ellipse([x - ew / 2, cy - eh / 2, x + ew / 2, cy + eh / 2], fill="white", outline=(40, 30, 40), width=int(5 * s))
        if not blink:
            p = 20 * s
            d.ellipse([x - p + look, cy - p + 6 * s, x + p + look, cy + p + 6 * s], fill=(30, 25, 40))
            d.ellipse([x - 6 * s + look, cy - 6 * s, x + 4 * s + look, cy + 4 * s], fill="white")
    my = cy + 95 * s
    mw, mh = 70 * s, (10 + 70 * mouth) * s
    if mouth < 0.08:
        d.arc([cx - mw, my - 40 * s, cx + mw, my + 30 * s], 20, 160, fill=(60, 20, 30), width=int(8 * s))
    else:
        d.ellipse([cx - mw * 0.8, my - mh / 2, cx + mw * 0.8, my + mh / 2], fill=(110, 20, 40), outline=(60, 20, 30), width=int(6 * s))
        d.ellipse([cx - mw * 0.4, my + mh / 2 - 22 * s, cx + mw * 0.4, my + mh / 2 - 2 * s], fill=(240, 110, 130))
    for dx in (-150, 150):  # cheeks
        x = cx + dx * s
        d.ellipse([x - 30 * s, cy + 50 * s, x + 30 * s, cy + 80 * s], fill=(255, 120, 140, 120))


def draw_kid(d, cx, cy, mouth, blink, bob):
    cy += bob
    d.rounded_rectangle([cx - 170, cy + 120, cx + 170, cy + 520], 90, fill=(60, 140, 240), outline=(30, 70, 140), width=8)
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=(255, 210, 170), outline=(150, 100, 70), width=8)
    d.chord([cx - 160, cy - 175, cx + 160, cy + 60], 180, 360, fill=(90, 55, 30))
    d.ellipse([cx - 20, cy - 200, cx + 60, cy - 130], fill=(90, 55, 30))
    draw_face(d, cx, cy - 10, 0.8, mouth, blink, look=6)


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


def outlined(d, xy, text, f, fill, stroke=(40, 20, 50), sw=8, anchor="mm"):
    d.text(xy, text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)


# ---------------------------------------------------------------- render
def render(ep, idx):
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav, total, timeline, env = build_audio(ep, tmp)
        bg = gradient(*ep["bg"])
        sprite = organ_sprite(ep["organ"], ep["color"])
        organ_name = ep["title"].replace("The ", "").upper()
        nframes = int(total * FPS)
        out = os.path.join(OUT, f"body-buddies-{ep['slug']}.mp4")
        ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
            stdin=subprocess.PIPE)
        f_title, f_ep, f_sub, f_name = font(92), font(46), font(56), font(40)
        size = 50
        while ImageDraw.Draw(bg).textlength(ep["fact"], font=font(size)) > 600:
            size -= 2
        f_fact = font(size)
        for fi in range(nframes):
            t = fi / FPS
            frame = bg.copy()
            d = ImageDraw.Draw(frame, "RGBA")
            cur = next((x for x in timeline if x[0] <= t < x[1]), None)
            speaker = cur[2] if cur else None
            amp = env[min(fi, len(env) - 1)]

            # title banner
            outlined(d, (W / 2, 120), "BODY BUDDIES", f_ep, (255, 230, 90), sw=6)
            outlined(d, (W / 2, 215), f"Ep {idx}: {ep['title']}", f_title, "white", sw=10)

            # organ: pop-in, idle bounce, heartbeat/breathing pulse
            pop = min(1, t / 0.5)
            pop = 1 - (1 - pop) ** 3 * math.cos(pop * 6)
            pulse = 1 + 0.04 * math.sin(t * (2 * math.pi * 1.3 if ep["organ"] == "heart" else 3))
            sc = 1.0 * pop * pulse
            sp = sprite.resize((max(1, int(sprite.width * sc)), max(1, int(sprite.height * sc))), Image.BILINEAR)
            ox, oy = W // 2, int(730 + 18 * math.sin(t * 2.4))
            if sc > 0.05:
                d.ellipse([ox - 250, 1070, ox + 250, 1110], fill=(0, 0, 0, 40))
                frame.paste(sp, (ox - sp.width // 2, oy - sp.height // 2), sp)
                d = ImageDraw.Draw(frame, "RGBA")
                blink = (t % 3.1) < 0.12
                for fx, fs in FACES.get(ep["organ"], [(0, 1.05)]):
                    draw_face(d, ox + fx * sc, oy - 40 * sc, sc * fs, amp if speaker == "organ" else 0, blink,
                              look=-14 if speaker == "kid" else 0)

            # kid at the bottom-left
            kb = 8 * math.sin(t * 3) if speaker == "kid" else 0
            draw_kid(d, 230, 1700, amp if speaker == "kid" else 0, (t % 3.7) < 0.12, kb)

            # speech bubble
            if cur:
                fade = min(1, (t - cur[0]) / 0.12)
                bx0, by0, bx1 = 70, 1150, W - 70
                lines = wrap(cur[3], f_sub, bx1 - bx0 - 80, d)
                by1 = by0 + 70 + 70 * len(lines)
                col = ep["color"] if speaker == "organ" else (60, 140, 240)
                d.rounded_rectangle([bx0, by0, bx1, by1], 45, fill=(255, 255, 255, int(240 * fade)), outline=col, width=10)
                tail = (230, by1 + 60) if speaker == "kid" else (W / 2, by0 - 50)
                base_y = by1 - 4 if speaker == "kid" else by0 + 4
                d.polygon([(tail[0] - 40, base_y), (tail[0] + 40, base_y), tail], fill=(255, 255, 255, int(240 * fade)))
                tag = NAMES.get(speaker, organ_name)
                tw = d.textlength(tag, font=f_name) + 50
                d.rounded_rectangle([bx0 + 40, by0 - 30, bx0 + 40 + tw, by0 + 30], 30, fill=col)
                d.text((bx0 + 40 + tw / 2, by0), tag, font=f_name, fill="white", anchor="mm")
                for li, line in enumerate(lines):
                    d.text((W / 2, by0 + 70 + 70 * li), line, font=f_sub, fill=(40, 30, 50), anchor="mm")

            # fun fact badge + outro
            if t > timeline[3][0]:
                outlined(d, (W / 2 + 170, 1700), "FUN FACT:", f_name, (255, 230, 90), sw=6)
                outlined(d, (W / 2 + 170, 1765), ep["fact"], f_fact, "white", sw=7)
            if t > total - OUTRO:
                outlined(d, (W / 2, 330), "Follow for the next organ!", font(54), (255, 230, 90), sw=8)
            ff.stdin.write(frame.tobytes())
        ff.stdin.close()
        ff.wait()
        print(f"{out}  ({total:.1f}s)")


if __name__ == "__main__":
    wanted = set(sys.argv[1:])
    for i, ep in enumerate(EPISODES, 1):
        if not wanted or ep["slug"] in wanted:
            render(ep, i)
