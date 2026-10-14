"""Engine for THE WOBBLES: multi-scene episodes in 16:9, built on the
mask-buddies voice/SFX pipeline."""
import math
import multiprocessing as mp
import os
import subprocess

import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mask-buddies"))

import cairo  # noqa: E402
import numpy as np  # noqa: E402

import audio  # noqa: E402
from characters import WALK_STYLES
from wob_chars import CAST, INK, TAU, col, ellipse, fill_ink, hexc, path_poly, rrect
from wob_world import SCENES, H, W, apply_cam, text_center

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
DEFAULT_CAM = {"x": 1000.0, "y": -470.0, "z": 0.85}
audio.CACHE = os.path.join(HERE, "build", "voice_cache")

# ---- voices for the family -------------------------------------------------
audio.VOICES.update({
    "gary": dict(voice="en-US-RogerNeural", rate="-4%", pitch="-10Hz", af="volume=1.2"),
    "linda": dict(voice="en-US-MichelleNeural", rate="+2%", pitch="-4Hz", af="volume=1.15"),
    "max": dict(voice="en-US-AndrewNeural", rate="+10%", pitch="+38Hz", af="volume=1.2"),
    "pip": dict(voice="en-US-AnaNeural", rate="+8%", pitch="+12Hz", af="volume=1.2"),
    "fuss": dict(voice="en-GB-RyanNeural", rate="-6%", pitch="-14Hz",
                 af="vibrato=f=5:d=0.08,highpass=f=160,volume=1.3"),
})


# ---- extra synthesized SFX -------------------------------------------------
def sfx_sizzle():
    rng = np.random.default_rng(9)
    t = audio._t(2.5)
    n = rng.standard_normal(len(t))
    n = n - np.convolve(n, np.ones(6) / 6, mode="same")
    crackle = (rng.random(len(t)) > 0.9993) * rng.standard_normal(len(t)) * 3
    return (n * 0.25 + crackle * 0.3) * audio._env(len(t), 0.3, 0.6)


def sfx_rocket():
    rng = np.random.default_rng(10)
    t = audio._t(2.2)
    n = np.convolve(rng.standard_normal(len(t)), np.ones(5) / 5, mode="same")
    tone = audio._sweep(120, 900, 2.2, "saw") * 0.15
    return (n * 0.6 + tone) * audio._env(len(t), 0.2, 0.6) * np.linspace(0.6, 1.0, len(t))


def sfx_bark():
    out = []
    for f0 in (520, 470):
        t = audio._t(0.16)
        f = f0 * np.linspace(1.2, 0.8, len(t))
        s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / audio.SR)) * 0.5
        s = np.convolve(s, np.ones(10) / 10, mode="same")
        out += [s * audio._env(len(t), 0.005, 0.06) * 0.6, np.zeros(int(0.1 * audio.SR))]
    return np.concatenate(out)


def sfx_beep():
    return audio._sweep(1760, 1760, 0.12, "square") * audio._env(int(0.12 * audio.SR), 0.003, 0.02) * 0.35


def sfx_thud():
    t = audio._t(0.5)
    return np.sin(2 * np.pi * np.cumsum(np.geomspace(140, 50, len(t))) / audio.SR) * np.exp(-t * 9) * 0.9


def sfx_fanfare():
    notes = [(523, 0.14), (659, 0.14), (784, 0.14), (1047, 0.5)]
    out = []
    for f, d in notes:
        s = audio._sweep(f, f, d, "saw", vib=0.004)
        s = np.convolve(s, np.ones(8) / 8, mode="same")
        out.append(s * audio._env(len(s), 0.01, 0.08) * 0.28)
    return np.concatenate(out)


for _fn in (sfx_sizzle, sfx_rocket, sfx_bark, sfx_beep, sfx_thud, sfx_fanfare):
    audio.SFX[_fn.__name__[4:]] = _fn


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


NAMES = {"gary": ("GARY", "#3d8b3d"), "linda": ("LINDA", "#8e44ad"), "max": ("MAX", "#ff8f1f"),
         "pip": ("PIP", "#ff6fae"), "fuss": ("MR. FUSSBUCKET", "#7a8b3a"), "biscuit": ("BISCUIT", "#b07a3c"),
         "narrator": ("", "#000000")}


class Episode:
    def __init__(self, number, title):
        self.number, self.title = number, title
        self.cursor = 0.0
        self.actors, self.order = {}, []
        self.cmds, self.lines, self.sfx_events = [], [], []
        self.cam_keys, self.var_keys, self.fx_texts = [], [], []
        self.scene_keys = []   # (t, scene)
        self.music_keys = []   # (t, path, start)
        self.vars0 = {"ep_title": title}
        self.end_card = "SEE YOU NEXT TIME!"

    def _at(self, at):
        return self.cursor if at is None else at

    # ---- cast & staging ----
    def add(self, name, x=-2000, facing=1, z=0, **state):
        self.actors[name] = dict(char=CAST[name](), x=x, facing=facing, z=z, state=state, plan_x=x)
        self.order.append(name)

    def cut(self, scene, cam=None, music=None):
        t = self.cursor
        self.scene_keys.append((t, scene))
        c = dict(DEFAULT_CAM, **(cam or {}))
        self.cam_keys.append((t, 0.0, c))
        self.var_keys.append((t, 0.0, "scene_start", t))
        if music:
            self.music_keys.append((t, music[0], music[1]))

    def place(self, name, x, facing=None, at=None, **state):
        kw = dict(state, x=float(x), visible=state.get("visible", True), _move=None)
        if facing is not None:
            kw["facing"] = facing
        self.cmds.append((self._at(at), name, "set", kw))
        self.actors[name]["plan_x"] = x

    def hide(self, *names, at=None):
        for n in names:
            self.cmds.append((self._at(at), n, "set", dict(visible=False, _move=None)))

    def walk(self, name, to, speed=None, style="normal", at=None, wait=False):
        a = self.actors[name]
        speed = speed or {"normal": 300, "stiff": 110, "run": 650, "sneak": 170, "shuffle": 95}[style]
        t = self._at(at)
        dur = abs(to - a["plan_x"]) / speed
        self.cmds.append((t, name, "walk", dict(to=to, speed=speed, style=style)))
        a["plan_x"] = to
        if wait:
            self.cursor = t + dur
        return dur

    def say(self, name, text, gap=0.3, at=None, wait=True):
        clip = audio.tts(name, text)
        t = self._at(at)
        self.lines.append((t, name, text, clip))
        d = len(clip) / audio.SR
        if wait:
            self.cursor = t + d + gap
        return d

    def wait(self, s):
        self.cursor += s

    def sfx(self, name, at=None, gain=1.0):
        self.sfx_events.append((self._at(at), name, gain))

    def set(self, name, at=None, **kw):
        self.cmds.append((self._at(at), name, "set", kw))

    def tween(self, name, key, value, dur, at=None):
        self.cmds.append((self._at(at), name, "tween", dict(key=key, value=value, dur=dur)))

    def arms(self, name, pose, at=None):
        self.set(name, at, arms=pose)

    def face(self, name, d, at=None):
        self.set(name, at, facing=d)

    def mood(self, name, m, at=None):
        self.set(name, at, mood=m)

    def emote(self, name, kind, dur=1.5, at=None):
        self.cmds.append((self._at(at), name, "emote", dict(emote=kind, dur=dur)))

    def jump(self, name, h=160, dur=0.5, at=None):
        self.cmds.append((self._at(at), name, "jump", dict(h=h, dur=dur)))

    def shake(self, name, dur=1.0, amt=1.0, at=None):
        self.cmds.append((self._at(at), name, "shake", dict(dur=dur, amt=amt)))

    def cam(self, dur=0.8, at=None, **kw):
        self.cam_keys.append((self._at(at), dur, kw))

    def var(self, name, value, at=None, dur=0.0):
        self.var_keys.append((self._at(at), dur, name, value))

    def fx_text(self, text, x, y, dur=1.0, at=None, color="#ffd23f", size=150, rot=-0.08):
        self.fx_texts.append((self._at(at), dur, text, x, y, hexc(color), size, rot))

    # ---- simulation ----
    def build(self):
        self.total = self.cursor + 3.4
        nfr = int(self.total * FPS)
        dt = 1.0 / FPS
        cmds = sorted(self.cmds, key=lambda c: c[0])
        st = {}
        for n in self.order:
            a = self.actors[n]
            s = dict(name=n, x=float(a["x"]), facing=a["facing"], z=a["z"], phase=0.0, walkw=0.0,
                     style="normal", arms="swing", talk=0.0, shake=0.0, jump=0.0, squash=0.0, lift=0.0,
                     emote=None, emote_t=0.0, t=0.0, arm_ang=None, visible=False, mood=None, item=None)
            s.update(a["state"])
            s.update(_move=None, _jump=None, _shake=None, _emote_until=-1.0, _tweens=[])
            st[n] = s
        talk_tracks, duck = [], []
        for t0, n, _, clip in self.lines:
            talk_tracks.append((t0, n, audio.envelope(clip, FPS)))
            duck.append((t0 - 0.1, t0 + len(clip) / audio.SR + 0.15))
        cam = dict(DEFAULT_CAM)
        cam_keys = sorted(self.cam_keys, key=lambda k: k[0])
        var_keys = sorted(self.var_keys, key=lambda k: k[0])
        vars_, var_from = dict(self.vars0), {}
        active, steps, frames, ci = None, [], [], 0
        scenes = sorted(self.scene_keys)
        for fi in range(nfr):
            t = fi * dt
            while ci < len(cmds) and cmds[ci][0] <= t + 1e-9:
                _, n, kind, kw = cmds[ci]
                s = st[n]
                if kind == "walk":
                    s["_move"] = kw
                    s["style"] = kw["style"]
                elif kind == "set":
                    s.update(kw)
                elif kind == "tween":
                    s["_tweens"].append((t, kw["dur"], kw["key"], s.get(kw["key"], 0.0), kw["value"]))
                elif kind == "emote":
                    s.update(emote=kw["emote"], emote_t=t, _emote_until=t + kw["dur"])
                elif kind == "jump":
                    s["_jump"] = (t, kw["h"], kw["dur"])
                elif kind == "shake":
                    s["_shake"] = (t, kw["dur"], kw["amt"])
                ci += 1
            for n in self.order:
                s = st[n]
                ch = self.actors[n]["char"]
                s["t"] = t
                mv, moving = s["_move"], False
                if mv:
                    dx = mv["to"] - s["x"]
                    step = mv["speed"] * dt
                    if abs(dx) <= step:
                        s["x"], s["_move"] = mv["to"], None
                    else:
                        s["x"] += math.copysign(step, dx)
                        s["facing"] = 1 if dx > 0 else -1
                    moving = True
                    stride = 110 * WALK_STYLES[s["style"]][3] * getattr(ch, "scale", 1.0)
                    old = s["phase"]
                    s["phase"] += min(step, abs(dx)) / stride * math.pi
                    if int(old // math.pi) != int(s["phase"] // math.pi) and s["visible"]:
                        steps.append(t)
                s["walkw"] += ((1.0 if moving else 0.0) - s["walkw"]) * min(1.0, dt * (9 if moving else 7))
                keep = []
                for t0, d, key, a0, a1 in s["_tweens"]:
                    u = ease((t - t0) / d) if d > 0 else 1.0
                    s[key] = a0 + (a1 - a0) * u
                    if t - t0 < d:
                        keep.append((t0, d, key, a0, a1))
                s["_tweens"] = keep
                s["jump"], s["squash"] = 0.0, 0.0
                if s["_jump"]:
                    j0, h, d = s["_jump"]
                    u = (t - j0) / d
                    if u <= 1:
                        s["jump"] = h * 4 * u * (1 - u)
                    elif u <= 1.35:
                        s["squash"] = 0.12 * math.sin((u - 1) / 0.35 * math.pi)
                    else:
                        s["_jump"] = None
                s["shake"] = 0.0
                if s["_shake"]:
                    if t - s["_shake"][0] <= s["_shake"][1]:
                        s["shake"] = s["_shake"][2]
                    else:
                        s["_shake"] = None
                if s["emote"] and t > s["_emote_until"]:
                    s["emote"] = None
                s["talk"] = 0.0
                for t0, who, env in talk_tracks:
                    if who == n:
                        i = int((t - t0) * FPS)
                        if 0 <= i < len(env):
                            s["talk"] = max(s["talk"], float(env[i]))
                tgt = ch.arm_targets(s)
                if s["arm_ang"] is None:
                    s["arm_ang"] = tuple(tgt)
                else:
                    k = min(1.0, dt * 12)
                    s["arm_ang"] = tuple(a + (b - a) * k for a, b in zip(s["arm_ang"], tgt))
            # camera
            for key in cam_keys:
                if key[0] <= t + 1e-9 and (active is None or key[0] > active[0][0]):
                    active = (key, dict(cam))
            if active:
                (k0, kd, tgt), start = active
                u = ease((t - k0) / kd) if kd > 0 else 1.0
                for ax in ("x", "y", "z"):
                    if tgt.get(ax) is not None:
                        cam[ax] = start[ax] + (tgt[ax] - start[ax]) * u
            # vars
            for vt, vd, vn, vv in var_keys:
                if vt <= t + 1e-9:
                    if isinstance(vv, (int, float)) and vd > 0:
                        if (vt, vn) not in var_from:
                            var_from[(vt, vn)] = vars_.get(vn, 0.0) or 0.0
                        vars_[vn] = var_from[(vt, vn)] + (vv - var_from[(vt, vn)]) * ease((t - vt) / vd)
                    else:
                        vars_[vn] = vv
            vars_["scene_t"] = t - vars_.get("scene_start", 0.0)
            scene = "intro"
            for s0, nm in scenes:
                if s0 <= t + 1e-9:
                    scene = nm
            if "fuss" in st:
                vars_["fuss_head"] = self.actors["fuss"]["char"].head_top(st["fuss"])
            caption = None
            for t0, who, text, clip in self.lines:
                if t0 - 0.05 <= t <= t0 + len(clip) / audio.SR + 0.2:
                    caption = (who, text, t - t0)
            frames.append(dict(t=t, scene=scene, cam=dict(cam), vars=dict(vars_), caption=caption,
                               actors=[{k: v for k, v in st[n].items() if not k.startswith("_")}
                                       for n in self.order]))
        self.frames, self.steps, self.duck = frames, steps, duck
        return self

    def build_audio(self, path):
        n = int(self.total * audio.SR)
        music = np.zeros(n)
        keys = sorted(self.music_keys)
        for i, (t0, p, start) in enumerate(keys):
            t1 = keys[i + 1][0] if i + 1 < len(keys) else self.total
            seg = audio.load_music(p, start, t1 - t0 + 0.6)
            a = int(t0 * audio.SR)
            seg = seg[: max(0, min(len(seg), n - a))]
            fi = int(0.3 * audio.SR)
            seg[:fi] *= np.linspace(0, 1, fi)
            music[a:a + len(seg)] += seg
        a = audio.mix(self.total, [(t, c) for t, _, _, c in self.lines], self.sfx_events, self.steps,
                      music, self.duck)
        audio.write_wav(path, a)


# --------------------------------------------------------------------------
_EP = None
_SCENES = None


def _wrap(ctx, text, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if ctx.text_extents(trial).x_advance > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def draw_emote(ctx, kind, x, y, u):
    ctx.save()
    ctx.translate(x, y)
    s = max(0.02, min(1.0, u * 6))
    ctx.scale(s, s)
    if kind in ("!", "?", "!?"):
        text_center(ctx, kind, 0, 0, 160, hexc("#ffd23f" if kind == "!" else "#7cf5ff"), outline=(INK, 12))
    elif kind == "sweat":
        ctx.move_to(70, -120)
        ctx.curve_to(40, -70, 50, -40, 70, -40)
        ctx.curve_to(90, -40, 100, -70, 70, -120)
        fill_ink(ctx, hexc("#8fd8ff"), 5)
    elif kind == "heart":
        for dx in (-60, 60):
            ctx.save()
            ctx.translate(dx, -40 - 20 * math.sin(u * 6 + dx))
            ctx.move_to(0, 20)
            ctx.curve_to(-50, -20, -20, -60, 0, -30)
            ctx.curve_to(20, -60, 50, -20, 0, 20)
            fill_ink(ctx, hexc("#ff5c8a"), 5)
            ctx.restore()
    elif kind == "music":
        for i in range(3):
            ctx.save()
            ctx.translate(-60 + i * 60, -30 - i * 30 - 15 * math.sin(u * 7 + i))
            ellipse(ctx, 0, 0, 16, 12)
            col(ctx, INK)
            ctx.fill()
            ctx.rectangle(12, -60, 6, 60)
            ctx.fill()
            ctx.restore()
    elif kind == "anger":
        for a in range(4):
            ctx.save()
            ctx.rotate(a * math.pi / 2 + 0.3)
            path_poly(ctx, [(10, -10), (50, -14), (14, -50)], close=False)
            ctx.set_line_width(12)
            col(ctx, hexc("#ff3b3b"))
            ctx.stroke()
            ctx.restore()
    ctx.restore()


def draw_hat(ctx, kind, x, y):
    if kind == "burger":
        ellipse(ctx, x, y - 20, 70, 26)
        fill_ink(ctx, hexc("#e9b44c"), 5)
        ellipse(ctx, x, y - 6, 66, 14)
        col(ctx, hexc("#6d3b1f"))
        ctx.fill()
        ellipse(ctx, x, y + 4, 72, 10)
        col(ctx, hexc("#7cb342"))
        ctx.fill()
    elif kind == "soot":
        for dx in (-50, 0, 50):
            ctx.arc(x + dx, y - 10, 34, 0, TAU)
        col(ctx, hexc("#424242", 0.9))
        ctx.fill()


def render_frame(fi):
    ep = _EP
    fr = ep.frames[fi]
    t, cam, v = fr["t"], dict(fr["cam"]), fr["vars"]
    if v.get("quake", 0) > 0:
        cam["x"] += math.sin(t * 61) * 22 * v["quake"]
        cam["y"] += math.cos(t * 47) * 16 * v["quake"]
    scene = _SCENES[fr["scene"]]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    scene.draw_bg(ctx, cam, t, v)

    def actors(front):
        for s in sorted(fr["actors"], key=lambda s: s["z"]):
            if not s["visible"] or (s["z"] >= 0) != front:
                continue
            ch = ep.actors[s["name"]]["char"]
            ctx.save()
            apply_cam(ctx, cam)
            sc = getattr(ch, "scale", 1.0)
            ellipse(ctx, s["x"], 6, 120 * sc, 22 * sc)
            col(ctx, (0, 0, 0, 0.2 * max(0.0, 1 - s.get("lift", 0) / 600)))
            ctx.fill()
            ch.draw(ctx, s)
            if s.get("hat"):
                draw_hat(ctx, s["hat"], s["x"] + 4 * s["facing"], -ch.head_top(s) - s["jump"] + 28)
            ctx.restore()

    actors(False)
    scene.draw_fg(ctx, cam, t, v)
    actors(True)
    scene.draw_top(ctx, cam, t, v)
    for s in fr["actors"]:
        if s["emote"] and s["visible"]:
            ch = ep.actors[s["name"]]["char"]
            ctx.save()
            apply_cam(ctx, cam)
            draw_emote(ctx, s["emote"], s["x"] + 80 * s["facing"], -ch.head_top(s) - s["jump"] - 20,
                       t - s["emote_t"])
            ctx.restore()
    for f0, d, text, x, y, c, size, rot in ep.fx_texts:
        if f0 <= t <= f0 + d:
            u = t - f0
            ctx.save()
            ctx.translate(x, y)
            ctx.rotate(rot)
            sc = max(0.02, min(1.0, u * 8)) * (1 + 0.05 * math.sin(u * 20))
            ctx.scale(sc, sc)
            text_center(ctx, text, 0, 0, size, c, outline=(INK, 16))
            ctx.restore()
    if v.get("flash", 0) > 0:
        col(ctx, (1, 1, 1, min(1.0, v["flash"])))
        ctx.paint()
    overlay(ctx, ep, fr)
    return bytes(surf.get_data())


def overlay(ctx, ep, fr):
    t = fr["t"]
    if fr["scene"] != "intro":
        ctx.save()
        ctx.translate(1770, 70)
        text_center(ctx, "WOBBLES", 0, 0, 40, hexc("#ffffff", 0.75), outline=(hexc("#000000", 0.35), 6))
        ctx.restore()
    if fr["caption"]:
        who, text, u = fr["caption"]
        ctx.select_font_face("Fredoka", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(46)
        lines = _wrap(ctx, text, 1400)
        name, c = NAMES.get(who, (who.upper(), "#000000"))
        lh = 56
        bh = 30 + lh * len(lines)
        y0 = H - 40 - bh
        rrect(ctx, 240, y0, 1440, bh, 24)
        col(ctx, (0.05, 0.04, 0.08, 0.72))
        ctx.fill()
        if name:
            ctx.select_font_face("Luckiest Guy")
            ctx.set_font_size(34)
            e = ctx.text_extents(name)
            rrect(ctx, 270, y0 - 30, e.x_advance + 40, 48, 24)
            fill_ink(ctx, hexc(c), 4)
            ctx.move_to(290, y0 + 5)
            col(ctx, hexc("#ffffff"))
            ctx.show_text(name)
        ctx.select_font_face("Fredoka", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(46)
        for i, line in enumerate(lines):
            e = ctx.text_extents(line)
            ctx.move_to(W / 2 - e.x_advance / 2, y0 + 58 + i * lh - 6)
            col(ctx, hexc("#ffffff"))
            ctx.show_text(line)
    end0 = ep.total - 3.0
    if t > end0:
        u = t - end0
        col(ctx, (0.05, 0.03, 0.1, 0.75 * ease(u * 3)))
        ctx.paint()
        ctx.save()
        ctx.translate(W / 2, H / 2)
        s = max(0.02, ease(u * 4))
        ctx.scale(s, s)
        text_center(ctx, "THE WOBBLES", 0, -40, 170, hexc("#ffd23f"), outline=(INK, 18))
        text_center(ctx, ep.end_card, 0, 90, 64, hexc("#ffffff"), font="Fredoka", outline=(INK, 8))
        ctx.restore()


def render(ep, out_path, preview=None):
    global _EP, _SCENES
    _EP = ep
    _SCENES = {k: c() for k, c in SCENES.items()}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if preview is not None:
        for fi in preview:
            data = render_frame(fi)
            surf = cairo.ImageSurface.create_for_data(bytearray(data), cairo.FORMAT_ARGB32, W, H)
            surf.write_to_png(out_path.replace(".mp4", f"_f{fi}.png"))
        return
    wav = out_path.replace(".mp4", ".wav")
    ep.build_audio(wav)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "21",
           "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-c:a", "aac", "-ar", "44100",
           "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with mp.get_context("fork").Pool(os.cpu_count()) as pool:
        for i, data in enumerate(pool.imap(render_frame, range(len(ep.frames)), chunksize=4)):
            proc.stdin.write(data)
            if i % 300 == 0:
                print(f"  frame {i}/{len(ep.frames)}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
