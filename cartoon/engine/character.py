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

class _Ink:
    """Outline colour that themes can change at runtime (unpacks like an RGB tuple)."""

    def __init__(self, c):
        self.c = c

    def __iter__(self):
        return iter(self.c)

    def __len__(self):
        return 3

    def __getitem__(self, i):
        return self.c[i]


OUTLINE = _Ink((0.16, 0.12, 0.19))
OW = 6.0  # outline width
# wobble > 0 gives hand-drawn ink: lines jitter around the fills and "boil" every few frames
STYLE = dict(wobble=0.0, k=0, ow_k=1.0, shade_a=0.13)


def set_style(name):
    STYLE["shade_a"] = 0.13
    STYLE["shade_c"] = (0.0, 0.0, 0.0)
    if name in ("euro", "storybook"):
        OUTLINE.c = (0.17, 0.11, 0.08) if name == "euro" else (0.16, 0.09, 0.18)
        STYLE.update(wobble=1.7, ow_k=0.72)
    elif name == "noir":  # 90s dark-deco action cartoon: crisp black lines, heavy black shadows
        OUTLINE.c = (0.02, 0.02, 0.04)
        STYLE.update(wobble=0.0, ow_k=0.62, shade_a=0.5, shade_c=(0.04, 0.06, 0.18))
    elif name == "flat":  # outline-free flat pastel look; only facial lines stay drawn
        OUTLINE.c = (0.17, 0.16, 0.27)
        STYLE.update(wobble=0.0, ow_k=0.0)
    else:
        OUTLINE.c = (0.16, 0.12, 0.19)
        STYLE.update(wobble=0.0, ow_k=1.0)


def _jit(x, y, seed):
    a, k = STYLE["wobble"], STYLE["k"]
    return (x + a * (math.sin(x * 0.045 + y * 0.021 + k * 2.1 + seed) + 0.5 * math.sin(x * 0.11 - y * 0.07 + k * 3.7 + seed * 2)),
            y + a * (math.cos(y * 0.05 - x * 0.027 + k * 1.7 + seed) + 0.5 * math.cos(y * 0.13 + x * 0.06 + k * 2.9 + seed * 3)))


def _wobbled(ctx, path, seed):
    for typ, pts in path:
        if typ == 0:
            ctx.move_to(*_jit(pts[0], pts[1], seed))
        elif typ == 1:
            ctx.line_to(*_jit(pts[0], pts[1], seed))
        elif typ == 3:
            ctx.close_path()


def ink(ctx, color, w):
    """Stroke the current path as an ink line (two offset passes = varying pen pressure)."""
    if not STYLE["wobble"]:
        ctx.set_source_rgb(*color)
        ctx.set_line_width(w)
        ctx.stroke()
        return
    ctx.set_tolerance(0.6)
    path = ctx.copy_path_flat()
    ctx.new_path()
    ctx.set_source_rgb(*color)
    for seed, kw in ((0.0, 0.85), (1.9, 0.55)):
        _wobbled(ctx, path, seed)
        ctx.set_line_width(w * kw)
        ctx.stroke()

# rig dimensions (local units, before character scale)
HIP_H = 326
THIGH, SHIN, ANKLE_H = 150, 148, 30
TORSO = 228
UPPER, FORE = 118, 112
HALF_STRIDE = 170
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


FOOT_HEEL = (-22.0, 30.0)  # floor contact points relative to the ankle (flat foot)
FOOT_TOE = (40.0, 30.0)
LEG_MAX = (THIGH + SHIN) * 0.985  # stance leg almost straight, like a real walk
SWING_LIFT = 30


def _about(pivot, rel, ang):
    """Ankle position when the foot rotates by ang (toe up +) about a floor pivot."""
    v = rot(rel, (0.0, 0.0), -ang)
    return pivot[0] - v[0], pivot[1] - v[1]


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
    ow *= STYLE["ow_k"]
    if STYLE["wobble"]:
        ctx.move_to(*_jit(*pts[0], 0.7))
        for p in pts[1:]:
            ctx.line_to(*_jit(*p, 0.7))
        ctx.set_source_rgb(*outline)
        ctx.set_line_width(width + 2 * ow)
        ctx.stroke()
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
    else:
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
    ink(ctx, outline, ow * STYLE["ow_k"])


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


def draw_paw(ctx, wrist, fore_deg, fur):
    """Round bear paw (no fingers) with a pad."""
    fx, fy = dirv(fore_deg)
    ctx.save()
    ctx.translate(*wrist)
    ctx.rotate(math.atan2(fy, fx))
    ellipse(ctx, 18, 0, 30, 27)
    fill_stroke(ctx, fur)
    for k in (-14, 0, 14):
        ellipse(ctx, 40, k, 8, 7)
        ctx.set_source_rgba(0, 0, 0, 0.18)
        ctx.fill()
    ctx.restore()


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
    "evil": dict(lift=-2, inner=-16, lid=0.32, mouth="grin", pupil=0.8),
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
            "rot": Track(0.0), "penguin": Track(0.0),
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
            if abs(dx) > 90:  # a scene cut teleported us: no walking, no footsteps
                dx, w = 0.0, 0.0
            airborne = self.tr["y"].at(t) < -20
            v = abs(dx) / dt
            target = clamp(v / 120.0)
            w += (target - w) * min(1.0, dt * 12)
            stride = (HALF_STRIDE * (1 + 0.2 * clamp((v - 320) / 500)) * self.look.get("stride", 1.0)
                      * self.look.get("leg_k", 1.0) * (1 - 0.55 * self.tr["penguin"].at(t)))
            old = phase
            phase += abs(dx) / (2 * stride * self.s)
            if w > 0.3 and int(old * 2) != int(phase * 2) and not airborne:
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
    @staticmethod
    def _gait_foot(p, S, D, lift=SWING_LIFT):
        """Ankle position (relative to its hip, y up = negative) and foot angle (toe up = +)
        for gait phase p (0 = heel strike).  Stance (0..S): heel strike -> flat foot -> heel
        rise rolling over the toes, with the contact point fixed on the floor.  Swing (S..1):
        knee folds, foot clears the floor and reaches forward for the next heel strike."""

        def stance(u):
            xa = D * S / 2 - D * S * u  # where the ankle would be with the foot flat
            if u < 0.14:  # heel contact, foot slaps down
                ang = 18 * (1 - smooth(u / 0.14))
                return _about(((xa + FOOT_HEEL[0], 0.0)), FOOT_HEEL, ang), ang
            if u < 0.55:
                return (xa, -ANKLE_H), 0.0
            ang = -38 * smooth((u - 0.55) / 0.45)  # heel rises, roll over the toes
            return _about((xa + FOOT_TOE[0], 0.0), FOOT_TOE, ang), ang

        if p < S:
            return stance(p / S)
        v = (p - S) / (1 - S)
        (x0, y0), a0 = stance(1.0)
        (x1, y1), a1 = stance(0.0)
        e = v * v * (3 - 2 * v)
        x = x0 + (x1 - x0) * e
        y = y0 + (y1 - y0) * v - lift * math.sin(math.pi * v ** 0.75)
        a = a0 * (1 - smooth(v / 0.45)) + a1 * smooth((v - 0.55) / 0.45)  # foot levels out, then toe lifts for the heel strike
        return (x, y), a

    def _world(self, p, st):
        dx, dy = st["fs"] * p[0], st["sy"] * p[1]
        r = st.get("rot", 0.0)
        if r:
            dx, dy = dx * math.cos(r) - dy * math.sin(r), dx * math.sin(r) + dy * math.cos(r)
        return (st["X"] + dx, st["G"] + st["Y"] + dy)

    def _arm(self, t, side, shoulder, st, walk_swing):
        ang = self.tr["arm" + side].at(t)
        s_a, e_a = ang[0] + walk_swing[0], ang[1] + walk_swing[1]
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
        run = clamp((v - 450) / 350) * w
        pF, pB = phase % 1.0, (phase + 0.5) % 1.0
        bw, hs = L.get("body_w", 1.0), L.get("head_s", 1.0)
        lk = L.get("leg_k", 1.0)  # leg length multiplier (tall / short characters)
        HH = ANKLE_H + (HIP_H - ANKLE_H) * lk
        pg = tr["penguin"].at(t)  # penguin walk on ice: short flat steps, rocking body
        lean = (tr["lean"].at(t) + w * 3 + run * 9 + 1.2 * w * math.cos(4 * math.pi * phase)
                + L.get("stoop", 0.0) + pg * 6)
        rot_deg = tr["rot"].at(t) + pg * w * 6 * math.sin(2 * math.pi * phase)
        st["rot"] = rad(rot_deg) * (1 if face >= 0 else -1)
        tilt = tr["tilt"].at(t)
        crouch = tr["crouch"].at(t)
        breathe = math.sin(t * 2 * math.pi / 3.1 + self.blink_seed) * 2.0
        hipxF, hipxB = 10.0, -12.0

        # walking legs: real gait timing (60% stance / 40% swing; less stance when running)
        S = 0.6 - 0.2 * run
        D = 2 * HALF_STRIDE * (1 + 0.2 * clamp((v - 320) / 500)) * L.get("stride", 1.0) * lk * (1 - 0.55 * pg)
        lift = SWING_LIFT * L.get("lift", 1.0) * (1 - 0.5 * pg)
        (wF, waF) = self._gait_foot(pF, S, D, lift)
        (wB, waB) = self._gait_foot(pB, S, D, lift)
        waF, waB = waF * (1 - pg), waB * (1 - pg)
        # pelvis height: the body vaults over the straight stance leg (inverted pendulum)
        hy = -1e9
        for p_, (ax, ay) in ((pF, wF), (pB, wB)):
            c = ay - math.sqrt(max(1.0, (LEG_MAX * lk) ** 2 - ax ** 2))
            if p_ >= S:  # swing leg only matters right before it lands
                c -= (1 - smooth(((p_ - S) / (1 - S) - 0.65) / 0.35)) * 300
            hy = max(hy, c)
        hy = clamp(hy, -HH + 2, -HH + 60 * lk) + run * 14
        stand_hy = -HH + 4
        hip = (0.0, stand_hy + (hy - stand_hy) * w + crouch * 70)
        ankF = ((hipxF + 20) + (hipxF + wF[0] - hipxF - 20) * w, -ANKLE_H + (wF[1] + ANKLE_H) * w)
        ankB = ((hipxB - 4) + (hipxB + wB[0] - hipxB + 4) * w, -ANKLE_H + (wB[1] + ANKLE_H) * w)
        aF, aB = waF * w, waB * w
        if air > 0:  # tuck the feet in when airborne
            ankF = (ankF[0] - 10 * air, ankF[1] - 38 * air)
            ankB = (ankB[0] - 10 * air, ankB[1] - 38 * air)
        st["hip"], st["lean"] = hip, lean

        # torso frame points
        neck = (6.0, hip[1] - TORSO - 6 + breathe * 0.3)
        sh_y = hip[1] - TORSO + 24 + breathe * 0.3
        shF, shB = (L.get("sh_f", 12.0) * bw, sh_y), (L.get("sh_b", -14.0) * bw, sh_y)
        nl = L.get("neck_len", 0)
        hc = (neck[0] + 4, neck[1] - 110 * hs - nl)
        head_c = rot(hc, neck, -tilt)
        nose_h = (FX + 52, 26)
        st["nose_t"] = rot((hc[0] + nose_h[0] * hs, hc[1] + nose_h[1] * hs), neck, -tilt)
        st["mouth_t"] = rot((hc[0] + (FX + 18) * hs, hc[1] + (70 + L.get("mouth_dy", 0)) * hs), neck, -tilt)
        es = L.get("eye_gap", 1.0)
        eyes_t = [rot((hc[0] + (FX + dx * es) * hs, hc[1] - 6 * hs), neck, -tilt) for dx in (-30, 40)]

        # arm swing opposite to the legs, slightly lagging; elbows flex on the forward swing
        sw = (20 + 14 * run) * w * tr["swing"].at(t) * L.get("arm_swing", 1.0)
        ph = 2 * math.pi * (pF - 0.04)
        swingF = (-sw * math.cos(ph), w * (8 + 14 * max(0.0, -math.cos(ph))) + run * 55)
        swingB = (sw * math.cos(ph), w * (8 + 14 * max(0.0, math.cos(ph))) + run * 55)

        elbF, wrF, foreF = self._arm(t, "F", shF, st, swingF)
        elbB, wrB, foreB = self._arm(t, "B", shB, st, swingB)

        # legs (local frame, not leaned)
        hipF, hipB = (hipxF, hip[1]), (hipxB, hip[1])
        knee_pick = lambda a, b: a if a[0] > b[0] else b
        kneeF = ik2(hipF, ankF, THIGH * lk, SHIN * lk, knee_pick)
        kneeB = ik2(hipB, ankB, THIGH * lk, SHIN * lk, knee_pick)

        # world joints for props
        to_local = lambda p: rot(p, hip, lean)
        self.joints = {
            "handF": self._world(to_local(wrF), st), "handB": self._world(to_local(wrB), st),
            "nose": self._world(to_local(st["nose_t"]), st), "head": self._world(to_local(head_c), st),
            "foreF": foreF, "chest": self._world(to_local((10, hip[1] - 150)), st),
            "eyes": [self._world(to_local(e), st) for e in eyes_t],
        }
        self._knees = (kneeF, kneeB)

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

        self._face = face
        ctx.translate(X, ground_y + Y)
        ctx.rotate(st["rot"])
        ctx.scale(face * s * sqx, s * sqy)

        dark = 0.84
        skin = L["skin"]
        if L.get("tail"):
            self._draw_tail(ctx, hip, t, w)
        # back arm (behind everything)
        ctx.save()
        ctx.translate(*hip)
        ctx.rotate(rad(lean))
        ctx.translate(-hip[0], -hip[1])
        if L.get("cape"):
            self._draw_cape(ctx, hip, t, w, lean)
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
        if L.get("mantle"):
            self._draw_mantle(ctx, hip, bw)
        if L.get("cape") and L.get("cape_collar", True):  # tall villain collar standing up behind the head
            top = hip[1] - TORSO
            for d in (-1, 1):  # two stiff wings of the collar
                ctx.move_to(14 + d * 20, top + 14)
                ctx.curve_to(14 + d * 90, top - 10, 14 + d * 150, top - 80, 14 + d * 160, top - 150)
                ctx.curve_to(14 + d * 120, top - 110, 14 + d * 100, top - 40, 14 + d * 80, top + 30)
                ctx.close_path()
                fill_stroke(ctx, L.get("cape_in", (0.6, 0.1, 0.2)))
        ctx.save()
        ctx.translate(*neck)
        ctx.rotate(rad(-tilt))
        ctx.translate(-neck[0], -neck[1])
        limb(ctx, [(neck[0], neck[1] + 10), (neck[0] + 2, neck[1] - 30 - nl)], L.get("neck_w", 40), skin)
        if L.get("scarf"):
            self._draw_scarf(ctx, neck, t)
        if L.get("bowtie"):
            nx_, ny_ = neck[0] + 16, neck[1] + 14
            for d in (-1, 1):
                ctx.move_to(nx_, ny_)
                ctx.line_to(nx_ + 26 * d, ny_ - 14)
                ctx.line_to(nx_ + 26 * d, ny_ + 14)
                ctx.close_path()
                fill_stroke(ctx, L["bowtie"], ow=3.5)
            ellipse(ctx, nx_, ny_, 7, 7)
            fill_stroke(ctx, L["bowtie"], ow=3)
        self._draw_head(ctx, hc, t, hs)
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
            if STYLE["ow_k"]:
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
        if L.get("paw"):
            draw_paw(ctx, wr, fore, skin)
        else:
            draw_hand(ctx, wr, fore, hand, shade(L["glove"], k) if L.get("glove") else skin)

    def _draw_torso(self, ctx, hip, breathe):
        L = self.look
        hx, hy = hip
        top = hy - TORSO + breathe * 0.4
        bw = L.get("body_w", 1.0)
        ctx.save()
        ctx.translate(hx, 0)
        ctx.scale(bw, 1)
        ctx.translate(-hx, 0)
        self._torso_body(ctx, hx, hy, top)
        ctx.restore()
        if L.get("coat"):
            self._draw_coat(ctx, hx, hy, top, bw)
        if L.get("apron"):
            self._draw_apron(ctx, hx, hy, top, bw)

    def _draw_apron(self, ctx, hx, hy, top, bw):
        c = self.look["apron"]
        bottom = hy + self.look.get("apron_len", 150)
        if self.look.get("apron_waist"):  # waiter's apron: tied at the waist
            top = hy - 30 - 52 + 0.0
            ctx.move_to(-44 * bw, hy - 30)
            ctx.line_to(84 * bw, hy - 30)
            ctx.curve_to(96 * bw, hy + 40, 100 * bw, bottom - 40, 104 * bw, bottom)
            ctx.curve_to(40 * bw, bottom + 12, -30 * bw, bottom + 12, -60 * bw, bottom)
            ctx.curve_to(-56 * bw, bottom - 40, -50 * bw, hy + 40, -44 * bw, hy - 30)
            ctx.close_path()
            fill_stroke(ctx, c)
            return
        ctx.move_to(-34 * bw, top + 52)
        ctx.line_to(74 * bw, top + 52)
        ctx.line_to(80 * bw, hy - 30)
        ctx.curve_to(96 * bw, hy + 40, 100 * bw, bottom - 40, 104 * bw, bottom)
        ctx.curve_to(40 * bw, bottom + 12, -30 * bw, bottom + 12, -60 * bw, bottom)
        ctx.curve_to(-56 * bw, bottom - 40, -50 * bw, hy + 40, -40 * bw, hy - 30)
        ctx.close_path()
        fill_stroke(ctx, c)
        ctx.move_to(-34 * bw, top + 52)
        ctx.line_to(-46 * bw, top + 4)
        ctx.move_to(74 * bw, top + 52)
        ctx.line_to(66 * bw, top + 4)
        ink(ctx, shade(c, 0.7), 5)
        ctx.rectangle(0, hy - 10, 56 * bw, 46)
        ink(ctx, shade(c, 0.6), 2.5)
        ctx.move_to(-48 * bw, hy - 36)
        ctx.line_to(84 * bw, hy - 36)
        ink(ctx, shade(c, 0.6), 3)

    def _draw_cape(self, ctx, hip, t, w, lean):
        """Long cloak from the shoulders to the ankles; it trails and flutters when walking."""
        L = self.look
        top = hip[1] - TORSO + 8
        bottom = -36
        trail = -70 * w - 10
        fl = 10 * math.sin(t * 3.1) + 18 * w * math.sin(t * 9)
        for col, dx, k in ((L.get("cape_in", (0.6, 0.1, 0.2)), 14, 1.0), (L["cape"], 0, 1.0)):
            ctx.move_to(-60 + dx, top)
            ctx.line_to(70 + dx, top)
            ctx.curve_to(110 + dx, top + 200, 120 + trail * 0.4 + dx, bottom - 200, 104 + trail * 0.5 + fl + dx, bottom)
            ctx.curve_to(40 + trail, bottom + 16 + fl * 0.5, -120 + trail, bottom + 10, -170 + trail + fl, bottom - 6)
            ctx.curve_to(-140 + trail * 0.6, bottom - 260, -110, top + 160, -60 + dx, top)
            ctx.close_path()
            cape_path = ctx.copy_path()
            fill_stroke(ctx, col)
        if L.get("cape_hi"):  # 90s animation: black cloth lit with blue highlights along the front edge
            ctx.save()
            ctx.append_path(cape_path)
            ctx.clip()
            ctx.move_to(78, top)
            ctx.curve_to(108, top + 200, 112 + trail * 0.4, bottom - 200, 92 + trail * 0.5 + fl, bottom)
            ctx.set_source_rgb(*L["cape_hi"])
            ctx.set_line_width(34)
            ctx.stroke()
            ctx.restore()
        for k in range(3):  # folds
            x0 = -90 + k * 50
            ctx.move_to(x0 + 30, top + 80)
            ctx.curve_to(x0 + 10, top + 300, x0 + trail * 0.6, bottom - 160, x0 - 30 + trail, bottom - 8)
        ink(ctx, shade(L["cape"], 0.6), 3)

    def _draw_mantle(self, ctx, hip, bw):
        """The cape draped over both shoulders, as in the 90s animated look."""
        L = self.look
        top = hip[1] - TORSO
        ctx.move_to(-104 * bw, top + 150)
        ctx.curve_to(-110 * bw, top + 40, -70 * bw, top - 8, -10, top - 10)
        ctx.line_to(40, top - 10)
        ctx.curve_to(90 * bw, top - 8, 116 * bw, top + 40, 110 * bw, top + 150)
        ctx.curve_to(96 * bw, top + 110, 80 * bw, top + 40, 52 * bw, top + 30)
        ctx.line_to(-24 * bw, top + 30)
        ctx.curve_to(-60 * bw, top + 40, -86 * bw, top + 110, -104 * bw, top + 150)
        ctx.close_path()
        path = ctx.copy_path()
        fill_stroke(ctx, L["cape"])
        if L.get("cape_hi"):
            ctx.save()
            ctx.append_path(path)
            ctx.clip()
            ctx.move_to(-10, top + 4)
            ctx.curve_to(60 * bw, top + 4, 100 * bw, top + 40, 104 * bw, top + 140)
            ctx.set_source_rgb(*L["cape_hi"])
            ctx.set_line_width(26)
            ctx.stroke()
            ctx.restore()

    def _draw_tail(self, ctx, hip, t, w):
        """Little devil tail with a spade tip, swishing."""
        c = self.look["skin"]
        hx, hy = hip[0] - 50, hip[1] + 10
        sw = 30 * math.sin(t * 4.2)
        tip = (hx - 150, hy - 70 + sw)
        ctx.move_to(hx, hy)
        ctx.curve_to(hx - 60, hy + 70, hx - 140, hy + 40 + sw * 0.5, *tip)
        ink(ctx, OUTLINE, 16 + 2 * OW * STYLE["ow_k"])
        ctx.move_to(hx, hy)
        ctx.curve_to(hx - 60, hy + 70, hx - 140, hy + 40 + sw * 0.5, *tip)
        ctx.set_source_rgb(*c)
        ctx.set_line_width(14)
        ctx.set_line_cap(1)
        ctx.stroke()
        tx, ty = tip
        ctx.move_to(tx, ty - 30)
        ctx.curve_to(tx + 26, ty - 10, tx + 20, ty + 14, tx, ty + 6)
        ctx.curve_to(tx - 20, ty + 14, tx - 26, ty - 10, tx, ty - 30)
        ctx.close_path()
        fill_stroke(ctx, shade(c, 0.85))

    def _draw_coat(self, ctx, hx, hy, top, bw):
        """Long coat skirt to the knees; its hem follows the knees so it swings when walking."""
        L = self.look
        bottom = hy + L["coat"]
        kx = [k[0] for k in getattr(self, "_knees", ((20, 0), (-20, 0)))]
        left = min(min(kx) - 52, -78 * bw)
        right = max(max(kx) + 56, 82 * bw)
        b = L.get("belly", 0)
        ctx.move_to(-84 * bw, hy - 40)
        ctx.line_to((88 + b * 0.75) * bw, hy - 40)
        ctx.curve_to((90 + b * 0.5) * bw, hy + 40, right + 6, bottom - 60, right + 14, bottom)
        ctx.curve_to((right + left) * 0.5 + 20, bottom + 14, (right + left) * 0.5 - 20, bottom + 14, left - 4, bottom)
        ctx.curve_to(left - 6, bottom - 60, -86 * bw, hy + 40, -84 * bw, hy - 40)
        ctx.close_path()
        ctx.set_source_rgb(*L["top"])
        ctx.fill()
        # ink only the sides and hem, so coat and torso read as one garment
        ctx.move_to((88 + b * 0.75) * bw, hy - 40)
        ctx.curve_to((90 + b * 0.5) * bw, hy + 40, right + 6, bottom - 60, right + 14, bottom)
        ctx.curve_to((right + left) * 0.5 + 20, bottom + 14, (right + left) * 0.5 - 20, bottom + 14, left - 4, bottom)
        ctx.curve_to(left - 6, bottom - 60, -86 * bw, hy + 40, -84 * bw, hy - 40)
        ink(ctx, OUTLINE, OW * STYLE["ow_k"])
        ctx.move_to(40 * bw, top + 40)
        ctx.curve_to(44 * bw, hy - 20, right * 0.7, bottom - 80, right * 0.75, bottom + 4)
        ink(ctx, OUTLINE, 3.5)
        for i in range(3):
            ellipse(ctx, 52 * bw, top + 78 + i * 62, 7, 7)
            fill_stroke(ctx, L.get("button", (0.15, 0.13, 0.12)), ow=3)
        if L.get("belt"):
            ctx.rectangle(-86 * bw, hy - 52, 176 * bw, 20)
            fill_stroke(ctx, L["belt"], ow=4)

    def _draw_scarf(self, ctx, neck, t):
        c = self.look["scarf"]
        nx, ny = neck
        ctx.move_to(nx - 58, ny + 4)
        ctx.curve_to(nx - 40, ny + 34, nx + 50, ny + 34, nx + 64, ny + 2)
        ctx.line_to(nx + 60, ny - 22)
        ctx.curve_to(nx + 40, ny + 2, nx - 40, ny + 4, nx - 56, ny - 20)
        ctx.close_path()
        fill_stroke(ctx, c)
        sway = 6 * math.sin(t * 3)
        ctx.move_to(nx + 26, ny + 18)
        ctx.curve_to(nx + 40 + sway, ny + 60, nx + 34 + sway, ny + 110, nx + 44 + sway, ny + 150)
        ctx.line_to(nx + 72 + sway, ny + 146)
        ctx.curve_to(nx + 64 + sway, ny + 100, nx + 66, ny + 50, nx + 54, ny + 14)
        ctx.close_path()
        fill_stroke(ctx, shade(c, 0.88))
        for k in range(4):
            ctx.move_to(nx + 46 + sway + k * 7, ny + 150)
            ctx.line_to(nx + 46 + sway + k * 7, ny + 166)
        ink(ctx, shade(c, 0.6), 3)

    def _torso_body(self, ctx, hx, hy, top):
        L = self.look
        if L.get("hood"):
            ellipse(ctx, -10, top + 8, 70, 30)
            fill_stroke(ctx, L["top2"])
        if L.get("species") == "bear":  # round, soft bear body
            ellipse(ctx, 4, (top + hy) / 2 + 6, 94, (hy - top) / 2 + 40)
        else:
            ctx.move_to(-76, hy + 22)
            ctx.curve_to(-86, hy - 60, -88, top + 70, -80, top + 34)
            ctx.curve_to(-74, top + 8, -58, top, -40, top)
            ctx.line_to(48, top)
            ctx.curve_to(66, top, 80, top + 8, 86, top + 34)
            b = L.get("belly", 0)
            ctx.curve_to(92 + b * 0.5, top + 90, 90 + b, hy - 50, 80 + b * 0.4, hy + 22)
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
        ctx.set_source_rgba(*STYLE.get("shade_c", (0, 0, 0)), STYLE["shade_a"])
        ctx.fill()
        if L.get("belly_patch"):
            ellipse(ctx, 26, hy - 86, 66, 84)
            ctx.set_source_rgb(*L["belly_patch"])
            ctx.fill()
        if STYLE["wobble"]:
            for i in range(7):  # hatching on the shadow side
                ctx.move_to(-100 + i * 11, hy + 10)
                ctx.line_to(-60 + i * 11, top + 90)
            ink(ctx, shade(L["top"], 0.62), 1.6)
            for (x0, y0, x1, y1, x2, y2) in ((-20, hy - 30, 10, hy - 44, 40, hy - 34), (30, top + 80, 44, top + 110, 40, top + 140),
                                              (-50, top + 120, -40, top + 150, -48, top + 176)):
                ctx.move_to(x0, y0)
                ctx.curve_to(x1, y1, x1, y1, x2, y2)  # fabric creases
            ink(ctx, shade(L["top"], 0.55), 2.4)
        if L.get("emblem") == "bat_oval":  # black bat inside a yellow oval
            ellipse(ctx, 14, top + 96, 66, 38)
            ctx.set_source_rgb(0.95, 0.72, 0.18)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.02, 0.02, 0.04)
            ctx.set_line_width(3)
            ctx.stroke()
        if L.get("emblem") in ("bat", "bat_oval"):  # black bat on the chest
            ex0, ey0 = 14, top + (92 if L.get("emblem") == "bat_oval" else 70)
            pts = [(-60, 0), (-30, -14), (-14, -8), (-10, -22), (-4, -12), (4, -12), (10, -22), (14, -8), (30, -14),
                   (60, 0), (40, 6), (30, 22), (14, 12), (0, 26), (-14, 12), (-30, 22), (-40, 6)]
            ctx.move_to(ex0 + pts[0][0], ey0 + pts[0][1])
            for px, py in pts[1:]:
                ctx.line_to(ex0 + px, ey0 + py)
            ctx.close_path()
            ctx.set_source_rgb(0.03, 0.03, 0.05)
            ctx.fill()
        elif L.get("emblem") == "S":  # diamond shield
            ex0, ey0 = 14, top + 74
            ctx.move_to(ex0 - 52, ey0 - 30)
            ctx.line_to(ex0 + 52, ey0 - 30)
            ctx.line_to(ex0 + 64, ey0 - 12)
            ctx.line_to(ex0, ey0 + 52)
            ctx.line_to(ex0 - 64, ey0 - 12)
            ctx.close_path()
            ctx.set_source_rgb(0.85, 0.12, 0.12)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.02, 0.02, 0.04)
            ctx.set_line_width(4)
            ctx.stroke()
            ctx.select_font_face("DejaVu Serif", 0, 1)
            ctx.set_font_size(56)
            ext = ctx.text_extents("S")
            ctx.save()
            if getattr(self, "_face", 1) < 0:  # letters must never read mirrored
                ctx.translate(ex0, 0)
                ctx.scale(-1, 1)
                ctx.translate(-ex0, 0)
            ctx.move_to(ex0 - ext.x_advance / 2, ey0 + 16)
            ctx.text_path("S")
            ctx.restore()
            ctx.set_source_rgb(1.0, 0.82, 0.1)
            ctx.fill()
        if L.get("belt"):
            ctx.rectangle(-100, hy - 46, 200, 24)
            ctx.set_source_rgb(*L["belt"])
            ctx.fill()
            ctx.rectangle(-100, hy - 46, 200, 24)
            ctx.set_source_rgb(0.02, 0.02, 0.04)
            ctx.set_line_width(3)
            ctx.stroke()
        if L.get("shirt_v"):  # open vest / jacket showing the shirt
            ctx.move_to(-14, top - 2)
            ctx.line_to(44, top - 2)
            ctx.line_to(16, top + 110)
            ctx.close_path()
            fill_stroke(ctx, L["shirt_v"], ow=4)
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
        ink(ctx, OUTLINE, OW * STYLE["ow_k"])
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

    def _draw_head(self, ctx, c, t, hs=1.0):
        L = self.look
        tr = self.tr
        cx, cy = c
        skin = L["skin"]
        hair = L["hair"]
        style = L.get("hairstyle", "spiky")
        ex = EXPR.get(tr["expr"].at(t), EXPR["neutral"])
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(hs, hs)
        if style == "bob":  # bob cut: hair mass behind the head down to the chin
            ctx.move_to(-HEAD_RX - 16, -20)
            ctx.curve_to(-HEAD_RX - 30, 60, -110, 120, -60, 118)
            ctx.line_to(40, 100)
            ctx.curve_to(0, 40, 40, -150, -HEAD_RX - 16, -20)
            ctx.close_path()
            fill_stroke(ctx, hair)
        if L.get("jaw"):  # big square superhero jaw
            ctx.move_to(-96, 0)
            ctx.line_to(FX + 96, -6)
            ctx.line_to(FX + 86, 96)
            ctx.curve_to(FX + 70, 132, FX + 20, 140, -20, 132)
            ctx.curve_to(-70, 120, -92, 90, -96, 0)
            ctx.close_path()
            fill_stroke(ctx, skin)
        if L.get("jowls"):
            for jx, jy, jr in ((-48, 78, 52), (54, 84, 50)):
                ellipse(ctx, jx, jy, jr, jr * 0.8)
                fill_stroke(ctx, skin)
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
        if L.get("species") == "bear":  # round bear ears on top
            for ex_, ey_ in ((-72, -96), (52, -108)):
                ellipse(ctx, ex_, ey_, 36, 34)
                fill_stroke(ctx, skin)
                ellipse(ctx, ex_ + 2, ey_ + 2, 19, 18)
                ctx.set_source_rgb(*L.get("muzzle", shade(skin, 1.3)))
                ctx.fill()
        if L.get("ears") == "none":
            pass
        elif L.get("ears") == "pointy":  # elf / imp ear sweeping back
            ctx.move_to(-92, -6)
            ctx.curve_to(-120, -20, -140, -40, -152, -66)
            ctx.curve_to(-140, -10, -120, 30, -96, 36)
            ctx.close_path()
            fill_stroke(ctx, skin)
        else:
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
        ctx.set_source_rgba(*STYLE.get("shade_c", (0, 0, 0)), STYLE["shade_a"] * 0.6)
        ctx.fill()
        if STYLE["wobble"]:  # pen hatching on the shadow side, Franco-Belgian style
            ellipse(ctx, -150, 40, 98, 150)
            ctx.clip()
            for i in range(9):
                ctx.move_to(-150 + i * 12, 130)
                ctx.line_to(-90 + i * 12, -40)
            ink(ctx, shade(skin, 0.62), 1.8)
            ctx.new_path()
        ctx.restore()

        f = FX
        # cheeks
        blush = 0.35 + 0.6 * tr["blush"].at(t)
        for bx in (f - 52, f + 64):
            ellipse(ctx, bx, 44, 18, 10)
            ctx.set_source_rgba(1, 0.45, 0.45, 0.28 * blush)
            ctx.fill()

        # eyes
        lid = ex["lid"] if ex["lid"] == 0 else max(ex["lid"], L.get("lid0", 0.0))
        bt = (t + self.blink_seed) % 3.4
        if bt < 0.14:
            lid = 1.0
        look = tr["look"].at(t)
        es, gap = L.get("eye_s", 1.0), L.get("eye_gap", 1.0)
        eyes = [(f - 30 * gap, -6, 21 * es), (f + 40 * gap, -6, 23 * es)]
        for (exx, eyy, erx) in eyes:
            if L.get("eyes") == "slits":
                continue  # drawn on top of the cowl later
            if L.get("eyes") == "joker":  # black sclera, tiny white pupils
                ellipse(ctx, exx, eyy, erx * 0.9, 24 * es)
                fill_stroke(ctx, (0.04, 0.04, 0.05), ow=4)
                ellipse(ctx, exx + 4 + look[0] * 6, eyy + look[1] * 6, 5, 5)
                ctx.set_source_rgb(1, 1, 1)
                ctx.fill()
                continue
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
            ry = 28 * es
            ellipse(ctx, exx, eyy, erx, ry)
            fill_stroke(ctx, (1, 1, 1), ow=5)
            ctx.save()
            ellipse(ctx, exx, eyy, erx - 2, ry - 2)
            ctx.clip()
            pr = 12 * ex["pupil"] * max(es, 0.75)
            px, py = exx + 5 * es + look[0] * 8 * es, eyy + 2 + look[1] * 9 * es
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
            ink(ctx, OUTLINE, 5 * STYLE["ow_k"] + 1)
            if L.get("kohl"):  # kohl: thick dark line hugging the lids, winged at the outer corner
                outer = -1 if exx < f else 1
                kc = L.get("kohl_c", (0.08, 0.06, 0.08))
                ctx.save()
                ctx.translate(exx, eyy)
                ctx.scale(erx + 2, ry + 2)
                ctx.arc(0, 0, 1, math.pi * 1.02, math.pi * 1.98)
                ctx.restore()
                ink(ctx, kc, 10)
                ctx.save()
                ctx.translate(exx, eyy)
                ctx.scale(erx + 1, ry + 1)
                ctx.arc(0, 0, 1, math.pi * 0.08, math.pi * 0.92)
                ctx.restore()
                ink(ctx, kc, 6)
                ctx.move_to(exx + outer * erx, eyy - 2)
                ctx.line_to(exx + outer * (erx + 18), eyy - 11)
                ink(ctx, kc, 7)
            if L.get("bags"):
                ctx.arc(exx, eyy + ry * 0.55, erx * 1.15, 0.2 * math.pi, 0.8 * math.pi)
                ink(ctx, shade(skin, 0.6), 3)
        # brows
        for i, (exx, eyy, erx) in enumerate(eyes if not L.get("cowl") else []):
            inner_dir = 1 if i == 0 else -1  # inner end points towards the other eye
            by = eyy - 14 - 28 * es - ex["lift"]
            x_in, x_out = exx + inner_dir * 16, exx - inner_dir * 18
            ctx.move_to(x_out, by + 2)
            ctx.line_to(x_in, by - ex["inner"])
            ctx.set_source_rgb(*L.get("brow", shade(hair, 0.8)))
            ctx.set_line_width(L.get("brow_w", 9))
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
        if L.get("nose") == "bear":  # muzzle + shiny black nose
            ellipse(ctx, f + 34, 42, 58, 44)
            fill_stroke(ctx, L.get("muzzle", shade(skin, 1.3)))
            ellipse(ctx, f + 56, 16, 21, 15)
            fill_stroke(ctx, (0.12, 0.09, 0.09), ow=3)
            ellipse(ctx, f + 50, 11, 6, 4)
            ctx.set_source_rgba(1, 1, 1, 0.7)
            ctx.fill()
            ctx.move_to(f + 56, 30)
            ctx.line_to(f + 56, 50)
            ink(ctx, (0.25, 0.15, 0.12), 4)
            ctx.new_path()
        elif L.get("nose") == "big":  # big bulbous caricature nose
            ellipse(ctx, nx - 4, ny + 4, 32, 27)
            fill_stroke(ctx, shade(skin, 0.97))
            ellipse(ctx, nx + 4, ny + 8, 16, 12)
            ctx.set_source_rgba(0.85, 0.35, 0.3, 0.25)
            ctx.fill()
            ctx.arc(nx - 6, ny + 22, 7, 0.1 * math.pi, 0.9 * math.pi)
            ink(ctx, OUTLINE, 3)
            ctx.new_path()
        elif L.get("nose") == "long":  # long pointed nose
            nk = L.get("nose_k", 1.0)
            ctx.move_to(nx - 10, ny - 16)
            ctx.curve_to(nx + 10, ny - 8, nx + 34 * nk, ny + 6, nx + 46 * nk, ny + 18)
            ctx.curve_to(nx + 30 * nk, ny + 22 + 4 * (nk - 1), nx + 4, ny + 22, nx - 8, ny + 14)
            ctx.close_path()
            fill_stroke(ctx, shade(skin, 0.9), ow=4.5)
            ctx.new_path()
        elif L.get("nose") == "button":
            ellipse(ctx, nx - 6, ny + 6, 12, 10)
            fill_stroke(ctx, shade(skin, 0.95), ow=4)
            ctx.new_path()
        ctx.move_to(nx - 8, ny - 22)
        ctx.curve_to(nx + 14, ny - 14, nx + 26, ny + 6, nx + 6, ny + 12)
        ctx.curve_to(nx - 2, ny + 14, nx - 8, ny + 10, nx - 10, ny + 6)
        if L.get("nose"):
            ctx.new_path()
        else:
            ctx.set_source_rgb(*shade(skin, 0.92))
            ctx.fill_preserve()
            ink(ctx, OUTLINE, 5 * STYLE["ow_k"])
        if L.get("freckles"):
            for fx_, fy_ in ((f - 54, 36), (f - 44, 44), (f - 60, 48), (f + 62, 38), (f + 72, 46), (f + 56, 48)):
                ellipse(ctx, fx_, fy_, 2.6, 2.6)
            ctx.set_source_rgba(0.55, 0.3, 0.2, 0.6)
            ctx.fill()
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

        if L.get("beard"):  # short neat beard along the jaw, with a moustache
            bc = L["beard"]
            ctx.move_to(-112, -24)
            ctx.line_to(-96, -24)
            ctx.curve_to(-96, 90, -40, 132, f + 20, 132)
            ctx.curve_to(f + 70, 132, f + 100, 90, f + 96, 40)
            ctx.curve_to(f + 80, 70, f + 60, 100, f + 18, 104)
            ctx.curve_to(-20, 104, -60, 80, -76, 10)
            ctx.line_to(-80, -24)
            ctx.curve_to(-100, 40, -112, 30, -112, -24)
            ctx.close_path()
            fill_stroke(ctx, bc, ow=4)
            ctx.move_to(f - 8, 58)
            ctx.curve_to(f + 10, 50, f + 30, 50, f + 48, 58)
            ink(ctx, bc, 9)

        # mouth
        ctx.save()
        if L.get("mouth_k"):  # extra-wide grin
            ctx.translate(f + 18, 72 + L.get("mouth_dy", 0))
            ctx.scale(L["mouth_k"], 1.0)
            ctx.translate(-(f + 18), -(72 + L.get("mouth_dy", 0)))
        m, wv = self.mouth(t)
        mx, my = f + 18, 72 + L.get("mouth_dy", 0)
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
            if L.get("fangs"):
                for fx_ in (mx - mw * 0.5, mx + mw * 0.5):
                    ctx.move_to(fx_ - 7, my - 8)
                    ctx.line_to(fx_ + 7, my - 8)
                    ctx.line_to(fx_, my + 10)
                    ctx.close_path()
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

        ctx.restore()
        if L.get("mustache"):  # curled waiter moustache
            mc = L.get("mustache_c", hair)
            for d in (-1, 1):
                ctx.move_to(f + 46, 62)
                ctx.curve_to(f + 46 + 26 * d, 54, f + 46 + 50 * d, 72, f + 46 + 56 * d, 50)
                ctx.curve_to(f + 46 + 60 * d, 40, f + 46 + 48 * d, 36, f + 46 + 46 * d, 46)
                ink(ctx, OUTLINE, 15)
                ctx.move_to(f + 46, 62)
                ctx.curve_to(f + 46 + 26 * d, 54, f + 46 + 50 * d, 72, f + 46 + 56 * d, 50)
                ctx.curve_to(f + 46 + 60 * d, 40, f + 46 + 48 * d, 36, f + 46 + 46 * d, 46)
                ctx.set_source_rgb(*mc)
                ctx.set_line_width(9)
                ctx.set_line_cap(1)
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
        elif style == "old":  # thick white hair combed straight back, full at the back
            ctx.move_to(64, -98)
            ctx.curve_to(70, -128, 20, -150, -30, -146)
            ctx.curve_to(-96, -140, -136, -96, -134, -40)
            ctx.curve_to(-134, -6, -126, 22, -116, 40)
            ctx.curve_to(-106, 28, -98, 6, -86, -6)
            ctx.curve_to(-74, -30, -66, -52, -46, -72)
            ctx.curve_to(-10, -98, 30, -100, 64, -98)
            ctx.close_path()
            fill_stroke(ctx, hair)
            for k in range(5):  # comb lines sweeping back
                y0 = -96 - k * 9
                ctx.move_to(50 - k * 6, y0 + 4)
                ctx.curve_to(10 - k * 8, y0 - 22 + k * 2, -60 - k * 6, y0 - 10 + k * 8, -110 + k * 2, -40 + k * 16)
                ink(ctx, shade(hair, 0.74), 2.2)
        elif style == "tuft":
            ctx.move_to(-HEAD_RX - 4, 10)
            ctx.curve_to(-HEAD_RX - 10, -110, 50, -150, HEAD_RX - 4, -60)
            ctx.curve_to(70, -80, 10, -86, -50, -60)
            ctx.curve_to(-80, -40, -92, -10, -96, 14)
            ctx.close_path()
            fill_stroke(ctx, hair)
            ctx.move_to(-10, -118)
            ctx.curve_to(-30, -190, 50, -210, 40, -160)
            ctx.curve_to(34, -136, 10, -150, 20, -168)
            ink(ctx, hair, 16)
        elif style == "bun":  # grey hair pulled back into a bun
            ctx.move_to(-HEAD_RX - 6, 20)
            ctx.curve_to(-HEAD_RX - 14, -120, 60, -160, HEAD_RX + 2, -50)
            ctx.curve_to(80, -84, 20, -90, -40, -70)
            ctx.curve_to(-70, -50, -86, -10, -90, 20)
            ctx.close_path()
            fill_stroke(ctx, hair)
            ellipse(ctx, -60, -140, 46, 40)
            fill_stroke(ctx, hair)
            ctx.arc(-60, -140, 24, 0.3, 5.5)
            ink(ctx, shade(hair, 0.7), 2.5)
            for k in range(4):
                ctx.move_to(70 - k * 30, -84 + k * 6)
                ctx.curve_to(30 - k * 30, -120, -40 - k * 20, -110, -80 - k * 8, -40 + k * 14)
            ink(ctx, shade(hair, 0.72), 2)
        elif style == "slick":  # slicked-back black hair with a shine
            ctx.move_to(70, -92)
            ctx.curve_to(60, -140, -40, -150, -100, -110)
            ctx.curve_to(-130, -80, -128, -20, -110, 10)
            ctx.curve_to(-100, -20, -90, -50, -60, -76)
            ctx.curve_to(-20, -94, 30, -96, 70, -92)
            ctx.close_path()
            fill_stroke(ctx, hair)
            ctx.move_to(40, -110)
            ctx.curve_to(0, -134, -50, -128, -86, -100)
            ink(ctx, (0.6, 0.6, 0.66), 4)
        elif style == "bob":
            for side_x in (-HEAD_RX + 6, f + 92):  # locks framing the face
                ctx.move_to(side_x - 12, -40)
                ctx.curve_to(side_x - 24, 20, side_x - 10, 70, side_x + 6, 86)
                ctx.curve_to(side_x + 16, 50, side_x + 14, 0, side_x + 12, -40)
                ctx.close_path()
                fill_stroke(ctx, hair, ow=4.5)
            ctx.move_to(-HEAD_RX - 14, 10)
            ctx.curve_to(-HEAD_RX - 20, -120, 70, -160, HEAD_RX + 8, -36)
            ctx.curve_to(100, -40, 80, -50, 66, -44)
            ctx.line_to(56, -60)
            ctx.line_to(40, -42)
            ctx.line_to(24, -62)
            ctx.line_to(6, -44)
            ctx.line_to(-12, -60)
            ctx.curve_to(-40, -40, -70, -20, -80, 14)
            ctx.close_path()
            fill_stroke(ctx, hair)
        if L.get("hat") == "beanie":
            hc_ = L.get("hat_c", (0.72, 0.2, 0.18))
            ctx.save()
            ctx.translate(0, -60)
            ctx.scale(L.get("hat_s", 1.0), L.get("hat_s", 1.0))
            ctx.translate(0, 60)
            ctx.move_to(-HEAD_RX - 6, -40)
            ctx.curve_to(-HEAD_RX, -190, HEAD_RX, -190, HEAD_RX + 4, -44)
            ctx.close_path()
            fill_stroke(ctx, hc_)
            for k in range(-3, 4):
                ctx.move_to(k * 26, -70)
                ctx.line_to(k * 22, -150 + abs(k) * 6)
            ink(ctx, shade(hc_, 0.7), 3)
            box_y = -74
            ctx.move_to(-HEAD_RX - 10, box_y + 34)
            ctx.curve_to(-60, box_y + 4, 60, box_y + 4, HEAD_RX + 10, box_y + 30)
            ctx.line_to(HEAD_RX + 8, box_y - 4)
            ctx.curve_to(60, box_y - 30, -60, box_y - 30, -HEAD_RX - 8, box_y)
            ctx.close_path()
            fill_stroke(ctx, shade(hc_, 0.85))
            ellipse(ctx, -6, -176, 30, 28)
            fill_stroke(ctx, L.get("pompom", (0.95, 0.9, 0.8)))
            ctx.restore()
        if L.get("cowl"):  # bat cowl: covers the head down to the nose, with ears and white slit eyes
            cc = L["cowl"]
            for ex0, tip in ((f + 34, (f + 56, -214)), (-58, (-66, -204))):
                ctx.move_to(ex0 - 26, -96)
                ctx.line_to(*tip)
                ctx.line_to(ex0 + 22, -100)
                ctx.close_path()
                fill_stroke(ctx, cc)
            ctx.move_to(-HEAD_RX - 3, 60)
            ctx.curve_to(-HEAD_RX - 14, -190, HEAD_RX + 14, -190, HEAD_RX + 3, 20)
            ctx.line_to(f + 82, 30)
            ctx.line_to(f + 56, 18)
            ctx.line_to(f + 20, 40)
            ctx.curve_to(-20, 46, -60, 60, -86, 96)
            ctx.close_path()
            cowl_path = ctx.copy_path()
            fill_stroke(ctx, cc)
            if L.get("cowl_hi"):  # blue sheen across the top-front of the cowl
                ctx.save()
                ctx.append_path(cowl_path)
                ctx.clip()
                ctx.arc(-30, 40, 165, -math.pi * 0.62, -math.pi * 0.1)
                ctx.set_source_rgb(*L["cowl_hi"])
                ctx.set_line_width(30)
                ctx.stroke()
                ctx.restore()
                ctx.move_to(f + 12, -100)
                ctx.line_to(f + 54, -206)
                ctx.set_source_rgb(*L["cowl_hi"])
                ctx.set_line_width(7)
                ctx.stroke()
            for i, (exx, eyy, erx) in enumerate(eyes):
                d = 1 if i == 0 else -1
                ctx.move_to(exx - 22, eyy + 2 - (8 if d < 0 else 0))
                ctx.line_to(exx + 20, eyy - 8 + (8 if d < 0 else 0) - 4)
                ctx.line_to(exx + 18, eyy + 6)
                ctx.line_to(exx - 18, eyy + 8)
                ctx.close_path()
                fill_stroke(ctx, (1, 1, 1), ow=4)
        if L.get("forelock"):  # the famous little curl on the forehead
            ctx.move_to(f + 10, -92)
            ctx.curve_to(f + 30, -70, f - 10, -56, f + 6, -44)
            ink(ctx, hair, 9)
        if L.get("horns"):
            hcol = L.get("horn_c", (0.95, 0.9, 0.78))
            for d, bx in ((-1, -46), (1, 44)):
                ctx.move_to(bx - 20, -100)
                ctx.curve_to(bx - 14, -150, bx + d * 10, -190, bx + d * 34, -200)
                ctx.curve_to(bx + d * 6, -170, bx + 18, -140, bx + 22, -104)
                ctx.close_path()
                fill_stroke(ctx, hcol, ow=4.5)
        if L.get("monocle"):
            ex_, ey_ = f + 40 * L.get("eye_gap", 1.0), -6
            ctx.arc(ex_, ey_, 30, 0, 2 * math.pi)
            ink(ctx, (0.85, 0.7, 0.3), 5)
            ctx.move_to(ex_ + 24, ey_ + 18)
            ctx.curve_to(ex_ + 50, ey_ + 60, ex_ + 56, ey_ + 110, ex_ + 40, ey_ + 150)
            ink(ctx, (0.85, 0.7, 0.3), 2.5)
        if L.get("hat") == "tophat":  # 1888 silk top hat, worn at a jaunty angle
            ctx.save()
            ctx.translate(0, -96)
            ctx.rotate(-0.08)
            hc_ = L.get("hat_c", (0.12, 0.1, 0.14))
            scene_rr = [(-84, -6), (84, -6)]
            ctx.move_to(-76, -4)
            ctx.line_to(-66, -200)
            ctx.curve_to(-30, -212, 30, -212, 66, -200)
            ctx.line_to(76, -4)
            ctx.close_path()
            fill_stroke(ctx, hc_)
            ctx.move_to(-74, -40)
            ctx.line_to(74, -40)
            ctx.line_to(75, -8)
            ctx.line_to(-75, -8)
            ctx.close_path()
            fill_stroke(ctx, L.get("hat_band", (0.55, 0.1, 0.2)), ow=3)
            ellipse(ctx, 0, 0, 120, 20)
            fill_stroke(ctx, hc_)
            ctx.move_to(-40, -190)
            ctx.line_to(-34, -60)
            ink(ctx, (1, 1, 1), 3)
            ctx.restore()
        ctx.restore()
