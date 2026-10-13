"""Timeline DSL, simulation and renderer for MASK BUDDIES shorts."""
import copy
import math
import multiprocessing as mp
import os
import subprocess

import cairo
import numpy as np

import audio
from characters import CAST, INK, TAU, WALK_STYLES, col, ellipse, fill_ink, hexc, path_poly, rrect
from world import SCENES, H, W, apply_cam, text_center

FPS = 30
DEFAULT_CAM = {"x": 540.0, "y": -560.0, "z": 1.0}

NAME_COLORS = {
    "poly": hexc("#e84a7f"),
    "stitches": hexc("#6f86c9"),
    "ghosty": hexc("#7a7aa0"),
    "granny": hexc("#e2771a"),
    "quackers": hexc("#2f5fb3"),
    "pigeon": hexc("#5d7a8c"),
    "narrator": hexc("#5a4ea8"),
}
DISPLAY_NAMES = {
    "poly": "POLY", "stitches": "STITCHES", "ghosty": "GHOSTY", "granny": "GRANNY PUMPKIN",
    "quackers": "OFFICER QUACKERS", "pigeon": "PIGEON", "narrator": "",
}


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


class Episode:
    def __init__(self, number, title, scene, music, music_start=0.0, cam=None):
        self.number = number
        self.title = title
        self.scene_name = scene
        self.music = music
        self.music_start = music_start
        self.cursor = 0.0
        self.actors = {}       # name -> spec
        self.order = []
        self.cmds = []         # (t, actor, kind, kwargs)
        self.lines = []        # (t, speaker, text, audio)
        self.sfx_events = []
        self.cam_keys = []
        self.var_keys = []
        self.fx_texts = []
        self.props = []
        self.cam0 = dict(DEFAULT_CAM, **(cam or {}))
        self.vars0 = {}
        self.end_card = "MORE MASK BUDDIES SOON!"

    # ---- setup ------------------------------------------------------------
    def add(self, name, x, facing=1, z=0, kind=None, **state):
        char = CAST[kind or name]()
        self.actors[name] = dict(char=char, x=x, facing=facing, z=z, state=state)
        self.order.append(name)
        self.actors[name]["plan_x"] = x
        return self

    def var(self, name, value, at=None, dur=0.0):
        self.var_keys.append((self._at(at), dur, name, value))

    def _at(self, at):
        return self.cursor if at is None else at

    # ---- actions ----------------------------------------------------------
    def walk(self, name, to, speed=None, style=None, at=None, wait=False):
        a = self.actors[name]
        style = style or a["char"].default_style
        base = {"normal": 260, "stiff": 110, "run": 560, "sneak": 170, "shuffle": 95}[style]
        speed = speed or base
        t = self._at(at)
        dur = abs(to - a["plan_x"]) / speed
        self.cmds.append((t, name, "walk", dict(to=to, speed=speed, style=style)))
        a["plan_x"] = to
        if wait:
            self.cursor = t + dur
        return dur

    def say(self, name, text, gap=0.3, at=None, wait=True, speaker=None):
        clip = audio.tts(speaker or name, text)
        t = self._at(at)
        self.lines.append((t, name, text, clip))
        dur = len(clip) / audio.SR
        if wait:
            self.cursor = t + dur + gap
        return dur

    def wait(self, s):
        self.cursor += s

    def sfx(self, name, at=None, gain=1.0):
        self.sfx_events.append((self._at(at), name, gain))

    def do(self, name, kind, at=None, **kw):
        self.cmds.append((self._at(at), name, kind, kw))

    def face(self, name, d, at=None):
        self.do(name, "face", at, d=d)

    def arms(self, name, pose, at=None):
        self.do(name, "arms", at, pose=pose)

    def emote(self, name, kind, dur=1.5, at=None):
        self.do(name, "emote", at, emote=kind, dur=dur)

    def jump(self, name, h=160, dur=0.5, at=None):
        self.do(name, "jump", at, h=h, dur=dur)

    def shake(self, name, dur=1.0, amt=1.0, at=None):
        self.do(name, "shake", at, dur=dur, amt=amt)

    def setstate(self, name, at=None, **kw):
        self.do(name, "set", at, **kw)

    def cam(self, x=None, y=None, z=None, dur=0.8, at=None, follow=None, offset=0.0):
        self.cam_keys.append((self._at(at), dur, dict(x=x, y=y, z=z), follow, offset))

    def fx_text(self, text, x, y, dur=1.0, at=None, color="#ffd84a", size=110, rot=-0.08):
        self.fx_texts.append((self._at(at), dur, text, x, y, hexc(color), size, rot))

    def prop(self, kind, x, y, at=None, until=None):
        self.props.append((self._at(at), until, kind, x, y))

    # ---- simulation -------------------------------------------------------
    def build(self):
        self.total = self.cursor + 3.2
        nfr = int(self.total * FPS)
        dt = 1.0 / FPS
        cmds = sorted(self.cmds, key=lambda c: c[0])
        ci = 0
        st = {}
        for name in self.order:
            a = self.actors[name]
            ch = a["char"]
            s = dict(name=name, x=float(a["x"]), y=0.0, facing=a["facing"], phase=0.0, walkw=0.0,
                     style=ch.default_style, arms="swing", talk=0.0, shake=0.0, jump=0.0,
                     squash=0.0, emote=None, emote_t=0.0, t=0.0, z=a["z"], item=None,
                     arm_ang=None, visible=True)
            s.update(a["state"])
            s["_move"] = None
            s["_jump"] = None
            s["_shake"] = None
            s["_emote_until"] = -1
            s["_perch"] = None
            s["_fly"] = None
            st[name] = s

        # talk envelopes
        talk_tracks = []
        duck = []
        for t0, name, text, clip in self.lines:
            env = audio.envelope(clip, FPS)
            talk_tracks.append((t0, name, env))
            duck.append((t0 - 0.1, t0 + len(clip) / audio.SR + 0.15))

        cam = dict(self.cam0)
        cam_keys = sorted(self.cam_keys, key=lambda k: k[0])
        cam_from = dict(cam)
        vars_ = dict(self.vars0)
        var_from = {}
        steps = []
        frames = []
        active_cam = None
        for fi in range(nfr):
            t = fi * dt
            while ci < len(cmds) and cmds[ci][0] <= t + 1e-9:
                _, name, kind, kw = cmds[ci]
                s = st[name]
                if kind == "walk":
                    s["_move"] = kw
                    s["style"] = kw["style"]
                elif kind == "face":
                    s["facing"] = kw["d"]
                elif kind == "arms":
                    s["arms"] = kw["pose"]
                elif kind == "emote":
                    s["emote"] = kw["emote"]
                    s["emote_t"] = t
                    s["_emote_until"] = t + kw["dur"]
                elif kind == "jump":
                    s["_jump"] = (t, kw["h"], kw["dur"])
                elif kind == "shake":
                    s["_shake"] = (t, kw["dur"], kw["amt"])
                elif kind == "perch":
                    s["_perch"] = kw["on"]
                    s["_fly"] = None
                elif kind == "fly":
                    s["_fly"] = (t, kw["dur"], s["x"], s["y"], kw["x"], kw["y"], kw.get("then"))
                    s["_perch"] = None
                elif kind == "set":
                    s.update(kw)
                ci += 1

            for name in self.order:
                s = st[name]
                ch = self.actors[name]["char"]
                s["t"] = t
                mv = s["_move"]
                moving = False
                if s.get("frozen"):
                    mv = None
                if mv:
                    dx = mv["to"] - s["x"]
                    step = mv["speed"] * dt
                    if abs(dx) <= step:
                        s["x"] = mv["to"]
                        s["_move"] = None
                    else:
                        s["x"] += math.copysign(step, dx)
                        s["facing"] = 1 if dx > 0 else -1
                    moving = True
                    stride = 110 * WALK_STYLES[s["style"]][3] * getattr(ch, "scale", 1.0)
                    old = s["phase"]
                    s["phase"] += min(step, abs(dx)) / stride * math.pi
                    if int(old // math.pi) != int(s["phase"] // math.pi) and name not in ("ghosty", "pigeon"):
                        steps.append(t)
                target_w = 1.0 if moving else 0.0
                if not s.get("frozen"):
                    s["walkw"] += (target_w - s["walkw"]) * min(1.0, dt * (9 if moving else 7))
                # jump
                s["jump"], s["squash"] = 0.0, 0.0
                if s["_jump"]:
                    j0, h, d = s["_jump"]
                    u = (t - j0) / d
                    if u <= 1:
                        s["jump"] = h * 4 * u * (1 - u)
                        s["squash"] = -0.08 * math.sin(u * math.pi)
                    elif u <= 1.35:
                        s["squash"] = 0.12 * math.sin((u - 1) / 0.35 * math.pi)
                    else:
                        s["_jump"] = None
                s["shake"] = 0.0
                if s["_shake"]:
                    s0, d, amt = s["_shake"]
                    if t - s0 <= d:
                        s["shake"] = amt
                    else:
                        s["_shake"] = None
                if s["emote"] and t > s["_emote_until"]:
                    s["emote"] = None
                # flying / perching (pigeon)
                if s["_fly"]:
                    f0, d, x0, y0, x1, y1, then = s["_fly"]
                    u = min(1.0, (t - f0) / d)
                    s["x"] = x0 + (x1 - x0) * ease(u)
                    s["y"] = y0 + (y1 - y0) * ease(u) - math.sin(u * math.pi) * 120
                    s["facing"] = 1 if x1 >= x0 else -1
                    s["flying"] = True
                    if u >= 1:
                        s["_fly"] = None
                        s["flying"] = False
                        if then:
                            s["_perch"] = then
                elif s["_perch"]:
                    host = st[s["_perch"]]
                    hch = self.actors[s["_perch"]]["char"]
                    s["x"] = host["x"] + math.sin(t * 70) * 7 * host["shake"]
                    s["y"] = -hch.head_top(host) - host["jump"] + 14
                    s["flying"] = False
                # talking
                s["talk"] = 0.0
                for t0, who, env in talk_tracks:
                    if who == name:
                        i = int((t - t0) * FPS)
                        if 0 <= i < len(env):
                            s["talk"] = max(s["talk"], float(env[i]))
                # smooth arms
                tgt = ch.arm_targets(s)
                if s["arm_ang"] is None:
                    s["arm_ang"] = tuple(tgt)
                else:
                    k = min(1.0, dt * 12)
                    s["arm_ang"] = tuple(a + (b - a) * k for a, b in zip(s["arm_ang"], tgt))

            # camera
            for key in cam_keys:
                if key[0] <= t + 1e-9 and (active_cam is None or key[0] > active_cam[0][0]):
                    active_cam = (key, dict(cam))
            if active_cam:
                (k0, kd, tgt, follow, off), start = active_cam
                u = ease((t - k0) / kd) if kd > 0 else 1.0
                for ax in ("y", "z"):
                    if tgt[ax] is not None:
                        cam[ax] = start[ax] + (tgt[ax] - start[ax]) * u
                if follow:
                    goal = st[follow]["x"] + off
                    cam["x"] += (goal - cam["x"]) * min(1.0, dt * 3.5)
                elif tgt["x"] is not None:
                    cam["x"] = start["x"] + (tgt["x"] - start["x"]) * u

            # vars
            for vt, vd, vn, vv in self.var_keys:
                if vt <= t:
                    if isinstance(vv, (int, float)) and vd > 0:
                        if (vt, vn) not in var_from:
                            var_from[(vt, vn)] = vars_.get(vn, 0.0)
                        u = ease((t - vt) / vd)
                        vars_[vn] = var_from[(vt, vn)] + (vv - var_from[(vt, vn)]) * u
                    else:
                        vars_[vn] = vv

            caption = None
            for t0, who, text, clip in self.lines:
                if t0 - 0.05 <= t <= t0 + len(clip) / audio.SR + 0.25:
                    caption = (who, text, t - t0)
            frames.append(dict(
                t=t,
                cam=dict(cam),
                vars=dict(vars_),
                actors=[{k: v for k, v in st[n].items() if not k.startswith("_")} for n in self.order],
                caption=caption,
            ))
        self.frames = frames
        self.steps = steps
        self.duck = duck
        return self

    # ---- audio ------------------------------------------------------------
    def build_audio(self, path):
        music = audio.load_music(self.music, self.music_start, self.total)
        a = audio.mix(self.total, [(t, c) for t, _, _, c in self.lines], self.sfx_events,
                      self.steps, music, self.duck)
        audio.write_wav(path, a)


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

_EP = None
_SCENE = None


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


def draw_emote(ctx, kind, x, y, s, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    pop = max(0.02, min(1.0, t * 6))
    ctx.scale(pop, pop)
    if kind == "!":
        text_center(ctx, "!", 0, 0, 150, hexc("#ffd84a"), outline=(INK, 12))
    elif kind == "?":
        text_center(ctx, "?", 0, 0, 150, hexc("#7cf5ff"), outline=(INK, 12))
    elif kind == "!?":
        text_center(ctx, "!?", 0, 0, 140, hexc("#ff6b6b"), outline=(INK, 12))
    elif kind == "sweat":
        ctx.move_to(70, -120)
        ctx.curve_to(40, -70, 50, -40, 70, -40)
        ctx.curve_to(90, -40, 100, -70, 70, -120)
        fill_ink(ctx, hexc("#8fd8ff"), 5)
    elif kind == "heart":
        for dx in (-70, 70):
            ctx.save()
            ctx.translate(dx, -40 - 20 * math.sin(t * 6 + dx))
            ctx.move_to(0, 20)
            ctx.curve_to(-50, -20, -20, -60, 0, -30)
            ctx.curve_to(20, -60, 50, -20, 0, 20)
            fill_ink(ctx, hexc("#ff5c8a"), 5)
            ctx.restore()
    elif kind == "zzz":
        for i in range(3):
            text_center(ctx, "z", 40 + i * 40, -20 - i * 50 - 10 * math.sin(t * 3 + i),
                        60 + i * 20, hexc("#ffffff"), outline=(INK, 8))
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


def draw_prop(ctx, kind, x, y, t):
    ctx.save()
    ctx.translate(x, y)
    pop = max(0.02, min(1.0, t * 7))
    ctx.scale(pop, pop)
    if kind == "muffin":
        path_poly(ctx, [(-40, 0), (40, 0), (50, -50), (-50, -50)])
        fill_ink(ctx, hexc("#d98b4a"), 5)
        ellipse(ctx, 0, -60, 58, 34)
        fill_ink(ctx, hexc("#5a7bd8"), 5)
    elif kind == "cup":
        rrect(ctx, -34, -80, 68, 80, 10)
        fill_ink(ctx, hexc("#ffffff"), 5)
        ctx.rectangle(-34, -55, 68, 22)
        col(ctx, hexc("#8a5a3b"))
        ctx.fill()
    elif kind == "squarecup":
        ctx.rectangle(-40, -80, 80, 80)
        fill_ink(ctx, hexc("#ffffff"), 5)
        text_center(ctx, "90", 0, -28, 34, hexc("#e84a7f"))
    elif kind == "coins":
        for i in range(4):
            ellipse(ctx, (i % 2) * 20 - 10, -i * 16, 34, 12)
            fill_ink(ctx, hexc("#ffd23f"), 4)
    elif kind == "pie":
        ellipse(ctx, 0, -20, 90, 30)
        fill_ink(ctx, hexc("#e8a33d"), 5)
        ellipse(ctx, 0, -28, 70, 18)
        col(ctx, hexc("#c2602a"))
        ctx.fill()
    elif kind == "nest":
        ellipse(ctx, 0, -10, 70, 24)
        fill_ink(ctx, hexc("#8a6a3b"), 5)
        ctx.set_line_width(3)
        col(ctx, hexc("#5e4524"))
        for i in range(8):
            ctx.move_to(-60 + i * 15, -20)
            ctx.line_to(-50 + i * 15, 4)
        ctx.stroke()
    ctx.restore()


def render_frame(fi):
    ep, scene = _EP, _SCENE
    fr = ep.frames[fi]
    t, cam, v = fr["t"], fr["cam"], fr["vars"]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    scene.draw_bg(ctx, cam, t, v)

    def draw_actors(layer):
        for s in sorted(fr["actors"], key=lambda s: s["z"]):
            if not s["visible"] or (s["z"] < 0) != (layer < 0):
                continue
            ch = ep.actors[s["name"]]["char"]
            ctx.save()
            apply_cam(ctx, cam)
            if s["name"] != "pigeon" or not s.get("flying"):
                sc = getattr(ch, "scale", 1.0)
                if s["name"] != "pigeon":
                    ellipse(ctx, s["x"], 6, 110 * sc * (1 - min(0.5, s["jump"] / 400)), 22 * sc)
                    col(ctx, (0, 0, 0, 0.22))
                    ctx.fill()
            ch.draw(ctx, s)
            if s.get("hat"):
                draw_prop(ctx, s["hat"], s["x"], -ch.head_top(s) - s["jump"] + 22, t - s.get("hat_t", 0))
            ctx.restore()

    draw_actors(-1)
    scene.draw_fg(ctx, cam, t, v)
    draw_actors(1)

    # props (world space)
    for p0, until, kind, x, y in ep.props:
        if p0 <= t and (until is None or t < until):
            ctx.save()
            apply_cam(ctx, cam)
            draw_prop(ctx, kind, x, y, t - p0)
            ctx.restore()

    # emotes above heads
    for s in fr["actors"]:
        if s["emote"] and s["visible"]:
            ch = ep.actors[s["name"]]["char"]
            ctx.save()
            apply_cam(ctx, cam)
            draw_emote(ctx, s["emote"], s["x"] + 70 * s["facing"],
                       -ch.head_top(s) - s["jump"] - 20, 1.0, t - s["emote_t"])
            ctx.restore()

    # comic sfx words
    for f0, d, text, x, y, c, size, rot in ep.fx_texts:
        if f0 <= t <= f0 + d:
            u = (t - f0)
            ctx.save()
            ctx.translate(x, y)
            ctx.rotate(rot)
            sc = max(0.02, min(1.0, u * 8)) * (1 + 0.05 * math.sin(u * 20))
            ctx.scale(sc, sc)
            text_center(ctx, text, 0, 0, size, c, outline=(INK, 14))
            ctx.restore()

    draw_overlay(ctx, ep, fr)
    return bytes(surf.get_data())


def draw_overlay(ctx, ep, fr):
    t = fr["t"]
    # logo pill
    rrect(ctx, 40, 50, 420, 86, 43)
    col(ctx, (0.08, 0.06, 0.12, 0.65))
    ctx.fill()
    text_center(ctx, "MASK BUDDIES", 250, 112, 52, hexc("#ffd84a"))
    rrect(ctx, 790, 54, 250, 78, 39)
    col(ctx, (0.08, 0.06, 0.12, 0.65))
    ctx.fill()
    text_center(ctx, f"EP. {ep.number}", 915, 110, 46, hexc("#ffffff"))

    # caption
    if fr["caption"]:
        who, text, u = fr["caption"]
        ctx.select_font_face("Fredoka", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(58)
        lines = _wrap(ctx, text, 880)
        lh = 70
        bh = 70 + lh * len(lines) + 20
        y0 = 1590 - bh / 2 + 60
        pop = 0.9 + 0.1 * ease(u * 6)
        ctx.save()
        ctx.translate(540, y0 + bh / 2)
        ctx.scale(pop, pop)
        ctx.translate(-540, -(y0 + bh / 2))
        rrect(ctx, 50, y0, 980, bh, 36)
        col(ctx, (1, 1, 1, 0.94))
        ctx.fill_preserve()
        col(ctx, INK)
        ctx.set_line_width(7)
        ctx.stroke()
        name = DISPLAY_NAMES.get(who, who.upper())
        if name:
            ctx.select_font_face("Luckiest Guy")
            ctx.set_font_size(44)
            e = ctx.text_extents(name)
            rrect(ctx, 80, y0 - 34, e.x_advance + 50, 64, 32)
            fill_ink(ctx, NAME_COLORS.get(who, INK), 6)
            ctx.move_to(105, y0 + 14)
            col(ctx, hexc("#ffffff"))
            ctx.show_text(name)
        ctx.select_font_face("Fredoka", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(58)
        for i, line in enumerate(lines):
            e = ctx.text_extents(line)
            ctx.move_to(540 - e.x_advance / 2, y0 + 92 + i * lh)
            col(ctx, INK)
            ctx.show_text(line)
        ctx.restore()

    # title card
    if t < 2.6:
        a = 1.0 if t < 2.1 else 1 - (t - 2.1) / 0.5
        ctx.save()
        col(ctx, (0.05, 0.03, 0.1, 0.55 * a))
        ctx.paint()
        bounce = 1 + 0.15 * math.exp(-t * 5) * math.sin(t * 18)
        ctx.translate(540, 880)
        ctx.scale(bounce * (0.6 + 0.4 * ease(t * 4)), bounce * (0.6 + 0.4 * ease(t * 4)))
        ctx.push_group()
        rrect(ctx, -470, -260, 940, 470, 60)
        fill_ink(ctx, hexc("#fff3d6"), 12)
        text_center(ctx, "MASK", 0, -110, 150, hexc("#e84a7f"), outline=(INK, 14))
        text_center(ctx, "BUDDIES", 0, 40, 150, hexc("#33405e"), outline=(INK, 14))
        text_center(ctx, f"Ep. {ep.number}: {ep.title}", 0, 150, 58, hexc("#5a4ea8"))
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        ctx.restore()

    # end card
    end0 = ep.total - 2.8
    if t > end0:
        u = t - end0
        ctx.save()
        col(ctx, (0.05, 0.03, 0.1, 0.6 * ease(u * 3)))
        ctx.paint()
        ctx.translate(540, 900)
        s = max(0.02, ease(u * 4))
        ctx.scale(s, s)
        rrect(ctx, -460, -230, 920, 420, 60)
        fill_ink(ctx, hexc("#fff3d6"), 12)
        text_center(ctx, "MASK BUDDIES", 0, -90, 110, hexc("#e84a7f"), outline=(INK, 12))
        text_center(ctx, ep.end_card, 0, 40, 54, hexc("#33405e"))
        text_center(ctx, "FOLLOW FOR MORE!", 0, 130, 60, hexc("#5a4ea8"))
        ctx.restore()


def render(ep, out_path, workers=None, preview_frames=None):
    global _EP, _SCENE
    _EP = ep
    _SCENE = SCENES[ep.scene_name]()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if preview_frames is not None:
        for fi in preview_frames:
            data = render_frame(fi)
            surf = cairo.ImageSurface.create_for_data(bytearray(data), cairo.FORMAT_ARGB32, W, H)
            surf.write_to_png(out_path.replace(".mp4", f"_f{fi}.png"))
        return
    wav = out_path.replace(".mp4", ".wav")
    ep.build_audio(wav)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "21",
           "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-c:a", "aac", "-ar", "44100", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
           out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ctxmp = mp.get_context("fork")
    with ctxmp.Pool(workers or os.cpu_count()) as pool:
        for i, data in enumerate(pool.imap(render_frame, range(len(ep.frames)), chunksize=4)):
            proc.stdin.write(data)
            if i % 150 == 0:
                print(f"  frame {i}/{len(ep.frames)}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
