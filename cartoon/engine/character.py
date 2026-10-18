"""Vector cartoon character rig.

Everything is drawn in a local frame facing +x with the feet at y=0 (y grows down),
then mirrored/scaled into the world.  Legs use 2-bone IK with feet planted in world
space while walking (no foot sliding); arms use poses (shoulder, elbow angles) that
can be blended with IK reaches (e.g. "pinch the nose", "hand under the tap").

Angle convention for limbs: degrees from straight down, positive = towards the
character's front.
"""
import math

from .anim import Track, clamp, smooth

OUTLINE = (0.16, 0.12, 0.19)
OW = 6.0  # outline width

# rig dimensions (local units, before character scale)
HIP_H = 326
THIGH, SHIN, ANKLE_H = 150, 148, 30
TORSO = 228
UPPER, FORE = 118, 112
HALF_STRIDE = 160
LIFT = 52
HEAD_RX, HEAD_RY = 118, 124
FX = 22  # how far the face is turned towards the front (3/4 view)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def shade(c, k):
    return tuple(clamp(v * k) for v in c)


def rad(d):
    return d * math.pi / 180


def dirv(a_deg):
    a = rad(a_deg)
    return math.sin(a), math.cos(a)


def rot(p, pivot, deg):
    """Rotate p about pivot by deg (cairo convention: positive = clockwise on screen)."""
    a = rad(deg)
    c, s = math.cos(a), math.sin(a)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return pivot[0] + x * c - y * s, pivot[1] + x * s + y * c


def ik2(root, target, l1, l2, prefer):
    """2-bone IK. Returns the middle joint. prefer(candidate_a, candidate_b) -> chosen."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = math.hypot(dx, dy)
    d = clamp(d, abs(l1 - l2) + 1e-3, (l1 + l2) * 0.999)
    base = math.atan2(dy, dx)
    a = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    c1 = (root[0] + l1 * math.cos(base + a), root[1] + l1 * math.sin(base + a))
    c2 = (root[0] + l1 * math.cos(base - a), root[1] + l1 * math.sin(base - a))
    return prefer(c1, c2)


def angle_of(p, q):
    """Limb angle (our convention) of the vector p->q."""
    return math.degrees(math.atan2(q[0] - p[0], q[1] - p[1]))


def limb(ctx, pts, width, color, outline=OUTLINE, ow=OW):
    ctx.set_line_cap(1)  # round
    ctx.set_line_join(1)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.set_source_rgb(*outline)
    ctx.set_line_width(width + 2 * ow)
    ctx.stroke_preserve()
    ctx.set_source_rgb(*color)
    ctx.set_line_width(width)
    ctx.stroke()


def fill_stroke(ctx, color, outline=OUTLINE, ow=OW):
    ctx.set_source_rgb(*color)
    ctx.fill_preserve()
    ctx.set_source_rgb(*outline)
    ctx.set_line_width(ow)
    ctx.stroke()


def ellipse(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(rx, ry)
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


# ---------------------------------------------------------------- hands
# curls per finger (index, middle, ring, pinky), spread multiplier, (thumb angle, thumb curl)
HANDS = {
    "open": ([0.05, 0.05, 0.08, 0.1], 1.5, (-1.15, 0.0)),
    "relaxed": ([0.5, 0.6, 0.68, 0.75], 1.0, (-0.75, 0.3)),
    "fist": ([2.3, 2.35, 2.35, 2.3], 0.35, (-0.25, 0.95)),
    "point": ([0.0, 2.3, 2.35, 2.3], 0.4, (-0.35, 0.85)),
    "thumbsup": ([2.3, 2.35, 2.35, 2.3], 0.35, (-1.57, 0.0)),
    "pinch": ([0.75, 2.0, 2.2, 2.3], 0.5, (-0.45, 0.55)),
    "hold": ([1.15, 1.25, 1.3, 1.35], 0.7, (-0.95, 0.15)),
}
FINGER_BASE_Y = [-13, -4, 5, 13]
FINGER_LEN = [27, 30, 28, 22]
FINGER_SPREAD = [-0.16, -0.03, 0.1, 0.24]


def draw_hand(ctx, wrist, fore_deg, shape, skin):
    curls, spread, (th_a, th_c) = HANDS.get(shape, HANDS["relaxed"])
    fx, fy = dirv(fore_deg)
    theta = math.atan2(fy, fx)
    ctx.save()
    ctx.translate(*wrist)
    ctx.rotate(theta)
    ctx.scale(1.12, 1.12)
    fist_like = sum(curls) / 4 > 1.4

    def fingers():
        for i in (3, 2, 1, 0):
            c = curls[i]
            L = FINGER_LEN[i]
            b = (27, FINGER_BASE_Y[i])
            a1 = FINGER_SPREAD[i] * spread - c * 0.8
            a2 = FINGER_SPREAD[i] * spread - c * 1.75
            p1 = (b[0] + L * 0.55 * math.cos(a1), b[1] + L * 0.55 * math.sin(a1))
            p2 = (p1[0] + L * 0.45 * math.cos(a2), p1[1] + L * 0.45 * math.sin(a2))
            limb(ctx, [b, p1, p2], 12.5, skin, ow=4.5)

    def palm():
        ellipse(ctx, 15, 0, 21, 21)
        fill_stroke(ctx, skin, ow=4.5)

    if fist_like:
        palm()
        fingers()
    else:
        fingers()
        palm()
    # thumb
    b = (15, -15)
    a1 = th_a + th_c * 0.7
    a2 = th_a + th_c * 1.6
    p1 = (b[0] + 13 * math.cos(a1), b[1] + 13 * math.sin(a1))
    p2 = (p1[0] + 12 * math.cos(a2), p1[1] + 12 * math.sin(a2))
    limb(ctx, [b, p1, p2], 13, skin, ow=4.5)
    ctx.restore()


# ---------------------------------------------------------------- expressions
EXPR = {
    "neutral": dict(lift=0, inner=0, lid=0.12, mouth="smile", pupil=1.0),
    "happy": dict(lift=6, inner=-2, lid=0.22, mouth="grin", pupil=1.0),
    "shocked": dict(lift=20, inner=5, lid=0.0, mouth="o", pupil=0.62),
    "worried": dict(lift=6, inner=12, lid=0.1, mouth="frown", pupil=0.9),
    "pain": dict(lift=-4, inner=10, lid=1.0, mouth="teeth", pupil=1.0, squeeze=True),
    "stern": dict(lift=-6, inner=-12, lid=0.28, mouth="flat", pupil=0.95),
    "smug": dict(lift=4, inner=-5, lid=0.45, mouth="smirk", pupil=1.0),
    "relieved": dict(lift=5, inner=7, lid=1.0, mouth="smile", pupil=1.0, arcs=True),
    "silly": dict(lift=10, inner=0, lid=0.05, mouth="grin", pupil=1.15),
}


class Character:
    def __init__(self, name, look, x, facing=1, scale=1.0, z=0):
        self.name = name
        self.look = {k: (hexrgb(v) if isinstance(v, str) and v.startswith("#") else v) for k, v in look.items()}
        self.s = scale
        self.z = z
        self.tr = {
            "x": Track(float(x)), "y": Track(0.0), "face": Track(float(facing)),
            "lean": Track(0.0), "tilt": Track(0.0), "crouch": Track(0.0),
            "armF": Track((5.0, 12.0)), "armB": Track((-5.0, 12.0)),
            "handF": Track("relaxed"), "handB": Track("relaxed"),
            "reachF": Track(None), "reachB": Track(None),
            "reachFw": Track(0.0), "reachBw": Track(0.0),
            "swing": Track(1.0), "expr": Track("neutral"), "look": Track((0.0, 0.0)),
            "sqx": Track(1.0), "sqy": Track(1.0), "bleed": Track(0.0), "visible": Track(1.0),
            "shake": Track(0.0), "blush": Track(0.0),
        }
        self.frames = []
        self.steps = []
        self.joints = {}
        self.mouth = lambda t: (0.0, 0.0)
        self.blink_seed = sum(map(ord, name)) * 0.37

    def __getitem__(self, k):
        return self.tr[k]

    # convenience authoring --------------------------------------------------
    def walk_to(self, t0, x, speed=300.0, ease="smooth"):
        x0 = self.tr["x"].at(t0)
        dur = max(0.2, abs(x - x0) / speed)
        if x != x0:
            self.tr["face"].to(t0, t0 + 0.12, 1.0 if x > x0 else -1.0, "linear")
        self.tr["x"].to(t0, t0 + dur, float(x), ease)
        return t0 + dur

    def turn(self, t, facing):
        self.tr["face"].to(t, t + 0.14, float(facing), "linear")

    def pose(self, t, armF=None, armB=None, handF=None, handB=None, dur=0.25, ease="back", swing=None):
        if armF is not None:
            self.tr["armF"].to(t, t + dur, tuple(map(float, armF)), ease)
        if armB is not None:
            self.tr["armB"].to(t, t + dur, tuple(map(float, armB)), ease)
        if handF is not None:
            self.tr["handF"].set(t + dur * 0.4, handF)
        if handB is not None:
            self.tr["handB"].set(t + dur * 0.4, handB)
        if swing is not None:
            self.tr["swing"].to(t, t + dur, float(swing))

    def rest(self, t, dur=0.3):
        self.pose(t, (5, 12), (-5, 12), "relaxed", "relaxed", dur, "inout", swing=1.0)

    def reach(self, t, side, target, dur=0.3, hand=None):
        """side 'F' or 'B'; target 'nose' or a world point (x, y); None releases."""
        w = self.tr["reach" + side + "w"]
        if target is None:
            w.to(t, t + dur, 0.0)
        else:
            self.tr["reach" + side].set(t, target)
            w.to(t, t + dur, 1.0, "inout")
        if hand:
            self.tr["hand" + side].set(t + dur * 0.5, hand)

    def expr(self, t, e):
        self.tr["expr"].set(t, e)

    def hop(self, t, height=90, dur=0.38):
        y = self.tr["y"]
        y.to(t, t + dur / 2, -float(height), "out")
        y.to(t + dur / 2, t + dur, 0.0, "in")
        self.tr["sqy"].to(t + dur - 0.02, t + dur + 0.06, 0.86, "out")
        self.tr["sqy"].to(t + dur + 0.06, t + dur + 0.22, 1.0, "back")
        self.tr["sqx"].to(t + dur - 0.02, t + dur + 0.06, 1.1, "out")
        self.tr["sqx"].to(t + dur + 0.06, t + dur + 0.22, 1.0, "back")
        return t + dur

    # simulation -------------------------------------------------------------
    def simulate(self, fps, n):
        """Integrate walk phase frame by frame (needed for planted feet + footstep sounds)."""
        dt = 1.0 / fps
        phase, w = 0.0, 0.0
        moving = False
        x_prev = self.tr["x"].at(0)
        self.frames, self.steps = [], []
        for i in range(n):
            t = i * dt
            x = self.tr["x"].at(t)
            dx = x - x_prev
            x_prev = x
            v = abs(dx) / dt
            target = clamp(v / 120.0)
            w += (target - w) * min(1.0, dt * 12)
            stride = HALF_STRIDE * (1 + 0.2 * clamp((v - 320) / 500))
            old = phase
            phase += abs(dx) / (2 * stride * self.s)
            if w > 0.3 and int(old * 2) != int(phase * 2):
                self.steps.append(dict(t=t, x=x, speed=v, w=w, foot=int(phase * 2) % 2, who=self.name))
                moving = True
            elif moving and w < 0.25:  # the last foot settles when we stop
                self.steps.append(dict(t=t, x=x, speed=150.0, w=0.6, foot=0, who=self.name))
                moving = False
            # when we stop, ease the phase to a neutral (feet together) value
            if w < 0.02:
                phase = round(phase * 2) / 2 if abs(phase * 2 - round(phase * 2)) < 0.02 else phase
            self.frames.append((phase, w, v))

    # geometry ---------------------------------------------------------------
    def _leg_target(self, p, w, side_x, air):
        if p < 0.5:
            u = p / 0.5
            fx = HALF_STRIDE / 2 - HALF_STRIDE * u
            fy = 0.0
            ang = 12 * (1 - smooth(u / 0.18)) - 24 * smooth((u - 0.72) / 0.28)
        else:
            u = (p - 0.5) / 0.5
            e = smooth(u)
            fx = -HALF_STRIDE / 2 + HALF_STRIDE * e
            fy = -LIFT * math.sin(math.pi * u)
            ang = -24 * (1 - smooth(u / 0.4)) + 12 * smooth((u - 0.6) / 0.4)
        sx, sy, sa = side_x, 0.0, 0.0
        x = sx + (fx * 1.0 - sx) * w
        y = sy + (fy - sy) * w
        a = sa + (ang - sa) * w
        y -= 38 * air
        return (x, -ANKLE_H + y), a

    def _world(self, p, st):
        return (st["X"] + st["fs"] * p[0], st["G"] + st["Y"] + st["sy"] * p[1])

    def _arm(self, t, side, shoulder, st, walk_swing):
        ang = self.tr["arm" + side].at(t)
        s_a, e_a = ang[0] + walk_swing, ang[1] + abs(walk_swing) * 0.4
        elbow = (shoulder[0] + UPPER * dirv(s_a)[0], shoulder[1] + UPPER * dirv(s_a)[1])
        fore = s_a + e_a
        wrist = (elbow[0] + FORE * dirv(fore)[0], elbow[1] + FORE * dirv(fore)[1])
        rw = self.tr["reach" + side + "w"].at(t)
        target = self.tr["reach" + side].at(t)
        if rw > 0.001 and target is not None:
            tgt = self._resolve_target(target, st)
            el = ik2(shoulder, tgt, UPPER, FORE, lambda a, b: a if a[1] > b[1] else b)
            s_ik = angle_of(shoulder, el)
            f_ik = angle_of(el, tgt)
            s2 = s_a + (s_ik - s_a) * rw
            f2 = fore + (f_ik - fore) * rw
            elbow = (shoulder[0] + UPPER * dirv(s2)[0], shoulder[1] + UPPER * dirv(s2)[1])
            fore = f2
            wrist = (elbow[0] + FORE * dirv(fore)[0], elbow[1] + FORE * dirv(fore)[1])
        return elbow, wrist, fore

    def _resolve_target(self, target, st):
        if target == "nose":
            n = st["nose_t"]
            return (n[0] - 14, n[1] + 46)
        if target == "mouth":
            n = st["mouth_t"]
            return (n[0] - 6, n[1] + 40)
        # world point -> local -> torso frame
        lx = (target[0] - st["X"]) / (st["fs"] if abs(st["fs"]) > 1e-3 else 1e-3)
        ly = (target[1] - st["G"] - st["Y"]) / st["sy"]
        return rot((lx, ly), st["hip"], -st["lean"])

    # drawing ----------------------------------------------------------------
    def draw(self, ctx, fi, t, ground_y):
        tr = self.tr
        if tr["visible"].at(t) < 0.5:
            return
        L = self.look
        phase, w, v = self.frames[min(fi, len(self.frames) - 1)]
        X = tr["x"].at(t)
        Y = tr["y"].at(t)
        shake = tr["shake"].at(t)
        if shake:
            X += shake * 9 * math.sin(t * 71)
        face = tr["face"].at(t)
        sqx, sqy = tr["sqx"].at(t), tr["sqy"].at(t)
        s = self.s
        st = dict(X=X, Y=Y, G=ground_y, fs=face * s * sqx, sy=s * sqy)
        air = clamp(-Y / 60.0)
        lean = tr["lean"].at(t) + w * 4
        tilt = tr["tilt"].at(t)
        crouch = tr["crouch"].at(t)
        bob = 7 * 0.5 * (1 + math.cos(4 * math.pi * phase)) * w
        breathe = math.sin(t * 2 * math.pi / 3.1 + self.blink_seed) * 2.0
        hip = (0.0, -HIP_H + bob + crouch * 70 + 4 + 12 * w)
        st["hip"], st["lean"] = hip, lean

        # torso frame points
        neck = (6.0, hip[1] - TORSO - 6 + breathe * 0.3)
        sh_y = hip[1] - TORSO + 24 + breathe * 0.3
        shF, shB = (12.0, sh_y), (-14.0, sh_y)
        head_c = rot((neck[0] + 4, neck[1] - 110), neck, -tilt)
        nose_h = (FX + 52, 26)
        st["nose_t"] = rot((neck[0] + 4 + nose_h[0], neck[1] - 110 + nose_h[1]), neck, -tilt)
        st["mouth_t"] = rot((neck[0] + 4 + FX + 18, neck[1] - 110 + 70), neck, -tilt)

        # walk arm swing
        pF = phase % 1.0
        sw = 26 * w * tr["swing"].at(t)
        swingF = -sw * math.cos(2 * math.pi * pF)
        swingB = sw * math.cos(2 * math.pi * pF)

        elbF, wrF, foreF = self._arm(t, "F", shF, st, swingF)
        elbB, wrB, foreB = self._arm(t, "B", shB, st, swingB)

        # legs (local frame, not leaned)
        hipF, hipB = (10.0, hip[1]), (-12.0, hip[1])
        ankF, aF = self._leg_target(pF, w, 20.0, air)
        ankB, aB = self._leg_target((phase + 0.5) % 1.0, w, -16.0, air)
        ankF = (ankF[0] + 10, ankF[1])
        ankB = (ankB[0] - 12, ankB[1])
        knee_pick = lambda a, b: a if a[0] > b[0] else b
        kneeF = ik2(hipF, ankF, THIGH, SHIN, knee_pick)
        kneeB = ik2(hipB, ankB, THIGH, SHIN, knee_pick)

        # world joints for props
        to_local = lambda p: rot(p, hip, lean)
        self.joints = {
            "handF": self._world(to_local(wrF), st), "handB": self._world(to_local(wrB), st),
            "nose": self._world(to_local(st["nose_t"]), st), "head": self._world(to_local(head_c), st),
            "foreF": foreF, "chest": self._world(to_local((10, hip[1] - 150)), st),
        }

        ctx.save()
        # ground shadow
        ctx.save()
        ctx.translate(X, ground_y + 4)
        k = 1 - 0.45 * clamp(-Y / 200)
        ctx.scale(110 * s * k, 17 * s * k)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.set_source_rgba(0.1, 0.05, 0.12, 0.2)
        ctx.fill()
        ctx.restore()

        ctx.translate(X, ground_y + Y)
        ctx.scale(face * s * sqx, s * sqy)

        dark = 0.84
        skin = L["skin"]
        # back arm (behind everything)
        ctx.save()
        ctx.translate(*hip)
        ctx.rotate(rad(lean))
        ctx.translate(-hip[0], -hip[1])
        self._draw_arm(ctx, shB, elbB, wrB, foreB, tr["handB"].at(t), dark)
        ctx.restore()
        # legs
        self._draw_leg(ctx, hipB, kneeB, ankB, aB, dark)
        self._draw_leg(ctx, hipF, kneeF, ankF, aF, 1.0)
        # upper body
        ctx.save()
        ctx.translate(*hip)
        ctx.rotate(rad(lean))
        ctx.translate(-hip[0], -hip[1])
        self._draw_torso(ctx, hip, breathe)
        ctx.save()
        ctx.translate(*neck)
        ctx.rotate(rad(-tilt))
        ctx.translate(-neck[0], -neck[1])
        limb(ctx, [(neck[0], neck[1] + 10), (neck[0] + 2, neck[1] - 30)], 40, skin)
        self._draw_head(ctx, (neck[0] + 4, neck[1] - 110), t)
        ctx.restore()
        self._draw_arm(ctx, shF, elbF, wrF, foreF, tr["handF"].at(t), 1.0)
        ctx.restore()
        ctx.restore()

    def _draw_leg(self, ctx, hip, knee, ank, foot_ang, k):
        L = self.look
        limb(ctx, [hip, knee, ank], L.get("leg_w", 46), shade(L["pants"], k))
        if L.get("socks"):
            limb(ctx, [((knee[0] * 0.25 + ank[0] * 0.75), (knee[1] * 0.25 + ank[1] * 0.75)), ank], 34, shade(L["socks"], k))
        ctx.save()
        ctx.translate(*ank)
        ctx.rotate(rad(-foot_ang))
        shoe = shade(L["shoe"], k)
        ctx.move_to(-22, -14)
        ctx.curve_to(-6, -22, 18, -16, 30, -8)
        ctx.curve_to(50, 0, 58, 12, 56, 22)
        ctx.curve_to(56, 30, 50, 31, 44, 31)
        ctx.line_to(-20, 31)
        ctx.curve_to(-30, 31, -32, 18, -28, 4)
        ctx.close_path()
        fill_stroke(ctx, shoe)
        if L.get("sole"):
            ctx.rectangle(-27, 22, 81, 8)
            ctx.set_source_rgb(*shade(L["sole"], k))
            ctx.fill()
            ctx.move_to(-29, 31)
            ctx.line_to(53, 31)
            ctx.set_source_rgb(*OUTLINE)
            ctx.set_line_width(OW)
            ctx.stroke()
        ctx.restore()

    def _draw_arm(self, ctx, sh, el, wr, fore, hand, k):
        L = self.look
        skin = shade(L["skin"], k)
        top = shade(L["top"], k)
        if L.get("sleeve") == "long":
            limb(ctx, [sh, el, wr], 40, top)
            cuff = (wr[0] - 10 * dirv(fore)[0], wr[1] - 10 * dirv(fore)[1])
            limb(ctx, [cuff, (wr[0] - 2 * dirv(fore)[0], wr[1] - 2 * dirv(fore)[1])], 42, shade(L["top2"], k))
        else:
            limb(ctx, [sh, el, wr], 33, skin)
            mid = (sh[0] + (el[0] - sh[0]) * 0.5, sh[1] + (el[1] - sh[1]) * 0.5)
            limb(ctx, [sh, mid], 46, top)
        draw_hand(ctx, wr, fore, hand, skin)

    def _draw_torso(self, ctx, hip, breathe):
        L = self.look
        hx, hy = hip
        top = hy - TORSO + breathe * 0.4
        if L.get("hood"):
            ellipse(ctx, -10, top + 8, 70, 30)
            fill_stroke(ctx, L["top2"])
        ctx.move_to(-76, hy + 22)
        ctx.curve_to(-86, hy - 60, -88, top + 70, -80, top + 34)
        ctx.curve_to(-74, top + 8, -58, top, -40, top)
        ctx.line_to(48, top)
        ctx.curve_to(66, top, 80, top + 8, 86, top + 34)
        ctx.curve_to(92, top + 70, 90, hy - 60, 80, hy + 22)
        ctx.curve_to(40, hy + 36, -40, hy + 36, -76, hy + 22)
        ctx.close_path()
        path = ctx.copy_path()
        ctx.set_source_rgb(*L["top"])
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        # cel shading on the back side
        ctx.move_to(-100, top - 10)
        ctx.curve_to(-40, top + 60, -46, hy - 40, -100, hy + 40)
        ctx.close_path()
        ctx.set_source_rgba(0, 0, 0, 0.13)
        ctx.fill()
        if L.get("pocket"):
            ctx.move_to(-30, hy - 70)
            ctx.line_to(52, hy - 70)
            ctx.line_to(62, hy - 6)
            ctx.line_to(-40, hy - 6)
            ctx.close_path()
            ctx.set_source_rgb(*L["top2"])
            ctx.fill_preserve()
            ctx.set_source_rgb(*OUTLINE)
            ctx.set_line_width(4)
            ctx.stroke()
        if L.get("stripe"):
            ctx.rectangle(-100, top + 90, 200, 22)
            ctx.set_source_rgb(*L["stripe"])
            ctx.fill()
        ctx.restore()
        ctx.append_path(path)
        ctx.set_source_rgb(*OUTLINE)
        ctx.set_line_width(OW)
        ctx.stroke()
        if L.get("hood"):  # drawstrings
            for dx in (14, 42):
                limb(ctx, [(dx, top + 14), (dx + 2, top + 70)], 5, (0.95, 0.93, 0.9), ow=2.5)
        if L.get("skirt"):
            ctx.move_to(-80, hy - 26)
            ctx.line_to(82, hy - 26)
            ctx.curve_to(100, hy + 20, 112, hy + 60, 116, hy + 78)
            ctx.curve_to(40, hy + 92, -40, hy + 92, -112, hy + 78)
            ctx.curve_to(-106, hy + 60, -96, hy + 20, -80, hy - 26)
            ctx.close_path()
            fill_stroke(ctx, L["skirt"])
            for dx in (-50, 0, 50):
                ctx.move_to(dx * 0.7, hy - 14)
                ctx.line_to(dx * 1.4, hy + 80)
                ctx.set_source_rgba(0, 0, 0, 0.16)
                ctx.set_line_width(4)
                ctx.stroke()

    def _draw_head(self, ctx, c, t):
        L = self.look
        tr = self.tr
        cx, cy = c
        skin = L["skin"]
        hair = L["hair"]
        style = L.get("hairstyle", "spiky")
        ex = EXPR.get(tr["expr"].at(t), EXPR["neutral"])
        ctx.save()
        ctx.translate(cx, cy)
        if style == "pony":
            # ponytail + back hair behind the head
            ctx.move_to(-96, -70)
            ctx.curve_to(-190, -90, -210, 30, -168, 110 + 6 * math.sin(t * 5))
            ctx.curve_to(-150, 60, -130, 10, -86, -10)
            ctx.close_path()
            fill_stroke(ctx, hair)
            ellipse(ctx, -14, -6, HEAD_RX + 12, HEAD_RY + 12)
            fill_stroke(ctx, hair)
            ellipse(ctx, -112, -46, 16, 20)
            fill_stroke(ctx, L.get("scrunchie", (0.95, 0.4, 0.55)))
        # ear
        ellipse(ctx, -96, 16, 19, 27)
        fill_stroke(ctx, skin)
        ellipse(ctx, -96, 16, 8, 14)
        ctx.set_source_rgba(0.5, 0.25, 0.2, 0.3)
        ctx.fill()
        # head
        ellipse(ctx, 0, 0, HEAD_RX, HEAD_RY)
        fill_stroke(ctx, skin)
        # face shading on the back side
        ctx.save()
        ellipse(ctx, 0, 0, HEAD_RX - 3, HEAD_RY - 3)
        ctx.clip()
        ellipse(ctx, -150, 30, 80, 150)
        ctx.set_source_rgba(0, 0, 0, 0.08)
        ctx.fill()
        ctx.restore()

        f = FX
        # cheeks
        blush = 0.35 + 0.6 * tr["blush"].at(t)
        for bx in (f - 52, f + 64):
            ellipse(ctx, bx, 44, 18, 10)
            ctx.set_source_rgba(1, 0.45, 0.45, 0.28 * blush)
            ctx.fill()

        # eyes
        lid = ex["lid"]
        bt = (t + self.blink_seed) % 3.4
        if bt < 0.14:
            lid = 1.0
        look = tr["look"].at(t)
        eyes = [(f - 30, -6, 21), (f + 40, -6, 23)]
        for (exx, eyy, erx) in eyes:
            if ex.get("squeeze") and lid >= 1:
                d = 1 if exx < f else -1  # ">" on the left eye, "<" on the right
                ctx.move_to(exx - 14 * d, eyy - 13)
                ctx.line_to(exx + 10 * d, eyy)
                ctx.line_to(exx - 14 * d, eyy + 13)
                ctx.set_source_rgb(*OUTLINE)
                ctx.set_line_width(6)
                ctx.stroke()
                continue
            if ex.get("arcs") and lid >= 1:
                ctx.arc(exx, eyy + 8, 16, math.pi * 1.1, math.pi * 1.9)
                ctx.set_source_rgb(*OUTLINE)
                ctx.set_line_width(6)
                ctx.stroke()
                continue
            ry = 28
            ellipse(ctx, exx, eyy, erx, ry)
            fill_stroke(ctx, (1, 1, 1), ow=5)
            ctx.save()
            ellipse(ctx, exx, eyy, erx - 2, ry - 2)
            ctx.clip()
            pr = 12 * ex["pupil"]
            px, py = exx + 5 + look[0] * 8, eyy + 2 + look[1] * 9
            ellipse(ctx, px, py, pr, pr * 1.12)
            ctx.set_source_rgb(*L.get("iris", (0.2, 0.14, 0.12)))
            ctx.fill()
            ellipse(ctx, px + 3.5, py - 4, 3.6, 3.6)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()
            if lid > 0.01:
                ctx.rectangle(exx - erx - 4, eyy - ry - 4, erx * 2 + 8, (ry * 2 + 4) * lid + 2)
                ctx.set_source_rgb(*skin)
                ctx.fill()
                ly = eyy - ry + (ry * 2) * lid
                ctx.move_to(exx - erx, ly)
                ctx.line_to(exx + erx, ly)
                ctx.set_source_rgb(*OUTLINE)
                ctx.set_line_width(5)
                ctx.stroke()
            ctx.restore()
            ellipse(ctx, exx, eyy, erx, ry)
            ctx.set_source_rgb(*OUTLINE)
            ctx.set_line_width(5)
            ctx.stroke()
        # brows
        for i, (exx, eyy, erx) in enumerate(eyes):
            inner_dir = 1 if i == 0 else -1  # inner end points towards the other eye
            by = eyy - 42 - ex["lift"]
            x_in, x_out = exx + inner_dir * 16, exx - inner_dir * 18
            ctx.move_to(x_out, by + 2)
            ctx.line_to(x_in, by - ex["inner"])
            ctx.set_source_rgb(*shade(hair, 0.8))
            ctx.set_line_width(9)
            ctx.set_line_cap(1)
            ctx.stroke()
        if L.get("glasses"):
            ctx.set_source_rgb(*OUTLINE)
            ctx.set_line_width(5.5)
            for (exx, eyy, erx) in eyes:
                ctx.new_sub_path()
                ctx.arc(exx, eyy, 33, 0, 2 * math.pi)
            ctx.stroke()
            ctx.move_to(eyes[0][0] + 31, eyes[0][1] - 6)
            ctx.curve_to(eyes[0][0] + 36, eyes[0][1] - 14, eyes[1][0] - 38, eyes[1][1] - 14, eyes[1][0] - 33, eyes[1][1] - 6)
            ctx.move_to(eyes[0][0] - 33, eyes[0][1] - 4)
            ctx.line_to(-82, 2)
            ctx.stroke()
        # nose
        nx, ny = f + 52, 26
        ctx.move_to(nx - 8, ny - 22)
        ctx.curve_to(nx + 14, ny - 14, nx + 26, ny + 6, nx + 6, ny + 12)
        ctx.curve_to(nx - 2, ny + 14, nx - 8, ny + 10, nx - 10, ny + 6)
        ctx.set_source_rgb(*shade(skin, 0.92))
        ctx.fill_preserve()
        ctx.set_source_rgb(*OUTLINE)
        ctx.set_line_width(5)
        ctx.stroke()
        bleed = tr["bleed"].at(t)
        if bleed > 0.01:
            red = (0.85, 0.08, 0.12)
            ctx.move_to(nx + 2, ny + 10)
            ctx.curve_to(nx + 8, ny + 16, nx + 6, ny + 16 + 34 * bleed, nx + 2, ny + 16 + 36 * bleed)
            ctx.curve_to(nx - 4, ny + 16 + 34 * bleed, nx - 4, ny + 16, nx + 2, ny + 10)
            ctx.set_source_rgb(*red)
            ctx.fill()
            dp = (t * 1.6) % 1.0
            ellipse(ctx, nx + 2, ny + 22 + 36 * bleed + dp * 80, 6 * bleed, 8 * bleed)
            ctx.set_source_rgba(*red, 1 - dp)
            ctx.fill()

        # mouth
        m, wv = self.mouth(t)
        mx, my = f + 18, 72
        kind = ex["mouth"]
        if m > 0.07:
            big = 1.25 if kind == "o" else 1.0
            mw = (24 + 16 * m + 8 * wv) * big
            mh = (6 + 36 * m) * big
            ctx.move_to(mx - mw, my - 4)
            ctx.curve_to(mx - mw * 0.5, my - 10, mx + mw * 0.5, my - 10, mx + mw, my - 4)
            ctx.curve_to(mx + mw * 0.9, my + mh * 1.2, mx - mw * 0.9, my + mh * 1.2, mx - mw, my - 4)
            ctx.close_path()
            path = ctx.copy_path()
            ctx.set_source_rgb(0.36, 0.08, 0.14)
            ctx.fill()
            ctx.save()
            ctx.append_path(path)
            ctx.clip()
            ellipse(ctx, mx + 4, my + mh * 0.95, mw * 0.6, mh * 0.45)
            ctx.set_source_rgb(0.93, 0.42, 0.5)
            ctx.fill()
            if m > 0.25:
                ctx.rectangle(mx - mw, my - 12, mw * 2, 10)
                ctx.set_source_rgb(1, 1, 1)
                ctx.fill()
            ctx.restore()
            ctx.append_path(path)
            ctx.set_source_rgb(*OUTLINE)
            ctx.set_line_width(5)
            ctx.stroke()
        else:
            ctx.set_source_rgb(*OUTLINE)
            ctx.set_line_width(6)
            ctx.set_line_cap(1)
            if kind == "smile":
                ctx.move_to(mx - 26, my - 6)
                ctx.curve_to(mx - 10, my + 12, mx + 14, my + 12, mx + 28, my - 8)
                ctx.stroke()
            elif kind == "grin":
                ctx.move_to(mx - 34, my - 10)
                ctx.curve_to(mx - 20, my + 34, mx + 26, my + 34, mx + 38, my - 12)
                ctx.close_path()
                path = ctx.copy_path()
                ctx.set_source_rgb(0.36, 0.08, 0.14)
                ctx.fill()
                ctx.save()
                ctx.append_path(path)
                ctx.clip()
                ctx.rectangle(mx - 40, my - 14, 80, 13)
                ctx.set_source_rgb(1, 1, 1)
                ctx.fill()
                ellipse(ctx, mx + 2, my + 26, 20, 10)
                ctx.set_source_rgb(0.93, 0.42, 0.5)
                ctx.fill()
                ctx.restore()
                ctx.append_path(path)
                ctx.set_source_rgb(*OUTLINE)
                ctx.set_line_width(5)
                ctx.stroke()
            elif kind == "frown":
                ctx.move_to(mx - 22, my + 8)
                ctx.curve_to(mx - 8, my - 6, mx + 10, my - 6, mx + 24, my + 8)
                ctx.stroke()
            elif kind == "flat":
                ctx.move_to(mx - 20, my + 2)
                ctx.line_to(mx + 22, my)
                ctx.stroke()
            elif kind == "smirk":
                ctx.move_to(mx - 18, my + 4)
                ctx.curve_to(mx, my + 8, mx + 16, my + 2, mx + 28, my - 10)
                ctx.stroke()
            elif kind == "o":
                ellipse(ctx, mx + 4, my + 8, 14, 18)
                fill_stroke(ctx, (0.36, 0.08, 0.14), ow=5)
            elif kind == "teeth":
                ctx.rectangle(mx - 28, my - 4, 58, 22)
                fill_stroke(ctx, (1, 1, 1), ow=5)
                ctx.move_to(mx - 28, my + 7)
                ctx.line_to(mx + 30, my + 7)
                for k in range(-2, 3):
                    ctx.move_to(mx + k * 11, my - 4)
                    ctx.line_to(mx + k * 11, my + 18)
                ctx.set_line_width(3)
                ctx.stroke()

        # front hair
        if style == "spiky":
            pts = []
            n = 11
            for i in range(n + 1):
                a = math.pi * (1.05 + 0.98 * i / n)
                r = 1.06 if i % 2 == 0 else 1.2
                pts.append((math.cos(a) * HEAD_RX * r, math.sin(a) * HEAD_RY * r - 8))
            ctx.move_to(-HEAD_RX - 6, 20)
            for p in pts:
                ctx.line_to(*p)
            ctx.line_to(HEAD_RX * 0.86, -50)
            ctx.line_to(f + 66, -58)
            ctx.line_to(f + 40, -44)
            ctx.line_to(f + 18, -66)
            ctx.line_to(f - 6, -46)
            ctx.line_to(f - 30, -70)
            ctx.line_to(f - 58, -48)
            ctx.line_to(-70, -40)
            ctx.line_to(-80, 0)
            ctx.line_to(-100, 26)
            ctx.close_path()
            fill_stroke(ctx, hair)
            ctx.move_to(-40, -100)
            ctx.curve_to(-10, -120, 30, -118, 56, -100)
            ctx.set_source_rgba(1, 1, 1, 0.18)
            ctx.set_line_width(8)
            ctx.stroke()
        elif style == "pony":
            ctx.move_to(-HEAD_RX - 8, 6)
            ctx.curve_to(-HEAD_RX - 14, -110, 60, -160, HEAD_RX + 6, -40)
            ctx.curve_to(80, -66, 40, -80, f - 6, -64)
            ctx.curve_to(-20, -52, -60, -30, -74, 6)
            ctx.close_path()
            fill_stroke(ctx, hair)
            ctx.move_to(-30, -104)
            ctx.curve_to(0, -118, 40, -112, 70, -92)
            ctx.set_source_rgba(1, 1, 1, 0.16)
            ctx.set_line_width(8)
            ctx.stroke()
        ctx.restore()
