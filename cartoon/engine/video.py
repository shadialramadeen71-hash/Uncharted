"""Episode model + build pipeline: TTS -> choreography -> audio mix -> frames -> mp4."""
import math
import os
import subprocess
import wave

import cairo
import numpy as np

from . import audio, character, euro, euro_places, flat_places, palace_places, scene  # noqa: F401 (*_places register backgrounds)
from .anim import Track, clamp
from .character import Character

FPS = 30
MAX_LEN = 20.0  # YouTube Shorts episodes must stay under 20 s
BASE_ZOOM, BASE_CY = 1.12, 1040.0


class Episode:
    def __init__(self, title, hook, scene_name, music_seed=1, mood="bouncy", bpm=124, theme="cartoon", floor=None,
                 max_len=MAX_LEN, ambience=None, hook_end=2.4, base_zoom=BASE_ZOOM, base_cy=BASE_CY):
        self.title = title
        self.hook = hook  # [(text, color), ...]
        self.hook_end = hook_end
        self.max_len = max_len
        self.cap_y = None  # override the theme's caption height for one episode
        self.ambience = ambience  # background atmosphere ("city", "forest", "park"); mood=None means no music
        self.scene = scene_name
        self.music_seed, self.mood, self.bpm = music_seed, mood, bpm
        self.chars = {}
        self.voices = {}
        self.lines = []
        self.sfx = []
        self.layers = {"back": [], "front": [], "ui": []}
        self.tip = None
        self.follow_at = None
        self.end = None
        self.theme = theme
        self.floor = floor  # e.g. "snow" overrides every character's footstep sound
        self.base_zoom, self.base_cy = base_zoom, base_cy
        self.cam = {"zoom": Track(base_zoom), "cx": Track(540.0), "cy": Track(base_cy), "shake": Track(0.0)}

    # authoring -------------------------------------------------------------------
    def cast(self, name, look, voice, x, facing=1, scale=1.0, z=0, label=None, color="#333333"):
        c = Character(name, look, x, facing, scale, z)
        self.chars[name] = c
        self.voices[name] = dict(voice, label=label or name.upper(), color=color)
        return c

    def say(self, who, text, wait=0.0, fx=None, gap=0.16):
        self.lines.append(dict(who=who, text=text, wait=wait, fx=fx, gap=gap))

    def sound(self, t, name, gain=1.0):
        self.sfx.append((t, name, gain))

    def draw(self, layer, fn):
        """fn(ctx, t) drawn on 'back' (behind characters), 'front', or 'ui' (screen space)."""
        self.layers[layer].append(fn)

    def punch(self, t, zoom=1.25, cx=540, cy=1000, dur=0.25, hold=None):
        c = self.cam
        c["zoom"].to(t, t + dur, zoom, "back")
        c["cx"].to(t, t + dur, float(cx), "out")
        c["cy"].to(t, t + dur, float(cy), "out")
        if hold is not None:
            self.unpunch(t + dur + hold)

    def unpunch(self, t, dur=0.35):
        c = self.cam
        c["zoom"].to(t, t + dur, self.base_zoom)
        c["cx"].to(t, t + dur, 540.0)
        c["cy"].to(t, t + dur, self.base_cy)

    def shake(self, t, amount=1.0, dur=0.35):
        self.cam["shake"].to(t, t + 0.03, amount, "linear")
        self.cam["shake"].to(t + 0.03, t + dur, 0.0, "linear")


# ---------------------------------------------------------------------- build
def _voice_pass(ep):
    t = 0.3
    for ln in ep.lines:
        v = ep.voices[ln["who"]]
        y, words = audio.tts(ln["text"], v["voice"], v.get("rate", "+0%"), v.get("pitch", "+0Hz"))
        y = audio.voice_fx(y, ln["fx"])
        ln["audio"] = y
        ln["words"] = words
        ln["start"] = t + ln["wait"]
        ln["dur"] = len(y) / audio.SR
        ln["end"] = ln["start"] + ln["dur"]
        ln["who_label"] = v["label"]
        ln["color"] = scene.hexrgb(v["color"])
        t = ln["end"] + ln["gap"]


def _mouths(ep, n):
    curves = {name: (np.zeros(n), np.zeros(n)) for name in ep.chars}
    for ln in ep.lines:
        m, w = audio.mouth_curve(ln["audio"], FPS)
        i0 = int(round(ln["start"] * FPS))
        k = min(len(m), n - i0)
        if k > 0:
            curves[ln["who"]][0][i0:i0 + k] = np.maximum(curves[ln["who"]][0][i0:i0 + k], m[:k])
            curves[ln["who"]][1][i0:i0 + k] = w[:k]
    for name, c in ep.chars.items():
        mm, ww = curves[name]
        c.mouth = (lambda mm, ww: lambda t: (float(mm[min(int(t * FPS), n - 1)]), float(ww[min(int(t * FPS), n - 1)])))(mm, ww)


def _mix(ep, dur, path):
    n = int(dur * audio.SR) + 1
    L = np.zeros(n)
    R = np.zeros(n)
    rng = np.random.default_rng(ep.music_seed + 100)

    def put(y, t, g, pan=0.0):
        i0 = int(t * audio.SR)
        if i0 >= n or i0 < 0:
            return
        y = y[:n - i0] * g
        L[i0:i0 + len(y)] += y * math.sqrt((1 - pan) / 2) * 1.414
        R[i0:i0 + len(y)] += y * math.sqrt((1 + pan) / 2) * 1.414

    pan_of = lambda x: float(np.clip((x - 540) / 540 * 0.35, -0.35, 0.35))
    voice = np.zeros(n)
    for ln in ep.lines:
        c = ep.chars[ln["who"]]
        y = ln["audio"] / (np.max(np.abs(ln["audio"])) + 1e-9) * 0.9
        put(y, ln["start"], 1.0, pan_of(c.tr["x"].at(ln["start"])))
        i0 = int(ln["start"] * audio.SR)
        voice[i0:i0 + len(y)] = np.maximum(voice[i0:i0 + len(y)], 1.0)
    # footsteps (real-time positioned, panned with the walker)
    steps = np.zeros(n)
    for c in ep.chars.values():
        kind = ep.floor or c.look.get("step", "sneaker")
        for st in c.steps:
            fs = audio.footstep(rng, kind, strength=st["w"], speed=st["speed"])
            i0 = int(st["t"] * audio.SR)
            fs = fs[:max(0, n - i0)]
            p = pan_of(st["x"])
            L[i0:i0 + len(fs)] += fs * 0.8 * (1 - p)
            R[i0:i0 + len(fs)] += fs * 0.8 * (1 + p)
            steps[i0:i0 + len(fs)] += fs
    for (t, name, g) in ep.sfx:
        put(audio.sfx(name, rng), t, 0.7 * g)
    # music with side-chain ducking under dialogue
    if ep.mood is None:
        mus = np.zeros(n)
    elif ep.mood == "villain":
        mus = audio.villain_music(dur, ep.music_seed, ep.bpm)
    elif ep.mood == "musette":
        mus = audio.musette(dur, ep.music_seed, ep.bpm)
    else:
        mus = audio.music(dur, ep.music_seed, ep.bpm, mood=ep.mood)
    mus = np.pad(mus, (0, max(0, n - len(mus))))[:n]
    k = int(0.15 * audio.SR)
    duck = np.convolve(voice, np.ones(k) / k, mode="same")
    gain = 0.32 - 0.2 * np.clip(duck, 0, 1)
    put(mus * gain, 0.0, 1.0)
    if ep.ambience:
        amb = audio.ambience(ep.ambience, dur, ep.music_seed)
        put(np.pad(amb, (0, max(0, n - len(amb))))[:n] * (0.55 - 0.25 * np.clip(duck, 0, 1)), 0.0, 1.0)
    L, R = audio.room_reverb(L, 0.06), audio.room_reverb(R, 0.06, seed=8)
    st = np.stack([L, R], 1)
    st /= np.max(np.abs(st)) + 1e-9
    st *= 0.95
    pcm = (st * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(audio.SR)
        wf.writeframes(pcm.tobytes())


def _active_line(ep, t):
    for ln in ep.lines:
        if ln["start"] - 0.05 <= t <= ln["end"] + 0.25:
            return ln
    return None


def build(ep, choreo, out_path, preview_frames=None):
    character.set_style(ep.theme)
    scene.set_theme(ep.theme)
    character.STYLE["k"] = 0
    _voice_pass(ep)
    L = ep.lines
    choreo(ep, L)
    dur = ep.end or (L[-1]["end"] + 1.2)
    if dur > ep.max_len:
        raise ValueError(f"{ep.title}: {dur:.1f}s is longer than {ep.max_len}s")
    n = int(dur * FPS)
    for c in ep.chars.values():
        c.simulate(FPS, n)
    _mouths(ep, n)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    wav = out_path.rsplit(".", 1)[0] + ".wav"
    _mix(ep, dur, wav)

    bg = scene.make_background(ep.scene)
    vig = scene.vignette()
    post = None
    if ep.theme == "euro":
        bg = euro.watercolorize(bg)
        post = euro.Post()
    elif ep.theme == "storybook":  # fairy-tale palace: same hand-drawn ink, cooler magical grade
        bg = euro.watercolorize(bg, seed=9)
        post = euro.Post(grade=(0.86, 0.78, 1.0, 0.16), paper=0.6, grain=0.06)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, scene.W, scene.H)
    ctx = cairo.Context(surf)

    frames = range(n) if preview_frames is None else preview_frames
    proc = None
    if preview_frames is None:
        proc = subprocess.Popen([
            "ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{scene.W}x{scene.H}",
            "-r", str(FPS), "-i", "-", "-i", wav,
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
            "-movflags", "+faststart", "-shortest", out_path], stdin=subprocess.PIPE)
    chars = sorted(ep.chars.values(), key=lambda c: c.z)
    for fi in frames:
        t = fi / FPS
        character.STYLE["k"] = fi // 3  # ink lines "boil" like hand-drawn animation
        ctx.save()
        z = ep.cam["zoom"].at(t) * (1 + 0.012 * t / dur)  # slow push-in keeps the frame alive
        sh = ep.cam["shake"].at(t)
        ctx.translate(scene.W / 2 + sh * 14 * math.sin(t * 83), scene.H / 2 + sh * 12 * math.cos(t * 67))
        ctx.scale(z, z)
        ctx.translate(-ep.cam["cx"].at(t), -ep.cam["cy"].at(t))
        ctx.set_source_surface(bg, -200, -200)
        ctx.paint()
        for fn in ep.layers["back"]:
            fn(ctx, t)
        for c in chars:
            c.draw(ctx, fi, t, scene.GROUND)
        for fn in ep.layers["front"]:
            fn(ctx, t)
        ctx.restore()
        if post:
            post.apply(ctx, fi)
        ctx.set_source_surface(vig, 0, 0)
        ctx.paint()
        # UI
        scene.hook_title(ctx, t, ep.hook, ep.hook_end)
        ln = _active_line(ep, t)
        tip_on = ep.tip and t >= ep.tip["t0"]
        if ln:
            scene.captions(ctx, ln, t, y=1270 if tip_on else (ep.cap_y or scene.THEME["cap_y"]))
        if tip_on:
            scene.tip_card(ctx, t, ep.tip)
        for fn in ep.layers["ui"]:
            fn(ctx, t)
        if ep.follow_at is not None:
            scene.follow_card(ctx, t, ep.follow_at)
        surf.flush()
        if proc:
            proc.stdin.write(surf.get_data())
        else:
            surf.write_to_png(out_path.rsplit(".", 1)[0] + f"_f{fi:04d}.png")
    if proc:
        proc.stdin.close()
        proc.wait()
        if proc.returncode:
            raise RuntimeError("ffmpeg failed")
    os.remove(wav)
    return dur
