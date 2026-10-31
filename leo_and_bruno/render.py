"""Render "Leo & Bruno" episodes as vertical 1080x1920 YouTube Shorts (max 15 s each).

    python3 render.py              # render every episode into output/
    python3 render.py 2 4          # only episodes 2 and 4
    python3 render.py 1 --preview  # write a contact sheet of frames instead of a video
"""
import argparse
import math
import os
import re
import subprocess
import sys
from multiprocessing import Pool

import cairo
import numpy as np

import audio
from draw import H, W, clamp, ease_out_back, hexc, rrect, sparkle, text, text_size
from episodes import EPISODES

FPS = 30
INTRO = 0.45   # title pops before the first line
END = 1.2      # "see you next time" card
PAD = 0.22     # breath after each spoken line
MAX_LEN = 14.9
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output")
NAME = {"leo": ("LEO", "#2F74D8"), "bruno": ("BRUNO", "#9A5B2C")}


def _core(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def align(tokens, words):
    """Map displayed tokens to TTS word start times (for karaoke highlighting)."""
    times, j = [None] * len(tokens), 0
    for k, tok in enumerate(tokens):
        core = _core(tok)
        for jj in range(j, len(words)):
            wc = _core(words[jj][0])
            if core and wc and (core.startswith(wc) or wc.startswith(core)):
                times[k], j = words[jj][1], jj + 1
                break
    last = 0.0
    for k in range(len(times)):
        times[k] = last = times[k] if times[k] is not None else last
    return times


class Timeline:
    def __init__(self, ep):
        self.ep, self.beats = ep, ep["beats"]
        self.starts, self.ends, self.lines = [], [], {}
        t = INTRO
        for i, b in enumerate(self.beats):
            if "say" in b:
                who, txt = b["say"]
                samples, words = audio.tts(who, txt)
                speech = words[-1][2] if words else len(samples) / audio.SR
                d = max(speech + PAD, b.get("min", 0))
                tokens = txt.split()
                self.lines[i] = dict(who=who, text=txt, samples=samples, words=words, tokens=tokens,
                                     token_t=align(tokens, words), env=audio.envelope(samples, FPS))
            else:
                d = b["dur"]
            self.starts.append(t)
            self.ends.append(t + d)
            t += d
        self.total = t + END
        if self.total > MAX_LEN:
            raise SystemExit(f"Episode {ep['num']} is {self.total:.2f}s — longer than {MAX_LEN}s")

    # ---- helpers used by the episode scripts
    def t0(self, i):
        return self.starts[i]

    def dur(self, i):
        return self.ends[i] - self.starts[i]

    def p(self, i, T):
        return clamp((T - self.starts[i]) / (self.ends[i] - self.starts[i]))

    def on(self, i, T):
        return self.starts[i] <= T < self.ends[i]

    def mouth(self, who, T):
        for i, ln in self.lines.items():
            if ln["who"] == who and self.on(i, T):
                f = (T - self.starts[i]) * FPS
                k = int(f)
                env = ln["env"]
                if k + 1 < len(env):
                    return float(env[k] * (1 - (f - k)) + env[k + 1] * (f - k))
        return 0.0

    def blink(self, who, T):
        per, off = (2.9, 0.4) if who == "leo" else (3.6, 1.7)
        return ((T + off) % per) < 0.12

    def word(self, i, T):
        ln = self.lines.get(i)
        if not ln:
            return -1
        rel = T - self.starts[i]
        return sum(1 for w in ln["words"] if w[1] <= rel) - 1

    def word_start(self, i, w):
        return self.starts[i] + self.lines[i]["words"][w][1]


# ------------------------------------------------------------------ overlays
def draw_title(ctx, T, ep):
    k = ease_out_back(T / 0.4) if T < 0.4 else 1.0
    ctx.save()
    ctx.translate(W / 2, 190)
    ctx.scale(k, k)
    ctx.rotate(math.sin(T * 2.2) * 0.02)
    text(ctx, "LEO & BRUNO", 0, 0, 104, color="#FFD23F", stroke="#2a1a10", sw=22)
    text(ctx, f"Episode {ep['num']}: {ep['title']}", 0, 78, 48, color="#FFFFFF", stroke="#2a1a10", sw=11)
    ctx.restore()


def wrap(ctx, tokens, size, maxw):
    lines, cur, curw = [], [], 0.0
    space = text_size(ctx, " ", size)
    for k, tok in enumerate(tokens):
        w = text_size(ctx, tok, size)
        if cur and curw + space + w > maxw:
            lines.append(cur)
            cur, curw = [], 0.0
        curw += (space if cur else 0) + w
        cur.append((k, tok, w))
    if cur:
        lines.append(cur)
    return lines


def draw_caption(ctx, T, tl):
    for i, ln in tl.lines.items():
        if not tl.on(i, T):
            continue
        rel = T - tl.starts[i]
        size, maxw = 68, 880
        rows = wrap(ctx, ln["tokens"], size, maxw)
        space = text_size(ctx, " ", size)
        widths = [sum(w for _, _, w in r) + space * (len(r) - 1) for r in rows]
        bw = max(widths) + 90
        bh = len(rows) * 88 + 56
        top = 360
        k = ease_out_back(rel / 0.18) if rel < 0.18 else 1.0
        ctx.save()
        ctx.translate(W / 2, top + bh / 2)
        ctx.scale(k, k)
        ctx.translate(-W / 2, -(top + bh / 2))
        rrect(ctx, W / 2 - bw / 2, top + 8, bw, bh, 40)
        ctx.set_source_rgba(0, 0, 0, 0.25)
        ctx.fill()
        rrect(ctx, W / 2 - bw / 2, top, bw, bh, 40)
        ctx.set_source_rgba(1, 1, 1, 0.96)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexc("#2a1a10"))
        ctx.set_line_width(6)
        ctx.stroke()
        name, col = NAME[ln["who"]]
        nw = text_size(ctx, name, 40) + 50
        rrect(ctx, W / 2 - bw / 2 + 30, top - 34, nw, 62, 31)
        ctx.set_source_rgba(*hexc(col))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexc("#2a1a10"))
        ctx.set_line_width(5)
        ctx.stroke()
        text(ctx, name, W / 2 - bw / 2 + 30 + nw / 2, top + 11, 40, color="#FFFFFF", stroke=None)
        cur = sum(1 for tt in ln["token_t"] if tt <= rel) - 1
        for r, row in enumerate(rows):
            x = W / 2 - widths[r] / 2
            y = top + 50 + 66 + r * 88 - 14
            for k_tok, tok, w in row:
                said = k_tok <= cur
                color = "#FF7A1A" if k_tok == cur else ("#2a1a10" if said else "#8A7A70")
                text(ctx, tok, x, y, size, color=color, stroke=None, align="left")
                x += w + space
        ctx.restore()


def draw_end(ctx, T, tl):
    age = T - (tl.total - END)
    if age < 0:
        return
    k = ease_out_back(age / 0.3)
    ctx.save()
    ctx.translate(W / 2, 470)
    ctx.scale(k, k)
    ctx.rotate(math.sin(age * 5) * 0.03)
    text(ctx, "See you next adventure!", 0, 0, 74, color="#FFFFFF", stroke="#2a1a10", sw=16)
    ctx.restore()
    for j in range(5):
        a = age * 3 + j * 1.3
        sparkle(ctx, W / 2 + math.cos(a) * 420, 445 + math.sin(a * 1.4) * 70, 22 * clamp(age * 4), 0.95, "#FFE14D")


def render_frame(ctx, T, ep, tl):
    ctx.set_source_rgb(1, 1, 1)
    ctx.paint()
    ctx.save()
    ep["draw"](ctx, T, tl)
    ctx.restore()
    ctx.new_path()
    draw_title(ctx, T, ep)
    draw_caption(ctx, T, tl)
    draw_end(ctx, T, tl)


# ------------------------------------------------------------------ audio mix
def mix(ep, tl):
    sr = audio.SR
    n = int(math.ceil(tl.total * sr))
    voice = np.zeros(n)
    fx = np.zeros(n)

    def put(buf, sig, at, gain=1.0):
        i = int(at * sr)
        j = min(n, i + len(sig))
        if i < n:
            buf[i:j] += sig[:j - i] * gain

    for i, ln in tl.lines.items():
        s = ln["samples"]
        put(voice, s / (np.max(np.abs(s)) + 1e-9) * 0.9, tl.starts[i])
    put(fx, audio.sfx("pop"), 0.02, 0.8)
    for i, b in enumerate(tl.beats):
        for name, off in b.get("sfx", []):
            put(fx, audio.sfx(name), tl.starts[i] + off, 0.7)
    put(fx, audio.sfx("tada"), tl.total - END + 0.05, 0.7)
    mus = np.zeros(n)
    m = audio.music(tl.total + 0.1, ep["seed"])[:n]
    mus[:len(m)] = m
    mus = mus / (np.max(np.abs(mus)) + 1e-9) * 0.22
    # duck the music under the voices
    env = np.convolve(np.abs(voice), np.ones(4410) / 4410, mode="same")
    duck = np.clip(env * 12, 0, 1)
    mus *= 1 - 0.55 * duck
    fade = int(0.5 * sr)
    mus[-fade:] *= np.linspace(1, 0, fade)
    return voice + fx * 0.9 + mus


# ------------------------------------------------------------------ main
def slug(ep):
    return f"ep{ep['num']:02d}_" + re.sub(r"[^a-z0-9]+", "_", ep["title"].lower()).strip("_")


def render(ep, preview=False):
    tl = Timeline(ep)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    os.makedirs(OUT_DIR, exist_ok=True)
    name = slug(ep)
    if preview:
        times = np.linspace(0.3, tl.total - 0.2, 12)
        thumbs = []
        for T in times:
            render_frame(ctx, T, ep, tl)
            buf = np.ndarray((H, W, 4), np.uint8, surf.get_data()).copy()
            thumbs.append(buf[::3, ::3, [2, 1, 0]])
        rows = [np.concatenate(thumbs[r * 6:(r + 1) * 6], axis=1) for r in range(2)]
        sheet = np.concatenate(rows, axis=0)
        path = os.path.join(HERE, "build", f"{name}_preview.ppm")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(f"P6 {sheet.shape[1]} {sheet.shape[0]} 255\n".encode())
            f.write(sheet.tobytes())
        png = path.replace(".ppm", ".png")
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", path, png], check=True)
        print(f"preview: {png}  ({tl.total:.2f}s)")
        return png

    wav = os.path.join(HERE, "build", f"{name}.wav")
    os.makedirs(os.path.dirname(wav), exist_ok=True)
    audio.write_wav(wav, mix(ep, tl))
    mp4 = os.path.join(OUT_DIR, f"{name}.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = int(round(tl.total * FPS))
    for f in range(frames):
        render_frame(ctx, f / FPS, ep, tl)
        surf.flush()
        proc.stdin.write(bytes(surf.get_data()))
    proc.stdin.close()
    proc.wait()
    print(f"{mp4}  ({tl.total:.2f}s)")
    return mp4


def _job(args):
    num, preview = args
    ep = next(e for e in EPISODES if e["num"] == num)
    return render(ep, preview)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes", nargs="*", type=int)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    nums = a.episodes or [e["num"] for e in EPISODES]
    for n in nums:  # fetch voices first (sequentially, it's network-bound)
        Timeline(next(e for e in EPISODES if e["num"] == n))
    with Pool(min(4, len(nums))) as pool:
        pool.map(_job, [(n, a.preview) for n in nums])


if __name__ == "__main__":
    sys.exit(main())
