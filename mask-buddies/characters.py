"""Cartoon characters for MASK BUDDIES, drawn procedurally with cairo.

Coordinates: each character is drawn with its feet at (0, 0), y grows down,
so the body lives in negative y.  Limb angles use 0 = straight down and
positive = towards the facing direction.
"""
import math
import random

import cairo

TAU = math.pi * 2


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


INK = hexc("#16121c")


def col(ctx, c):
    ctx.set_source_rgba(*c)


def shade(c, f=0.75):
    return (c[0] * f, c[1] * f, c[2] * f, c[3])


def path_poly(ctx, pts, close=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


def fill_ink(ctx, fill, lw=6):
    col(ctx, fill)
    ctx.fill_preserve()
    col(ctx, INK)
    ctx.set_line_width(lw)
    ctx.stroke()


def ellipse(ctx, x, y, rx, ry):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, TAU)
    ctx.restore()


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def stroke_limb(ctx, pts, w, c, lw=5):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    path_poly(ctx, pts, close=False)
    col(ctx, INK)
    ctx.set_line_width(w + 2 * lw)
    ctx.stroke()
    path_poly(ctx, pts, close=False)
    col(ctx, c)
    ctx.set_line_width(w)
    ctx.stroke()


def vec(a, length, f):
    return (math.sin(a) * length * f, math.cos(a) * length)


# --------------------------------------------------------------------------
# Walking humanoid base
# --------------------------------------------------------------------------

WALK_STYLES = {
    #          leg amp, knee flex, arm amp, step length factor
    "normal": (0.46, 0.75, 0.55, 1.0),
    "stiff": (0.26, 0.35, 0.06, 0.55),   # slow horror-movie stalk
    "run": (0.75, 1.30, 1.00, 1.7),
    "sneak": (0.40, 1.10, 0.25, 0.8),
    "shuffle": (0.22, 0.40, 0.20, 0.45),  # granny steps
}


class Humanoid:
    thigh = 118
    shin = 118
    foot_h = 24
    torso = 185
    torso_w = 150
    limb_w = 44
    arm_up = 96
    arm_lo = 90
    head_off = 120   # neck -> head centre
    head_top_ext = 160
    scale = 1.0
    body = hexc("#888888")
    shoe = hexc("#222222")
    hand = hexc("#222222")
    default_style = "normal"

    # ---- kinematics -------------------------------------------------------
    def leg(self, phase, w, style):
        amp, flex, _, _ = WALK_STYLES[style]
        a = amp * w * math.sin(phase)
        k = flex * w * max(0.0, math.cos(phase)) ** 1.3
        if style == "sneak":
            k += 0.35 * w
        b = a - k
        kx, ky = math.sin(a) * self.thigh, math.cos(a) * self.thigh
        fx, fy = kx + math.sin(b) * self.shin, ky + math.cos(b) * self.shin
        return (kx, ky), (fx, fy), b

    def hip_height(self, phase, w, style):
        _, (_, f1), _ = self.leg(phase, w, style)
        _, (_, f2), _ = self.leg(phase + math.pi, w, style)
        return max(f1, f2) + self.foot_h

    def head_top(self, st):
        hip = self.hip_height(st["phase"], st["walkw"], st["style"])
        return (hip + self.torso + self.head_off + self.head_top_ext) * self.scale

    def arm_targets(self, st):
        """(near_upper, near_lower, far_upper, far_lower) angles."""
        ph, w, t = st["phase"], st["walkw"], st["t"]
        _, _, aamp, _ = WALK_STYLES[st["style"]]
        sw = aamp * w * math.sin(ph)
        bend = 0.25 + 0.35 * w
        pose = st["arms"]
        near = (-sw, -sw + bend)
        far = (sw, sw + bend)
        if pose == "stiff":
            near = (0.04 + 0.05 * w * math.sin(ph), 0.08)
            far = (0.04 - 0.05 * w * math.sin(ph), 0.08)
        elif pose == "up":
            wig = 0.12 * math.sin(t * 14)
            near, far = (2.75 + wig, 2.95 + wig), (2.55 - wig, 2.75 - wig)
        elif pose == "wave":
            near = (2.5, 2.6 + 0.55 * math.sin(t * 11))
        elif pose == "point":
            near = (1.5, 1.52)
        elif pose == "hips":
            near, far = (-0.7, 0.95), (-0.6, 0.95)
        elif pose == "shrug":
            near, far = (-0.25, 1.75), (-0.15, 1.85)
        elif pose == "zombie":
            near, far = (1.5 + 0.04 * math.sin(t * 3), 1.55), (1.45, 1.5)
        elif pose == "hold":
            near = (0.55, 1.6)
        elif pose == "cover":
            near, far = (2.55, 3.05), (2.45, 2.95)
        elif pose == "knock":
            near = (1.35, 1.4 + 0.7 * max(0.0, math.sin(t * 16)))
        elif pose == "think":
            near = (2.1, 3.0)
        return near + far

    # ---- drawing ----------------------------------------------------------
    def draw(self, ctx, st):
        f = st["facing"]
        ph, w, style = st["phase"], st["walkw"], st["style"]
        ctx.save()
        sx = st.get("squash", 0.0)
        ctx.translate(st["x"] + math.sin(st["t"] * 70) * 7 * st["shake"], -st["jump"])
        ctx.scale(self.scale * (1 + sx), self.scale * (1 - sx))

        hip = -self.hip_height(ph, w, style)
        if st.get("breathe", True):
            hip += math.sin(st["t"] * 2.2) * 2.5 * (1 - w)
        near_leg = self.leg(ph, w, style)
        far_leg = self.leg(ph + math.pi, w, style)
        shoulder_y = hip - self.torso + 34
        arms = st.get("arm_ang") or self.arm_targets(st)

        # far arm, far leg
        self.draw_arm(ctx, (f * -6, shoulder_y), arms[2], arms[3], f, far=True, st=st)
        self.draw_leg(ctx, hip, far_leg, f, far=True)
        self.draw_leg(ctx, hip, near_leg, f, far=False)
        self.draw_torso(ctx, hip, f, st)
        self.draw_arm(ctx, (f * 10, shoulder_y), arms[0], arms[1], f, far=False, st=st)

        # head
        neck_y = hip - self.torso
        talk = st["talk"]
        tilt = talk * 0.07 * math.sin(st["t"] * 17) + st.get("tilt", 0.0)
        bob = -abs(math.sin(st["t"] * 9)) * 7 * talk
        ctx.save()
        ctx.translate(f * 4, neck_y - self.head_off + bob)
        ctx.rotate(tilt)
        self.draw_head(ctx, st)
        ctx.restore()
        ctx.restore()

    def draw_leg(self, ctx, hip, leg, f, far):
        (kx, ky), (fx, fy), b = leg
        c = shade(self.leg_col(), 0.78) if far else self.leg_col()
        hx = f * (-8 if far else 8)
        stroke_limb(ctx, [(hx, hip), (hx + kx * f, hip + ky), (hx + fx * f, hip + fy)], self.limb_w, c)
        # shoe
        ctx.save()
        ctx.translate(hx + fx * f + f * 16, hip + fy + self.foot_h * 0.45)
        ctx.rotate(-f * max(-0.5, min(0.5, b * 0.45)))
        rrect(ctx, -36, -self.foot_h * 0.6, 72, self.foot_h * 1.15, 14)
        fill_ink(ctx, shade(self.shoe, 0.8) if far else self.shoe, 5)
        ctx.restore()

    def leg_col(self):
        return self.body

    def draw_arm(self, ctx, sh, up, lo, f, far, st):
        c = shade(self.sleeve_col(), 0.78) if far else self.sleeve_col()
        ex, ey = vec(up, self.arm_up, f)
        hx, hy = vec(lo, self.arm_lo, f)
        p0 = sh
        p1 = (sh[0] + ex, sh[1] + ey)
        p2 = (p1[0] + hx, p1[1] + hy)
        stroke_limb(ctx, [p0, p1, p2], self.limb_w * 0.82, c)
        if not far:
            self.held_item(ctx, p2, lo, f, st)
        ctx.arc(p2[0], p2[1], 22, 0, TAU)
        fill_ink(ctx, shade(self.hand, 0.8) if far else self.hand, 5)

    def sleeve_col(self):
        return self.body

    def held_item(self, ctx, p, ang, f, st):
        item = st.get("item")
        if not item:
            return
        ctx.save()
        ctx.translate(*p)
        if item == "spatula":
            ctx.rotate(-f * (ang - 0.3))
            stroke_limb(ctx, [(0, 0), (0, 95)], 10, hexc("#c8915a"), 4)
            rrect(ctx, -24, 90, 48, 62, 10)
            fill_ink(ctx, hexc("#d9d9de"), 5)
        elif item == "cup":
            rrect(ctx, f * 8 - 24, -44, 48, 56, 8)
            fill_ink(ctx, hexc("#ffffff"), 5)
            ctx.rectangle(f * 8 - 24, -24, 48, 16)
            col(ctx, hexc("#8a5a3b"))
            ctx.fill()
        elif item == "pie":
            ellipse(ctx, f * 30, -18, 60, 20)
            fill_ink(ctx, hexc("#e8a33d"), 5)
            ellipse(ctx, f * 30, -24, 46, 12)
            col(ctx, hexc("#c2602a"))
            ctx.fill()
        elif item == "cane":
            stroke_limb(ctx, [(0, -10), (f * 6, 240)], 12, hexc("#7a4a2a"), 4)
        ctx.restore()

    def draw_torso(self, ctx, hip, f, st):
        top = hip - self.torso
        rrect(ctx, -self.torso_w / 2, top, self.torso_w, self.torso + 26, 48)
        fill_ink(ctx, self.body)
        self.torso_details(ctx, hip, top, f, st)

    def torso_details(self, ctx, hip, top, f, st):
        pass

    def draw_head(self, ctx, st):
        ellipse(ctx, 0, 0, 100, 120)
        fill_ink(ctx, hexc("#ffcc99"))


# --------------------------------------------------------------------------
# POLY  (the low-poly black mask)
# --------------------------------------------------------------------------

class Poly(Humanoid):
    name = "Poly"
    body = hexc("#e84a7f")
    shoe = hexc("#1d1d22")
    hand = hexc("#1d1d22")
    head_off = 118
    head_top_ext = 165

    def torso_details(self, ctx, hip, top, f, st):
        # zipper + belt + hood rim
        ctx.set_line_width(5)
        col(ctx, shade(self.body, 0.6))
        ctx.move_to(f * 12, top + 30)
        ctx.line_to(f * 12, hip + 10)
        ctx.stroke()
        rrect(ctx, -self.torso_w / 2 + 3, hip - 18, self.torso_w - 6, 22, 6)
        fill_ink(ctx, hexc("#2a2a30"), 4)
        rrect(ctx, -62, top - 6, 124, 34, 16)
        fill_ink(ctx, shade(self.body, 0.82), 5)

    def draw_head(self, ctx, st):
        outline = [(0, -160), (-24, -128), (-80, -118), (-104, -60), (-110, 10), (-99, 62),
                   (-75, 108), (-38, 136), (38, 136), (75, 108), (99, 62), (110, 10),
                   (104, -60), (80, -118), (24, -128)]
        path_poly(ctx, outline)
        fill_ink(ctx, hexc("#18181d"), 7)

        def facet(pts, c, edge=True):
            path_poly(ctx, pts)
            col(ctx, hexc(c))
            ctx.fill_preserve()
            ctx.set_line_width(2)
            col(ctx, hexc("#3d3d46") if edge else hexc(c))
            ctx.stroke()

        facet([(-22, -126), (0, -158), (22, -126)], "#2b2b32")
        facet([(-78, -116), (78, -116), (62, -82), (-62, -82)], "#2c2c33")
        facet([(-62, -82), (62, -82), (28, -56), (-28, -56)], "#222228")
        facet([(-104, -58), (-62, -82), (-84, -40)], "#26262c")
        facet([(104, -58), (62, -82), (84, -40)], "#34343c")
        facet([(-106, 4), (-60, 14), (-52, 72), (-96, 60)], "#202026")
        facet([(106, 4), (60, 14), (52, 72), (96, 60)], "#383840")
        facet([(-60, 14), (-20, 34), (-26, 64), (-52, 72)], "#26262c")
        facet([(60, 14), (20, 34), (26, 64), (52, 72)], "#2f2f36")
        facet([(-15, -52), (15, -52), (19, 30), (-19, 30)], "#33333b")
        facet([(-27, 30), (27, 30), (18, 50), (-18, 50)], "#1d1d22")
        facet([(-52, 74), (-26, 64), (0, 70), (26, 64), (52, 74), (0, 80)], "#26262c")
        facet([(-42, 86), (42, 86), (28, 104), (-28, 104)], "#2d2d34")
        facet([(-36, 134), (36, 134), (28, 112), (-28, 112)], "#25252a")
        facet([(-96, 62), (-52, 74), (-42, 86), (-74, 108)], "#1c1c21")
        facet([(96, 62), (52, 74), (42, 86), (74, 108)], "#303037")
        # nostrils
        col(ctx, hexc("#0b0b0e"))
        ctx.rectangle(-16, 46, 10, 5)
        ctx.rectangle(6, 46, 10, 5)
        ctx.fill()
        # mouth line (grumpy)
        ctx.set_line_width(5)
        col(ctx, hexc("#08080a"))
        path_poly(ctx, [(-46, 86), (-18, 80), (18, 80), (46, 86)], close=False)
        ctx.stroke()
        # mesh eyes
        glow = st.get("eye_glow", 0.0)
        for s in (-1, 1):
            eye = [(s * -84, -30), (s * -64, -42), (s * -26, -36), (s * -20, -22),
                   (s * -38, -11), (s * -76, -13)]
            ctx.save()
            path_poly(ctx, eye)
            ctx.clip_preserve()
            col(ctx, hexc("#ffe08a") if glow > 0.5 else hexc("#f1e2b6"))
            ctx.fill()
            col(ctx, hexc("#141418"))
            ctx.set_line_width(3.5)
            for gx in range(-90, 0, 8):
                ctx.move_to(s * gx, -50)
                ctx.line_to(s * gx, 0)
            for gy in range(-46, 0, 8):
                ctx.move_to(-100, gy)
                ctx.line_to(100, gy)
            ctx.stroke()
            ctx.restore()
            path_poly(ctx, eye)
            col(ctx, INK)
            ctx.set_line_width(4)
            ctx.stroke()


# --------------------------------------------------------------------------
# STITCHES  (the rubber horror mask with messy hair and a scar)
# --------------------------------------------------------------------------

class Stitches(Humanoid):
    name = "Stitches"
    body = hexc("#33405e")
    shoe = hexc("#4a3426")
    hand = hexc("#5c5c66")
    head_off = 122
    head_top_ext = 175
    default_style = "stiff"

    def __init__(self):
        rnd = random.Random(7)
        self.hair = []
        for i in range(140):
            a = rnd.uniform(-2.7, -0.45)
            r0 = rnd.uniform(70, 118)
            ln = rnd.uniform(25, 75)
            wob = rnd.uniform(-0.6, 0.6)
            c = rnd.choice(["#4b3e35", "#5e5045", "#3a3029", "#6f6257", "#2e2621"])
            self.hair.append((a, r0, ln, wob, c, rnd.uniform(2, 5)))

    def torso_details(self, ctx, hip, top, f, st):
        # collar
        path_poly(ctx, [(-50, top + 4), (0, top + 40), (50, top + 4)], close=False)
        ctx.set_line_width(6)
        col(ctx, hexc("#222b40"))
        ctx.stroke()
        # chest pocket + name patch
        rrect(ctx, f * 18 - 26 if f > 0 else f * 18 - 26, top + 60, 52, 40, 6)
        fill_ink(ctx, shade(self.body, 0.85), 4)
        rrect(ctx, -f * 40 - 30, top + 62, 60, 22, 6)
        fill_ink(ctx, hexc("#e9e4d8"), 3)
        col(ctx, hexc("#7a1b2a"))
        ctx.set_line_width(3)
        ctx.move_to(-f * 40 - 20, top + 73)
        ctx.line_to(-f * 40 + 20, top + 73)
        ctx.stroke()
        rrect(ctx, -self.torso_w / 2 + 3, hip - 16, self.torso_w - 6, 18, 6)
        fill_ink(ctx, hexc("#2a2018"), 4)

    def draw_head(self, ctx, st):
        # hair behind
        ellipse(ctx, 0, -40, 112, 110)
        col(ctx, hexc("#3e332b"))
        ctx.fill()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        t = st["t"]
        windy = 0.06 * math.sin(t * 3) + st["walkw"] * 0.08
        for a, r0, ln, wob, c, lw in self.hair:
            x0, y0 = math.cos(a) * r0, math.sin(a) * r0 * 1.05 - 18
            a2 = a + wob * 0.5 + windy
            x1, y1 = x0 + math.cos(a2) * ln, y0 + math.sin(a2) * ln
            ctx.move_to(x0, y0)
            ctx.curve_to(x0 + (x1 - x0) * 0.5 + wob * 10, y0 + (y1 - y0) * 0.3,
                         x1 - wob * 8, y1, x1, y1)
            col(ctx, hexc(c))
            ctx.set_line_width(lw)
            ctx.stroke()
        # face
        ellipse(ctx, 0, 6, 96, 128)
        ctx.save()
        ctx.clip_preserve()
        g = cairo.LinearGradient(-96, 0, 96, 0)
        g.add_color_stop_rgb(0, 0.93, 0.92, 0.89)
        g.add_color_stop_rgb(0.42, 0.88, 0.87, 0.84)
        g.add_color_stop_rgb(0.56, 0.24, 0.24, 0.25)
        g.add_color_stop_rgb(1, 0.13, 0.13, 0.14)
        ctx.set_source(g)
        ctx.fill()
        # wrinkles
        ctx.set_line_width(2)
        col(ctx, hexc("#9a978f", 0.7))
        for y in (-70, -58, -46):
            ctx.move_to(-60, y)
            ctx.curve_to(-30, y - 6, 0, y + 4, 30, y - 3)
        ctx.stroke()
        ctx.restore()
        ellipse(ctx, 0, 6, 96, 128)
        col(ctx, INK)
        ctx.set_line_width(7)
        ctx.stroke()
        # hairline fringe
        for i in range(-5, 6):
            x = i * 17
            ctx.move_to(x, -112 + abs(i) * 4)
            ctx.line_to(x + 8 * math.sin(i + t), -78 + abs(i) * 5)
            col(ctx, hexc("#3a3029"))
            ctx.set_line_width(7)
            ctx.stroke()
        # eye sockets + holes
        ellipse(ctx, -40, -12, 36, 22)
        col(ctx, hexc("#4b4b50", 0.75))
        ctx.fill()
        for s, xo in ((-1, -40), (1, 40)):
            ctx.save()
            ctx.translate(xo, -10)
            ctx.move_to(-26, 2)
            ctx.curve_to(-12, -14, 14, -14, 26, -2)
            ctx.curve_to(12, 10, -12, 10, -26, 2)
            col(ctx, hexc("#070707"))
            ctx.fill()
            ctx.restore()
        # shy little pupils that only appear when he blinks at you
        if st.get("eyes_shine", 0) > 0.5:
            for xo in (-40, 40):
                ctx.arc(xo + 4, -10, 4, 0, TAU)
                col(ctx, hexc("#ffffff"))
                ctx.fill()
        # nose
        ellipse(ctx, 2, 30, 20, 18)
        col(ctx, hexc("#f2efe8"))
        ctx.fill()
        col(ctx, hexc("#111111"))
        ctx.arc(-8, 42, 4, 0, TAU)
        ctx.fill()
        ctx.arc(12, 42, 4, 0, TAU)
        ctx.fill()
        # lips
        ctx.move_to(-30, 76)
        ctx.curve_to(-10, 70, 12, 72, 32, 80)
        ctx.set_line_width(5)
        col(ctx, hexc("#2b2b2b"))
        ctx.stroke()
        ellipse(ctx, 0, 92, 26, 12)
        col(ctx, hexc("#d8d5cd", 0.8))
        ctx.fill()
        # stitched scar
        ctx.move_to(-78, 6)
        ctx.curve_to(-70, 34, -64, 60, -54, 92)
        col(ctx, hexc("#8e1b2e"))
        ctx.set_line_width(6)
        ctx.stroke()
        ctx.set_line_width(3)
        for k in range(6):
            u = k / 5
            x = -78 + u * 24
            y = 6 + u * 86
            ctx.move_to(x - 9, y - 2)
            ctx.line_to(x + 9, y + 2)
        ctx.stroke()


# --------------------------------------------------------------------------
# Supporting cast
# --------------------------------------------------------------------------

class Ghosty:
    """Bedsheet ghost barista. Floats instead of walking."""
    name = "Ghosty"
    scale = 1.0
    default_style = "normal"

    def head_top(self, st):
        return 520 + 60 + st.get("lift", 0)

    def arm_targets(self, st):
        return (0, 0, 0, 0)

    def draw(self, ctx, st):
        t = st["t"]
        ctx.save()
        ctx.translate(st["x"] + math.sin(t * 70) * 9 * st["shake"],
                      -60 - st.get("lift", 0) - math.sin(t * 2.4) * 16 - st["jump"])
        # shadow is drawn by the engine; body:
        ctx.move_to(-120, 0)
        for i in range(0, 13):
            x = -120 + i * 20
            y = 14 * math.sin(i * 1.3 + t * 5)
            ctx.line_to(x, y)
        ctx.curve_to(150, -200, 140, -380, 0, -500)
        ctx.curve_to(-140, -380, -150, -200, -120, 0)
        ctx.close_path()
        fill_ink(ctx, hexc("#fbfbff"), 7)
        # apron
        path_poly(ctx, [(-70, -250), (70, -250), (90, -40), (-90, -40)])
        fill_ink(ctx, hexc("#8a5a3b"), 5)
        col(ctx, hexc("#fbe7c6"))
        ctx.select_font_face("Luckiest Guy")
        ctx.set_font_size(30)
        ext = ctx.text_extents("BOO")
        ctx.move_to(-ext.width / 2 - ext.x_bearing, -150)
        ctx.show_text("BOO")
        # nub arms
        wave = 0.3 * math.sin(t * 6) if st["talk"] > 0 else 0
        for s in (-1, 1):
            ctx.save()
            ctx.translate(s * 110, -280)
            ctx.rotate(s * (0.6 + wave) if st["arms"] != "up" else s * 2.4)
            ellipse(ctx, 0, 34, 24, 46)
            fill_ink(ctx, hexc("#f2f2fa"), 6)
            ctx.restore()
        # face
        scared = st.get("scared", 0)
        for s in (-1, 1):
            ellipse(ctx, s * 38, -380, 20 + 6 * scared, 30 + 8 * scared)
            col(ctx, hexc("#121212"))
            ctx.fill()
            ctx.arc(s * 38 + 6, -390, 6, 0, TAU)
            col(ctx, hexc("#ffffff"))
            ctx.fill()
        for s in (-1, 1):
            ellipse(ctx, s * 66, -340, 18, 10)
            col(ctx, hexc("#ff9bb3", 0.7))
            ctx.fill()
        mo = 6 + 18 * st["talk"] * abs(math.sin(t * 15)) + 18 * scared
        ellipse(ctx, 0, -322, 16, mo)
        col(ctx, hexc("#2a1020"))
        ctx.fill()
        ctx.restore()


class GrannyPumpkin(Humanoid):
    name = "Granny Pumpkin"
    scale = 0.86
    body = hexc("#7b4fa3")
    shoe = hexc("#3b2a22")
    hand = hexc("#f2c9a0")
    torso = 170
    head_off = 92
    head_top_ext = 140
    default_style = "shuffle"

    def leg_col(self):
        return hexc("#c9b8a6")

    def sleeve_col(self):
        return hexc("#a27fc4")

    def draw_torso(self, ctx, hip, f, st):
        top = hip - self.torso
        # long skirt
        path_poly(ctx, [(-70, top + 60), (70, top + 60), (110, hip + 120), (-110, hip + 120)])
        fill_ink(ctx, self.body)
        for k in range(-2, 3):
            ctx.arc(k * 40, hip + 60, 9, 0, TAU)
            col(ctx, hexc("#f4d35e"))
            ctx.fill()
        rrect(ctx, -72, top, 144, 130, 46)
        fill_ink(ctx, hexc("#a27fc4"))
        # shawl
        path_poly(ctx, [(-80, top + 10), (80, top + 10), (0, top + 120)])
        fill_ink(ctx, hexc("#e36f8e"), 5)

    def draw_head(self, ctx, st):
        glow = st.get("glow", 0.0)
        if glow > 0.01:
            g = cairo.RadialGradient(0, 0, 40, 0, 0, 420)
            g.add_color_stop_rgba(0, 1, 0.85, 0.3, 0.75 * glow)
            g.add_color_stop_rgba(1, 1, 0.6, 0.1, 0)
            ctx.set_source(g)
            ctx.arc(0, 0, 420, 0, TAU)
            ctx.fill()
        # pumpkin ribs
        for dx, rx in ((-70, 70), (70, 70), (-30, 70), (30, 70), (0, 66)):
            ellipse(ctx, dx, 0, rx, 104)
            fill_ink(ctx, hexc("#f08a24") if dx == 0 else hexc("#e2771a"), 6)
        # stem
        path_poly(ctx, [(-10, -100), (10, -100), (18, -140), (2, -146)])
        fill_ink(ctx, hexc("#5c7a2e"), 5)
        # carved face
        lit = hexc("#ffe066") if glow > 0.3 else hexc("#4a2205")
        for s in (-1, 1):
            path_poly(ctx, [(s * 22, -10), (s * 70, -10), (s * 46, -50)])
            fill_ink(ctx, lit, 4)
        path_poly(ctx, [(-10, 16), (10, 16), (0, 2)])
        fill_ink(ctx, lit, 4)
        mo = 1.0 + 0.6 * st["talk"] * abs(math.sin(st["t"] * 13)) + glow * 0.6
        pts = [(-62, 38)]
        for i in range(9):
            x = -62 + (i + 1) * 13.8
            pts.append((x, 38 + (10 if i % 2 == 0 else 0)))
        pts += [(62, 38), (40, 38 + 34 * mo), (-40, 38 + 34 * mo)]
        path_poly(ctx, pts)
        fill_ink(ctx, lit, 4)
        # glasses
        ctx.set_line_width(5)
        col(ctx, hexc("#c9a227"))
        for s in (-1, 1):
            ctx.arc(s * 46, -26, 32, 0, TAU)
            ctx.stroke()
        ctx.move_to(-14, -26)
        ctx.line_to(14, -26)
        ctx.stroke()
        # headscarf knot
        ellipse(ctx, 0, -96, 80, 30)
        fill_ink(ctx, hexc("#e36f8e"), 5)


class OfficerQuackers(Humanoid):
    name = "Officer Quackers"
    body = hexc("#2f5fb3")
    shoe = hexc("#151515")
    hand = hexc("#f2f2f2")
    head_off = 100
    head_top_ext = 165

    def torso_details(self, ctx, hip, top, f, st):
        rrect(ctx, -self.torso_w / 2 + 3, hip - 20, self.torso_w - 6, 24, 6)
        fill_ink(ctx, hexc("#151515"), 4)
        # badge star
        cx, cy = f * 30, top + 70
        pts = []
        for i in range(10):
            r = 22 if i % 2 == 0 else 10
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        path_poly(ctx, pts)
        fill_ink(ctx, hexc("#ffd23f"), 3)
        ctx.set_line_width(4)
        col(ctx, shade(self.body, 0.6))
        ctx.move_to(0, top + 30)
        ctx.line_to(0, hip - 20)
        ctx.stroke()

    def draw_head(self, ctx, st):
        f = st["facing"]
        ctx.arc(0, 0, 104, 0, TAU)
        fill_ink(ctx, hexc("#ffd23f"), 7)
        for s in (-1, 1):
            ellipse(ctx, s * 40, -20, 22, 28)
            fill_ink(ctx, hexc("#ffffff"), 4)
            ctx.arc(s * 40 + f * 7, -16, 11, 0, TAU)
            col(ctx, hexc("#111111"))
            ctx.fill()
        # beak: opens with talking
        open_ = 0.05 + 0.35 * st["talk"] * abs(math.sin(st["t"] * 15))
        ctx.save()
        ctx.translate(0, 30)
        ellipse(ctx, 0, 0, 74, 26)
        fill_ink(ctx, hexc("#ff8c1a"), 5)
        ctx.rotate(0)
        ctx.translate(0, 18 + open_ * 60)
        ellipse(ctx, 0, 0, 60, 18)
        fill_ink(ctx, hexc("#f07c0a"), 5)
        ctx.restore()
        # police cap
        path_poly(ctx, [(-96, -66), (96, -66), (84, -130), (-84, -130)])
        fill_ink(ctx, hexc("#1d2f5e"), 6)
        ellipse(ctx, 0, -66, 112, 16)
        fill_ink(ctx, hexc("#111a33"), 5)
        ctx.arc(0, -100, 16, 0, TAU)
        fill_ink(ctx, hexc("#ffd23f"), 4)


class Pigeon:
    name = "Pigeon"
    scale = 1.0
    default_style = "normal"

    def head_top(self, st):
        return 60

    def arm_targets(self, st):
        return (0, 0, 0, 0)

    def draw(self, ctx, st):
        t = st["t"]
        f = st["facing"]
        ctx.save()
        ctx.translate(st["x"], st.get("y", 0) - st["jump"])
        ctx.scale(f * 1.0, 1.0)
        flying = st.get("flying", False)
        peck = 0.0 if flying else max(0.0, math.sin(t * 5)) ** 8 * 0.6
        # legs
        if not flying:
            stroke_limb(ctx, [(-6, -14), (-8, 0)], 4, hexc("#e0703a"), 2)
            stroke_limb(ctx, [(8, -14), (10, 0)], 4, hexc("#e0703a"), 2)
        ellipse(ctx, 0, -38, 44, 28)
        fill_ink(ctx, hexc("#8d93a3"), 5)
        # wing
        flap = math.sin(t * 30) if flying else 0
        ctx.save()
        ctx.translate(-6, -44)
        ctx.rotate(-0.2 - flap * 0.9)
        ellipse(ctx, -14, 0, 30, 14)
        fill_ink(ctx, hexc("#6f7586"), 4)
        ctx.restore()
        # head
        ctx.save()
        ctx.translate(30, -64)
        ctx.rotate(peck)
        ctx.arc(0, 0, 18, 0, TAU)
        fill_ink(ctx, hexc("#5d7a8c"), 4)
        path_poly(ctx, [(14, -2), (30, 3), (14, 8)])
        fill_ink(ctx, hexc("#f2b33d"), 3)
        ctx.arc(5, -4, 4, 0, TAU)
        col(ctx, hexc("#ff7a1a"))
        ctx.fill()
        ctx.restore()
        ctx.restore()


CAST = {
    "poly": Poly,
    "stitches": Stitches,
    "ghosty": Ghosty,
    "granny": GrannyPumpkin,
    "quackers": OfficerQuackers,
    "pigeon": Pigeon,
}
